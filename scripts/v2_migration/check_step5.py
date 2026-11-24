# 步驟 5（5.1～5.5）程式化檢查：測試站 portal-v2 用，直接呼叫 API view，結果與 Solr 直接查詢比對
# 用法（在 ~/tbia-portal-v2）：
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/check_step5.py > /tmp/check_step5.txt 2>&1
# 選項（exec 後加 -e，例 exec -T -e STEP5_TEMP_KEY=1 web-v2 ...）：
#   STEP5_TEMP_KEY=1  DB 沒有 status=pass 的 APIkey 時，暫時建一把測限制型，結束時刪除（會寫 portal-v2 DB）
#   STEP5_STAT=1      檢查第一頁會寫 SearchStat、from_example=1 不寫（會寫 portal-v2 DB 的 SearchStat / SearchCount）
#   STEP5_ONLY=5.3    只跑指定的項目，可用逗號分隔（例 5.3,5.4）；不加時 5.1～5.5 全跑
# 不加選項時只讀不寫（所有呼叫都帶 from_example=1，不列入統計）。
# 每項印 PASS / FAIL / SKIP / INFO，編號對應交接文件「5.2 測試清單」「5.3 測試清單」「5.4 測試清單」「5.5 測試清單」
import json
import os
import re
import time
import traceback
import uuid
from urllib.parse import urlsplit, parse_qsl

import requests
from django.test import RequestFactory

from conf.settings import RECORDS_URL, RECORDS_V1_URL, SOLR_TIMEOUT
from api.models import APIkey
from manager.models import SearchStat
from data.fields import API_OCCURRENCE_FIELDS
from data.utils import INFRASPECIES_RANKS
from data.search_params import RANK_SOLR_TO_EN, TAXON_GROUPS, SOURCE_DATABASE_RENAME
from data.fields import API_DATASET_FIELDS
from data.utils import datahub_conn
from conf.settings import SOLR_PREFIX
import api.v2 as v2
import api.views as av

RF = RequestFactory()
RESULTS = []
HOST = 'v2-wip.tbiadata.tw'


def report(no, ok, msg=''):
    status = {True: 'PASS', False: 'FAIL', None: 'SKIP', 'info': 'INFO'}[ok]
    RESULTS.append((no, status))
    print(f'[{status}] {no} {msg}')


def run(no, fn):
    try:
        fn()
    except Exception as e:
        report(no, False, f'例外：{e}')
        traceback.print_exc()


def api(params=None, key=None, stat=False, view=None):
    """呼叫 v2 occurrence（或指定 view），回傳 (HTTP 狀態碼, JSON)"""
    params = dict(params or {})
    if not stat:
        params['from_example'] = '1'
    headers = {'HTTP_HOST': HOST}
    if key:
        headers['HTTP_AUTHORIZATION'] = f'Bearer {key}'
    resp = (view or v2.occurrence)(RF.get('/api/v2/occurrence', params, **headers))
    return resp.status_code, json.loads(resp.content)


def solr_count(fq, url=RECORDS_URL):
    body = {'query': '*:*', 'limit': 0}
    if fq:
        body['filter'] = fq if isinstance(fq, list) else [fq]
    r = requests.post(url, data=json.dumps(body), headers={'content-type': 'application/json'}, timeout=SOLR_TIMEOUT)
    r.raise_for_status()
    return r.json()['response']['numFound']


def solr_docs(fq, fl, rows=1, url=RECORDS_URL):
    body = {'query': '*:*', 'limit': rows, 'fields': fl, 'filter': fq if isinstance(fq, list) else [fq]}
    r = requests.post(url, data=json.dumps(body), headers={'content-type': 'application/json'}, timeout=SOLR_TIMEOUT)
    r.raise_for_status()
    return r.json()['response']['docs']


def total(params, key=None):
    code, b = api(params, key)
    if code != 200:
        raise AssertionError(f'{params} 回 {code} {b.get("status")}')
    return b['meta']['total']


def same(no, label, params, fq, key=None):
    a, s = total(params, key), solr_count(fq)
    report(no, a == s, f'{label}：API {a:,} / Solr {s:,}')


# ===================== 5.1 v1 =====================

def c_5_1():
    code, b = api({'limit': 1}, view=av.occurrence)
    t = solr_count([], RECORDS_V1_URL)
    doc = (b.get('data') or [{}])[0]
    ok = code == 200 and b['meta']['total'] == t and 'rightsHolder' in doc and 'sourceDatabase' not in doc
    report('5.1-1', ok, f'v1 occurrence 讀 {RECORDS_V1_URL.split("/")[-2]}：total {b["meta"]["total"]:,} / Solr {t:,}，欄位為 v1 名稱')


# ===================== 5.2 共通 =====================

def c_1():
    code, b = api({'limit': 3})
    ok = (code == 200 and b['status'] == {'code': 200, 'message': 'Success'}
          and set(b) == {'status', 'meta', 'links', 'data'} and b['meta']['limit'] == 3 and len(b['data']) == 3)
    report('5.2-1', ok, '回傳結構 status / meta / links / data，HTTP 200')
    t = solr_count([])
    report('5.2-2', b['meta']['total'] == t, f'不帶參數 total {b["meta"]["total"]:,} = Solr {t:,}')
    keys_ok = all(list(d) == API_OCCURRENCE_FIELDS for d in b['data'])
    report('5.2-3', keys_ok and not any(k.startswith('raw') for d in b['data'] for k in d),
           f'每筆 {len(API_OCCURRENCE_FIELDS)} 個欄位、順序同 user.html（partnerName 在 tbiaPartnerID 後）、沒有 raw*')


