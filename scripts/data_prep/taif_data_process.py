# 2023-05-22
# RUN in web container
# script for TAIF API
from django.db import connection
import urllib.parse
import numpy as np
import bisect
import re
from numpy import nan
import requests
import pandas as pd
import bson
import time
import os
from conf.settings import env
from dateutil import parser
from datetime import datetime, timedelta
import glob
from data.models import Namecode, Taxon, DatasetKey
from sqlalchemy import create_engine
import psycopg2
import math

from scripts.data_prep.utils import *


# 拿掉保育資訊
fields = [f.name for f in Taxon._meta.get_fields()]
fields.remove('cites')
fields.remove('iucn')
fields.remove('redlist')
fields.remove('protected')
fields.remove('sensitive')


issue_map = {
    1: 'higherrank',
    2: 'none',
    3: 'fuzzy',
    4: 'multiple'
}


rank_map = {
    1: 'Domain', 2: 'Superkingdom', 3: 'Kingdom', 4: 'Subkingdom', 5: 'Infrakingdom', 6: 'Superdivision', 7: 'Division', 8: 'Subdivision', 9: 'Infradivision', 10: 'Parvdivision', 11: 'Superphylum', 12:
    'Phylum', 13: 'Subphylum', 14: 'Infraphylum', 15: 'Microphylum', 16: 'Parvphylum', 17: 'Superclass', 18: 'Class', 19: 'Subclass', 20: 'Infraclass', 21: 'Superorder', 22: 'Order', 23: 'Suborder',
    24: 'Infraorder', 25: 'Superfamily', 26: 'Family', 27: 'Subfamily', 28: 'Tribe', 29: 'Subtribe', 30: 'Genus', 31: 'Subgenus', 32: 'Section', 33: 'Subsection', 34: 'Species', 35: 'Subspecies', 36:
    'Nothosubspecies', 37: 'Variety', 38: 'Subvariety', 39: 'Nothovariety', 40: 'Form', 41: 'Subform', 42: 'Special Form', 43: 'Race', 44: 'Stirp', 45: 'Morph', 46: 'Aberration', 47: 'Hybrid Formula'}

def standardize_coor(lon,lat):
    try:
        standardLon = float(lon) if lon not in ['', None, '0', 'WGS84'] else None
    except:
        standardLon = None
    if standardLon:
        if not (-180 <= standardLon  and standardLon <= 180):
            standardLon = None
    try:
        standardLat = float(lat) if lat not in ['', None] else None
    except:
        standardLat = None
    if standardLat:
        if not (-90 <= standardLat and standardLat <= 90):
            standardLat = None
    if standardLon and standardLat:
        # if -180 <= standardLon  and standardLon <= 180 and -90 <= standardLat and standardLat <= 90:
        location_rpt = f'POINT({standardLon} {standardLat})' 
    else:
        location_rpt = None
    return standardLon, standardLat, location_rpt


# 國家公園都沒有上階層的資訊

def match_name(matching_name,sci_name,original_name,match_stage):
    if matching_name:
        request_url = f"http://host.docker.internal:8080/api.php?names={urllib.parse.quote(matching_name)}&format=json&source=taicol"
        response = requests.get(request_url)
        if response.status_code == 200:
            result = response.json()
            if result['data'][0][0]: # 因為一次只比對到一個，所以只要取第一個search term
                # 排除地位為誤用的taxon，因為代表該名字不該指涉到此taxon
                match_score = result['data'][0][0].get('score')
                if match_score == 'N/A': #有對到但無法計算分數
                    match_score = 0 
                filtered_rs = [rs for rs in result['data'][0][0]['results'] if rs['name_status'] != 'misapplied']
                if len(filtered_rs):
                    # 排除掉同個taxonID但有不同name的情況
                    filtered_rs = pd.DataFrame(filtered_rs)[['accepted_namecode']].drop_duplicates().to_dict(orient='records')
                    # NomenMatch 有比對到有效taxon
                    # 沒有上階層資訊，就直接取比對結果
                    if len(filtered_rs) == 1:
                        if match_score < 1:
                            sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 3
                        else:
                            sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = None
                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']
                    else:
                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 4


