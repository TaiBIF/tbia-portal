# script for GBIF (currently from TBN)

import requests
import pandas as pd

request_url = "https://www.tbn.org.tw/api/v25/dataset?modified=1000-01-01"
response = requests.get(request_url)
data = response.json()
len_of_data = data['meta']['total'] 
j = 0
total_data = data["data"]
while data['links']['next'] != "":
    print(j)
    request_url = data['links']['next']
    response = requests.get(request_url)
    data = response.json()
    total_data += data["data"]
    j += 1


df = pd.DataFrame(total_data)

# subset GBIF 資料集
df = df[df.datasetDataFrom=='GBIF']

# df.to_csv('tbn_gbif.csv')

# 確認publisher
# df.datasetPublisher.unique()

# 夥伴單位 publisher 不排除特生
# 'National Taiwan Museum'
# 'Taiwan Biodiversity Information Facility (TaiBIF)'
# 'Taiwan Endemic Species Research Institute'
# 'Taiwan Forestry Bureau'
# 'Taiwan Forestry Research Institute'
df = df[~df.datasetPublisher.isin(['National Taiwan Museum',
'Taiwan Biodiversity Information Facility (TaiBIF)',
'Taiwan Forestry Bureau',
'Taiwan Forestry Research Institute'])]

df = df.reset_index(drop=True)

# for d in df.datasetUUID.to_list():
#     print('get:' + d)
#     # 只取自產資料
#     request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000"
#     response = requests.get(request_url)
#     data = response.json()
#     if len_of_data := data['meta'].get('total'):
#         j = 0
#         total_data = data["data"]
#         while data['links']['next'] != "":
#             print('get:'+d)
#             request_url = data['links']['next']
#             response = requests.get(request_url)
#             data = response.json()
#             total_data += data["data"]
#             j += 1
#         df = pd.DataFrame(total_data)
#         df.to_csv(f"/tbia-volumes/bucket/gbif_v25/{d}.csv")

c = 0
for d in df.datasetUUID.to_list():
    c += 1
    print(f"{c} get: {d}")
    request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000"
    response = requests.get(request_url)
    data = response.json()
    len_of_data = data['meta']['total'] # 43242
    j = 0
    total_data = data["data"]
    while data['links']['next'] != "":
        print(f"{c} get: {d} {j}")
        request_url = data['links']['next']
        response = requests.get(request_url)
        data = response.json()
        total_data += data["data"]
        j += 1
        if j != 0 and j % 100 == 0:
            df = pd.DataFrame(total_data)
            df.to_csv(f"/tbia-volumes/bucket/gbif_v25/{d}_{j/100}.csv")
            total_data = []
    df = pd.DataFrame(total_data)
    df.to_csv(f"/tbia-volumes/bucket/gbif_v25/{d}_{j}.csv")


print('done!')