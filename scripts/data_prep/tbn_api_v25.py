# script for TBN API version 2.5

import requests
import pandas as pd

request_url = "https://www.tbn.org.tw/api/v25/dataset?modified=1000-01-01"
response = requests.get(request_url)
data = response.json()
len_of_data = data['meta']['total'] 
j = 0
total_data = data["data"]
while data['links']['next'] != "":
    request_url = data['links']['next']
    response = requests.get(request_url)
    data = response.json()
    total_data += data["data"]
    j += 1
df = pd.DataFrame(total_data)

for d in df.datasetUUID.to_list():
    print('get:' + d)
    # 只取自產資料
    request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000&selfProduced=y"
    response = requests.get(request_url)
    data = response.json()
    if len_of_data := data['meta'].get('total'):
        j = 0
        total_data = data["data"]
        while data['links']['next'] != "":
            print('get:'+d)
            request_url = data['links']['next']
            response = requests.get(request_url)
            data = response.json()
            total_data += data["data"]
            j += 1
        df = pd.DataFrame(total_data)
        df.to_csv(f"/tbia-volumes/bucket/tbn_v25/{d}.csv")

print('done!')
