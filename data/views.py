from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT
from utils.solr_query import SolrQuery, col_facets, occ_facets, SOLR_PREFIX
from pages.models import Resource, News
from django.db.models import Q
from data.utils import *
from data.taicol import taicol
import pandas as pd
import numpy as np
from django.http import (
    request,
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponse,
)
import json
from pages.templatetags.tags import highlight
import math
import time
import requests
import geopandas as gpd
import shapely.wkt as wkt
from shapely.geometry import MultiPolygon
from datetime import datetime, timedelta
import re
from bson.objectid import ObjectId
import subprocess
import os
from conf import settings
import threading
from manager.models import SearchQuery, User
from pages.models import Notification
from urllib import parse
from manager.views import send_notification
from django.utils import timezone

basis_dict = { 'HumanObservation':'人為觀察', 'PreservedSpecimen':'保存標本', 'FossilSpecimen':'化石標本', 
                'LivingSpecimen':'活體標本', 'MaterialSample':'組織樣本',
                'MachineObservation':'機器觀測', 'Occurrence':'出現紀錄'}


def send_sensitive_request(request):
    if request.method == 'POST':
        req_dict = request.POST
        user_id = request.user.id
        query_string = req_dict.urlencode()
        download_id = f"{user_id}_{str(ObjectId())}"
        # TODO 這邊要改成敏感資料自己的table
        # sq = SearchQuery.objects.create(
        #     user = User.objects.filter(id=user_id).first(),
        #     query = query_string,
        #     status = 'pending',
        #     type = 'taxon',
        #     query_id = download_id.split('_')[-1]
        # )
        # 先取得筆數，export to csv
        query_list = []

        record_type = req_dict.get('record_type')
        if record_type == 'col': # occurrence include occurrence + collection
            query_list += ['recordType:col']

        for i in ['rightsHolder', 'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'resourceContacts',
                    'taxonID', 'preservation']:
            if val := req_dict.get(i):
                if val != 'undefined':
                    val = val.strip()
                    keyword_reg = ''
                    for j in val:
                        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                    if i in ['rightsHolder', 'locality', 'recordedBy', 'datasetName', 'resourceContacts', 'preservation']:
                        keyword_reg = get_variants(keyword_reg)
                    query_list += [f'{i}:/.*{keyword_reg}.*/']
        
        if quantity := req_dict.get('organismQuantity'):
            query_list += [f'standardOrganismQuantity: {quantity}']

        for i in ['sensitiveCategory', 'taxonRank', 'typeStatus']: # 下拉選單
            if val := req_dict.get(i):
                if i == 'sensitiveCategory' and val == '無':
                    query_list += [f'-(-{i}:{val} {i}:*)']
                else:
                    query_list += [f'{i}:{val}']

        if req_dict.get('start_date') and req_dict.get('end_date'):
            try: 
                start_date = datetime.strptime(req_dict.get('start_date'), '%Y-%m-%d').isoformat() + 'Z'
                end_date = datetime.strptime(req_dict.get('end_date'), '%Y-%m-%d')
                end_date = end_date.isoformat() + 'Z'
                end_date = end_date.replace('00:00:00','23:59:59')
                query_list += [f'standardDate:[{start_date} TO {end_date}]']
            except:
                pass

        geojson = {}
        geojson['features'] = ''

        if g_str := req_dict.get('geojson'):
            geojson = json.loads(g_str)
        elif g_id := req_dict.get('geojson_id'):
            try:
                with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                    geojson = json.loads(j.read())
            except:
                pass

        if geojson['features']:
            if circle_radius := req_dict.get('circle_radius'):
                query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (geojson['features'][0]['geometry']['coordinates'][1], geojson['features'][0]['geometry']['coordinates'][0], int(circle_radius))]
            else:
                geo_df = gpd.GeoDataFrame.from_features(geojson)
                g_list = []
                for i in geo_df.to_wkt()['geometry']:
                    if str(i).startswith('POLYGON'):
                        g_list += [i]
                try:
                    mp = MultiPolygon(map(wkt.loads, g_list))
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
                except:
                    pass
        
        if val := req_dict.get('name'):
            val = val.strip()
            keyword_reg = ''
            for j in val:
                keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
            keyword_reg = get_variants(keyword_reg)
            col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
            query_str = ' OR '.join( col_list )
            query_list += [ '(' + query_str + ')' ]
        # 如果有其他條件才進行搜尋，否則回傳空值
        if query_list and query_list != ['recordType:col']:

            query = { "query": "*:*",
                    "offset": 0,
                    "limit": 0,
                    "filter": query_list,
                    "sort":  "scientificName asc",
                    "facet": {
                        "scientificName": {
                            "type": "terms",
                            "field": "scientificName",
                            "limit": -1,
                            "facet": {
                                "taxonID": {
                                "type": "terms",
                                "field": "taxonID",
                                "limit": -1
                                }
                            }

                            }
                        }
                    }
            response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
            data = response.json()['facets']['scientificName']['buckets']
            df = pd.DataFrame(columns=['taxonID','scientificName'])
            for d in data:
                # print(d)
                df = df.append({'taxonID':d['taxonID']['buckets'][0]['val'] ,'scientificName':d['val'] },ignore_index=True)
            csv_folder = os.path.join(settings.MEDIA_ROOT, 'species_list')
            csv_file_path = os.path.join(csv_folder, f'{download_id}_taxon.csv')
            # print(csv_file_path)
            df.to_csv(csv_file_path, index=None)
            # return df

            # TODO 儲存到下載統計
            # sq.status = 'pass'
            # sq.modified = timezone.now()
            # sq.save()

            # TODO 寄送通知給相關的單位
            # nn = Notification.objects.create(
            #     type = 0,
            #     content = sq.id,
            #     user_id = user_id
            # )
            # content = nn.get_type_display().replace('0000', str(nn.content))
            # send_notification([user_id],content,'下載名錄已完成通知')