def c_4():
    # 找一個 30～120 筆的資料集，limit=20 走完 links.next
    r = requests.get(RECORDS_URL, params={
        'q': '*:*', 'rows': 0, 'facet': 'true', 'facet.field': 'tbiaDatasetID', 'facet.limit': 2000,
        'facet.mincount': 30, 'facet.sort': 'count'}, timeout=SOLR_TIMEOUT).json()
    f = r['facet_counts']['facet_fields']['tbiaDatasetID']
    cand = [(f[i], f[i + 1]) for i in range(0, len(f), 2) if 30 <= f[i + 1] <= 120]
    if not cand:
        report('5.2-4', None, '找不到 30～120 筆的資料集')
        return
    ds, n = cand[-1]
    params, ids, pages = {'tbiaDatasetID': ds, 'limit': 20}, [], 0
    while params is not None and pages < 20:
        code, b = api(params)
        assert code == 200, b
        ids += [d['tbiaID'] for d in b['data']]
        pages += 1
        nxt = b['links']['next']
        params = dict(parse_qsl(urlsplit(nxt).query)) if nxt else None
    # 總數剛好是 limit 的倍數：最後一頁取滿後 next 應為 null，不能多一頁空的（11/23 修正）
    code, b = api({'tbiaDatasetID': ds, 'limit': n})
    exact = code == 200 and len(b['data']) == n and b['links']['next'] is None
    report('5.2-4', len(ids) == n == len(set(ids)) and params is None and exact,
           f'分頁：資料集 {ds} {n} 筆，{pages} 頁取回 {len(ids)} 筆、不重複，最後一頁 next 為 null；'
           f'limit={n}（剛好一頁）next 為 null：{exact}')


def c_5():
    code, b = api({'limit': 5000})
    ok = code == 200 and b['meta']['limit'] == 1000 and len(b['data']) == 1000
    t0 = time.time()
    api({'limit': 1000, 'taxonGroup': '鳥類'})
    report('5.2-5', ok, f'limit 超過 1000 以 1000 計；limit=1000 一頁 {time.time() - t0:.1f} 秒')


BAD = [
    ({'limit': '0'}, 'limit=0'),
    ({'taxonGroupByHabitat': 'freshWater'}, 'freshWater'),
    ({'taxonGroupByHabitat': 'fossil'}, 'fossil'),
    ({'taxonRank': 'species'}, 'taxonRank 小寫'),
    ({'taxonGroup': '昆蟲'}, '舊類群'),
    ({'mediaType': 'image'}, 'mediaType 無 hasMedia'),
    ({'hasMedia': 'yes'}, 'hasMedia 非布林'),
    ({'circle': '121.5,23.5,25.01'}, 'circle 25.01 公里'),
    ({'polygon': 'POLYGON((121 22,122 22,122 23))'}, 'polygon 未閉合'),
    ({'boundedBy': '121,23,122,22'}, 'boundedBy 最大小於最小'),
    ({'created': '2024-01-01'}, 'created 非 YYYYMMDD'),
    ({'eventDate': '20240230'}, 'eventDate 不存在的日期'),
    ({'apikey': 'x'}, 'v1 apikey 參數'),
    ({'cursor': 'AoE_bad'}, '竄改的 cursor'),
]


def c_6():
    fails = []
    for p, label in BAD:
        code, b = api(p)
        if not (code == 400 and b['status']['code'] == 400):
            fails.append(f'{label}→{code}')
    report('5.2-6', not fails, f'不合法參數 {len(BAD)} 種皆回 400' + (f'；不符：{fails}' if fails else ''))


def c_7():
    code1, b1 = api({'limit': 1}, key='not-a-key-' + uuid.uuid4().hex)
    resp = v2.occurrence(RF.get('/api/v2/occurrence', {'from_example': '1'}, HTTP_HOST=HOST, HTTP_AUTHORIZATION='Token abc'))
    report('5.2-7', code1 == 401 == b1['status']['code'] and resp.status_code == 401,
           '無效金鑰、非 Bearer 格式皆回 401（HTTP 與 status.code 一致）')


# ===================== 5.2 參數與 Solr 比對 =====================

