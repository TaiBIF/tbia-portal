import pandas as pd
import numpy as np
import math
from dateutil import parser
from datetime import datetime #, timedelta
import numpy as np
import bisect
import os
from os.path import exists
from conf.settings import datahub_db_settings
import psycopg2
from django.db.models import Q
import requests
from conf.settings import SOLR_PREFIX, env
import html
import geopandas as gpd
import shapely.wkt as wkt
from shapely.geometry import MultiPolygon
import json
import re
from data.solr_query import *
from pages.templatetags.tags import highlight, get_variants
from django.utils import timezone, translation
from django.utils.translation import gettext
from manager.models import User, Partner, SearchStat, SearchQuery, Ark
from pages.models import News
# import time
# from urllib import parse
import threading
import random
import string

# taxon-related fields
taxon_facets = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'taxonRank', 'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c', 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c']
taxon_keyword_list = taxon_facets + ['sourceScientificName','sourceVernacularName','taxonID','originalScientificName']


name_status_map = {
    'not-accepted': '的無效名',
    'misapplied': '的誤用名',
}


basis_map = {
    "HumanObservation":"人為觀測",
    "MachineObservation":"機器觀測",
    "PreservedSpecimen":"保存標本",
    "MaterialSample":"材料樣本",
    "LivingSpecimen":"活體標本",
    "FossilSpecimen":"化石標本",
    "MaterialCitation":"文獻紀錄",
    "MaterialEntity":"材料實體",
    "Taxon":"分類群",
    "Occurrence":"出現紀錄",
    "Event":"調查活動"
}


def get_dataset_name(key):
    # 2024-12 修改為tbiaDatasetID
    name = ''

    response = requests.get(f'{SOLR_PREFIX}dataset/select?q.op=OR&q=id:{key} OR tbiaDatasetID:{key}&rows=20&fq=deprecated:false')
    print(f'{SOLR_PREFIX}dataset/select?q.op=OR&q=id:{key} OR tbiaDatasetID:{key}&rows=20&fq=deprecated:false')
    d_list = response.json()['response']['docs']

    # solr內的id和datahub的postgres互通
    for l in d_list:
        name = l['name'] 
        if l.get('is_duplicated_name'):
            name += ' ({})'.format(l['rights_holder'])
    return name



def get_tbia_dataset_id(key):
    # 2024-12 修改為tbiaDatasetID
    results = None
    conn = psycopg2.connect(**datahub_db_settings)
    try:
        key = int(key)        
        query = 'SELECT "tbiaDatasetID" FROM dataset WHERE "id" = %s' # 不考慮deprecated
        with conn.cursor() as cursor:
            cursor.execute(query, (key,))
            results = cursor.fetchone()
    except:
        query = 'SELECT "tbiaDatasetID" FROM dataset WHERE "tbiaDatasetID" = %s' # 不考慮deprecated
        with conn.cursor() as cursor:
            cursor.execute(query, (key,))
            results = cursor.fetchone()
    conn.close()
    if results:
        results = results[0]
    return results


def get_species_images(taxon_id):
    conn = psycopg2.connect(**datahub_db_settings)
    query = "SELECT taieol_id, images FROM species_images WHERE taxon_id = %s"
    with conn.cursor() as cursor:
        cursor.execute(query, (taxon_id,))
        results = cursor.fetchone()
        conn.close()
    return results


def get_dataset_by_key(key_list):
    
    results = []
    conn = psycopg2.connect(**datahub_db_settings)
    
    query = f''' select "tbiaDatasetID", name FROM dataset WHERE "tbiaDatasetID" IN %s AND deprecated = 'f' '''

    with conn.cursor() as cursor:
        cursor.execute(query, (tuple(key_list), ))
        results = cursor.fetchall()
        conn.close()
        
    return results


spe_chars = ['+','-', '&','&&', '||', '!','(', ')', '{', '}', '[', ']', '^', '"', '~', '*', '?', ':', '/']

def escape_solr_query(string):
    final_string = ''
    for s in string:
        if s in spe_chars:
            final_string += f'\{s}'
        else:
            final_string += s
    return final_string


# x: longtitude, y: latitude


# 舊的
old_taxon_group_map_c = {
    'Plants' : '維管束植物',
    # 'Others': '其他', 沒有可以對應的 不讓他選
}


taxon_group_map_c = {
    'Insects' : '昆蟲',
    'Spiders' : '蜘蛛',
    'Fishes' : '魚類',
    'Reptiles' : '爬蟲類',
    'Amphibians': '兩棲類',
    'Birds' : '鳥類',
    'Mammals' : '哺乳類',
    'Vascular Plants' : '維管束植物',
    'Ferns' : '蕨類植物',
    'Mosses' : '苔蘚植物',
    'Algae' : '藻類',
    'Viruses': '病毒',
    'Bacteria': '細菌',
    'Fungi': '真菌',
    'Others': '其他'
}

taxon_group_map_e = {
    "昆蟲": "Insects",
    "蜘蛛": "Spiders",
    "魚類": "Fishes",
    "爬蟲類": "Reptiles",
    "兩棲類": "Amphibians",
    "鳥類": "Birds",
    "哺乳類": "Mammals",
    "維管束植物": "Vascular Plants",
    "蕨類植物": "Ferns",
    "苔蘚植物": "Mosses",
    "藻類": "Algae",
    "病毒": "Viruses",
    "細菌": "Bacteria",
    "真菌": "Fungi",
}


taxon_group_map_tbn = {
    "昆蟲": "beetles,butterflies,moths,dragonflies,otherinsects",
    "蜘蛛": "spiders",
    "魚類": "fishes",
    "爬蟲類": "reptiles",
    "兩棲類": "amphibians",
    "鳥類": "birds",
    "哺乳類": "mammals",
    "維管束植物": "lycophytes,gymnosperms,angiosperms,ferns",
    "蕨類植物": "ferns",
    "苔蘚植物": "ferns",
    # "藻類": "Algae",
    # "病毒": "Viruses",
    # "細菌": "Bacteria",
    "真菌": "fungi",
}



def convert_coor_to_grid(x, y, grid):
    list_x = np.arange(-180, 180+grid, grid)
    list_y = np.arange(-90, 90+grid, grid)
    grid_x = bisect.bisect(list_x, x)-1
    grid_y = bisect.bisect(list_y, y)-1
    return grid_x, grid_y

def convert_grid_to_square(grid_x, grid_y, grid):
    list_x = np.arange(-180, 180+grid, grid)
    list_y = np.arange(-90, 90+grid, grid)
    x1 = round(list_x[grid_x],4)
    x2 = round(list_x[grid_x+1],4)
    y1 = round(list_y[grid_y],4)
    y2 = round(list_y[grid_y+1],4)
    return [[x1,y1],[x2,y1],[x2,y2],[x1,y2],[x1,y1]]

def format_grid(grid_x, grid_y, grid, count):
    dic = {
            "type": "Feature",
            "geometry":{"type":"Polygon","coordinates":[convert_grid_to_square(grid_x, grid_y, grid/100)]},
            "properties": {
                "counts": count
            }
        }
    return dic

rank_list = ['domain', 'superkingdom', 'kingdom', 'subkingdom', 'infrakingdom', 'superdivision', 'division', 'subdivision', 
            'infradivision', 'parvdivision', 'superphylum', 'phylum', 'subphylum', 'infraphylum', 'microphylum', 'parvphylum', 
            'superclass', 'class', 'subclass', 'infraclass', 'superorder', 'order', 'suborder', 'infraorder', 'superfamily', 'family', 
            'subfamily', 'tribe', 'subtribe', 'genus', 'subgenus', 'section', 'subsection', 'species', 'subspecies', 'nothosubspecies', 
            'variety', 'subvariety', 'nothovariety', 'form', 'subform', 'specialform', 'race', 'stirp', 'morph', 'aberration', 'hybridformula']


def get_page_list(current_page, total_page, window=5):
  list_index = math.ceil(current_page/window)
  if list_index*window > total_page:
    page_list = list(range(list_index*window-(window-1),total_page+1))
  else:
    page_list = list(range(list_index*window-(window-1),list_index*window+1))
  return page_list


def is_alpha(word):
    try:
        return word.encode('ascii').isalpha()
    except:
        return False


# 進階搜尋查詢name欄位
name_search_col = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'sourceScientificName', 'sourceVernacularName', 'originalScientificName']

def get_key(val, my_dict):
    for key, value in my_dict.items():
         if val == value:
             return key
    return "key doesn't exist"

