# script for TBN API version 2.5


# test for TBN API

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

for i in df.index:
    print(i)
    request_url = f'https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={df.datasetUUID[i]}&limit=1'
    response = requests.get(request_url)
    data = response.json()
    d = data["data"]
    if d:
        df.loc[i, 'selfProduced'] = d[0].get('selfProduced')

# 只取自產資料
datasets = df[df.selfProduced==True].datasetUUID.to_list() # 46

# # 536dbfa2-6972-495c-a051-77312f04072b
# # 6f689983-76a3-4d82-a393-ab731c5655da
# # 97c21d3f-774b-45e7-9149-4c0697fadbde

for d in datasets:
    print('get:'+d)
    request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000&apikey={env('TBN_KEY')}"
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
    df = pd.DataFrame(total_data)
    # 如果有模糊化才撈
    df = df[df.dataGeneralizations==True]
    if len(df) > 1:
        df = df.reset_index()
        # 只取經緯度
        df = df[['decimalLatitude','decimalLongitude']]
        for i in df.index:
            row = df.iloc[i]
            standardLon = float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None
            standardLat = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None
            if standardLon and standardLat:
                if -180 <= standardLon  and standardLon <= 180 and -90 <= standardLat and standardLat <= 90:
                    location_rpt = f'POINT({standardLon} {standardLat})' 
            else:
                location_rpt = None
            df['standardLat'] = standardLat
            df['standardLon'] = standardLon
            df['location_rpt'] = location_rpt
        df = df.rename(columns={'standardLat':'standardRawLatitude','standardLon':'standardRawLongitude',
                                'decimalLatitude':'verbatimRawLatitude','decimalLongitude':'verbatimRawLongitude',
                                'location_rpt':'raw_location_rpt'})
        # 和直接的merge找回id
        old = pd.read_csv(f"/tbia-volumes/solr/csvs/get/{d}.csv", usecols=['occurrenceID','id'])
        df = df.merge(old,by='occurrenceID')
        df.to_csv(f"/tbia-volumes/solr/csvs/update/{d}.csv", index=None)
