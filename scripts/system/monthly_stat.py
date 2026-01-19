# 每月更新後台儀表板統計
from manager.models import *
# import json
import urllib.parse
import pandas as pd
from django.utils import timezone
# from datetime import timedelta
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
    for sst in s.stat:
        stat_list.append({'count': sst['count'], 'rights_holder': sst['val']})

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
            group = group,
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
                group = group,
                rights_holder= 'total',
                type = 'download'
            )




# search_times
# 每月累積被查詢次數

ss = SearchStat.objects.filter(created__contains=current_year_month)
# 在stat裡面會有total的筆數

stat_list = []
for s in ss:
    for sst in s.stat:
        stat_list.append({'year_month': current_year_month, 'rights_holder': sst['val']})

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

