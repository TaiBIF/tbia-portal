# 2022-12-01
# 在docker container外執行

# script for TBN API version 2.5

# test for TBN API

import numpy as np
import bisect

# x: longtitude, y: latitude

# grid = [0.01, 0.05, 0.1, 1]

def convert_grid_to_coor(grid_x, grid_y, grid):
    list_x = np.arange(-180, 180, grid)
    list_y = np.arange(-90, 90, grid)
    center_x = (list_x[grid_x] + list_x[grid_x+1])/2
    center_y = (list_y[grid_y] + list_y[grid_y+1])/2
    return center_x, center_y

# x_grid = bisect.bisect(list_x, grid_x)-1
# y_grid = bisect.bisect_right(list_y, grid_y)-1

def convert_coor_to_grid(x, y, grid):
    list_x = np.arange(-180, 180, grid)
    list_y = np.arange(-90, 90, grid)
    grid_x = bisect.bisect(list_x, x)-1
    grid_y = bisect.bisect(list_y, y)-1
    return grid_x, grid_y

import re
from numpy import nan
import requests
import pandas as pd
import bson
import time
import os
# from conf.settings import env
from dateutil import parser
from datetime import datetime, timedelta

taicol = pd.read_csv('~/tbia-volumes/solr/csvs/source_taicol_for_tbia_20220905.csv')
taicol = taicol.rename(columns={'id': 'taxonID', 'scientificNameID': 'taxon_name_id'})
# taicol = taicol.drop(columns=['scientificNameID'])

# TaiCOL新舊namecode對應
namecodes = pd.read_csv('~/tbia-volumes/bucket/namecode_to_taxon_name_id.csv')


def convert_date(date):
    formatted_date = None
    if date != '' and date is not None:
        try:
            formatted_date = parser.parse(date) 
        except parser._parser.ParserError:
            formatted_date = datetime.fromtimestamp(int(date))
        except:
            formatted_date = None
    return formatted_date

# 學名比對

import glob

folder = '~/tbia-volumes/bucket/tbn_v25/'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
# extension = 'csv'
# os.chdir(folder)
# files = glob.glob('*.{}'.format(extension))
# # len_f = len(files)


# # df = pd.read_csv(f'/tbia-volumes/bucket/tbn_v25/536dbfa2-6972-495c-a051-77312f04072b.csv', index_col=0)

# for f in files:
#     d = f.split('.csv')[0]
#     print(d)

d = '248d6799-bb66-40a5-b7ba-b45bbb818ddc'
f = '248d6799-bb66-40a5-b7ba-b45bbb818ddc.csv'
df = pd.read_csv(f'~/tbia-volumes/bucket/tbn_v25/{f}', index_col=0)

# 排除originalVernacularName為空值的資料
df = df[~df.originalVernacularName.isin([nan,'',None]) ]
df = df.reset_index(drop=True)

df['taxon_id'] = ''

sci_names = df[['scientificName','taxonUUID']].drop_duplicates().reset_index(drop=True)
sci_names['scientificName'] = sci_names.scientificName.str.replace('<i>','').str.replace('</i>','')
# unique_sci = [x for x in sci_names if str(x) != 'nan']

no_taxon = []
for s in sci_names.index:
    print(s)
    s_row = sci_names.iloc[s]
    acp_namecode, taxon_id = None, None
    if s_row.scientificName != nan:
        request_url = f"http://127.0.0.1:8080/api.php?names={s_row.scientificName}&format=json&source=taicol"
        # request_url = f"http://127.0.0.1:8080/api.php?names=Taiwania&format=json&source=taicol"
        response = requests.get(request_url)
        if response.status_code == 200:
            result = response.json()
            # if result['data']:
            # if result['data'][0]:
            if result['data'][0][0]:
                if len(result['data'][0][0]['results']) == 1: # 如果只比對到一個
                    # 有可能會沒有accepted namecode 但有namecode
                    if acp_namecode := result['data'][0][0]['results'][0]['accepted_namecode']:
                        acp_namecode = int(acp_namecode.replace('.0',''))
                    else:
                        no_taxon.append(s_row.scientificName)
                elif len(result['data'][0][0]['results']) > 1: # 如果比對到多個, 找上階層
                    if s_uuid := s_row.taxonUUID:
                        tbn_url = "https://www.tbn.org.tw/api/v25/taxon?uuid=" + s_uuid
                        tbn_response = requests.get(tbn_url)
                        if tbn_response.status_code == 200:
                            if tbn_data := tbn_response.json().get('data'):
                                t_family = tbn_data[0].get('family')
                                t_class = tbn_data[0].get('class')
                                rrr = pd.DataFrame(result['data'][0][0]['results'])
                                if len(rrr[(rrr['class']==t_class) & (rrr['family']==t_family)]) == 1:
                                    acp_namecode = rrr.loc[(rrr['class']==t_class) & (rrr['family']==t_family)].accepted_namecode.to_list()[0]
                                    acp_namecode = int(acp_namecode.replace('.0',''))
                else:
                    no_taxon.append(s_row.scientificName)
            if acp_namecode:
                # 這邊對到的都是taxon_name_id 要再換成taxonID
                # TODO 一個taxon_name_id可能會對到多個taxon...?
                taxon_id = taicol[taicol.scientificNameID==acp_namecode].taxonID.to_list()
                if taxon_id:
                    taxon_id = taxon_id[0]
                    df.loc[df.taxonUUID==s_row.taxonUUID,'taxon_id'] = taxon_id
            # if data['info']['total'] == 1: # 只對到一個taxon
            #     df.loc[df.simplifiedScientificName==s,'taxon_id'] = data['data'][0]['taxon_id']
    # TODO
    # 把沒對到的另外處理


