"""API v2（5.2 occurrence；5.3 dataset / map；5.4 partner 之後加在這裡）

共通行為（user.html）：
- 回傳 {status: {code, message}, meta: {total, limit}, links: {self, next}, data: [...]}；map 例外（直接回 GeoJSON）
- HTTP 狀態碼與 status.code 一致：200（查無資料也是 200、data 為空陣列）、400、401、404、500
- 游標分頁：參數 cursor 由 links.next 帶，使用者不用自己組；最後一頁 links.next 為 null
- 限制型（只有 occurrence）：Authorization: Bearer <API_KEY>（APIkey.status='pass'）；帶了但無效 → 401。
  dataset / map 只有公開版，不看 Authorization header（11/23 Kim）
參數驗證與欄位整理在 api/v2_params.py（不需要 Django，有單元測試）。
"""
import json
import logging
from urllib.parse import urlencode

import psycopg2
import requests
from psycopg2.extras import RealDictCursor
from django.http import HttpResponse, QueryDict

from api.models import APIkey
from api.v2_params import (ParamError, parse_limit, occurrence_query, format_occurrence,
                           parse_cursor_id, dataset_query, format_dataset, DATASET_SELECT, map_query)
from conf.background import run_light
from conf.settings import RECORDS_URL, SOLR_TIMEOUT
from conf.utils import scheme
from data.fields import API_OCCURRENCE_SOLR_FL, API_OCCURRENCE_SOLR_FL_WITH_SENSITIVE
from data.utils import (create_search_query, background_search_stat, build_stat_query_string, get_partner_name_map,
                        get_partner_id_by_group, get_map_geojson, datahub_conn)
from manager.models import SearchCount, Partner

logger = logging.getLogger(__name__)

STATUS_MESSAGE = {200: 'Success', 400: 'Bad Request', 401: 'Unauthorized', 404: 'Not Found', 500: 'Internal Server Error'}


def json_response(code, body=None, message=None):
    body = dict(body or {})
    body = {'status': {'code': code, 'message': message or STATUS_MESSAGE.get(code, '')}, **body}
    return HttpResponse(json.dumps(body, ensure_ascii=False, default=str), status=code,
                        content_type='application/json; charset=utf-8')


def error_response(code, message=None):
    return json_response(code, message=message)


def api_key_status(request):
    """(restricted, error_response)：沒帶 header → 公開；Bearer 金鑰有效 → 限制型；帶了但格式或金鑰無效 → 401"""
    auth = request.headers.get('Authorization')
    if not auth:
        return False, None
    scheme_, _, key = auth.strip().partition(' ')
    key = key.strip()
    if scheme_.lower() != 'bearer' or not key:
        return False, error_response(401, 'Invalid Authorization header: 格式為 Bearer <API_KEY>')
    if not APIkey.objects.filter(key=key, status='pass').exists():
        return False, error_response(401, 'Invalid API key')
    return True, None


def request_params(request):
    """QueryDict → {參數: [值]}，並取出 from_example（文件範例連結，不列入統計）"""
    params = {k: v for k, v in request.GET.lists()}
    is_from_example = (params.pop('from_example', None) or [''])[0] == '1'   # 同 v1 pop_internal_flags
    return params, is_from_example


def page_links(request, path, params, cursor, next_cursor, n_docs, limit):
    """self：本頁（含 cursor，第一頁不帶）；next：還有下一頁才給，否則 None"""
    base = {k: v for k, v in params.items() if k != 'cursor'}

    def url(c):
        p = dict(base)
        if c and c != '*':
            p['cursor'] = [c]
        qs = urlencode(p, doseq=True)
        return f'{scheme}://{request.get_host()}{path}' + (f'?{qs}' if qs else '')

    has_next = next_cursor and next_cursor != cursor and n_docs == limit
    return {'self': url(cursor), 'next': url(next_cursor) if has_next else None}


