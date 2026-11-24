# 步驟 3（3.3 / 3.4）程式化檢查：測試站用，直接查 Solr / DB，不寄信、不建立 ARK、不改任何既有資料
# 用法（在 portal 目錄）：
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/check_step3.py > /tmp/check_step3.txt 2>&1
#   大量下載計時（約 100 萬筆，數分鐘）另外開：在上面的指令前加 STEP3_BIG=1，並把 exec 改成 exec -T -e STEP3_BIG=1
# 產生的暫存檔都在 /tmp/step3_check，結束時刪除；Django 測試用的登入 session 會留在 session 表（無害，會自然過期）
# 每項結果印 PASS / FAIL / SKIP，對應交接文件「3.3 / 3.4 測試清單」的編號
import csv
import io
import os
import re
import shutil
import time
import traceback
import zipfile

import requests
from django.conf import settings
from django.http import QueryDict
from django.test import Client

from conf.settings import RECORDS_URL, SOLR_TIMEOUT, MEDIA_ROOT
from data.fields import DOWNLOAD_FIELDS, RESTRICTED_OVERRIDE, UNSORTABLE_KEYS, map_occurrence
from data.utils import (
    create_search_query, solr_csv_to_zip, download_fl, download_fl_with_sensitive, download_cols,
    get_partner_name_map, get_partner_name, create_data_detail, records_sort, normalize_search_params,
    canonical_query_string, parse_query_string, create_query_display, if_raw_map,
)
from data.search_params import normalize_pairs
from manager.models import SearchQuery, User, Partner, Ark

TMP = '/tmp/step3_check'
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


def solr(params):
    r = requests.get(RECORDS_URL, params=params, timeout=SOLR_TIMEOUT)
    r.raise_for_status()
    return r.json()


def read_zip_csv(path):
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        text = z.read(name).decode('utf-8')
    rows = list(csv.reader(io.StringIO(text)))
    return rows[0], rows[1:]


def host():
    for h in settings.ALLOWED_HOSTS:
        if h != '*':
            return h.lstrip('.')
    return 'localhost'


def client(user=None):
    c = Client(HTTP_HOST=host())
    if user:
        c.force_login(user)
    return c


def partner_user():
    """有權限（取得原始值）的單位帳號"""
    for u in User.objects.filter(is_partner_account=True, partner__is_collaboration=False).order_by('id'):
        if if_raw_map(u.id):
            return u
    return None


os.makedirs(TMP, exist_ok=True)
print('=== 步驟 3 檢查開始 ===')


