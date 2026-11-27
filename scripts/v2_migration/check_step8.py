# 步驟 8（8.1 正式切換）portal 端檢查：切換後（⑥）在正式站 / 測試站的主 portal 跑，只讀不寫
# 用法：
#   正式站（~/tbia-portal）：
#     docker compose -f production.yml exec -T web python manage.py shell < scripts/v2_migration/check_step8.py > /tmp/check_step8_portal.txt 2>&1; grep -E '^\[|合計' /tmp/check_step8_portal.txt
#   測試站演練（~/tbia-portal）：把 production.yml 換成 staging.yml
# 維護模式（MAINTENANCE_MODE=True）中也可以跑：API 直接呼叫 view，不經過 middleware；只有 W9 頁面檢查會略過。
# 每項印 PASS / FAIL / SKIP / INFO，編號對應交接文件「8.1 測試清單」
import datetime
import json
import traceback

import requests
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, RequestFactory

import conf.settings as S
from api.doc_v2 import V2_RELEASE_DATE
from data.search_params import SOURCE_DATABASE_RENAME
from manager.models import Partner, DataStat, UserDownloadStat, TaxonStat, MatchStat, MatchReport
import api.v2 as v2
import api.views as av

RESULTS = []
RF = RequestFactory()
HOST = next((h for h in S.ALLOWED_HOSTS if h and '*' not in h and not h.startswith('.')), 'localhost')
OLD_NAMES = set(SOURCE_DATABASE_RENAME)


def report(no, ok, msg=''):
    status = {True: 'PASS', False: 'FAIL', None: 'SKIP', 'info': 'INFO'}[ok]
    RESULTS.append((no, status))
    print(f'[{status}] {no} {msg}')


def run(no, fn):
    try:
        fn()
    except Exception as e:
        report(no, False, f'例外：{type(e).__name__}: {e}')
        traceback.print_exc()


def core_of(url):
    return url.rstrip('/').split('/')[-2]


def solr_fields(core):
    r = requests.get(f'{S.SOLR_PREFIX}{core}/schema/fields', params={'wt': 'json'}, timeout=S.SOLR_TIMEOUT)
    r.raise_for_status()
    return {f['name'] for f in r.json()['fields']}


def solr_count(url):
    r = requests.get(url, params={'q': '*:*', 'rows': 0, 'wt': 'json'}, timeout=S.SOLR_TIMEOUT)
    r.raise_for_status()
    return r.json()['response']['numFound']


def solr_facet(url, field):
    r = requests.get(url, timeout=S.SOLR_TIMEOUT, params={'q': '*:*', 'rows': 0, 'wt': 'json', 'facet': 'true',
                                                         'facet.field': field, 'facet.limit': -1, 'facet.mincount': 1})
    r.raise_for_status()
    f = r.json()['facet_counts']['facet_fields'][field]
    return {f[i]: f[i + 1] for i in range(0, len(f), 2)}


def call(view, path, params):
    params = dict(params, from_example='1')   # 不列入統計
    resp = view(RF.get(path, params, HTTP_HOST=HOST))
    return resp.status_code, json.loads(resp.content)


# ---------- W1 設定值為上線值（上線 .env 檢查表） ----------
def w1():
    want = {
        'RECORDS_CORE': (S.RECORDS_CORE, 'tbia_records'),
        'RECORDS_V1_CORE': (S.RECORDS_V1_CORE, 'tbia_records_v1'),
        'TW_GRID_CORE': (S.TW_GRID_CORE, 'tw_grid'),
        'TAXON_STAT_DIR': (S.TAXON_STAT_DIR.rstrip('/'), '/tbia-volumes/media/taxon_stat'),
        'SEARCH_STAT_DIR': (S.SEARCH_STAT_DIR.rstrip('/'), '/tbia-volumes/media/search_stat'),
    }
    bad = {k: v for k, (v, d) in want.items() if v != d}
    report('8.1-W1', not bad, f'portal .env 沒有開發期的值（不同：{bad or "無"}）')
    report('8.1-W1b', 'info', f"MAINTENANCE_MODE={S.env('MAINTENANCE_MODE', default='')}、HOST={HOST}")


# ---------- W2 core：v2 / v1 schema、筆數一致 ----------
def w2():
    v2c, v1c = core_of(S.RECORDS_URL), core_of(S.RECORDS_V1_URL)
    f2, f1 = solr_fields(v2c), solr_fields(v1c)
    n2, n1 = solr_count(S.RECORDS_URL), solr_count(S.RECORDS_V1_URL)
    ok = ('tbiaPartnerID' in f2 and 'rightsHolder' not in f2 and 'rightsHolder' in f1 and 'tbiaPartnerID' not in f1
          and n2 == n1 and n2 > 0)
    report('8.1-W2', ok, f'{v2c} 為 v2、{v1c} 為 v1；筆數 {n2:,} / {n1:,}')
    ft = solr_fields(core_of(S.TW_GRID_URL))
    report('8.1-W2b', 'sourceDatabase' in ft, f'{core_of(S.TW_GRID_URL)} 為 v2（有 sourceDatabase 欄位）')