def c_8():
    same('5.2-8a', 'isCollection=true', {'isCollection': 'true'}, 'recordType:col')
    same('5.2-8b', 'isCollection=false', {'isCollection': 'false'}, 'recordType:occ')
    same('5.2-8c', 'created 單日', {'created': '20261105'}, 'created:[2026-11-05T00:00:00Z TO 2026-11-05T23:59:59Z]')
    same('5.2-8d', 'modified 一邊 *', {'modified': '20261101,*'}, 'modified:[2026-11-01T00:00:00Z TO *]')
    same('5.2-8e', 'eventDate 一邊 *', {'eventDate': '*,19991231'}, 'standardDate:[* TO 1999-12-31T23:59:59Z]')
    same('5.2-8f', 'boundedBy', {'boundedBy': '121.6,22.7,121.4,22.6'}, 'location_rpt:[22.6,121.4 TO 22.7,121.6]')
    same('5.2-8g', 'circle 25 公里', {'circle': '121.5,23.5,25'}, '{!geofilt sfield=location_rpt pt=23.5,121.5 d=25}')
    same('5.2-8h', 'protectedStatus=CHPA（含舊值 1）', {'protectedStatus': 'CHPA'}, 'protected:("CHPA" OR "1")')
    same('5.2-8i', 'taxonRank=Infraspecies', {'taxonRank': 'Infraspecies'}, f'taxonRank:({" OR ".join(INFRASPECIES_RANKS)})')
    same('5.2-8r', 'taxonRank=Subspecies（TaiCOL 全部階層）', {'taxonRank': 'Subspecies'}, 'taxonRank:subspecies')
    same('5.2-8s', 'taxonRank=Special Form', {'taxonRank': 'Special Form'}, 'taxonRank:"special form"')
    same('5.2-8j', 'taxonGroupByHabitat=freshwater', {'taxonGroupByHabitat': 'freshwater'}, 'is_freshwater:true')
    a, b = total({'hasMedia': 'true', 'mediaType': 'image,video,audio'}), total({'hasMedia': 'true'})
    report('5.2-8k', a == b, f'mediaType 三種全選 = hasMedia=true：{a:,} / {b:,}')
    pid = solr_docs('tbiaPartnerID:*', ['tbiaPartnerID'])[0]['tbiaPartnerID']
    same('5.2-8l', 'tbiaPartnerID', {'tbiaPartnerID': pid}, f'tbiaPartnerID:"{pid}"')
    doc = solr_docs('datasetID:* AND sourceDatabase:*', ['datasetID', 'sourceDatabase', 'id'])[0]
    same('5.2-8m', 'datasetID + sourceDatabase 交集', {'datasetID': doc['datasetID'], 'sourceDatabase': doc['sourceDatabase']},
         [f'datasetID:"{doc["datasetID"]}"', f'sourceDatabase:"{doc["sourceDatabase"]}"'])
    code, b = api({'tbiaID': doc['id']})
    report('5.2-8n', code == 200 and b['meta']['total'] == 1 and b['data'][0]['tbiaID'] == doc['id'], f'tbiaID={doc["id"]} 取回 1 筆')
    a = total({'higherTaxonID': 't9999999999'})
    report('5.2-8p', a == 0, f'不存在的 higherTaxonID 查無資料（網站與 API 相同）：{a:,}')
    from django.http import QueryDict
    from data.utils import create_search_query
    n1 = solr_count(create_search_query(QueryDict('higherTaxonID=t9999999999')))
    n2 = solr_count(create_search_query(QueryDict('tbiaDatasetID=not-a-dataset')))
    report('5.2-8q', n1 == 0 and n2 == 0, f'網站搜尋：不存在的 higherTaxonID {n1:,} 筆、tbiaDatasetID {n2:,} 筆（原本會回全部資料）')
    a = total({'taxonGroup': '鳥類,哺乳類'})
    s = solr_count('taxonGroup:("鳥類" OR "哺乳類")')
    report('5.2-8o', a == s, f'多值聯集 taxonGroup=鳥類,哺乳類：API {a:,} / Solr {s:,}')


def c_9():
    code, b = api({'limit': 200, 'sourceDatabase': '台灣生物多樣性網絡 TBN'})
    rows = b['data']
    fmt = all(re.fullmatch(r'\d{8} \d{6}', r['created'] or '') and re.fullmatch(r'\d{8} \d{6}', r['modified'] or '') for r in rows)
    pn = all(r['partnerName'] for r in rows if r['tbiaPartnerID'])
    report('5.2-9a', bool(rows) and fmt, 'created / modified 為 YYYYMMDD HHMMSS')
    report('5.2-9b', bool(rows) and pn, '有 tbiaPartnerID 的都有 partnerName')
    # taxonRank：records 與 taxa core 實際出現的值都要對得到 TaiCOL ranks 表（對不到 = Solr 寫法和 key 換空白的規則不同）
    for no, url in (('5.2-9c', RECORDS_URL), ('5.2-9e', f'{SOLR_PREFIX}taxa/select')):
        r = requests.get(url, params={'q': '*:*', 'rows': 0, 'facet': 'true', 'facet.field': 'taxonRank',
                                      'facet.limit': -1, 'facet.mincount': 1}, timeout=SOLR_TIMEOUT).json()
        f = r['facet_counts']['facet_fields']['taxonRank']
        vals = {f[i]: f[i + 1] for i in range(0, len(f), 2)}
        missing = {v: n for v, n in vals.items() if v not in RANK_SOLR_TO_EN}
        report(no, not missing, f'{url.split("/")[-2]} 的 taxonRank {len(vals)} 種皆對得到 ranks 表'
               + (f'；對不到：{missing}' if missing else ''))
    code, b = api({'limit': 5, 'sourceDatabase': 'GBIF'})
    report('5.2-9d', all(r['tbiaPartnerID'] is None and r['partnerName'] is None for r in b['data']),
           f'GBIF 的 tbiaPartnerID / partnerName 為 null（{len(b["data"])} 筆）')


# ===================== 5.2 公開 / 限制型 =====================

def find_key():
    k = APIkey.objects.filter(status='pass').values_list('key', flat=True).first()
    if k:
        return k, False
    if os.environ.get('STEP5_TEMP_KEY') == '1':
        obj = APIkey.objects.create(key='check-step5-' + uuid.uuid4().hex, status='pass')
        return obj.key, True
    return None, False


