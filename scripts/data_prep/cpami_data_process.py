# 2023-04-14
# RUN in web container
# script for CPAMI API version 2.5
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

from scripts.data_prep.utils import *

issue_map = {
    1: 'higherrank',
    2: 'none',
    3: 'fuzzy',
    4: 'multiple'
}

locality_map = {
    'YMS': '陽明山國家公園',
    'TRK': '太魯閣國家公園',
    'SP': '雪霸國家公園',
    'ES': '玉山國家公園',
    'KT': '墾丁國家公園',
    'KM': '金門國家公園',
    'DS': '東沙環礁國家公園',
    'TJ': '台江國家公園',
    'SNNP': '壽山國家自然公園',
    'SSNP': '壽山國家自然公園',
    'SPM': '澎湖南方四島國家公園',
    'TCMP': '台中都會公園',
    'KCMP': '高雄都會公園',
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
        request_url = f"http://host.docker.internal:8080/api.php?names={urllib.parse.quote(matching_name.replace(' ','+'))}&format=json&source=taicol"
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
                            sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.isPreferredName==original_name)),f'stage_{match_stage}'] = 3
                        else:
                            sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.isPreferredName==original_name)),f'stage_{match_stage}'] = None
                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.isPreferredName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']
                    else:
                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.isPreferredName==original_name)),f'stage_{match_stage}'] = 4


# 國家公園只有1,3,4階段
def matching_flow(sci_names):
    ## 第一階段比對 - scientificName
    # TODO 未來要改成優先採用TaiCOL taxonID (若原資料庫有提供)
    for s in sci_names.index:
        s_row = sci_names.iloc[s]
        if s_row.sourceScientificName:
            match_name(s_row.sourceScientificName,s_row.sourceScientificName,s_row.isPreferredName,1)
    # ## 第二階段比對 沒有taxonID的 試抓TaiCOL namecode
    ## 第三階段比對 - isPreferredName 中文比對
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 3
    no_taxon = sci_names[(sci_names.taxonID=='')&(sci_names.isPreferredName!='')]
    for nti in no_taxon.index:
        match_name(sci_names.loc[nti,'isPreferredName'], sci_names.loc[nti,'sourceScientificName'],sci_names.loc[nti,'isPreferredName'],3)
    ## 第四階段比對 - scientificName第一個英文單詞 (為了至少可以補階層)
    ## 這個情況要給的是parentTaxonID
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 4
    no_taxon = sci_names[sci_names.taxonID=='']
    for nti in no_taxon.index:
        if nt_str := sci_names.loc[nti,'sourceScientificName']:
            if len(nt_str.split(' ')) > 1: # 等於0的話代表上面已經對過了
                match_name(nt_str.split(' ')[0], sci_names.loc[nti,'sourceScientificName'],sci_names.loc[nti,'isPreferredName'],4)
    # 確定match_stage
    stage_list = [1,2,3,4,5]
    for i in stage_list[:4]:
        for stg in stage_list[stage_list.index(i)+1:]:
            sci_names.loc[sci_names.match_stage==i,f'stage_{stg}'] = None
    sci_names.loc[(sci_names.match_stage==4)&(sci_names.taxonID==''),'match_stage'] = None
    return sci_names



url = f"https://npgis.cpami.gov.tw//TBiAOpenApi/api/Data/Get?Token={env('CPAMI_KEY')}"
response = requests.get(url)
data = []
c = 0
if response.status_code == 200:
    result = response.json()
    total_page = result['Meta']['TotalPages']
    data += result.get('Data')