map_occurrence = {
    'associatedMedia': '影像',
    'domain'	:'域',
    'superkingdom'	:'總界',
    'kingdom'	:'界',
    'subkingdom'	:'亞界',
    'infrakingdom'	:'下界',
    'superdivision'	:'超部|總部',
    'division'	:'部|類',
    'subdivision'	:'亞部|亞類',
    'infradivision'	:'下部|下類',
    'parvdivision'	:'小部|小類',
    'superphylum'	:'超門|總門',
    'phylum'	:'門',
    'subphylum'	:'亞門',
    'infraphylum'	:'下門',
    'microphylum'	:'微門',
    'parvphylum'	:'小門',
    'superclass'	:'超綱|總綱',
    'class'	:'綱',
    'subclass'	:'亞綱',
    'infraclass'	:'下綱',
    'superorder'	:'超目|總目',
    'order'	:'目',
    'suborder'	:'亞目',
    'infraorder'	:'下目',
    'superfamily'	:'超科|總科',
    'family'	:'科',
    'subfamily'	:'亞科',
    'tribe'	:'族',
    'subtribe'	:'亞族',
    'genus'	:'屬',
    'subgenus'	:'亞屬',
    'section'	:'組|節',
    'subsection'	:'亞組|亞節',
    'species'	:'種',
    'subspecies'	:'亞種',
    'nothosubspecies'	:'雜交亞種',
    'variety'	:'變種',
    'subvariety'	:'亞變種',
    'nothovariety'	:'雜交變種',
    'form'	:'型',
    'subform'	:'亞型',
    'special form'	:'特別品型',
    'race'	:'種族',
    'stirp'	:'血統',
    'morph'	:'形態型',
    'aberration'	:'異常個體',
    'hybrid formula'	:'雜交組合',
    'domain_c'	:'域中文名',
    'superkingdom_c'	:'總界中文名',
    'kingdom_c'	:'界中文名',
    'subkingdom_c'	:'亞界中文名',
    'infrakingdom_c'	:'下界中文名',
    'superdivision_c'	:'超部|總部中文名',
    'division_c'	:'部|類中文名',
    'subdivision_c'	:'亞部|亞類中文名',
    'infradivision_c'	:'下部|下類中文名',
    'parvdivision_c'	:'小部|小類中文名',
    'superphylum_c'	:'超門|總門中文名',
    'phylum_c'	:'門中文名',
    'subphylum_c'	:'亞門中文名',
    'infraphylum_c'	:'下門中文名',
    'microphylum_c'	:'微門中文名',
    'parvphylum_c'	:'小門中文名',
    'superclass_c'	:'超綱|總綱中文名',
    'class_c'	:'綱中文名',
    'subclass_c'	:'亞綱中文名',
    'infraclass_c'	:'下綱中文名',
    'superorder_c'	:'超目|總目中文名',
    'order_c'	:'目中文名',
    'suborder_c'	:'亞目中文名',
    'infraorder_c'	:'下目中文名',
    'superfamily_c'	:'超科|總科中文名',
    'family_c'	:'科中文名',
    'subfamily_c'	:'亞科中文名',
    'tribe_c'	:'族中文名',
    'subtribe_c'	:'亞族中文名',
    'genus_c'	:'屬中文名',
    'subgenus_c'	:'亞屬中文名',
    'section_c'	:'組|節中文名',
    'subsection_c'	:'亞組|亞節中文名',
    'species_c'	:'種中文名',
    'subspecies_c'	:'亞種中文名',
    'nothosubspecies_c'	:'雜交亞種中文名',
    'variety_c'	:'變種中文名',
    'subvariety_c'	:'亞變種中文名',
    'nothovariety_c'	:'雜交變種中文名',
    'form_c'	:'型中文名',
    'subform_c'	:'亞型中文名',
    'special form_c'	:'特別品型中文名',
    'race_c'	:'種族中文名',
    'stirp_c'	:'血統中文名',
    'morph_c'	:'形態型中文名',
    'aberration_c'	:'異常個體中文名',
    'hybrid formula_c'	:'雜交組合中文名',
    'higherTaxa'	:'較高分類群',
    'taxonGroup'	:'物種類群',
    'scientificName': '學名',
    'common_name_c': '中文名', 
    'alternative_name_c': '中文別名', 
    'synonyms': '同物異名',
    'misapplied': '誤用名',
    'sourceScientificName': '來源資料庫使用學名',
    'sourceVernacularName': '來源資料庫使用中文名',
    'originalScientificName': '原始紀錄物種',
    'bioGroup': '物種類群', 
    'taxonRank': '鑑定層級', 
    'sensitiveCategory': '敏感層級', 
    'rightsHolder': '來源資料庫', 
    'taxonID': 'TaiCOL物種編號', 
    'eventDate': '紀錄日期', 
    'county': '縣市',
    'municipality': '鄉鎮市區',
    'date': '紀錄日期', 
    'locality': '出現地', 
    'organismQuantity': '數量',
    'quantity': '數量',
    'organismQuantityType': '數量單位',
    'recordedBy': '記錄者', 
    'verbatimLongitude': '經度',
    'verbatimLatitude': '緯度',
    'lon': '經度',
    'lat': '緯度',
    'verbatimSRS': '空間參考系統',
    'verbatimCoordinateSystem': '座標系統',
    'coordinateUncertaintyInMeters': '座標誤差（公尺）',
    'dataGeneralizations': '座標是否有模糊化',
    'coordinatePrecision': '座標模糊化程度',
    'basisOfRecord': '紀錄類型', 
    'datasetName': '資料集名稱', 
    'resourceContacts': '資料集聯絡人',
    'license': '授權狀況',
    'occurrenceID': 'occurrenceID',
    'grid_1': '1公里網格編號',
    'grid_5': '5公里網格編號',
    'grid_10': '10公里網格編號',
    'grid_100': '100公里網格編號',
}

# 抓出collection和occurrence不一樣的地方
map_collection = { key: value for (key, value) in map_occurrence.items() }
map_collection.update({
    'eventDate': '採集日期',
    'date': '採集日期',
    'locality': '採集地',
    'recordedBy': '採集者',
    'recordNumber': '採集號',
    'typeStatus': '標本類型',
    'preservation': '保存方式',
    'catalogNumber': '館藏號'
})