def c_10(key):
    if not key:
        for n in ('5.2-10a', '5.2-10b', '5.2-10c', '5.2-10d'):
            report(n, None, '沒有 status=pass 的 APIkey；加 -e STEP5_TEMP_KEY=1 重跑')
        return
    doc = solr_docs('rawDecimalLatitude:* AND decimalLatitude:* AND rawCounty:*',
                    ['id', 'decimalLatitude', 'rawDecimalLatitude', 'county', 'rawCounty', 'dataGeneralizations'])[0]
    _, pub = api({'tbiaID': doc['id']})
    _, res = api({'tbiaID': doc['id']}, key=key)
    p, r = pub['data'][0], res['data'][0]
    report('5.2-10a', p['decimalLatitude'] == doc['decimalLatitude'] and p['county'] == doc.get('county'),
           f'公開：模糊化紀錄 {doc["id"]} 回公開座標 / 縣市')
    report('5.2-10b', r['decimalLatitude'] == doc['rawDecimalLatitude'] and r['county'] == doc['rawCounty']
           and r['dataGeneralizations'] == p['dataGeneralizations'] and not any(k.startswith('raw') for k in r),
           '限制型：回原始座標 / 縣市、dataGeneralizations 與公開相同、沒有 raw* 欄位')
    county = doc['rawCounty']
    a_pub, a_res = total({'county': county}), total({'county': county}, key)
    s_pub = solr_count(f'county:"{county}"')
    s_res = solr_count(f'county:"{county}" OR rawCounty:"{county}"')
    report('5.2-10c', a_pub == s_pub and a_res == s_res,
           f'county={county}：公開 {a_pub:,}（Solr 公開欄位 {s_pub:,}）、限制型 {a_res:,}（公開或原始 {s_res:,}）')
    box, rng = '122.1,25.4,120.0,21.8', '[21.8,120.0 TO 25.4,122.1]'
    a_pub, a_res = total({'boundedBy': box}), total({'boundedBy': box}, key)
    s_pub = solr_count(f'location_rpt:{rng}')
    s_res = solr_count(f'location_rpt:{rng} OR raw_location_rpt:{rng}')
    report('5.2-10d', a_pub == s_pub and a_res == s_res,
           f'boundedBy 臺灣本島：公開 {a_pub:,}（Solr {s_pub:,}）、限制型 {a_res:,}（公開或原始座標 {s_res:,}）')


def c_11():
    if os.environ.get('STEP5_STAT') != '1':
        report('5.2-11', None, '加 -e STEP5_STAT=1 才檢查（會寫 SearchStat）')
        return
    before = SearchStat.objects.filter(search_location='api_occ').count()
    api({'taxonGroup': '鳥類', 'limit': 1}, stat=True)
    api({'taxonGroup': '鳥類', 'limit': 1})             # from_example=1
    time.sleep(5)
    after = SearchStat.objects.filter(search_location='api_occ').count()
    last = SearchStat.objects.filter(search_location='api_occ').order_by('-id').first()
    report('5.2-11', after - before == 1 and 'taxonGroup' in (last.query or '') and 'limit' not in (last.query or ''),
           f'第一頁寫 1 筆 SearchStat（query={last.query if last else None}）、from_example=1 不寫')


# ===================== 5.3 dataset =====================

def call(view, path, params, stat=False, **headers):
    params = dict(params or {})
    if not stat:
        params['from_example'] = '1'
    resp = view(RF.get(path, params, HTTP_HOST=HOST, **headers))
    return resp.status_code, json.loads(resp.content)


def ds(params, stat=False, **headers):
    return call(v2.dataset, '/api/v2/dataset', params, stat, **headers)


def pg(sql, values=()):
    with datahub_conn() as conn, conn.cursor() as cur:
        cur.execute(sql, list(values))
        return cur.fetchall()


def pg_count(cond='', values=()):
    return pg('SELECT count(*) FROM dataset WHERE "deprecated" = \'f\'' + (' AND ' + cond if cond else ''), values)[0][0]


def ds_total(params):
    code, b = ds(params)
    if code != 200:
        raise AssertionError(f'{params} 回 {code} {b.get("status")}')
    return b['meta']['total']


def d_1():
    code, b = ds({'limit': 5})
    t = pg_count()
    ok = (code == 200 and set(b) == {'status', 'meta', 'links', 'data'} and len(b['data']) == 5
          and all(list(d) == API_DATASET_FIELDS for d in b['data']) and b['meta']['total'] == t)
    report('5.3-1', ok, f'結構、每筆 {len(API_DATASET_FIELDS)} 欄（順序同 user.html，partnerName 在 tbiaPartnerID 後）、'
                        f'total {b["meta"]["total"]:,} = PG {t:,}')


def d_2():
    # 找一個 30～300 個資料集的來源資料庫，limit=25 走完 links.next
    rows = pg('SELECT "rights_holder", count(*) FROM dataset WHERE "deprecated" = \'f\' GROUP BY 1 '
              'HAVING count(*) BETWEEN 30 AND 300 ORDER BY 2')
    if not rows:
        report('5.3-2', None, '找不到 30～300 個資料集的來源資料庫')
        return
    old, n = rows[0]
    name = SOURCE_DATABASE_RENAME.get(old, old)
    params, ids, pages = {'sourceDatabase': name, 'limit': 25}, [], 0
    while params is not None and pages < 30:
        code, b = ds(params)
        assert code == 200, b
        ids += [d['tbiaDatasetID'] for d in b['data']]
        pages += 1
        nxt = b['links']['next']
        params = dict(parse_qsl(urlsplit(nxt).query)) if nxt else None
    # 總數剛好是 limit 的倍數：最後一頁取滿後 next 應為 null，不能多一頁空的（11/23 修正）
    lim = next((k for k in range(7, n) if n % k == 0), n)
    params, pages2, empty = {'sourceDatabase': name, 'limit': lim}, 0, 0
    while params is not None and pages2 < 100:
        code, b = ds(params)
        assert code == 200, b
        pages2 += 1
        empty += not b['data']
        nxt = b['links']['next']
        params = dict(parse_qsl(urlsplit(nxt).query)) if nxt else None
    exact = empty == 0 and pages2 == n // lim
    report('5.3-2', len(ids) == n == len(set(ids)) and params is None and exact,
           f'分頁：{name} {n} 個資料集，{pages} 頁取回 {len(ids)} 個、不重複，最後一頁 next 為 null；'
           f'limit={lim}（整除）{pages2} 頁、沒有空頁：{exact}')


