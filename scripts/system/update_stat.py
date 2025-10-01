# 每次資料更新完成時需要更新的統計

import requests
from conf.settings import SOLR_PREFIX
import json
from manager.models import DataStat, TaxonStat


# TODO 這邊要修改成最新的
year_month='2025-09'


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
    '國家海洋資料庫及共享平台': 'namr',
    '農業部農村發展及水土保持署': 'ardswc',
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
    else:
        group = 'total'
    DataStat.objects.create(
        year_month=year_month,
        count=d['count'],
        rights_holder=d['val'],
        group=group,
        type='data'
    )