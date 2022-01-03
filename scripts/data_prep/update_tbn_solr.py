# update sensitiveState field for TBN data
import pandas as pd
import os
import glob
import requests

folder = '/tbia-volumes/solr/csvs/col'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
len_f = len(files)

for i in range(len_f):
    print(folder, i)
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    df['id'] = 'tbn_' + df['occurrenceID']
    df.to_csv(path)


folder = '/tbia-volumes/solr/csvs/occ'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
len_f = len(files)

for i in range(len_f):
    print(folder, i)
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    df['id'] = 'tbn_' + df['occurrenceID']
    df.to_csv(path)


# df['tbnID'] = df.references.apply(lambda x: x.split('/')[-1])

# for i in df.index:
#     print(i, df.iloc[i].tbiaUUID)
#     request_url = f"https://www.tbn.org.tw/api/v2/occurrence?tbnID={df.iloc[i].tbnID}"
#     response = requests.get(request_url)
#     t = response.json()['data']
#     sensitiveCategory = t[0]['dataSensitiveIndicator']
#     occurrenceID = df.iloc[i].occurrenceID
#     updates = {'id': f'tbn_{occurrenceID}', 'sensitiveCategory': {'set': sensitiveCategory}}
#     headers = {'Content-Type': 'application/json',}
#     params = (('commit', 'true'),)
#     data = json.dumps([updates])
#     response = requests.post('http://solr:8983/solr/tbia_occurrence/update', headers=headers, params=params, data=data)




# curl http://127.0.0.1:8983/solr/update -H "Content-type: text/xml" --data-binary '<delete><query>*:*</query></delete>'


# bin/post -c tbia_occurrence -type text/xml -out yes -d $'<delete><query>*:*</query></delete>'


# curl http://127.0.0.1:8983/solr/tbia_occurrence/update?commit=true --data '<delete><query>*:*</query></delete>' -H 'Content-type:text/xml; charset=utf-8'
# curl http://localhost:8983/solr/tbia_occurrence/update?commit=true&stream.body=<delete><query>*%3A*</query></delete>