# ---------- 1.3 敏感申請：一個單位通過、一個不通過（同 generate_sensitive_csv 的兩段查詢） ----------
def check_sensitive_partial():
    facets = solr({'q': 'raw_location_rpt:*', 'rows': 0, 'facet': 'true', 'facet.field': 'group', 'facet.mincount': 1})
    groups = facets['facet_counts']['facet_fields']['group'][::2]
    if len(groups) < 2:
        return report('1.3', None, '模糊化資料不到兩個單位')
    pass_g, fail_g = groups[0], groups[1]
    base_raw = create_search_query(QueryDict('record_type=occ'), get_raw_map=True) + ['raw_location_rpt:*', f'group:({pass_g} OR {fail_g})']
    base_pub = create_search_query(QueryDict('record_type=occ'), get_raw_map=False) + ['raw_location_rpt:*', f'group:({pass_g} OR {fail_g})']
    q1 = {'query': '*:*', 'offset': 0, 'limit': 300, 'filter': base_raw + [f'-(group:{fail_g})'], 'fields': download_fl_with_sensitive}
    q2 = {'query': '*:*', 'offset': 0, 'limit': 300, 'filter': base_pub + [f'(group:{fail_g})'], 'fields': download_fl}
    csv_path, zip_path, pub_path = f'{TMP}/s.csv', f'{TMP}/s.zip', f'{TMP}/s_public.zip'
    assert solr_csv_to_zip([q1, q2], csv_path, zip_path, out_cols=download_cols, public_zip_path=pub_path), '產檔失敗'
    head, rows = read_zip_csv(zip_path)
    phead, prows = read_zip_csv(pub_path)
    errs = []
    if head != DOWNLOAD_FIELDS or phead != DOWNLOAD_FIELDS:
        errs.append('表頭不是 77 欄 v2')
    if any(c.startswith('raw') for c in head):
        errs.append('有 raw 欄位')
    if any(len(r) != len(head) for r in rows + prows):
        errs.append('有列的欄位數和表頭不同')
    # 逐列對照 Solr 的公開值與原始值
    idx = {c: i for i, c in enumerate(head)}
    ids = [r[idx['tbiaID']] for r in rows]
    docs = {}
    for i in range(0, len(ids), 100):
        part = ids[i:i + 100]
        d = solr({'q': '*:*', 'fq': 'id:(' + ' OR '.join(f'"{x}"' for x in part) + ')', 'rows': 100,
                  'fl': 'id,group,decimalLatitude,rawDecimalLatitude'})
        docs.update({x['id']: x for x in d['response']['docs']})
    n_pass = n_fail = 0
    for r, pr in zip(rows, prows):
        doc = docs.get(r[idx['tbiaID']])
        if not doc:
            continue
        pub = '' if doc.get('decimalLatitude') is None else str(doc['decimalLatitude'])
        raw = '' if doc.get('rawDecimalLatitude') is None else str(doc['rawDecimalLatitude'])
        got, got_pub = r[idx['decimalLatitude']], pr[idx['decimalLatitude']]
        if doc['group'] == pass_g:
            n_pass += 1
            if raw and float(got or 'nan') != float(raw):
                errs.append(f'通過單位 {doc["id"]} 不是原始值')
        else:
            n_fail += 1
            if (got or '') != '' and pub and float(got) != float(pub):
                errs.append(f'不通過單位 {doc["id"]} 不是公開值')
        if (got_pub or '') != '' and pub and float(got_pub) != float(pub):
            errs.append(f'公開版 {doc["id"]} 不是公開值')
    if not n_pass or not n_fail:
        errs.append(f'兩段資料筆數不足（通過 {n_pass}、不通過 {n_fail}）')
    report('1.3', not errs, f'通過單位 {pass_g} {n_pass} 筆、不通過單位 {fail_g} {n_fail} 筆；' + ('；'.join(errs[:5]) or '欄位對齊、取值正確、公開版正確'))


# ---------- 1.5 約 100 萬筆下載計時（STEP3_BIG=1 才跑） ----------
def check_big_download():
    if os.environ.get('STEP3_BIG') != '1':
        return report('1.5', None, '未設定 STEP3_BIG=1，略過')
    f = solr({'q': '*:*', 'rows': 0, 'facet': 'true', 'facet.field': 'sourceDatabase', 'facet.limit': -1})['facet_counts']['facet_fields']['sourceDatabase']
    pairs = list(zip(f[::2], f[1::2]))
    name, count = min(pairs, key=lambda p: abs(p[1] - 1_000_000))
    q = {'query': '*:*', 'offset': 0, 'limit': 2140000000, 'filter': [f'sourceDatabase:"{name}"'], 'fields': download_fl_with_sensitive}
    t = time.time()
    ok = solr_csv_to_zip([q], f'{TMP}/big.csv', f'{TMP}/big.zip', out_cols=download_cols, public_zip_path=f'{TMP}/big_public.zip')
    t_new = time.time() - t
    q_old = dict(q, fields=download_fl)
    t = time.time()
    solr_csv_to_zip([q_old], f'{TMP}/big_raw.csv', f'{TMP}/big_raw.zip')   # 不轉換、不寫公開版，作為對照
    t_raw = time.time() - t
    report('1.5', ok, f'{name} {count:,} 筆：v2 下載（含逐列轉換與公開版）{t_new:.0f} 秒；只串接 Solr 輸出 {t_raw:.0f} 秒；'
                      f'差 {t_new - t_raw:.0f} 秒（{count / max(t_new, 1):,.0f} 列/秒）')


