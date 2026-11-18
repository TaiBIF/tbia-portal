# 步驟 4（4.1 / 4.2 / 4.4）程式化檢查：測試站 portal-v2 用，直接呼叫後台統計的 view、查 Solr / DB
# 用法（在 ~/tbia-portal-v2）：
#   docker compose -f staging-v2.yml exec -T web-v2 python manage.py shell < scripts/v2_migration/check_step4.py > /tmp/check_step4.txt 2>&1
# 選項（exec 後加 -e，例 exec -T -e STEP4_MONTHLY=1 web-v2 ...）：
#   STEP4_MONTHLY=1  重跑 STAT_YEAR_MONTH（預設 2026-10）的 monthly_stat，與重跑前（正式站複本、舊程式算的）逐項比對；會改寫 portal-v2 DB 該月統計
#   STEP4_MATCH=1    重跑 stat_match <同月份> --no-mail，檢查寫入新名稱、列數不變；不寄信
#   STAT_YEAR_MONTH  指定月份（預設 2026-10）
# 不加選項時只讀不寫。每項印 PASS / FAIL / SKIP / INFO，編號對應交接文件「4.1 測試清單」「4.2 / 4.4 測試清單」
import json
import os
import runpy
import traceback
from collections import Counter, defaultdict

import requests
from django.conf import settings
from django.core.management import call_command
from django.test import RequestFactory

from conf.settings import RECORDS_URL, RECORDS_V1_URL, SOLR_TIMEOUT
from data.search_params import SOURCE_DATABASE_RENAME, to_source_database
from manager.models import (Partner, DataStat, TaxonStat, UserDownloadStat, MatchStat, MatchReport,
                            SearchStat, SearchQuery, KeywordStat, Ark)
import manager.views as mv
import api.views as av

OLD_NAMES = set(SOURCE_DATABASE_RENAME) | {'觀塘生態保育網'}
YM = os.environ.get('STAT_YEAR_MONTH', '2026-10')
RF = RequestFactory()
RESULTS = []


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


def call(view, **params):
    resp = view(RF.get('/x', params))
    return json.loads(resp.content)


def facet(url, field, q='*:*'):
    r = requests.get(url, params={'q': q, 'rows': 0, 'facet': 'true', 'facet.field': field,
                                  'facet.limit': -1, 'facet.mincount': 1}, timeout=SOLR_TIMEOUT)
    r.raise_for_status()
    d = r.json()
    f = d['facet_counts']['facet_fields'][field]
    return d['response']['numFound'], {f[i]: f[i + 1] for i in range(0, len(f), 2)}


def v1_by_new_name(q='*:*'):
    """v1 core 的 rightsHolder 筆數，名稱換成新名稱後合併"""
    total, counts = facet(RECORDS_V1_URL, 'rightsHolder', q)
    merged = Counter()
    for k, v in counts.items():
        merged[to_source_database(k)] += v
    return total, merged


def renamed_units():
    """有改名的來源資料庫（新名稱），加一個未改名的對照"""
    _, v2 = facet(RECORDS_URL, 'sourceDatabase')
    names = [n for n in SOURCE_DATABASE_RENAME.values() if n in v2]
    plain = next((n for n in sorted(v2) if n not in SOURCE_DATABASE_RENAME.values()), None)
    return names, plain


# ===================== 4.1 系統管理員後台 =====================

def c_1_1():
    total, v2 = facet(RECORDS_URL, 'sourceDatabase')
    v1_total, v1 = v1_by_new_name()
    old = [n for n in v2 if n in OLD_NAMES]
    diff = {k: (v1.get(k), v2.get(k)) for k in set(v1) | set(v2) if v1.get(k) != v2.get(k)}
    r = call(mv.get_system_stat)
    pie = sum(d['y'] for d in r['data_total'])
    ok = not old and not diff and total == v1_total and pie == total
    report('4.1-1.1', ok, f'資料筆數：v2 {total:,} / v1 {v1_total:,}，圓餅圖加總 {pie:,}，舊名稱 {old or "無"}，'
                          f'各來源資料庫差異 {diff or "無"}')
    _, img2 = facet(RECORDS_URL, 'sourceDatabase', 'associatedMedia:*')
    _, img1 = v1_by_new_name('associatedMedia:*')
    img_pie = sum(d['y'] for d in r['image_data_total'])
    idiff = {k: (img1.get(k), img2.get(k)) for k in set(img1) | set(img2) if img1.get(k) != img2.get(k)}
    report('4.1-1.1b', not idiff and img_pie == sum(img2.values()),
           f'影像筆數：圓餅圖加總 {img_pie:,}，與 v1 差異 {idiff or "無"}')