date_formats = ['%Y/%m/%d','%Y%m%d','%Y-%m-%d','%Y/%m/%d %H:%M:%S','%Y-%m-%d %H:%M',
                '%Y/%m/%d %H:%M','%Y-%m-%d %H:%M:%S','%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %p %I:%M:%S', '%Y/%m/%d %H', '%Y-%m-%d %H', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']
# 要和datahub同步
def convert_date(date):
    formatted_date = None
    if date != '' and date is not None:
        date = str(date)
        date = date.replace('上午','AM').replace('下午','PM')
        for ff in date_formats:
            try:
                formatted_date = datetime.strptime(date, ff)
                return formatted_date
            except:
                formatted_date = None
        if not formatted_date:
            try:
                formatted_date = parser.parse(date)
            except:
                formatted_date = None
        if not formatted_date:
            try: 
                date = date.split('T')[0]
                formatted_date = datetime.strptime(date, '%Y-%m-%d')
                return formatted_date
            except:
                formatted_date = None        
        if not formatted_date:
            try:
                formatted_date = datetime.fromtimestamp(int(date))
                return formatted_date
            except:
                formatted_date = None
    return formatted_date


download_cols = [
'id',
'created',
'modified',
'standardDate',
'standardLatitude',
'standardLongitude',
'standardOrganismQuantity',
'associatedMedia',
'basisOfRecord',
'catalogNumber',
'coordinatePrecision',
'coordinateUncertaintyInMeters',
'dataGeneralizations',
'datasetName',
'tbiaDatasetID',
'sourceDatasetID',
'gbifDatasetID',
'eventDate',
'county',
'municipality',
'license',
'locality',
'mediaLicense',
'occurrenceID',
'organismQuantity',
'organismQuantityType',
'originalScientificName',
'preservation',
'recordedBy',
'recordNumber',
'references',
'resourceContacts',
'rightsHolder',
'sensitiveCategory',
'sourceCreated',
'sourceModified',
'sourceScientificName',
'sourceVernacularName',
'typeStatus',
'verbatimCoordinateSystem',
'verbatimLatitude',
'verbatimLongitude',
'verbatimSRS',
'scientificNameID',
'taxonID',
'match_higher_taxon',
# 'parentTaxonID',
'scientificName',
'name_author',
'bioGroup',
'taxonRank',
'common_name_c',
'alternative_name_c',
'synonyms',
'misapplied',
'kingdom',
'kingdom_c',
'phylum',
'phylum_c',
'class',
'class_c',
'order',
'order_c',
'family',
'family_c',
'genus',
'genus_c'
]



download_cols_with_sensitive = [
'id',
'created',
'modified',
'standardDate',
'standardLatitude',
'standardLongitude',
'standardOrganismQuantity',
'associatedMedia',
'basisOfRecord',
'catalogNumber',
'coordinatePrecision',
'coordinateUncertaintyInMeters',
'dataGeneralizations',
'datasetName',
'tbiaDatasetID',
'sourceDatasetID',
'gbifDatasetID',
'eventDate',
'county',
'municipality',
'license',
'locality',
'mediaLicense',
'occurrenceID',
'organismQuantity',
'organismQuantityType',
'originalScientificName',
'preservation',
'recordedBy',
'recordNumber',
'references',
'resourceContacts',
'rightsHolder',
'sensitiveCategory',
'sourceCreated',
'sourceModified',
'sourceScientificName',
'sourceVernacularName',
'typeStatus',
'verbatimCoordinateSystem',
'verbatimLatitude',
'verbatimLongitude',
'verbatimSRS',
'scientificNameID',
'taxonID',
'match_higher_taxon',
# 'parentTaxonID',
'scientificName',
'name_author',
'bioGroup',
'taxonRank',
'common_name_c',
'alternative_name_c',
'synonyms',
'misapplied',
'kingdom',
'kingdom_c',
'phylum',
'phylum_c',
'class',
'class_c',
'order',
'order_c',
'family',
'family_c',
'genus',
'genus_c',
'standardRawLatitude',
'standardRawLongitude',
'verbatimRawLatitude',
'verbatimRawLongitude',
'rawCounty',
'rawMunicipality',
]

sensitive_cols = ['standardRawLatitude',
'standardRawLongitude',
'verbatimRawLatitude',
'verbatimRawLongitude',
'rawCounty',
'rawMunicipality',
]


# 整理搜尋條件
def create_query_display(search_dict,lang=None):
    if lang:
        translation.activate(lang)
    query = ''
    if search_dict.get('record_type') == 'occ':
        query += f'<b>{gettext("類別")}</b>{gettext("：")}{gettext("物種出現紀錄")}'
        map_dict = map_occurrence
    else:
        map_dict = map_collection
        query += f'<b>{gettext("類別")}</b>{gettext("：")}{gettext("自然史典藏")}'

    d_list = []
    r_list = []
    l_list = []

    if search_dict.get('current_grid_level') in map_dict.keys() and search_dict.get('current_grid'):
        query += f'<br><b>{gettext(map_dict[search_dict["current_grid_level"]])}</b>{gettext("：")}{search_dict.get("current_grid")}'

    for k in search_dict.keys():
        if k in map_dict.keys():
            if k == 'taxonRank':
                if search_dict[k] == 'sub':
                    query += f'<br><b>{gettext(map_dict[k])}</b>{gettext("：")}{gettext("種下")}'
                else:
                    query += f'<br><b>{gettext(map_dict[k])}</b>{gettext("：")}{gettext(map_dict[search_dict[k]])}'
            elif k == 'datasetName':
                if isinstance(search_dict[k], str):
                    if search_dict[k].startswith('['):
                        for d in eval(search_dict[k]):
                            if d_name := get_dataset_name(d):
                                d_list.append(d_name)
                    else:
                        if d_name := get_dataset_name(search_dict[k]):
                            d_list.append(d_name)
                else:
                    for d in list(search_dict[k]):
                        if d_name := get_dataset_name(d):
                            d_list.append(d_name)
            elif k == 'rightsHolder':
                if isinstance(search_dict[k], str):
                    if search_dict[k].startswith('['):
                        r_list = eval(search_dict[k])
                    else:
                        r_list.append(search_dict[k])
                else:
                    r_list = list(search_dict[k])
                r_list = [gettext(r) for r in r_list]
            elif k == 'locality':
                if isinstance(search_dict[k], str):
                    if search_dict[k].startswith('['):
                        l_list = eval(search_dict[k])
                    else:
                        l_list.append(search_dict[k])
                else:
                    l_list = list(search_dict[k])
            elif k == 'higherTaxa':
                response = requests.get(f'{SOLR_PREFIX}taxa/select?q=id:{search_dict[k]}')
                if response.status_code == 200:
                    resp = response.json()
                    if data := resp['response']['docs']:
                        data = data[0]
                        query += f"<br><b>{gettext(map_dict[k])}</b>{gettext('：')}{data.get('scientificName')} {data.get('common_name_c') if data.get('common_name_c')  else ''}"                    
                # if Taxon.objects.filter(taxonID=search_dict[k]).exists():
                #     taxon_obj = Taxon.objects.get(taxonID=search_dict[k])
            # 這邊要讓新舊互通 因為舊的會需要再次查詢
            elif k == 'taxonGroup':
                if search_dict[k] in taxon_group_map_e.keys():
                    query += f"<br><b>{gettext(map_dict[k])}</b>{gettext('：')}{ taxon_group_map_e[search_dict[k]] if lang == 'en-us' else search_dict[k]}"
                elif search_dict[k] in taxon_group_map_c.keys():
                    query += f"<br><b>{gettext(map_dict[k])}</b>{gettext('：')}{search_dict[k] if lang == 'en-us' else taxon_group_map_c[search_dict[k]] }"
                elif search_dict[k] in old_taxon_group_map_c.keys():
                    query += f"<br><b>{gettext(map_dict[k])}</b>{gettext('：')}{search_dict[k] if lang == 'en-us' else old_taxon_group_map_c[search_dict[k]] }"
            # 需要調整的選單內容
            elif k in ['basisOfRecord','dataGeneralizations']:
                query += f"<br><b>{gettext(map_dict[k])}</b>{gettext('：')}{gettext(search_dict[k])}"
            else:
                query += f"<br><b>{gettext(map_dict[k])}</b>{gettext('：')}{search_dict[k]}"
        # 地圖搜尋
        elif k == 'geo_type':
            if search_dict[k] == 'polygon':
                geojson_path= f"media/geojson/{search_dict.get('geojson_id')}.json"
                if exists(os.path.join('/tbia-volumes/', geojson_path)):
                    query += f"<br><b>{gettext('上傳Polygon')}</b>{gettext('：')}<a target='_blank' href='/{geojson_path}'>{gettext('點此下載GeoJSON')}</a>"
            elif search_dict[k] == 'circle':
                if search_dict.get('circle_radius') and search_dict.get('center_lon') and search_dict.get('center_lat'):
                    query += f"<br><b>{gettext('圓中心框選')}</b>{gettext('：')}{gettext('半徑')} {search_dict.get('circle_radius')} KM {gettext('中心點經度')} {search_dict.get('center_lon')} {gettext('中心點緯度')} {search_dict.get('center_lat')}" 
            elif search_dict[k] == 'map' and search_dict.get('polygon'):
                query += f"<br><b>{gettext('地圖框選')}</b>{gettext('：')}{search_dict.get('polygon')}" 
        # 日期
        elif k == 'start_date':
            query += f"<br><b>{gettext('起始日期')}</b>{gettext('：')}{search_dict.get('start_date')}" 
        elif k == 'end_date':
            query += f"<br><b>{gettext('結束日期')}</b>{gettext('：')}{search_dict.get('end_date')}" 
        elif k == 'name':
            query += f"<br><b>{gettext('學名/中文名/中文別名/同物異名/誤用名')}</b>{gettext('：')}{search_dict.get('name')}" 
        elif k == 'has_image':
            query += f"<br><b>{gettext('有無影像')}</b>{gettext('：')}{gettext('有影像') if search_dict.get('has_image') == 'y' else gettext('無影像')}" 
        elif k == 'is_protected':
            query += f"<br><b>{gettext('是否為保育類')}</b>{gettext('：')}{gettext('是') if search_dict.get('is_protected') == 'y' else gettext('否')}" 
        elif k == 'is_native':
            query += f"<br><b>{gettext('是否為原生種')}</b>{gettext('：')}{gettext('是') if search_dict.get('is_native') == 'y' else gettext('否')}" 
    if r_list:
        r_list = [gettext(r) for r in r_list]
        query += f"<br><b>{gettext('來源資料庫')}</b>{gettext('：')}{'、'.join(r_list)}" 
    if d_list:
        query += f"<br><b>{gettext('資料集名稱')}</b>{gettext('：')}{'、'.join(d_list)}" 
    if l_list:
        query += f"<br><b>{gettext(map_dict['locality'])}</b>{gettext('：')}{'、'.join(l_list)}" 

    return query


# 整理搜尋條件 再次查詢按鈕的連結
def create_query_a(search_dict):
    # 只處理多選 & 需要調整的參數
    query_a = ''

    d_list = []
    r_list = []
    l_list = []

    # 這邊要處理taxonGroup 因為會有新舊的問題
    for k in search_dict.keys():
        if k == 'datasetName':
            if isinstance(search_dict[k], str):
                if search_dict[k].startswith('['):
                    for d in eval(search_dict[k]):
                        d_list.append(d)
                else:
                    d_list.append(search_dict[k])
            else:
                for d in list(search_dict[k]):
                    d_list.append(d)
        elif k == 'rightsHolder':
            if isinstance(search_dict[k], str):
                if search_dict[k].startswith('['):
                    r_list = eval(search_dict[k])
                else:
                    r_list.append(search_dict[k])
            else:
                r_list = list(search_dict[k])
        elif k == 'locality':
            if isinstance(search_dict[k], str):
                if search_dict[k].startswith('['):
                    l_list = eval(search_dict[k])
                else:
                    l_list.append(search_dict[k])
            else:
                l_list = list(search_dict[k])
        
        elif k == 'taxonGroup':
            # 這邊是給網址使用的 所以參數是taxonGroup
            if search_dict[k] in taxon_group_map_e.keys():
                query_a += f'&taxonGroup={search_dict[k]}'
            elif search_dict[k] in taxon_group_map_c.keys(): #這邊要讓新舊互通 因為舊的會需要再次查詢 舊的會是英文
                query_a += f'&taxonGroup={taxon_group_map_c[search_dict[k]]}' # 改成中文
            elif search_dict[k] in old_taxon_group_map_c.keys(): #這邊要讓新舊互通 因為舊的會需要再次查詢 舊的會是英文
                query_a += f'&taxonGroup={old_taxon_group_map_c[search_dict[k]]}' # 改成中文

    for l in l_list:
        query_a += f'&locality={l}'
    for r in r_list:
        query_a += f'&rightsHolder={r}'
    for d in d_list:
        query_a += f'&datasetName={d}'

    return query_a


def query_a_href(query, query_a, lang=None):
    if lang:
        translation.activate(lang)
    query += f'''<br><a class="search-again-a" target="_blank" href="{query_a}">{gettext('再次查詢')}<svg class="search-again-icon" xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25"><g id="loupe" transform="translate(0 -0.003)"><g id="Group_13" data-name="Group 13" transform="translate(0 0.003)"><path id="Path_54" data-name="Path 54" d="M24.695,23.225l-7.109-7.109a9.915,9.915,0,1,0-1.473,1.473L23.222,24.7a1.041,1.041,0,1,0,1.473-1.473ZM9.9,17.711A7.812,7.812,0,1,1,17.708,9.9,7.821,7.821,0,0,1,9.9,17.711Z" transform="translate(0 -0.003)" fill="#3f5146"></path></g></g></svg></a>'''
    return query


def return_selected_grid_text(req_dict,map_dict):

    string = ''
    if req_dict.get('current_grid_level') in ['grid_1','grid_10','grid_100','grid_5'] and req_dict.get('current_grid'):
        string = f'''{gettext(map_dict[req_dict["current_grid_level"]])} {req_dict.get('current_grid')}'''
    return string


# 已經預先存好的req_dict, getlist改為get
# generate_sensitive_csv (v), transfer_sensitive_response (v), submit_sensitive_request(v)

# 直接從form傳過來的req_dict, 使用getlist
# datasetName, rightsHolder, locality, polygon
# , generate_download_csv, generate_species_csv(v), get_map_grid(v), get_conditional_records(v)

def create_search_query(req_dict, from_request=False, get_raw_map=False):

    query_list = []

    # 有無影像
    if has_image := req_dict.get('has_image'):
        if has_image == 'y':
            query_list += ['associatedMedia:*']
        elif has_image == 'n':
            query_list += ['-associatedMedia:*']

    # 是否為原生種
    if is_native := req_dict.get('is_native'):
        if is_native == 'y':
            query_list += ['alien_type:native']
        elif is_native == 'n':
            query_list += ['alien_type:(naturalized OR invasive OR cultured)']


    # 是否為保育類
    if is_protected := req_dict.get('is_protected'):
        if is_protected == 'y':
            query_list += ['protected:*']
        elif is_protected == 'n':
            query_list += ['-protected:*']


    record_type = req_dict.get('record_type')
    if record_type == 'col': # occurrence include occurrence + collection
        query_list += ['recordType:col']

    if val := req_dict.get('taxonGroup'):
        # 這邊改用bioGroup 且是中文
        now_bio_group = None
        if val in taxon_group_map_e.keys():
            now_bio_group = val
        elif val in taxon_group_map_c.keys(): #這邊要讓新舊互通 因為舊的會需要再次查詢 舊的會是英文
            now_bio_group = taxon_group_map_c[val] # 改成中文
        elif val in old_taxon_group_map_c.keys(): #這邊要讓新舊互通 因為舊的會需要再次查詢 舊的會是英文
            now_bio_group = old_taxon_group_map_c[val] # 改成中文
        
        if now_bio_group == '維管束植物':
            now_bio_group = '(維管束植物 OR 蕨類植物)'

        query_list += [f'bioGroup:{now_bio_group}']


    for i in ['recordedBy', 'resourceContacts', 'preservation']:
        if val := req_dict.get(i):
            if val != 'undefined':
                val = val.strip()
                val = html.unescape(val)
                keyword_reg = ''
                for j in val:
                    keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
                keyword_reg = get_variants(keyword_reg)
                query_list += [f'{i}:/.*{keyword_reg}.*/']

    for i in ['taxonID', 'occurrenceID', 'catalogNumber', 'recordNumber']:
        if val := req_dict.get(i):
            query_list += [f'{i}:"{val}"']

    # 這邊會不會有模糊化的問題
    if req_dict.get('current_grid_level') in ['grid_1','grid_10','grid_100','grid_5'] and req_dict.get('current_grid'):
        query_list += [f'''{req_dict.get('current_grid_level')}:"{req_dict.get('current_grid')}"''']

    # higherTaxa
    # 找到該分類群的階層 & 名稱
    # 要包含自己的階層
    if val := req_dict.get('higherTaxa'):
        response = requests.get(f'{SOLR_PREFIX}taxa/select?q=id:{val}')
        if response.status_code == 200:
            resp = response.json()
            if data := resp['response']['docs']:
                data = data[0]
                higher_rank = data.get('taxonRank')
                higher_name = data.get('scientificName')
                query_list += [f'({higher_rank}:"{higher_name}" OR taxonID:"{val}")']

    if quantity := req_dict.get('organismQuantity'):
        query_list += [f'standardOrganismQuantity: {quantity}']

    if val := req_dict.get('typeStatus'):
        if val == '模式':
            query_list += [f'typeStatus:[* TO *]']
        elif val == '一般':
            query_list += [f'-typeStatus:*']
    
    if val := req_dict.get('basisOfRecord'):
        if val in basis_map.keys():
            query_list += [f'basisOfRecord:{val}']

    # 下拉選單單選
    for i in ['sensitiveCategory', 'taxonRank']: 
        if val := req_dict.get(i):
            if i == 'sensitiveCategory' and val == '無':
                query_list += [f'-(-{i}:{val} {i}:*)']
            elif i == 'taxonRank' and val == 'sub':
                query_list += [f'taxonRank:(subspecies OR nothosubspecies OR variety  OR subvariety  OR nothovariety OR form OR subform OR "special form" OR race OR stirp OR morph OR aberration)']
            else:
                query_list += [f'{i}:{val}']

    # 下拉選單多選
    d_list = []
    if from_request:
        if val := req_dict.getlist('datasetName'):
            for v in val:
                if d_id := get_tbia_dataset_id(v):
                        d_list.append(d_id)
    else:
        if val := req_dict.get('datasetName'):
            if isinstance(val, str):
                if val.startswith('['):
                    for d in eval(val):
                        if d_id := get_tbia_dataset_id(d):
                            d_list.append(d_id)
                else:
                    if d_id := get_tbia_dataset_id(val):
                        d_list.append(d_id)
            else:
                for d in list(val):
                    if d_id := get_tbia_dataset_id(d):
                        d_list.append(d_id)

    # 這邊要改成tbiaDatasetID才對
    if d_list:
        d_list_str = '" OR "'.join(d_list)
        query_list += [f'tbiaDatasetID:("{d_list_str}")']

    r_list = []

    if from_request:
        if val := req_dict.getlist('rightsHolder'):
            for v in val:
                r_list.append(v)
    else:
        if val := req_dict.get('rightsHolder'):
            if isinstance(val, str):
                if val.startswith('['):
                    r_list = eval(val)
                else:
                    r_list.append(val)
            else:
                r_list = list(val)
    
    
    if r_list:
        r_list_str = '" OR "'.join(r_list)
        query_list += [f'rightsHolder:("{r_list_str}")']

    l_list = []

    if from_request:
        if val := req_dict.getlist('locality'):
            l_list_str = '" OR "'.join(val)
            query_list += [f'locality:("{l_list_str}")']
    else:
        if val := req_dict.get('locality'):
            if isinstance(val, str):
                if val.startswith('['):
                    l_list = eval(val)
                else:
                    l_list.append(val)
            else:
                l_list = list(val)
        if l_list:
            l_list_str = '" OR "'.join(l_list)
            query_list += [f'locality:("{l_list_str}")']


    if req_dict.get('start_date') and req_dict.get('end_date'):
        try: 
            start_date = datetime.strptime(req_dict.get('start_date'), '%Y-%m-%d').isoformat() + 'Z'
            end_date = datetime.strptime(req_dict.get('end_date'), '%Y-%m-%d')
            end_date = end_date.isoformat() + 'Z'
            end_date = end_date.replace('00:00:00','23:59:59')
            query_list += [f'standardDate:[{start_date} TO {end_date}]']
        except:
            pass
    elif req_dict.get('start_date'):
        try: 
            start_date = datetime.strptime(req_dict.get('start_date'), '%Y-%m-%d').isoformat() + 'Z'
            query_list += [f'standardDate:[{start_date} TO *]']
        except:
            pass
    elif req_dict.get('end_date'):
        try: 
            end_date = datetime.strptime(req_dict.get('end_date'), '%Y-%m-%d')
            end_date = end_date.isoformat() + 'Z'
            end_date = end_date.replace('00:00:00','23:59:59')
            query_list += [f'standardDate:[* TO {end_date}]']
        except:
            pass


    #  要處理敏感資料

    if county := req_dict.get('county'):
        if get_raw_map:
            query_list += ['county: "%s" OR rawCounty: "%s"' % (county, county) ]
        else:
            query_list += ['county: "%s"' % county]

    if municipality := req_dict.get('municipality'):
        if get_raw_map:
            query_list += ['municipality: "%s" OR rawMunicipality: "%s"' % (municipality, municipality) ]
        else:
            query_list += ['municipality: "%s"' % municipality]


    # 地圖框選
    if req_dict.get('geo_type') == 'map':
        if from_request:
            if g_list := req_dict.getlist('polygon'): 
                try:
                    mp = MultiPolygon(map(wkt.loads, g_list))
                    if get_raw_map:
                        query_list += ['location_rpt: "Within(%s)" OR raw_location_rpt: "Within(%s)" ' % (mp, mp)]
                    else:
                        query_list += ['location_rpt: "Within(%s)"' % mp]
                    
                except:
                    pass
        else:
            if g_list := req_dict.get('polygon'):
                try:
                    mp = MultiPolygon(map(wkt.loads, [g_list]))
                    if get_raw_map:
                        query_list += ['location_rpt: "Within(%s)" OR raw_location_rpt: "Within(%s)" ' % (mp, mp)]
                    else:
                        query_list += ['location_rpt: "Within(%s)"' % mp]
                except:
                    pass

    # 上傳polygon
    if req_dict.get('geo_type') == 'polygon':

        if g_id := req_dict.get('geojson_id'):
            try:
                with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                    geojson = json.loads(j.read())
                    geo_df = gpd.GeoDataFrame.from_features(geojson)
                    g_list = []
                    for i in geo_df.to_wkt()['geometry']:
                        g_list += ['"Within(%s)"' % i]
                    if get_raw_map:
                        query_list += [ f"location_rpt: ({' OR '.join(g_list)}) OR raw_location_rpt: ({' OR '.join(g_list)})" ]
                    else:
                        query_list += [ f"location_rpt: ({' OR '.join(g_list)})" ]
            except:
                pass

    # 圓中心框選
    if req_dict.get('geo_type') == 'circle':
        if circle_radius := req_dict.get('circle_radius'):
            query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (req_dict.get('center_lat').strip(), req_dict.get('center_lon').strip(), int(circle_radius))]

    # 學名相關
    if val := req_dict.get('name'):
        val = val.strip()
        # 去除重複空格
        val = re.sub(' +', ' ', val)
        # 去除頭尾空格
        val = val.strip()
        keyword_reg = ''
        val = html.unescape(val)
        for j in val:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
        keyword_reg = get_variants(keyword_reg)
        col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in name_search_col ]
        query_str = ' OR '.join( col_list )
        query_list += [ '(' + query_str + ')' ]


    # group (後台儀表板的query)
    if group := req_dict.get('group'):
        if group != 'total':
            query_list += ['group:{}'.format(group)]

    # rights_holder (後台儀表板的query)
    if rights_holder := req_dict.get('rights_holder'):
        if rights_holder != 'total':
            query_list += ['rightsHolder:{}'.format(rights_holder)]

    return query_list