def d_3():
    # 各參數與 PG 直接查詢筆數一致
    from manager.models import Partner
    for p in Partner.objects.exclude(tbia_partner_id__isnull=True).exclude(group='gbif').order_by('id'):
        groups = list(Partner.objects.filter(tbia_partner_id=p.tbia_partner_id).values_list('group', flat=True).distinct())
        s = pg_count('"group" = ANY(%s)', [groups])
        if s:
            break
    a = ds_total({'tbiaPartnerID': str(p.tbia_partner_id)})
    report('5.3-3a', a == s and a > 0, f'tbiaPartnerID（{p.title}，group {groups}）：API {a:,} / PG {s:,}')

    old, new = '科博典藏 (NMNS Collection)', '科博典藏'
    a, s = ds_total({'sourceDatabase': new}), pg_count('"rights_holder" IN (%s, %s)', [old, new])
    a_old = ds_total({'sourceDatabase': old})
    report('5.3-3b', a == s and a > 0 and a_old == 0, f'sourceDatabase 新名稱 {new}：API {a:,} / PG {s:,}；舊名稱 {a_old}（應為 0）')

    a, s = ds_total({'datasetTaxonGroup': '鳥類,哺乳類'}), pg_count(
        '("datasetTaxonGroup" LIKE %s OR "datasetTaxonGroup" LIKE %s)', ['%鳥類%', '%哺乳類%'])
    report('5.3-3c', a == s and a > 0, f'datasetTaxonGroup=鳥類,哺乳類：API {a:,} / PG {s:,}')

    a, s = ds_total({'datasetName': '調查'}), pg_count('"name" LIKE %s', ['%調查%'])
    report('5.3-3d', a == s and a > 0, f'datasetName=調查（部分比對）：API {a:,} / PG {s:,}')

    # created：取 PG 最常見的建立日期，單日、區間、一邊為 *
    day = pg('SELECT "created"::date, count(*) FROM dataset WHERE "deprecated" = \'f\' GROUP BY 1 ORDER BY 2 DESC LIMIT 1')[0][0]
    d8 = day.strftime('%Y%m%d')
    checks = [
        ({'created': d8}, '"created"::date = %s', [day]),
        ({'created': f'{d8},*'}, '"created"::date >= %s', [day]),
        ({'modified': f'*,{d8}'}, '"modified"::date <= %s', [day]),
    ]
    out = []
    for params, cond, vals in checks:
        a, s = ds_total(params), pg_count(cond, vals)
        out.append((a == s, f'{params}：{a:,}/{s:,}'))
    report('5.3-3e', all(o for o, _ in out), '日期：' + '；'.join(m for _, m in out))

    r = pg('SELECT "tbiaDatasetID", "sourceDatasetID" FROM dataset WHERE "deprecated" = \'f\' '
           'AND "sourceDatasetID" <> \'\' AND "gbifDatasetID" <> \'\' LIMIT 1')
    if r:
        code, b = ds({'tbiaDatasetID': r[0][0]})
        report('5.3-3f', code == 200 and b['meta']['total'] == 1 and b['data'][0]['tbiaDatasetID'] == r[0][0],
               f'tbiaDatasetID={r[0][0]} 取回 1 筆')
    else:
        report('5.3-3f', None, '找不到同時有 datasetID 與 gbifDatasetID 的資料集')


def d_4():
    # 值的格式：created / modified YYYYMMDD HHMMSS、datasetDateStart / End YYYYMMDD、夥伴單位、GBIF
    code, b = ds({'limit': 1000})
    data = b['data']
    bad_time = [d['tbiaDatasetID'] for d in data for f in ('created', 'modified')
                if d[f] is not None and not re.fullmatch(r'\d{8} \d{6}', d[f])]
    report('5.3-4a', not bad_time, f'前 {len(data)} 筆 created / modified 皆為 YYYYMMDD HHMMSS' + (f'；不符 {bad_time[:5]}' if bad_time else ''))
    bad_date = sorted({d[f] for d in data for f in ('datasetDateStart', 'datasetDateEnd')
                       if d[f] is not None and not re.fullmatch(r'\d{8}', d[f])})
    col_type = pg("SELECT data_type FROM information_schema.columns WHERE table_name = 'dataset' AND column_name = 'datasetDateStart'")
    report('5.3-4b', not bad_date, f'datasetDateStart / End 皆為 YYYYMMDD（PG 型別 {col_type[0][0] if col_type else "?"}）'
           + (f'；其他格式 {bad_date[:10]}' if bad_date else ''))
    no_name = [d['tbiaDatasetID'] for d in data if d['tbiaPartnerID'] and not d['partnerName']]
    report('5.3-4c', not no_name, '有 tbiaPartnerID 的都有 partnerName' + (f'；缺 {no_name[:5]}' if no_name else ''))
    g = pg('SELECT count(*) FROM dataset WHERE "deprecated" = \'f\' AND "group" = \'gbif\'')[0][0]
    if g:
        a = ds_total({'sourceDatabase': 'GBIF'})
        code, b = ds({'sourceDatabase': 'GBIF', 'limit': 50})
        report('5.3-4d', b['data'] and all(d['tbiaPartnerID'] is None and d['partnerName'] is None for d in b['data']),
               f'GBIF 資料集（{a:,} 個）tbiaPartnerID / partnerName 為 null')
    else:
        report('5.3-4d', None, 'PG 沒有 group=gbif 的資料集')
    # 實際存在的類群詞（不在 v2 控制詞彙的列出來：查詢用 LIKE，舊類群詞會查不到）
    tokens = {}
    for (v,) in pg('SELECT "datasetTaxonGroup" FROM dataset WHERE "deprecated" = \'f\' AND "datasetTaxonGroup" <> \'\''):
        for t in re.split(r'[,、;|]\s*', v or ''):
            if t.strip():
                tokens[t.strip()] = tokens.get(t.strip(), 0) + 1
    other = {k: n for k, n in tokens.items() if k not in TAXON_GROUPS}
    report('5.3-4e', not other, 'PG datasetTaxonGroup 的值都在 v2 類群詞彙內' + (f'；其他值 {other}' if other else ''))


