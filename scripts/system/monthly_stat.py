# 每月更新後台儀表板統計
from manager.models import *
import pandas as pd
from django.utils import timezone
import os
import dateutil.relativedelta
from data.utils import source_database_map, to_source_database, parse_query_string

# 先找出前一個月；STAT_YEAR_MONTH=YYYY-MM 可指定月份（重跑 / 驗證用）
now = timezone.now()
current_year_month = now + dateutil.relativedelta.relativedelta(months=-1)
current_year_month = os.environ.get('STAT_YEAR_MONTH') or current_year_month.strftime('%Y-%m')

# 4.1：來源資料庫一律存 v2 sourceDatabase 名稱。已存的 stat / sensitive_stat 在 4.4 migration 前有舊名稱、
# v1 API 也可能寫入舊名稱，統計前先轉新名稱（新舊名稱合併計算），再以 source_database_map 對 group
rights_holder_map = source_database_map

# 可重跑：先刪除這個月份由本程式產生的統計（DataStat 的 data 由 stat_data 產生，不刪）
KeywordStat.objects.filter(year_month=current_year_month).delete()
ChecklistStat.objects.filter(year_month=current_year_month).delete()
DataStat.objects.filter(year_month=current_year_month,
                        type__in=['search', 'download', 'search_times', 'download_times', 'sensitive', 'ark']).delete()
UserDownloadStat.objects.filter(year_month=current_year_month).delete()

# 每月最常被搜尋的10個關鍵字

ss = SearchStat.objects.filter(search_location='full', created__contains=current_year_month)
stat_list = []
for s in ss:
    # 4.2：已存字串統一用 parse_query_string 讀（相容舊格式 key=['A','B']）；全站搜尋只取 keyword，不需轉 v2
    query_dict = parse_query_string(s.query or '', normalize=False)
    for k in query_dict.getlist('keyword'):
        stat_list.append({'keyword': k})

# 該月沒有全站搜尋時 groupby 會 KeyError，整支中止（後面的統計都不會產生）
if stat_list:
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
            stat_list.append({'count': sst['count'], 'rights_holder': to_source_database(sst['val'])})

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
            stat_list.append({'count': sst['count'], 'rights_holder': to_source_database(sst['val'])})

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
            stat_list.append({'year_month': current_year_month, 'rights_holder': to_source_database(sst['val'])})

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
            stat_list.append({'rights_holder': to_source_database(sst['val']), 'year_month': current_year_month})

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
            stat_list.append({'rights_holder': to_source_database(sst['val']),'count': sst['count'],'year_month': current_year_month})

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
                    'rights_holder': to_source_database(sst['val'])
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
    count = len(ss),
    type = 'ark'
)

# ============ 每月查詢參數統計(次數 + 值分佈,輸出 zip,並更新總表) ============
from data.search_param_stat import build_month_zip, build_total_zip

build_month_zip(current_year_month)
build_total_zip()
