# 使用方式：python update_stat.py 2026-03

import argparse
import json
import requests

from conf.settings import SOLR_PREFIX
from manager.models import DataStat
from data.utils import rights_holder_map

parser = argparse.ArgumentParser()
parser.add_argument('year_month', help='YYYY-MM, 例如 2026-03')
args = parser.parse_args()
year_month = args.year_month

query = {
    "query": "*:*",
    "offset": 0,
    "limit": 0,
    "facet": {
        "stat_rightsHolder": {
            "type": "terms",
            "field": "rightsHolder",
            "mincount": 1,
            "limit": -1,
            "allBuckets": False,
            "numBuckets": False,
        }
    },
}

resp = requests.post(
    f'{SOLR_PREFIX}tbia_records/select',
    data=json.dumps(query),
    headers={'content-type': 'application/json'},
).json()

buckets = resp['facets']['stat_rightsHolder']['buckets']
buckets.append({'val': 'total', 'count': resp['response']['numFound']})

group_map = {**rights_holder_map, 'total': 'total'}

DataStat.objects.filter(year_month=year_month, type='data').delete()
DataStat.objects.bulk_create([
    DataStat(
        year_month=year_month,
        count=b['count'],
        rights_holder=b['val'],
        group=group_map[b['val']],
        type='data',
    )
    for b in buckets if b['val'] in group_map
])