# 國家公園只有1,3,4階段
def matching_flow(sci_names):
    ## 第一階段比對 - scientificName
    # TODO 未來要改成優先採用TaiCOL taxonID (若原資料庫有提供)
    for s in sci_names.index:
        s_row = sci_names.iloc[s]
        if s_row.sourceScientificName:
            match_name(s_row.sourceScientificName,s_row.sourceScientificName,s_row.sourceVernacularName,1)
    # ## 第二階段比對 沒有taxonID的 試抓TaiCOL namecode
    ## 第三階段比對 - sourceVernacularName 中文比對
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 3
    no_taxon = sci_names[(sci_names.taxonID=='')&(sci_names.sourceVernacularName!='')]
    for nti in no_taxon.index:
        # 可能有多個sourceVernacularName
        names = sci_names.iloc[nti].sourceVernacularName
        for nn in names.split(';'):
            if not sci_names.loc[nti,'taxonID']:
                match_name(nn, sci_names.loc[nti,'sourceScientificName'],sci_names.loc[nti,'sourceVernacularName'],3)
    ## 第四階段比對 - scientificName第一個英文單詞 (為了至少可以補階層)
    ## 這個情況要給的是parentTaxonID
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 4
    no_taxon = sci_names[sci_names.taxonID=='']
    for nti in no_taxon.index:
        if nt_str := sci_names.loc[nti,'sourceScientificName']:
            if len(nt_str.split(' ')) > 1: # 等於0的話代表上面已經對過了
                match_name(nt_str.split(' ')[0], sci_names.loc[nti,'sourceScientificName'],sci_names.loc[nti,'sourceVernacularName'],4)
    # 確定match_stage
    stage_list = [1,2,3,4,5]
    for i in stage_list[:4]:
        for stg in stage_list[stage_list.index(i)+1:]:
            sci_names.loc[sci_names.match_stage==i,f'stage_{stg}'] = None
    sci_names.loc[(sci_names.match_stage==4)&(sci_names.taxonID==''),'match_stage'] = None
    return sci_names

group = 'taif'
url = f"https://taifdb.tfri.gov.tw/apis/data.php?limit=1"
response = requests.get(url)
data = []
c = 0
if response.status_code == 200:
    result = response.json()
    total_count = response.json()['total_count'] # 393809
    total_page = math.ceil(total_count/300)
    # data += result.get('Data')

# ['occurrenceID', 'collectionID', 'associatedMedia', 'scientificName',
#        'isPreferredName', 'taxonRank', 'typeStatus', 'eventDate',
#        'verbatimLongitude', 'verbatimLatitude', 'verbatimCoordinateSystem',
#        'locality', 'recordedBy', 'recordNumber', 'preservation', 'datasetName',
#        'resourceContacts', 'references', 'license', 'mediaLicense',
#        'modified']


