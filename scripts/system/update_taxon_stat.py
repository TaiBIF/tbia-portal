import requests
import pandas as pd
from conf.settings import SOLR_PREFIX
from manager.models import TaxonStat
from numpy import nan
import json
import math
from data.utils import taxon_group_map_c
from datetime import datetime
now = datetime.now()

# 只取 year 從1900開始的
# 也有可能有 year 但沒有 month
# 這樣的話沒有month的year會被漏掉 
# 所以計算的時候 後面要再加一個 -month:*的 year facet 把 month為空值的部分考慮進去


# 以 group + rightsHolder 為單位

rights_holder_map = {
    'GBIF': 'gbif',
    '中央研究院生物多樣性中心動物標本館': 'asiz',
    '中央研究院生物多樣性中心植物標本資料庫': 'hast',
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
    'total': 'total'
}


# # 這邊改用bioGroup

# taxon_group_map = {
#     'Insects' : [{'key': 'class', 'value': 'Insecta'}],
#     'Fishes' : [{'key': 'superclass', 'value': 'Actinopterygii'},{'key': 'superclass', 'value': 'Chondrichthyes'},{'key': 'class', 'value': 'Myxini'}],
#     'Reptiles' : [{'key': 'class', 'value': 'Reptilia'}],
#     'Fungi' : [{'key': 'kingdom', 'value': 'Fungi'}],
#     'Plants' : [{'key': 'kingdom', 'value': 'Plantae'}],
#     'Birds' : [{'key': 'class', 'value': 'Aves'}],
#     'Mammals' : [{'key': 'class', 'value': 'Mammalia'}],
#     'Amphibians' : [{'key': 'class', 'value': 'Amphibia'}],
#     'Bacteria' : [{'key': 'kingdom', 'value': 'Bacteria'}],
#     'Others' : [{'key': 'class', 'value': ''}],
# }

taxon_group_map_e = {
    "昆蟲": "Insects",
    "蜘蛛": "Spiders",
    "魚類": "Fishes",
    "爬蟲類": "Reptiles",
    "兩棲類": "Amphibians",
    "鳥類": "Birds",
    "哺乳類": "Mammals",
    "維管束植物": "Vascular Plants",
    "蕨類植物": "Ferns",
    "苔蘚植物": "Mosses",
    "藻類": "Algae",
    "病毒": "Viruses",
    "細菌": "Bacteria",
    "真菌": "Fungi",
    "其他": "Others"
}



# 第一個month應該也要加上1~12的限制
# 確認一下現在 year & month 的值有哪些樣態

stat_list = []

for k in rights_holder_map.keys():
    if k == 'total':
        fq_query = ''
    else:
        fq_query = f'fq=rightsHolder:"{k}"&'
    # 1. 先計算有 year + month 的
    url = f'{SOLR_PREFIX}tbia_records/select?{fq_query}q.op=OR&q=*:*&facet.pivot=year,month&facet=true&rows=0&start=0&facet.limit=-1&facet.mincount=1'
    data = requests.get(url).json()
    for dd in data['facet_counts']['facet_pivot']['year,month']:
        now_year = dd['value']
        if dd.get('pivot'):
            for ddd in dd['pivot']:
                now_month = ddd['value']
                now_count = ddd['count']
                stat_list.append({
                    'year': int(float(now_year)),
                    'month': int(float(now_month)),
                    'count': now_count,
                    'rights_holder': k,
                    'group': rights_holder_map[k]
                })
    # 2. 再計算沒有 month 的 
    url = f'{SOLR_PREFIX}tbia_records/select?{fq_query}q=-month:*&q.op=OR&facet.field=year&facet=true&rows=0&start=0&facet.limit=-1&facet.mincount=1'
    data = requests.get(url).json()
    data = data['facet_counts']['facet_fields']['year']
    for i in range(0, len(data), 2):
        now_year = data[i]
        now_count = data[i+1]
        # print(now_year, now_count)
        stat_list.append({
                    'year': int(float(now_year)),
                    'month': 'x',
                    'count': int(float(now_count)),
                    'rights_holder': k,
                    'group': rights_holder_map[k]
                })   


stat_df = pd.DataFrame(stat_list)


stat_df = stat_df[(stat_df.month.isin([r for r in range(1,13)])) | (stat_df.month=='x') ]
stat_df = stat_df[stat_df.year.isin([r for r in range(1900, now.year + 1)])]


stat_df = stat_df.groupby(['year', 'month', 'rights_holder', 'group'], as_index=False).sum()
stat_df['type'] = 'temporal' # 時間空缺

