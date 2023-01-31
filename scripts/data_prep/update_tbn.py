# update sensitiveState field for TBN data
import pandas as pd
import os
import glob
import requests
import json
import numpy as np
folder = '/tbia-volumes/solr/csvs/udpate'
# folder = '/tbia-volumes/solr/csvs/posted_csv'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
len_f = len(files)

for i in range(len_f):
    print(files[i])
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    if '公園' in files[i]:
        df['group'] = 'cpami'
    else:
        df['group'] = 'tesri'
    df = df.replace({np.nan: None})
    df.to_csv(path, index=False)

# # folder = '/tbia-volumes/solr/csvs/col'
# folder = '/home/centos/tbia-volumes/solr/csvs/col'
# # tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
# extension = 'csv'
# os.chdir(folder)
# files = glob.glob('*.{}'.format(extension))
# len_f = len(files)

# for i in range(len_f):
#     print(folder, i)
#     path = os.path.join(folder, files[i])
#     df = pd.read_csv(path)
#     df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
#     # df['id'] = df['tbiaUUID']
#     # df = df.drop(['tbiaUUID'], axis=1)
#     df['references'] = df['references'].replace('.0', '')
#     df['scientificNameID'] = df['scientificNameID'].astype(str).replace('.0', '')
#     df['location_rpt'] = None
#     df[df[['standardLatitude','standardLongitude']].notnull()]['location_rpt'] = "POINT(" + df[df[['standardLatitude','standardLongitude']].notnull()]["standardLongitude"].astype(str) + ' ' + df[df[['standardLatitude','standardLongitude']].notnull()]["standardLatitude"].astype(str) + ")"
#     df.to_csv(path, index=False)


folder = '/tbia-volumes/solr/csvs/col'
# folder = '/tbia-volumes/solr/csvs/posted_csv'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
len_f = len(files)


for i in range(5):
    print(files[i])
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    df['group'] = 'tesri'
    df = df.replace({np.nan: None})
    df.to_csv(path, index=False)



for i in range(len_f):
    print(folder, i)
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    df = df.replace({np.nan: ''})
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # df['id'] = df['tbiaUUID']
    # df = df.drop(['tbiaUUID'], axis=1)
    # df['references'] = f"https://www.tbn.org.tw/occurrence/{str(int(row.tbnID))}"
    # df['scientificNameID'] = df['scientificNameID'].astype(str).replace('.0', '')
    df['standardOrganismQuantity'] = None
    for j in df.index:
        # namecode
        df.loc[j, 'scientificNameID'] = str(df.loc[j, 'scientificNameID']).replace('.0', '')
        # references
        if df.loc[j, 'occurrenceID']:
            df.loc[j, 'references'] = "https://www.tbn.org.tw/occurrence/" + df.loc[j, 'occurrenceID']
        # organismQuantity
        try:
            df.loc[j, 'standardOrganismQuantity'] = int(df.loc[j, 'organismQuantity'])
        except:
            pass
        # location_rpt
        if df.loc[j, 'standardLongitude'] and df.loc[j, 'standardLatitude']:
            df.loc[j, 'location_rpt'] = f'POINT({df.loc[j, "standardLongitude"]} {df.loc[j, "standardLatitude"]})'
    df.to_csv(path, index=False)


folder = '/tbia-volumes/solr/csvs/occ'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
len_f = len(files)

for i in range(len_f):
    print(folder, i)
    path = os.path.join(folder, files[i])
    df = pd.read_csv(path)
    df = df.replace({np.nan: ''})
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # df['id'] = df['tbiaUUID']
    # df = df.drop(['tbiaUUID'], axis=1)
    # df['references'] = f"https://www.tbn.org.tw/occurrence/{str(int(row.tbnID))}"
    # df['scientificNameID'] = df['scientificNameID'].astype(str).replace('.0', '')
    df['standardOrganismQuantity'] = None
    for j in df.index:
        # namecode
        df.loc[j, 'scientificNameID'] = str(df.loc[j, 'scientificNameID']).replace('.0', '')
        # references
        if df.loc[j, 'occurrenceID']:
            df.loc[j, 'references'] = "https://www.tbn.org.tw/occurrence/" + df.loc[j, 'occurrenceID']
        # organismQuantity
        try:
            df.loc[j, 'standardOrganismQuantity'] = int(df.loc[j, 'organismQuantity'])
        except:
            pass
        # location_rpt
        if df.loc[j, 'standardLongitude'] and df.loc[j, 'standardLatitude']:
            df.loc[j, 'location_rpt'] = f'POINT({df.loc[j, "standardLongitude"]} {df.loc[j, "standardLatitude"]})'
    df.to_csv(path, index=False)


