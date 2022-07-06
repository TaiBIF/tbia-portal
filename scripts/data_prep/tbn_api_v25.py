# script for TBN API version 2.5


# test for TBN API

from xml.sax import default_parser_list
from numpy import nan
import requests
import pandas as pd
from data.models import *
from datetime import datetime, tzinfo,timedelta
from dateutil import parser


def convert_date(date):
    formatted_date = None
    if date != '' and date is not None:
        try:
            formatted_date = parser.parse(date) 
        except parser._parser.ParserError:
            formatted_date = datetime.fromtimestamp(int(date))
        except:
            formatted_date = None
    return formatted_date


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


datasets = df[df.selfProduced==True].datasetUUID.to_list() # 46


for d in datasets:
    print('get:'+d)
    request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000"
    response = requests.get(request_url)
    data = response.json()
    len_of_data = data['meta']['total'] # 6846187 -> 22820
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



# 只取自產資料

# NomenMatch


