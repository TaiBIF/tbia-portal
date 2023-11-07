import pandas as pd
import numpy as np
import math
from dateutil import parser
from datetime import datetime, timedelta
import numpy as np
import bisect
import os
from os.path import exists
from data.models import Taxon #DatasetKey, 
from conf.settings import datahub_db_settings
import psycopg2


def get_dataset_key(key):
    results = None
    conn = psycopg2.connect(**datahub_db_settings)
    query = 'SELECT "name" FROM dataset WHERE id = %s'
    with conn.cursor() as cursor:
        cursor.execute(query, (key,))
        results = cursor.fetchone()
        conn.close()
        if results:
            results = results[0]
    return results
        

# DatasetKey.objects.filter(record_type='col',deprecated=False,name__in=dataset_list)

def get_dataset_list(dataset_list ,record_type=None, rights_holder=None):
    results = []
    conn = psycopg2.connect(**datahub_db_settings)


    query = f''' select distinct on ("name") id, name FROM dataset WHERE "name" IN %s AND deprecated = 'f' 
                {f"AND record_type = '{record_type}'" if record_type else ''}  
                {f"AND rights_holder = '{rights_holder}'" if rights_holder else ''}  
            '''


    # if record_type:
    #     query = '''SELECT id, "name" FROM dataset WHERE "name" IN %s AND record_type = %s AND deprecated = 'f' '''
    #     with conn.cursor() as cursor:
    #         cursor.execute(query, (tuple(dataset_list),record_type, ))
    #         results = cursor.fetchall()
    #         conn.close()
    # else:
    #     query = ''' select distinct on ("name") id, name FROM dataset WHERE "name" IN %s AND deprecated = 'f'  '''
    with conn.cursor() as cursor:
        cursor.execute(query, (tuple(dataset_list), ))
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

taxon_group_map = {
    'Insects' : [{'key': 'class', 'value': 'Insecta'}],
    'Fishes' : [{'key': 'class', 'value': 'Actinopterygii'},{'key': 'class', 'value': 'Chondrichthyes'},{'key': 'class', 'value': 'Myxini'}],
    'Reptiles' : [{'key': 'class', 'value': 'Reptilia'}],
    'Fungi' : [{'key': 'kingdom', 'value': 'Fungi'}],
    'Plants' : [{'key': 'kingdom', 'value': 'Plantae'}],
    'Birds' : [{'key': 'class', 'value': 'Aves'}],
    'Mammals' : [{'key': 'class', 'value': 'Mammalia'}],
}

taxon_group_map_c = {
    'Insects' : '昆蟲',
    'Fishes' : '魚類',
    'Reptiles' : '爬蟲類',
    'Fungi' : '真菌(含地衣)',
    'Plants' : '植物',
    'Birds' : '鳥類',
    'Mammals' : '哺乳類',
}


def convert_grid_to_coor(grid_x, grid_y, list_x, list_y):
  center_x = (list_x[grid_x] + list_x[grid_x+1])/2
  center_y = (list_y[grid_y] + list_y[grid_y+1])/2
  return center_x, center_y

def convert_coor_to_grid(x, y, grid):
    list_x = np.arange(-180, 180+grid, grid)
    list_y = np.arange(-90, 90+grid, grid)
    grid_x = bisect.bisect(list_x, x)-1
    grid_y = bisect.bisect(list_y, y)-1
    return grid_x, grid_y

def convert_grid_to_square(grid_x, grid_y, grid):
    list_x = np.arange(-180, 180+grid, grid)
    list_y = np.arange(-90, 90+grid, grid)
    x1 = list_x[grid_x]
    x2 = list_x[grid_x+1]
    y1 = list_y[grid_y]
    y2 = list_y[grid_y+1]
    # [[x1,y1],[x1,y2],[x2,y1],[x2,y2]]
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
              'variety', 'subvariety', 'nothovariety', 'form', 'subform', 'special-form', 'race', 'stirp', 'morph', 'aberration', 'hybrid-formula']