DS_BAD = [
    ({'cursor': 'abc'}, '不合法 cursor'),
    ({'limit': '0'}, 'limit=0'),
    ({'datasetTaxonGroup': '昆蟲'}, '舊類群'),
    ({'created': '2024-01-01'}, 'created 非 YYYYMMDD'),
    ({'tbiaDatasetID': ['a', 'b']}, 'tbiaDatasetID 重複帶不同值'),
]


def d_5():
    fails = [f'{label}→{ds(p)[0]}' for p, label in DS_BAD if ds(p)[0] != 400]
    code, b = ds({'limit': 1}, HTTP_AUTHORIZATION='Bearer not-a-key')
    zero = ds_total({'tbiaPartnerID': 'not-a-partner'})
    report('5.3-5', not fails and code == 200 and zero == 0,
           f'不合法參數 {len(DS_BAD)} 種回 400；帶無效 Bearer 仍 200（dataset 不看金鑰）；不存在的 tbiaPartnerID 0 筆'
           + (f'；不符：{fails}' if fails else ''))


# ===================== 5.3 map =====================

def mp(params, stat=False):
    return call(v2.map, '/api/v2/map', params, stat)


def map_sum(params):
    code, b = mp(params)
    if code != 200:
        raise AssertionError(f'{params} 回 {code} {b}')
    return sum(f['properties']['counts'] for f in b['features']), b


def m_1():
    params = {'boundedBy': '122,24,121,23', 'grid': '5', 'taxonGroup': '鳥類'}
    n, b = map_sum(params)
    s = solr_count(['location_rpt:[23,121 TO 24,122]', '-organismQuantity:0', 'taxonGroup:"鳥類"'])
    props_ok = all(set(f['properties']) == {'counts', 'current_grid_level', 'current_grid'}
                   and f['properties']['current_grid_level'] == 'grid_5' for f in b['features'])
    report('5.3-6', b.get('type') == 'FeatureCollection' and 'status' not in b and props_ok and n == s and n > 0,
           f'直接回 FeatureCollection（{len(b["features"])} 格，properties 為 counts / current_grid_level / current_grid）；'
           f'網格筆數合計 {n:,} / Solr {s:,}（不含 organismQuantity=0）')


def m_2():
    base = {'boundedBy': '122,24,121,23', 'grid': '10'}
    box = ['location_rpt:[23,121 TO 24,122]', '-organismQuantity:0']
    out = []
    for y, fq in [('2020', 'year:2020'), ('2018,2021', 'year:[2018 TO 2021]'),
                  ('2020,*', 'year:[2020 TO *]'), ('*,2000', 'year:[* TO 2000]')]:
        n, _ = map_sum({**base, 'year': y})
        s = solr_count(box + [fq])
        out.append((n == s, f'{y}：{n:,}/{s:,}'))
    n, _ = map_sum({**base, 'county': '臺東縣'})
    s = solr_count(box + ['county:"臺東縣"'])
    out.append((n == s, f'county 臺東縣：{n:,}/{s:,}'))
    report('5.3-7', all(o for o, _ in out), 'year 單一值為該年（v1 為該年以後）、區間與縣市與 Solr 一致：' + '；'.join(m for _, m in out))


MAP_BAD = [
    ({'grid': '1'}, '缺 boundedBy'),
    ({'boundedBy': '122,23,121,22'}, '缺 grid'),
    ({'boundedBy': '122,23,121,22', 'grid': '2'}, 'grid=2'),
    ({'boundedBy': '125,25,115,15', 'grid': '1'}, '1 公里網格跨度 10 度'),
    ({'boundedBy': '122,23,121,22', 'grid': '1', 'year': '20'}, 'year 非 yyyy'),
    ({'boundedBy': '122,23,121,22', 'grid': '1', 'taxonGroup': '昆蟲'}, '舊類群'),
]


def m_3():
    fails = []
    for p, label in MAP_BAD:
        code, b = mp(p)
        if not (code == 400 and b.get('status', {}).get('code') == 400):
            fails.append(f'{label}→{code}')
    # user.html 的 4 個網格範例都要 200
    ex = [('122,23,121,22', '1'), ('125,25,115,15', '5'), ('122,23,102,3', '10'), ('120,25,80,-15', '100')]
    ex_fail = [g for bb, g in ex if mp({'boundedBy': bb, 'grid': g})[0] != 200]
    report('5.3-8', not fails and not ex_fail, f'不合法參數 {len(MAP_BAD)} 種回 400（{{status}} 格式）；user.html 4 個網格範例皆 200'
           + (f'；不符：{fails} {ex_fail}' if fails or ex_fail else ''))


