"""[V1-API-REMOVE] v1 API 專用：凍結的 v1 查詢條件與欄位清單（D29）

v1 API 讀凍結的 tbia_records_v1（RECORDS_V1_CORE，v1 欄位名稱），不跟著 v2 改。
內容複製自 2026-11-13 的 data/utils.py（create_search_query、download_cols 等），之後不再修改。
v1 API 停用（8.2）時刪除整個檔案。
"""
import re
import html
import json
import requests
import geopandas as gpd
from datetime import datetime

from conf.settings import SOLR_PREFIX, SOLR_TIMEOUT
from pages.templatetags.tags import process_text_variants
from data.utils import (
    _esc_q, _expand_composite_forms, build_keyword_reg, solr_quote, get_multi, get_tbia_dataset_id,
    merge_polygons, split_group_map, taxon_group_map_e, taxon_group_map_c, old_taxon_group_map_c,
    habitat_map, basis_map,
)


# ---- v1 子字串查詢 ----
LATIN_TXT_FIELDS_V1 = frozenset([
    'scientificName', 'sourceScientificName', 'originalScientificName',
    'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species',
    'synonyms', 'misapplied',
])
BIGRAM_FIELDS_V1 = frozenset([
    'datasetName', 'locality', 'recordedBy', 'resourceContacts',
    'sourceVernacularName', 'common_name_c', 'alternative_name_c',
])



NGRAM_FIELDS_V1 = frozenset([
    # 名稱（18）
    'scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied',
    'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species',
    'kingdom_c', 'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c',
    # 紀錄層（14）
    'sourceScientificName', 'sourceVernacularName', 'originalScientificName',
    'locality', 'recordedBy', 'datasetName', 'basisOfRecord', 'license',
    'rightsHolder', 'sensitiveCategory', 'eventDate', 'typeStatus', 'preservation',
    'resourceContacts',
])



def ngram_contains_query_v1(field, keyword):
    """依欄位型別建立查詢：
    - 拉丁欄位(_txt)：分詞 + 前綴，各詞皆須命中（整詞可在任何位置、支援前綴 typeahead）。
    - datasetName(_bi)：長度>=2 走 bigram，否則 unigram；含會意字 OR 展開。
    - 其餘(_ngram)：unigram 子字串；含會意字 OR 展開。
    單字元異體字一律由 Solr charfilter 折疊。"""
    kw = re.sub(' +', ' ', keyword).strip()
    if not kw:
        return f'{field}_ngram:""'
    if field in LATIN_TXT_FIELDS_V1:
        parts = [f'+{field}_txt:"{_esc_q(w)}"' for w in kw.split(' ') if w]
        return '(' + ' '.join(parts) + ')' if parts else f'{field}_txt:""'
    suffix = '_bi' if (field in BIGRAM_FIELDS_V1 and len(kw) >= 2) else '_ngram'
    clauses = [f'{field}{suffix}:"{_esc_q(form)}"' for form in _expand_composite_forms(kw)]
    return '(' + ' OR '.join(clauses) + ')'



def contains_clause_v1(field, keyword, keyword_reg):
    """單一欄位的 contains 查詢：有 _ngram 就走 ngram，否則沿用舊 regex（keyword_reg 已含變體展開）。"""
    if field in NGRAM_FIELDS_V1:
        return ngram_contains_query_v1(field, keyword)
    return f'{field}:/.*{keyword_reg}.*/'



# ---- v1 欄位清單 ----
NAME_SEARCH_COL_V1 = ['scientificName', 'common_name_c', 'alternative_name_c', 'synonyms', 'misapplied', 'sourceScientificName', 'sourceVernacularName', 'originalScientificName']