for ss in stat_df.to_dict('records'):
    # 存在則update
    if TaxonStat.objects.filter(type=ss['type'],year=ss['year'],month=ss['month'],
                                rights_holder=ss['rights_holder'], group=ss['group']).exists():
        ts_obj = TaxonStat.objects.get(type=ss['type'],year=ss['year'],month=ss['month'],
                                rights_holder=ss['rights_holder'], group=ss['group'])
        ts_obj.count = ss['count']
        ts_obj.save()
    # 不存在則新增
    else:
        ts_obj = TaxonStat.objects.create(type=ss['type'],year=ss['year'],month=ss['month'],
                                rights_holder=ss['rights_holder'], group=ss['group'],
                                count=ss['count'])


# 以下為區分類群
# 這邊要只計算種 & 種下

taxon_stat_list = []


for tt in taxon_group_map_e.keys():
    query_list = []
    # vv_list = []
    # if tt == 'Others':
    #     for vv in taxon_group_map.keys():
    #         if vv != 'Others':
    #             for vvv in taxon_group_map[vv]:
    #                 vv_list.append(f'''-{vvv['key']}:"{vvv['value']}"''')
    # else:
    #     for vv in taxon_group_map[tt]:
    #         vv_list.append(f'''{vv['key']}:"{vv['value']}"''')
    # query_list += [" OR ".join(vv_list)]
    if tt == '其他':
        query_list += ['-bioGroup:*']
    else:
        query_list += [f'bioGroup:{tt}']
    query_list += [f'taxonRank:(species OR subspecies OR nothosubspecies OR variety OR subvariety OR nothovariety OR form OR subform OR "special form" OR race OR stirp OR morph OR aberration)']
    query_list += ['is_in_taiwan:1']
    for k in rights_holder_map.keys():
        if k != 'total':
            # query_list += [f'rightsHolder:"{k}"']
            holder_str = f'&fq=rightsHolder:"{k}"'
        else:
            holder_str = ''
        query = {
                    "offset": 0,
                    "limit": 0,
                    "filter": query_list
                }
        url = f'{SOLR_PREFIX}tbia_records/select?q=*:*&facet.pivot=year,month&facet=true&facet.limit=-1&facet.mincount=1{holder_str}'
        data = requests.post(url, data=json.dumps(query), headers={'content-type': "application/json" }).json()
        # 1. 先計算有 year + month 的
        # data = requests.get(url).json()
        for dd in data['facet_counts']['facet_pivot']['year,month']:
            now_year = dd['value']
            if dd.get('pivot'):
                for ddd in dd['pivot']:
                    now_month = ddd['value']
                    now_count = ddd['count']
                    taxon_stat_list.append({
                        'year': int(float(now_year)),
                        'month': int(float(now_month)),
                        'count': now_count,
                        'rights_holder': k,
                        'group': rights_holder_map[k],
                        'name': taxon_group_map_e[tt]
                    })
        # 2. 再計算沒有 month 的 
        url = f'{SOLR_PREFIX}tbia_records/select?q=-month:*&q.op=OR&facet.field=year&facet=true&facet.limit=-1&facet.mincount=1{holder_str}'
        data = requests.post(url, data=json.dumps(query), headers={'content-type': "application/json" }).json()
        data = data['facet_counts']['facet_fields']['year']
        for i in range(0, len(data), 2):
            now_year = data[i]
            now_count = data[i+1]
            # print(now_year, now_count)
            taxon_stat_list.append({
                        'year': int(float(now_year)),
                        'month': 'x',
                        'count': int(float(now_count)),
                        'rights_holder': k,
                        'group': rights_holder_map[k],
                        'name': taxon_group_map_e[tt]
                    })
        # 3. 再計算完全沒有考慮時間的總和
        url = f'{SOLR_PREFIX}tbia_records/select?q=*:*{holder_str}'
        data = requests.post(url, data=json.dumps(query), headers={'content-type': "application/json" }).json()
        taxon_stat_list.append({
                    'year': 'x',
                    'month': 'x',
                    'count': data['response']['numFound'],
                    'rights_holder': k,
                    'group': rights_holder_map[k],
                    'name': taxon_group_map_e[tt]
                })


taxon_stat_df = pd.DataFrame(taxon_stat_list)

