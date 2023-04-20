import requests
import json


response = requests.get('http://solr:8983/solr/tbia_occurrence/select?facet.field=scientificNameID&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
f_list = response.json()['facet_counts']['facet_fields']['scientificNameID']

composite_list = [f_list[x:x+2] for x in range(0, len(f_list),2)]


for i in composite_list:
    namecode = i[0]
    if namecode.endswith('.0'):
        # update solr
        # get all id first
        res = requests.get(f'http://solr:8983/solr/tbia_occurrence/select?fl=id&fq=scientificNameID%3A"{namecode}"&indent=true&q.op=OR&q=*:*&rows=2147483647')
        for j in res.json()['response']['docs']:
            print('occ', j, namecode)
            updates = {'id': j['id'], 'scientificNameID': {'set': namecode.replace('.0','')}}
            headers = {'Content-Type': 'application/json',}
            params = (('commit', 'true'),)
            data = json.dumps([updates])
            response = requests.post('http://solr:8983/solr/tbia_occurrence/update', headers=headers, params=params, data=data)



response = requests.get('http://solr:8983/solr/tbia_collection/select?facet.field=scientificNameID&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
f_list = response.json()['facet_counts']['facet_fields']['scientificNameID']

composite_list = [f_list[x:x+2] for x in range(0, len(f_list),2)]


for i in composite_list:
    namecode = i[0]
    if namecode.endswith('.0'):
        # update solr
        # get all id first
        res = requests.get(f'http://solr:8983/solr/tbia_collection/select?fl=id&fq=scientificNameID%3A"{namecode}"&indent=true&q.op=OR&q=*:*&rows=2147483647')
        for j in res.json()['response']['docs']:
            print('col', j, namecode)
            updates = {'id': j['id'], 'scientificNameID': {'set': namecode.replace('.0','')}}
            headers = {'Content-Type': 'application/json',}
            params = (('commit', 'true'),)
            data = json.dumps([updates])
            response = requests.post('http://solr:8983/solr/tbia_collection/update', headers=headers, params=params, data=data)


