# 每月更新後台儀表板統計
from manager.models import *
import urllib.parse
import pandas as pd
from django.utils import timezone
import dateutil.relativedelta
from data.utils import rights_holder_map

# 先找出前一個月
now = timezone.now()
current_year_month = now + dateutil.relativedelta.relativedelta(months=-1)
current_year_month = current_year_month.strftime('%Y-%m')

# 每月最常被搜尋的10個關鍵字

ss = SearchStat.objects.filter(search_location='full', created__contains=current_year_month)
stat_list = []
for s in ss:
    query_dict = urllib.parse.parse_qs(s.query)
    if query_dict.get('keyword'):
        for k in query_dict.get('keyword'):
            stat_list.append({'keyword': k})

stat_df = pd.DataFrame(stat_list)
stat_df = stat_df.groupby(['keyword']).size().reset_index(name='count').sort_values(['count'], ascending=[False])

# 只存每個月的前十名
for v in stat_df.values[:10]:
    KeywordStat.objects.create(
        keyword = v[0],
        year_month = current_year_month,
        count = v[1],
    )


# 每月名錄下載次數
    
sq = SearchQuery.objects.filter(type='taxon', created__contains=current_year_month)

# for v in stat_df.values:
ChecklistStat.objects.create(
    year_month = current_year_month,
    count = len(sq),
)


# 每月資料被查詢
# 在stat裡面會有total的筆數

ss = SearchStat.objects.filter(created__contains=current_year_month)
stat_list = []
for s in ss:
    if s.stat:
        for sst in s.stat:
            stat_list.append({'count': sst['count'], 'rights_holder': sst['val']})

if len(stat_list):
    stat_df = pd.DataFrame(stat_list)
    stat_df = stat_df.groupby(['rights_holder'], as_index=False).sum().sort_values(['count'], ascending=[False])

    for s in stat_df.to_dict('records'):
        if s['rights_holder'] in rights_holder_map.keys():
            group = rights_holder_map[s['rights_holder']]
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = group,
                rights_holder= s['rights_holder'],
                type = 'search'
            )
        elif s['rights_holder'] == 'total':
            # 全部
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = 'total',
                rights_holder= 'total',
                type = 'search'
            )


# 每月資料被下載
# 在stat裡面會有total的筆數

ss = SearchQuery.objects.filter(type='record',created__contains=current_year_month)
stat_list = []
for s in ss:
    if s.stat:
        for sst in s.stat:
            stat_list.append({'count': sst['count'], 'rights_holder': sst['val']})

if len(stat_list):
    stat_df = pd.DataFrame(stat_list)
    stat_df = stat_df.groupby(['rights_holder'], as_index=False).sum().sort_values(['count'], ascending=[False])
    for s in stat_df.to_dict('records'):
        if s['rights_holder'] in rights_holder_map.keys():
            group = rights_holder_map[s['rights_holder']]
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = group,
                rights_holder= s['rights_holder'],
                type = 'download'
            )
        elif s['rights_holder'] == 'total':
            # 全部
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = 'total',
                rights_holder= 'total',
                type = 'download'
            )




# search_times
# 每月累積被查詢次數

ss = SearchStat.objects.filter(created__contains=current_year_month)
# 在stat裡面會有total的筆數

stat_list = []
for s in ss:
    if s.stat:
        for sst in s.stat:
            stat_list.append({'year_month': current_year_month, 'rights_holder': sst['val']})

if len(stat_list):
    stat_df = pd.DataFrame(stat_list)
    stat_df = stat_df.groupby(['year_month','rights_holder']).size().reset_index(name='count').sort_values('year_month')

    for s in stat_df.to_dict('records'):
        if s['rights_holder'] in rights_holder_map.keys():
            group = rights_holder_map[s['rights_holder']]
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = group,
                rights_holder= s['rights_holder'],
                type = 'search_times'
            )
        elif s['rights_holder'] == 'total':
            # 全部
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = 'total',
                rights_holder= 'total',
                type = 'search_times'
            )



# ('download_times', '累積被下載次數'),

ss = SearchQuery.objects.filter(type='record',created__contains=current_year_month)
# 在stat裡面會有total的筆數

stat_list = []
for s in ss:
    if s.stat:
        for sst in s.stat:
            stat_list.append({'rights_holder': sst['val'], 'year_month': current_year_month})

if len(stat_list):
    stat_df = pd.DataFrame(stat_list)
    stat_df = stat_df.groupby(['rights_holder', 'year_month']).size().reset_index(name='count').sort_values('year_month')
    for s in stat_df.to_dict('records'):
        if s['rights_holder'] in rights_holder_map.keys():
            group = rights_holder_map[s['rights_holder']]
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = group,
                rights_holder= s['rights_holder'],
                type = 'download_times'
            )
        elif s['rights_holder'] == 'total':
            # 全部
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = 'total',
                rights_holder= 'total',
                type = 'download_times'
            )

# ('sensitive', '累積敏感資料被下載筆數'),


