# 取得TBN上的GBIF資料集
# 需排除透過TaiBIF發布的
# 2022-09-06

import re
from numpy import nan
import requests
import pandas as pd
from data.models import *
from datetime import datetime, tzinfo,timedelta
from dateutil import parser
import bson
import time
import os
from conf.settings import env


ds = pd.read_csv('/tbia-volumes/bucket/taibif_datasets.csv')

request_url = "https://www.tbn.org.tw/api/v25/dataset?modified=1000-01-01"
response = requests.get(request_url)
data = response.json()
len_of_data = data['meta']['total'] # 1452
j = 0
total_data = data["data"]
while data['links']['next'] != "":
    request_url = data['links']['next']
    response = requests.get(request_url)
    data = response.json()
    total_data += data["data"]
    j += 1
df = pd.DataFrame(total_data)

df = df[(~df.datasetUUID.isin(ds.guid))&(df.datasetDataFrom=='GBIF')]
df = df.reset_index(drop=True)

for d in df.datasetUUID:
    print('get:'+d)
    request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000"
    response = requests.get(request_url)
    data = response.json()
    len_of_data = data['meta']['total'] # 43242
    j = 0
    total_data = data["data"]
    while data['links']['next'] != "":
        print('get:'+d)
        request_url = data['links']['next']
        response = requests.get(request_url)
        data = response.json()
        total_data += data["data"]
        j += 1
        if j != 0 and j % 100 == 0:
            df = pd.DataFrame(total_data)
            df.to_csv(f"/tbia-volumes/bucket/tbn_gbif/{d}_{j/100}.csv")
            total_data = []
    df = pd.DataFrame(total_data)
    df.to_csv(f"/tbia-volumes/bucket/tbn_gbif/{d}_{j}.csv")