# ---------- 2.1 永久保存用公開版 ----------
def check_ark_public():
    from manager.views import generate_storage_csv
    for sq in SearchQuery.objects.filter(type='record', status='pass').order_by('-id')[:200]:
        pub = os.path.join(MEDIA_ROOT, 'download', 'record_public', f'tbia_{sq.query_id}.zip')
        if os.path.exists(pub):
            ark = 'step3check'
            out = os.path.join(MEDIA_ROOT, 'download', 'storage', f'tbia_{ark}.zip')
            try:
                generate_storage_csv(sq.query_id, ark)
                same = open(out, 'rb').read() == open(pub, 'rb').read()
            finally:
                if os.path.exists(out):
                    os.remove(out)
            return report('2.1', same, f'query_id={sq.query_id}：保存檔{"與公開版相同" if same else "與公開版不同"}')
    report('2.1', None, '找不到有公開版的下載（請先用單位帳號下載一次）')


# ---------- 2.2 / 2.3 ARK 申請擋下（只送會被擋的請求，不會建立 ARK） ----------
def check_ark_block():
    sq = SearchQuery.objects.filter(type='record').order_by('-id').first()
    other = User.objects.exclude(id=sq.user_id).order_by('id').first()
    r = client(other).post('/submit_apply_ark', {'query_id': sq.query_id}, secure=True)
    ok = r.status_code == 200 and '找不到' in r.json().get('message', '')
    report('2.3', ok, f'別人的 query_id：{r.json().get("message")}')
    ark = Ark.objects.filter(type='data').order_by('-id').first()
    sq2 = SearchQuery.objects.filter(id=ark.model_id).first() if ark else None
    if not sq2:
        return report('2.2', None, '沒有已申請過 ARK 的下載')
    r = client(sq2.user).post('/submit_apply_ark', {'query_id': sq2.query_id}, secure=True)
    msg = r.json().get('message', '')
    report('2.2', r.status_code == 200 and bool(msg), f'重複申請：{msg}')


# ---------- 3.x 詳細頁、夥伴單位、不可排序 ----------
def check_detail():
    pu = partner_user()
    if not pu:
        return report('3.1-3.2', None, '找不到有權限的單位帳號')
    d = solr({'q': 'raw_location_rpt:* AND rawVerbatimLatitude:*', 'fq': f'group:{pu.partner.group}', 'rows': 1, 'fl': 'id,rawVerbatimLatitude,tbiaPartnerID'})
    docs = d['response']['docs']
    if not docs:
        return report('3.1-3.2', None, f'{pu.partner.group} 沒有模糊化且有原始 verbatim 座標的資料')
    doc = docs[0]
    row, _, _ = create_data_detail(doc['id'], pu.id, 'occ')
    anon, _, _ = create_data_detail(doc['id'], 0, 'occ')
    errs = []
    if not row.get('partnerName'):
        errs.append('沒有 partnerName')
    if str(row.get('verbatimLatitude')) != str(doc['rawVerbatimLatitude']):
        errs.append('有權限時 verbatim 不是原始值')
    if anon.get('verbatimLatitude') not in ('', None):
        errs.append('未登入時 verbatim 應為空')
    report('3.1-3.2', not errs, f'{doc["id"]}：' + ('；'.join(errs) or f'夥伴單位「{row.get("partnerName")}」，verbatim 依權限顯示正確'))
    zh, en = get_partner_name_map('zh'), get_partner_name_map('en')
    pid = doc.get('tbiaPartnerID')
    report('3.3', bool(pid and en.get(pid)), f'英文名稱：{en.get(pid)}（中文：{zh.get(pid)}）')
    g = solr({'q': 'group:gbif', 'rows': 1, 'fl': 'id'})['response']['docs']
    if g:
        grow, _, _ = create_data_detail(g[0]['id'], 0, 'occ')
        report('3.1', not grow.get('partnerName'), 'GBIF 紀錄的夥伴單位為空' if not grow.get('partnerName') else f'GBIF 不應有夥伴單位：{grow.get("partnerName")}')
    ok = 'partnerName' in UNSORTABLE_KEYS and records_sort('partnerName', 'asc', False, map_occurrence) is None
    report('3.5', ok, '夥伴單位不可排序（後端）；前端三個搜尋頁與資料集詳細頁的標題請在瀏覽器確認')


