# test cpami API
# species: 盤古蟾蜍

import requests
import pandas as pd
from conf.settings import env

# national park
request_url = f"https://npgis.cpami.gov.tw/openapi/v1/api/InvestigateRecord?apiKey={env('CPAMI_KEY')}&speciesName=盤古蟾蜍"
response = requests.get(request_url)


data = response.json()
len_of_data = data['total_results']
data_per_page = data['per_page']
total_page, remainder = divmod(len_of_data, data_per_page)

if remainder != 0:
    total_page += 1

total_data = []
for i in range(0, total_page):
    current_page = i+1
    print(current_page)
    temp_response = requests.get(request_url,params={'page': current_page})
    temp_data = temp_response.json()
    total_data += temp_data["results"]

df = pd.json_normalize(total_data)