ss = SearchQuery.objects.filter(type__in=['sensitive','record'],created__contains=current_year_month)
# 在stat裡面會有total的筆數

stat_list = []
for s in ss:
    if s.sensitive_stat:
        for sst in s.sensitive_stat:
            # if sst['val'] in rights_holder_map.keys():
            stat_list.append({'rights_holder': sst['val'],'count': sst['count'],'year_month': current_year_month})

if len(stat_list):
    stat_df = pd.DataFrame(stat_list)
    stat_df = stat_df.groupby(['rights_holder', 'year_month'], as_index=False).sum().sort_values('year_month')
    for s in stat_df.to_dict('records'):
        if s['rights_holder'] in rights_holder_map.keys():
            group = rights_holder_map[s['rights_holder']]
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = group,
                rights_holder= s['rights_holder'],
                type = 'sensitive'
            )
        elif s['rights_holder'] == 'total':
            DataStat.objects.create(
                year_month = current_year_month,
                count = s['count'],
                group = 'total',
                rights_holder= 'total',
                type = 'sensitive'
            )


# 使用者統計

ss = SearchQuery.objects.filter(type__in=['record','taxon'], created__contains=current_year_month)

stat_list = []
for s in ss:
    if s.user_stat and s.stat:
        for option in s.user_stat:
            for sst in s.stat:
                stat_list.append({
                    'option': option,
                    'rights_holder': sst['val']
                })

if len(stat_list):
    stat_df = pd.DataFrame(stat_list)
    stat_df = stat_df.groupby(['option', 'rights_holder']).size().reset_index(name='count')
    for s in stat_df.to_dict('records'):
        option = s['option']
        rights_holder = s['rights_holder']
        # 判斷 type
        if option.startswith('a'):
            stat_type = 'affiliation'
        elif option.startswith('b'):
            stat_type = 'role'
        elif option.startswith('c'):
            stat_type = 'purpose'
        else:
            continue
        # 判斷 group
        if rights_holder in rights_holder_map.keys():
            group = rights_holder_map[rights_holder]
        elif rights_holder == 'total':
            group = 'total'
        else:
            continue
        UserDownloadStat.objects.create(
            year_month=current_year_month,
            count=s['count'],
            type=stat_type,
            option=option,
            group=group,
            rights_holder=rights_holder,
        )


# ark
# ARK每月申請次數

ss = Ark.objects.filter(created__contains=current_year_month,type='data')
    
DataStat.objects.create(
    year_month = current_year_month,
    count = len(sq),
    type = 'ark'
)

# ============ 每月查詢參數統計(次數 + 值分佈,輸出 zip) ============
import csv
import os
import zipfile
from collections import defaultdict, Counter
from data.utils import parse_query_string, STAT_EXCLUDE_KEYS

OUTPUT_DIR = '/tbia-volumes/media/search_stat'
TOPN = 10

EXCLUDE_KEYS = STAT_EXCLUDE_KEYS | {
    'search_location',
    'get_record',
    'polygon', 'geojson_id', 'center_lat', 'center_lon', 'circle_radius', 'boundedBy',
    'geo_type',   # 本身排除,改用展開後的 geo_type:<值>
}
GEO_TYPES = ('map', 'circle', 'polygon')

year, mm = current_year_month.split('-')   # current_year_month = 'YYYY-MM'

count_data = defaultdict(int)        # (location, param) -> 次數
dist_data = defaultdict(Counter)     # (location, param) -> Counter(value -> 次數)

ss = SearchStat.objects.filter(
    created__contains=current_year_month
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

os.makedirs(OUTPUT_DIR, exist_ok=True)

# 次數 CSV
count_path = os.path.join(OUTPUT_DIR, f'tbia_search_stat_{year}_{mm}_次數.csv')
rows = [(loc, param, cnt) for (loc, param), cnt in count_data.items()]
rows.sort(key=lambda r: (r[0], -r[2], r[1]))   # location -> 次數 -> param
with open(count_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['search_location', 'param', 'count'])
    w.writerows(rows)

# 值分佈 CSV
dist_path = os.path.join(OUTPUT_DIR, f'tbia_search_stat_{year}_{mm}_值分佈.csv')
with open(dist_path, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.writer(f)
    w.writerow(['search_location', 'param', 'rank', 'value', 'count'])
    for (location, param) in sorted(dist_data.keys()):
        items = dist_data[(location, param)].most_common()
        for rank, (value, count) in enumerate(items[:TOPN], 1):
            w.writerow([location, param, rank, value, count])
        rest = items[TOPN:]
        if rest:
            w.writerow([location, param, '其他', '(其他)', sum(c for _, c in rest)])

# 打包成 zip,刪掉原始 CSV
zip_path = os.path.join(OUTPUT_DIR, f'tbia_search_stat_{year}_{mm}.zip')
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write(count_path, os.path.basename(count_path))
    zf.write(dist_path, os.path.basename(dist_path))

os.remove(count_path)
os.remove(dist_path)