# 全站搜尋 物種出現紀錄 / 自然史典藏
def get_search_full_cards(keyword, card_class, is_sub, offset, key, lang=None, is_first_time=False):
    if lang:
        translation.activate(lang)

    keyword = keyword.strip()

    # # 去除重複空格
    # keyword = re.sub(' +', ' ', keyword)
    # 去除頭尾空格
    # keyword = keyword.strip()
    # 去除特殊字元
    # keyword = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', keyword)

    if re.match(r'^([\s\d]+)$', keyword):
        # 純數字
        enable_query_date = False
    elif re.match(r'^[0-9-]*$', keyword):
        # 數字和-的組合 一定要符合日期格式才行
        try:
            datetime.strptime(keyword, '%Y-%m-%d')
            enable_query_date = True
        except:
            enable_query_date = False
    else:
        enable_query_date = True

    query_list = []

    query = {
        "query": '*:*',
        "limit": 0,
        "facet": {},
        "sort":  "scientificName asc"
    }

    keyword_reg = ''
    q = ''
    keyword = html.unescape(keyword)
    for j in keyword:
        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
    keyword_reg = get_variants(keyword_reg)

    # 查詢學名相關欄位時 去除重複空格
    keyword_name = re.sub(' +', ' ', keyword)
    keyword_name_reg = ''
    for j in keyword_name:
        keyword_name_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
    keyword_name_reg = get_variants(keyword_name_reg)

    if card_class.startswith('.col'):
        map_dict = map_collection
        record_type = 'col'
        title_prefix = f'{gettext("自然史典藏")} > '
        query_list.append('recordType:col')
    else: # taxon 跟 occ 都算在這裡
        map_dict = map_occurrence
        query.pop('filter', None)
        record_type = 'occ'
        title_prefix = f'{gettext("物種出現紀錄")} > '

    facet_list = create_facet_list(record_type=record_type)

    if not enable_query_date:
        if 'eventDate' in facet_list['facet'].keys():
            facet_list['facet'].pop('eventDate')

    # 是否為特定facet卡片底下的
    if is_sub == 'true':
        facet_list = {'facet': {k: v for k, v in facet_list['facet'].items() if k == key} }

    q = ''

    for i in facet_list['facet']:
        if i in taxon_keyword_list:
            q += f'{i}:/.*{keyword_name_reg}.*/ OR ' 
            if card_class.startswith('.col'):
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_name_reg}.*/', 'filter': ['recordType:col']}})
            else:
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_name_reg}.*/'}})
        else:
            q += f'{i}:/.*{keyword_reg}.*/ OR ' 
            if card_class.startswith('.col'):
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/', 'filter': ['recordType:col']}})
            else:
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})

    if is_first_time:
        # 背景處理stat
        query_string = 'keyword=' + keyword
        task = threading.Thread(target=backgroud_search_stat, args=(q[:-4],'full',query_string))
        task.start()
    
    query.update(facet_list)
    query_list.append(q[:-4])
    query['filter'] = query_list

    # s = time.time()

    response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
    facets = response.json()['facets']
    total_count = response.json()['response']['numFound']
    facets.pop('count', None)

    # print('get_resp', time.time()-s)

    menu_rows = [] # 側邊欄
    result = [] # 卡片
    has_more = False

    # 2023/11/20前 如果是對到高階層的話，存parentTaxonID，會有taxonID是空值，但其實有對到高階層的情況，產生bug
    # 目前全部改存taxonID

    for i in facets:
        x = facets[i]
        if x['allBuckets']['count']:
            menu_rows.append({
                'title': map_dict[i],
                'total_count': x['allBuckets']['count'],
                'key': i
            })
        for k in x['buckets']:
            bucket = k['taxonID']['buckets']
            if bucket:
                if i == 'eventDate':
                    if f_date := convert_date(k['val']):
                        f_date = f_date.strftime('%Y-%m-%d %H:%M:%S')
                        for item in bucket:
                            if dict(item, **{'matched_value':f_date, 'matched_col': i}) not in result:
                                result.append(dict(item, **{'matched_value': f_date, 'matched_col': i}))
                else:
                    for item in bucket:
                        if dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in result:
                            result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i}))
            elif not bucket and k['count']:
                if {'val': '', 'count': k['count'],'matched_value':k['val'], 'matched_col': i} not in result:
                    result.append({'val': '', 'count': k['count'],'matched_value':k['val'], 'matched_col': i})

    # 卡片
    result_df = pd.DataFrame(result)
    res_c = 0
    result_dict_all = []

    if len(result_df):
        for t in result_df.val.unique():
            # 若是taxon-related的算在同一張
            rows = []
            if len(result_df[(result_df.val==t) & (result_df.matched_col.isin(taxon_facets))]):
                if res_c in range(offset,offset+9):
                    rows = result_df[(result_df.val==t) & (result_df.matched_col.isin(taxon_facets))]
                    matched = []
                    for ii in rows.index:
                        match_val = result_df.loc[ii].matched_value
                        # 改成後面一起處理
                        matched.append({'key': result_df.loc[ii].matched_col, 
                                        'matched_col': map_dict[result_df.loc[ii].matched_col], 
                                        'matched_value_ori': match_val,
                                        'matched_value': highlight(match_val,keyword,'1'),
                                        })
                    result_dict_all.append({
                        'val': t,
                        'count': result_df[(result_df.val==t) & (result_df.matched_col.isin(taxon_facets))]['count'].values[0],
                        'matched': matched,
                        'match_type': 'taxon-related'
                    })
                res_c += 1
            # 如果沒有任何taxon-related的對到，則顯示來源資料庫使用的名稱
            else: # 內容不一樣 要拆成不同卡片
                rows = result_df[(result_df.val==t) & (result_df.matched_col.isin(['sourceScientificName','sourceVernacularName','originalScientificName']))]
                for ii in rows.index:
                    if res_c in range(offset,offset+9):
                        matched = [{'key': result_df.loc[ii].matched_col, 
                                    'matched_col': map_dict[result_df.loc[ii].matched_col], 
                                    'matched_value_ori': result_df.loc[ii].matched_value,
                                    'matched_value': highlight(result_df.loc[ii].matched_value,keyword,'1'),
                                    }]
                        result_dict_all.append({
                            'val': t,
                            'count': result_df.loc[ii]['count'],
                            'matched': matched,
                            'match_type': 'non-taxon-related'
                        })
                    res_c += 1
            for ii in result_df[(result_df.val==t) & ~(result_df.matched_col.isin(taxon_facets+['sourceScientificName','sourceVernacularName','originalScientificName']))].index:
                if res_c in range(offset,offset+9):
                    matched= [{'key': result_df.loc[ii].matched_col,
                                'matched_col': map_dict[result_df.loc[ii].matched_col], 
                                'matched_value_ori': result_df.loc[ii].matched_value,
                                'matched_value': highlight(result_df.loc[ii].matched_value,keyword),
                                }]
                    result_dict_all.append({
                        'val': result_df.loc[ii].val,
                        'count': result_df.loc[ii]['count'],
                        'matched': matched,
                        'match_type': 'non-taxon-related'
                    })
                res_c += 1
            if offset >= 27:
                if res_c > offset+3:
                    has_more = True
                    break
            else:
                if res_c > offset+9:
                    has_more = True
                    break

        if offset >= 27:
            result_df = pd.DataFrame(result_dict_all[:3])
        else:
            result_df = pd.DataFrame(result_dict_all[:9])

        # s = time.time()
        result_df = result_df.replace({None:'', np.nan: ''}) 
        taicol = pd.DataFrame()
        if len(result_df):
            taxon_ids = [f"id:{d}" for d in result_df[result_df.val!=''].val.unique()]
            response = requests.get(f'{SOLR_PREFIX}taxa/select?q={" OR ".join(taxon_ids)}&fl=common_name_c,formatted_name,id,scientificName,taxonRank,formatted_misapplied,formatted_synonyms')
            # response = requests.get(f'{SOLR_PREFIX}taxa/select?q={" OR ".join(taxon_ids)}')
            if response.status_code == 200:
                resp = response.json()
                if data := resp['response']['docs']:
                    taicol = pd.DataFrame(data)
                    used_cols = ['common_name_c','formatted_name','id','scientificName','taxonRank', 'formatted_misapplied', 'formatted_synonyms']
                    for u in used_cols:
                        if u not in taicol.keys():
                            taicol[u] = ''
                    taicol = taicol[used_cols]
                    taicol = taicol.rename(columns={'scientificName': 'name', 'id': 'taxonID'})
                    # print(taicol.keys())
            # print(taicol)
            if len(taicol):
                result_df = pd.merge(result_df,taicol,left_on='val',right_on='taxonID', how='left')
                result_df = result_df.replace({np.nan:'', None:''})
                result_df['taxonRank'] = result_df['taxonRank'].apply(lambda x: map_dict[x] if x else x)
                # 如果match_col是synonyms & misapplied 要修改
            else:
                result_df['common_name_c'] = ''
                result_df['formatted_name'] = ''
                result_df['taxonID'] = ''
                result_df['name'] = ''
                result_df['taxonRank'] = ''
            result_df['val'] = result_df['formatted_name']
            if (is_sub != 'true') or (is_sub == 'true' and key == 'scientificName'):
                result_df['val'] = result_df['val'].apply(lambda x: highlight(x, keyword,'1'))
            if (is_sub != 'true') or (is_sub == 'true' and key == 'common_name_c'):
                result_df['common_name_c'] = result_df['common_name_c'].apply(lambda x: highlight(x, keyword,'1'))
            result_df = result_df.replace({np.nan:'', None:''})
            result_df = result_df.drop(columns=['formatted_name'],errors='ignore')
        # print('get_taxon', time.time()-s)

    # get_focus_card 使用
    if key:
        title = f"{title_prefix}{gettext(map_dict[key])}"
        item_class = f"item_{record_type}_{key}"
        card_class = f"{record_type}-{key}-card"
    else:
        title = None
        item_class = None
        card_class = None

    data = []

    for rr in result_df.to_dict('records'):
        matches = rr.get('matched')
        new_matches = []
        for mm in matches:
            tmp_m = mm
            if mm.get('key') in ['synonyms', 'misapplied']:
                if f"formatted_{mm.get('key')}" in taicol.keys():
                    new_value = taicol[taicol.taxonID==rr.get('taxonID')][f"formatted_{mm.get('key')}"].values[0]
                    if new_value:
                        new_value = (', ').join(new_value.split(','))
                        new_value = highlight(new_value, keyword, 1)
                    tmp_m.update({'matched_value': new_value})
            new_matches.append(tmp_m)
        rr.update({'matched': new_matches})
        data += [rr]

    response = {
        'total_count': total_count, # 總數
        'menu_rows': menu_rows, # 側邊欄
        'data': data, # 卡片
        'has_more': has_more,
        'reach_end': True if offset >= 27 else False,
        # get_focus_card 使用
        'item_class': item_class,
        'card_class': card_class,
        'title': title,
    }

    return response