for p in range(0,total_page,10):
    print(p)
    data = []
    c = p
    while c < p + 10 and c < total_page:
        offset = c*300
        print('offset:',offset)
        # time.sleep(30)
        url = f"https://taifdb.tfri.gov.tw/apis/data.php?limit=300&offset={offset}"
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            data += result.get('data')
        c+=1
    df = pd.DataFrame(data)
    df = df.replace({'NA': ''})
    # 林試所的typeStatus會寫成一般，應該要改為空值？
    # preservation和basisOfRecord的差異？
    df = df[~(df.isPreferredName.isin([nan,'',None])&df.scientificName.isin([nan,'',None]))]
    df = df.reset_index(drop=True)
    df = df.replace({np.nan: '', 'NA': ''})
    df = df.drop(columns=['taxonRank'])
    df = df.rename(columns={'modified': 'sourceModified', 'scientificName': 'sourceScientificName',
                            'isPreferredName': 'sourceVernacularName'})
    # 排除學名為空值
    sci_names = df[['sourceScientificName','sourceVernacularName']].drop_duplicates().reset_index(drop=True)
    sci_names['taxonID'] = ''
    sci_names['parentTaxonID'] = ''
    sci_names['match_stage'] = 1
    # 各階段的issue default是沒有對到
    # 國家公園只有1,3,4
    sci_names['stage_1'] = 2
    sci_names['stage_2'] = None
    sci_names['stage_3'] = 2
    sci_names['stage_4'] = 2
    sci_names['stage_5'] = None
    sci_names = matching_flow(sci_names)
    taxon_list = list(sci_names[sci_names.taxonID!=''].taxonID.unique()) + list(sci_names[sci_names.parentTaxonID!=''].parentTaxonID.unique())
    final_taxon = Taxon.objects.filter(taxonID__in=taxon_list).values(*fields)
    final_taxon = pd.DataFrame(final_taxon)
    if len(final_taxon):
        final_taxon = final_taxon.drop(columns=['id'])
        final_taxon = final_taxon.rename(columns={'scientificNameID': 'taxon_name_id'})
        # sci_names = sci_names.rename(columns={'scientificName': 'sourceScientificName'})
        match_taxon_id = sci_names.merge(final_taxon,how='left')
        # 若沒有taxonID的 改以parentTaxonID串
        match_parent_taxon_id = sci_names.drop(columns=['taxonID']).merge(final_taxon,left_on='parentTaxonID',right_on='taxonID')
        match_parent_taxon_id['taxonID'] = ''
        match_taxon_id = match_taxon_id.append(match_parent_taxon_id,ignore_index=True)
        match_taxon_id[['sourceScientificName','sourceVernacularName']] = match_taxon_id[['sourceScientificName','sourceVernacularName']].replace({'': '-999999'})
    if len(match_taxon_id):
        df[['sourceScientificName','sourceVernacularName']] = df[['sourceScientificName','sourceVernacularName']].replace({'': '-999999',None:'-999999'})
        df = df.merge(match_taxon_id, on=['sourceScientificName','sourceVernacularName'], how='left')
        df[['sourceScientificName','sourceVernacularName']] = df[['sourceScientificName','sourceVernacularName']].replace({'-999999': ''})
    # df['sourceCreated'] = df['sourceCreated'].apply(lambda x: convert_date(x))
    df['sourceModified'] = df['sourceModified'].apply(lambda x: convert_date(x))
    df['standardDate'] = df['eventDate'].apply(lambda x: convert_date(x))
    # df['dataGeneralizations'] = df['dataGeneralizations'].replace({'N': False, 'Y': True})
    df['group'] = group
    df['rightsHolder'] = '林業試驗所植物標本資料庫'
    df['created'] = datetime.now()
    df['modified'] = datetime.now()
    # df['grid_x_1'] = -1
    df['grid_1'] = '-1_-1'
    # df['grid_x_5'] = -1
    df['grid_5'] = '-1_-1'
    # df['grid_x_10'] = -1
    df['grid_10'] = '-1_-1'
    # df['grid_x_100'] = -1
    df['grid_100'] = '-1_-1'
    for i in df.index:
        df.loc[i,'id'] = bson.objectid.ObjectId()
        row = df.iloc[i]
        df.loc[i,'recordType'] = 'col'
        # if '標本' in row.basisOfRecord:
        #     df.loc[i,'recordType'] = 'col'
        # else:
        #     df.loc[i,'recordType'] = 'occ'
        standardLon, standardLat, location_rpt = standardize_coor(row.verbatimLongitude, row.verbatimLatitude)
        if standardLon and standardLat:
            df.loc[i,'standardLongitude'] = standardLon
            df.loc[i,'standardLatitude'] = standardLat
            df.loc[i,'location_rpt'] = location_rpt
            df.loc[i,'verbatimSRS'] = 'WGS84'
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.01)
            df.loc[i, 'grid_1'] = str(int(grid_x)) + '_' + str(int(grid_y))
            # df.loc[i, 'grid_y_1'] = grid_y
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.05)
            df.loc[i, 'grid_5'] = str(int(grid_x)) + '_' + str(int(grid_y))
            # df.loc[i, 'grid_y_5'] = grid_y
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.1)
            df.loc[i, 'grid_10'] = str(int(grid_x)) + '_' + str(int(grid_y))
            # df.loc[i, 'grid_x_10'] = grid_x
            # df.loc[i, 'grid_y_10'] = grid_y
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 1)
            df.loc[i, 'grid_100'] = str(int(grid_x)) + '_' + str(int(grid_y))
            # df.loc[i, 'grid_x_100'] = grid_x
            # df.loc[i, 'grid_y_100'] = grid_y
        try:
            standardOrganismQuantity = int(row.organismQuantity)
            df.loc[i,'standardOrganismQuantity'] = standardOrganismQuantity
        except:
            pass
    # df.to_csv(f'/tbia-volumes/solr/csvs/processed/{group}_{p}.csv', index=False)
    ds_name = df[['datasetName','recordType']].drop_duplicates().to_dict(orient='records')
    for r in ds_name:
        if DatasetKey.objects.filter(group=group,name=r['datasetName'],record_type=r['recordType']).exists():
            # 更新
            dk = DatasetKey.objects.get(group=group,name=r['datasetName'],record_type=r['recordType'])
            dk.deprecated = False
            dk.save()
        else:
            # 新建
            DatasetKey.objects.create(
                name = r['datasetName'],
                record_type = r['recordType'],
                group = group,
            )
    match_log = df[['occurrenceID','id','sourceScientificName','taxonID','parentTaxonID','match_stage','stage_1','stage_2','stage_3','stage_4','stage_5','group','created','modified']]
    match_log.loc[match_log.taxonID=='','is_matched'] = False
    match_log.loc[(match_log.taxonID!='')|(match_log.parentTaxonID!=''),'is_matched'] = True
    match_log = match_log.replace({np.nan: None})
    match_log['match_stage'] = match_log['match_stage'].apply(lambda x: int(x) if x else x)
    match_log['stage_1'] = match_log['stage_1'].apply(lambda x: issue_map[x] if x else x)
    match_log['stage_2'] = match_log['stage_2'].apply(lambda x: issue_map[x] if x else x)
    match_log['stage_3'] = match_log['stage_3'].apply(lambda x: issue_map[x] if x else x)
    match_log['stage_4'] = match_log['stage_4'].apply(lambda x: issue_map[x] if x else x)
    match_log['stage_5'] = match_log['stage_5'].apply(lambda x: issue_map[x] if x else x)
    match_log['group'] = group
    match_log = match_log.rename(columns={'id': 'tbiaID'})
    match_log['tbiaID'] = match_log['tbiaID'].apply(lambda x: str(x))
    conn_string = env('DATABASE_URL').replace('postgres://', 'postgresql://')
    db = create_engine(conn_string)
    match_log.to_sql('manager_matchlog', db, if_exists='append',schema='public', index=False)
    df = df.drop(columns=['match_stage','stage_1','stage_2','stage_3','stage_4','stage_5','taxon_name_id'],errors='ignore')
    # df = df.rename(columns={'taxon_name_id': 'scientificNameID'})
    df.to_csv(f'/tbia-volumes/solr/csvs/processed/{group}_{p}.csv', index=False)


sql = """
copy (
    SELECT mm."tbiaID", mm."occurrenceID", mm."sourceScientificName", mm."taxonID",
    mm."parentTaxonID", mm.is_matched, dt."scientificName", dt."taxonRank",
    mm.match_stage, mm.stage_1, mm.stage_2, mm.stage_3, mm.stage_4, mm.stage_5
    FROM manager_matchlog mm
    LEFT JOIN data_taxon dt ON mm."taxonID" = dt."taxonID"
    WHERE mm."group" = '{}'
) to stdout with delimiter ',' csv header;
""".format(group)
with connection.cursor() as cursor:
    with open(f'/tbia-volumes/media/match_log/{group}_match_log.csv', 'w+') as fp:
        cursor.copy_expert(sql, fp)


import subprocess
zip_file_path = f'/tbia-volumes/media/match_log/{group}_match_log.zip'
csv_file_path = f'/tbia-volumes/media/match_log/{group}_match_log.csv'
commands = f"zip -j {zip_file_path} {csv_file_path}; rm {csv_file_path}"
process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# 等待檔案完成
process.communicate()


print('done!')
