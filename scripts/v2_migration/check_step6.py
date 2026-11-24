# 步驟 6（6.1 TBN ↔ TBIA commonsearch）程式化檢查：測試站 portal-v2 用，只讀不寫
# 用法（在 ~/tbia-portal-v2）：
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/check_step6.py > /tmp/check_step6.txt 2>&1
# 每項印 PASS / FAIL，編號對應交接文件「6.1 測試清單」
import traceback
from urllib.parse import urlsplit, parse_qsl, unquote

import requests
from django.conf import settings
from django.http import QueryDict
from django.test import Client
from django.urls import reverse

from conf.settings import RECORDS_URL, SOLR_TIMEOUT
from data.common_search import (
    tbia_to_common, common_to_tbia, parse_common_query, build_common_url,
    CIRCLE_MAX_RADIUS, TBN_COMMON_SEARCH_URL,
)
from data.search_params import CIRCLE_MAX_KM, normalize_pairs
from data.utils import create_search_query, normalize_search_params

RESULTS = []
LON, LAT = 121.56, 25.03   # 臺北市中心


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


def host():
    for h in settings.ALLOWED_HOSTS:
        if h != '*':
            return h.lstrip('.')
    return 'localhost'


def solr_count(qs):
    fq = create_search_query(QueryDict(qs), get_raw_map=False)
    r = requests.get(RECORDS_URL, params={'q': '*:*', 'rows': 0, 'fq': fq}, timeout=SOLR_TIMEOUT)
    r.raise_for_status()
    return r.json()['response']['numFound']


# ---------- 6.1-1 TBIA → TBN 參數對應（回歸，同 check_step3 8.x） ----------
def check_a_direction():
    errs = []
    common, ok_list, ng_list = tbia_to_common(QueryDict(
        'record_type=occ&name=臺灣獼猴&nativeness=native&protectedStatus=I,II,III,CHPA&eventDate=20240101,*&circle=121.5,23.5,2'))
    expect = {'taxon_name', 'is_native', 'is_protected', 'event_date_from', 'circle'}
    if not expect <= set(common):
        errs.append(f'缺 {expect - set(common)}')
    if common.get('is_native') != 'y' or common.get('is_protected') != 'y':
        errs.append(f'is_native / is_protected 值不對：{common}')
    if ng_list:
        errs.append(f'不應有不可對應項目：{ng_list}')
    common2, _, ng2 = tbia_to_common(QueryDict('nativeness=native,invasive&protectedStatus=I'))
    if 'is_native' in common2 or 'is_protected' in common2 or len(ng2) != 2:
        errs.append(f'部分原生性 / 保育類應列為不可對應：{common2} {ng2}')
    common3, _, _ = tbia_to_common(QueryDict('nativeness=naturalized,invasive,cultured'))
    if common3.get('is_native') != 'n':
        errs.append(f'歸化＋入侵＋栽培豢養應對應 is_native=n：{common3}')
    report('6.1-1', not errs, '；'.join(errs) or 'TBIA→TBN 可／不可對應正確（原生性、保育類只有全選時對應）')


# ---------- 6.1-2 TBN → TBIA 參數還原（回歸） ----------
def check_b_direction():
    errs = []
    params, warnings, perrs = parse_common_query('taxon_name=臺灣獼猴&is_native=y&is_protected=n&event_date_to=2024-01-31')
    if perrs:
        errs.append(f'不應有錯誤：{perrs}')
    pairs, removed, _ = normalize_pairs(common_to_tbia(params))
    d = dict(pairs)
    if d.get('name') != '臺灣獼猴' or d.get('eventDate') != '*,20240131' or d.get('nativeness') != 'native':
        errs.append(f'條件還原不對：{pairs}')
    if removed != ['是否為保育類：否']:
        errs.append(f'is_protected=n 應被移除並提示：{removed}')
    params, _, perrs = parse_common_query('taxon_group=birds,mammals&event_date_from=2024-01')
    pairs, removed, _ = normalize_pairs(common_to_tbia(params))
    d = dict(pairs)
    groups = {g for k, v in pairs if k == 'taxonGroup' for g in v.split(',')}
    if perrs or d.get('eventDate') != '20240101,*' or groups != {'鳥類', '哺乳類'}:
        errs.append(f'類群多值 / 只填起始月不對：{pairs} {perrs}')
    report('6.1-2', not errs, '；'.join(errs) or 'TBN→TBIA 條件還原正確（is_protected=n 移除並提示、日期只填一邊）')