def save_geojson(request):
    if request.method == 'POST':
        geojson = json.loads(request.POST.get('geojson_text'))
        oid = str(ObjectId())
        with open(f'/tbia-volumes/media/geojson/{oid}.json', 'w') as f:
            json.dump(geojson, f)
        return JsonResponse({"geojson_id": oid}, safe=False)


def send_download_request(request):
    if request.method == 'POST':
        # print(request.POST.get('taxon'))
        if request.POST.get('from_full'):
            task = threading.Thread(target=generate_download_csv_full, args=(request.POST, request.user.id))
            task.start()
        elif request.POST.get('taxon'):
            task = threading.Thread(target=generate_species_csv, args=(request.POST, request.user.id))
            task.start()
        else:
            task = threading.Thread(target=generate_download_csv, args=(request.POST, request.user.id))
            task.start()
        return JsonResponse({"status": 'success'}, safe=False)


# 這邊是for條件搜尋 全站搜尋要先另外寫
def generate_download_csv(req_dict,user_id):
    query_string = req_dict.urlencode()
    download_id = f"{user_id}_{str(ObjectId())}"
    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'record',
        query_id = download_id.split('_')[-1]
    )
    
    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
        fl_cols = download_cols + sensitive_cols
    else:
        fl_cols = download_cols

    # 先取得筆數，export to csv
    query_list = []

    record_type = req_dict.get('record_type')
    if record_type == 'col': # occurrence include occurrence + collection
        query_list += ['recordType:col']

    for i in ['rightsHolder', 'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'resourceContacts',
                'taxonID', 'preservation']:
        if val := req_dict.get(i):
            if val != 'undefined':
                val = val.strip()
                keyword_reg = ''
                for j in val:
                    keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                if i in ['rightsHolder', 'locality', 'recordedBy', 'datasetName', 'resourceContacts', 'preservation']:
                    keyword_reg = get_variants(keyword_reg)
                query_list += [f'{i}:/.*{keyword_reg}.*/']
    
    if quantity := req_dict.get('organismQuantity'):
        query_list += [f'standardOrganismQuantity: {quantity}']

    for i in ['sensitiveCategory', 'taxonRank', 'typeStatus']: # 下拉選單
        if val := req_dict.get(i):
            if i == 'sensitiveCategory' and val == '無':
                query_list += [f'-(-{i}:{val} {i}:*)']
            else:
                query_list += [f'{i}:{val}']

    if req_dict.get('start_date') and req_dict.get('end_date'):
        try: 
            start_date = datetime.strptime(req_dict.get('start_date'), '%Y-%m-%d').isoformat() + 'Z'
            end_date = datetime.strptime(req_dict.get('end_date'), '%Y-%m-%d')
            end_date = end_date.isoformat() + 'Z'
            end_date = end_date.replace('00:00:00','23:59:59')
            query_list += [f'standardDate:[{start_date} TO {end_date}]']
        except:
            pass

    geojson = {}
    geojson['features'] = ''

    if g_str := req_dict.get('geojson'):
        geojson = json.loads(g_str)
    elif g_id := req_dict.get('geojson_id'):
        try:
            with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                geojson = json.loads(j.read())
        except:
            pass

    if geojson['features']:
        if circle_radius := req_dict.get('circle_radius'):
            query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (geojson['features'][0]['geometry']['coordinates'][1], geojson['features'][0]['geometry']['coordinates'][0], int(circle_radius))]
        else:
            geo_df = gpd.GeoDataFrame.from_features(geojson)
            g_list = []
            for i in geo_df.to_wkt()['geometry']:
                if str(i).startswith('POLYGON'):
                    g_list += [i]
            try:
                mp = MultiPolygon(map(wkt.loads, g_list))
                query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
            except:
                pass
    
    if val := req_dict.get('name'):
        val = val.strip()
        keyword_reg = ''
        for j in val:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
        query_str = ' OR '.join( col_list )
        query_list += [ '(' + query_str + ')' ]
    # 如果有其他條件才進行搜尋，否則回傳空值
    if query_list and query_list != ['recordType:col']:

        query = { "query": "*:*",
                "offset": 0,
                "limit": req_dict.get('total_count'),
                "filter": query_list,
                "sort":  "scientificName asc",
                "fields": fl_cols
                }

        csv_folder = os.path.join(settings.MEDIA_ROOT, 'download')
        csv_file_path = os.path.join(csv_folder, f'{download_id}.csv')
        solr_url = f"{SOLR_PREFIX}tbia_records/select?wt=csv"
        commands = f"curl -X POST {solr_url} -d '{json.dumps(query)}' > {csv_file_path} "
        process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # 儲存到下載統計
        sq.status = 'pass'
        sq.modified = timezone.now()
        sq.save()

        # 寄送通知
        nn = Notification.objects.create(
            type = 1,
            content = sq.id,
            user_id = user_id
        )
        content = nn.get_type_display().replace('0000', str(nn.content))
        send_notification([user_id],content,'下載資料已完成通知')
# facet.pivot=taxonID,scientificName