for p in range(0,total_page,10):
    print(p)
    data = []
    c = p
    while c < p + 10 and c < total_page:
        c+=1
        print('page:',c)
        time.sleep(30)
        url = f"https://npgis.cpami.gov.tw//TBiAOpenApi/api/Data/Get?Token={env('CPAMI_KEY')}&Page={c}"
        response = requests.get(url)
        if response.status_code == 200:
            result = response.json()
            total_page = result['Meta']['TotalPages']
            data += result.get('Data')
    df = pd.DataFrame(data)
    df = df[~(df.isPreferredName.isin([nan,'',None])&df.scientificName.isin([nan,'',None]))]
    df = df.reset_index(drop=True)
    df = df.replace({np.nan: '', 'NA': ''})
    df = df.drop(columns=['taxonRank'])
    df = df.rename(columns={'basicOfRecord': 'basisOfRecord', 'created': 'sourceCreated', 'modified': 'sourceModified', 'scientificName': 'sourceScientificName'})
    # 排除學名為空值
    sci_names = df[['sourceScientificName','isPreferredName',]].drop_duplicates().reset_index(drop=True)
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
    final_taxon = Taxon.objects.filter(taxonID__in=taxon_list).values()
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
        match_taxon_id[['sourceScientificName','isPreferredName']] = match_taxon_id[['sourceScientificName','isPreferredName']].replace({'': '-999999'})
    if len(match_taxon_id):
        df[['sourceScientificName','isPreferredName']] = df[['sourceScientificName','isPreferredName']].replace({'': '-999999',None:'-999999'})
        df = df.merge(match_taxon_id, on=['sourceScientificName','isPreferredName'], how='left')
        df[['sourceScientificName','isPreferredName']] = df[['sourceScientificName','isPreferredName']].replace({'-999999': ''})
    df['locality'] = df['locality'].apply(lambda x: locality_map[x] if x in locality_map.keys() else x)
    df['sourceCreated'] = df['sourceCreated'].str.replace('上午', 'AM').str.replace('下午','PM')
    df['sourceCreated'] = df['sourceCreated'].apply(lambda x: convert_date(x))
    df['sourceModified'] = df['sourceModified'].str.replace('上午', 'AM').str.replace('下午','PM')
    df['sourceModified'] = df['sourceModified'].apply(lambda x: convert_date(x))
    df['group'] = 'cpami'
    df['created'] = datetime.now()
    df['modified'] = datetime.now()
    for i in df.index:
        df.loc[i,'id'] = bson.objectid.ObjectId()
        row = df.iloc[i]
        if '標本' in row.basisOfRecord:
            df.loc[i,'recordType'] = 'col'
        else:
            df.loc[i,'recordType'] = 'occ'
        standardLon, standardLat, location_rpt = standardize_coor(row.verbatimLongitude, row.verbatimLatitude)
        if standardLon and standardLat:
            df.loc[i,'standardLongitude'] = standardLon
            df.loc[i,'standardLatitude'] = standardLat
            df.loc[i,'location_rpt'] = location_rpt
            df.loc[i,'verbatimSRS'] = 'WGS84'
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.01)
            df.loc[i, 'grid_x_1'] = grid_x
            df.loc[i, 'grid_y_1'] = grid_y
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.05)
            df.loc[i, 'grid_x_5'] = grid_x
            df.loc[i, 'grid_y_5'] = grid_y
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.1)
            df.loc[i, 'grid_x_10'] = grid_x
            df.loc[i, 'grid_y_10'] = grid_y
            grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 1)
            df.loc[i, 'grid_x_100'] = grid_x
            df.loc[i, 'grid_y_100'] = grid_y
        try:
            standardOrganismQuantity = int(row.organismQuantity)
            df.loc[i,'standardOrganismQuantity'] = standardOrganismQuantity
        except:
            pass
    group = 'cpami'
    df.to_csv(f'/tbia-volumes/solr/csvs/processed/{group}_{p}.csv', index=False)
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
    match_log = df[['occurrenceID','id','sourceScientificName','taxonID','parentTaxonID','match_stage','stage_1','stage_2','stage_3','stage_4','stage_5','created','modified']]
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



sql = """
copy (
    SELECT mm."tbiaID", mm."occurrenceID", mm."sourceScientificName", mm."taxonID",
    mm."parentTaxonID", mm.is_matched, dt."scientificName", dt."taxonRank",
    mm.match_stage, mm.stage_1, mm.stage_2, mm.stage_3, mm.stage_4, mm.stage_5
    FROM manager_matchlog mm
    LEFT JOIN data_taxon dt ON mm."taxonID" = dt."taxonID"
    WHERE mm."group" = 'cpami'
) to stdout with delimiter ',' csv header;
"""
with connection.cursor() as cursor:
    with open(f'/tbia-volumes/media/match_log/{group}_match_log.csv', 'w+') as fp:
        cursor.copy_expert(sql, fp)
