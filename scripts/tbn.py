# test for TBN API

import requests
import pandas as pd

request_url = "https://www.tbn.org.tw/api/v2/occurrence?taxonUUID=7fd8cbf6-4128-4215-989f-4bcfc328f693&limit=20"
response = requests.get(request_url)

data = response.json()

# df = pd.json_normalize(data['data'])

len_of_data = data['meta']['total']

# check if next url exist
i = 0
total_data = data["data"]
while data['links']['next'] != "":
    print(i)
    request_url = data['links']['next']
    response = requests.get(request_url)
    data = response.json()
    total_data += data["data"]
    i += 1



# occurrence url https://www.tbn.org.tw/occurrence/{tbnID}