DOWNLOAD_COLS_V1 = [
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


DOWNLOAD_COLS_WITH_SENSITIVE_V1 = [
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

SENSITIVE_COLS_V1 = ['standardRawLatitude',
'standardRawLongitude',
'verbatimRawLatitude',
'verbatimRawLongitude',
'rawCounty',
'rawMunicipality',
]



# ---- v1 查詢條件 ----
def create_search_query_v1(req_dict, get_raw_map=False):

    query_list = []

    # 有無多媒體
    if has_image := req_dict.get('has_image'):
        if has_image == 'n':
            query_list += ['-associatedMedia:*']
        elif has_image in ['image', 'video', 'audio']:
            query_list += [f'associatedMediaType:{has_image}']
        # 兼容舊參數 y / true（一律視為有任何多媒體）
        elif has_image in ['y', 'true']:
            query_list += ['associatedMedia:*']

    # 是否為原生種
    if is_native := req_dict.get('is_native'):
        if is_native in ['y','true']:
            query_list += ['alien_type:native']
        elif is_native in ['n','false']:
            query_list += ['alien_type:(naturalized OR invasive OR cultured)']


    # 是否為保育類
    if is_protected := req_dict.get('is_protected'):
        if is_protected in ['y','true']:
            query_list += ['protected:*']
        elif is_protected in ['n','false']:
            query_list += ['-protected:*']


    record_type = req_dict.get('record_type')
    if record_type == 'col': # occurrence include occurrence + collection
        query_list += ['recordType:col']

    raw_vals = get_multi(req_dict, 'taxonGroup')
    bio_groups = []
    for v in raw_vals:
        if v in split_group_map:
            bio_groups.extend(split_group_map[v])
        elif v in taxon_group_map_e:
            bio_groups.append(v)
        elif v in taxon_group_map_c:
            bio_groups.append(taxon_group_map_c[v])
        elif v in old_taxon_group_map_c:
            bio_groups.append(old_taxon_group_map_c[v])
        elif v:
            bio_groups.append(v)

    if bio_groups:
        query_list += [f'bioGroup:({" OR ".join(solr_quote(g) for g in bio_groups)})']

    habitat_vals = [v for v in get_multi(req_dict, 'habitat') if v in habitat_map]
    if habitat_vals:
        query_list += [f'({" OR ".join([f"{v}:true" for v in habitat_vals])})']

    for i in ['recordedBy', 'resourceContacts', 'preservation']:
        if val := req_dict.get(i):
            if val != 'undefined':
                val = val.strip()
                val = html.unescape(val)
                keyword_reg = build_keyword_reg(val)
                keyword_reg = process_text_variants(keyword_reg)
                query_list += [contains_clause_v1(i, val, keyword_reg)]

    for i in ['taxonID', 'occurrenceID', 'catalogNumber', 'recordNumber']:
        if val := req_dict.get(i):
            query_list += [f'{i}:{solr_quote(val)}']

    # 這邊會不會有模糊化的問題
    if req_dict.get('current_grid_level') in ['grid_1','grid_10','grid_100','grid_5'] and req_dict.get('current_grid'):
        query_list += [f"{req_dict.get('current_grid_level')}:{solr_quote(req_dict.get('current_grid'))}"]

    # higherTaxa
    # 找到該分類群的階層 & 名稱
    # 要包含自己的階層
    if val := req_dict.get('higherTaxa'):
        response = requests.get(f'{SOLR_PREFIX}taxa/select', params={'q': f'id:{solr_quote(val)}'}, timeout=SOLR_TIMEOUT)
        if response.status_code == 200:
            resp = response.json()
            if data := resp['response']['docs']:
                data = data[0]
                higher_rank = data.get('taxonRank')
                higher_name = data.get('scientificName')
                query_list += [f'({higher_rank}:{solr_quote(higher_name)} OR taxonID:{solr_quote(val)})']

    if quantity := req_dict.get('organismQuantity'):
        try:
            float(quantity)  # 前端是 number 欄位；非數字忽略
            query_list += [f'standardOrganismQuantity:{solr_quote(quantity.strip())}']
        except ValueError:
            pass

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
            elif i == 'taxonRank' and val in ['sub','infraspecies']:
                query_list += [f'taxonRank:(subspecies OR nothosubspecies OR variety  OR subvariety  OR nothovariety OR form OR subform OR "special form" OR race OR stirp OR morph OR aberration)']
            else:
                query_list += [f'{i}:{solr_quote(val)}']

    # 下拉選單多選
    d_list = []
    for v in get_multi(req_dict, 'datasetName'):
        if d_id := get_tbia_dataset_id(v):
            d_list.append(d_id)

    # 這邊要改成tbiaDatasetID才對
    if d_list:
        query_list += [f'tbiaDatasetID:({" OR ".join(solr_quote(d) for d in d_list)})']

    r_list = []
    r_list = get_multi(req_dict, 'rightsHolder')
    
    if r_list:
        query_list += [f'rightsHolder:({" OR ".join(solr_quote(r) for r in r_list)})']

    l_list = []

    l_list = get_multi(req_dict, 'locality')
    if l_list:
        query_list += [f'locality:({" OR ".join(solr_quote(l) for l in l_list)})']

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
            query_list += [f'county:{solr_quote(county)} OR rawCounty:{solr_quote(county)}']
        else:
            query_list += [f'county:{solr_quote(county)}']

    if municipality := req_dict.get('municipality'):
        if get_raw_map:
            query_list += [f'municipality:{solr_quote(municipality)} OR rawMunicipality:{solr_quote(municipality)}']
        else:
            query_list += [f'municipality:{solr_quote(municipality)}']


    # 地圖框選
    # 資料皆為點位，使用 Intersects：落在邊線上的點也符合（共同規格要求包含邊界）
    if req_dict.get('geo_type') == 'map':
        if g_list := get_multi(req_dict, 'polygon'):
            try:
                mp = merge_polygons(g_list)
                if get_raw_map:
                    query_list += ['{!cache=false}location_rpt: "Intersects(%s)" OR raw_location_rpt: "Intersects(%s)" ' % (mp, mp)]
                else:
                    query_list += ['{!cache=false}location_rpt: "Intersects(%s)"' % mp]
            except:
                pass

    # 上傳polygon
    if req_dict.get('geo_type') == 'polygon':

        # geojson_id 會組成檔案路徑，只接受英數、底線、連字號，避免路徑穿越
        if (g_id := req_dict.get('geojson_id')) and re.fullmatch(r'[\w-]+', g_id):
            try:
                with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                    geojson = json.loads(j.read())
                    geo_df = gpd.GeoDataFrame.from_features(geojson)
                    g_list = []
                    for i in geo_df.to_wkt()['geometry']:
                        g_list += ['"Intersects(%s)"' % i]
                    if get_raw_map:
                        query_list += [ f"{{!cache=false}}location_rpt: ({' OR '.join(g_list)}) OR raw_location_rpt: ({' OR '.join(g_list)})" ]
                    else:
                        query_list += [ f"{{!cache=false}}location_rpt: ({' OR '.join(g_list)})" ]
            except:
                pass

    # 圓中心框選
    if req_dict.get('geo_type') == 'circle':
        if circle_radius := req_dict.get('circle_radius'):
            try:
                c_lat, c_lon = float(req_dict.get('center_lat')), float(req_dict.get('center_lon'))
                query_list += ['{!geofilt cache=false pt=%s,%s sfield=location_rpt d=%s}' %  (req_dict.get('center_lat').strip(), req_dict.get('center_lon').strip(), float(circle_radius))]
            except (TypeError, ValueError):
                pass

    # 學名相關
    if val := req_dict.get('name'):
        val = val.strip()
        # 去除重複空格
        val = re.sub(' +', ' ', val)
        # 去除頭尾空格
        val = val.strip()
        val = html.unescape(val)
        keyword_reg = build_keyword_reg(val)
        keyword_reg = process_text_variants(keyword_reg)
        col_list = [ contains_clause_v1(i, val, keyword_reg) for i in NAME_SEARCH_COL_V1 ]
        query_str = ' OR '.join( col_list )
        query_list += [ '(' + query_str + ')' ]

    # group (後台儀表板的query)
    if group := req_dict.get('group'):
        if group != 'total':
            query_list += [f'group:{solr_quote(group)}']

    # rights_holder (後台儀表板的query)
    if rights_holder := req_dict.get('rights_holder'):
        if rights_holder != 'total':
            query_list += ['rightsHolder:{}'.format(rights_holder)]

    return query_list