# ---------- 4.x 資料集 ----------
def check_dataset():
    c = client()
    r = c.post('/get_conditional_dataset', {'limit': 10, 'page': 1, 'orderby': 'sourceDatabase', 'sort': 'desc'}, secure=True)
    data = r.json()
    rows = data.get('rows', [])
    errs = []
    if r.status_code != 200 or not rows:
        errs.append(f'列表失敗 {r.status_code}')
    elif not all('partnerName' in x and 'sourceDatabase' in x for x in rows):
        errs.append('列表缺 partnerName / sourceDatabase')
    if rows:
        name = rows[0]['sourceDatabase']
        r2 = c.post('/get_conditional_dataset', {'limit': 10, 'page': 1, 'sourceDatabase': name}, secure=True).json()
        if not r2.get('rows') or any(x['sourceDatabase'] != name for x in r2['rows']):
            errs.append(f'來源資料庫篩選結果不對（{name}）')
    report('4.1-4.2', not errs, '；'.join(errs) or f'列表 {data.get("count")} 筆，依來源資料庫排序與篩選正常')
    r = c.post('/download_dataset_results', {'orderby': 'name', 'sort': 'asc'}, secure=True)
    text = r.content.decode('utf-8')
    rows = list(csv.reader(io.StringIO(text)))
    head = rows[0] if rows else []
    expect = ['datasetName', 'sourceDatabase', 'tbiaPartnerID', 'partnerName', 'tbiaDatasetID', 'datasetID', 'gbifDatasetID',
              'resourceContacts', 'occurrenceCount', 'datasetDateStart', 'datasetDateEnd', 'resourceCitationIdentifier',
              'datasetPublisher', 'datasetLicense', 'datasetTaxonGroup', 'created', 'modified']
    i_c = head.index('created') if 'created' in head else None
    bad_date = [x[i_c] for x in rows[1:] if i_c is not None and x[i_c] and not re.fullmatch(r'\d{8} \d{6}', x[i_c])]
    i_pn = head.index('partnerName') if 'partnerName' in head else None
    has_pn = sum(1 for x in rows[1:] if i_pn is not None and x[i_pn])
    ok = head == expect and not bad_date and has_pn > 0
    report('4.4', ok, f'表頭{"正確" if head == expect else "不符：" + ",".join(head)}；{len(rows) - 1} 筆，partnerName 有值 {has_pn} 筆；created 格式錯誤 {len(bad_date)} 筆')
    tid = rows[1][head.index('tbiaDatasetID')] if len(rows) > 1 and 'tbiaDatasetID' in head else None
    if tid:
        r = c.get(f'/dataset/{tid}/', secure=True)
        report('4.3', r.status_code == 200, f'詳細頁 /dataset/{tid}/ 狀態 {r.status_code}（logo、連結請在瀏覽器確認）')