# ---------- W3 migration 全部套用 ----------
def w3():
    ex = MigrationExecutor(connection)
    plan = ex.migration_plan(ex.loader.graph.leaf_nodes())
    pending = [f'{m.app_label}.{m.name}' for m, _ in plan]
    applied = ex.loader.applied_migrations
    need = [('manager', '0098_partner_dbname_v2'), ('manager', '0099_stat_source_database_v2'),
            ('manager', '0100_search_location_api_partner'), ('api', '0003_alter_apikey_status')]
    missing = [f'{a}.{n}' for a, n in need if (a, n) not in applied]
    report('8.1-W3', not pending and not missing, f'未套用的 migration：{pending or "無"}；v2 必要的缺 {missing or "無"}')


# ---------- W4 Partner：dbname 新名稱、ID、對得到資料 ----------
def w4():
    facet = solr_facet(S.RECORDS_URL, 'sourceDatabase')
    old, no_data, no_id = [], [], []
    for p in Partner.objects.all():
        if p.group != 'gbif' and not p.tbia_partner_id:
            no_id.append(p.group)
        for i in (p.info or []):
            name = i.get('dbname')
            if name in OLD_NAMES:
                old.append(f'{p.group}:{name}')
            elif name and name not in facet:
                no_data.append(f'{p.group}:{name}')
    report('8.1-W4', not old and not no_id, f'Partner.info.dbname 舊名稱 {old or "無"}；沒有 tbia_partner_id {no_id or "無"}')
    report('8.1-W4b', 'info', f'dbname 在 tbia_records 沒有資料（例：臺灣生命大百科屬正常）：{no_data or "無"}')


# ---------- W5 歷史統計沒有舊名稱（0099） ----------
def w5():
    left = {}
    for M in (DataStat, UserDownloadStat, TaxonStat, MatchStat, MatchReport):
        n = M.objects.filter(rights_holder__in=OLD_NAMES).count()
        if n:
            left[M.__name__] = n
    report('8.1-W5', not left, f'統計表 rights_holder 舊名稱殘留：{left or "無"}')


# ---------- W6 API v2 / v1 ----------
def w6():
    code, b = call(v2.occurrence, '/api/v2/occurrence', {'limit': 1})
    n2 = solr_count(S.RECORDS_URL)
    doc = (b.get('data') or [{}])[0]
    ok = code == 200 and b['meta']['total'] == n2 and 'sourceDatabase' in doc and 'tbiaPartnerID' in doc
    report('8.1-W6', ok, f'v2 occurrence HTTP {code}，total {b.get("meta", {}).get("total")} / Solr {n2:,}')


def w6b():
    code, b = call(av.occurrence, '/api/v1/occurrence', {'limit': 1})
    n1 = solr_count(S.RECORDS_V1_URL)
    doc = (b.get('data') or [{}])[0]
    ok = code == 200 and b['meta']['total'] == n1 and 'rightsHolder' in doc and 'sourceDatabase' not in doc
    report('8.1-W6b', ok, f'v1 occurrence HTTP {code}，total {b.get("meta", {}).get("total")} / Solr {n1:,}，欄位為 v1')


def w6c():
    for no, view, path, params in [('8.1-W6c', v2.dataset, '/api/v2/dataset', {'limit': 1}),
                                   ('8.1-W6d', v2.partner, '/api/v2/partner', {'limit': 1}),
                                   ('8.1-W6e', v2.map, '/api/v2/map', {'grid': '10', 'boundedBy': '122,24,121,23'})]:
        code, b = call(view, path, params)
        report(no, code == 200, f'{path} HTTP {code}')


# ---------- W7 /api/partner-info（datahub 更新用） ----------
def w7():
    resp = av.partner_info(RF.get('/api/partner-info', HTTP_HOST=HOST))
    data = json.loads(resp.content)['data']
    old = [d['group'] for d in data for i in d['databases'] if i.get('dbname') in OLD_NAMES]
    report('8.1-W7', resp.status_code == 200 and data and not old,
           f'/api/partner-info HTTP {resp.status_code}、{len(data)} 個 group、舊 dbname {old or "無"}')


# ---------- W8 API 說明頁的 V2 上線日期 ----------
def w8():
    today = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date().isoformat()
    report('8.1-W8', V2_RELEASE_DATE == today,
           f'api/doc_v2.py V2_RELEASE_DATE={V2_RELEASE_DATE}，今天 {today}（測試站演練不同日屬正常）')


# ---------- W9 主要頁面（維護模式中略過） ----------
def w9():
    if S.env('MAINTENANCE_MODE', default='') == 'True':
        report('8.1-W9', None, '維護模式中，頁面一律 503；結束維護後再跑一次')
        return
    c = Client(HTTP_HOST=HOST)
    bad = []
    for path in ['/', '/search/occurrence', '/search/collection', '/search/dataset', '/api/doc', '/api/doc/v1',
                 '/data-fields']:
        code = c.get(path).status_code
        if code != 200:
            bad.append((path, code))
    report('8.1-W9', not bad, f'主要頁面 200（不是 200：{bad or "無"}）')


for no, fn in [('8.1-W1', w1), ('8.1-W2', w2), ('8.1-W3', w3), ('8.1-W4', w4), ('8.1-W5', w5), ('8.1-W6', w6), ('8.1-W6b', w6b), ('8.1-W6c', w6c),
               ('8.1-W7', w7), ('8.1-W8', w8), ('8.1-W9', w9)]:
    run(no, fn)

n = {s: sum(1 for _, x in RESULTS if x == s) for s in ('PASS', 'FAIL', 'SKIP', 'INFO')}
print(f"合計：PASS {n['PASS']}、FAIL {n['FAIL']}、SKIP {n['SKIP']}、INFO {n['INFO']}")
