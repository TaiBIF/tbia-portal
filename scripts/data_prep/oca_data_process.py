# 2023-05-23
# RUN in web container
# script for 海保署 data (from TBN & 海保署倉儲系統)
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


rank_map = {
    1: 'Domain', 2: 'Superkingdom', 3: 'Kingdom', 4: 'Subkingdom', 5: 'Infrakingdom', 6: 'Superdivision', 7: 'Division', 8: 'Subdivision', 9: 'Infradivision', 10: 'Parvdivision', 11: 'Superphylum', 12:
    'Phylum', 13: 'Subphylum', 14: 'Infraphylum', 15: 'Microphylum', 16: 'Parvphylum', 17: 'Superclass', 18: 'Class', 19: 'Subclass', 20: 'Infraclass', 21: 'Superorder', 22: 'Order', 23: 'Suborder',
    24: 'Infraorder', 25: 'Superfamily', 26: 'Family', 27: 'Subfamily', 28: 'Tribe', 29: 'Subtribe', 30: 'Genus', 31: 'Subgenus', 32: 'Section', 33: 'Subsection', 34: 'Species', 35: 'Subspecies', 36:
    'Nothosubspecies', 37: 'Variety', 38: 'Subvariety', 39: 'Nothovariety', 40: 'Form', 41: 'Subform', 42: 'Special Form', 43: 'Race', 44: 'Stirp', 45: 'Morph', 46: 'Aberration', 47: 'Hybrid Formula'}

def match_name(matching_name,sci_name,original_name,original_taxonuuid,is_parent,match_stage):
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
                    filtered_rs = pd.DataFrame(filtered_rs)[['accepted_namecode','family','class']].drop_duplicates().to_dict(orient='records')
                    # NomenMatch 有比對到有效taxon
                    # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_nm_result'] = True
                    # 是否有上階層資訊
                    has_parent = False
                    if original_taxonuuid:
                        tbn_url = "https://www.tbn.org.tw/api/v25/taxon?uuid=" + original_taxonuuid
                        tbn_response = requests.get(tbn_url)
                        if tbn_response.status_code == 200:
                            if tbn_data := tbn_response.json().get('data'):
                                t_family = tbn_data[0].get('family') # 科
                                t_class = tbn_data[0].get('class') # 綱
                                t_rank = tbn_data[0].get('taxonRank')
                                t_patent_uuid = tbn_data[0].get('parentUUID')
                                has_parent = True
                                # if t_family or t_class:
                                #     sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_tbn_parent'] = True
                    # 若有上階層資訊，加上比對上階層                    
                    if has_parent:
                        has_nm_parent = False
                        for frs in filtered_rs:
                            if t_rank in ['種','種下階層']: # 直接比對family
                                if frs.get('family'):
                                    # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_nm_parent'] = True
                                    if frs.get('family') == t_family:
                                        filtered_rss.append(frs)
                                        has_nm_parent = True
                                        # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_nm_parent'] = True
                                        # 本來就沒有上階層的話就不管
                            elif t_rank in ['亞綱','總目','目','亞目','總科','科','亞科','屬','亞屬']: # 
                                if frs.get('family') or frs.get('class'):
                                    # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_nm_parent'] = True
                                    if frs.get('family') == t_family or frs.get('class') == t_class:
                                        filtered_rss.append(frs)
                                        has_nm_parent = True
                                        # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_nm_parent'] = True
                            else:
                                has_nm_parent = False # TODO 這邊先當成沒有nm上階層，直接比對學名
                            # elif t_rank in ['綱','總綱','亞門']: # 還要再往上抓到門
                            # elif t_rank in ['亞界','總門','門']: #  還要再往上抓到界
                        # 如果有任何有nm上階層 且filtered_rss > 0 就代表有上階層比對成功的結果
                        if has_nm_parent:
                            if len(filtered_rss) == 1:
                                if is_parent:
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 1
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'parentTaxonID'] = filtered_rss[0]['accepted_namecode']
                                else:
                                    # 根據NomenMatch給的score確認名字是不是完全一樣
                                    if match_score < 1:
                                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 3
                                    else:
                                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = None
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rss[0]['accepted_namecode']
                            else:
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 4
                                # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = True
                        else:
                            # 如果沒有任何nm上階層的結果，則直接用filtered_rs
                            if len(filtered_rs) == 1:
                                if is_parent:
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 1
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'parentTaxonID'] = filtered_rs[0]['accepted_namecode']
                                else:
                                    if match_score < 1:
                                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 3
                                    else:
                                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = None
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']
                            else:
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 4
                                # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = True
                    # 若沒有上階層資訊，就直接取比對結果
                    else:
                        if len(filtered_rs) == 1:
                            if is_parent:
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 1
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'parentTaxonID'] = filtered_rs[0]['accepted_namecode']
                            else:
                                if match_score < 1:
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 3
                                else:
                                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = None
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']
                        else:
                            sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 4
                            # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = True
                # else:
                #     sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 2 # none