# ---------- 5.x / 6.x 搜尋參數 ----------
PAIRS = [
    # (舊寫法, v2 寫法)：兩者的 Solr 筆數必須相同
    ('record_type=occ&rightsHolder=科博典藏 (NMNS Collection)', 'record_type=occ&sourceDatabase=科博典藏'),
    ('record_type=occ&has_image=image', 'record_type=occ&hasMedia=true&mediaType=image'),
    ('record_type=occ&has_image=y', 'record_type=occ&hasMedia=true&mediaType=image&mediaType=video&mediaType=audio'),
    ('record_type=occ&has_image=n', 'record_type=occ&hasMedia=false'),
    ('record_type=occ&is_native=n', 'record_type=occ&nativeness=naturalized&nativeness=invasive&nativeness=cultured'),
    ('record_type=occ&is_protected=y', 'record_type=occ&protectedStatus=I,II,III,CHPA'),
    ('record_type=occ&habitat=is_marine', 'record_type=occ&taxonGroupByHabitat=marine'),
    ('record_type=occ&taxonRank=sub', 'record_type=occ&taxonRank=Infraspecies'),
    ('record_type=occ&taxonGroup=Insects', 'record_type=occ&taxonGroup=甲蟲類,蛾類,蝶類,蜻蛉類,其他昆蟲'),
    ('record_type=occ&start_date=2024-01-01&end_date=2024-01-31', 'record_type=occ&eventDate=20240101,20240131'),
    ('record_type=occ&start_date=2024-01-01', 'record_type=occ&eventDate=20240101,*'),
    ('record_type=occ&geo_type=circle&center_lat=25.03&center_lon=121.56&circle_radius=3', 'record_type=occ&circle=121.56,25.03,3'),
    ('record_type=col&preservation=浸液', 'record_type=col&preparations=浸液'),
]


def count(qs):
    fq = create_search_query(QueryDict(qs), get_raw_map=False)
    return solr({'q': '*:*', 'rows': 0, 'fq': fq})['response']['numFound']


def check_param_counts():
    errs, lines = [], []
    for old, new in PAIRS:
        a, b = count(old), count(new)
        lines.append(f'{new}={b:,}')
        if a != b:
            errs.append(f'{old}（{a:,}）≠ {new}（{b:,}）')
        if b == 0:
            print(f'       （提醒）{new} 查無資料，這組比對沒有意義，可換條件再測')
    report('5.1', not errs, '；'.join(errs) or '舊寫法與 v2 筆數一致：' + '、'.join(lines))
    a = count('record_type=occ&mediaType=image,audio')
    b = count('record_type=occ&mediaType=image') + count('record_type=occ&mediaType=audio')
    report('5.4', a <= b and a >= max(count('record_type=occ&mediaType=image'), count('record_type=occ&mediaType=audio')),
           f'影像＋音檔聯集 {a:,}（各別相加 {b:,}）')
    n25 = normalize_search_params(QueryDict('circle=121.56,25.03,25')).get('circle')
    n26 = normalize_search_params(QueryDict('circle=121.56,25.03,25.01')).get('circle')
    report('5.5', n25 and not n26, '半徑 25 接受、25.01 移除（11/24 上限改回 25）')


