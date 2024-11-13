# 每次資料更新完成時需要更新的統計

import requests
from conf.settings import SOLR_PREFIX
import json
from manager.models import DataStat, TaxonStat

year_month=''
    
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
}

query = { "query": "*:*",
        "offset": 0,
        "limit": 0,
        # "filter": fq_list,
        }
# 查詢記錄
# if offset == 0:
query['facet'] = {}
query['facet']['stat_rightsHolder'] = {
    'type': 'terms',
    'field': 'rightsHolder',
    'mincount': 1,
    'limit': -1,
    'allBuckets': False,
    'numBuckets': False}

response = requests.post(f'{{SOLR_PREFIX}}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
response = response.json()
# 整理欄位
total = response['response']['numFound']
# data = response['response']['docs']
stat_rightsHolder = []
# if 'stat_rightsHolder' in response['facets'].keys():
stat_rightsHolder = response['facets']['stat_rightsHolder']['buckets']
stat_rightsHolder.append({'val': 'total', 'count': total})

for d in stat_rightsHolder:
    if d['val'] in rights_holder_map.keys():
        group = rights_holder_map[d['val']]
    else:
        group = 'total'
    DataStat.objects.create(
        year_month=year_month,
        count=d['count'],
        rights_holder=d['val'],
        group=group,
        type='data'
    )



# taxon stat
# 2024-11 改成也存year_month


taxon_group_map = {
    'Insects' : [{'key': 'class', 'value': 'Insecta'}],
    'Fishes' : [{'key': 'superclass', 'value': 'Actinopterygii'},{'key': 'superclass', 'value': 'Chondrichthyes'},{'key': 'class', 'value': 'Myxini'}],
    'Reptiles' : [{'key': 'class', 'value': 'Reptilia'}],
    'Fungi' : [{'key': 'kingdom', 'value': 'Fungi'}],
    'Plants' : [{'key': 'kingdom', 'value': 'Plantae'}],
    'Birds' : [{'key': 'class', 'value': 'Aves'}],
    'Mammals' : [{'key': 'class', 'value': 'Mammalia'}],
    'Amphibians' : [{'key': 'class', 'value': 'Amphibia'}],
    'Bacteria' : [{'key': 'kingdom', 'value': 'Bacteria'}],
    'Others' : [{'key': 'class', 'value': ''}],
}


for val in taxon_group_map.keys():
    query_list = ['is_in_taiwan:1']
    vv_list = []
    # 如果是others的話 要排除掉其他的
    if val == 'Others':
        for vv in taxon_group_map.keys():
            if vv != 'Others':
                for vvv in taxon_group_map[vv]:
                    vv_list.append(f'''-{vvv['key']}:"{vvv['value']}"''')
    else:
        for vv in taxon_group_map[val]:
            vv_list.append(f'''{vv['key']}:"{vv['value']}"''')
    query_list += [" OR ".join(vv_list)]
    query = { "query": "*:*",
            "offset": 0,
            "limit": 0,
            "filter": query_list,
            "facet": {
                "rightsHolder": {
                    "type": "terms",
                    "field": "rightsHolder",
                    "limit": -1,
                    }
                }
            }
    response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
    data = response.json()['facets']['rightsHolder']['buckets']
    total_count = 0
    for d in data:
        if d['val'] in rights_holder_map.keys():
            group = rights_holder_map[d['val']]
        total_count += d['count']
        TaxonStat.objects.create(rights_holder=d['val'],name=val,type='taxon_group',count=d['count'], group=group,year_month=year_month)
    TaxonStat.objects.create(rights_holder='total',name=val,type='taxon_group',count=total_count, group='total',year_month=year_month)


for r in rights_holder_map.keys():
    query = { "query": "*:*",
            "offset": 0,
            "limit": 0,
            "filter": [f'rightsHolder:"{r}"',"is_in_taiwan:1"],
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
    data = response.json()['facets']['family']['buckets']
    for d in data:
        if d['val'] in rights_holder_map.keys():
            group = rights_holder_map[d['val']]
        TaxonStat.objects.create(rights_holder=r,name=d['val'],type='family',count=d['count'],group=group,year_month=year_month)