def m_4():
    if os.environ.get('STEP5_STAT') != '1':
        report('5.3-9', None, '加 -e STEP5_STAT=1 才檢查（會寫 SearchStat）')
        return
    res = []
    for loc, fn, params in [('api_dataset', ds, {'limit': 1}),
                            ('api_map', mp, {'boundedBy': '122,23,121,22', 'grid': '1'})]:
        before = SearchStat.objects.filter(search_location=loc).count()
        fn(params, stat=True)
        fn(params)    # from_example=1
        time.sleep(5)
        res.append((loc, SearchStat.objects.filter(search_location=loc).count() - before))
    report('5.3-9', all(n == 1 for _, n in res), f'各寫 1 筆 SearchStat、from_example=1 不寫：{res}')


# ===================== 5.4 partner =====================

def pt(params, stat=False):
    return call(v2.partner, '/api/v2/partner', params, stat)


def p_expected():
    """Partner 表直接算：每個 tbia_partner_id 一筆，依最早的 Partner.id 排序"""
    from manager.models import Partner
    out = {}
    for pk, pid, title in Partner.objects.exclude(tbia_partner_id__isnull=True).order_by('id').values_list('id', 'tbia_partner_id', 'title'):
        out.setdefault(str(pid), title)
    return out


def p_1():
    exp = p_expected()
    code, b = pt({'limit': 1000})
    got = {d['tbiaPartnerID']: d['partnerName'] for d in b['data']}
    ok = (code == 200 and set(b) == {'status', 'meta', 'links', 'data'} and b['meta']['total'] == len(exp)
          and all(list(d) == ['tbiaPartnerID', 'partnerName'] for d in b['data'])
          and len(got) == len(b['data']) and got == exp and list(got) == list(exp) and b['links']['next'] is None)
    report('5.4-1', ok, f'結構、每筆 2 欄、{len(got)} 個夥伴單位與 Partner 表一致（ID 不重複、名稱為 title、依建立順序、GBIF 不列）')


def p_2():
    # 其他 API 用到的 tbiaPartnerID 都查得到
    code, b = pt({'limit': 1000})
    ids = {d['tbiaPartnerID'] for d in b['data']}
    r = requests.get(RECORDS_URL, params={'q': '*:*', 'rows': 0, 'facet': 'true', 'facet.field': 'tbiaPartnerID',
                                          'facet.limit': -1, 'facet.mincount': 1}, timeout=SOLR_TIMEOUT).json()
    f = r['facet_counts']['facet_fields']['tbiaPartnerID']
    solr_ids = {f[i] for i in range(0, len(f), 2)}
    ds_ids, params = set(), {'limit': 1000}
    while params is not None:
        code, d = ds(params)
        ds_ids |= {x['tbiaPartnerID'] for x in d['data'] if x['tbiaPartnerID']}
        nxt = d['links']['next']
        params = dict(parse_qsl(urlsplit(nxt).query)) if nxt else None
    miss_solr, miss_ds = solr_ids - ids, ds_ids - ids
    report('5.4-2', not miss_solr and not miss_ds,
           f'records 的 {len(solr_ids)} 個、dataset 的 {len(ds_ids)} 個 tbiaPartnerID 都在 Partner API'
           + (f'；缺：records {miss_solr} dataset {miss_ds}' if miss_solr or miss_ds else ''))


def p_3():
    exp = p_expected()
    pid, title = next(iter(exp.items()))
    code, b = pt({'tbiaPartnerID': pid})
    one = code == 200 and b['meta']['total'] == 1 and b['data'][0] == {'tbiaPartnerID': pid, 'partnerName': title}
    word = '博物館' if any('博物館' in t for t in exp.values()) else title[:2]
    n_exp = sum(1 for t in exp.values() if word in (t or ''))
    n = pt({'partnerName': word})[1]['meta']['total']
    zero = pt({'tbiaPartnerID': 'not-a-partner'})[1]['meta']['total']
    # 分頁：limit 整除與不整除都走完，不重複、沒有空頁
    pages_ok = []
    for lim in sorted({next((k for k in range(2, len(exp)) if len(exp) % k == 0), len(exp)), 5}):
        params, got, empty = {'limit': lim}, [], 0
        while params is not None and len(got) <= len(exp) + lim:
            code, b = pt(params)
            got += [d['tbiaPartnerID'] for d in b['data']]
            empty += not b['data']
            nxt = b['links']['next']
            params = dict(parse_qsl(urlsplit(nxt).query)) if nxt else None
        pages_ok.append((lim, got == list(exp) and empty == 0))
    report('5.4-3', one and n == n_exp and zero == 0 and all(o for _, o in pages_ok),
           f'tbiaPartnerID 完全比對 1 筆：{one}；partnerName={word}：{n} / 預期 {n_exp}；不存在的 ID 0 筆；'
           f'分頁（limit, 正確）：{pages_ok}')


def p_4():
    bad = [({'limit': '0'}, 'limit=0'), ({'cursor': 'abc'}, '不合法 cursor'),
           ({'tbiaPartnerID': ['a', 'b']}, 'tbiaPartnerID 重複帶不同值')]
    fails = [f'{label}→{pt(p)[0]}' for p, label in bad if pt(p)[0] != 400]
    report('5.4-4', not fails, f'不合法參數 {len(bad)} 種回 400' + (f'；不符：{fails}' if fails else ''))


