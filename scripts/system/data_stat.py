
# 每次資料更新完成後計算

from manager.models import *
# import json
import urllib.parse
import pandas as pd
from django.utils import timezone
# from datetime import timedelta
# import dateutil.relativedelta

import requests
from conf.settings import SOLR_PREFIX
import json

# 先找出上次更新的年月
response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q.op=OR&q=*%3A*&rows=1&fl=modified')
resp = response.json()

current_year_month = resp['response']['docs'][0]['modified'][0][:7]

rights_holder_map = {
    'GBIF': 'gbif',
    '中央研究院生物多樣性中心植物標本資料庫': 'brmas',
    '台灣生物多樣性網絡 TBN': 'tbri',
    '國立臺灣博物館典藏': 'ntm',
    '林業試驗所昆蟲標本館': 'fact',
    '林業試驗所植物標本資料庫': 'taif',
    '河川環境資料庫': 'wra',
    '濕地環境資料庫': 'nps',
    '生態調查資料庫系統': 'forest',
    '臺灣國家公園生物多樣性資料庫': 'nps',
    '臺灣生物多樣性資訊機構 TaiBIF': 'brcas',
    '海洋保育資料倉儲系統': 'oca'
}


# 入口網每次更新所屬單位的資料累積折線圖

query = { "query": "*:*",
        "offset": 0,
        "limit": 0,
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
    DataStat.objects.create(
        year_month = current_year_month,
        count = d['count'],
        rights_holder= d['val'],
        group=group,
        type = 'data'
    )

DataStat.objects.create(
    year_month = current_year_month,
    count = total_count,
    rights_holder= 'total',
    group= 'total',
    type = 'data'
)




taxon_group_map = {
    'Insects' : [{'key': 'class', 'value': 'Insecta'}],
    'Fishes' : [{'key': 'class', 'value': 'Actinopterygii'},{'key': 'class', 'value': 'Chondrichthyes'},{'key': 'class', 'value': 'Myxini'}],
    'Reptiles' : [{'key': 'class', 'value': 'Reptilia'}],
    'Fungi' : [{'key': 'kingdom', 'value': 'Fungi'}],
    'Plants' : [{'key': 'kingdom', 'value': 'Plantae'}],
    'Birds' : [{'key': 'class', 'value': 'Aves'}],
    'Mammals' : [{'key': 'class', 'value': 'Mammalia'}],
    'Amphibians' : [{'key': 'class', 'value': 'Amphibia'}],
    'Bacteria' : [{'key': 'kingdom', 'value': 'Bacteria'}],
    'Others' : [{'key': 'class', 'value': ''}],
}


# 入口網上各物種類群資料筆數圓餅圖


for val in taxon_group_map.keys():
    query_list = []
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
        if TaxonStat.objects.filter(rights_holder=d['val'],name=val,type='taxon_group', group=group).exists():
            TaxonStat.objects.filter(rights_holder=d['val'],name=val,type='taxon_group', group=group).update(count=d['count'])
        else:
            TaxonStat.objects.create(rights_holder=d['val'],name=val,type='taxon_group',count=d['count'], group=group)
    if TaxonStat.objects.filter(rights_holder='total',name=val,type='taxon_group', group='total').exists():
        TaxonStat.objects.filter(rights_holder='total',name=val,type='taxon_group', group='total').update(count=total_count,modified=timezone.now())
    else:
        TaxonStat.objects.create(rights_holder='total',name=val,type='taxon_group',count=total_count, group='total')


# 各單位提供最多資料的前五個科與對應資料筆數

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
    data = response.json()['facets']['family']['buckets']
    # 每次要先刪掉原本的
    TaxonStat.objects.filter(rights_holder=r,type='family').delete()
    for d in data:
        if d['val'] in rights_holder_map.keys():
            group = rights_holder_map[d['val']]
        TaxonStat.objects.create(rights_holder=r,name=d['val'],type='family',count=d['count'],group=group)