def generate_species_csv(req_dict,user_id):
    query_string = req_dict.urlencode()
    download_id = f"{user_id}_{str(ObjectId())}"
    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'taxon',
        query_id = download_id.split('_')[-1]
    )
    # 先取得筆數，export to csv
    query_list = []

    record_type = req_dict.get('record_type')
    if record_type == 'col': # occurrence include occurrence + collection
        query_list += ['recordType:col']

    for i in ['rightsHolder', 'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'resourceContacts',
                'taxonID', 'preservation']:
        if val := req_dict.get(i):
            if val != 'undefined':
                val = val.strip()
                keyword_reg = ''
                for j in val:
                    keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                if i in ['rightsHolder', 'locality', 'recordedBy', 'datasetName', 'resourceContacts', 'preservation']:
                    keyword_reg = get_variants(keyword_reg)
                query_list += [f'{i}:/.*{keyword_reg}.*/']
    
    if quantity := req_dict.get('organismQuantity'):
        query_list += [f'standardOrganismQuantity: {quantity}']

    for i in ['sensitiveCategory', 'taxonRank', 'typeStatus']: # 下拉選單
        if val := req_dict.get(i):
            if i == 'sensitiveCategory' and val == '無':
                query_list += [f'-(-{i}:{val} {i}:*)']
            else:
                query_list += [f'{i}:{val}']

    if req_dict.get('start_date') and req_dict.get('end_date'):
        try: 
            start_date = datetime.strptime(req_dict.get('start_date'), '%Y-%m-%d').isoformat() + 'Z'
            end_date = datetime.strptime(req_dict.get('end_date'), '%Y-%m-%d')
            end_date = end_date.isoformat() + 'Z'
            end_date = end_date.replace('00:00:00','23:59:59')
            query_list += [f'standardDate:[{start_date} TO {end_date}]']
        except:
            pass

    geojson = {}
    geojson['features'] = ''

    if g_str := req_dict.get('geojson'):
        geojson = json.loads(g_str)
    elif g_id := req_dict.get('geojson_id'):
        try:
            with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                geojson = json.loads(j.read())
        except:
            pass

    if geojson['features']:
        if circle_radius := req_dict.get('circle_radius'):
            query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (geojson['features'][0]['geometry']['coordinates'][1], geojson['features'][0]['geometry']['coordinates'][0], int(circle_radius))]
        else:
            geo_df = gpd.GeoDataFrame.from_features(geojson)
            g_list = []
            for i in geo_df.to_wkt()['geometry']:
                if str(i).startswith('POLYGON'):
                    g_list += [i]
            try:
                mp = MultiPolygon(map(wkt.loads, g_list))
                query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
            except:
                pass
    
    if val := req_dict.get('name'):
        val = val.strip()
        keyword_reg = ''
        for j in val:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
        query_str = ' OR '.join( col_list )
        query_list += [ '(' + query_str + ')' ]
    # 如果有其他條件才進行搜尋，否則回傳空值
    if query_list and query_list != ['recordType:col']:

        query = { "query": "*:*",
                "offset": 0,
                "limit": 0,
                "filter": query_list,
                "sort":  "scientificName asc",
                "facet": {
                    "scientificName": {
                        "type": "terms",
                        "field": "scientificName",
                        "limit": -1,
                        "facet": {
                            "taxonID": {
                            "type": "terms",
                            "field": "taxonID",
                            "limit": -1
                            }
                        }

                        }
                    }
                }
        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        data = response.json()['facets']['scientificName']['buckets']
        df = pd.DataFrame(columns=['taxonID','scientificName'])
        for d in data:
            # print(d)
            df = df.append({'taxonID':d['taxonID']['buckets'][0]['val'] ,'scientificName':d['val'] },ignore_index=True)
        csv_folder = os.path.join(settings.MEDIA_ROOT, 'species_list')
        csv_file_path = os.path.join(csv_folder, f'{download_id}_taxon.csv')
        # print(csv_file_path)
        df.to_csv(csv_file_path, index=None)
        # return df

        # 儲存到下載統計
        sq.status = 'pass'
        sq.modified = timezone.now()
        sq.save()

        # 寄送通知
        nn = Notification.objects.create(
            type = 0,
            content = sq.id,
            user_id = user_id
        )
        content = nn.get_type_display().replace('0000', str(nn.content))
        send_notification([user_id],content,'下載名錄已完成通知')


    # return csv file

def generate_download_csv_full(req_dict,user_id):
    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
        fl_cols = download_cols + sensitive_cols
    else:
        fl_cols = download_cols

    query_string = req_dict.urlencode()
    # req_dict_query = req_dict.get('search_str')
    req_dict_query = dict(parse.parse_qsl(req_dict.get('search_str')))
    download_id = f"{user_id}_{str(ObjectId())}"
    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'record',
        query_id = download_id.split('_')[-1]
    )

    keyword = req_dict_query.get('keyword', '')
    key = req_dict_query.get('key', '')
    value = req_dict_query.get('value', '')
    record_type = req_dict_query.get('record_type', 'occ')
    scientific_name = req_dict_query.get('scientificName', '')
    # limit = int(request.POST.get('limit', -1))
    # page = int(request.POST.get('page', 1))
    # only facet selected field
    if record_type == 'col':
        map_dict = map_collection
        query_list = ['recordType:col']
        # title = '自然史典藏'
    else:
        map_dict = map_occurrence
        # core = 'tbia_occurrence'
        query_list = []
        # title = '物種出現紀錄'

    # key = get_key(key, map_dict)
    # search_str = f'keyword={keyword}&{key}={value}&record_type={record_type}'
    # if 'scientificName' not in search_str:
    #     search_str += f'&scientificName={scientific_name}'

    keyword_reg = ''
    for j in keyword:
        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
    keyword_reg = get_variants(keyword_reg)
    q = f'{key}:/.*{keyword_reg}.*/' 

    # offset = (page-1)*10
    # solr = SolrQuery('tbia_records')
    query_list += [f'{key}:{value}',f'scientificName:{scientific_name}']
    # req = solr.request(query_list)
    # docs = pd.DataFrame(req['solr_response']['response']['docs'])

    # download_id = 'test'
    if query_list:

        query = { "query": q,
                "offset": 0,
                "limit": req_dict.get('total_count'),
                "filter": query_list,
                "sort":  "scientificName asc",
                "fields": fl_cols,
                }

        csv_folder = os.path.join(settings.MEDIA_ROOT, 'download')
        csv_file_path = os.path.join(csv_folder, f'{download_id}.csv')
        solr_url = f"{SOLR_PREFIX}tbia_records/select?wt=csv"
        commands = f"curl -X POST {solr_url} -d '{json.dumps(query)}' > {csv_file_path} "

        process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # return HttpResponse(json.dumps(response), content_type='application/json')

        # 儲存到下載統計
        sq.status = 'pass'
        sq.modified = timezone.now()
        sq.save()

        # 寄送通知
        nn = Notification.objects.create(
            type = 1,
            content = sq.id,
            user_id = user_id
        )
        content = nn.get_type_display().replace('0000', str(nn.content))
        send_notification([user_id],content,'下載資料已完成通知')