def match_namecode(matching_namecode,sci_name,original_name,original_taxonuuid,match_stage):
    # 這邊不會有fuzzy的問題 因為直接用namecode對應
    try:
        matching_namecode = str(int(matching_namecode))
    except:
        pass
    # 改成用TaiCOL API
    taxon_name_id = None
    taxon_data = []
    name_res = requests.get(f'https://api.taicol.tw/v2/namecode?namecode={matching_namecode}')
    if name_res.status_code == 200:
        if name_data := name_res.json().get('data'):
            taxon_name_id = name_data[0].get('name_id')
    if taxon_name_id:
        taxon_res = requests.get(f'https://api.taicol.tw/v2/nameMatch?name_id={taxon_name_id}')
        if taxon_res.status_code == 200:
            if taxon_data := taxon_res.json().get('data'):
                # 排除誤用
                taxon_data = [t.get('taxon_id') for t in taxon_data if t.get('usage_status') != 'Misapplied']
        filtered_rs = []
        # 可能對到不只一個taxon
        if Taxon.objects.filter(taxonID__in=taxon_data).exists():
            has_parent = False
            # namecode有對應到有效Taxon
            # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_namecode_result'] = True
            matched_taxon = Taxon.objects.filter(taxonID__in=taxon_data).values()
            if original_taxonuuid:
                tbn_url = "https://www.tbn.org.tw/api/v25/taxon?uuid=" + original_taxonuuid
                tbn_response = requests.get(tbn_url)
                if tbn_response.status_code == 200:
                    if tbn_data := tbn_response.json().get('data'):
                        t_family = tbn_data[0].get('family') # 科
                        t_class = tbn_data[0].get('class') # 綱
                        t_rank = tbn_data[0].get('taxonRank')
                        t_patent_uuid = tbn_data[0].get('parentUUID')
                        has_parent = True
                        # if t_family or t_class:
                        #     sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_tbn_parent'] = True
            # 若有上階層資訊，加上比對上階層                    
            if has_parent:
                has_taxon_parent = False
                for frs in matched_taxon:
                    if t_rank in ['種','種下階層']: # 直接比對family
                        if frs.get('family'):
                            # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_taxon_parent'] = True
                            if frs.get('family') == t_family:
                                filtered_rs.append(frs)
                                has_taxon_parent = True
                                # 本來就沒有上階層的話就不管
                    elif t_rank in ['亞綱','總目','目','亞目','總科','科','亞科','屬','亞屬']: # 
                        if frs.get('family') or frs.get('class'):
                            # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_taxon_parent'] = True
                            if frs.get('family') == t_family or frs.get('class') == t_class:
                                filtered_rs.append(frs)
                                has_taxon_parent = True
                    else:
                        has_taxon_parent = False # TODO 這邊先當成沒有nm上階層，直接比對學名
                    # elif t_rank in ['綱','總綱','亞門']: # 還要再往上抓到門
                    # elif t_rank in ['亞界','總門','門']: #  還要再往上抓到界
                # 如果有任何有nm上階層 且filtered_rss > 0 就代表有上階層比對成功的結果
                if has_taxon_parent:
                    # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'has_taxon_parent'] = True
                    if len(filtered_rs) == 1:
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rs[0]['taxonID']
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = None
                        # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = False
                    else:
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 4
                        # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = True
                else:
                    # 如果沒有任何nm上階層的結果，則直接用filtered_rs
                    if len(matched_taxon) == 1:
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = matched_taxon[0]['taxonID']
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = None
                        # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = False
                    else:
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 4
                        # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = True
            # 若沒有上階層資訊，就直接取比對結果
            else:
                if len(matched_taxon) == 1:
                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = matched_taxon[0]['taxonID']
                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = None
                    # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = False
                else:
                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),f'stage_{match_stage}'] = 4
                    # sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'more_than_one'] = True

