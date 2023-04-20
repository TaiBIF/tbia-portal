# 更新資料集

from utils.solr_query import SOLR_PREFIX
import requests

from data.models import DatasetKey

# http://localhost:8983/solr/techproducts/select?q=*:*&facet.pivot=cat,popularity,inStock
#    &facet.pivot=popularity,cat&facet=true&facet.field=cat&facet.limit=5&rows=0&facet.pivot.mincount=2

response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.pivot=group,recordType,datasetName&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
d_list = response.json()['facet_counts']['facet_pivot']['group,recordType,datasetName']
# dataset_list = [d_list[x] for x in range(0, len(d_list),2)]

for d in d_list:
    for dd in d['pivot']:
        # print(dd)
        for ddd in dd['pivot']:
            # print(ddd)
            DatasetKey.objects.create(group= d['value'],record_type=dd['value'], name=ddd['value'])
    # print(d)