def search_full(request):
    keyword = request.GET.get('keyword', '')

    if keyword:
        keyword = keyword.strip()
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

        query = {
            "query": '',
            "filter": ['recordType:col'],
            "limit": 0,
            "facet": {},
            "sort":  "scientificName asc"
            }

        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)

        # collection
        facet_list = col_facets
        q = ''
        for i in facet_list['facet']:
            q += f'{i}:/.*{keyword_reg}.*/ OR ' 
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/', 'filter': 'recordType:col'}})
        query.update(facet_list)
        q = q[:-4]
        query.update({'query': q})

        # s = time.time()
        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        # print('get collection', time.time() - s)
        facets = response.json()['facets']
        facets.pop('count', None)

        c_collection = response.json()['response']['numFound']
        # c_collection = 0
        collection_rows = []
        result = []
        for i in facets:
            x = facets[i]
            if (i != 'eventDate') or (enable_query_date and i == 'eventDate'): 
                if x['buckets']:
                    collection_rows.append({
                        'title': map_collection[i],
                        'total_count': sum(item['count'] for item in x['buckets']),
                        'key': i
                    })
                for k in x['buckets']:
                    bucket = k['taxonID']['buckets']
                    result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
            else:
                if x['buckets']:
                    c_collection -= sum(item['count'] for item in x['buckets'])
        col_result_df = pd.DataFrame(result)
        col_result_df_duplicated = col_result_df[col_result_df.duplicated(['val','count'])]
        if len(col_result_df_duplicated):
            col_remove_index = col_result_df_duplicated[col_result_df_duplicated.matched_col.isin(dup_col)].index
            col_result_df = col_result_df.loc[~col_result_df.index.isin(col_remove_index)]
        if len(col_result_df):
            col_card_len = len(col_result_df)
            col_result_df = col_result_df[:9]
            col_result_df = pd.merge(col_result_df,taicol,left_on='val',right_on='taxonID')
            col_result_df['val'] = col_result_df['formatted_name']
            col_result_df['matched_col'] = col_result_df['matched_col'].apply(lambda x: map_collection[x])
            col_result_df = col_result_df.replace({np.nan: ''})
        else:
            col_card_len = 0
        # occurrence
        facet_list = occ_facets
        q = ''
        for i in facet_list['facet']:
            q += f'{i}:/.*{keyword_reg}.*/ OR ' 
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.pop('filter', None)
        query.update(facet_list)
        q = q[:-4]
        query.update({'query': q})

        # s = time.time()
        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        # print('get occurrence', time.time() - s)
        facets = response.json()['facets']
        facets.pop('count', None)
        
        c_occurrence = response.json()['response']['numFound']
        occurrence_rows = []
        result = []
        for i in facets:
            x = facets[i]
            if (i!='eventDate') or (enable_query_date and i == 'eventDate'): 
                if x['buckets']:
                    total_count =  sum(item['count'] for item in x['buckets'])
                    occurrence_rows.append({
                        'title': map_occurrence[i],
                        'total_count': total_count,
                        'key': i
                    })
                for k in x['buckets']:
                    bucket = k['taxonID']['buckets']
                    result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
            else:
                if x['buckets']:
                    c_occurrence -= sum(item['count'] for item in x['buckets'])

        occ_result_df = pd.DataFrame(result)
        occ_result_df_duplicated = occ_result_df[occ_result_df.duplicated(['val','count'])]
        if len(occ_result_df_duplicated):
            occ_remove_index = occ_result_df_duplicated[occ_result_df_duplicated.matched_col.isin(dup_col)].index
            occ_result_df = occ_result_df.loc[~occ_result_df.index.isin(occ_remove_index)]        
        if len(occ_result_df):
            occ_card_len = len(occ_result_df)
            occ_result_df = occ_result_df[:9]
            occ_result_df = pd.merge(occ_result_df,taicol,left_on='val',right_on='taxonID')
            occ_result_df['val'] = occ_result_df['formatted_name']
            occ_result_df['matched_col'] = occ_result_df['matched_col'].apply(lambda x: map_occurrence[x])
            occ_result_df = occ_result_df.replace({np.nan: ''})
        else:
            occ_card_len = 0

        # news
        news = News.objects.filter(type='news').filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
        c_news = news.count()
        news_rows = []
        for x in news.all()[:6]:
            news_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        event = News.objects.filter(type='event').filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
        c_event = event.count()
        event_rows = []
        for x in event.all()[:6]:
            event_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        project = News.objects.filter(type='project').filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
        c_project = project.count()
        project_rows = []
        for x in project.all()[:6]:
            project_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        # resource
        resource = Resource.objects.filter(title__regex=keyword_reg)
        c_resource = resource.count()
        resource_rows = []
        for x in resource.all()[:6]:
            resource_rows.append({
                'title': x.title,
                'extension': x.extension,
                'url': x.url,
                'date': x.modified.strftime("%Y.%m.%d")
            })
        
        occurrence_more = True if occ_card_len > 9 else False
        collection_more = True if col_card_len > 9 else False

        response = {
            'keyword': keyword,
            'occurrence': {'rows': occurrence_rows, 'count': c_occurrence, 'card': occ_result_df.to_dict('records'), 'more': occurrence_more},
            'collection': {'rows': collection_rows, 'count': c_collection, 'card': col_result_df.to_dict('records'), 'more': collection_more},
            'news': {'rows': news_rows, 'count': c_news},
            'event': {'rows': event_rows, 'count': c_event},
            'project': {'rows': project_rows, 'count': c_project},
            'resource': {'rows': resource_rows, 'count': c_resource},
            }
    else:
        response = {
            'keyword': keyword,
            'occurrence': {'count': 0},
            'collection': {'count': 0},
            'news': {'count': 0},
            'event': {'count': 0},
            'project': {'count': 0},
            'resource': {'count': 0},
        }

    return render(request, 'pages/search_full.html', response)