def c_1_2():
    r = call(mv.get_system_stat)
    total, _ = facet(RECORDS_URL, 'sourceDatabase')
    v1_total, _ = facet(RECORDS_V1_URL, 'rightsHolder')
    v1_no, _ = facet(RECORDS_V1_URL, 'rightsHolder', '-taxonID:*')
    ok = r['has_taxon'] + r['no_taxon'] == total
    report('4.1-1.2', ok, f'TaiCOL 對應：有對到 {r["has_taxon"]:,} + 未對到 {r["no_taxon"]:,} = {r["has_taxon"] + r["no_taxon"]:,}'
                          f'（總數 {total:,}）；v1 未對到 {v1_no:,}（重新比對造成的差異屬預期）')


def c_1_3():
    r = call(mv.get_system_stat)
    names = [row[0] for row in r['db_quality_stat']]
    old = [n for n in names if n in OLD_NAMES]
    report('4.1-1.3', not old and len(names) > 0, f'資料品質：{len(names)} 個來源資料庫，舊名稱 {old or "無"}')


def c_1_4():
    names, plain = renamed_units()
    problems = []
    for n in names + ([plain] if plain else []):
        for view, params in [(mv.get_taxon_group_stat, {}),
                             (mv.get_data_stat, {'year': YM[:4], 'type': 'data'}),
                             (mv.get_temporal_stat, {'where': 'system'}),
                             (mv.get_user_download_stat, {'year': YM[:4], 'type': 'role'})]:
            try:
                r = call(view, rights_holder=n, **params)
            except Exception as e:
                problems.append(f'{n} {view.__name__}：{e}')
                continue
            if view is mv.get_taxon_group_stat and not any(sum(s['data']) for s in r['taxon_group_stat']):
                problems.append(f'{n} 類群全為 0')
            if view is mv.get_data_stat and not any(sum(s['data']) for s in r['data']):
                problems.append(f'{n} 資料累積 {YM[:4]} 全為 0')
            if view is mv.get_temporal_stat and not any(sum(s['data']) for s in r['year_data']):
                problems.append(f'{n} 時間空缺全為 0')
    report('4.1-1.4', not problems, f'下拉選單（{len(names)} 個改名單位＋{plain}）：{problems or "類群 / 資料累積 / 時間空缺都有數字"}')
    # 使用者類型、被查詢 / 被下載 / 敏感（歷史 DataStat）在 4.4 檢查


def c_1_5():
    d = settings.TAXON_STAT_DIR
    names, _ = renamed_units()
    missing = []
    for n in names + ['total']:
        for g in ['鳥類', '魚類', '被子植物']:
            if not os.path.exists(os.path.join(d, f'{n}_{g}.csv')):
                missing.append(f'{n}_{g}.csv')
    url_ok = settings.TAXON_STAT_URL.rstrip('/').endswith(os.path.basename(d.rstrip('/')))
    report('4.1-1.5', not missing and url_ok, f'類群 CSV：目錄 {d}、網址 {settings.TAXON_STAT_URL}；缺少 {missing or "無"}')


def c_1_6():
    r = call(mv.get_system_stat)
    old = [x['rights_holder'] for x in r['top3_taxon_list'] + r['top5_family_list'] if x['rights_holder'] in OLD_NAMES]
    report('4.1-1.6', not old, f'前三類群 / 前五科：{len(r["top3_taxon_list"])} / {len(r["top5_family_list"])} 個來源資料庫，舊名稱 {old or "無"}')


def c_1_7():
    d = settings.SEARCH_STAT_DIR
    url_ok = settings.SEARCH_STAT_URL.rstrip('/').endswith(os.path.basename(d.rstrip('/')))
    report('4.1-1.7', url_ok and 'search_stat_v2' in d, f'查詢參數統計：目錄 {d}、網址 {settings.SEARCH_STAT_URL}（開發期應為 search_stat_v2）')


def c_1_8():
    units = [u for p in Partner.objects.all() for u in mv._partner_units(p)]
    old = [u['name'] for u in units if u['name'] in OLD_NAMES]
    report('4.1-1.8', not old, f'學名比對下拉：{len(units)} 個資料庫，舊名稱 {old or "無"}')


# ===================== 4.1 夥伴後台 =====================