taxon_stat_df = taxon_stat_df[(taxon_stat_df.month.isin([r for r in range(1,13)])) | (taxon_stat_df.month=='x')]
taxon_stat_df = taxon_stat_df[(taxon_stat_df.year.isin([r for r in range(1900, now.year + 1)])) | (taxon_stat_df.year=='x')]
taxon_stat_df = taxon_stat_df.groupby(['year', 'month', 'rights_holder', 'group', 'name'], as_index=False).sum()
taxon_stat_df['type'] = 'taxon_group'


c = 0
for ss in taxon_stat_df.to_dict('records'):
    c += 1
    if c % 100 == 0:
        print(c)
    # 存在則update
    if TaxonStat.objects.filter(type=ss['type'],year=ss['year'],month=ss['month'],
                                rights_holder=ss['rights_holder'], group=ss['group'],name=ss['name']).exists():
        ts_obj = TaxonStat.objects.get(type=ss['type'],year=ss['year'],month=ss['month'],
                                rights_holder=ss['rights_holder'], group=ss['group'], name=ss['name'])
        ts_obj.count = ss['count']
        ts_obj.save()
    # 不存在則新增
    else:
        ts_obj = TaxonStat.objects.create(type=ss['type'],year=ss['year'],month=ss['month'],
                                rights_holder=ss['rights_holder'], group=ss['group'],
                                name=ss['name'], count=ss['count'])


# 以下為區分 family
# 只需要取前五
# 用taxon group區分


# 把舊的刪除
TaxonStat.objects.filter(type='family').delete()

for r in rights_holder_map.keys():
    query = { "query": "*:*",
            "offset": 0,
            "limit": 0,
            "filter": [f'rightsHolder:"{r}"'],
            "facet": {
                "family": {
                    "type": "terms",
                    "field": "family",
                    "limit": 5,
                    "sort": 'count'
                    }
                }
            }
    response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
    if response.json()['facets'].get('count'):
        data = response.json()['facets']['family']['buckets']
        for d in data:
            if r in rights_holder_map.keys():
                group = rights_holder_map[r]
            else:
                group = r
            ts_obj = TaxonStat.objects.create(rights_holder=r,name=d['val'],type='family',count=d['count'],group=group)


# 產生名錄列表 & 台灣種比例

# 1. 先從taxa找出 is_in_taiwan=1 & taxonRank = 種和種下 & 依據各類群的篩選條件
# 2. 再從tbia_records找出 is_in_taiwan=1 & taxonRank = 種和種下 & 依據各類群的篩選條件



# query_list += [f'taxonRank:(subspecies OR nothosubspecies OR variety OR subvariety OR nothovariety OR form OR subform OR "special form" OR race OR stirp OR morph OR aberration)']

# 佔TaiCOL臺灣鳥類物種數 1% <- 單位所有階層含有鳥綱的台灣種 / TaiCOL所有階層含有鳥綱的台灣種
# type = taiwan_percentage
# 計算的時候只從上面取taxonRank=species的資料


# 可以點選文字後下載TaiCOL所有臺灣鳥類名錄，檔案中標明哪些是單位內有收錄的物種（計算的時候跟TaiCOL一樣只算到種，但是在名錄裡面會有種和種以下，另外多提供分類階層的欄位）
# csv 欄位: 學名 主要中文名 階層 所屬單位資料庫是否有收錄

taicol_df = pd.DataFrame()

# 先從taxa取得清單
for tt in taxon_group_map_e.keys():
    query_list = []
    if tt == '其他':
        query_list += ['-bioGroup:*']
    else:
        query_list += [f'bioGroup:{tt}']
    # vv_list = []
    # if tt == 'Others':
    #     for vv in taxon_group_map.keys():
    #         if vv != 'Others':
    #             for vvv in taxon_group_map[vv]:
    #                 vv_list.append(f'''-{vvv['key']}:"{vvv['value']}"''')
    # else:
    #     for vv in taxon_group_map[tt]:
    #         vv_list.append(f'''{vv['key']}:"{vv['value']}"''')
    # query_list += [" OR ".join(vv_list)]
    query_list += [f'taxonRank:(species OR subspecies OR nothosubspecies OR variety OR subvariety OR nothovariety OR form OR subform OR "special form" OR race OR stirp OR morph OR aberration)']
    query_list += ['is_in_taiwan:1']
    query = { "query": "*:*",
            "offset": 0,
            "limit": 1000000,
            "filter": query_list,
            "fields": ['id','scientificName','common_name_c','taxonRank']
            }
    response = requests.post(f'{SOLR_PREFIX}taxa/select', data=json.dumps(query), headers={'content-type': "application/json" })
    data = response.json()['response']['docs']
    df = pd.DataFrame(data)
    df['taxon_group'] = taxon_group_map_e[tt]
    taicol_df = pd.concat([taicol_df, df], ignore_index=True)


