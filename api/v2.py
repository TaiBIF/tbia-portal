"""API v2（5.2 occurrence；5.3 dataset / map、5.4 partner 之後加在這裡）

共通行為（user.html）：
- 回傳 {status: {code, message}, meta: {total, limit}, links: {self, next}, data: [...]}；map 例外（直接回 GeoJSON）
- HTTP 狀態碼與 status.code 一致：200（查無資料也是 200、data 為空陣列）、400、401、404、500
- 游標分頁：參數 cursor 由 links.next 帶，使用者不用自己組；最後一頁 links.next 為 null
- 限制型：Authorization: Bearer <API_KEY>（APIkey.status='pass'）；帶了但無效 → 401
參數驗證與欄位整理在 api/v2_params.py（不需要 Django，有單元測試）。
"""
import json
import logging
from urllib.parse import urlencode

import requests
from django.http import HttpResponse, QueryDict

from api.models import APIkey
from api.v2_params import ParamError, parse_limit, occurrence_query, format_occurrence
from conf.background import run_light
from conf.settings import RECORDS_URL, SOLR_TIMEOUT
from conf.utils import scheme
from data.fields import API_OCCURRENCE_SOLR_FL, API_OCCURRENCE_SOLR_FL_WITH_SENSITIVE
from data.utils import create_search_query, background_search_stat, build_stat_query_string, get_partner_name_map
from manager.models import SearchCount

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


def record_stat(location, fq, params):
    """SearchStat（第一頁）與 SearchCount；v2 存原始的 v2 參數（不含 cursor / limit）"""
    query_string = build_stat_query_string({k: v for k, v in params.items()})
    if not params.get('cursor'):
        run_light(background_search_stat, fq, location, query_string, True, False)
    obj, _ = SearchCount.objects.get_or_create(search_location=location)
    obj.count += 1
    obj.save()


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
    partner_names = get_partner_name_map('zh')
    data = [format_occurrence(d, restricted, partner_names) for d in docs]

    if not is_from_example:
        record_stat('api_occ', fq, params)

    return json_response(200, {
        'meta': {'total': body['response']['numFound'], 'limit': limit},
        'links': page_links(request, request.path, params, cursor, body.get('nextCursorMark'), len(docs), limit),
        'data': data,
    })