def c_2():
    names, plain = renamed_units()
    problems, info = [], []
    _, v1 = v1_by_new_name()
    for n in names + ([plain] if plain else []):
        p = next((p for p in Partner.objects.all() for i in (p.info or []) if to_source_database(i.get('dbname')) == n), None)
        if not p:
            info.append(f'{n} 沒有對應的 Partner')
            continue
        dbname = next(i.get('dbname') for i in p.info if to_source_database(i.get('dbname')) == n)
        r_new = call(mv.get_partner_stat, rights_holder=n)
        r_old = call(mv.get_partner_stat, rights_holder=dbname)  # 舊網址 / migration 前的 dbname 也要一樣
        cnt = r_new['data_total'][0]['y'] if r_new['data_total'] else None
        if cnt != v1.get(n):
            problems.append(f'{n} 筆數 {cnt} ≠ v1 {v1.get(n)}')
        if r_new['data_total'] != r_old['data_total']:
            problems.append(f'{n} 新舊名稱參數結果不同')
        if r_new['has_taxon'] + r_new['no_taxon'] != cnt:
            problems.append(f'{n} TaiCOL 對應加總不符')
        match_log = os.path.join(settings.MEDIA_ROOT, r_new['download_url'].replace('/media/', '', 1)) if r_new['download_url'] else ''
        if not (match_log and os.path.exists(match_log)):
            info.append(f'{n} match_log 連結 {r_new["download_url"] or "空"}（檔案不存在時屬正常）')
        if not any(s.get('taiwanPercentage') for s in r_new['taxon_group_stat'] if s['name'].endswith('-單位')):
            problems.append(f'{n} 佔 TaiCOL 臺灣物種數全為 0')
    report('4.1-2', not problems, f'夥伴後台（{len(names)} 個改名單位＋{plain}）：{problems or "筆數與 v1 相同、新舊名稱參數一致"}')
    if info:
        report('4.1-2i', 'info', '；'.join(info))


# ===================== 4.1 資料概況 =====================

def c_3():
    r = call(mv.get_taxon_group_stat, rights_holder='total')
    ok = any(sum(s['data']) for s in r['taxon_group_stat'])
    t = call(mv.get_temporal_stat, group='total')
    ok2 = any(sum(s['data']) for s in t['year_data'])
    missing = [g for g in ['鳥類', '魚類'] if not os.path.exists(os.path.join(settings.TAXON_STAT_DIR, f'total_{g}.csv'))]
    report('4.1-3', ok and ok2 and not missing, f'資料概況：類群 {"有" if ok else "無"}數字、時間空缺 {"有" if ok2 else "無"}數字、total CSV 缺少 {missing or "無"}')


# ===================== 4.1 monthly_stat（選項） =====================

def snapshot_month():
    data = {(d.type, d.rights_holder): str(d.count) for d in
            DataStat.objects.filter(year_month=YM).exclude(type='data')}
    uds = {(u.type, u.option, u.rights_holder): u.count for u in UserDownloadStat.objects.filter(year_month=YM)}
    kw = sorted(KeywordStat.objects.filter(year_month=YM).values_list('keyword', 'count'))
    data_rows = DataStat.objects.filter(year_month=YM, type='data').count()
    return data, uds, kw, data_rows


def c_4():
    if not os.environ.get('STEP4_MONTHLY'):
        report('4.1-4', None, '未設 STEP4_MONTHLY=1')
        return
    os.environ['STAT_YEAR_MONTH'] = YM
    before = snapshot_month()
    v1_zip = os.path.join('/tbia-volumes/media/search_stat', f'tbia_search_stat_{YM[:4]}_{YM[5:]}.zip')
    v1_mtime = os.path.getmtime(v1_zip) if os.path.exists(v1_zip) else None
    runpy.run_path(os.path.join(settings.BASE_DIR, 'scripts/system/monthly_stat.py'))
    after = snapshot_month()
    runpy.run_path(os.path.join(settings.BASE_DIR, 'scripts/system/monthly_stat.py'))
    again = snapshot_month()

    ark = Ark.objects.filter(created__contains=YM, type='data').count()
    b_data = {k: v for k, v in before[0].items() if k[0] != 'ark'}
    a_data = {k: v for k, v in after[0].items() if k[0] != 'ark'}
    diff = {k: (b_data.get(k), a_data.get(k)) for k in set(b_data) | set(a_data) if b_data.get(k) != a_data.get(k)}
    report('4.1-4.2', not diff, f'{YM} DataStat 與重跑前（舊程式結果）相同：差異 {diff or "無"}')
    udiff = {k: (before[1].get(k), after[1].get(k)) for k in set(before[1]) | set(after[1]) if before[1].get(k) != after[1].get(k)}
    report('4.1-4.3', not udiff, f'{YM} UserDownloadStat 與重跑前相同：差異 {udiff or "無"}')
    a_ark = after[0].get(('ark', None))
    report('4.1-4.4', str(a_ark) == str(ark), f'ARK：重跑後 {a_ark}、Ark 表 {ark}、重跑前（舊程式）{before[0].get(("ark", None))}')
    report('4.1-4.5', after == again and before[3] == after[3],
           f'可重跑：兩次結果{"相同" if after == again else "不同"}；type=data {before[3]} → {after[3]} 列')
    v2_zip = os.path.join(settings.SEARCH_STAT_DIR, f'tbia_search_stat_{YM[:4]}_{YM[5:]}.zip')
    v1_same = v1_mtime == (os.path.getmtime(v1_zip) if os.path.exists(v1_zip) else None)
    report('4.1-4.6', os.path.exists(v2_zip) and v1_same, f'{v2_zip} {"存在" if os.path.exists(v2_zip) else "不存在"}；v1 search_stat {"未改動" if v1_same else "被改動"}')
    report('4.2-3', before[2] == after[2], f'{YM} 關鍵字前十名與重跑前{"相同" if before[2] == after[2] else f"不同：{before[2]} → {after[2]}"}')


