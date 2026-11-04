# 每月查詢參數統計:產出單月 zip,以及彙整全部年月的總表 zip
import csv
import glob
import io
import os
import re
import zipfile
from collections import Counter, defaultdict

from data.utils import STAT_EXCLUDE_KEYS, parse_query_string
from manager.models import SearchStat

OUTPUT_DIR = '/tbia-volumes/media/search_stat'
TOPN = 10
TOTAL_NAME = 'tbia_search_stat_total'
MONTH_ZIP_RE = re.compile(r'tbia_search_stat_(\d{4})_(\d{2})\.zip')

EXCLUDE_KEYS = STAT_EXCLUDE_KEYS | {
    'search_location',
    'get_record',
    'polygon', 'geojson_id', 'center_lat', 'center_lon', 'circle_radius', 'boundedBy',
    'geo_type',   # 本身排除,改用展開後的 geo_type:<值>
}
GEO_TYPES = ('map', 'circle', 'polygon')

COUNT_HEADER = ['search_location', 'param', 'count']
DIST_HEADER = ['search_location', 'param', 'rank', 'value', 'count']


def _csv_bytes(header, rows):
    buffer = io.StringIO(newline='')
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    return buffer.getvalue().encode('utf-8-sig')


def _write_zip(zip_path, files):
    # 先寫暫存檔再取代,避免有人下載到寫到一半的檔案
    tmp_path = f'{zip_path}.tmp'
    with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    os.replace(tmp_path, zip_path)


def _read_rows(zf, name, year, mm):
    text = zf.read(name).decode('utf-8-sig')
    reader = csv.reader(io.StringIO(text, newline=''))
    next(reader)   # 略過標題列
    return [[int(year), int(mm), *row] for row in reader]


def month_zip_path(year_month):
    year, mm = year_month.split('-')
    return os.path.join(OUTPUT_DIR, f'tbia_search_stat_{year}_{mm}.zip')


def build_month_zip(year_month):
    """產出單月 zip。year_month 格式為 YYYY-MM,該月沒有資料時不產檔並回傳 False。"""
    year, mm = year_month.split('-')

    count_data = defaultdict(int)        # (location, param) -> 次數
    dist_data = defaultdict(Counter)     # (location, param) -> Counter(value -> 次數)

    ss = SearchStat.objects.filter(
        created__contains=year_month
    ).exclude(search_location='full').values_list('search_location', 'query')

    for location, query in ss.iterator():
        location = location or ''
        qd = parse_query_string(query or '')

        # 空間查詢方式:把 geo_type 的值展開成獨立統計項
        gt = qd.get('geo_type')
        if gt in GEO_TYPES:
            count_data[(location, f'geo_type:{gt}')] += 1

        for key in qd.keys():
            if key in EXCLUDE_KEYS:
                continue
            count_data[(location, key)] += 1
            for v in qd.getlist(key):
                dist_data[(location, key)][v] += 1

    if not count_data:
        return False

    count_rows = [(loc, param, cnt) for (loc, param), cnt in count_data.items()]
    count_rows.sort(key=lambda r: (r[0], -r[2], r[1]))   # location -> 次數 -> param

    dist_rows = []
    for (location, param) in sorted(dist_data.keys()):
        items = dist_data[(location, param)].most_common()
        for rank, (value, count) in enumerate(items[:TOPN], 1):
            dist_rows.append([location, param, rank, value, count])
        rest = items[TOPN:]
        if rest:
            dist_rows.append([location, param, '其他', '(其他)', sum(c for _, c in rest)])

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    _write_zip(month_zip_path(year_month), {
        f'tbia_search_stat_{year}_{mm}_次數.csv': _csv_bytes(COUNT_HEADER, count_rows),
        f'tbia_search_stat_{year}_{mm}_值分佈.csv': _csv_bytes(DIST_HEADER, dist_rows),
    })
    return True


def build_total_zip():
    """彙整所有單月 zip 成總表,兩個 CSV 都加上 year、month 欄位。"""
    count_rows, dist_rows = [], []

    for path in sorted(glob.glob(os.path.join(OUTPUT_DIR, 'tbia_search_stat_*.zip'))):
        match = MONTH_ZIP_RE.fullmatch(os.path.basename(path))
        if not match:   # 略過總表本身
            continue
        year, mm = match.groups()
        with zipfile.ZipFile(path) as zf:
            count_rows += _read_rows(zf, f'tbia_search_stat_{year}_{mm}_次數.csv', year, mm)
            dist_rows += _read_rows(zf, f'tbia_search_stat_{year}_{mm}_值分佈.csv', year, mm)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    _write_zip(os.path.join(OUTPUT_DIR, f'{TOTAL_NAME}.zip'), {
        f'{TOTAL_NAME}_次數.csv': _csv_bytes(['year', 'month', *COUNT_HEADER], count_rows),
        f'{TOTAL_NAME}_值分佈.csv': _csv_bytes(['year', 'month', *DIST_HEADER], dist_rows),
    })
