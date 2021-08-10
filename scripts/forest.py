# key a684b9ba-1a1a-49ac-8a9c-7485b6502775
import requests
import pandas as pd
from conf.settings import env

request_url = f"http://ecollect.forest.gov.tw/EcologicalOdata/odata/data?$filter=decimalLatitude gt 22.696100 and decimalLatitude lt 22.696120 and decimalLongitude gt 120.996940 and decimalLongitude lt 120.996945$top=10&key={env('FOREST_KEY')}"
response = requests.get(request_url)

