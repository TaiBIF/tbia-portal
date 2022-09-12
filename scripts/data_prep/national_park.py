# 2022-09-06
# 取得國家公園資料

# occurrenceID occurrenceID
# 調查日期 eventDate
# 調查時間 不存
# 原始資料紀錄 originalScientificName
# 鑑定層級 不存
# 分類名稱 不存
# 中文俗名 sourceVernacularName
# 學名 sourceScientificName
# 數量 organismQuantity
# 數量單位 organismQuantityType
# 調查方法 不存
# 調查者 recordedBy
# 鑑定者 不存
# 經度 verbatimLongitude
# 緯度 verbatimLatitude
# 國家(自然)公園 locality
# 不準度 coordinateUncertaintyInMeters 不存
# 備註 不存 
# 座標是否有模糊化 dataGeneralizations
# TaiCoL物種代碼 scientificNameID
# 計畫名稱 存成資料集名稱？ datasetName
# 計畫主持人 存成資料集聯絡人？ resourceContacts
# 資料建立日期 sourceCreated
# 資料更新日期 sourceModified
#-------
# verbatimCoordinateSystem:均為WGS84。 -> decimalDegrees
# verbatimSRS:均為EPSG:4326。 -> WGS84
# taxonID:TaiCoL尚未有此欄位可供對應。
# basisOfRecord:應皆可套用為occurrence標籤屬性。 -> 改成HumanObservation
# references:目前並未提供每一筆資料的URL連結，應可統一放置開放資料專區連結頁面https://npgis.cpami.gov.tw/newpublic/open-data。 -> 不放
# license:原則上均採CC-BY格式。

# rightsHolder: 臺灣國家公園生物多樣性資料庫

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
from conf.settings import env

taicol = pd.read_csv('/tbia-volumes/solr/csvs/source_taicol_for_tbia_20220905.csv')
taicol = taicol.rename(columns={'id': 'taxonID'})
taicol = taicol.drop(columns=['scientificNameID'])

# TaiCOL新舊namecode對應
namecodes = pd.read_csv('/tbia-volumes/bucket/namecode_to_taxon_name_id.csv')

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


import glob

folder = '/tbia-volumes/bucket/national_park/'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension)) # 12



col_dict = { '調查日期': 'eventDate',
 '原始資料紀錄': 'originalScientificName',
 '中文俗名': 'sourceVernacularName',
 '學名': 'sourceScientificName',
 '數量': 'organismQuantity',
 '數量單位': 'organismQuantityType',
 '調查者': 'recordedBy',
 '經度': 'verbatimLongitude',
 '緯度': 'verbatimLatitude',
 '國家(自然)公園': 'locality',
 '座標是否有模糊化': 'dataGeneralizations',
 'TaiCoL物種代碼': 'scientificNameID',
 '計畫名稱':  'datasetName',
 '計畫主持人':  'resourceContacts',
 '資料建立日期': 'sourceCreated',
 '資料更新日期': 'sourceModified'}


# TODO 目前沒有未模糊化的原始資料，之後若有需要修改