var_df = pd.DataFrame([
('鲃','[鲃䰾]'),
('䰾','[鲃䰾]'),
('刺','[刺刺]'),
('刺','[刺刺]'),
('葉','[葉葉]'),
('葉','[葉葉]'),
('鈎','[鈎鉤]'),
('鉤','[鈎鉤]'),
('臺','[臺台]'),
('台','[臺台]'),
('螺','[螺螺]'),
('螺','[螺螺]'),
('羣','[群羣]'),
('群','[群羣]'),
('峯','[峯峰]'),
('峰','[峯峰]'),
('曬','[晒曬]'),
('晒','[晒曬]'),
('裏','[裏裡]'),
('裡','[裏裡]'),
('薦','[荐薦]'),
('荐','[荐薦]'),
('艷','[豔艷]'),
('豔','[豔艷]'),
('粧','[妝粧]'),
('妝','[妝粧]'),
('濕','[溼濕]'),
('溼','[溼濕]'),
('樑','[梁樑]'),
('梁','[梁樑]'),
('秘','[祕秘]'),
('祕','[祕秘]'),
('污','[汙污]'),
('汙','[汙污]'),
('册','[冊册]'),
('冊','[冊册]'),
('唇','[脣唇]'),
('脣','[脣唇]'),
('朶','[朵朶]'),
('朵','[朵朶]'),
('鷄','[雞鷄]'),
('雞','[雞鷄]'),
('猫','[貓猫]'),
('貓','[貓猫]'),
('踪','[蹤踪]'),
('蹤','[蹤踪]'),
('恒','[恆恒]'),
('恆','[恆恒]'),
('獾','[貛獾]'),
('貛','[貛獾]'),
('万','[萬万]'),
('萬','[萬万]'),
('两','[兩两]'),
('兩','[兩两]'),
('椮','[槮椮]'),
('槮','[槮椮]'),
('体','[體体]'),
('體','[體体]'),
('鳗','[鰻鳗]'),
('鰻','[鰻鳗]'),
('蝨','[虱蝨]'),
('虱','[虱蝨]'),
('鲹','[鰺鲹]'),
('鰺','[鰺鲹]'),
('鳞','[鱗鳞]'),
('鱗','[鱗鳞]'),
('鳊','[鯿鳊]'),
('鯿','[鯿鳊]'),
('鯵','[鰺鯵]'),
('鰺','[鰺鯵]'),
('鲨','[鯊鲨]'),
('鯊','[鯊鲨]'),
('鹮','[䴉鹮]'),
('䴉','[䴉鹮]'),
('鴴','(行鳥|鴴)'),
('鵐','(鵐|巫鳥)'),
('䱵','(䱵|魚翁)'),
('䲗','(䲗|魚銜)'),
('䱀','(䱀|魚央)'),
('䳭','(䳭|即鳥)'),
('鱼','[魚鱼]'),
('魚','[魚鱼]'),
('万','[萬万]'),
('萬','[萬万]'),
('鹨','[鷚鹨]'),
('鷚','[鷚鹨]'),
('蓟','[薊蓟]'),
('薊','[薊蓟]'),
('黒','[黑黒]'),
('黑','[黑黒]'),
('隠','[隱隠]'),
('隱','[隱隠]'),
('黄','[黃黄]'),
('黃','[黃黄]'),
('囓','[嚙囓]'),
('嚙','[嚙囓]'),
('莨','[茛莨]'),
('茛','[茛莨]'),
('霉','[黴霉]'),
('黴','[黴霉]'),
('莓','[苺莓]'),  
('苺','[苺莓]'),  
('藥','[葯藥]'),  
('葯','[葯藥]'),  
('菫','[堇菫]'),
('堇','[堇菫]')], columns=['char','pattern'])
var_df['idx'] = var_df.groupby(['pattern']).ngroup()

var_df_2 = pd.DataFrame([('行鳥','(行鳥|鴴)'),
('蝦虎','[鰕蝦]虎'),
('鰕虎','[鰕蝦]虎'),
('巫鳥','(鵐|巫鳥)'),
('魚翁','(䱵|魚翁)'),
('魚銜','(䲗|魚銜)'),
('魚央','(䱀|魚央)'),
('游蛇','[遊游]蛇'),
('遊蛇','[遊游]蛇'),
('即鳥','(䳭|即鳥)'),
('椿象','[蝽椿]象'),
('蝽象','[蝽椿]象')], columns=['char','pattern'])


# 產生javascript使用的dict
# dict(zip(var_df.char, var_df.pattern))
# dict(zip(var_df_2.char, var_df_2.pattern))


# 先對一個字再對兩個字

def get_variants(string):
  new_string = ''
  # 單個異體字
  for s in string:    
    if len(var_df[var_df['char']==s]):
      new_string += var_df[var_df['char']==s].pattern.values[0]
    else:
      new_string += s
  # 兩個異體字
  for i in var_df_2.index:
    char = var_df_2.loc[i, 'char']
    if char in new_string:
      new_string = new_string.replace(char,f"{var_df_2.loc[i, 'pattern']}")
  return new_string


