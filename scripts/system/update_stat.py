# 每次資料更新完成時需要更新的統計

import requests
from conf.settings import SOLR_PREFIX
import json
from manager.models import DataStat, TaxonStat
from data.utils import rights_holder_map

# TODO 這邊要修改成最新的
year_month='2025-09'


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

response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
response = response.json()
# 整理欄位
total = response['response']['numFound']
# data = response['response']['docs']
stat_rightsHolder = []
# if 'stat_rightsHolder' in response['facets'].keys():
stat_rightsHolder = response['facets']['stat_rightsHolder']['buckets']
stat_rightsHolder.append({'val': 'total', 'count': total})


DataStat.objects.filter(year_month=year_month,type='data').delete()

for d in stat_rightsHolder:
    if d['val'] in rights_holder_map.keys():
        group = rights_holder_map[d['val']]
        DataStat.objects.create(
            year_month=year_month,
            count=d['count'],
            rights_holder=d['val'],
            group=group,
            type='data'
        )
    elif d['val'] == 'total':
        group = 'total'
        DataStat.objects.create(
            year_month=year_month,
            count=d['count'],
            rights_holder=d['val'],
            group=group,
            type='data'
        )