def c_5():
    if not os.environ.get('STEP4_MATCH'):
        report('4.1-5', None, '未設 STEP4_MATCH=1')
        return
    n_before = MatchStat.objects.filter(year_month=YM).count()
    call_command('stat_match', YM, '--no-mail')
    qs = MatchStat.objects.filter(year_month=YM)
    old = list(qs.filter(rights_holder__in=OLD_NAMES).values_list('rights_holder', flat=True).distinct())
    old_r = list(MatchReport.objects.filter(year_month=YM, rights_holder__in=OLD_NAMES).values_list('rights_holder', flat=True))
    report('4.1-5.1', not old and not old_r, f'stat_match {YM}：MatchStat {n_before} → {qs.count()} 列，舊名稱 {old + old_r or "無"}')


# ===================== 4.4 migration =====================

def c_44_1():
    old = []
    for p in Partner.objects.all():
        old += [i.get('dbname') for i in (p.info or []) if i.get('dbname') in OLD_NAMES]
    cpc = [i.get('dbname') for p in Partner.objects.filter(group='cpc') for i in (p.info or [])]
    report('4.4-1.1', not old, f'Partner dbname 舊名稱 {old or "無"}；cpc {cpc}')
    r = json.loads(av.partner_info(RF.get('/api/partner-info')).content)
    items = r['data']
    dbnames = [d['dbname'] for x in items for d in x.get('databases', [])]
    old_api = [n for n in dbnames if n in OLD_NAMES]
    report('4.4-1.4', not old_api and bool(dbnames), f'/api/partner-info：{len(dbnames)} 個資料庫，舊名稱 {old_api or "無"}')


def c_44_2():
    rows = {}
    for M in (DataStat, UserDownloadStat, TaxonStat, MatchStat, MatchReport):
        rows[M.__name__] = M.objects.filter(rights_holder__in=OLD_NAMES).count()
    for M, fields in ((SearchStat, ['stat']), (SearchQuery, ['stat', 'sensitive_stat'])):
        for f in fields:
            rows[f'{M.__name__}.{f}'] = sum(M.objects.filter(**{f'{f}__contains': [{'val': o}]}).count() for o in OLD_NAMES)
    bad = {k: v for k, v in rows.items() if v}
    report('4.4-2.1', not bad, f'舊名稱殘留：{bad or "全部 0"}')


def c_44_3():
    keys = Counter(TaxonStat.objects.values_list('type', 'year', 'month', 'name', 'rights_holder'))
    dup = [k for k, v in keys.items() if v > 1]
    report('4.4-2.2', not dup, f'TaxonStat 重複列：{len(dup)}' + (f'，例 {dup[:3]}' if dup else ''))
    d = settings.TAXON_STAT_DIR
    old_csv = [f for f in os.listdir(d) if any(f.startswith(f'{o}_') for o in OLD_NAMES)] if os.path.isdir(d) else []
    report('4.4-2.3', not old_csv, f'{d} 舊名稱 CSV：{old_csv or "無"}')


def c_44_4():
    names, _ = renamed_units()
    empty = []
    for n in names:
        for t in ['search', 'download', 'search_times', 'download_times']:
            if not DataStat.objects.filter(rights_holder=n, type=t).exists():
                empty.append(f'{n}/{t}')
        if not UserDownloadStat.objects.filter(rights_holder=n).exists():
            empty.append(f'{n}/使用者類型')
    report('4.4-2.4', 'info', f'改名單位沒有歷史統計的項目（該單位本來就沒被查詢 / 下載時屬正常）：{empty or "無"}')


for no, fn in [('4.1-1.1', c_1_1), ('4.1-1.2', c_1_2), ('4.1-1.3', c_1_3), ('4.1-1.4', c_1_4), ('4.1-1.5', c_1_5),
               ('4.1-1.6', c_1_6), ('4.1-1.7', c_1_7), ('4.1-1.8', c_1_8), ('4.1-2', c_2), ('4.1-3', c_3),
               ('4.4-1', c_44_1), ('4.4-2', c_44_2), ('4.4-3', c_44_3), ('4.4-4', c_44_4),
               ('4.1-4', c_4), ('4.1-5', c_5)]:
    run(no, fn)

print('\n== 摘要 ==')
print(Counter(s for _, s in RESULTS))
for no, s in RESULTS:
    if s == 'FAIL':
        print('FAIL', no)
