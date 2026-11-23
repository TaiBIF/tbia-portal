# 步驟 5（5.1 / 5.2）程式化檢查：測試站 portal-v2 用，直接呼叫 API view，結果與 Solr 直接查詢比對
# 用法（在 ~/tbia-portal-v2）：
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/check_step5.py > /tmp/check_step5.txt 2>&1
# 選項（exec 後加 -e，例 exec -T -e STEP5_TEMP_KEY=1 web-v2 ...）：
#   STEP5_TEMP_KEY=1  DB 沒有 status=pass 的 APIkey 時，暫時建一把測限制型，結束時刪除（會寫 portal-v2 DB）
#   STEP5_STAT=1      檢查第一頁會寫 SearchStat、from_example=1 不寫（會寫 portal-v2 DB 的 SearchStat / SearchCount）
# 不加選項時只讀不寫（所有呼叫都帶 from_example=1，不列入統計）。
# 每項印 PASS / FAIL / SKIP / INFO，編號對應交接文件「5.2 測試清單」
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
from data.search_params import RANK_SOLR_TO_EN
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
    report('5.2-4', len(ids) == n == len(set(ids)) and params is None,
           f'分頁：資料集 {ds} {n} 筆，{pages} 頁取回 {len(ids)} 筆、不重複，最後一頁 next 為 null')


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
    ({'circle': '121.5,23.5,51'}, 'circle 51 公里'),
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
    same('5.2-8g', 'circle 50 公里', {'circle': '121.5,23.5,50'}, '{!geofilt sfield=location_rpt pt=23.5,121.5 d=50}')
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

counts = {}
for _, s in RESULTS:
    counts[s] = counts.get(s, 0) + 1
print('合計：' + '、'.join(f'{k} {v}' for k, v in sorted(counts.items())))
