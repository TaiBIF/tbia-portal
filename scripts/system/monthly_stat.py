# 每月更新後台儀表板統計
from manager.models import *
# import json
import urllib.parse
import pandas as pd
from django.utils import timezone
# from datetime import timedelta
import dateutil.relativedelta

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
    
rights_holder_map = {
    'GBIF': 'gbif',
    '中央研究院生物多樣性中心植物標本資料庫': 'hast',
    '中央研究院生物多樣性中心動物標本館': 'asiz',
    '台灣生物多樣性網絡 TBN': 'tbri',
    '國立臺灣博物館典藏': 'ntm',
    '林業試驗所昆蟲標本館': 'fact',
    '林業試驗所植物標本資料庫': 'taif',
    '河川環境資料庫': 'wra',
    '濕地環境資料庫': 'nps',
    '生態調查資料庫系統': 'forest',
    '臺灣國家公園生物多樣性資料庫': 'nps',
    '臺灣生物多樣性資訊機構 TaiBIF': 'brcas',
    '海洋保育資料倉儲系統': 'oca',
    '科博典藏 (NMNS Collection)': 'nmns',
    '臺灣魚類資料庫': 'ascdc',
}

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
    else:
        group = 'total'
    DataStat.objects.create(
        year_month = current_year_month,
        count = s['count'],
        group = group,
        rights_holder= s['rights_holder'],
        type = 'search'
    )


# 每月資料被下載

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
        else:
            group = 'total'
        DataStat.objects.create(
            year_month = current_year_month,
            count = s['count'],
            group = group,
            rights_holder= s['rights_holder'],
            type = 'download'
        )




# search_times
# 每月累積被查詢次數

ss = SearchStat.objects.filter(created__contains=current_year_month)
stat_list = []
for s in ss:
    for sst in s.stat:
        stat_list.append({'year_month': current_year_month, 'rights_holder': sst['val']})

stat_df = pd.DataFrame(stat_list)
stat_df = stat_df.groupby(['year_month','rights_holder']).size().reset_index(name='count').sort_values('year_month')

# stat_df[stat_df.rights_holder=='total']


for s in stat_df.to_dict('records'):
    if s['rights_holder'] in rights_holder_map.keys():
        group = rights_holder_map[s['rights_holder']]
    else:
        group = 'total'
    DataStat.objects.create(
        year_month = current_year_month,
        count = s['count'],
        group = group,
        rights_holder= s['rights_holder'],
        type = 'search_times'
    )



# ('download_times', '累積被下載次數'),


ss = SearchQuery.objects.filter(type='record',created__contains=current_year_month)
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
        else:
            group = 'total'
        DataStat.objects.create(
            year_month = current_year_month,
            count = s['count'],
            group = group,
            rights_holder= s['rights_holder'],
            type = 'download_times'
        )


# ('sensitive', '累積敏感資料被下載筆數'),


ss = SearchQuery.objects.filter(type__in=['sensitive','record'],created__contains=current_year_month)
stat_list = []
for s in ss:
    if s.sensitive_stat:
        for sst in s.sensitive_stat:
            if sst['val'] in rights_holder_map.keys():
                stat_list.append({'rights_holder': sst['val'],'count': sst['count'],'year_month': current_year_month})

if len(stat_list):
    stat_df = pd.DataFrame(stat_list)
    stat_df = stat_df.groupby(['rights_holder', 'year_month'], as_index=False).sum().sort_values('year_month')
    for s in stat_df.to_dict('records'):
        if s['rights_holder'] in rights_holder_map.keys():
            group = rights_holder_map[s['rights_holder']]
        else:
            group = 'total'
        DataStat.objects.create(
            year_month = current_year_month,
            count = s['count'],
            group = group,
            rights_holder= s['rights_holder'],
            type = 'sensitive'
        )