def p_5():
    if os.environ.get('STEP5_STAT') != '1':
        report('5.4-5', None, '加 -e STEP5_STAT=1 才檢查（會寫 SearchStat）')
        return
    from manager.models import SearchCount
    before = SearchStat.objects.filter(search_location='api_partner').count()
    c0 = getattr(SearchCount.objects.filter(search_location='api_partner').first(), 'count', 0)
    pt({'limit': 1}, stat=True)
    pt({'limit': 1})    # from_example=1
    time.sleep(5)
    n = SearchStat.objects.filter(search_location='api_partner').count() - before
    c1 = getattr(SearchCount.objects.filter(search_location='api_partner').first(), 'count', 0)
    report('5.4-5', n == 1 and c1 - c0 == 1, f'SearchStat api_partner +{n}、SearchCount +{c1 - c0}（應各 +1，from_example=1 不寫）')


# ===================== 5.5 說明頁、JSON 404 =====================

def s_1():
    from django.test import Client
    from api import doc_v2
    c = Client()
    r2, r1 = c.get('/api/doc', HTTP_HOST=HOST), c.get('/api/doc/v1', HTTP_HOST=HOST)
    html = r2.content.decode('utf-8') if r2.status_code == 200 else ''
    missing = [f for f in API_OCCURRENCE_FIELDS + API_DATASET_FIELDS if f'<td>{f}</td>' not in html]
    v1_ok = r1.status_code == 200 and '/api/v1/occurrence' in r1.content.decode('utf-8')
    report('5.5-1', r2.status_code == 200 and not missing and 'TBIA API - V2' in html and '/api/doc/v1' in html and v1_ok,
           f'/api/doc {r2.status_code}（v2，回傳欄位都在、連到 v1）、/api/doc/v1 {r1.status_code}（v1 舊版）'
           + (f'；文件缺欄位 {missing}' if missing else ''))


def s_2():
    # 說明頁上每個範例網址實際呼叫（經過 urls.py，帶 from_example=1 不列入統計）
    from django.test import Client
    from api.doc_v2 import all_examples, example
    c, fails, n = Client(), [], 0
    for url in all_examples():
        r = c.get(example(url)[1], HTTP_HOST=HOST)
        n += 1
        body = json.loads(r.content)
        ok = r.status_code == 200 and (body.get('type') == 'FeatureCollection' if '/map' in url else body['status']['code'] == 200)
        if not ok:
            fails.append(f'{url} → {r.status_code}')
    report('5.5-2', not fails, f'說明頁範例網址 {n} 個皆回 200' + (f'；不符：{fails}' if fails else ''))


def s_3():
    from django.test import Client
    c, out = Client(), []
    for url in ['/api/v2', '/api/v2/', '/api/v2/occurrences', '/api/v2/occurrence/', '/api/v2/dataset/abc']:
        r = c.get(url, HTTP_HOST=HOST)
        try:
            code = json.loads(r.content)['status']['code']
        except (ValueError, KeyError, TypeError):
            code = None
        out.append((url, r.status_code, code))
    report('5.5-3', all(s == 404 and c_ == 404 for _, s, c_ in out),
           f'/api/v2 底下不存在的網址回 JSON 404：{out}')


def s_4():
    # 文件的來源資料庫列表涵蓋 records 實際的 sourceDatabase
    from data.utils import source_database_map
    r = requests.get(RECORDS_URL, params={'q': '*:*', 'rows': 0, 'facet': 'true', 'facet.field': 'sourceDatabase',
                                          'facet.limit': -1, 'facet.mincount': 1}, timeout=SOLR_TIMEOUT).json()
    f = r['facet_counts']['facet_fields']['sourceDatabase']
    actual = {f[i] for i in range(0, len(f), 2)}
    listed = set(source_database_map)
    report('5.5-4', actual <= listed, f'文件列 {len(listed)} 個來源資料庫，records 實際 {len(actual)} 個'
           + (f'；文件缺 {actual - listed}' if actual - listed else '')
           + (f'；文件多列（目前沒有資料）{listed - actual}' if listed - actual else ''))


ONLY = [x.strip() for x in os.environ.get('STEP5_ONLY', '').split(',') if x.strip()]


def want(sec):
    return not ONLY or sec in ONLY


if want('5.2'):
    run('5.1-1', c_5_1)
    run('5.2-1~3', c_1)
    run('5.2-4', c_4)
    run('5.2-5', c_5)
    run('5.2-6', c_6)
    run('5.2-7', c_7)
    run('5.2-8', c_8)
    run('5.2-9', c_9)
    key, temp = find_key()
    try:
        run('5.2-10', lambda: c_10(key))
    finally:
        if temp:
            APIkey.objects.filter(key=key).delete()
    run('5.2-11', c_11)

if want('5.3'):
    run('5.3-1', d_1)
    run('5.3-2', d_2)
    run('5.3-3', d_3)
    run('5.3-4', d_4)
    run('5.3-5', d_5)
    run('5.3-6', m_1)
    run('5.3-7', m_2)
    run('5.3-8', m_3)
    run('5.3-9', m_4)

if want('5.4'):
    run('5.4-1', p_1)
    run('5.4-2', p_2)
    run('5.4-3', p_3)
    run('5.4-4', p_4)
    run('5.4-5', p_5)

if want('5.5'):
    run('5.5-1', s_1)
    run('5.5-2', s_2)
    run('5.5-3', s_3)
    run('5.5-4', s_4)

counts = {}
for _, s in RESULTS:
    counts[s] = counts.get(s, 0) + 1
print('合計：' + '、'.join(f'{k} {v}' for k, v in sorted(counts.items())))