for f in files:
    df = pd.read_csv(f'/tbia-volumes/bucket/national_park/{f}', encoding='big5hkscs')
    df['taxon_id'] = ''
    df = df.rename(columns=col_dict)
    sci_names = df.sourceScientificName.unique()
    unique_sci = [x for x in sci_names if str(x) != 'nan']
    count = 0
    for s in unique_sci:
        count +=1
        print(count)
        request_url = f"http://18.183.59.124/v1/nameMatch?name={s}"    
        response = requests.get(request_url)
        if response.status_code == 200:
            data = response.json()
            if data['info']['total'] == 1: # 只對到一個taxon
                df.loc[df.sourceScientificName==s,'taxon_id'] = data['data'][0]['taxon_id']
        # TODO 沒對到的另外處理, 有可能是同名異物
    # 如果沒對到taxon 看原資料庫有沒有提供namecode 有的話直接對應taxon id
    for n in df[df.taxon_id.isnull()].index:
        nc = df.loc[n,'scientificNameID']
        if len(namecodes[namecodes.namecode==nc])==1:
            taxon_name_id = namecodes[namecodes.namecode==nc].taxon_name_id.values[0]
            request_url = f"http://18.183.59.124/v1/nameMatch?name_id={taxon_name_id}"    
            response = requests.get(request_url)
            if response.status_code == 200:
                data = response.json()
                if data['info']['total'] == 1: # 只對到一個taxon
                    df.loc[n,'taxon_id'] = data['data'][0]['taxon_id']
    row_list = []
    df = df.replace({nan: None})
    for i in df.index:
        if i % 1000 == 0:
            print(i)
        row = df.iloc[i]
        try:
            if row.organismQuantity:
                quantity = float(row.organismQuantity)
            else:
                quantity = None
        except:
            quantity = None
        try:
            standardLon = float(row.verbatimLongitude) 
        except:
            standardLon = None
        try:
            standardLat = float(row.verbatimLatitude) 
        except:
            standardLat = None
        if standardLon and standardLat:
            if -180 <= standardLon  and standardLon <= 180 and -90 <= standardLat and standardLat <= 90:
                location_rpt = f'POINT({standardLon} {standardLat})' 
        else:
            location_rpt = None
        # sensitiveCategory:目前釋出之資料如有模糊化皆採輕度模糊化程度。
        # coordinatePrecision:如有模糊化之欄位皆為0.01。
        if row.dataGeneralizations:
            sensitiveCategory, coordinatePrecision = '輕度', 0.01
        else:
            sensitiveCategory, coordinatePrecision = None, None
        tmp = {
            'recordType' : 'occ', # 皆為
            'id' : bson.objectid.ObjectId(),
            'sourceModified' : convert_date(str(row.sourceModified)),
            'sourceCreated' : convert_date(str(row.sourceCreated)), 
            'modified' : datetime.now(),
            'created' : datetime.now(),
            'rightsHolder' : '臺灣國家公園生物多樣性資料庫',
            'occurrenceID' : row.occurrenceID,
            'originalScientificName' : row.originalScientificName, 
            'sourceScientificName' : row.sourceScientificName,
            'sourceVernacularName' : row.sourceVernacularName,
            'eventDate' : row.eventDate,
            'standardDate' : convert_date(str(row.eventDate)),
            'verbatimLongitude' : row.verbatimLongitude,
            'verbatimLatitude' : row.verbatimLatitude,
            'verbatimCoordinateSystem' : 'decimalDegrees' if row.verbatimLongitude and row.verbatimLatitude else None,
            'verbatimSRS' : 'WGS84',
            'standardLongitude' : standardLon,
            'standardLatitude' : standardLat,
            'dataGeneralizations' : row.dataGeneralizations,
            'locality' : row.locality,
            'organismQuantity' : row.organismQuantity,
            'standardOrganismQuantity' : quantity,
            'organismQuantityType' : row.organismQuantityType,
            'recordedBy' : row.recordedBy, 
            'basisOfRecord' : '人為觀察',
            'datasetName' : row.datasetName,
            'resourceContacts' : row.resourceContacts,
            'license' : 'CC-BY',
            'selfProduced' : True,
            'taxonID' : row.get('taxon_id'),
            'location_rpt' : location_rpt,
            'scientificNameID': row.scientificNameID
            }
        row_list.append(tmp)
    final = pd.DataFrame(row_list)
    final = final.merge(taicol,how='left',on="taxonID")
    final = final.replace({nan: None})
    final.scientificNameID = final.scientificNameID.apply(lambda x: str(x).replace('None', '').replace('.0', ''))
    final.to_csv(f'/tbia-volumes/solr/csvs/get/{f}', index=False)


print('done!')