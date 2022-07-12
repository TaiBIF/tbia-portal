from urllib import request
import pandas as pd
import numpy as np
from utils.solr_query import SolrQuery, col_facets, occ_facets, SOLR_PREFIX
import requests



rows = 0
start = 0

url = f"{SOLR_PREFIX}taxa/select?indent=on&q=*:*&wt=json&rows={rows}&start={start}"
init = requests.get(url).json()

len_taxa = init['response']['numFound']

get_data = True
rows = 20000
start = 0

taxa = []
while get_data:
    print(start)
    url = f"{SOLR_PREFIX}taxa/select?indent=on&q=*:*&wt=json&fl=id,scientificName,formatted_name,common_name_c&rows={rows}&start={start}"
    res = requests.get(url).json()
    taxa += res['response']['docs']
    if start > len_taxa:
        get_data = False
    else:
        start += 20000

taicol = pd.DataFrame(taxa)
taicol = taicol.rename(columns={'id': 'taxonID', 'scientificName': 'name'})