def get_page_list(current_page, total_page, window=5):
  list_index = math.ceil(current_page/window)
  if list_index*window > total_page:
    page_list = list(range(list_index*window-(window-1),total_page+1))
  else:
    page_list = list(range(list_index*window-(window-1),list_index*window+1))
  return page_list

# from django.core.paginator import Paginator

# def get_page_list(current_page, total_count, data_per_page, window=5):
#   objects = [r for r in range(1,total_count+1)]
#   p = Paginator(objects, data_per_page)
#   page_list = list(p.get_elided_page_range(current_page, on_each_side=int((window-1)/2), on_ends=0))
#   return page_list


def is_alpha(word):
    try:
        return word.encode('ascii').isalpha()
    except:
        return False


dup_col = ['scientificName', 'common_name_c', 
            'alternative_name_c', 'synonyms', 'misapplied','kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c',
            'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c',  'sourceScientificName', 'sourceVernacularName']

# 進階搜尋查詢name欄位
name_search_col = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'sourceScientificName', 'sourceVernacularName']

def get_key(val, my_dict):
    for key, value in my_dict.items():
         if val == value:
             return key
 
    return "key doesn't exist"

# facet_collection = ['scientificName', 'common_name_c','alternative_name_c', 
#                     'synonyms', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
#                     'locality', 'recordedBy', 'typeStatus', 'preservation', 'datasetName', 'license',
#                     'kingdom','phylum','class','order','family','genus','species',
#                     'kingdom_c','phylum_c','class_c','order_c','family_c','genus_c']

# facet_occurrence = ['scientificName', 'common_name_c', 'alternative_name_c', 
#                     'synonyms', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
#                     'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'license',
#                     'kingdom','phylum','class','order','family','genus','species',
#                     'kingdom_c','phylum_c','class_c','order_c','family_c','genus_c']

map_occurrence = {
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
    'microphylum'	:'小門',
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
    'special-form'	:'特別品型',
    'race'	:'種族',
    'stirp'	:'種族',
    'morph'	:'形態型',
    'aberration'	:'異常個體',
    'hybrid-formula'	:'雜交組合',
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
    'microphylum_c'	:'小門中文名',
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
    'special-form_c'	:'特別品型中文名',
    'race_c'	:'種族中文名',
    'stirp_c'	:'種族中文名',
    'morph_c'	:'形態型中文名',
    'aberration_c'	:'異常個體中文名',
    'hybrid-formula_c'	:'雜交組合中文名',
    'higherTaxa'	:'較高分類群',
    'taxonGroup'	:'物種類群',
    'scientificName': '學名',
    'common_name_c': '中文名', 
    'alternative_name_c': '中文別名', 
    'synonyms': '同物異名',
    'misapplied': '誤用名',
    'sourceScientificName': '來源資料庫使用學名',
    'sourceVernacularName': '來源資料庫使用中文名',
    'taxonRank': '鑑定層級', 
    'sensitiveCategory': '敏感層級', 
    'rightsHolder': '來源資料庫', 
    'taxonID': 'TaiCOL物種編號', 
    'eventDate': '紀錄日期', 
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
    'coordinateUncertaintyInMeters': '座標誤差',
    'dataGeneralizations': '座標是否有模糊化',
    'coordinatePrecision': '座標模糊化程度',
    'basisOfRecord': '紀錄類型', 
    'datasetName': '資料集名稱', 
    'resourceContacts': '資料集聯絡人',
    'license': '授權狀況',
}

map_collection = {
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
    'microphylum'	:'小門',
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
    'special-form'	:'特別品型',
    'race'	:'種族',
    'stirp'	:'種族',
    'morph'	:'形態型',
    'aberration'	:'異常個體',
    'hybrid-formula'	:'雜交組合',
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
    'microphylum_c'	:'小門中文名',
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
    'special-form_c'	:'特別品型中文名',
    'race_c'	:'種族中文名',
    'stirp_c'	:'種族中文名',
    'morph_c'	:'形態型中文名',
    'aberration_c'	:'異常個體中文名',
    'hybrid-formula_c'	:'雜交組合中文名',
    'higherTaxa'	:'較高分類群',
    'taxonGroup'	:'物種類群',
    'scientificName': '學名', 
    'common_name_c': '中文名', 
    'alternative_name_c': '中文別名', 
    'synonyms': '同物異名',
    'misapplied': '誤用名',
    'sourceScientificName': '來源資料庫使用學名',
    'sourceVernacularName': '來源資料庫使用中文名',
    'rightsHolder': '來源資料庫', 
    'taxonID': 'TaiCOL物種編號', 
    'catalogNumber': '館藏號', 
    'taxonRank': '鑑定層級', 
    'sensitiveCategory': '敏感層級', 
    'typeStatus': '標本類型', 
    'preservation': '保存方式', 
    'eventDate': '採集日期', 
    'date': '採集日期', 
    'locality': '採集地', 
    'recordedBy': '採集者', 
    'recordNumber': '採集號', 
    'organismQuantity': '數量',
    'quantity': '數量',
    'organismQuantityType': '數量單位',
    'verbatimLongitude': '經度',
    'verbatimLatitude': '緯度',
    'lon': '經度',
    'lat': '緯度',
    'verbatimCoordinateSystem': '座標系統',
    'verbatimSRS': '空間參考系統',
    'coordinateUncertaintyInMeters': '座標誤差',
    'dataGeneralizations': '座標是否有模糊化',
    'coordinatePrecision': '座標模糊化程度',
    'datasetName': '資料集名稱', 
    'resourceContacts': '資料集聯絡人',
    'license': '授權狀況',
}