def record_stat(location, fq, params, compute_stat=True):
    """SearchStat（第一頁）與 SearchCount；v2 存原始的 v2 參數（不含 cursor / limit）。
    dataset / map 同 v1 不算各單位筆數（compute_stat=False）"""
    query_string = build_stat_query_string({k: v for k, v in params.items()})
    if not params.get('cursor'):
        run_light(background_search_stat, fq, location, query_string, compute_stat, False)
    obj, _ = SearchCount.objects.get_or_create(search_location=location)
    obj.count += 1
    obj.save()


def has_more_docs(query, next_cursor):
    """本頁取滿時，用下一個 cursor 取 1 筆 id 確認還有沒有資料（Solr cursorMark 在剛好取完時仍會給新的 cursor，
    要再查一次才會得到空頁）。查詢失敗時當作還有，保留 next（最多多一頁空的，不影響資料）"""
    probe = dict(query, params={'cursorMark': next_cursor}, limit=1, fields=['id'])
    try:
        r = requests.post(RECORDS_URL, data=json.dumps(probe), headers={'content-type': 'application/json'},
                          timeout=SOLR_TIMEOUT)
        r.raise_for_status()
        return bool(r.json()['response']['docs'])
    except (requests.RequestException, ValueError, KeyError):
        logger.warning('api v2 occurrence: next page probe failed', exc_info=True)
        return True


def occurrence(request):
    if request.method != 'GET':
        return error_response(400, 'Only GET is supported')

    restricted, err = api_key_status(request)
    if err:
        return err

    params, is_from_example = request_params(request)
    try:
        limit = parse_limit(params)
        site_params, extra_fq = occurrence_query(params, restricted)
    except ParamError as e:
        return error_response(400, str(e))

    qd = QueryDict('', mutable=True)
    for k, vals in site_params.items():
        qd.setlist(k, vals)
    try:
        # higherTaxonID 查不到時，create_search_query 會加上查無資料的條件（11/20 網站與 API 一起改）
        fq = create_search_query(qd, get_raw_map=restricted) + extra_fq if site_params else list(extra_fq)
    except requests.RequestException:
        logger.exception('api v2 occurrence: taxa request failed')
        return error_response(500)

    cursor = (params.get('cursor') or ['*'])[0] or '*'
    query = {
        'query': '*:*',
        'params': {'cursorMark': cursor},
        'limit': limit,
        'sort': 'id asc',   # cursorMark 需要以 uniqueKey 排序
        'fields': API_OCCURRENCE_SOLR_FL_WITH_SENSITIVE if restricted else API_OCCURRENCE_SOLR_FL,
    }
    if fq:
        query['filter'] = fq

    try:
        resp = requests.post(RECORDS_URL, data=json.dumps(query), headers={'content-type': 'application/json'},
                             timeout=SOLR_TIMEOUT)
    except requests.RequestException:
        logger.exception('api v2 occurrence: Solr request failed')
        return error_response(500)
    if resp.status_code == 400:
        # 參數都驗證過，Solr 回 400 通常是 cursor 被改過
        msg = 'Invalid cursor' if cursor != '*' else 'Invalid query'
        logger.warning('api v2 occurrence: Solr 400 %s %s', msg, resp.text[:500])
        return error_response(400, msg)
    if resp.status_code != 200:
        logger.error('api v2 occurrence: Solr %s %s', resp.status_code, resp.text[:500])
        return error_response(500)

    body = resp.json()
    docs = body['response']['docs']
    next_cursor = body.get('nextCursorMark')
    if len(docs) == limit and next_cursor and next_cursor != cursor and not has_more_docs(query, next_cursor):
        next_cursor = None   # 剛好取完（總數是 limit 的倍數），不給空的下一頁
    partner_names = get_partner_name_map('zh')
    data = [format_occurrence(d, restricted, partner_names) for d in docs]

    if not is_from_example:
        record_stat('api_occ', fq, params)

    return json_response(200, {
        'meta': {'total': body['response']['numFound'], 'limit': limit},
        'links': page_links(request, request.path, params, cursor, next_cursor, len(docs), limit),
        'data': data,
    })