def matching_flow(sci_names):
    ## 第一階段比對 - scientificName
    # TODO 未來要改成優先採用TaiCOL taxonID (若原資料庫有提供)
    for s in sci_names.index:
        s_row = sci_names.iloc[s]
        if s_row.scientificName:
            match_name(s_row.scientificName,s_row.scientificName,s_row.originalVernacularName,s_row.taxonUUID,False,1)
    ## 第二階段比對 沒有taxonID的 試抓TaiCOL namecode
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 2
    no_taxon = sci_names[sci_names.taxonID=='']
    for s in no_taxon.index:
        s_row = sci_names.iloc[s]
        if s_row.taiCOLNameCode:
            match_namecode(s_row.taiCOLNameCode,s_row.scientificName,s_row.originalVernacularName,s_row.taxonUUID,2)
    ## 第三階段比對 - originalVernacularName 英文比對
    ## 第三階段比對 - originalVernacularName 中文比對
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 3
    no_taxon = sci_names[(sci_names.taxonID=='')&(sci_names.originalVernacularName!='')]
    # 要判斷是中文還是英文(英文可能帶有標點符號)
    for nti in no_taxon.index:
        nt_str = sci_names.loc[nti,'originalVernacularName']
        # 拿掉階層名
        for v in rank_map.values():
            nt_str = nt_str.replace(v, '')
        # 拿掉空格
        nt_str = re.sub(' +', ' ', nt_str)
        str_list = nt_str.split(' ')
        # 英文的部分組合起來
        eng_part = [' '.join([s for s in str_list if not any(re.findall(r'[\u4e00-\u9fff]+', s))])]
        c_part = [s for s in str_list if re.findall(r'[\u4e00-\u9fff]+', s)]
        str_list = eng_part + c_part
        for sl in str_list:
            if sl:
                if not any(re.findall(r'[\u4e00-\u9fff]+', sl)):
                    # 英文
                    match_name(sl, sci_names.loc[nti,'scientificName'],sci_names.loc[nti,'originalVernacularName'],sci_names.loc[nti,'taxonUUID'],False,3)
                    # 如果對到就break
                    if sci_names.loc[nti,'taxonID']:
                        break
                else:
                    # 中文
                    match_name(sl, sci_names.loc[nti,'scientificName'],sci_names.loc[nti,'originalVernacularName'],sci_names.loc[nti,'taxonUUID'],False,3)
    ## 第四階段比對 - scientificName第一個英文單詞 (為了至少可以補階層)
    ## 這個情況要給的是parentTaxonID
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 4
    no_taxon = sci_names[sci_names.taxonID=='']
    for nti in no_taxon.index:
        if nt_str := sci_names.loc[nti,'scientificName']:
            if len(nt_str.split(' ')) > 1: # 等於0的話代表上面已經對過了
                match_name(nt_str.split(' ')[0], sci_names.loc[nti,'scientificName'],sci_names.loc[nti,'originalVernacularName'],sci_names.loc[nti,'taxonUUID'],True,4)
    ## 第五階段比對 - originalVernacularName第一個英文單詞 (為了至少可以補階層)
    ## 這個情況要給的是parentTaxonID
    sci_names.loc[sci_names.taxonID=='','match_stage'] = 5
    no_taxon = sci_names[(sci_names.taxonID=='')&(sci_names.parentTaxonID=='')]
    for nti in no_taxon.index:
        if nt_str := sci_names.loc[nti,'originalVernacularName']:
            if len(nt_str.split(' ')) > 1: # 等於0的話代表上面已經對過了
                # 以TBN的資料來說應該第一個是英文 但再確認一次
                nt_str = sci_names.loc[nti,'originalVernacularName']
                # 拿掉階層名
                for v in rank_map.values():
                    nt_str = nt_str.replace(v, '')
                # 拿掉空格
                nt_str = re.sub(' +', ' ', nt_str)
                str_list = nt_str.split(' ')
                # 英文的部分組合起來
                eng_part = ' '.join([s for s in str_list if not any(re.findall(r'[\u4e00-\u9fff]+', s))])
                # if not any(re.findall(r'[\u4e00-\u9fff]+', eng_part)):
                match_name(eng_part.split(' ')[0], sci_names.loc[nti,'scientificName'],sci_names.loc[nti,'originalVernacularName'],sci_names.loc[nti,'taxonUUID'],True,5)
    # 確定match_stage
    stage_list = [1,2,3,4,5]
    for i in stage_list[:4]:
        for stg in stage_list[stage_list.index(i)+1:]:
            sci_names.loc[sci_names.match_stage==i,f'stage_{stg}'] = None
    sci_names.loc[(sci_names.match_stage==5)&(sci_names.taxonID==''),'match_stage'] = None
    return sci_names