# 如果沒對到taxon 看原資料庫有沒有提供namecode 有的話直接對應taxon id
count = 0
for nc in df[df.taxon_id==''].scientificNameID.unique():
    count+=1
    print(count)
    # nc = df.loc[n,'scientificNameID']
    try:
        nc = int(nc)
    except:
        pass
    try:
        nc = str(nc)
    except:
        pass
    if len(namecodes[namecodes.namecode==nc])==1:
        # 舊namecode轉換成新taxon_name_id
        taxon_name_id = namecodes[namecodes.namecode==nc].taxon_name_id.values[0]
        request_url = f"http://18.183.59.124/v1/nameMatch?name_id={taxon_name_id}"    
        response = requests.get(request_url)
        if response.status_code == 200:
            data = response.json()
            if data['info']['total'] == 1: # 只對到一個taxon
                try:
                    nc = int(nc)
                except:
                    pass
                df.loc[(df.taxon_id=='')&(df.scientificNameID==nc),'taxon_id'] = data['data'][0]['taxon_id']
    

# TODO 如果沒對到taxon 改比對原始紀錄提供的學／俗名



# v_names = df[df.taxon_id.isnull()][['originalVernacularName','taxonUUID']].drop_duplicates().reset_index(drop=True)
# v_names['scientificName'] = sci_names.scientificName.str.replace('<i>','').str.replace('</i>','')
# # unique_sci = [x for x in sci_names if str(x) != 'nan']

# no_taxon = []
# for s in sci_names.index:
#     print(s)
#     s_row = sci_names.iloc[s]
#     acp_namecode, taxon_id = None, None
#     if s_row.scientificName != nan:
#         request_url = f"http://127.0.0.1:8080/api.php?names={s_row.scientificName}&format=json&source=taicol"
#         # request_url = f"http://127.0.0.1:8080/api.php?names=Taiwania&format=json&source=taicol"
#         response = requests.get(request_url)
#         if response.status_code == 200:
#             result = response.json()
#             # if result['data']:
#             # if result['data'][0]:
#             if result['data'][0][0]:
#                 if len(result['data'][0][0]['results']) == 1: # 如果只比對到一個
#                     # 有可能會沒有accepted namecode 但有namecode
#                     if acp_namecode := result['data'][0][0]['results'][0]['accepted_namecode']:
#                         acp_namecode = int(acp_namecode.replace('.0',''))
#                     else:
#                         no_taxon.append(s_row.scientificName)
#                 elif len(result['data'][0][0]['results']) > 1: # 如果比對到多個, 找上階層
#                     if s_uuid := s_row.taxonUUID:
#                         tbn_url = "https://www.tbn.org.tw/api/v25/taxon?uuid=" + s_uuid
#                         tbn_response = requests.get(tbn_url)
#                         if tbn_response.status_code == 200:
#                             if tbn_data := tbn_response.json().get('data'):
#                                 t_family = tbn_data[0].get('family')
#                                 t_class = tbn_data[0].get('class')
#                                 rrr = pd.DataFrame(result['data'][0][0]['results'])
#                                 if len(rrr[(rrr['class']==t_class) & (rrr['family']==t_family)]) == 1:
#                                     acp_namecode = rrr.loc[(rrr['class']==t_class) & (rrr['family']==t_family)].accepted_namecode.to_list()[0]
#                                     acp_namecode = int(acp_namecode.replace('.0',''))
#                 else:
#                     no_taxon.append(s_row.scientificName)
#             if acp_namecode:
#                 # 這邊對到的都是taxon_name_id 要再換成taxonID
#                 # TODO 一個taxon_name_id可能會對到多個taxon...?
#                 taxon_id = taicol[taicol.scientificNameID==acp_namecode].taxonID.to_list()
#                 if taxon_id:
#                     taxon_id = taxon_id[0]
#                     df.loc[df.taxonUUID==s_row.taxonUUID,'taxon_id'] = taxon_id