def get_records(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        key = request.POST.get('key', '')
        value = request.POST.get('value', '')
        record_type = request.POST.get('record_type', '')
        scientific_name = request.POST.get('scientific_name', '')
        limit = int(request.POST.get('limit', -1))
        page = int(request.POST.get('page', 1))
        # only facet selected field
        if record_type == 'col':
            map_dict = map_collection
            query_list = [('fq','recordType:col')]
            title = '自然史典藏'
        else:
            map_dict = map_occurrence
            # core = 'tbia_occurrence'
            query_list = []
            title = '物種出現紀錄'

        key = get_key(key, map_dict)
        search_str = f'keyword={keyword}&key={key}&value={value}&record_type={record_type}'
        if 'scientificName' not in search_str:
            search_str += f'&scientificName={scientific_name}'

        # if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isdigit() for i in keyword ]):
        #     keyword_str = f'"{keyword}"'
        # else:
        #     keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isdigit() else f"{keyword}"
        #     keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isdigit() else ""
        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        q = f'{key}:/.*{keyword_reg}.*/' 

        offset = (page-1)*10
        solr = SolrQuery('tbia_records')
        query_list += [('q', q),(key,value),('scientificName',scientific_name), ('rows', 10), ('offset', offset), ('sort', 'scientificName asc')]
        req = solr.request(query_list)
        docs = pd.DataFrame(req['solr_response']['response']['docs'])

        # print(docs.keys())
        docs = docs.replace({np.nan: ''})
        docs = docs.replace({'nan': ''})

        # docs['scientificName'] = docs['formatted_name']

        for i in docs.index:
            row = docs.iloc[i]
            if f_name := row.get('formatted_name'):
                docs.loc[i , 'scientificName'] = f_name
            # date
            if date := row.get('standardDate'):
                # date = date[0].replace('T', ' ').replace('Z','')
                docs.loc[i , 'date'] = date[0].replace('T', ' ').replace('Z','')
            else:
                if row.get('eventDate'):
                    docs.loc[i , 'date'] = '---<br><small style="color: silver">[原始紀錄日期]' + docs.loc[i , 'eventDate'] + '</small>'
            # 經緯度
            if lat := row.get('standardLatitude'):
                docs.loc[i , 'lat'] = lat[0]
            else:
                if row.get('verbatimLatitude'):
                    docs.loc[i , 'lat'] = '---<br><small style="color: silver">[原始紀錄緯度]' + docs.loc[i , 'verbatimLatitude'] + '</small>'

            if lon := row.get('standardLongitude'):
                docs.loc[i , 'lon'] = lon[0]
            else:
                if row.get('verbatimLongitude'):
                    docs.loc[i , 'lon'] = '---<br><small style="color: silver">[原始紀錄經度]' + docs.loc[i , 'verbatimLongitude'] + '</small>'
            # 數量
            if quantity := row.get('standardOrganismQuantity'):
                docs.loc[i , 'quantity'] = int(quantity[0])
            else:
                if row.get('organismQuantity'):
                    docs.loc[i , 'quantity'] = '---<br><small style="color: silver">[原始紀錄數量]' + docs.loc[i , 'organismQuantity'] + '</small>'

        docs = docs.replace({np.nan: ''})
        docs = docs.replace({'nan': ''})


        docs = docs.to_dict('records')

        current_page = offset / 10 + 1
        total_page = math.ceil(limit / 10)
        page_list = get_page_list(current_page, total_page)

        if key in ['common_name_c','scientificName', 'rightsHolder']:
            selected_col = ['common_name_c','scientificName', 'rightsHolder']
        else:
            selected_col = [key,'common_name_c','scientificName','rightsHolder']

        response = {
            'title': title,
            'rows' : docs,
            'current_page' : current_page,
            'total_page' : total_page,
            'selected_col': selected_col,
            'map_dict': map_dict,
            'page_list': page_list,
            'search_str': search_str
        }

        return HttpResponse(json.dumps(response), content_type='application/json')



def get_more_docs(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        keyword_reg = ''
        for j in keyword:    
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)

        doc_type = request.POST.get('doc_type', '')
        offset = request.POST.get('offset', '')
        if offset:
            offset = int(offset)

        rows = []
        if doc_type == 'resource':
            resource = Resource.objects.filter(title__regex=keyword_reg)
            for x in resource.all()[offset:offset+6]:
                rows.append({
                    'title': highlight(x.title,keyword),
                    'extension': x.extension,
                    'url': x.url,
                    'date': x.modified.strftime("%Y.%m.%d")
                })
            has_more = True if resource.all()[offset+6:].count() > 0 else False
        else:
            news = News.objects.filter(type=doc_type).filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
            for x in news.all()[offset:offset+6]:
                rows.append({
                    'title': highlight(x.title,keyword),
                    'content': highlight(x.content,keyword),
                    'id': x.id
                })
            has_more = True if news.all()[offset+6:].count() > 0 else False

        response = {
            'rows': rows,
            'has_more': has_more
        }

        return HttpResponse(json.dumps(response), content_type='application/json')



def get_focus_cards(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        record_type = request.POST.get('record_type', '')
        key = request.POST.get('key', '')
        
        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        q = f'{key}:/.*{keyword_reg}.*/' 
        
        if record_type == 'col':
            facet_list = {'facet': {k: v for k, v in col_facets['facet'].items() if k == key} }
            map_dict = map_collection
            query = {
                "query": q,
                "limit": 0,
                "filter": ['recordType:col'],
                "facet": {},
                "sort": "scientificName asc"
                } 
            # core = 'tbia_collection'
            title_prefix = '自然史典藏 > '
        else:
            facet_list = {'facet': {k: v for k, v in occ_facets['facet'].items() if k == key} }
            map_dict = map_occurrence
            # core = 'tbia_occurrence'
            title_prefix = '物種出現紀錄 > '
            query = {
                "query": q,
                "limit": 0,
                "facet": {},
                "sort":  "scientificName asc"
                } 

        # keyword_reg = ''
        # for j in keyword:
        #     keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else j
        for i in facet_list['facet']:
            if record_type == 'col':
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/', 'filter': 'recordType:col'}})
            else:
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)


        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)

        x = facets[key]
        total_count =  sum(item['count'] for item in x['buckets'])
        result = []
        for k in x['buckets']:
            bucket = k['taxonID']['buckets']
            if key == 'eventDate':
                if f_date := convert_date(k['val']):
                    f_date = f_date.strftime('%Y-%m-%d %H:%M:%S')
                    result += [dict(item, **{'matched_value':f_date, 'matched_col': key}) for item in bucket]
            else:
                result += [dict(item, **{'matched_value':k['val'], 'matched_col': key}) for item in bucket]
        result_df = pd.DataFrame(result)
        if len(result_df):
            # result_df = pd.merge(result_df,taicol,left_on='val',right_on='name')
            card_len = len(result_df)
            result_df = result_df[:9]
            result_df = pd.merge(result_df,taicol,left_on='val',right_on='taxonID')
            result_df['val'] = result_df['formatted_name']
            result_df['matched_value_ori'] = result_df['matched_value']
            result_df = result_df.replace({np.nan: ''})
            # result_df['val_ori'] = result_df['name']
            result_df['matched_col'] = result_df['matched_col'].apply(lambda x: map_dict[x])
            result_df['matched_value'] = result_df['matched_value'].apply(lambda x: highlight(x,keyword))
            result_df['val'] = result_df['val'].apply(lambda x: highlight(x,keyword))
            result_df['common_name_c'] = result_df['common_name_c'].apply(lambda x: highlight(x,keyword))

        else:
            card_len = 0
        
        response = {
            'title': f"{title_prefix}{map_dict[key]}",
            'total_count': total_count,
            'item_class': f"item_{record_type}_{key}",
            'card_class': f"{record_type}-{key}-card",
            'data': result_df.to_dict('records'),
            'has_more': True if card_len > 9 else False
        }

        return HttpResponse(json.dumps(response), content_type='application/json')


