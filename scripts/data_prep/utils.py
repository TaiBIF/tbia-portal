# 2023-02-10
# RUN in web container
# script for TBN API version 2.5

import numpy as np
import bisect
from dateutil import parser
from datetime import datetime, timedelta
import requests

# x: longtitude, y: latitude
# grid = [0.01, 0.05, 0.1, 1]

def convert_grid_to_coor(grid_x, grid_y, grid):
    list_x = np.arange(-180, 180, grid)
    list_y = np.arange(-90, 90, grid)
    center_x = (list_x[grid_x] + list_x[grid_x+1])/2
    center_y = (list_y[grid_y] + list_y[grid_y+1])/2
    return center_x, center_y

def convert_coor_to_grid(x, y, grid):
    list_x = np.arange(-180, 180, grid)
    list_y = np.arange(-90, 90, grid)
    grid_x = bisect.bisect(list_x, x)-1
    grid_y = bisect.bisect(list_y, y)-1
    return grid_x, grid_y

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


# 如果不是TBN的學名比對

def match_name(matching_name,sci_name,original_name,original_taxonuuid,is_parent):
    request_url = f"http://host.docker.internal:8080/api.php?names={matching_name.replace(' ','+')}&format=json&source=taicol"
    response = requests.get(request_url)
    if response.status_code == 200:
        result = response.json()
        if result['data'][0][0]: # 因為一次只比對到一個，所以只要取第一個search term
            # 排除地位為誤用的taxon，因為代表該名字不該指涉到此taxon
            filtered_rs = [rs for rs in result['data'][0][0]['results'] if rs['name_status'] != 'misapplied']
            filtered_rss = []
            if len(filtered_rs):
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
                # 若有上階層資訊，加上比對上階層                    
                if has_parent:
                    has_nm_parent = False
                    for frs in filtered_rs:
                        if t_rank in ['種','種下階層']: # 直接比對family
                            if frs.get('family'):
                                if frs.get('family') == t_family:
                                    filtered_rss.append(frs)
                                    has_nm_parent = True
                                    # 本來就沒有上階層的話就不管
                        elif t_rank in ['亞綱','總目','目','亞目','總科','科','亞科','屬','亞屬']: # 
                            if frs.get('family') or frs.get('class'):
                                if frs.get('family') == t_family or frs.get('class') == t_class:
                                    filtered_rss.append(frs)
                                    has_nm_parent = True
                        else:
                            has_nm_parent = False # TODO 這邊先當成沒有nm上階層，直接比對學名
                        # elif t_rank in ['綱','總綱','亞門']: # 還要再往上抓到門
                        # elif t_rank in ['亞界','總門','門']: #  還要再往上抓到界
                    # 如果有任何有nm上階層 且filtered_rss > 0 就代表有上階層比對成功的結果
                    if has_nm_parent:
                        if len(filtered_rss) == 1:
                            if is_parent:
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'parentTaxonID'] = filtered_rss[0]['accepted_namecode']
                            else:
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rss[0]['accepted_namecode']
                    else:
                        # 如果沒有任何nm上階層的結果，則直接用filtered_rs
                        if len(filtered_rs) == 1:
                            if is_parent:
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'parentTaxonID'] = filtered_rs[0]['accepted_namecode']
                            else:
                                sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']
                # 若沒有上階層資訊，就直接取比對結果
                else:
                    if len(filtered_rs) == 1:
                        if is_parent:
                            sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'parentTaxonID'] = filtered_rs[0]['accepted_namecode']
                        else:
                            sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rs[0]['accepted_namecode']


def match_namecode(matching_namecode,sci_name,original_name,original_taxonuuid):
    try:
        matching_namecode = str(int(matching_namecode))
    except:
        pass
    if Namecode.objects.filter(namecode=matching_namecode).exists():
        # 基本上只會對到一個
        filtered_rs = []
        taxon_name_id = Namecode.objects.get(namecode=matching_namecode).taxon_name_id
        if Taxon.objects.filter(scientificNameID=taxon_name_id).exists():
            matched_taxon = Taxon.objects.filter(scientificNameID=taxon_name_id).values()
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
            # 若有上階層資訊，加上比對上階層                    
            if has_parent:
                has_taxon_parent = False
                for frs in matched_taxon:
                    if t_rank in ['種','種下階層']: # 直接比對family
                        if frs.get('family'):
                            if frs.get('family') == t_family:
                                filtered_rs.append(frs)
                                has_taxon_parent = True
                                # 本來就沒有上階層的話就不管
                    elif t_rank in ['亞綱','總目','目','亞目','總科','科','亞科','屬','亞屬']: # 
                        if frs.get('family') or frs.get('class'):
                            if frs.get('family') == t_family or frs.get('class') == t_class:
                                filtered_rs.append(frs)
                                has_taxon_parent = True
                    else:
                        has_taxon_parent = False # TODO 這邊先當成沒有nm上階層，直接比對學名
                    # elif t_rank in ['綱','總綱','亞門']: # 還要再往上抓到門
                    # elif t_rank in ['亞界','總門','門']: #  還要再往上抓到界
                # 如果有任何有nm上階層 且filtered_rss > 0 就代表有上階層比對成功的結果
                if has_taxon_parent:
                    if len(filtered_rs) == 1:
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = filtered_rs[0]['taxonID']
                else:
                    # 如果沒有任何nm上階層的結果，則直接用filtered_rs
                    if len(matched_taxon) == 1:
                        sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = matched_taxon[0]['taxonID']
            # 若沒有上階層資訊，就直接取比對結果
            else:
                if len(matched_taxon) == 1:
                    sci_names.loc[((sci_names.scientificName==sci_name)&(sci_names.originalVernacularName==original_name)),'taxonID'] = matched_taxon[0]['taxonID']