row_list = []

df = df.replace({nan: None})
df = df.replace({'': None})
df = df.replace({"": None})
df = df.replace({"\'\'": None})
df = df.replace({'\"\"': None})

for i in df.index:
    if i % 1000 == 0:
        print(i)
    row = df.iloc[i]
    try:
        if row.individualCount:
            quantity = int(row.individualCount)
        elif row.organismQuantity:
            quantity = float(row.organismQuantity)
        else:
            quantity = None
    except:
        quantity = None
    # 如果不在範圍內也不能算是standard lat & lon
    try:
        standardLon = float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None
    except:
        standardLon = None
    if standardLon:
        if not (-180 <= standardLon  and standardLon <= 180):
            standardLon = None
    try:
        standardLat = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None
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
    # date
    converted_date = None
    if not convert_date(row.eventDate):
        if row.year and row.month and row.day:
            try:
                converted_date = datetime(year=row.year, month=row.month, day=row.day)
            except:
                converted_date = None
    else:
        converted_date = convert_date(row.eventDate)
    # collectionID
    c_list_str = None
    if row.collectionID:
        if c_list := eval(row.collectionID):
            c_list_str = c_list[0]
    try:
        coordinateUncertaintyInMeters = str(int(row.coordinateUncertaintyInMeters))
    except:
        coordinateUncertaintyInMeters = row.coordinateUncertaintyInMeters
    try:
        recordNumber = str(int(row.recordNumber))
    except:
        recordNumber = row.recordNumber
    if recordNumber == '\"\"':
        recordNumber = None
    try:
        scientificNameID = int(row.scientificNameID)
    except:
        scientificNameID = row.scientificNameID
    tmp = {
        'recordType' : 'occ' if '標本' not in str(row.basisOfRecord) else 'col',
        'id' : bson.objectid.ObjectId(),
        'sourceModified' : convert_date(row.modified),
        'sourceCreated' : None, # TBN沒這個欄位 # 
        'modified' : datetime.now(),
        'created' : datetime.now(),
        'rightsHolder' : '台灣生物多樣性網絡 TBN',
        'occurrenceID' : row.occurrenceID,
        'originalScientificName' : row.originalVernacularName, 
        'sourceScientificName' : row.scientificName,
        'basisOfRecord' : row.basisOfRecord,
        'sourceVernacularName' : row.vernacularName,
        'eventDate' : row.eventDate,
        'standardDate' : converted_date,
        'verbatimLongitude' : row.decimalLongitude,
        'verbatimLatitude' : row.decimalLatitude,
        'verbatimCoordinateSystem' : 'DecimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
        'verbatimSRS' : row.geodeticDatum,
        'standardLongitude' : standardLon,
        'standardLatitude' : standardLat,
        'coordinateUncertaintyInMeters' : coordinateUncertaintyInMeters,
        'dataGeneralizations' : row.dataGeneralizations,
        'coordinatePrecision' : row.coordinatePrecision,
        'sensitiveCategory' : row.sensitiveCategory,
        'locality' : row.eventPlaceAdminarea,
        'organismQuantity' : row.organismQuantity if row.individualCount in [None,'',nan] else row.individualCount,
        'standardOrganismQuantity' : quantity,
        'organismQuantityType' : row.organismQuantityType,
        'recordedBy' : row.recordedBy, 
        'datasetName': row.datasetName,
        'resourceContacts' : row.resourceContacts,
        'references' : f"https://www.tbn.org.tw/occurrence/{row.occurrenceID}" if row.occurrenceID else None, 
        'license' : row.license,
        'mediaLicense' : row.mediaLicense,
        'selfProduced' : row.selfProduced,
        'collectionID' : c_list_str,
        'associatedMedia' : row.associatedMedia,
        'recordNumber' : recordNumber,
        'scientificNameID' : scientificNameID,
        'preservation' : None,
        'taxonID' : row.get('taxon_id'),
        'location_rpt' : location_rpt,
        }
    row_list.append(tmp)


final = pd.DataFrame(row_list)