def get_more_cards(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        card_class = request.POST.get('card_class', '')
        is_sub = request.POST.get('is_sub', '')
        offset = request.POST.get('offset', '')
        offset = int(offset) if offset else offset
        key = card_class.split('-')[1]

        query = {
            "query": '',
            "limit": 0,
            "filter": ['recordType:col'],
            "facet": {},
            "sort":  "scientificName asc"
            }        

        if card_class.startswith('.col'):
            facet_list = col_facets
            map_dict = map_collection
        elif card_class.startswith('.occ'):
            facet_list = occ_facets
            map_dict = map_occurrence
            query.pop('filter', None)

        keyword_reg = ''
        q = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)

        
        if is_sub == 'true':
            facet_list = {'facet': {k: v for k, v in occ_facets['facet'].items() if k == key} }
            # query.update({'query': f'{key}:/.*{keyword_reg}.*/'})

        for i in facet_list['facet']:
            q += f'{i}:/.*{keyword_reg}.*/ OR ' 
            if card_class.startswith('.col'):
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/', 'filter': ['recordType:col']}})
            else:
                facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})

        query.update(facet_list)
        query.update({'query': q[:-4]})

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)      

        result = []
        if is_sub == 'false':
            for i in facets:
                x = facets[i]
                for k in x['buckets']:
                    bucket = k['taxonID']['buckets']
                    if i == 'eventDate':
                        if f_date := convert_date(k['val']):
                            f_date = f_date.strftime('%Y-%m-%d %H:%M:%S')
                            result += [dict(item, **{'matched_value':f_date, 'matched_col': i}) for item in bucket]
                    else:
                        result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
            result_df = pd.DataFrame(result)
            result_df_duplicated = result_df[result_df.duplicated(['val','count'])]
            if len(result_df_duplicated):
                remove_index = result_df_duplicated[result_df_duplicated.matched_col.isin(dup_col)].index
                result_df = result_df.loc[~result_df.index.isin(remove_index)]
        else:
            x = facets[key]
            for k in x['buckets']:
                bucket = k['taxonID']['buckets']
                if i == 'eventDate':
                    if f_date := convert_date(k['val']):
                        f_date = f_date.strftime('%Y-%m-%d %H:%M:%S')
                        result += [dict(item, **{'matched_value':f_date, 'matched_col': key}) for item in bucket]
                else:
                    result += [dict(item, **{'matched_value':k['val'], 'matched_col': key}) for item in bucket]
            result_df = pd.DataFrame(result)

        if len(result_df):
            card_len = len(result_df[offset:])
            result_df = result_df[offset:offset+9]
            result_df = pd.merge(result_df,taicol,left_on='val',right_on='taxonID')
            result_df['val'] = result_df['formatted_name']
            result_df['matched_col'] = result_df['matched_col'].apply(lambda x: map_dict[x])
            result_df['matched_value_ori'] = result_df['matched_value']
            result_df = result_df.replace({np.nan: ''}) 
            # result_df['val_ori'] = result_df['val']
            result_df['matched_value'] = result_df['matched_value'].apply(lambda x: highlight(x,keyword))
            result_df['val'] = result_df['val'].apply(lambda x: highlight(x,keyword))
            result_df['common_name_c'] = result_df['common_name_c'].apply(lambda x: highlight(x,keyword))
        else:
            card_len = 0

        response = {
            'data': result_df.to_dict('records'),
            'has_more': True if card_len > 9 else False
        }

        return HttpResponse(json.dumps(response), content_type='application/json')


def search_collection(request):

    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0&fq=recordType:col')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list = [f_list[x] for x in range(0, len(f_list),2)]

    sensitive_list = ['輕度', '重度', '縣市', '座標不開放', '物種不開放', '無']
    rank_list = [('界', 'kingdom'), ('門', 'phylum'), ('綱', 'class'), ('目', 'order'), ('科', 'family'), ('屬', 'genus'), ('種', 'species')]

    return render(request, 'pages/search_collection.html', {'holder_list': holder_list, 'sensitive_list': sensitive_list,
        'rank_list': rank_list})
    

