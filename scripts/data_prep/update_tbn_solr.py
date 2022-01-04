# update sensitiveState field for TBN data
import pandas as pd
import os
import glob
import requests
import json

# folder = '/tbia-volumes/solr/csvs/col'
folder = '/home/centos/tbia-volumes/solr/csvs/col'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
len_f = len(files)

for i in range(len_f):
    print(folder, i)
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    # df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # df.to_csv(path, index=False)
    # df['id'] = df['tbiaUUID']
    # df = df.drop(['tbiaUUID'], axis=1)
    # df['references'] = df['references'].replace('.0', '')
    # df.to_csv(path, index=False)
    df['tbnID'] = df.references.apply(lambda x: x.split('/')[-1])
    for j in df.index:
        print(j, df.iloc[j].id)
        request_url = f"https://www.tbn.org.tw/api/v2/occurrence?tbnID={df.iloc[j].tbnID}"
        response = requests.get(request_url)
        t = response.json()['data']
        sensitiveCategory = t[0]['dataSensitiveIndicator']
        updates = {'id': df.iloc[j].id, 'sensitiveCategory': {'set': sensitiveCategory}}
        headers = {'Content-Type': 'application/json',}
        params = (('commit', 'true'),)
        data = json.dumps([updates])
        response = requests.post('http://127.0.0.1:8983/solr/tbia_collection/update', headers=headers, params=params, data=data)

# folder = '/tbia-volumes/solr/csvs/occ'
folder = '/home/centos/tbia-volumes/solr/csvs/occ'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
len_f = len(files)

for i in range(len_f):
    print(folder, i)
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    # df['id'] = df['tbiaUUID']
    # df = df.drop(['tbiaUUID'], axis=1)
    # df['references'] = df['references'].replace('.0', '')
    # df.to_csv(path)
    df['tbnID'] = df.references.apply(lambda x: x.split('/')[-1])
    for j in df.index:
        print(j, df.iloc[j].id)
        request_url = f"https://www.tbn.org.tw/api/v2/occurrence?tbnID={df.iloc[j].tbnID}"
        response = requests.get(request_url)
        t = response.json()['data']
        sensitiveCategory = t[0]['dataSensitiveIndicator']
        updates = {'id': df.iloc[j].id, 'sensitiveCategory': {'set': sensitiveCategory}}
        headers = {'Content-Type': 'application/json',}
        params = (('commit', 'true'),)
        data = json.dumps([updates])
        response = requests.post('http://127.0.0.1:8983/solr/tbia_occurrence/update', headers=headers, params=params, data=data)




# curl http://127.0.0.1:8983/solr/update -H "Content-type: text/xml" --data-binary '<delete><query>*:*</query></delete>'


# bin/post -c tbia_occurrence -type text/xml -out yes -d $'<delete><query>*:*</query></delete>'


# curl http://127.0.0.1:8983/solr/tbia_occurrence/update?commit=true --data '<delete><query>*:*</query></delete>' -H 'Content-type:text/xml; charset=utf-8'
# curl http://localhost:8983/solr/tbia_occurrence/update?commit=true&stream.body=<delete><query>*%3A*</query></delete>