# 全站搜尋 物種
def get_search_full_cards_taxon(keyword, card_class, is_sub, offset, lang=None):
    if lang:
        translation.activate(lang)

    taxon_result_dict = []
    offset = int(offset) if offset else offset
    if card_class and card_class != '.taxon-card':
        key = card_class.split('-')[1]
    else:
        key = None

    taxon_facet_list = create_taxon_facet_list()

    keyword_reg = ''
    keyword = html.unescape(keyword)
    for j in keyword:
        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
    keyword_reg = get_variants(keyword_reg)

    # 查詢學名相關欄位時 去除重複空格
    keyword_name = re.sub(' +', ' ', keyword)
    keyword_name_reg = ''
    for j in keyword_name:
        keyword_name_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
    keyword_name_reg = get_variants(keyword_name_reg)
    
    if is_sub == 'true':
        taxon_facet_list = {'facet': {k: v for k, v in taxon_facet_list['facet'].items() if k == key} }

    taxon_q = ''

    for i in taxon_facet_list['facet']:
        facet_taxon_query = f'({i}:/.*{keyword_name_reg}.*/) OR ({i}:/{keyword_name_reg}/{"^3 AND (is_in_taiwan:1^1 or is_in_taiwan:*)" if i in ["scientificName", "common_name_c", "alternative_name_c"] else ""}) '
        taxon_q += f'({i}:/.*{keyword_name_reg}.*/) OR ' 
        taxon_q += f'({i}:/{keyword_name_reg}/{"^3 AND (is_in_taiwan:1^1 or is_in_taiwan:*)" if i in ["scientificName", "common_name_c", "alternative_name_c"] else ""} ) OR ' 
        taxon_facet_list['facet'][i].update({'domain': { 'query': facet_taxon_query}})

    taxon_q = taxon_q[:-4]

    query = {}
    query['query'] = taxon_q
    query['limit'] = 4 if offset < 28 else 2
    query['offset'] = offset
    query['facet'] = taxon_facet_list['facet']
    # query['fields'] = 'common_name_c,formatted_name,id,scientificName,taxonRank,formatted_misapplied,formatted_synonyms'

    response = requests.post(f'{SOLR_PREFIX}taxa/select', data=json.dumps(query), headers={'content-type': "application/json" })
    facets = response.json()['facets']
    facets.pop('count', None)
    data = response.json()['response']

    total_count = data['numFound']
    if total_count:
        taicol = pd.DataFrame(data['docs'])
        taicol_cols = [c for c in ['common_name_c', 'alternative_name_c', 'synonyms', 'formatted_name', 'id', 'taxon_name_id','taxonRank', 'formatted_misapplied', 'formatted_synonyms'] if c in taicol.keys()]
        taicol = taicol[taicol_cols]
        taicol = taicol.rename(columns={'scientificName': 'name', 'id': 'taxonID'})
    taxon_ids = [f"taxonID:{d['id']}" for d in data['docs']]

    # 側邊欄
    menu_rows = []
    for i in facets:
        x = facets[i]
        if x['allBuckets']['count']:
            menu_rows.append({
                'title': map_collection[i],
                'total_count': x['allBuckets']['count'],
                'key': i
            })

    taxon_result = []
    regexp = re.compile(keyword_name_reg)
    for d in data['docs']:
        # if is_sub == 'false':
        for k in taxon_facet_list['facet'].keys():
            if d.get(k):
                if regexp.search(d.get(k)):
                    taxon_result.append({
                        'val': d.get('id'),
                        'matched_value': d.get(k),
                        'matched_col': k,
                    })

    # 物種整理
    taxon_result_df = pd.DataFrame(taxon_result)
    taxon_result_dict_all = []

    if len(taxon_result_df):
        for tt in taxon_result_df.val.unique(): ## tt = taxonID
            rows = []
            if len(taxon_result_df[(taxon_result_df.val==tt)]):
                # tt_c += 1
                rows = taxon_result_df[(taxon_result_df.val==tt)]
                matched = []
                for ii in rows.index:
                    match_val = taxon_result_df.loc[ii].matched_value
                    match_col = taxon_result_df.loc[ii].matched_col
                    if match_col in ['synonyms','misapplied']:
                        if f'formatted_{match_col}' in taicol.keys():
                            if len(taicol[taicol.taxonID==tt]):
                                match_val = taicol.loc[taicol.taxonID==tt][f'formatted_{match_col}'].values[0]
                        if match_val:
                            match_val = (', ').join(match_val.split(','))
                    matched.append({'key': match_col, 'matched_col': map_collection[match_col], 'matched_value': match_val})
                taxon_result_dict_all.append({
                    'val': tt,
                    'matched': matched,
                    # 'match_type': 'taxon-related'
                })

    taxon_result_df = pd.DataFrame(taxon_result_dict_all[:4])

    if len(taxon_result_df):
        taxon_result_df = pd.merge(taxon_result_df,taicol,left_on='val',right_on='taxonID', how='left')
        taxon_result_df = taxon_result_df.replace({np.nan:'', None:''})
        taxon_result_df['taxonRank'] = taxon_result_df['taxonRank'].apply(lambda x: map_occurrence[x] if x else x)
        taxon_result_df = taxon_result_df.replace({np.nan:'', None:''})
        if 'synonyms' in taxon_result_df.keys():
            if 'formatted_synonyms' in taxon_result_df.keys():
                taxon_result_df['synonyms'] = taxon_result_df['formatted_synonyms']
            taxon_result_df['synonyms'] = taxon_result_df['synonyms'].apply(lambda x: ', '.join(x.split(',')))
        taxon_result_df['col_count'] = 0 
        taxon_result_df['occ_count'] = 0 
        # 取得出現紀錄及自然史典藏筆數
        response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.pivot=taxonID,recordType&facet=true&q.op=OR&q={" OR ".join(taxon_ids)}&rows=0')
        data = response.json()['facet_counts']['facet_pivot']['taxonID,recordType']
        # print(response.json())

        for d in data:
            taxon_result_df.loc[taxon_result_df.taxonID==d['value'],'occ_count'] = d['count']
            col_count = 0
            for dp in d['pivot']:
                if dp.get('value') == 'col':
                    col_count = dp.get('count')
            taxon_result_df.loc[taxon_result_df.taxonID==d['value'],'col_count'] = col_count
        
        # 處理hightlight
        # taxon_result_df['matched_value'] = taxon_result_df['matched_value'].apply(lambda x: highlight(x,keyword,'1'))
        # TODO 這邊應該可以簡化
        if 'common_name_c' in taxon_result_df.keys():
            if (is_sub == 'false') or (is_sub != 'false' and key == 'common_name_c') :
                taxon_result_df['common_name_c'] = taxon_result_df['common_name_c'].apply(lambda x: highlight(x,keyword,'1'))
        if 'alternative_name_c' in taxon_result_df.keys():
            if (is_sub == 'false') or (is_sub != 'false' and key == 'alternative_name_c') :
                taxon_result_df['alternative_name_c'] = taxon_result_df['alternative_name_c'].apply(lambda x: highlight(x,keyword,'1'))
        if 'synonyms' in taxon_result_df.keys():
            if (is_sub == 'false') or (is_sub != 'false' and key == 'synonyms') :
                taxon_result_df['synonyms'] = taxon_result_df['synonyms'].apply(lambda x: highlight(x,keyword,'1'))
            taxon_result_df['synonyms'] = taxon_result_df['synonyms'].apply(lambda x: ', '.join(x.split(',')))
        if (is_sub == 'false') or (is_sub != 'false' and key == 'scientificName') :
            taxon_result_df['formatted_name'] = taxon_result_df['formatted_name'].apply(lambda x: highlight(x,keyword,'1'))
        for required_cols in ['common_name_c', 'alternative_name_c', 'synonyms']:
            if required_cols not in taxon_result_df.keys():
                taxon_result_df[required_cols] = ''
        taxon_result_df = taxon_result_df.replace({np.nan:'', None:''})
    # 照片
    taxon_result_dict = []
    for tr in taxon_result_df.to_dict('records'):
        tr['images'] = []
        results = get_species_images(tr['taxonID'])
        if results:
            tr['taieol_id'] = results[0]
            tr['images'] = results[1]

        tmp = []
        for ii in tr['matched']:
            match_val = ii['matched_value']
            if ii['matched_col'] == '誤用名':
                match_val = (', ').join(match_val.split(','))
            match_val = highlight(match_val,keyword,'1')
            tmp.append({'matched_col': ii['matched_col'], 'matched_value': match_val})
        tr['matched'] = tmp
        taxon_result_dict.append(tr)

    # get_focus_card_taxon 使用
    map_dict = map_occurrence # occ或col沒有差別

    if key:
        title = f"{gettext('物種')} > {gettext(map_dict[key])}"
        item_class = f"item_taxon_{key}"
        card_class = f"taxon-{key}-card"
    else:
        title = None
        item_class = None
        card_class = None

    response = {
        'title': title,
        'item_class': item_class,
        'card_class': card_class,
        'total_count': total_count, # 總數
        'menu_rows': menu_rows, # 側邊欄
        'data': taxon_result_dict,
        'has_more': True if total_count > offset + 4  else False,
        'reach_end': True if offset >= 28 else False
    }

    return response