def partner_groups_map():
    """tbiaPartnerID → [Partner.group]（dataset 篩選用；PG dataset 沒有 tbiaPartnerID）[P2-2-REMOVE]"""
    out = {}
    for pid, group in Partner.objects.exclude(tbia_partner_id__isnull=True).values_list('tbia_partner_id', 'group'):
        out.setdefault(str(pid), [])
        if group not in out[str(pid)]:
            out[str(pid)].append(group)
    return out


def dataset(request):
    """5.3 v2 dataset：查 PG dataset（第一階段仍是舊欄位名，用別名輸出 v2 名稱）。游標為 dataset.id"""
    if request.method != 'GET':
        return error_response(400, 'Only GET is supported')

    params, is_from_example = request_params(request)
    try:
        limit = parse_limit(params)
        cursor = parse_cursor_id(params)
        groups = partner_groups_map() if params.get('tbiaPartnerID') else {}
        where, values = dataset_query(params, groups)
    except ParamError as e:
        return error_response(400, str(e))

    cond = ' WHERE ' + ' AND '.join(where)
    page_cond = cond + (' AND "id" > %s' if cursor is not None else '')
    page_values = values + ([cursor] if cursor is not None else [])
    try:
        with datahub_conn() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT count(*) AS n FROM dataset' + cond, values)
            total = cur.fetchone()['n']
            # 多取 1 筆判斷是否還有下一頁（總數剛好是 limit 的倍數時，不給空的下一頁）
            cur.execute(DATASET_SELECT + page_cond + ' ORDER BY "id" LIMIT %s', page_values + [limit + 1])
            rows = cur.fetchall()
    except psycopg2.Error:
        logger.exception('api v2 dataset: PG query failed')
        return error_response(500)
    has_more = len(rows) > limit
    rows = rows[:limit]

    partner_names = get_partner_name_map('zh')
    data = [format_dataset(r, _GroupToPartner(), partner_names) for r in rows]

    if not is_from_example:
        record_stat('api_dataset', [], params, compute_stat=False)

    cur_str = str(cursor) if cursor is not None else '*'
    next_str = str(rows[-1]['id']) if has_more else None
    return json_response(200, {
        'meta': {'total': total, 'limit': limit},
        'links': page_links(request, request.path, params, cur_str, next_str, len(rows), limit),
        'data': data,
    })


class _GroupToPartner:
    """format_dataset 用的 group → tbiaPartnerID（走 data.utils 的 5 分鐘快取）"""
    def get(self, group):
        return get_partner_id_by_group(group) if group else None


def map(request):
    """5.3 v2 map：成功時直接回 GeoJSON FeatureCollection（user.html）；錯誤同其他 v2 API 回 {status}。
    只有公開版：模糊化網格 grid_N_blurred、公開縣市（11/23 Kim）"""
    if request.method != 'GET':
        return error_response(400, 'Only GET is supported')

    params, is_from_example = request_params(request)
    try:
        grid, fq = map_query(params)
    except ParamError as e:
        return error_response(400, str(e))

    facet_grid = f'grid_{grid}_blurred'
    query = {
        'query': '*:*',
        'limit': 0,
        'filter': fq,
        'facet': {facet_grid: {'field': facet_grid, 'mincount': 1, 'type': 'terms', 'limit': -1}},
    }
    try:
        resp = requests.post(RECORDS_URL, data=json.dumps(query), headers={'content-type': 'application/json'},
                             timeout=SOLR_TIMEOUT)
    except requests.RequestException:
        logger.exception('api v2 map: Solr request failed')
        return error_response(500)
    if resp.status_code != 200:
        logger.error('api v2 map: Solr %s %s', resp.status_code, resp.text[:500])
        return error_response(500)

    facets = resp.json().get('facets') or {}
    buckets = (facets.get(facet_grid) or {}).get('buckets') or []
    geojson = get_map_geojson(data_c=buckets, grid=grid)[f'grid_{grid}']

    if not is_from_example:
        record_stat('api_map', [], params, compute_stat=False)

    return HttpResponse(json.dumps(geojson, ensure_ascii=False), status=200,
                        content_type='application/json; charset=utf-8')