# ---------- 6.1-3 半徑上限 25（11/24 網站、API 改回 25，與共同規格一致） ----------
def check_radius():
    errs = []
    if not (CIRCLE_MAX_RADIUS == CIRCLE_MAX_KM == 25):
        errs.append(f'上限不一致：共同規格 {CIRCLE_MAX_RADIUS}、網站 {CIRCLE_MAX_KM}')
    for r in ('0.2', '10', '24.5', '25'):
        _, _, perrs = parse_common_query(f'circle={LON}%20{LAT}%20{r}')
        if perrs:
            errs.append(f'TBN→TBIA 半徑 {r} 應接受：{perrs}')
        common, _, ng = tbia_to_common(QueryDict(f'circle={LON},{LAT},{r}'))
        if common.get('circle') != f'{LON:.10g} {LAT:.10g} {float(r):.10g}' or ng:
            errs.append(f'TBIA→TBN 半徑 {r} 應可對應：{common} {ng}')
    for r in ('0', '-1', '25.01', '50'):
        _, _, perrs = parse_common_query(f'circle={LON}%20{LAT}%20{r}')
        if not perrs:
            errs.append(f'TBN→TBIA 半徑 {r} 應回錯誤')
    # 來回轉換：TBN 帶 25 → TBIA 網站參數保留 25（normalize 不會移除）
    params, _, _ = parse_common_query(f'circle={LON}%20{LAT}%2025')
    nq = normalize_search_params(QueryDict(build_qs(common_to_tbia(params))))
    if nq.get('circle') != f'{LON:.10g},{LAT:.10g},25':
        errs.append(f'TBN 半徑 25 轉入後網站參數不對：{nq.urlencode()}')
    # 網站已擋掉 > 25；舊網址若帶 50，normalize 會移除，不會送到 TBN
    common, _, _ = tbia_to_common(QueryDict(f'circle={LON},{LAT},50'))
    if 'circle' in common:
        errs.append(f'TBIA 半徑 50 不應帶到 TBN：{common}')
    report('6.1-3', not errs, '；'.join(errs) or '三邊上限皆 25；0.2～25 兩方向可對應；0、負值、> 25 回錯誤或不帶出')


def build_qs(pairs):
    from urllib.parse import urlencode
    return urlencode(pairs)


# ---------- 6.1-4 /commonsearch/occurrence 入口 ----------
def check_entry():
    errs = []
    c = Client(HTTP_HOST=host())
    url = reverse('commonsearch_occurrence')
    resp = c.get(f'{url}?taxon_group=birds&circle={LON}%20{LAT}%2020')
    if resp.status_code != 302:
        errs.append(f'半徑 20 應 302，實際 {resp.status_code}')
    else:
        loc = resp['Location']
        q = dict(parse_qsl(urlsplit(loc).query))
        if q.get('circle') != f'{LON:.10g},{LAT:.10g},20' or q.get('taxonGroup') != '鳥類':
            errs.append(f'轉址參數不對：{unquote(loc)}')
        page = c.get(loc, follow=True)
        if page.status_code != 200:
            errs.append(f'搜尋頁 {page.status_code}')
        warns = page.context.get('common_search_warnings') if page.context else None
        if warns:
            errs.append(f'不應有提示：{warns}')
    bad = c.get(f'{url}?circle={LON}%20{LAT}%2030')
    if bad.status_code != 400 or '25' not in bad.content.decode('utf-8'):
        errs.append(f'半徑 30 應回 400 且訊息含上限 25，實際 {bad.status_code}')
    report('6.1-4', not errs, '；'.join(errs) or '入口轉址正確（半徑 20 → 搜尋頁；30 → 400）')


# ---------- 6.1-5 搜尋頁「前往 TBN」連結（get_tbn_query） ----------
def check_tbn_link():
    errs = []
    c = Client(HTTP_HOST=host())
    resp = c.post(reverse('get_tbn_query'), {'record_type': 'occ', 'taxonGroup': '鳥類', 'circle': f'{LON},{LAT},20'})
    if resp.status_code != 200:
        errs.append(f'get_tbn_query 回 {resp.status_code}')
    else:
        data = resp.json()
        expect = build_common_url(TBN_COMMON_SEARCH_URL, {'taxon_group': 'birds', 'circle': f'{LON:.10g} {LAT:.10g} 20'})
        if f'circle={LON:.10g}%20{LAT:.10g}%2020' not in data['tbn_url']:
            errs.append(f'TBN 連結沒有半徑 20：{data["tbn_url"]}（預期類似 {expect}）')
        if data['tbn_error']:
            errs.append(f'不應有不可對應項目：{data["tbn_error"]}')
    report('6.1-5', not errs, '；'.join(errs) or '半徑 20 的條件帶進 TBN 連結，沒有不可對應項目')


# ---------- 6.1-6 Solr 實際查詢：半徑 10 / 20 / 25 ----------
def check_solr():
    n = {r: solr_count(f'record_type=occ&circle={LON},{LAT},{r}') for r in (10, 20, 25)}
    ok = 0 < n[10] <= n[20] <= n[25]
    report('6.1-6', ok, '、'.join(f'半徑 {r}：{v:,}' for r, v in n.items()) + ('' if ok else '（應 0 < 10 ≤ 20 ≤ 25）'))


for no, fn in [('6.1-1', check_a_direction), ('6.1-2', check_b_direction), ('6.1-3', check_radius),
               ('6.1-4', check_entry), ('6.1-5', check_tbn_link), ('6.1-6', check_solr)]:
    run(no, fn)

print('=== 結果 ===')
for no, status in RESULTS:
    print(f'{status:4} {no}')
print(f'合計 PASS {sum(s == "PASS" for _, s in RESULTS)} / FAIL {sum(s == "FAIL" for _, s in RESULTS)}')
