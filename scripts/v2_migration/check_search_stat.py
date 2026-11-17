# 檢查 search_param_stat：舊月份（v1 參數）與新月份（3.4 後 v2 參數）統計出的參數名稱是否一致、geo_type 是否有計數
# 輸出寫到 /tmp/search_stat_check，不動 media 裡的正式統計檔
import csv, io, os, zipfile
import data.search_param_stat as sps

sps.OUTPUT_DIR = '/tmp/search_stat_check'
MONTHS = os.environ.get('STAT_MONTHS', '2026-10,2026-11').split(',')
OLD_NAMES = {'rightsHolder', 'datasetName', 'higherTaxa', 'habitat', 'preservation', 'has_image', 'is_native',
             'is_protected', 'start_date', 'end_date', 'center_lat', 'center_lon', 'circle_radius'}

params = {}
for ym in MONTHS:
    if not sps.build_month_zip(ym):
        print(f'== {ym}：沒有資料'); continue
    y, m = ym.split('-')
    with zipfile.ZipFile(sps.month_zip_path(ym)) as zf:
        rows = list(csv.DictReader(io.StringIO(zf.read(f'tbia_search_stat_{y}_{m}_次數.csv').decode('utf-8-sig'))))
    web = [r for r in rows if r['search_location'] in ('occ', 'col')]
    params[ym] = {r['param'] for r in web if not r['param'].startswith('geo_type:')}
    print(f'== {ym}（網站搜尋 occ / col）')
    print('  geo_type：', [(r['search_location'], r['param'], r['count']) for r in web if r['param'].startswith('geo_type:')] or '無')
    print('  舊參數名稱：', sorted(params[ym] & OLD_NAMES) or '無')
    print('  參數：', sorted(params[ym]))

if len(params) >= 2:
    a, b = list(params)[:2]
    print(f'== 只在 {a} 出現：', sorted(params[a] - params[b]) or '無')
    print(f'== 只在 {b} 出現：', sorted(params[b] - params[a]) or '無')