def if_raw_map(user_id):
    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True,partner__is_collaboration=False)|Q(is_partner_admin=True,partner__is_collaboration=False)|Q(is_system_admin=True)).exists():
        return True
    else:
        return False


def get_map_geojson(data_c, grid):

    map_geojson = {}
    map_geojson[f'grid_{grid}'] = {"type":"FeatureCollection","features":[]}
    # data_c = resp['facets'][facet_grid]['buckets']
    # s = time.time()
    for cc in data_c:
        if len(cc['val'].split('_')) > 1:
            current_grid_x = int(cc['val'].split('_')[0])
            current_grid_y = int(cc['val'].split('_')[1])
            current_count = cc['count']
            if current_grid_x > 0 and current_grid_y > 0:
                borders = convert_grid_to_square(current_grid_x, current_grid_y, grid/100)
                tmp = [{
                    "type": "Feature",
                    "geometry":{"type":"Polygon","coordinates":[borders]},
                    "properties": {
                        "counts": current_count,
                        "current_grid_level": f'grid_{grid}',
                        "current_grid": cc['val'],
                    }
                }]
                map_geojson[f'grid_{grid}']['features'] += tmp
    # print(time.time()-s)
    return map_geojson

def get_map_response(map_query, grid_list, get_raw_map):

    map_geojson = {}

    facet_str = ''
    for g in grid_list:
        map_geojson[f'grid_{g}'] = {"type":"FeatureCollection","features":[]}
        if get_raw_map:
            facet_str += f'&facet.field=grid_{g}'
        else:
            facet_str += f'&facet.field=grid_{g}_blurred'
            
    map_response = requests.post(f'{SOLR_PREFIX}tbia_records/select?facet=true&rows=0&facet.mincount=1&facet.limit=-1{facet_str}', data=json.dumps(map_query), headers={'content-type': "application/json" }) 


    data_c = {}
    for grid in grid_list:
        if get_raw_map:
            facet_grid = f'grid_{grid}'
        else:
            facet_grid = f'grid_{grid}_blurred'
        data_c = map_response.json()['facet_counts']['facet_fields'][facet_grid]
        for i in range(0, len(data_c), 2):
            if len(data_c[i].split('_')) > 1:
                current_grid_x = int(data_c[i].split('_')[0])
                current_grid_y = int(data_c[i].split('_')[1])
                current_count = data_c[i+1]
                if current_grid_x > 0 and current_grid_y > 0:
                    borders = convert_grid_to_square(current_grid_x, current_grid_y, grid/100)
                    tmp = [{
                        "type": "Feature",
                        "geometry":{"type":"Polygon","coordinates":[borders]},
                        "properties": {
                            "counts": current_count
                        }
                    }]
                    map_geojson[f'grid_{grid}']['features'] += tmp

    return map_geojson