def search_occurrence(request):

    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list = [f_list[x] for x in range(0, len(f_list),2)]

    sensitive_list = ['輕度', '重度', '縣市', '座標不開放', '物種不開放', '無'] # TODO 物種不開放僅開放有權限的人查詢
    rank_list = [('界', 'kingdom'), ('門', 'phylum'), ('綱', 'class'), ('目', 'order'), ('科', 'family'), ('屬', 'genus'), ('種', 'species')]
    basis_list = basis_dict.values()
        
    return render(request, 'pages/search_occurrence.html', {'holder_list': holder_list, 'sensitive_list': sensitive_list,
        'rank_list': rank_list, 'basis_list': basis_list})


def occurrence_detail(request, id):
    solr = SolrQuery('tbia_records')
    query_list = [('id', id), ('row',1)]
    req = solr.request(query_list)
    row = pd.DataFrame(req['solr_response']['response']['docs'])
    row = row.replace({np.nan: ''})
    row = row.replace({'nan': ''})
    row = row.to_dict('records')
    row = row[0]

    if row.get('taxonRank', ''):
        row.update({'taxonRank': map_occurrence[row['taxonRank']]})

    if row.get('dataGeneralizations', ''):
        if row['dataGeneralizations'] == 'True':
            row.update({'dataGeneralizations': '是'})
        elif row['dataGeneralizations'] == 'False':
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
        quantity = int(quantity[0])
    else:
        quantity = None
    row.update({'quantity': quantity})

    # taxon
    path_str = ''
    path = []
    if row.get('taxonID'):
        for r in rank_list:
            if row.get(r):
                if row.get(f"formatted_{r}"):
                    current_str = row.get(f"formatted_{r}")
                else:
                    current_str = row.get(r)
                if row.get(f"{r}_c"):
                    current_str += ' ' + row.get(f"{r}_c")
                path.append(current_str)
    path_str = ' > '.join(path)

    return render(request, 'pages/occurrence_detail.html', {'row': row, 'path_str': path_str})


def collection_detail(request, id):
    path_str = ''
    solr = SolrQuery('tbia_records')
    query_list = [('id', id), ('row',1)]
    req = solr.request(query_list)
    row = pd.DataFrame(req['solr_response']['response']['docs'])
    row = row.replace({np.nan: ''})
    row = row.replace({'nan': ''})
    row = row.to_dict('records')
    row = row[0]
    print(row.get('recordType'))
    if row.get('recordType') == ['col']:

        if row.get('taxonRank', ''):
            row.update({'taxonRank': map_collection[row['taxonRank']]})

        if row.get('dataGeneralizations', ''):
            if row['dataGeneralizations'] == 'True':
                row.update({'dataGeneralizations': '是'})
            elif row['dataGeneralizations'] == 'False':
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
            quantity = int(quantity[0])
        else:
            quantity = None
        row.update({'quantity': quantity})

        # taxon
        path = []
        if row.get('taxonID'):
            for r in rank_list:
                if row.get(r):
                    if row.get(f"formatted_{r}"):
                        current_str = row.get(f"formatted_{r}")
                    else:
                        current_str = row.get(r)
                    if row.get(f"{r}_c"):
                        current_str += ' ' + row.get(f"{r}_c")
                    path.append(current_str)
        path_str = ' > '.join(path)
    else:
        row = []

    return render(request, 'pages/collection_detail.html', {'row': row, 'path_str': path_str})




