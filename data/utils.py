import pandas as pd
import numpy as np
import math

var_df = pd.DataFrame([
('臺','[臺台]'),
('台','[臺台]'),
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
    'rightsHolder': '來源資料庫', 
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
