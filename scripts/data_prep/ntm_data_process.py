# 2023-06-02
# RUN in web container
# script for ntm API (from taibif)
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
import math 


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

def match_name(matching_name,sci_name,original_name,original_gbifid,is_parent,match_stage):
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
                filtered_rss = []
                if len(filtered_rs):
                    # 排除掉同個taxonID但有不同name的情況
                    filtered_rs = pd.DataFrame(filtered_rs)[['accepted_namecode','family','order','class']].drop_duplicates().to_dict(orient='records')
                    # NomenMatch 有比對到有效taxon
                    # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'has_nm_result'] = True
                    # 是否有上階層資訊
                    has_parent = False
                    if original_gbifid:
                        t_family = sci_names[sci_names.gbifAcceptedID==original_gbifid]['family'].values[0] # 科
                        t_order = sci_names[sci_names.gbifAcceptedID==original_gbifid]['order'].values[0] # 目
                        t_class = sci_names[sci_names.gbifAcceptedID==original_gbifid]['class'].values[0] # 綱
                        # t_rank = tbn_data[0].get('taxonRank')
                        # t_patent_uuid = tbn_data[0].get('parentUUID')
                        has_parent = True
                            # if t_family or t_class:
                            #     sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'has_tbn_parent'] = True
                    # 若有上階層資訊，加上比對上階層                    
                    if has_parent:
                        has_nm_parent = False # True代表有比對到
                        for frs in filtered_rs:
                            if frs.get('family') or frs.get('order') or frs.get('class'):
                                if frs.get('family') == t_family or frs.get('class') == t_class or frs.get('order') == t_order:
                                    filtered_rss.append(frs)
                                    has_nm_parent = True                            # if t_rank in ['種','種下階層']: # 直接比對family
                        # 如果有任何有nm上階層 且filtered_rss > 0 就代表有上階層比對成功的結果
                        if has_nm_parent:
                            if len(filtered_rss) == 1:
                                if is_parent:
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 1
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'parentTaxonID'] = filtered_rss[0]['accepted_namecode']
                                else:
                                    # 根據NomenMatch給的score確認名字是不是完全一樣
                                    if match_score < 1:
                                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 3
                                    else:
                                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = None
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'taxonID'] = filtered_rss[0]['accepted_namecode']
                            else:
                                sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 4
                                # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'more_than_one'] = True
                        else:
                            # 如果沒有任何nm上階層的結果，則直接用filtered_rs
                            if len(filtered_rs) == 1:
                                if is_parent:
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 1
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'parentTaxonID'] = filtered_rs[0]['accepted_namecode']
                                else:
                                    if match_score < 1:
                                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 3
                                    else:
                                        sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = None
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']
                            else:
                                sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 4
                                # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'more_than_one'] = True
                    # 若沒有上階層資訊，就直接取比對結果
                    else:
                        if len(filtered_rs) == 1:
                            if is_parent:
                                sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 1
                                sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'parentTaxonID'] = filtered_rs[0]['accepted_namecode']
                            else:
                                if match_score < 1:
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 3
                                else:
                                    sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = None
                                sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']
                        else:
                            sci_names.loc[((sci_names.sourceScientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 4
                            # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),'more_than_one'] = True
                # else:
                #     sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.sourceVernacularName==original_name)),f'stage_{match_stage}'] = 2 # none


# (matching_name,sci_name,original_name,original_gbifid,is_parent,match_stage):
def matching_flow(sci_names):
    # 優先採用TaiCOL taxonID (若原資料庫有提供)
    ## 第一階段比對 - scientificName
    no_taxon = sci_names[(sci_names.taxonID=='')]
    for s in no_taxon.index:
        s_row = sci_names.iloc[s]
        if s_row.sourceScientificName:
            match_name(s_row.sourceScientificName,s_row.sourceScientificName,s_row.sourceVernacularName,s_row.gbifAcceptedID,False,1)
    # ## 第二階段比對 沒有taxonID的 試抓TaiCOL namecode
    ## 第三階段比對 - sourceVernacularName 中文比對
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 3
    no_taxon = sci_names[(sci_names.taxonID=='')&(sci_names.sourceVernacularName!='')]
    for nti in no_taxon.index:
        # 可能有多個sourceVernacularName
        if names := sci_names.iloc[nti].sourceVernacularName:
            for nn in names.split(';'):
                if not sci_names.loc[nti,'taxonID']:
                    match_name(nn,s_row.sourceScientificName,s_row.sourceVernacularName,s_row.gbifAcceptedID,False,3)
                # match_name(nn, sci_names.loc[nti,'sourceScientificName'],sci_names.loc[nti,'sourceVernacularName'],3)
    ## 第四階段比對 - scientificName第一個英文單詞 (為了至少可以補階層)
    ## 這個情況要給的是parentTaxonID
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 4
    no_taxon = sci_names[sci_names.taxonID=='']
    for nti in no_taxon.index:
        if nt_str := sci_names.loc[nti,'sourceScientificName']:
            if len(nt_str.split(' ')) > 1: # 等於0的話代表上面已經對過了
                match_name(nt_str.split(' ')[0], sci_names.loc[nti,'sourceScientificName'],sci_names.loc[nti,'sourceVernacularName'],sci_names.loc[nti,'gbifAcceptedID'],True,4)
    ## 比對綱目科
    # 確定match_stage
    stage_list = [1,2,3,4,5]
    for i in stage_list[:4]:
        for stg in stage_list[stage_list.index(i)+1:]:
            sci_names.loc[sci_names.match_stage==i,f'stage_{stg}'] = None
    # TODO 這樣寫會忽略到比對parentTaxonID的資料 但或許不用改?
    sci_names.loc[(sci_names.match_stage==4)&(sci_names.taxonID==''),'match_stage'] = None
    return sci_names



# # 取得所有台灣發布者
# url = "https://portal.taibif.tw/api/v2/publisher?countryCode=TW"
# response = requests.get(url)
# if response.status_code == 200:
#     data = response.json()
#     pub = pd.DataFrame(data)
# #     pub.to_csv('taibif_pub.csv')


# partners = ['Taiwan Forestry Bureau', 'Taiwan Endemic Species Research Institute', 'Taiwan Forestry Research Institute',
# 'Marine National Park Headquarters', 'Yushan National Park Headquarters', 'National Taiwan Museum', 'Water Resources Agency,Ministry of Economic Affairs']


# pub = pub[~pub.publisherName.isin(partners)]

# 取得所有資料集
url = 'https://portal.taibif.tw/api/v2/dataset?publisherName=National Taiwan Museum'
response = requests.get(url)
if response.status_code == 200:
    data = response.json()
    dataset = pd.DataFrame(data)


# dataset = dataset[dataset.core.isin(['OCCURRENCE','SAMPLINGEVENT'])]

# 取得台博館 

group = 'ntm'
d_count = 0
d = dataset.taibifDatasetID[0]
gbif_d = dataset.gbifDatasetID[0]
# for d in dataset.taibifDatasetID.unique():
#     d_count += 1
    # print(d, ': ', d_count)
data = []
url = f"https://portal.taibif.tw/api/v2/occurrence/basic_occ?taibifDatasetID={d}&rows=1000"
response = requests.get(url)
c = 0
offset = 0
if response.status_code == 200:
    result = response.json()
    if total_count := result.get('count'):
        data += result.get('results')
        while offset < total_count:
            c += 1
            offset = c * 1000
            next_url = f"https://portal.taibif.tw/api/v2/occurrence/basic_occ?taibifDatasetID={d}&rows=1000&offset={offset}"
            response = requests.get(next_url)
            if response.status_code == 200:
                result = response.json()
                data += result.get('results')
if len(data):
    df = pd.DataFrame(data)
    # df = df.drop(columns=['occurrenceID'])
    df = df.rename(columns={'taibifCreatedDate': 'sourceCreated',
                            'taibifModifiedDate': 'sourceModified',
                            'scientificName': 'sourceScientificName',
                            'isPreferredName': 'sourceVernacularName',
                            'taicolTaxonID': 'taxonID',
                            'decimalLatitude': 'verbatimLatitude',
                            'decimalLongitude': 'verbatimLongitude'})
    df = df[~(df.sourceVernacularName.isin([nan,'',None])&df.sourceScientificName.isin([nan,'',None]))]
    if len(df):
        df = df.replace({nan: '', None: ''})
        sci_names = df[['taxonID','sourceScientificName','sourceVernacularName','gbifAcceptedID','class', 'order', 'family']].drop_duplicates().reset_index(drop=True)
        # sci_names['taxonID'] = ''
        sci_names['parentTaxonID'] = ''
        sci_names['match_stage'] = 1
        # 各階段的issue default是沒有對到
        # 只有1,3,4
        sci_names['stage_1'] = 2
        sci_names['stage_2'] = None
        sci_names['stage_3'] = 2
        sci_names['stage_4'] = 2
        sci_names['stage_5'] = None
        sci_names = matching_flow(sci_names)
        df = df.drop(columns=['occurrenceStatus', 'taibifDatasetID', 'taxonRank', 
                            'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'taxonGroup', 
                            'year', 'month', 'country', 'county', 'datasetShortName', 'scientificNameID', 
                            'taxonBackbone', 'day', 'geodeticDatum', 'habitatReserve', 'wildlifeReserve', 
                            'countryCode'], errors='ignore')
        taxon_list = list(sci_names[sci_names.taxonID!=''].taxonID.unique()) + list(sci_names[sci_names.parentTaxonID!=''].parentTaxonID.unique())
        final_taxon = Taxon.objects.filter(taxonID__in=taxon_list).values(*fields)
        final_taxon = pd.DataFrame(final_taxon)
        if len(final_taxon):
            final_taxon = final_taxon.drop(columns=['id'])
            final_taxon = final_taxon.rename(columns={'scientificNameID': 'taxon_name_id'})
            # sci_names = sci_names.rename(columns={'scientificName': 'sourceScientificName'})
            sci_names['copy_index'] = sci_names.index
            match_taxon_id = sci_names.drop(['class','family','order'],errors='ignore').merge(final_taxon)
            # 若沒有taxonID的 改以parentTaxonID串
            match_parent_taxon_id = sci_names.drop(columns=['taxonID','class','family','order'],errors='ignore').merge(final_taxon,left_on='parentTaxonID',right_on='taxonID')
            match_parent_taxon_id['taxonID'] = ''
            match_taxon_id = match_taxon_id.append(match_parent_taxon_id,ignore_index=True)
            # 如果都沒有對到 要再加回來
            match_taxon_id = match_taxon_id.append(sci_names[~sci_names.copy_index.isin(match_taxon_id.copy_index.to_list())],ignore_index=True)
            match_taxon_id = match_taxon_id.replace({np.nan: ''})
            match_taxon_id[['sourceScientificName','sourceVernacularName','gbifAcceptedID']] = match_taxon_id[['sourceScientificName','sourceVernacularName','gbifAcceptedID']].replace({'': '-999999'})
        if len(match_taxon_id):
            # 要拆成原本有taxonID / 沒有taxonID的兩個部分
            df_w = df[df.taxonID!='']
            df_w = df_w.reset_index(drop=True)
            if len(df_w):
                df_w = df_w.merge(match_taxon_id.drop(columns=['gbifAcceptedID'],errors='ignore'),on=['sourceScientificName','sourceVernacularName','taxonID'],how='left')
            df_wo = df[df.taxonID=='']
            df_wo = df_wo.reset_index(drop=True)
            if len(df_wo):
                df_wo[['sourceScientificName','sourceVernacularName','gbifAcceptedID']] = df_wo[['sourceScientificName','sourceVernacularName','gbifAcceptedID']].replace({'': '-999999',None:'-999999'})
                df_wo = df_wo.drop(columns=['taxonID']).merge(match_taxon_id, on=['sourceScientificName','sourceVernacularName','gbifAcceptedID'], how='left')
                df_wo[['sourceScientificName','sourceVernacularName','gbifAcceptedID']] = df_wo[['sourceScientificName','sourceVernacularName','gbifAcceptedID']].replace({'-999999': ''})            
            df = pd.concat([df_w, df_wo])
        df = df.reset_index(drop=True)
        df['sourceModified'] = df['sourceModified'].apply(lambda x: convert_date(x))
        df['sourceCreated'] = df['sourceCreated'].apply(lambda x: convert_date(x))
        df['standardDate'] = df['eventDate'].apply(lambda x: convert_date(x))
        df['group'] = group
        df['rightsHolder'] = '國立臺灣博物館典藏'
        df['created'] = datetime.now()
        df['modified'] = datetime.now()
        df['grid_1'] = '-1_-1'
        df['grid_5'] = '-1_-1'
        df['grid_10'] = '-1_-1'
        df['grid_100'] = '-1_-1'
        for i in df.index:
            print(i)
            df.loc[i,'id'] = bson.objectid.ObjectId()
            row = df.iloc[i]
            # 取得GBIF ID
            gbif_url = f"https://api.gbif.org/v1/occurrence/{gbif_d}/{row.occurrenceID}"
            gbif_resp = requests.get(gbif_url)
            if gbif_resp.status_code == 200:
                gbif_res = gbif_resp.json()
                if gbif_res.get('occurrenceID'):
                    df.loc[i, 'occurrenceID'] = gbif_res.get('occurrenceID')
                if gbif_res.get('gbifID'):
                    df.loc[i, 'references'] = f"https://www.gbif.org/occurrence/{gbif_res.get('gbifID')}" 
            if 'Specimen' in row.basisOfRecord:
                df.loc[i,'recordType'] = 'col'
            else:
                df.loc[i,'recordType'] = 'occ'
            standardLon, standardLat, location_rpt = standardize_coor(row.verbatimLongitude, row.verbatimLatitude)
            if standardLon and standardLat:
                df.loc[i,'standardLongitude'] = standardLon
                df.loc[i,'standardLatitude'] = standardLat
                df.loc[i,'location_rpt'] = location_rpt
                grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.01)
                df.loc[i, 'grid_1'] = str(int(grid_x)) + '_' + str(int(grid_y))
                grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.05)
                df.loc[i, 'grid_5'] = str(int(grid_x)) + '_' + str(int(grid_y))
                grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.1)
                df.loc[i, 'grid_10'] = str(int(grid_x)) + '_' + str(int(grid_y))
                grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 1)
                df.loc[i, 'grid_100'] = str(int(grid_x)) + '_' + str(int(grid_y))
            try:
                standardOrganismQuantity = int(row.organismQuantity)
                df.loc[i,'standardOrganismQuantity'] = standardOrganismQuantity
            except:
                pass
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
        df = df.drop(columns=['match_stage','stage_1','stage_2','stage_3','stage_4','stage_5','taxon_name_id','gbifAcceptedID','copy_index'],errors='ignore')
        # df = df.rename(columns={'taxon_name_id': 'scientificNameID'})
        df.to_csv(f'/tbia-volumes/solr/csvs/processed/{group}_{d}.csv', index=False)


# # 台博館 & 水利署
# for d in dataset_include.taibifDatasetID.unique():
#     # data = []
#     url = f"https://portal.taibif.tw/api/v2/occurrence/basic_occ?taibifDatasetID={d}&rows=1000"
#     response = requests.get(url)
#     if response.status_code == 200:
#         # data += response.json().get('results')
#         # df = pd.DataFrame(data)
#         data = response.json()
#         if data.get('count'):
#             print(d, data['count'])
#         else:
#             print(d, 'error')


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