# occurrence & collection detail頁面整理
def create_data_detail(id, user_id, record_type):

    path_str = ''
    logo = ''

    query = {
        'query': "*:*",
        'limit': 1,
        'filter': f"id:{id}",
        }
    response = requests.post(f'{SOLR_PREFIX}tbia_records/select?', data=json.dumps(query), headers={'content-type': "application/json" })
    row = pd.DataFrame(response.json()['response']['docs'])
    row = row.replace({np.nan: '', 'nan': ''})
    row = row.to_dict('records')
    row = row[0]

    if record_type == 'col':
        link_prefix = 'collection'
    else:
        link_prefix = 'occurrence'

    if (record_type == 'col' and row.get('recordType') == ['col']) or record_type == 'occ':
        if row.get('taxonRank', ''):
            row.update({'taxonRank': map_occurrence[row['taxonRank']]})

        am = []
        if ams := row.get('associatedMedia'):
            if ';' in ams:
                img_sep = ';'
            else:
                img_sep = '|'
            ams = ams.split(img_sep)
            if row.get('mediaLicense'):
                mls = row.get('mediaLicense').split(';')
                if len(mls) == 1:
                    for a in ams:
                        am.append({'img': a, 'license': row.get('mediaLicense')})
                else:
                    img_len = len(ams)
                    for i in range(img_len):
                        am.append({'img': ams[i], 'license': mls[i]})
            else:
                for a in ams:
                    am.append({'img': a, 'license': ''})
        row.update({'associatedMedia': am})

        if str(row.get('dataGeneralizations')) in ['True', True, "true"]:
            row.update({'dataGeneralizations': '是'})
        elif str(row.get('dataGeneralizations')) in ['False', False, "false"]:
            row.update({'dataGeneralizations': '否'})
        else:
            pass

        # date
        if date := row.get('standardDate'):
            # date = date[0].replace('T', ' ').replace('Z','')
            date = date[0].split('T')[0]
        else:
            date = None
        row.update({'date': date})

        # 經緯度
        if row.get('raw_location_rpt') and User.objects.filter(id=user_id).filter(Q(is_partner_account=True,partner__is_collaboration=False)|Q(is_partner_admin=True,partner__is_collaboration=False)|Q(is_system_admin=True)).exists():
            lat = None
            if lat := row.get('standardRawLatitude'):
                if -90 <= lat[0] and lat[0] <= 90:        
                    lat = lat[0]
                else:
                    lat = None
            row.update({'lat': lat})
            lon = None
            if lon := row.get('standardRawLongitude'):
                if -180 <= lon[0] and lon[0] <= 180:             
                    lon = lon[0]
                else:
                    lon = None
            row.update({'lon': lon})

            if row.get('rawCounty'):
                row.update({'county': row.get('rawCounty')})

            if row.get('rawMunicipality'):
                row.update({'municipality': row.get('rawMunicipality')})

        else:
            lat = None
            if lat := row.get('standardLatitude'):
                if -90 <= lat[0] and lat[0] <= 90:        
                    lat = lat[0]
                else:
                    lat = None
            row.update({'lat': lat})

            lon = None
            if lon := row.get('standardLongitude'):
                if -180 <= lon[0] and lon[0] <= 180:             
                    lon = lon[0]
                else:
                    lon = None
            row.update({'lon': lon})

        # 數量
        if quantity := row.get('standardOrganismQuantity'):
            # quantity = int(quantity[0])
            quantity = str(quantity[0])
            if quantity.endswith('.0'):
                quantity = quantity[:-2]
        else:
            quantity = None
        row.update({'quantity': quantity})

        # taxon
        path = []
        path_taxon_id = None
        if row.get('taxonID'):
            path_taxon_id = row.get('taxonID')
        # elif row.get('parentTaxonID'):
        #     path_taxon_id = row.get('parentTaxonID')
        if path_taxon_id:
            response = requests.get(f'{SOLR_PREFIX}taxa/select?q=id:{path_taxon_id}')
            data = response.json()
            t_rank = data['response']['docs'][0]
            for r in rank_list:
                if t_rank.get(r):
                    if t_rank.get(f"formatted_{r}"):
                        current_str = t_rank.get(f"formatted_{r}")
                    else:
                        current_str = t_rank.get(r)
                    if t_rank.get(f"{r}_c"):
                        current_str += ' ' + t_rank.get(f"{r}_c")

                    t_taxonID = t_rank.get(f"{r}_taxonID")

                    current_str = f'{r.capitalize()} <a target="_blank" href="/search/{link_prefix}?higherTaxa={t_taxonID}&from=search">{current_str}</a>'
                    path.append(current_str)

        path_str = ' > '.join(path)

        # logo
        if group := row.get('group'):
            if group == 'gbif':
                logo = 'GBIF-2015.png'
            elif logo := Partner.objects.filter(group=group).values('logo'):
                logo = logo[0]['logo']
                logo = 'partner/' + logo

        # references
        if not row.get('references'):
            if Partner.objects.filter(group=group).values('info').exists():
                row['references'] = Partner.objects.get(group=group).info[0]['link']

        modified = row.get('modified')[0].split('.')[0].replace('T',' ').replace('Z',' ')
        row.update({'modified': modified})
    else:
        row = [] # 如果不是自然史典藏，在自然史典藏頁面不顯示
    return row, path_str, logo


# 進階搜尋 / 全站搜尋 表格整理
def create_data_table(docs, user_id, obv_str):
    rows = []

    for i in docs.index:
        docs = docs.replace({np.nan:None})
        row = docs.iloc[i]
        if row.get('scientificName') and row.get('formatted_name'):
            docs.loc[i, 'scientificName'] = docs.loc[i, 'formatted_name']

        # 這邊如果太長的時候不顯示全部

        syns, misapplied = '', ''

        if row.get('formatted_synonyms'):
            syns = row.get('formatted_synonyms')
        elif row.get('synonyms'):
            syns = row.get('synonyms')
        
        if syns:
            syns = syns.split(',')
            if len(syns) > 1:
                syns = syns[:2]
                syns = ', '.join(syns) + '...'
            else:
                syns = ', '.join(syns)
            docs.loc[i, 'synonyms'] = syns

        if row.get('formatted_misapplied'):
            misapplied = row.get('formatted_misapplied')
        elif row.get('misapplied'):
            misapplied = row.get('misapplied')
        
        if misapplied:
            misapplied = misapplied.split(',')
            if len(misapplied) > 1:
                misapplied = misapplied[:2]
                misapplied = ', '.join(misapplied) + '...'
            else:
                misapplied = ', '.join(misapplied)
            docs.loc[i, 'misapplied'] = misapplied

        # date
        if date := row.get('standardDate'):
            date = date[0].split('T')[0]
            docs.loc[i , 'eventDate'] = date
        else:
            if row.get('eventDate'):
                date_str = gettext(f'原始{obv_str}日期')
                docs.loc[i , 'eventDate'] = f'---<br><small class="color-silver">[{date_str}]' + row.get('eventDate') + '</small>'

        # 經緯度
        # 如果是正式會員直接給原始
        if row.get('raw_location_rpt') and User.objects.filter(id=user_id).filter(Q(is_partner_account=True,partner__is_collaboration=False)|Q(is_partner_admin=True,partner__is_collaboration=False)|Q(is_system_admin=True)).exists():
            if lat := row.get('standardRawLatitude'):
                docs.loc[i , 'verbatimLatitude'] = lat[0]
            else:
                if row.get('verbatimRawLatitude'):
                    docs.loc[i , 'verbatimLatitude'] = f'---<br><small class="color-silver">[{gettext("原始紀錄緯度")}]' + row.get('verbatimRawLatitude') + '</small>'

            if lon := row.get('standardRawLongitude'):
                docs.loc[i , 'verbatimLongitude'] = lon[0]
            else:
                if row.get('verbatimRawLongitude'):
                    docs.loc[i , 'verbatimLongitude'] = f'---<br><small class="color-silver">[{gettext("原始紀錄經度")}]' + row.get('verbatimRawLongitude') + '</small>'

            if row.get('rawCounty'):
                docs.loc[i , 'county'] = row.get('rawCounty')

            if row.get('rawMunicipality'):
                docs.loc[i , 'municipality'] = row.get('rawMunicipality')
                
        else:
            if lat := row.get('standardLatitude'):
                docs.loc[i , 'verbatimLatitude'] = lat[0]
            else:
                if row.get('verbatimLatitude'):
                    docs.loc[i , 'verbatimLatitude'] = f'---<br><small class="color-silver">[{gettext("原始紀錄緯度")}]' + row.get('verbatimLatitude') + '</small>'

            if lon := row.get('standardLongitude'):
                docs.loc[i , 'verbatimLongitude'] = lon[0]
            else:
                if row.get('verbatimLongitude'):
                    docs.loc[i , 'verbatimLongitude'] = f'---<br><small class="color-silver">[{gettext("原始紀錄經度")}]' + row.get('verbatimLongitude') + '</small>'
        # 數量
        if quantity := row.get('standardOrganismQuantity'):
            quantity = str(quantity[0])
            if quantity.endswith('.0'):
                quantity = quantity[:-2]
            docs.loc[i , 'organismQuantity'] = quantity
        else:
            if row.get('organismQuantity'):
                docs.loc[i , 'organismQuantity'] = f'---<br><small class="color-silver">[{gettext("原始紀錄數量")}]' + row.get('organismQuantity') + '</small>'
        
        # 分類階層
        if row.get('taxonRank', ''):
            now_rank = row.get('taxonRank')
            docs.loc[i , 'taxonRank'] = map_collection[now_rank]

        # 座標是否有模糊化
        if str(row.get('dataGeneralizations')) in ['True', True, "true"]:
            docs.loc[i , 'dataGeneralizations'] = '是'
        elif str(row.get('dataGeneralizations')) in ['False', False, "false"]:
            docs.loc[i , 'dataGeneralizations'] = '否'
        else:
            pass

        # 紀錄類型
        if row.get('basisOfRecord',''):
            if row.get('basisOfRecord') in basis_map.keys():
                docs.loc[i , 'basisOfRecord'] = basis_map[row.get('basisOfRecord')]

        if media_list := row.get('associatedMedia'):

            if ';' in media_list:
                img_sep = ';'
            else:
                img_sep = '|'

            media_list = media_list.split(img_sep)

            if len(media_list):
                # 取第一張
                docs.loc[i, 'associatedMedia'] = '<img class="icon-size-50" alt="{}" title="{}" src="{}">'.format(gettext('圖片無法正常顯示'),gettext('圖片無法正常顯示'),media_list[0])


    docs = docs.replace({np.nan: ''})
    docs = docs.replace({'nan': ''})

    rows = docs.to_dict('records')

    return rows



def get_resource_cate(extension):
    if extension.lower() in ['docx','csv','json','xlsx', 'xls']:
        cate = 'doc'
    elif extension.lower() in ['ppt','doc','pdf','xml', 'link']:
        cate = extension.lower()
    else:
        cate = 'other'
    return cate