# 確認有無限制型資料
if len(final[final.dataGeneralizations==True]) > 1:
    request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000&apikey=9c98309a-880c-4eb3-b1fa-c2ecafb744db"
    response = requests.get(request_url)
    data = response.json()
    len_of_data = data['meta']['total'] # 43242
    j = 0
    total_data = data["data"]
    while data['links']['next'] != "":
        print('get:'+d)
        request_url = data['links']['next']
        response = requests.get(request_url)
        data = response.json()
        total_data += data["data"]
        j += 1
    x = pd.DataFrame(total_data)
    # 如果有模糊化才撈
    x = x[x.dataGeneralizations==True]
    if len(x) > 1:
        x = x.reset_index()
        # 只取經緯度
        x = x[['occurrenceID','decimalLatitude','decimalLongitude']]
        for i in x.index:
            standardLon, standardLat, location_rpt = None, None, None
            row = x.iloc[i]
            # standardLon = float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None
            # standardLat = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None
            # if standardLon and standardLat:
            #     if -180 <= standardLon  and standardLon <= 180 and -90 <= standardLat and standardLat <= 90:
            #         location_rpt = f'POINT({standardLon} {standardLat})' 
            try:
                standardLon = float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None
            except:
                standardLon = None
            if standardLon:
                if not (-180 <= standardLon  and standardLon <= 180):
                    standardLon = None
            try:
                standardLat = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None
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
            x['standardRawLatitude'] = standardLat
            x['standardRawLongitude'] = standardLon
            x['raw_location_rpt'] = location_rpt
        x = x.rename(columns={'decimalLatitude':'verbatimRawLatitude','decimalLongitude':'verbatimRawLongitude'})
        final = final.merge(x,on='occurrenceID',how='left')

# merge with taxa info
# final = pd.read_csv('/Users/taibif/Documents/GitHub/tbia-volumes/solr/csvs/new_2022_11/248d6799-bb66-40a5-b7ba-b45bbb818ddc.csv')
final = final.merge(taicol,how='left', on="taxonID")

final = final.replace({nan: None})

final.scientificNameID = final.scientificNameID.apply(lambda x: str(x).replace('None', '').replace('.0', ''))

final['group'] = 'tesri'




final['grid_x_1'] = -1
final['grid_y_1'] = -1
final['grid_x_5'] = -1
final['grid_y_5'] = -1
final['grid_x_10'] = -1
final['grid_y_10'] = -1
final['grid_x_100'] = -1
final['grid_y_100'] = -1
# for i in range(len(df)):
for i in range(len(final)):
    # print(i)
    if i % 1000 == 0:
        print(i)
    if not pd.isna(final.iloc[i].standardLatitude) and not pd.isna(final.iloc[i].standardLongitude):
        grid_x, grid_y = convert_coor_to_grid(final.iloc[i].standardLongitude, final.iloc[i].standardLatitude, 0.01)
        final.iloc[i, final.columns.get_loc('grid_x_1')] = grid_x
        final.iloc[i, final.columns.get_loc('grid_y_1')] = grid_y
        grid_x, grid_y = convert_coor_to_grid(final.iloc[i].standardLongitude, final.iloc[i].standardLatitude, 0.05)
        final.iloc[i, final.columns.get_loc('grid_x_5')] = grid_x
        final.iloc[i, final.columns.get_loc('grid_y_5')] = grid_y
        grid_x, grid_y = convert_coor_to_grid(final.iloc[i].standardLongitude, final.iloc[i].standardLatitude, 0.1)
        final.iloc[i, final.columns.get_loc('grid_x_10')] = grid_x
        final.iloc[i, final.columns.get_loc('grid_y_10')] = grid_y
        grid_x, grid_y = convert_coor_to_grid(final.iloc[i].standardLongitude, final.iloc[i].standardLatitude, 1)
        final.iloc[i, final.columns.get_loc('grid_x_100')] = grid_x
        final.iloc[i, final.columns.get_loc('grid_y_100')] = grid_y



for i in final.index:
    if i % 1000 == 0:
        print(i)
    row = final.iloc[i]
    try:
        coordinateUncertaintyInMeters = str(int(row.coordinateUncertaintyInMeters))
    except:
        coordinateUncertaintyInMeters = row.coordinateUncertaintyInMeters
    try:
        recordNumber = str(int(row.recordNumber))
    except:
        recordNumber = row.recordNumber
    final.loc[i,'coordinateUncertaintyInMeters'] = coordinateUncertaintyInMeters
    final.loc[i,'recordNumber'] = recordNumber


# 改成不要區分
final = final.replace({nan: None})
final.to_csv(f'/Users/taibif/Documents/GitHub/tbia-volumes/solr/csvs/new_2022_11/248d6799-bb66-40a5-b7ba-b45bbb818ddc.csv', index=False)


final.to_csv(f'~/tbia-volumes/solr/csvs/tbn_test_202211/{d}.csv', index=False)


print('done!')
    # df_occ = final[final['recordType']=='occ']
    # df_col = final[final['recordType']=='col']

    # if len(df_occ):
    #     df_occ.to_csv(f'/tbia-volumes/solr/csvs/occ/{d}.csv', index=False)

    # if len(df_col):
    #     df_col.to_csv(f'/tbia-volumes/solr/csvs/col/{d}.csv', index=False)






# https://www.tbn.org.tw/api/v25/occurrence?UUID=74c38f9a-1830-429b-a7b7-a782c4f7f908&limit=1000&apikey=9c98309a-880c-4eb3-b1fa-c2ecafb744db