# 從TBN取得海保署資料集

request_url = f"https://www.tbn.org.tw/api/v25/dataset?name={urllib.parse.quote('海洋保育署')}"
response = requests.get(request_url)
data = response.json()
len_of_data = data['meta']['total'] 
j = 0
total_data = data["data"]
while data['links']['next'] != "":
    request_url = data['links']['next']
    response = requests.get(request_url)
    data = response.json()
    total_data += data["data"]
    j += 1

dataset = pd.DataFrame(total_data)

# dataset = dataset[~dataset.datasetName.str.contains('結構化')]

# 海洋保育署-MARN海龜擱淺資料
# 海洋保育署-MARN鯨豚擱淺資料
# 海洋保育署-iOcean海洋生物目擊回報
# 海洋保育署-iOcean垂釣回報
# 海洋保育署-白海豚調查相關結構化檔案
# 海洋保育署-110年生態調查相關結構化檔案
# 海洋保育署-108年國內海龜擱淺件數統計
# 海洋保育署-109年國內海龜擱淺件數統計
# 海洋保育署-110年國內海龜擱淺件數統計
# 海洋保育署-111年國內海龜擱淺件數統計
# 海洋保育署-108年國內鯨豚擱淺件數統計
# 海洋保育署-109年國內鯨豚擱淺件數統計
# 海洋保育署-110年國內鯨豚擱淺件數統計
# 海洋保育署-111年國內鯨豚擱淺件數統計

total_data = []
for d in dataset.datasetUUID:
    print('get:' + d)
    # 直接取限制型資料
    request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000&apikey={env('TBN_KEY')}"
    # request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000"
    response = requests.get(request_url)
    data = response.json()
    if len_of_data := data['meta'].get('total'):
        j = 0
        total_data += data["data"]
        while data['links']['next'] != "":
            print('get:'+d)
            request_url = data['links']['next']
            response = requests.get(request_url)
            data = response.json()
            total_data += data["data"]
            j += 1


group = 'oca'

df = pd.DataFrame(total_data)
df['group'] = group
df['dataGeneralizations'] = False
df['rightsHolder'] = '海洋保育資料倉儲系統'
df['datasetName'] = df['datasetName'].str.replace('海洋保育署-', '')