taicol_df = taicol_df.replace({nan: None})
taicol_df = taicol_df.rename(columns={'id': 'taxon_id'})


for tt in taxon_group_map_e.keys():
    for k in rights_holder_map.keys():
        query_list = []
        if k != 'total':
            query_list += [f'rightsHolder:"{k}"']
        if tt == '其他':
            query_list += ['-bioGroup:*']
        else:
            query_list += [f'bioGroup:{tt}']
        # vv_list = []
        # if tt == 'Others':
        #     for vv in taxon_group_map.keys():
        #         if vv != 'Others':
        #             for vvv in taxon_group_map[vv]:
        #                 vv_list.append(f'''-{vvv['key']}:"{vvv['value']}"''')
        # else:
        #     for vv in taxon_group_map[tt]:
        #         vv_list.append(f'''{vv['key']}:"{vv['value']}"''')
        # query_list += [" OR ".join(vv_list)]
        query_list += [f'taxonRank:(species OR subspecies OR nothosubspecies OR variety OR subvariety OR nothovariety OR form OR subform OR "special form" OR race OR stirp OR morph OR aberration)']
        query_list += ['is_in_taiwan:1']
        #  這邊應該要用facet才對
        query = { "query": "*:*",
                    "offset": 0,
                    "limit": 0,
                    "filter": query_list,
                    "facet": {
                        "taxon_id": {
                            "type": "terms",
                            "field": "taxonID",
                            "limit": -1,
                        }
                    }
                }
        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        if response.json()['facets']['count']:
            data = response.json()['facets']['taxon_id']['buckets']
            df = pd.DataFrame(data)
            df = df.rename(columns={'val': 'taxon_id'})
        else:
            df = pd.DataFrame(columns=['taxon_id','count'])
        now_taicol_df = taicol_df[(taicol_df.taxon_group==taxon_group_map_e[tt])].merge(df, how='left')
        # if taicol_len:
        taicol_len = len(now_taicol_df[(now_taicol_df.taxon_group==taxon_group_map_e[tt])&(now_taicol_df.taxonRank=='species')])
        partner_len = len(now_taicol_df[(now_taicol_df.taxonRank=='species')&(now_taicol_df['count'].notna())])
        tw_percentage = round((partner_len / taicol_len) * 100, 2)
        print(k, tt, tw_percentage)
        # 存在則update
        if TaxonStat.objects.filter(type='taiwan_percentage',
                                    rights_holder=k, 
                                    group=rights_holder_map[k],
                                    name=taxon_group_map_e[tt]).exists():
            ts_obj = TaxonStat.objects.get(type='taiwan_percentage',
                                    rights_holder=k, 
                                    group=rights_holder_map[k],
                                    name=taxon_group_map_e[tt])
            ts_obj.count = tw_percentage
            ts_obj.save()
        # 不存在則新增
        else:
            ts_obj = TaxonStat.objects.create(type='taiwan_percentage',
                                    rights_holder=k, group=rights_holder_map[k],
                                    name=taxon_group_map_e[tt], count=tw_percentage)
        # csv 欄位: 學名 主要中文名 階層 所屬單位資料庫是否有收錄
        if k == 'total':
            now_taicol_df['TBIA入口網是否有收錄'] = now_taicol_df['count'].apply(lambda x: False if math.isnan(x) else True)
            now_taicol_df = now_taicol_df[['scientificName','common_name_c','taxonRank','taxon_id','TBIA入口網是否有收錄']]
            now_taicol_df = now_taicol_df.rename(columns={'scientificName': '學名', 'common_name_c': '中文名', 'taxonRank': '分類階層',
                                                        'taxon_id': 'taxonID'})
            now_taicol_df.to_csv('/tbia-volumes/media/taxon_stat/{}_{}.csv'.format(k,tt),index=None)
        else:
            now_taicol_df['所屬單位資料庫是否有收錄'] = now_taicol_df['count'].apply(lambda x: False if math.isnan(x) else True)
            now_taicol_df = now_taicol_df[['scientificName','common_name_c','taxonRank','taxon_id','所屬單位資料庫是否有收錄']]
            now_taicol_df = now_taicol_df.rename(columns={'scientificName': '學名', 'common_name_c': '中文名', 'taxonRank': '分類階層',
                                                        'taxon_id': 'taxonID'})
            now_taicol_df.to_csv('/tbia-volumes/media/taxon_stat/{}_{}.csv'.format(k,tt),index=None)

