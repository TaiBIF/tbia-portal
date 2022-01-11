import pandas as pd
import numpy as np


def is_alpha(word):
    try:
        return word.encode('ascii').isalpha()
    except:
        return False


dup_col = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c',
            'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c', 'scientificName', 'common_name_c', 
            'alternative_name_c', 'synonyms']


def get_key(val, my_dict):
    for key, value in my_dict.items():
         if val == value:
             return key
 
    return "key doesn't exist"

taicol = pd.read_csv('/tbia-volumes/bucket/TaiwanSpecies20211019_UTF8.csv')
# taicol = pd.read_csv('/Users/taibif/Documents/GitHub/tbia-volumes/TaiwanSpecies20210618_UTF8.csv')
taicol = taicol[taicol['is_accepted_name']==True][['name','common_name_c']]
taicol = taicol.replace({np.nan: ''})
taicol['common_name_c'] = taicol['common_name_c'].apply(lambda x: x.split(';')[0] if x else x)


facet_collection = ['scientificName', 'common_name_c','alternative_name_c', 
                    'synonyms', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'typeStatus', 'preservation', 'datasetName', 'license',
                    'kingdom','phylum','class','order','family','genus','species',
                    'kingdom_c','phylum_c','class_c','order_c','family_c','genus_c']

facet_occurrence = ['scientificName', 'common_name_c', 'alternative_name_c', 
                    'synonyms', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'license',
                    'kingdom','phylum','class','order','family','genus','species',
                    'kingdom_c','phylum_c','class_c','order_c','family_c','genus_c']

map_occurrence = {
    'kingdom':'界',
    'phylum':'門',
    'class':'綱',
    'order':'目',
    'family':'科',
    'genus':'屬',
    'species':'種',
    'kingdom_c':'界中文名',
    'phylum_c':'門中文名',
    'class_c':'綱中文名',
    'order_c':'目中文名',
    'family_c':'科中文名',
    'genus_c':'屬中文名',
    'common_name_c': '中文名', 
    'scientificName': '學名',
    'alternative_name_c': '中文別名', 
    'synonyms': '同物異名',
    'taxonRank': '分類層級', 
    'sensitiveCategory': '敏感層級', 
    'rightsHolder': '來源資料庫', 
    'scientificNameID': 'Name Code', 
    'eventDate': '紀錄日期', 
    'locality': '出現地', 
    'organismQuantity': '數量',
    'organismQuantityType': '數量單位',
    'recordedBy': '紀錄者', 
    'verbatimLongitude': '經度',
    'verbatimLatitude': '緯度',
    'verbatimSRS': '空間參考系統',
    'verbatimCoordinateSystem': '座標系統',
    'coordinateUncertaintyInMeters': '座標誤差',
    'dataGeneralizations': '座標是否有模糊化',
    'coordinatePrecision': '座標模糊化程度',
    'basisOfRecord': '資料基底', 
    'datasetName': '資料集名稱', 
    'resourceContacts': '資料集聯絡人',
    'license': '授權狀況',
    'sourceScientificName': '原資料庫使用學名',
    'sourceVernacularName': '原資料庫使用中文名',
}

map_collection = {
    'kingdom':'界',
    'phylum':'門',
    'class':'綱',
    'order':'目',
    'family':'科',
    'genus':'屬',
    'species':'種',
    'kingdom_c':'界中文名',
    'phylum_c':'門中文名',
    'class_c':'綱中文名',
    'order_c':'目中文名',
    'family_c':'科中文名',
    'genus_c':'屬中文名',
    'common_name_c': '中文名', 
    'scientificName': '學名', 
    'alternative_name_c': '中文別名', 
    'synonyms': '同物異名',
    'rightsHolder': '典藏單位', 
    'scientificNameID': 'Name Code', 
    'collectionID': '館藏號', 
    'taxonRank': '分類層級', 
    'sensitiveCategory': '敏感層級', 
    'typeStatus': '標本類型', 
    'preservation': '保存方式', 
    'eventDate': '採集日期', 
    'locality': '採集地', 
    'recordedBy': '採集者', 
    'recordNumber': '採集號', 
    'organismQuantity': '數量',
    'organismQuantityType': '數量單位',
    'verbatimLongitude': '經度',
    'verbatimLatitude': '緯度',
    'verbatimCoordinateSystem': '座標系統',
    'verbatimSRS': '空間參考系統',
    'coordinateUncertaintyInMeters': '座標誤差',
    'dataGeneralizations': '座標是否有模糊化',
    'coordinatePrecision': '座標模糊化程度',
    'datasetName': '資料集名稱', 
    'resourceContacts': '資料集聯絡人',
    'license': '授權狀況',
    'sourceScientificName': '原資料庫使用學名',
    'sourceVernacularName': '原資料庫使用中文名',
}
