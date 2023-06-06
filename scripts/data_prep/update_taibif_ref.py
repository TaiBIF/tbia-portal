# merge grid_x & grid_y into one field to improve facet efficiency
import requests
from utils.solr_query import SOLR_PREFIX
import pandas as pd
import json
import os
import glob

query = []

folder = '/tbia-volumes/solr/csvs/processed'
extension = 'csv'
os.chdir(folder)
files = glob.glob('brcas_*.{}'.format(extension))
for i in range(0, len(files)):
    print(i, '/',  len(files))
    df = pd.read_csv(files[i],usecols=['id','references','occurrenceID'])
    df['references'] = df.apply(lambda x: f"https://portal.taibif.tw/occurrence/{x.occurrenceID}" if x.occurrenceID else None, axis=1)
    # query = df[['id','grid_1','grid_5','grid_10','grid_100']].to_dict(orient='records')
    response = requests.post(f'{SOLR_PREFIX}tbia_records/update?commit=true', data=json.dumps(query), headers={'content-type': "application/json" })