def check_redirects():
    """不用 follow：轉址目標是相對網址，test client 跟過去時不會帶 secure，可能讓訊息 cookie 沒送出；這裡每一步都明確用 https"""
    c = client()
    cases = [
        ('/search/occurrence?rightsHolder=科博典藏 (NMNS Collection)&has_image=y&is_native=n&taxonRank=sub&start_date=2024-01-01&page=1', []),
        ('/search/occurrence?is_protected=n&taxonGroup=鳥類&page=1', ['是否為保育類：否']),
        ('/search/collection?typeStatus=模式&typeStatus=一般&page=1', ['標本類型：模式', '標本類型：一般']),
    ]
    errs = []
    for url, notices in cases:
        r = c.get(url, secure=True)
        if r.status_code != 302:
            errs.append(f'{url} 沒有轉址（{r.status_code}）')
            continue
        loc = r['Location']
        target = QueryDict(loc.split('?', 1)[1] if '?' in loc else '')
        if not target or normalize_search_params(target).urlencode() != target.urlencode():
            errs.append(f'轉址後不是 v2：{loc}')
        r2 = c.get(loc, secure=True)
        if r2.status_code != 200:
            errs.append(f'{loc} 狀態 {r2.status_code}')
            continue
        # shell 裡沒有 setup_test_environment，r2.context 會是 None，直接看 HTML 的提示框
        html = r2.content.decode('utf-8', 'ignore')
        warn = ' '.join(re.findall(r'<li>(.*?)</li>', html.split('common-search-warning-pop', 1)[1].split('</ul>', 1)[0])) if 'common-search-warning-pop' in html else ''
        for n in notices:
            if n not in warn:
                errs.append(f'{url} 頁面沒有提示「{n}」（拿到的提示：{warn or "無"}）')
        r3 = c.get(loc, secure=True)
        if r3.status_code != 200:
            errs.append(f'v2 網址再開一次應直接顯示，狀態 {r3.status_code}')
    report('6.1-6.2', not errs, '；'.join(errs) or '舊網址都轉成 v2、停用條件有提示、v2 網址不再轉址')

    # 只測後端：轉址函式有沒有把提示放進 messages（排除 test client cookie 的影響）
    from django.test import RequestFactory
    from django.contrib.sessions.middleware import SessionMiddleware
    from django.contrib.messages.middleware import MessageMiddleware
    from django.contrib import messages as dj_messages
    from data.views import redirect_to_v2_params
    req = RequestFactory().get('/search/occurrence', {'is_protected': 'n', 'typeStatus': '模式', 'page': '1'})
    SessionMiddleware(lambda r: None).process_request(req)
    MessageMiddleware(lambda r: None).process_request(req)
    resp = redirect_to_v2_params(req)
    msgs = [str(m) for m in dj_messages.get_messages(req) if 'common_search' in m.tags]
    ok = resp is not None and resp.status_code == 302 and any('是否為保育類：否' in m and '標本類型：模式' in m for m in msgs)
    report('6.2（後端）', ok, f'轉址 {resp and resp.status_code}，messages：{msgs}')


def check_canonical():
    post = QueryDict('record_type=occ&name=鳥&sourceDatabase=GBIF&hasMedia=true&mediaType=image&limit=10&page=1&orderby=x'
                     '&sort=asc&from=search&csrfmiddlewaretoken=t&selected_col=a&user_affiliation=a1&from_full=yes&lang=zh-hant')
    s = canonical_query_string(post)
    bad = [k for k in ('limit', 'page', 'orderby', 'sort', 'from=', 'csrf', 'selected_col', 'user_', 'from_full', 'lang') if k in s]
    report('7.5', not bad, f'存檔字串：{s}' + (f'；不應出現 {bad}' if bad else ''))
    recent = SearchQuery.objects.order_by('-id')[:30]
    junk = [sq.id for sq in recent if any(k in (sq.query or '') for k in ('limit=', 'csrfmiddlewaretoken', 'user_affiliation', 'has_image='))]
    print(f'       （參考）最近 30 筆 SearchQuery 含舊參數的 id：{junk}，3.4 部署後新建的應該都沒有）')


# ---------- 7.x 後台顯示 ----------
def check_manager_display():
    errs = []
    n = 0
    for sq in SearchQuery.objects.order_by('-id')[:2000]:
        try:
            create_query_display(parse_query_string(sq.query))
            n += 1
        except Exception as e:
            errs.append(f'{sq.id}: {e}')
    report('7.1', not errs, f'最近 {n} 筆下載紀錄條件顯示無錯誤' + ('；' + '；'.join(errs[:5]) if errs else ''))
    stopped = [sq for sq in SearchQuery.objects.filter(query__contains='is_protected=n').exclude(status='expired')]
    bad = [sq.id for sq in stopped if '已停用' not in create_query_display(parse_query_string(sq.query))]
    report('7.2', None if not stopped else not bad, f'未過期的非保育類下載 {len(stopped)} 筆' + (f'，未標示已停用：{bad}' if bad else '，都有標示已停用'))
    full = [sq for sq in SearchQuery.objects.filter(type='record').order_by('-id')[:2000] if parse_query_string(sq.query).get('keyword')]
    report('7.3', None if not full else True, f'最近 2000 筆中全站搜尋下載 {len(full)} 筆，會以「全站搜尋」顯示（畫面請在後台確認）')