def get_conditional_records(request):
    if request.method == 'POST':
        # print(request.POST)
        # query_string = request.POST.urlencode()
        
        map_geojson = {}
        map_geojson[f'grid_1'] = {"type":"FeatureCollection","features":[]}
        map_geojson[f'grid_5'] = {"type":"FeatureCollection","features":[]}
        map_geojson[f'grid_10'] = {"type":"FeatureCollection","features":[]}
        map_geojson[f'grid_100'] = {"type":"FeatureCollection","features":[]}
        # default columns
        selected_col = ['common_name_c','scientificName', 'recordedBy', 'eventDate', 'rightsHolder']
        # use JSON API to avoid overlong query url
        query_list = []


        record_type = request.POST.get('record_type')
        if record_type == 'col': # occurrence include occurrence + collection
            query_list += ['recordType:col']
            map_dict = map_collection
        else:
            map_dict = map_occurrence

        for i in ['rightsHolder', 'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'resourceContacts',
                  'taxonID', 'preservation']:
            if val := request.POST.get(i):
                if val != 'undefined':
                    val = val.strip()
                    keyword_reg = ''
                    for j in val:
                        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                    if i in ['rightsHolder', 'locality', 'recordedBy', 'datasetName', 'resourceContacts', 'preservation']:
                        keyword_reg = get_variants(keyword_reg)
                    query_list += [f'{i}:/.*{keyword_reg}.*/']
        
        if quantity := request.POST.get('organismQuantity'):
            query_list += [f'standardOrganismQuantity: {quantity}']

        for i in ['sensitiveCategory', 'taxonRank', 'typeStatus']: # 下拉選單
            if val := request.POST.get(i):
                if i == 'sensitiveCategory' and val == '無':
                    query_list += [f'-(-{i}:{val} {i}:*)']
                else:
                    query_list += [f'{i}:{val}']

        if request.POST.get('start_date') and request.POST.get('end_date'):
            try: 
                start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').isoformat() + 'Z'
                end_date = datetime.strptime(request.POST.get('end_date'), '%Y-%m-%d')
                end_date = end_date.isoformat() + 'Z'
                end_date = end_date.replace('00:00:00','23:59:59')
                query_list += [f'standardDate:[{start_date} TO {end_date}]']
            except:
                pass

        geojson = {}
        geojson['features'] = ''

        if g_str := request.POST.get('geojson'):
            geojson = json.loads(g_str)
        elif g_id := request.POST.get('geojson_id'):
            try:
                with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                    geojson = json.loads(j.read())
            except:
                pass

        if geojson['features']:
            if circle_radius := request.POST.get('circle_radius'):
                query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (geojson['features'][0]['geometry']['coordinates'][1], geojson['features'][0]['geometry']['coordinates'][0], int(circle_radius))]
            else:
                geo_df = gpd.GeoDataFrame.from_features(geojson)
                g_list = []
                for i in geo_df.to_wkt()['geometry']:
                    if str(i).startswith('POLYGON'):
                        g_list += [i]
                try:
                    mp = MultiPolygon(map(wkt.loads, g_list))
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
                except:
                    pass
        
        if val := request.POST.get('name'):
            val = val.strip()
            keyword_reg = ''
            for j in val:
                keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
            keyword_reg = get_variants(keyword_reg)
            col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
            query_str = ' OR '.join( col_list )
            query_list += [ '(' + query_str + ')' ]
        # 如果有其他條件才進行搜尋，否則回傳空值
        if query_list and query_list != ['recordType:col']:

            page = int(request.POST.get('page', 1))
            offset = (page-1)*10

            query = { "query": "*:*",
                    "offset": offset,
                    "limit": 10,
                    "filter": query_list,
                    "sort":  "scientificName asc",
                    
                    }
            if request.POST.get('from') == 'page':
                response = requests.post(f'{SOLR_PREFIX}tbia_records/select?', data=json.dumps(query), headers={'content-type': "application/json" })
            else:
                for grid in [1,5,10,100]:
                    response = requests.post(f'{SOLR_PREFIX}tbia_records/select?facet=true&facet.pivot=grid_x_{grid},grid_y_{grid}', data=json.dumps(query), headers={'content-type': "application/json" })
                    # map
                    data_c = {}
                    data_c = response.json()['facet_counts']['facet_pivot'][f'grid_x_{grid},grid_y_{grid}']

                    for i in data_c:
                        current_grid_x = i['value']
                        for j in i['pivot']:
                            current_grid_y = j['value']
                            current_count = j['count']
                            # current_center_x, current_center_y = convert_grid_to_coor(current_grid_x, current_grid_y)
                            if current_grid_x != -1 and current_grid_y != -1:
                                borders = convert_grid_to_square(current_grid_x, current_grid_y, grid/100)
                                # print(borders)
                                tmp = [{
                                    "type": "Feature",
                                    "geometry":{"type":"Polygon","coordinates":[borders]},
                                    "properties": {
                                        "counts": current_count
                                    }
                                }]
                                map_geojson[f'grid_{grid}']['features'] += tmp


            count = response.json()['response']['numFound']
            docs = pd.DataFrame(response.json()['response']['docs'])
            docs = docs.replace({np.nan: ''})
            docs = docs.replace({'nan': ''})

            for i in docs.index:
                row = docs.iloc[i]
                if row.get('scientificName') and row.get('formatted_name'):
                    docs.loc[i, 'scientificName'] = docs.loc[i, 'formatted_name']
                # date
                if date := row.get('standardDate'):
                    date = date[0].split('T')[0]
                    docs.loc[i , 'eventDate'] = date
                else:
                    if row.get('eventDate'):
                        docs.loc[i , 'eventDate'] = '---<br><small style="color: silver">[原始紀錄日期]' + docs.loc[i , 'eventDate'] + '</small>'

                #     # date = date[0].replace('T', ' ').replace('Z','')
                #     # 如果是國家公園，原本調查的時間是區段
                #     if row.get('rightsHolder') == '臺灣國家公園生物多樣性資料庫':
                #         docs.loc[i , 'eventDate'] = date[0].split('T')[0] # 只取日期
                #     else:
                #         docs.loc[i , 'eventDate'] = date[0].replace('T', ' ').replace('Z','')
                # else:
                    # if row.get('eventDate'):
                    #     docs.loc[i , 'eventDate'] = '---<br><small style="color: silver">[原始紀錄日期]' + docs.loc[i , 'eventDate'] + '</small>'
                # 經緯度
                if lat := row.get('standardLatitude'):
                    docs.loc[i , 'verbatimLatitude'] = lat[0]
                else:
                    if row.get('verbatimLatitude'):
                        docs.loc[i , 'verbatimLatitude'] = '---<br><small style="color: silver">[原始紀錄緯度]' + docs.loc[i , 'verbatimLatitude'] + '</small>'

                if lon := row.get('standardLongitude'):
                    docs.loc[i , 'verbatimLongitude'] = lon[0]
                else:
                    if row.get('verbatimLongitude'):
                        docs.loc[i , 'verbatimLongitude'] = '---<br><small style="color: silver">[原始紀錄經度]' + docs.loc[i , 'verbatimLongitude'] + '</small>'
                # 數量
                if quantity := row.get('standardOrganismQuantity'):
                    docs.loc[i , 'standardOrganismQuantity'] = int(quantity[0])
                else:
                    if row.get('organismQuantity'):
                        docs.loc[i , 'organismQuantity'] = '---<br><small style="color: silver">[原始紀錄數量]' + docs.loc[i , 'organismQuantity'] + '</small>'

            docs = docs.replace({np.nan: ''})
            docs = docs.replace({'nan': ''})
            
            docs = docs.to_dict('records')

            current_page = offset / 10 + 1
            total_page = math.ceil(count / 10)
            page_list = get_page_list(current_page, total_page)

            response = {
                'rows' : docs,
                'count': count,
                'page_list': page_list,
                'current_page' : current_page,
                'total_page' : total_page,
                'selected_col': selected_col,
                'map_dict': map_dict,
                'map_geojson': map_geojson
            }
        
        else:
            response = {
                'rows' : {},
                'count': 0,
                'current_page' : 0,
                'total_page' : 0,
                'selected_col': selected_col,
                'map_dict': map_dict,
                'map_geojson': map_geojson,
            }

        return HttpResponse(json.dumps(response, default=str), content_type='application/json')