df = df[~(df.originalVernacularName.isin([nan,'',None])&df.scientificName.isin([nan,'',None]))]
df['scientificName'] = df.scientificName.str.replace('<i>','').str.replace('</i>','')
df = df.reset_index(drop=True)
df = df.replace({nan: '', None: ''})
df = df.drop(columns=['taxonRank'])
sci_names = df[['scientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].drop_duplicates().reset_index(drop=True)
sci_names['sourceScientificName'] = sci_names['scientificName']
sci_names['taxonID'] = ''
sci_names['parentTaxonID'] = ''
sci_names['match_stage'] = 1
# 各階段的issue default是沒有對到
sci_names['stage_1'] = 2
sci_names['stage_2'] = 2
sci_names['stage_3'] = 2
sci_names['stage_4'] = 2
sci_names['stage_5'] = 2
sci_names = matching_flow(sci_names)
# 比對流程結束後 統一串階層

fields = [f.name for f in Taxon._meta.get_fields()]
fields.remove('cites')
fields.remove('iucn')
fields.remove('redlist')
fields.remove('protected')
fields.remove('sensitive')

taxon_list = list(sci_names[sci_names.taxonID!=''].taxonID.unique()) + list(sci_names[sci_names.parentTaxonID!=''].parentTaxonID.unique())
final_taxon = Taxon.objects.filter(taxonID__in=taxon_list).values(*fields)
final_taxon = pd.DataFrame(final_taxon)

if len(final_taxon):
    final_taxon = final_taxon.drop(columns=['id'])
    final_taxon = final_taxon.rename(columns={'scientificNameID': 'taxon_name_id'})
    # sci_names = sci_names.rename(columns={'scientificName': 'sourceScientificName'})
    sci_names['copy_index'] = sci_names.index
    match_taxon_id = sci_names.drop(columns=['scientificName']).merge(final_taxon)
    # 若沒有taxonID的 改以parentTaxonID串
    match_parent_taxon_id = sci_names.drop(columns=['taxonID','scientificName']).merge(final_taxon,left_on='parentTaxonID',right_on='taxonID')
    match_parent_taxon_id['taxonID'] = ''
    match_taxon_id = match_taxon_id.append(match_parent_taxon_id,ignore_index=True)
    # 如果都沒有對到 要再加回來
    match_taxon_id = match_taxon_id.append(sci_names[~sci_names.copy_index.isin(match_taxon_id.copy_index.to_list())],ignore_index=True)
    match_taxon_id = match_taxon_id.replace({np.nan: ''})
    match_taxon_id[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']] = match_taxon_id[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].replace({'': '-999999'})

df = df.replace({nan: None, '': None, "": None, "\'\'": None, '\"\"': None})
df['grid_1'] = '-1_-1'
df['grid_5'] = '-1_-1'
df['grid_10'] = '-1_-1'
df['grid_100'] = '-1_-1'

df = df.reset_index(drop=True)
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
    df.loc[i, 'standardOrganismQuantity'] = quantity
    df.loc[i, 'organismQuantity'] = row.organismQuantity if row.individualCount in [None,'',nan] else row.individualCount
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
    df.loc[i, 'standardLongitude'] = standardLon
    df.loc[i, 'standardLatitude'] = standardLat
    df.loc[i, 'location_rpt'] = location_rpt
    if standardLon and standardLat:
        df.loc[i, 'verbatimCoordinateSystem'] = 'DecimalDegrees'
        grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.01)
        df.loc[i, 'grid_1'] = str(int(grid_x)) + '_' + str(int(grid_y))
        grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.05)
        df.loc[i, 'grid_5'] = str(int(grid_x)) + '_' + str(int(grid_y))
        grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 0.1)
        df.loc[i, 'grid_10'] = str(int(grid_x)) + '_' + str(int(grid_y))
        grid_x, grid_y = convert_coor_to_grid(standardLon, standardLat, 1)
        df.loc[i, 'grid_100'] = str(int(grid_x)) + '_' + str(int(grid_y))
    try:
        scientificNameID = int(row.scientificNameID)
    except:
        scientificNameID = row.scientificNameID
    df.loc[i, 'scientificNameID'] = scientificNameID
    df.loc[i, 'id'] = bson.objectid.ObjectId()