def check_map_bound(map_bound):

    map_str = map_bound.split(' TO ')
    map_min_lat =  float(map_str[0].split(',')[0])
    map_min_lon = float(map_str[0].split(',')[1])
    map_max_lat =  float(map_str[1].split(',')[0])
    map_max_lon =  float(map_str[1].split(',')[1])
    if map_min_lon < -180 :
        map_min_lon = -180
    if map_min_lat < -90:
        map_min_lat = -90
    if map_max_lon > 180:
        map_max_lon = 180
    if map_max_lat > 90:
        map_max_lat = 90

    new_map_bound = f'[{map_min_lat},{map_min_lon} TO {map_max_lat},{map_max_lon}]'
    return new_map_bound


def create_search_stat(query_list):

    stat_query = { "query": "*:*",
            "offset": 0,
            "limit": 0,
            "filter": query_list,
            "facet": {
                "stat_rightsHolder": {
                    'type': 'terms',
                    'field': 'rightsHolder',
                    'mincount': 1,
                    'limit': -1,
                    'allBuckets': False,
                    'numBuckets': False
                }
            }
        }
    
    if not query_list:
        stat_query.pop('filter', None)

    response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(stat_query), headers={'content-type': "application/json" })
    facets = response.json()['facets']

    total_count = response.json()['response']['numFound']

    stat_rightsHolder = []

    if total_count:
        stat_rightsHolder = facets['stat_rightsHolder']['buckets']

    stat_rightsHolder.append({'val': 'total', 'count': total_count})

    return stat_rightsHolder


def backgroud_search_stat(query_list,record_type,query_string):

    stat_rightsHolder = create_search_stat(query_list=query_list)
    SearchStat.objects.create(query=query_string,search_location=record_type,stat=stat_rightsHolder,created=timezone.now())


def create_sensitive_partner_stat(query_list):

    query = { "query": "raw_location_rpt:*",
                "offset": 0,
                "limit": 0,
                "filter": query_list,
                "facet": {
                    "stat_rightsHolder": {
                        'type': 'terms',
                        'field': 'rightsHolder',
                        'mincount': 1,
                        'limit': -1,
                        'allBuckets': False,
                        'numBuckets': False
                    }
                }
            }

    if not query_list:
        query.pop('filter')

    response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
    facets = response.json()['facets']

    total_count = response.json()['response']['numFound']

    stat_rightsHolder = []

    if total_count: # 有的話再存
        stat_rightsHolder = facets['stat_rightsHolder']['buckets']
        stat_rightsHolder.append({'val': 'total', 'count': total_count})

    return stat_rightsHolder


def create_dataset_stat(query_list):

    query = { "query": "*:*",
                "offset": 0,
                "limit": 0,
                "filter": query_list,
                "facet": {
                    "stat_tbiaDatasetID": {
                        'type': 'terms',
                        'field': 'tbiaDatasetID',
                        'mincount': 1,
                        'limit': -1,
                        'allBuckets': False,
                        'numBuckets': False
                    }
                }
            }

    if not query_list:
        query.pop('filter')

    response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
    facets = response.json()['facets']

    stat_tbiaDatasetID = []

    stat_tbiaDatasetID = facets['stat_tbiaDatasetID']['buckets']

    for row in stat_tbiaDatasetID:
        

        conn = psycopg2.connect(**datahub_db_settings)
        query = 'UPDATE dataset set "downloadCount" = "downloadCount" + 1 WHERE "tbiaDatasetID" = %s'
        with conn.cursor() as cursor:
            cursor.execute(query, (row.get('val'),))
            conn.commit()


        # if DatasetStat.objects.filter(tbiaDatasetID=row.get('val')).exists():
        #     dataset_obj = DatasetStat.objects.get(tbiaDatasetID=row.get('val'))
        #     dataset_obj.count += 1
        #     dataset_obj.modified = timezone.now()
        #     dataset_obj.save()
        # else:
        #     DatasetStat.objects.create(tbiaDatasetID=row.get('val'), count=1)

    return 'done'



def ark_generator(data_type, size=6, chars=string.ascii_lowercase + string.digits, mode=env('ENV')):
    if mode == 'prod':
        prefix_number = '1' # 正式站
    else:
        prefix_number = '2' # 測試站

    if data_type == 'news':
        prefix_char = 'n' # 文章
    else:
        prefix_char = 'd' # 資料

    new_ark = prefix_char + prefix_number + ''.join(random.choice(chars) for _ in range(size))
    # 要確認有沒有存在在資料庫中
    is_new_ark = False
    while not is_new_ark:
        if Ark.objects.filter(ark=new_ark).exists():
            new_ark = ''.join(random.choice(chars) for _ in range(size))
        else:
            is_new_ark = True
    return new_ark




def create_tbn_query(req_dict):

    query_list = []
    query_str_list = [] # 可以轉換的
    error_str_list = [] # 無法轉換的

    # 學名相關
    if val := req_dict.get('name'):
        val = val.strip()
        # 去除重複空格
        val = re.sub(' +', ' ', val)
        # 去除頭尾空格
        val = val.strip()
        query_list.append('taxonbioname:{}'.format(val))
        query_str_list.append('{} = {}'.format(gettext('學名/中文名/中文別名/同物異名/誤用名'),val))


    # 有無影像
    if has_image := req_dict.get('has_image'):
        if has_image == 'y':
            error_str_list.append('{} = {}'.format(gettext('有影像'),gettext('是')))
        else:
            error_str_list.append('{} = {}'.format(gettext('有影像'),gettext('否')))

    # 是否為原生種
    if is_native := req_dict.get('is_native'):
        if is_native == 'y':
            query_list.append('nativeness:i')
            query_str_list.append('{} = {}'.format(gettext('是否為原生種'),gettext('是')))
        elif is_native == 'n':
            query_list.append('nativeness:v,n,a,o')
            query_str_list.append('{} = {}'.format(gettext('是否為原生種'),gettext('否')))


    # 是否為保育類
    if is_protected := req_dict.get('is_protected'):
        if is_protected == 'y':
            query_list.append('protectedstatus:y01,y02,y03,w01')
            query_str_list.append('{} = {}'.format(gettext('是否為保育類'),gettext('是')))
        elif is_protected == 'n':
            error_str_list.append('{} = {}'.format(gettext('是否為保育類'),gettext('否')))


    if val := req_dict.get('taxonGroup'):
        if val in taxon_group_map_tbn.keys():
            query_list.append('taxongroup:{}'.format(taxon_group_map_tbn[val]))
            query_str_list.append('{} = {}'.format(gettext('物種類群'),gettext(val)))
        else:
            error_str_list.append('{} = {}'.format(gettext('物種類群'),gettext(val)))


    if val := req_dict.get('taxonRank'):
        if val == 'sub':
            error_str_list.append('{} = {}'.format(gettext('鑑定層級'),gettext("種下")))
        else:
            error_str_list.append('{} = {}'.format(gettext('鑑定層級'),gettext(map_occurrence[val])))


    if val := req_dict.get('datasetName'):
        d_list = []

        if isinstance(val, str):
            if val.startswith('['):
                for d in eval(val):
                    d_list.append(get_dataset_name(d))
            else:
                d_list.append(get_dataset_name(val))
        else:
            for d in list(val):
                d_list.append(get_dataset_name(d))

        error_str_list.append('{} = {}'.format(gettext('資料集名稱'),','.join(d_list)))


    if val := req_dict.get('locality'):
        l_list = []
        if isinstance(val, str):
            if val.startswith('['):
                l_list = eval(val)
            else:
                l_list.append(val)
        else:
            l_list = list(val)
        error_str_list.append('{} = {}'.format(gettext('出現地'),','.join(l_list)))


    if val := req_dict.get('rightsHolder'):
        r_list = []
        if isinstance(val, str):
            if val.startswith('['):
                r_list = eval(val)
            else:
                r_list.append(val)
        else:
            r_list = list(val)
        error_str_list.append('{} = {}'.format(gettext('來源資料庫'),','.join(r_list)))


    if val := req_dict.get('basisOfRecord'):

        error_str_list.append('{} = {}'.format(gettext('紀錄類型'),gettext(basis_map[val])))


    # TODO county, municipality 待確認對照表 先加到不可轉換

    for i in ['recordedBy', 'resourceContacts', 'preservation','occurrenceID', 'catalogNumber', 'recordNumber','organismQuantity','typeStatus',
              'county', 'municipality','taxonID']:
        if val := req_dict.get(i):
            if val != 'undefined':
                error_str_list.append('{} = {}'.format(gettext(map_occurrence[i]),gettext(val)))

    if val := req_dict.get('higherTaxa'):
        response = requests.get(f'{SOLR_PREFIX}taxa/select?q=id:{val}')
        if response.status_code == 200:
            resp = response.json()
            if data := resp['response']['docs']:
                data = data[0]
                error_str_list.append('{} = {}'.format(gettext('較高分類群'),f"{data.get('scientificName')} {data.get('common_name_c') if data.get('common_name_c')  else ''}"))

    if req_dict.get('start_date') and req_dict.get('end_date'):
        query_list.append('date:{},{}'.format(req_dict.get('start_date'),req_dict.get('end_date')))
        query_str_list.append('{} = {}'.format(gettext('起始日期'),req_dict.get('start_date')))
        query_str_list.append('{} = {}'.format(gettext('結束日期'),req_dict.get('end_date')))
    elif req_dict.get('start_date'):
        query_list.append('date:{}'.format(req_dict.get('start_date')))
        query_str_list.append('{} = {}'.format(gettext('起始日期'),req_dict.get('start_date')))
    elif req_dict.get('end_date'):
        error_str_list.append('{} = {}'.format(gettext('結束日期'),req_dict.get('end_date')))



    # 地圖框選
    if req_dict.get('geo_type') == 'map':
        if g_list := req_dict.get('polygon'): 
            query_list.append('wkt:'.format(g_list))
            query_str_list.append('{} = {}'.format(gettext('地圖框選'),g_list))


    # 上傳polygon
    if req_dict.get('geo_type') == 'polygon':
        # error_str_list.append('geo_type:polygon')
        error_str_list.append('{}'.format(gettext('上傳Polygon')))

    # 圓中心框選
    if req_dict.get('geo_type') == 'circle':
        if circle_radius := req_dict.get('circle_radius'):
            query_list.append('circle:{},{},{}'.format(req_dict.get('center_lon').strip(),req_dict.get('center_lat').strip(),int(circle_radius)*1000))
            query_str_list.append('{} = {}'.format(gettext('圓中心框選'),f"{gettext('半徑')} {circle_radius} KM {gettext('中心點經度')} {req_dict.get('center_lon')} {gettext('中心點緯度')} {req_dict.get('center_lat')}"))


    return query_list, query_str_list, error_str_list