def check_param_stat():
    import data.search_param_stat as sps
    old_dir = sps.OUTPUT_DIR
    sps.OUTPUT_DIR = TMP
    try:
        month = time.strftime('%Y-%m')
        ok = sps.build_month_zip(month)
        if not ok:
            return report('7.7', None, f'{month} 沒有搜尋紀錄')
        path = os.path.join(TMP, f'tbia_search_stat_{month.replace("-", "_")}.zip')
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            text = ''.join(z.read(n).decode('utf-8-sig') for n in names)
        rows = list(csv.reader(io.StringIO(text)))
        web = [r for r in rows if r and r[0] in ('occ', 'col')]
        old_keys = {r[1] for r in web} & {'has_image', 'is_native', 'is_protected', 'rightsHolder', 'datasetName', 'habitat', 'start_date', 'higherTaxa'}
        geo = sorted({r[1] for r in web if r[1].startswith('geo_type:')})
        report('7.7', not old_keys, f'{month}：網站搜尋參數 {"沒有舊名稱" if not old_keys else "仍有舊名稱 " + str(old_keys)}；空間統計項 {geo}')
    finally:
        sps.OUTPUT_DIR = old_dir


# ---------- 8.x TBN 共同規格 ----------
def check_common():
    from data.common_search import tbia_to_common, common_to_tbia, parse_common_query
    common, ok_list, ng_list = tbia_to_common(QueryDict(
        'record_type=occ&name=臺灣獼猴&nativeness=native&protectedStatus=I,II,III,CHPA&eventDate=20240101,*&circle=121.5,23.5,2'))
    expect = {'taxon_name', 'is_native', 'is_protected', 'event_date_from', 'circle'}
    errs = [] if expect <= set(common) else [f'TBIA→TBN 缺 {expect - set(common)}']
    common2, _, ng2 = tbia_to_common(QueryDict('nativeness=native,invasive&protectedStatus=I'))
    if 'is_native' in common2 or 'is_protected' in common2:
        errs.append('部分原生性 / 保育類不應對應')
    params, warnings, perrs = parse_common_query('taxon_name=臺灣獼猴&is_native=y&is_protected=n&event_date_to=2024-01-31')
    pairs, removed, _ = normalize_pairs(common_to_tbia(params))
    d = dict(pairs)
    if d.get('eventDate') != '*,20240131' or d.get('nativeness') != 'native' or removed != ['是否為保育類：否']:
        errs.append(f'TBN→TBIA 轉換不對：{pairs} {removed}')
    report('8.1-8.2', not errs, '；'.join(errs) or '兩個方向的參數對應正確（畫面上的條件清單請在瀏覽器確認）')


for no, fn in [('1.3', check_sensitive_partial), ('1.5', check_big_download), ('2.1', check_ark_public),
               ('2.2-2.3', check_ark_block), ('3.x', check_detail), ('4.x', check_dataset),
               ('5.x', check_param_counts), ('6.x', check_redirects), ('7.5', check_canonical),
               ('7.1-7.3', check_manager_display), ('7.7', check_param_stat), ('8.x', check_common)]:
    run(no, fn)

shutil.rmtree(TMP, ignore_errors=True)
print('=== 結果 ===')
for no, status in RESULTS:
    print(f'{status:4} {no}')
print('完成')