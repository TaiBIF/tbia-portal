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
for g in ['tesri', 'brmas', 'cpami','fact']:
    files = glob.glob('{}*.{}'.format(g,extension))
    for i in range(0, len(files)):
        print(g, ':' ,i, '/',  len(files))
        df = pd.read_csv(files[i],usecols=['id','grid_x_1','grid_y_1','grid_x_5','grid_y_5','grid_x_10','grid_y_10','grid_x_100','grid_y_100'])
        df['grid_1'] = df.apply(lambda x: str(int(x['grid_x_1'])) +'_'+ str(int(x['grid_y_1'])), axis=1)
        df['grid_5'] = df.apply(lambda x: str(int(x['grid_x_5'])) +'_'+ str(int(x['grid_y_5'])), axis=1)
        df['grid_10'] = df.apply(lambda x: str(int(x['grid_x_10'])) +'_'+ str(int(x['grid_y_10'])), axis=1)
        df['grid_100'] = df.apply(lambda x: str(int(x['grid_x_100'])) +'_'+ str(int(x['grid_y_100'])), axis=1)
        df['grid_1'] = df['grid_1'].apply(lambda x: {"set": x})
        df['grid_5'] = df['grid_5'].apply(lambda x: {"set": x})
        df['grid_10'] = df['grid_10'].apply(lambda x: {"set": x})
        df['grid_100'] = df['grid_100'].apply(lambda x: {"set": x})
        query = df[['id','grid_1','grid_5','grid_10','grid_100']].to_dict(orient='records')
        response = requests.post(f'{SOLR_PREFIX}tbia_records/update?commit=true', data=json.dumps(query), headers={'content-type': "application/json" })