date_formats = ['%Y/%m/%d','%Y%m%d','%Y-%m-%d','%Y/%m/%d %p %H:%M:%S','%Y-%m-%d %H:%M','%Y-%m-%d %H:%M:%S','%Y/%m/%d %H:%M:%S']

def convert_date(date):
    formatted_date = None
    if date != '' and date is not None:
        for ff in date_formats:
            try:
                formatted_date = datetime.strptime(date, ff)
                return formatted_date
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
'eventDate',
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
'parentTaxonID',
'scientificName',
'name_author',
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

sensitive_cols = ['standardRawLatitude',
'standardRawLongitude',
'verbatimRawLatitude',
'verbatimRawLongitude']


# 整理搜尋條件
def create_query_display(search_dict,sq_id):
    query = ''
    if search_dict.get('record_type') == 'occ':
        query += '<b>類別</b>：物種出現紀錄'
        map_dict = map_occurrence
    else:
        map_dict = map_collection
        query += '<b>類別</b>：自然史典藏'

    d_list = []
    r_list = []
    l_list = []

    for k in search_dict.keys():
        if k in map_dict.keys():
            if k == 'taxonRank':
                if search_dict[k] == 'sub':
                    query += f"<br><b>{map_dict[k]}</b>：種下"
                else:
                    query += f"<br><b>{map_dict[k]}</b>：{map_dict[search_dict[k]]}"
            elif k == 'datasetName':
                if isinstance(search_dict[k], str):
                    if search_dict[k].startswith('['):
                        for d in eval(search_dict[k]):
                            if d_name := get_dataset_key(d):
                                d_list.append(d_name)
                            # if DatasetKey.objects.filter(id=d).exists():
                                # d_list.append(DatasetKey.objects.get(id=d).name)
                    else:
                        if d_name := get_dataset_key(search_dict[k]):
                            d_list.append(d_name)
                        # if DatasetKey.objects.filter(id=search_dict[k]).exists():
                        #     d_list.append(DatasetKey.objects.get(id=search_dict[k]).name)
                else:
                    for d in list(search_dict[k]):
                        if d_name := get_dataset_key(d):
                            d_list.append(d_name)
                        # if DatasetKey.objects.filter(id=d).exists():
                        #     d_list.append(DatasetKey.objects.get(id=d).name)
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
            elif k == 'higherTaxa':
                if Taxon.objects.filter(taxonID=search_dict[k]).exists():
                    taxon_obj = Taxon.objects.get(taxonID=search_dict[k])
                    query += f"<br><b>{map_dict[k]}</b>：{taxon_obj.scientificName} {taxon_obj.common_name_c if taxon_obj.common_name_c  else ''}"
            elif k == 'taxonGroup':
                if search_dict[k] in taxon_group_map_c.keys():
                    query += f"<br><b>{map_dict[k]}</b>：{taxon_group_map_c[search_dict[k]]}"
            else:
                query += f"<br><b>{map_dict[k]}</b>：{search_dict[k]}"
        # 地圖搜尋
        elif k == 'geo_type':
            if search_dict[k] == 'polygon':
                geojson_path= f"media/geojson/{search_dict.get('geojson_id')}.json"
                if exists(os.path.join('/tbia-volumes/', geojson_path)):
                    query += f"<br><b>上傳polygon</b>：<a target='_blank' href='/{geojson_path}'>點此下載geojson</a>"
            elif search_dict[k] == 'circle':
                if search_dict.get('circle_radius') and search_dict.get('center_lon') and search_dict.get('center_lat'):
                    query += f"<br><b>圓中心框選</b>：半徑 {search_dict.get('circle_radius')} KM 中心點經度 {search_dict.get('center_lon')} 中心點緯度 {search_dict.get('center_lat')}" 
            elif search_dict[k] == 'map':
                query += f"<br><b>地圖框選</b>：{search_dict.get('polygon')}" 
        # 日期
        elif k == 'start_date':
            query += f"<br><b>起始日期</b>：{search_dict.get('start_date')}" 
        elif k == 'end_date':
            query += f"<br><b>結束日期</b>：{search_dict.get('end_date')}" 
        elif k == 'name':
            query += f"<br><b>中文名/學名/中文別名</b>：{search_dict.get('name')}" 
        elif k == 'has_image':
            query += f"<br><b>有無影像</b>：{'有' if search_dict.get('has_image') == 'y' else '無'}" 
    if r_list:
        query += f"<br><b>來源資料庫</b>：{'、'.join(r_list)}" 
    if d_list:
        query += f"<br><b>資料集名稱</b>：{'、'.join(d_list)}" 
    if l_list:
        query += f"<br><b>{map_dict['locality']}</b>：{'、'.join(l_list)}" 

    return query


