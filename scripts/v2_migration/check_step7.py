# 步驟 7（7.1 欄位說明頁、下載的值以 API 為準）檢查：測試站 portal-v2 用，只讀不寫
# 用法（在 ~/tbia-portal-v2）：
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/check_step7.py > /tmp/check_step7.txt 2>&1; grep -E '^\[|合計' /tmp/check_step7.txt
# 每項印 PASS / FAIL，編號對應交接文件「7.1 測試清單」
import csv
import io
import json
import traceback

import requests
from django.conf import settings
from django.test import Client

from conf.settings import SOLR_PREFIX, RECORDS_URL, SOLR_TIMEOUT
from api.v2_params import format_occurrence
from data.field_doc import field_doc_context, DATASET_DOWNLOAD_COLUMNS, SPECIES_COLUMNS
from data.fields import DOWNLOAD_FIELDS, DOWNLOAD_SOLR_FL, SPECIES_DOWNLOAD_COLUMNS
from data.search_params import RANK_SOLR_TO_EN, NATIVENESS, PROTECTED_STATUS
from data.utils import write_download_rows, format_species_download, get_partner_name_map

RESULTS = []


def report(no, ok, msg=''):
    status = {True: 'PASS', False: 'FAIL', None: 'SKIP'}[ok]
    RESULTS.append((no, status))
    print(f'[{status}] {no} {msg}')


def run(no, fn):
    try:
        fn()
    except Exception as e:
        report(no, False, f'例外：{e}')
        traceback.print_exc()


# ---------- 7.1-1 名錄下載：taxa core 全部物種轉換後的值都在 API 詞彙內 ----------
def check_species():
    taxa_cols = ['id'] + [c for c, _ in SPECIES_DOWNLOAD_COLUMNS]
    docs, cursor = [], '*'
    while True:
        r = requests.post(f'{SOLR_PREFIX}taxa/select', timeout=SOLR_TIMEOUT, headers={'content-type': 'application/json'},
                          data=json.dumps({'query': '*:*', 'limit': 10000, 'sort': 'id asc', 'fields': taxa_cols,
                                           'params': {'cursorMark': cursor}}))
        r.raise_for_status()
        j = r.json()
        docs += j['response']['docs']
        if j['nextCursorMark'] == cursor:
            break
        cursor = j['nextCursorMark']
    rows = format_species_download(docs)
    errs = []
    bad_rank = {x['taxonRank'] for x in rows if x['taxonRank'] and x['taxonRank'] not in RANK_SOLR_TO_EN.values()}
    bad_nat = {x['nativeness'] for x in rows if x['nativeness'] and x['nativeness'] not in NATIVENESS}
    bad_pro = {x['protectedStatus'] for x in rows if x['protectedStatus'] and x['protectedStatus'] not in PROTECTED_STATUS}
    bools = [c for c in ('isEndemic', 'isFossil', 'isTerrestrial', 'isFreshwater', 'isBrackish', 'isMarine')]
    bad_bool = {x[c] for x in rows for c in bools if x[c] not in ('true', 'false', '')}
    for name, bad in [('taxonRank', bad_rank), ('nativeness', bad_nat), ('protectedStatus', bad_pro), ('布林', bad_bool)]:
        if bad:
            errs.append(f'{name} 不在 API 詞彙：{sorted(bad)[:10]}')
    for f in ('suggestedSensitiveCategory', 'citesAppendix', 'iucnCategory', 'redListCategory'):
        vals = sorted({x[f] for x in rows if x[f]})
        print(f'    {f}：{vals}')
    report('7.1-1', not errs, '；'.join(errs) or f'taxa {len(rows):,} 筆：taxonRank、nativeness、protectedStatus、布林欄位皆為 API 的值')


# ---------- 7.1-2 紀錄下載：同一批紀錄的下載 CSV 與 API v2 回傳值相同 ----------
def check_records():
    # 各階層、敏感、有夥伴單位的資料都抽一些
    queries = ['*:*', 'taxonRank:"special form" OR taxonRank:"hybrid formula"', 'taxonRank:variety',
               'sensitiveCategory:*', '-tbiaPartnerID:*']
    partner_names = get_partner_name_map('zh')
    n, diffs = 0, []
    for q in queries:
        # 與 solr_csv_to_zip 相同的查法（POST JSON 到 ?wt=csv）
        body = json.dumps({'query': q, 'limit': 200, 'sort': 'id asc', 'fields': DOWNLOAD_SOLR_FL})
        csv_resp = requests.post(f'{RECORDS_URL}?wt=csv', data=body, timeout=SOLR_TIMEOUT,
                                 headers={'content-type': 'application/json'})
        csv_resp.raise_for_status()
        out = io.StringIO()
        write_download_rows([csv_resp.content], csv.writer(out), DOWNLOAD_FIELDS)
        dl_rows = list(csv.reader(io.StringIO(out.getvalue())))
        json_resp = requests.post(RECORDS_URL, data=body, timeout=SOLR_TIMEOUT, headers={'content-type': 'application/json'})
        json_resp.raise_for_status()
        for doc, row in zip(json_resp.json()['response']['docs'], dl_rows):
            api = format_occurrence(doc, False, partner_names)
            n += 1
            for k, f in enumerate(DOWNLOAD_FIELDS):
                a = api.get(f)
                a = '' if a is None else ('true' if a is True else 'false' if a is False else str(a))
                if a != row[k]:
                    # 數值格式差異（Solr CSV 1.0 / JSON 1）不算
                    try:
                        if float(a) == float(row[k]):
                            continue
                    except ValueError:
                        pass
                    diffs.append((api.get('tbiaID'), f, a, row[k]))
    for d in diffs[:20]:
        print('    不同：', d)
    fields = sorted({d[1] for d in diffs})
    report('7.1-2', not diffs, f'{n:,} 筆、{len(DOWNLOAD_FIELDS)} 欄' + (f'，不同 {len(diffs)} 處，欄位：{fields}' if diffs else '，下載與 API 值相同'))


# ---------- 7.1-3 欄位說明頁 ----------
def check_page():
    host = next((h.lstrip('.') for h in settings.ALLOWED_HOSTS if h != '*'), 'localhost')
    c = Client(HTTP_HOST=host)
    codes = [c.get(u).status_code for u in ('/zh-hant/data-fields', '/en-us/data-fields')]
    ctx = field_doc_context()
    same = ([f['name'] for f in ctx['occurrence_fields']] == DOWNLOAD_FIELDS
            and [f['name'] for f in ctx['dataset_fields']] == DATASET_DOWNLOAD_COLUMNS
            and [f['name'] for f in ctx['species_fields']] == SPECIES_COLUMNS)
    report('7.1-3', codes == [200, 200] and same,
           f'中英文 {codes}；欄位 紀錄 {len(ctx["occurrence_fields"])} / 資料集 {len(ctx["dataset_fields"])} / 名錄 {len(ctx["species_fields"])}，順序同下載檔案：{same}')


for no, fn in [('7.1-1', check_species), ('7.1-2', check_records), ('7.1-3', check_page)]:
    run(no, fn)

print('=== 結果 ===')
for no, status in RESULTS:
    print(f'{status:4} {no}')
print(f'合計 PASS {sum(s == "PASS" for _, s in RESULTS)} / FAIL {sum(s == "FAIL" for _, s in RESULTS)}')
