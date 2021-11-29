# key a684b9ba-1a1a-49ac-8a9c-7485b6502775
import requests
import pandas as pd
from requests.api import request
from conf.settings import env

request_url = f"https://ecollect.forest.gov.tw/EcologicalOdata/odata/data?$filter=vernacularname eq '白羊草'&$top=10"
response = requests.get(request_url)

# get all plan
request_url = "https://ecollect.forest.gov.tw/EcologicalOdata/odata/odata_plan_basic"
response = requests.get(request_url)
data = response.json()['value'] # 595
plans = []
for i in range(len(data)):
    name = data[i]['plan_name']
    plans.append(name)

# get all data
for i in plans:
    request_url = f"https://ecollect.forest.gov.tw/EcologicalOdata/odata/data?$filter=planname eq '{i}'"
    response = requests.get(request_url)