# 整理搜尋條件 再次查詢按鈕的連結
def create_query_a(search_dict):
    query_a = ''

    d_list = []
    r_list = []
    l_list = []

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

    for l in l_list:
        query_a += f'&locality={l}'
    for r in r_list:
        query_a += f'&rightsHolder={r}'
    for d in d_list:
        query_a += f'&datasetName={d}'

    return query_a


def query_a_href(query, query_a):
    query += f'''<br><a class="search-again-a" target="_blank" href="{query_a}">再次查詢<svg class="search-again-icon" xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25"><g id="loupe" transform="translate(0 -0.003)"><g id="Group_13" data-name="Group 13" transform="translate(0 0.003)"><path id="Path_54" data-name="Path 54" d="M24.695,23.225l-7.109-7.109a9.915,9.915,0,1,0-1.473,1.473L23.222,24.7a1.041,1.041,0,1,0,1.473-1.473ZM9.9,17.711A7.812,7.812,0,1,1,17.708,9.9,7.821,7.821,0,0,1,9.9,17.711Z" transform="translate(0 -0.003)" fill="#3f5146"></path></g></g></svg></a>'''
    return query



# taxon-related columns
taxon_cols = [
    'domain',
    'superkingdom',
    'kingdom',
    'subkingdom',
    'infrakingdom',
    'superdivision',
    'division',
    'subdivision',
    'infradivision',
    'parvdivision',
    'superphylum',
    'phylum',
    'subphylum',
    'infraphylum',
    'microphylum',
    'parvphylum',
    'superclass',
    'class',
    'subclass',
    'infraclass',
    'superorder',
    'order',
    'suborder',
    'infraorder',
    'superfamily',
    'family',
    'subfamily',
    'tribe',
    'subtribe',
    'genus',
    'subgenus',
    'section',
    'subsection',
    'species',
    'subspecies',
    'nothosubspecies',
    'variety',
    'subvariety',
    'nothovariety',
    'form',
    'subform',
    'special-form',
    'race',
    'stirp',
    'morph',
    'aberration',
    'hybrid-formula',
    'domain_c',
    'superkingdom_c',
    'kingdom_c',
    'subkingdom_c',
    'infrakingdom_c',
    'superdivision_c',
    'division_c',
    'subdivision_c',
    'infradivision_c',
    'parvdivision_c',
    'superphylum_c',
    'phylum_c',
    'subphylum_c',
    'infraphylum_c',
    'microphylum_c',
    'parvphylum_c',
    'superclass_c',
    'class_c',
    'subclass_c',
    'infraclass_c',
    'superorder_c',
    'order_c',
    'suborder_c',
    'infraorder_c',
    'superfamily_c',
    'family_c',
    'subfamily_c',
    'tribe_c',
    'subtribe_c',
    'genus_c',
    'subgenus_c',
    'section_c',
    'subsection_c',
    'species_c',
    'subspecies_c',
    'nothosubspecies_c'
    'variety_c',
    'subvariety_c',
    'nothovariety_c',
    'form_c',
    'subform_c',
    'special-form_c',
    'race_c',
    'stirp_c',
    'morph_c',
    'aberration_c',
    'hybrid-formula_c',
    'common_name_c', 
    'scientificName', 
    'alternative_name_c', 
    'synonyms',
    'misapplied'
]