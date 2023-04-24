# 2023-02-10
# RUN in web container
# script for TBN API version 2.5
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

# 學名比對

folder = '/tbia-volumes/bucket/tbn_v25/'
extension = 'csv'
os.chdir(folder)
files = glob.glob('*.{}'.format(extension))

# TODO 這邊要先排除掉GBIF

group = 'tesri'

count = 0
for f in files:
    count += 1
    d = f.split('.csv')[0]
    print(count, ': ', d)
    df = pd.read_csv(f, index_col=0)
    # 排除originalVernacularName&scientificNam皆為空值的資料
    df = df[~(df.originalVernacularName.isin([nan,'',None])&df.scientificName.isin([nan,'',None]))]
    df = df.reset_index(drop=True)
    df = df.replace({nan: '', None: ''})
    sci_names = df[['scientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].drop_duplicates().reset_index(drop=True)
    sci_names['sourceScientificName'] = sci_names['scientificName']
    sci_names['scientificName'] = sci_names.scientificName.str.replace('<i>','').str.replace('</i>','')
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
    taxon_list = list(sci_names[sci_names.taxonID!=''].taxonID.unique()) + list(sci_names[sci_names.parentTaxonID!=''].parentTaxonID.unique())
    final_taxon = Taxon.objects.filter(taxonID__in=taxon_list).values()
    final_taxon = pd.DataFrame(final_taxon)
    if len(final_taxon):
        final_taxon = final_taxon.drop(columns=['id'])
        final_taxon = final_taxon.rename(columns={'scientificNameID': 'taxon_name_id'})
        # sci_names = sci_names.rename(columns={'scientificName': 'sourceScientificName'})
        match_taxon_id = sci_names.drop(columns=['scientificName']).merge(final_taxon,how='left')
        # 若沒有taxonID的 改以parentTaxonID串
        match_parent_taxon_id = sci_names.drop(columns=['taxonID','scientificName']).merge(final_taxon,left_on='parentTaxonID',right_on='taxonID')
        match_parent_taxon_id['taxonID'] = ''
        match_taxon_id = match_taxon_id.append(match_parent_taxon_id,ignore_index=True)
        match_taxon_id[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']] = match_taxon_id[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].replace({'': '-999999'})
    row_list = []
    df = df.replace({nan: None, '': None, "": None, "\'\'": None, '\"\"': None})
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
        if not convert_date:
            converted_date = convert_date(row.verbatimEventDate)
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
            'eventDate' : row.eventDate if row.eventDate else row.verbatimEventDate,
            'standardDate' : converted_date,
            'verbatimLongitude' : row.decimalLongitude,
            'verbatimLatitude' : row.decimalLatitude,
            'verbatimCoordinateSystem' : 'DecimalDegrees' if row.decimalLongitude and row.decimalLatitude else None, # TBN的情況
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
            # TODO 這邊也要考慮mediaLicense為多值的情況 但目前都是單值
            'mediaLicense' : row.mediaLicense,
            'selfProduced' : row.selfProduced,
            'collectionID' : c_list_str,
            'associatedMedia' : row.associatedMedia,
            'recordNumber' : recordNumber,
            'scientificNameID' : scientificNameID,
            'preservation' : None,
            # 'taxonID' : row.get('taxonID'),
            'location_rpt' : location_rpt,
            # 'originalVernacularName': row.originalVernacularName, 
            'taxonUUID': row.taxonUUID, 
            'taiCOLNameCode': row.taiCOLNameCode
            }
        row_list.append(tmp)
    final = pd.DataFrame(row_list)
    # 確認有無限制型資料
    if len(final[final.dataGeneralizations==True]) > 1:
        request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID={d}&limit=1000&apikey={env('TBN_KEY')}"
        # request_url = f"https://www.tbn.org.tw/api/v25/occurrence?datasetUUID=7a1d54c7-8f2e-4672-bb5b-bc29249aff9f&limit=1000&apikey=9c98309a-880c-4eb3-b1fa-c2ecafb744db"
        response = requests.get(request_url)
        if response.status_code==200:
            data = response.json()
            len_of_data = data['meta']['total'] # 43242
            j = 0
            total_data = data["data"]
            while data['links']['next'] != "":
                print('get:'+d)
                request_url = data['links']['next']
                response = requests.get(request_url)
                if response.status_code==200:
                    data = response.json()
                    total_data += data["data"]
                    j += 1
                else:
                    break
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
                    location_rpt = f'POINT({standardLon} {standardLat})' 
                else:
                    location_rpt = None
                x['standardRawLatitude'] = standardLat
                x['standardRawLongitude'] = standardLon
                x['raw_location_rpt'] = location_rpt
            x = x.rename(columns={'decimalLatitude':'verbatimRawLatitude','decimalLongitude':'verbatimRawLongitude'})
            final = final.merge(x,on='occurrenceID',how='left')
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
    # 串回taxon資訊 
    final = final.replace({nan: None})
    if len(match_taxon_id):
        final[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']] = final[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].replace({'': '-999999',None:'-999999'})
        final = final.merge(match_taxon_id, on=['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode'], how='left')
        final[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']] = final[['sourceScientificName','originalVernacularName','taxonUUID','taiCOLNameCode']].replace({'-999999': ''})
    final = final.replace({nan: None})
    final = final.drop(columns=['originalVernacularName','taxonUUID','taiCOLNameCode'])
    # final.to_csv(f'/tbia-volumes/solr/csvs/processed/{f}', index=False)
    # update datasetName key
    # recordType可能同時有兩個
    recs = final.recordType.unique()
    ds_name = df.datasetName.to_list()[0]
    for rec in recs:
        if DatasetKey.objects.filter(group=group,name=ds_name,record_type=rec).exists():
            # 更新
            dk = DatasetKey.objects.get(group=group,name=ds_name,record_type=rec)
            dk.deprecated = False
            dk.save()
        else:
            # 新建
            DatasetKey.objects.create(
                name = ds_name,
                record_type = rec,
                group = group,
            )
    # 建立未對應學名清單
    # * 自己的資料庫的occurrenceID
    # * TBIA入口網的occurrenceID
    # * 自己的資料庫的學名
    # * 是否有對應到taxonID（Yes/No）
    # * 對應到的taxonID
    # * taxonID的taxonRank
    # * taxonID的學名
    # * 比對狀態的log（標示對應到哪個步驟；NomenMatch比對狀態）
    match_log = final[['occurrenceID','id','sourceScientificName','taxonID','parentTaxonID','match_stage','stage_1','stage_2','stage_3','stage_4','stage_5','group','created','modified']]
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
    final = final.rename(columns={'taxon_name_id': 'scientificNameID'})
    final = df.drop(columns=['match_stage','stage_1','stage_2','stage_3','stage_4','stage_5','taiCOLNameCode','taxonUUID'],errors='ignore')
    final.to_csv(f'/tbia-volumes/solr/csvs/processed/{group}_{f}', index=False)



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


print('done!')

    # df_occ = final[final['recordType']=='occ']
    # df_col = final[final['recordType']=='col']

    # if len(df_occ):
    #     df_occ.to_csv(f'/tbia-volumes/solr/csvs/occ/{d}.csv', index=False)

    # if len(df_col):
    #     df_col.to_csv(f'/tbia-volumes/solr/csvs/col/{d}.csv', index=False)