# 串回taxon資訊  
df = df.replace({nan: None})
df = df.rename(columns={ 'scientificName': 'sourceScientificName'})
if len(match_taxon_id):
    df[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']] = df[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].replace({'': '-999999',None:'-999999'})
    df = df.merge(match_taxon_id, on=['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode'], how='left')
    df[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']] = df[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].replace({'-999999': ''})

df = df.replace({nan: None})
df = df.drop(columns=['taxonUUID','taiCOLNameCode'],errors='ignore')


df['standardDate'] = df['eventDate'].apply(lambda x: convert_date(x))
df['recordType'] = 'occ'
df['recordedBy'] = df['recordedBy'].apply(lambda x: x.strip() if x else None)

df = df.rename(columns={'geodeticDatum': 'verbatimSRS', 'decimalLongitude': 'verbatimLongitude', 'decimalLatitude': 'verbatimLatitude',
                         'eventPlaceAdminarea': 'locality', 'modified': 'sourceModified',
                         'originalVernacularName': 'originalScientificName',
                         'vernacularName': 'sourceVernacularName'})

df['created'] = datetime.now()
df['modified'] = datetime.now()

df = df.drop(columns=
['datasetPublisher','datasetAuthor','identifiedBy','identificationVerificationStatus','eventTime','year','month','day',
'hour','minute','county','countyCode','recordNumber','individualCount','taxonGroup','protectedStatusTW','categoryRedlistTW',
'categoryIUCN','endemism','nativeness','establishmentMeans','coordinatePrecision','datasetUUID','datasetURL','resourceCitationIdentifier',
'simplifiedScientificName','taiCOLNameCode','tfNameCode','externalID','eventID','samplingProtocol','collectionID','partner','verbatimEventDate','originalScientificName',
'taxonGroup','coordinatePrecision'], errors='ignore')

df['occurrenceID'] = ''

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
match_log['match_stage'] = match_log['match_stage'].apply(lambda x: int(x) if x else x)
match_log['stage_1'] = match_log['stage_1'].apply(lambda x: issue_map[x] if x else x)
match_log['stage_2'] = match_log['stage_2'].apply(lambda x: issue_map[x] if x else x)
match_log['stage_3'] = match_log['stage_3'].apply(lambda x: issue_map[x] if x else x)
match_log['stage_4'] = match_log['stage_4'].apply(lambda x: issue_map[x] if x else x)
match_log['stage_5'] = match_log['stage_5'].apply(lambda x: issue_map[x] if x else x)
match_log = match_log.rename(columns={'id': 'tbiaID'})
match_log['tbiaID'] = match_log['tbiaID'].apply(lambda x: str(x))
conn_string = env('DATABASE_URL').replace('postgres://', 'postgresql://')
db = create_engine(conn_string)
match_log.to_sql('manager_matchlog', db, if_exists='append',schema='public', index=False)
# final = final.rename(columns={'taxon_name_id': 'scientificNameID'})
df = df.drop(columns=['match_stage','stage_1','stage_2','stage_3','stage_4','stage_5','taiCOLNameCode','taxonUUID','taxon_name_id','copy_index'],errors='ignore')
df.to_csv(f'/tbia-volumes/solr/csvs/processed/{group}_from_tbn.csv', index=False)



# # 海保署 API

# d_list = ['488cdd8b-ddca-49a9-96c2-20771682640f',
# 'a5fa22f6-a950-4677-98b8-33033b5cfff6',
# 'e75e41e4-d157-42e6-b36b-4b27ba5d632d',
# '53a26fed-436d-4d8a-9ba1-59e83c9ef4bd',
# '7cdbcb45-037a-4ee3-94af-5fb93a8c9d39',
# '3e97198f-972f-44be-82d8-92c1f9af74cd',
# 'af174f84-ba9e-44ff-8ac3-b0d8bf47ac05',
# '01748ac5-993b-4e75-bd5b-56a8ae4fe5c5',
# 'fdab2d5a-535d-47ff-8229-c6a3d7051a65',
# 'ad1b1949-001b-431f-a2f0-6a37e72bdc0e',
# '96272500-e4f8-4f1e-93ff-4b2ffa90dbe9',
# '8017ec93-2089-408d-862e-661a2cecedf4',
# '115f4b52-c185-44b4-91a3-ce07e86c1082',
# 'bd5a7bd5-7065-4d82-b756-1973c30cfd0a',
# 'cb527c5a-078a-4555-8105-f31aa0b068a4',
# 'b0c308cf-803f-47f5-bc79-5e0c8e343ed4',
# '507ead53-66b9-4273-bbd8-1f1a46a3871d',
# '39616c61-0c28-4662-971b-ac6c2a51dbf9'
# ]

# d_names = [
# '海域棲地調查相關結構化檔案',
# '海域棲地調查相關結構化檔案',
# '海域棲地調查相關結構化檔案',
# '海域棲地調查相關結構化檔案',
# '海域棲地調查相關結構化檔案',
# '海域棲地調查相關結構化檔案',
# '珊瑚調查相關結構化檔案',
# '硨磲貝及其他重要螺貝類調查相關結構化檔案',
# '三棘鱟調查相關結構化檔案',
# '軟骨魚調查相關結構化檔案',
# '海鳥調查相關結構化檔案',
# '海鳥調查相關結構化檔案',
# '海馬調查相關結構化檔案',
# '鯨豚調查相關結構化檔案',
# '白海豚調查相關結構化檔案',
# '白海豚調查相關結構化檔案',
# '白海豚調查相關結構化檔案',
# '白海豚調查相關結構化檔案'
# ]

# ocas = pd.DataFrame({'file_id': d_list, 'name': d_names})


# import json


# total_df = pd.DataFrame()
# for i in ocas.index:
#     print(i)
#     row = ocas.iloc[i]
#     url = f"https://iocean.oca.gov.tw/oca_datahub/WebService/GetData.ashx?id={row.file_id}"
#     payload = {'API-KEY': ''}
#     headers = {'content-type': 'application/json'}
#     data = []
#     r = requests.post(url, data=json.dumps(payload), headers=headers)
#     if r.status_code == 200:
#         x = r.content
#         data += json.loads(x)
#         tmp_df = pd.DataFrame(data)
#         tmp_df['datasetName'] = row['name']
#         total_df = total_df.append(tmp_df)
        




