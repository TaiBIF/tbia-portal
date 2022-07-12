# script for TBN API version 2.5


# test for TBN API

import re
from numpy import nan
import requests
import pandas as pd
from data.models import *
from datetime import datetime, tzinfo,timedelta
from dateutil import parser
import bson
import time
import os

taicol = pd.read_csv('/tbia-volumes/solr/csvs/source_taicol_for_tbia_20220707.csv')
taicol = taicol.rename(columns={'id': 'taxonID'})


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


# request_url = "https://www.tbn.org.tw/api/v25/dataset?modified=1000-01-01"
# response = requests.get(request_url)
# data = response.json()
# len_of_data = data['meta']['total'] # 1452
# j = 0
# total_data = data["data"]
# while data['links']['next'] != "":
#     request_url = data['links']['next']
#     response = requests.get(request_url)
#     data = response.json()
#     total_data += data["data"]
#     j += 1
# df = pd.DataFrame(total_data)

# for i in df.index:
#     print(i)
#     request_url = f'https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={df.datasetUUID[i]}&limit=1'
#     response = requests.get(request_url)
#     data = response.json()
#     d = data["data"]
#     if d:
#         df.loc[i, 'selfProduced'] = d[0].get('selfProduced')

# # 只取自產資料
# datasets = df[df.selfProduced==True].datasetUUID.to_list() # 46

# # 536dbfa2-6972-495c-a051-77312f04072b
# # 6f689983-76a3-4d82-a393-ab731c5655da
# # 97c21d3f-774b-45e7-9149-4c0697fadbde

# for d in datasets:
#     print('get:'+d)
#     request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000"
#     response = requests.get(request_url)
#     data = response.json()
#     len_of_data = data['meta']['total'] # 43242
#     j = 0
#     total_data = data["data"]
#     while data['links']['next'] != "":
#         print('get:'+d)
#         request_url = data['links']['next']
#         response = requests.get(request_url)
#         data = response.json()
#         total_data += data["data"]
#         j += 1
#     df = pd.DataFrame(total_data)
#     df.to_csv(f"/tbia-volumes/bucket/tbn_v25/{d}.csv")


# 學名比對

import glob

folder = '/tbia-volumes/bucket/tbn_v25/'
# tbn_path = '/Users/taibif/Documents/GitHub/tbia-volumes/tbn_data'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))
# len_f = len(files)

for f in files:
    d = f.split('.csv')[0]
    print(d)
    df = pd.read_csv(f'/tbia-volumes/bucket/tbn_v25/{f}', index_col=0)

    sci_names = df.simplifiedScientificName.unique()
    unique_sci = [x for x in sci_names if str(x) != 'nan']

    for s in unique_sci:
        request_url = f"http://18.183.59.124/v1/nameMatch?name={s}"    
        response = requests.get(request_url)
        if response.status_code == 200:
            data = response.json()
            if data['info']['total'] == 1: # 只對到一個taxon
                df.loc[df.simplifiedScientificName==s,'taxon_id'] = data['data'][0]['taxon_id']
        # TODO 沒對到的另外處理, 有可能是同名異物
        
    row_list = []

    df = df.replace({nan: None})

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
        standardLon = float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None
        standardLat = float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None
        location_rpt = f'POINT({standardLon} {standardLat})' if standardLon and standardLat else None
        tmp = {
            'recordType' : 'occ' if '標本' not in str(row.basisOfRecord) else 'col',
            'id' : bson.objectid.ObjectId(),
            'sourceModified' : convert_date(row.modified),
            'sourceCreated' : None, # TBN沒這個欄位
            'modified' : datetime.now(),
            'created' : datetime.now(),
            'rightsHolder' : 'TBN',
            'occurrenceID' : row.occurrenceID,
            'originalScientificName' : row.originalVernacularName, 
            'sourceScientificName' : row.scientificName,
            'sourceVernacularName' : row.vernacularName,
            'eventDate' : row.eventDate,
            'standardDate' : convert_date(row.eventDate),
            'verbatimLongitude' : row.decimalLongitude,
            'verbatimLatitude' : row.decimalLatitude,
            'verbatimCoordinateSystem' : 'decimalDegrees' if row.decimalLongitude and row.decimalLatitude else None,
            'verbatimSRS' : row.geodeticDatum,
            'standardLongitude' : float(row.decimalLongitude) if row.decimalLongitude not in ['', None, '0', 'WGS84'] else None,
            'standardLatitude' : float(row.decimalLatitude) if row.decimalLatitude not in ['', None] else None,
            'coordinateUncertaintyInMeters' : row.coordinateUncertaintyInMeters,
            'dataGeneralizations' : row.dataGeneralizations,
            'coordinatePrecision' : row.coordinatePrecision,
            'locality' : row.eventPlaceAdminarea,
            'organismQuantity' : row.organismQuantity if row.individualCount == '' else row.individualCount,
            'standardOrganismQuantity' : quantity,
            'organismQuantityType' : row.organismQuantityType,
            'recordedBy' : row.recordedBy, 
            'basisOfRecord' : row.basisOfRecord,
            'datasetName' : row.datasetName,
            'resourceContacts' : row.datasetAuthor,
            'references' : f"https://www.tbn.org.tw/occurrence/{row.occurrenceID}",
            'license' : row.license,
            'selfProduced' : row.selfProduced,
            'collectionID' : eval(row.collectionID) if row.collectionID else None,
            'associatedMedia' : row.associatedMedia,
            'recordNumber' : row.recordNumber,
            'preservation' : None,
            'taxonID' : row.get('taxon_id'),
            'location_rpt' : location_rpt,
            'rightsHolder': 'TBN'
            }
        row_list.append(tmp)

    # merge with taxa info

    final = pd.DataFrame(row_list)

    final = final.merge(taicol,how='left')

    final = final.replace({nan: None})

    final.scientificNameID = final.scientificNameID.apply(lambda x: str(x).replace('None', '').replace('.0', ''))

    df_occ = final[final['recordType']=='occ']
    df_col = final[final['recordType']=='col']

    if len(df_occ):
        df_occ.to_csv(f'/tbia-volumes/solr/csvs/occ/{d}.csv', index=False)

    if len(df_col):
        df_col.to_csv(f'/tbia-volumes/solr/csvs/col/{d}.csv', index=False)


