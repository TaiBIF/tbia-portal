from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT
from utils.solr_query import SolrQuery, col_facets, occ_facets, SOLR_PREFIX
from pages.models import Resource, News
from django.db.models import Q
from data.utils import *
# from data.taicol import taicol
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
from manager.models import SearchQuery, User, SensitiveDataRequest, SensitiveDataResponse, Partner
from pages.models import Notification
from urllib import parse
from manager.views import send_notification
from django.utils import timezone
from os.path import exists
from data.models import Namecode, Taxon, DatasetKey

basis_dict = { 'HumanObservation':'人為觀察', 'PreservedSpecimen':'保存標本', 'FossilSpecimen':'化石標本', 
                'LivingSpecimen':'活體標本', 'MaterialSample':'組織樣本',
                'MachineObservation':'機器觀測', 'Occurrence':'出現紀錄'}


def get_geojson(request,id):
    if SearchQuery.objects.filter(id=id).exists():
        sq = SearchQuery.objects.get(id=id)
        search_dict = dict(parse.parse_qsl(sq.query))
        map_json = search_dict.get('geojson')
        response = HttpResponse(map_json, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="geojson.json"'
        return response


def get_taxon_dist(request):
    taxon_id = request.GET.get('taxonID')
    map_geojson = {}
    map_geojson[f'grid_1'] = {"type":"FeatureCollection","features":[]}
    map_geojson[f'grid_5'] = {"type":"FeatureCollection","features":[]}
    map_geojson[f'grid_10'] = {"type":"FeatureCollection","features":[]}
    map_geojson[f'grid_100'] = {"type":"FeatureCollection","features":[]}

    query = {"query": f"taxonID:{taxon_id}",
            "offset": 0,
            "limit": 0}
    
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
                    tmp = [{
                        "type": "Feature",
                        "geometry":{"type":"Polygon","coordinates":[borders]},
                        "properties": {
                            "counts": current_count
                        }
                    }]
                    map_geojson[f'grid_{grid}']['features'] += tmp

    return HttpResponse(json.dumps(map_geojson, default=str), content_type='application/json')


def sensitive_agreement(request):
    return render(request, 'pages/agreement.html')


def send_sensitive_request(request):
    if request.method == 'GET':
        # 整理查詢條件
        search_dict = request.GET
        query = create_query_display(search_dict,None)
        return render(request, 'pages/application.html', {'query': query})


def submit_sensitive_request(request):
    if request.method == 'POST':
        req_dict = dict(request.POST)
        not_query = ['selected_col','applicant','phone','address','affiliation','type','project_name','project_affiliation','abstract','users','csrfmiddlewaretoken','page','from']
        for nq in not_query:
            if nq in req_dict.keys():
                req_dict.pop(nq)
        for k in req_dict.keys():
            if len(req_dict[k])==1:
                req_dict[k] = req_dict[k][0]

        query_string = parse.urlencode(req_dict)
        user_id = request.user.id
        query_id = str(ObjectId())
        
        sq = SearchQuery.objects.create(
            user = User.objects.filter(id=user_id).first(),
            query = query_string,
            status = 'pending', # 如果單位都同意,檔案也製作好,這邊才會變成pass
            type = 'sensitive',
            query_id = query_id
        )

        # SensitiveDataRequest
        SensitiveDataRequest.objects.create(
            applicant = request.POST.get('applicant'),
            phone = request.POST.get('phone'),
            address = request.POST.get('address'),
            affiliation = request.POST.get('affiliation'),
            project_name = request.POST.get('project_name'),
            project_affiliation = request.POST.get('project_affiliation'),
            type = request.POST.get('type'),
            users = json.loads(request.POST.get('users')),
            abstract = request.POST.get('abstract'),
            query_id = query_id
        )

        # 抓出所有單位
        if request.POST.get('type') == '0':
            query_list = []

            record_type = req_dict.get('record_type')
            if record_type == 'col': # occurrence include occurrence + collection
                query_list += ['recordType:col']

            for i in ['locality', 'recordedBy', 'resourceContacts', 'taxonID', 'preservation']:
                if val := req_dict.get(i):
                    if val != 'undefined':
                        val = val.strip()
                        keyword_reg = ''
                        for j in val:
                            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                        if i in ['locality', 'recordedBy', 'resourceContacts', 'preservation']:
                            keyword_reg = get_variants(keyword_reg)
                        query_list += [f'{i}:/.*{keyword_reg}.*/']
            
            if quantity := req_dict.get('organismQuantity'):
                query_list += [f'standardOrganismQuantity: {quantity}']

            # 下拉選單單選
            for i in ['sensitiveCategory', 'taxonRank','typeStatus','rightsHolder','basisOfRecord']: 
                if val := req_dict.get(i):
                    if i == 'sensitiveCategory' and val == '無':
                        query_list += [f'-(-{i}:{val} {i}:*)']
                    else:
                        query_list += [f'{i}:{val}']

            # 下拉選單多選
            d_list = []
            if val := req_dict.getlist('datasetName'):
                for v in val:
                    if DatasetKey.objects.filter(id=v).exists():
                        d_list.append(DatasetKey.objects.get(id=v).name)
            
            if d_list:
                d_list_str = '" OR "'.join(d_list)
                query_list += [f'datasetName:("{d_list_str}")']

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

            if g_id := req_dict.get('geojson_id'):
                try:
                    with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                        geojson = json.loads(j.read())
                except:
                    pass

            if circle_radius := req_dict.get('circle_radius'):
                query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (req_dict.get('center_lat'), req_dict.get('center_lon'), int(circle_radius))]

            if g_list := req_dict.getlist('polygon'):
                try:
                    mp = MultiPolygon(map(wkt.loads, g_list))
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
                except:
                    pass

            if geojson['features']:
                geo_df = gpd.GeoDataFrame.from_features(geojson)
                g_list = []
                for i in geo_df.to_wkt()['geometry']:
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % i]

            # if geojson['features']:
            #     if circle_radius := req_dict.get('circle_radius'):
            #         query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (geojson['features'][0]['geometry']['coordinates'][1], geojson['features'][0]['geometry']['coordinates'][0], int(circle_radius))]
            #     else:
            #         geo_df = gpd.GeoDataFrame.from_features(geojson)
            #         g_list = []
            #         for i in geo_df.to_wkt()['geometry']:
            #             if str(i).startswith('POLYGON'):
            #                 g_list += [i]
            #         try:
            #             mp = MultiPolygon(map(wkt.loads, g_list))
            #             query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
            #         except:
            #             pass
            
            if val := req_dict.get('name'):
                val = val.strip()
                # 去除重複空格
                val = re.sub(' +', ' ', val)
                # 去除特殊字元
                val = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', val)
                keyword_reg = ''
                for j in val:
                    keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                keyword_reg = get_variants(keyword_reg)
                col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
                query_str = ' OR '.join( col_list )
                query_list += [ '(' + query_str + ')' ]
            # 如果有其他條件才進行搜尋，否則回傳空值
            if query_list and query_list != ['recordType:col']:

                query = { "query": "raw_location_rpt:[* TO *]",
                        "offset": 0,
                        "limit": 0,
                        "filter": query_list,
                        "facet":{  
                            "group": {
                                "type": "terms",
                                "field": "group",
                                "limit": -1,
                                }
                        }
                        }
                response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
                groups = []
                if  response.json()['facets'].get('group'):
                    group = response.json()['facets']['group']['buckets']
                    for g in group:
                        groups.append(g['val'])
            
                for p in Partner.objects.filter(group__in=groups):
                    sdr = SensitiveDataResponse.objects.create(
                        partner = p,
                        status = 'pending',
                        query_id = query_id
                    )       
                    # 寄送通知給系統管理員 & 單位管理員
                    usrs = User.objects.filter(Q(is_system_admin=True)|Q(is_partner_admin=True, partner_id=p.id)) # 個人研究計畫
                    for u in usrs:
                        nn = Notification.objects.create(
                            type = 3,
                            content = sdr.id,
                            user = u
                        )
                        content = nn.get_type_display().replace('0000', str(nn.content))
                        send_notification([u.id],content,'單次使用敏感資料申請通知')

            # TODO 這邊要寫else嗎
        else:
            # 委辦工作計畫
            sdr = SensitiveDataResponse.objects.create(
                        status = 'pending',
                        query_id = query_id
                    )     
            usrs = User.objects.filter(is_system_admin=True) 
            for u in usrs:
                nn = Notification.objects.create(
                    type = 3,
                    content = sdr.id,
                    user = u
                )
                content = nn.get_type_display().replace('0000', str(nn.content))
                send_notification([u.id],content,'單次使用敏感資料申請通知')

        
        return JsonResponse({"status": 'success'}, safe=False)


def submit_sensitive_response(request):
    if SensitiveDataResponse.objects.filter(id=request.POST.get('sdr_id')).exists():
        sdr = SensitiveDataResponse.objects.get(id=request.POST.get('sdr_id'))
        sdr.status = request.POST.get('status')
        sdr.reviewer_name = request.POST.get('reviewer_name')
        sdr.comment = request.POST.get('comment')
        sdr.save()

    # 確認是不是最後一個單位審核, 如果是的話產生下載檔案
    # 若是機關委託計畫，排除已轉移給各單位審核的
    if not SensitiveDataResponse.objects.filter(query_id=request.POST.get('query_id'),status='pending').exclude(is_transferred=True).exists():
        task = threading.Thread(target=generate_sensitive_csv, args=(request.POST.get('query_id'),))
        task.start()

    return JsonResponse({"status": 'success'}, safe=False)


def transfer_sensitive_response(request):
    # 原本的SensitiveDataResponse 改成is_transferred
    if request.method == 'POST':
        query_id = request.POST.get('query_id')
        if SensitiveDataResponse.objects.filter(query_id=query_id, partner_id=None, is_transferred=False).exists() and SearchQuery.objects.filter(query_id=query_id).exists():
            sdr = SensitiveDataResponse.objects.get(query_id=query_id, partner_id=None, is_transferred=False)
            sdr.is_transferred = True
            sdr.save()
            
            # 機關計畫送交給夥伴單位審核
            sq = SearchQuery.objects.get(query_id=query_id)
            req_dict = dict(parse.parse_qsl(sq.query))
            query_list = []

            record_type = req_dict.get('record_type')
            if record_type == 'col': # occurrence include occurrence + collection
                query_list += ['recordType:col']

            for i in ['locality', 'recordedBy', 'resourceContacts', 'taxonID', 'preservation']:
                if val := req_dict.get(i):
                    if val != 'undefined':
                        val = val.strip()
                        keyword_reg = ''
                        for j in val:
                            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                        if i in ['locality', 'recordedBy', 'resourceContacts', 'preservation']:
                            keyword_reg = get_variants(keyword_reg)
                        query_list += [f'{i}:/.*{keyword_reg}.*/']
            
            if quantity := req_dict.get('organismQuantity'):
                query_list += [f'standardOrganismQuantity: {quantity}']

            # 下拉選單單選
            for i in ['sensitiveCategory', 'taxonRank','typeStatus','rightsHolder','basisOfRecord']: 
                if val := req_dict.get(i):
                    if i == 'sensitiveCategory' and val == '無':
                        query_list += [f'-(-{i}:{val} {i}:*)']
                    else:
                        query_list += [f'{i}:{val}']
            
            # 下拉選單多選
            d_list = []
            if val := req_dict.getlist('datasetName'):
                for v in val:
                    if DatasetKey.objects.filter(id=v).exists():
                        d_list.append(DatasetKey.objects.get(id=v).name)
            
            if d_list:
                d_list_str = '" OR "'.join(d_list)
                query_list += [f'datasetName:("{d_list_str}")']

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

            if g_id := req_dict.get('geojson_id'):
                try:
                    with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                        geojson = json.loads(j.read())
                except:
                    pass

            if circle_radius := req_dict.get('circle_radius'):
                query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (req_dict.get('center_lat'), req_dict.get('center_lon'), int(circle_radius))]

            if g_list := req_dict.getlist('polygon'):
                try:
                    mp = MultiPolygon(map(wkt.loads, g_list))
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
                except:
                    pass

            if geojson['features']:
                geo_df = gpd.GeoDataFrame.from_features(geojson)
                g_list = []
                for i in geo_df.to_wkt()['geometry']:
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % i]
                
            if val := req_dict.get('name'):
                val = val.strip()
                # 去除重複空格
                val = re.sub(' +', ' ', val)
                # 去除特殊字元
                val = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', val)
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
                        "facet": {
                            "group": {
                                "type": "terms",
                                "field": "group",
                                "limit": -1,
                                }
                            }
                        }
                response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
                group = response.json()['facets']['group']['buckets']
                groups = []
                for g in group:
                    groups.append(g['val'])
            
                for p in Partner.objects.filter(group__in=groups):
                    new_sdr = SensitiveDataResponse.objects.create(
                        partner = p,
                        status = 'pending',
                        query_id = query_id
                    )       
                    # 寄送通知給系統管理員 & 單位管理員
                    usrs = User.objects.filter(Q(is_system_admin=True)|Q(is_partner_admin=True, partner_id=p.id)) # 個人研究計畫
                    for u in usrs:
                        nn = Notification.objects.create(
                            type = 3,
                            content = new_sdr.id,
                            user = u
                        )
                        content = nn.get_type_display().replace('0000', str(nn.content))
                        send_notification([u.id],content,'單次使用敏感資料申請通知')
        # TODO 要不要寫else
    return JsonResponse({"status": 'success'}, safe=False)


def generate_sensitive_csv(query_id):
    
    if SearchQuery.objects.filter(query_id=query_id).exists():
        sq = SearchQuery.objects.get(query_id=query_id)
        req_dict = dict(parse.parse_qsl(sq.query))

        download_id = f"{sq.user_id}_{query_id}"

        # 只給有同意單位的資料
        # 如果是機關委託計畫的話 則全部都給
        if SensitiveDataResponse.objects.filter(query_id=query_id,status='pass',is_transferred=False, partner_id=None).exists():
            group = ['*']
        elif SensitiveDataResponse.objects.filter(query_id=query_id,status='fail',is_transferred=False, partner_id=None).exists():
            group = []
        else:
            ps = list(SensitiveDataResponse.objects.filter(query_id=query_id,status='pass').values_list('partner_id'))
            if ps:
                ps = [p for p in ps[0]]
                group = list(Partner.objects.filter(id__in=ps).values_list('group'))
                group = [g for g in group[0]]
            else:
                group = []

        if group:

            fl_cols = download_cols + sensitive_cols
            # 先取得筆數，export to csv
            query_list = []

            record_type = req_dict.get('record_type')
            if record_type == 'col': # occurrence include occurrence + collection
                query_list += ['recordType:col']

            for i in ['locality', 'recordedBy', 'resourceContacts', 'taxonID', 'preservation']:
                if val := req_dict.get(i):
                    if val != 'undefined':
                        val = val.strip()
                        keyword_reg = ''
                        for j in val:
                            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                        if i in ['locality', 'recordedBy', 'resourceContacts', 'preservation']:
                            keyword_reg = get_variants(keyword_reg)
                        query_list += [f'{i}:/.*{keyword_reg}.*/']
            
            if quantity := req_dict.get('organismQuantity'):
                query_list += [f'standardOrganismQuantity: {quantity}']

            # 下拉選單單選
            for i in ['sensitiveCategory', 'taxonRank','typeStatus','rightsHolder','basisOfRecord']: 
                if val := req_dict.get(i):
                    if i == 'sensitiveCategory' and val == '無':
                        query_list += [f'-(-{i}:{val} {i}:*)']
                    else:
                        query_list += [f'{i}:{val}']

            # 下拉選單多選
            d_list = []
            if val := req_dict.getlist('datasetName'):
                for v in val:
                    if DatasetKey.objects.filter(id=v).exists():
                        d_list.append(DatasetKey.objects.get(id=v).name)
            
            if d_list:
                d_list_str = '" OR "'.join(d_list)
                query_list += [f'datasetName:("{d_list_str}")']

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

            if g_id := req_dict.get('geojson_id'):
                try:
                    with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                        geojson = json.loads(j.read())
                except:
                    pass

            if circle_radius := req_dict.get('circle_radius'):
                query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (req_dict.get('center_lat'), req_dict.get('center_lon'), int(circle_radius))]

            if g_list := req_dict.getlist('polygon'):
                try:
                    mp = MultiPolygon(map(wkt.loads, g_list))
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
                except:
                    pass

            if geojson['features']:
                geo_df = gpd.GeoDataFrame.from_features(geojson)
                g_list = []
                for i in geo_df.to_wkt()['geometry']:
                    query_list += ['{!field f=location_rpt}Intersects(%s)' % i]

            if val := req_dict.get('name'):
                val = val.strip()
                # 去除重複空格
                val = re.sub(' +', ' ', val)
                # 去除特殊字元
                val = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', val)
                keyword_reg = ''
                for j in val:
                    keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                keyword_reg = get_variants(keyword_reg)
                col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
                query_str = ' OR '.join( col_list )
                query_list += [ '(' + query_str + ')' ]

            group = [ f'group:{g}' for g in group ]
            group_str = ' OR '.join( group )
            query_list += [ '(' + group_str + ')' ]
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
                csv_folder = os.path.join(csv_folder, 'sensitive')
                csv_file_path = os.path.join(csv_folder, f'{download_id}.csv')
                solr_url = f"{SOLR_PREFIX}tbia_records/select?wt=csv"
                commands = f"curl -X POST {solr_url} -d '{json.dumps(query)}' > {csv_file_path} "
                process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # 儲存到下載統計
                # 要排除掉轉交的情況
                tmp = SensitiveDataResponse.objects.filter(query_id=query_id).exclude(is_transferred=True)
                # if len(tmp) == len(tmp.filter(status='pass')):
                #     sq.status = 'pass'
                # else:
                #     sq.status = 'partial'
                sq.status = 'pass'
                sq.modified = timezone.now()
                sq.save()
            # TODO 這邊要寫else嗎

        else:
            # 沒有帳號通過
            
            sq.status = 'fail'
            sq.modified = timezone.now()
            sq.save()


        #  這邊要給審查意見
        nn = Notification.objects.create(
            type = 4,
            content = sq.id,
            user_id = sq.user_id
        )
        content = nn.get_type_display().replace('0000', str(nn.content))
        send_notification([sq.user_id],content,'單次使用敏感資料申請結果通知')



def save_geojson(request):
    if request.method == 'POST':
        geojson = request.POST.get('geojson_text')
        geojson = gpd.read_file(geojson, driver='GeoJSON')
        geojson = geojson.dissolve()
        geojson = geojson.to_json()

        oid = str(ObjectId())
        with open(f'/tbia-volumes/media/geojson/{oid}.json', 'w') as f:
            json.dump(json.loads(geojson), f)
        return JsonResponse({"geojson_id": oid, "geojson": geojson}, safe=False)


def return_geojson_query(request):
    if request.method == 'POST':
        geojson = request.POST.get('geojson_text')
        geojson = gpd.read_file(geojson, driver='GeoJSON')
        geojson = geojson.dissolve()

    # geo_df = gpd.GeoDataFrame.from_features(geojson)
        g_list = []
        for i in geojson.to_wkt()['geometry']:
            if str(i).startswith('POLYGON'):
                g_list += [i]
        # print(g_list)
        return JsonResponse({"polygon": g_list}, safe=False)

def send_download_request(request):
    if request.method == 'POST':
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
    download_id = f"{user_id}_{str(ObjectId())}"

    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
        fl_cols = download_cols + sensitive_cols
    else:
        fl_cols = download_cols

    # 先取得筆數，export to csv
    query_list = []

    record_type = req_dict.get('record_type')
    if record_type == 'col': # occurrence include occurrence + collection
        query_list += ['recordType:col']

    for i in ['locality', 'recordedBy', 'resourceContacts', 'taxonID', 'preservation']:
        if val := req_dict.get(i):
            if val != 'undefined':
                val = val.strip()
                keyword_reg = ''
                for j in val:
                    keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                if i in ['locality', 'recordedBy', 'resourceContacts', 'preservation']:
                    keyword_reg = get_variants(keyword_reg)
                query_list += [f'{i}:/.*{keyword_reg}.*/']
    
    if quantity := req_dict.get('organismQuantity'):
        query_list += [f'standardOrganismQuantity: {quantity}']

    # 下拉選單單選
    for i in ['sensitiveCategory', 'taxonRank','typeStatus','rightsHolder','basisOfRecord']: 
        if val := req_dict.get(i):
            if i == 'sensitiveCategory' and val == '無':
                query_list += [f'-(-{i}:{val} {i}:*)']
            else:
                query_list += [f'{i}:{val}']

    # 下拉選單多選
    d_list = []
    if val := req_dict.getlist('datasetName'):
        for v in val:
            if DatasetKey.objects.filter(id=v).exists():
                d_list.append(DatasetKey.objects.get(id=v).name)

    if d_list:
        d_list_str = '" OR "'.join(d_list)
        query_list += [f'datasetName:("{d_list_str}")']

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

    if g_id := req_dict.get('geojson_id'):
        try:
            with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                geojson = json.loads(j.read())
        except:
            pass

    if circle_radius := req_dict.get('circle_radius'):
        query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (req_dict.get('center_lat'), req_dict.get('center_lon'), int(circle_radius))]

    if g_list := req_dict.getlist('polygon'):
        try:
            mp = MultiPolygon(map(wkt.loads, g_list))
            query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
        except:
            pass

    if geojson['features']:
        geo_df = gpd.GeoDataFrame.from_features(geojson)
        g_list = []
        for i in geo_df.to_wkt()['geometry']:
            query_list += ['{!field f=location_rpt}Intersects(%s)' % i]

    # if geojson['features']:
    #     if circle_radius := req_dict.get('circle_radius'):
    #         query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (geojson['features'][0]['geometry']['coordinates'][1], geojson['features'][0]['geometry']['coordinates'][0], int(circle_radius))]
    #     else:
    #         geo_df = gpd.GeoDataFrame.from_features(geojson)
    #         g_list = []
    #         for i in geo_df.to_wkt()['geometry']:
    #             if str(i).startswith('POLYGON'):
    #                 g_list += [i]
    #         try:
    #             mp = MultiPolygon(map(wkt.loads, g_list))
    #             query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
    #         except:
    #             pass
    
    if val := req_dict.get('name'):
        val = val.strip()
        # 去除重複空格
        val = re.sub(' +', ' ', val)
        # 去除特殊字元
        val = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', val)
        keyword_reg = ''
        for j in val:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
        query_str = ' OR '.join( col_list )
        query_list += [ '(' + query_str + ')' ]


    req_dict = dict(req_dict)
    not_query = ['csrfmiddlewaretoken','page','from','taxon','selected_col']
    for nq in not_query:
        if nq in req_dict.keys():
            req_dict.pop(nq)
    for k in req_dict.keys():
        if len(req_dict[k])==1:
            req_dict[k] = req_dict[k][0]
    query_string = parse.urlencode(req_dict)

    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'record',
        query_id = download_id.split('_')[-1]
    )
    

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
        csv_folder = os.path.join(csv_folder, 'record')
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
    # TODO 這邊要做else嗎？
# facet.pivot=taxonID,scientificName


def generate_species_csv(req_dict,user_id):
    download_id = f"{user_id}_{str(ObjectId())}"

    # 先取得筆數，export to csv
    query_list = []

    record_type = req_dict.get('record_type')
    if record_type == 'col': # occurrence include occurrence + collection
        query_list += ['recordType:col']

    for i in ['locality', 'recordedBy', 'resourceContacts', 'taxonID', 'preservation']:
        if val := req_dict.get(i):
            if val != 'undefined':
                val = val.strip()
                keyword_reg = ''
                for j in val:
                    keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                if i in ['locality', 'recordedBy', 'resourceContacts', 'preservation']:
                    keyword_reg = get_variants(keyword_reg)
                query_list += [f'{i}:/.*{keyword_reg}.*/']
    
    if quantity := req_dict.get('organismQuantity'):
        query_list += [f'standardOrganismQuantity: {quantity}']

    # 下拉選單單選
    for i in ['sensitiveCategory', 'taxonRank','typeStatus','rightsHolder','basisOfRecord']: 
        if val := req_dict.get(i):
            if i == 'sensitiveCategory' and val == '無':
                query_list += [f'-(-{i}:{val} {i}:*)']
            else:
                query_list += [f'{i}:{val}']

    # 下拉選單多選
    d_list = []
    if val := req_dict.getlist('datasetName'):
        for v in val:
            if DatasetKey.objects.filter(id=v).exists():
                d_list.append(DatasetKey.objects.get(id=v).name)
    
    if d_list:
        d_list_str = '" OR "'.join(d_list)
        query_list += [f'datasetName:("{d_list_str}")']

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

    if g_id := req_dict.get('geojson_id'):
        try:
            with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                geojson = json.loads(j.read())
        except:
            pass

    if circle_radius := req_dict.get('circle_radius'):
        query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (req_dict.get('center_lat'), req_dict.get('center_lon'), int(circle_radius))]

    if g_list := req_dict.getlist('polygon'):
        try:
            mp = MultiPolygon(map(wkt.loads, g_list))
            query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
        except:
            pass

    if geojson['features']:
        geo_df = gpd.GeoDataFrame.from_features(geojson)
        g_list = []
        for i in geo_df.to_wkt()['geometry']:
            query_list += ['{!field f=location_rpt}Intersects(%s)' % i]

    if val := req_dict.get('name'):
        val = val.strip()
        # 去除重複空格
        val = re.sub(' +', ' ', val)
        # 去除特殊字元
        val = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', val)
        keyword_reg = ''
        for j in val:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        col_list = [ f'{i}:/.*{keyword_reg}.*/' for i in dup_col ]
        query_str = ' OR '.join( col_list )
        query_list += [ '(' + query_str + ')' ]

    req_dict = dict(req_dict)
    not_query = ['csrfmiddlewaretoken','page','from','taxon','selected_col']
    for nq in not_query:
        if nq in req_dict.keys():
            req_dict.pop(nq)
    for k in req_dict.keys():
        if len(req_dict[k])==1:
            req_dict[k] = req_dict[k][0]
    query_string = parse.urlencode(req_dict)

    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'taxon',
        query_id = download_id.split('_')[-1]
    )

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
        if len(df):
            subset_taxon = pd.DataFrame(Taxon.objects.filter(taxonID__in=df.taxonID.to_list()).values('common_name_c','alternative_name_c','synonyms','taxonID'))
            df = df.merge(subset_taxon, how='left')

        csv_folder = os.path.join(settings.MEDIA_ROOT, 'download')
        csv_folder = os.path.join(csv_folder, 'taxon')
        csv_file_path = os.path.join(csv_folder, f'{download_id}.csv')
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
    # TODO 這邊要不要寫else

    # return csv file

def generate_download_csv_full(req_dict,user_id):
    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
        fl_cols = download_cols + sensitive_cols
    else:
        fl_cols = download_cols
    # req_dict_query = req_dict.get('search_str')
    download_id = f"{user_id}_{str(ObjectId())}"
    req_dict_query = dict(parse.parse_qsl(req_dict.get('search_str')))

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
    req_dict = dict(req_dict)
    not_query = ['csrfmiddlewaretoken','page','from','taxon','selected_col']
    for nq in not_query:
        if nq in req_dict.keys():
            req_dict.pop(nq)
    for k in req_dict.keys():
        if len(req_dict[k])==1:
            req_dict[k] = req_dict[k][0]

    query_string = parse.urlencode(req_dict)
    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'record',
        query_id = download_id.split('_')[-1]
    )


    if query_list:

        query = { "query": q,
                "offset": 0,
                "limit": req_dict.get('total_count'),
                "filter": query_list,
                "sort":  "scientificName asc",
                "fields": fl_cols,
                }

        csv_folder = os.path.join(settings.MEDIA_ROOT, 'download')
        csv_folder = os.path.join(csv_folder, 'record')
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

        # 去除重複空格
        keyword = re.sub(' +', ' ', keyword)
        # 去除特殊字元
        keyword = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', keyword)

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
        if not enable_query_date:
            if 'eventDate' in facet_list['facet'].keys():
                facet_list['facet'].pop('eventDate')
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

        # 物種結果
        # taxon_list = []

        c_collection = response.json()['response']['numFound']
        # c_collection = 0
        collection_rows = []
        result = []
        taxon_result = []
        col_card_len = 0
        for i in facets:
            x = facets[i]
            if (i != 'eventDate') or (enable_query_date and i == 'eventDate'): 
                if x['allBuckets']['count']:
                    collection_rows.append({
                        'title': map_collection[i],
                        'total_count': x['allBuckets']['count'],
                        'key': i
                    })
                for k in x['buckets']:
                    col_card_len += k['taxonID']['numBuckets']
                    bucket = k['taxonID']['buckets']
                    for item in bucket:
                        if dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in result:
                            result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i})) 
                        if i in taxon_cols and dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in taxon_result:
                            taxon_result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i})) 
            else:
                # if x['buckets']:
                c_collection -= x['allBuckets']['count']
        col_result_df = pd.DataFrame(result)
        # col_result_df_duplicated = col_result_df[col_result_df.duplicated(['val','count'])]
        # if len(col_result_df_duplicated):
        #     col_remove_index = col_result_df_duplicated[col_result_df_duplicated.matched_col.isin(dup_col)].index
        #     col_result_df = col_result_df.loc[~col_result_df.index.isin(col_remove_index)]
        if col_card_len:
            # col_card_len = len(col_result_df)
            col_result_df = col_result_df[:9]
            taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=col_result_df.val.unique()).values())
            taicol = taicol.rename(columns={'scientificName': 'name', 'scientificNameID': 'taxon_name_id'})
            col_result_df = pd.merge(col_result_df,taicol,left_on='val',right_on='taxonID')
            col_result_df['val'] = col_result_df['formatted_name']
            col_result_df['key'] = col_result_df['matched_col']
            col_result_df['matched_col'] = col_result_df['matched_col'].apply(lambda x: map_collection[x])
            col_result_df = col_result_df.replace({np.nan: ''})
        else:
            col_card_len = 0
        # 物種整理
        taxon_result_df = pd.DataFrame(taxon_result)
        # occurrence
        facet_list = occ_facets
        if not enable_query_date:
            if 'eventDate' in facet_list['facet'].keys():
                facet_list['facet'].pop('eventDate')
        q = ''
        for i in facet_list['facet']:
            q += f'{i}:/.*{keyword_reg}.*/ OR ' 
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.pop('filter', None)
        query.update(facet_list)
        q = q[:-4]
        query.update({'query': q})

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)
        
        c_occurrence = response.json()['response']['numFound']
        occurrence_rows = []
        result = []
        taxon_result = []

        occ_card_len = 0
        for i in facets:
            x = facets[i]
            if (i!='eventDate') or (enable_query_date and i == 'eventDate'): 
                if x['allBuckets']['count']:
                    # print(x)
                    occurrence_rows.append({
                        'title': map_occurrence[i],
                        'total_count': x['allBuckets']['count'],
                        'key': i
                    })
                for k in x['buckets']:
                    occ_card_len += k['taxonID']['numBuckets']
                    bucket = k['taxonID']['buckets']
                    for item in bucket:
                        if dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in result:
                            result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i}))
                    # result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
                            if i in taxon_cols and dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in taxon_result:
                                taxon_result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i}))
                        # for item in bucket:
                        #     if dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in taxon_result:
                        #         taxon_result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i}))
                            # taxon_result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
            else:
                if x['buckets']:
                    c_occurrence -= x['allBuckets']['count']

        occ_result_df = pd.DataFrame(result)
        # occ_result_df_duplicated = occ_result_df[occ_result_df.duplicated(['val','count'])]
        # print(len(occ_result_df))
        c = 0
        for i in x['buckets']:
            c+=i['taxonID']['numBuckets']
        print(occ_card_len)
        # if len(occ_result_df_duplicated):
        #     occ_remove_index = occ_result_df_duplicated[occ_result_df_duplicated.matched_col.isin(dup_col)].index
        #     occ_result_df = occ_result_df.loc[~occ_result_df.index.isin(occ_remove_index)]        
        if occ_card_len:
            # occ_card_len = len(occ_result_df)
            occ_result_df = occ_result_df[:9]
            taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=occ_result_df.val.unique()).values())
            taicol = taicol.rename(columns={'scientificName': 'name', 'scientificNameID': 'taxon_name_id'})
            occ_result_df = pd.merge(occ_result_df,taicol,left_on='val',right_on='taxonID')
            occ_result_df['val'] = occ_result_df['formatted_name']
            occ_result_df['key'] = occ_result_df['matched_col']
            occ_result_df['matched_col'] = occ_result_df['matched_col'].apply(lambda x: map_occurrence[x])
            occ_result_df = occ_result_df.replace({np.nan: ''})
        else:
            occ_card_len = 0
        # 物種整理
        taxon_occ_result_df = pd.DataFrame(taxon_result)
        # taxon_occ_result_df_duplicated = taxon_occ_result_df[taxon_occ_result_df.duplicated(['val','count'])]
        # if len(taxon_occ_result_df_duplicated):
        #     taxon_occ_remove_index = taxon_occ_result_df_duplicated[taxon_occ_result_df_duplicated.matched_col.isin(dup_col)].index
        #     taxon_occ_result_df = taxon_occ_result_df.loc[~taxon_occ_result_df.index.isin(taxon_occ_remove_index)]
        # 這邊要把兩種類型的資料加在一起
        taxon_occ_result_df = taxon_occ_result_df.rename(columns={'count': 'occ_count'})
        taxon_result_df = taxon_result_df.rename(columns={'count': 'col_count'})
        if len(taxon_occ_result_df) and len(taxon_result_df):
            taxon_result_df = taxon_occ_result_df.merge(taxon_result_df,how='left')
        elif len(taxon_occ_result_df) and not len(taxon_result_df):
            taxon_result_df = taxon_occ_result_df
            taxon_result_df['col_count'] = 0
        elif not len(taxon_occ_result_df) and len(taxon_result_df):
            taxon_result_df['occ_count'] = 0


        # 整理側邊欄
        taxon_rows = []
        taxon_card_len = 0
        if len(taxon_result_df):
            taxon_groupby = taxon_result_df.groupby('matched_col')['val'].nunique()
            for tt in taxon_groupby.index:
                taxon_rows.append({
                    'title': map_occurrence[tt],
                    'total_count': taxon_groupby[tt],
                    'key': tt
                })

            taxon_result_df = taxon_result_df.reset_index(drop=True)
            taxon_result_df_duplicated = taxon_result_df[taxon_result_df.duplicated(['val','col_count','occ_count'])]
            if len(taxon_result_df_duplicated):
                taxon_remove_index = taxon_result_df_duplicated[taxon_result_df_duplicated.matched_col.isin(dup_col)].index
                taxon_result_df = taxon_result_df.loc[~taxon_result_df.index.isin(taxon_remove_index)]

            taxon_card_len = len(taxon_result_df)

            taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=taxon_result_df[:4].val.unique()).values())
            taicol = taicol.rename(columns={'scientificName': 'name', 'scientificNameID': 'taxon_name_id'})


            taxon_result_df = pd.merge(taxon_result_df[:4],taicol,left_on='val',right_on='taxonID')
            taxon_result_df['val'] = taxon_result_df['formatted_name']
            taxon_result_df['key'] = taxon_result_df['matched_col']
            taxon_result_df['matched_col'] = taxon_result_df['matched_col'].apply(lambda x: map_collection[x])
            taxon_result_df['occ_count'] = taxon_result_df['occ_count'].replace({np.nan: 0})
            taxon_result_df['col_count'] = taxon_result_df['col_count'].replace({np.nan: 0})
            taxon_result_df.occ_count = taxon_result_df.occ_count.astype('int64')
            taxon_result_df.col_count = taxon_result_df.col_count.astype('int64')
            taxon_result_df = taxon_result_df.replace({np.nan: ''})

        # 照片
        # taxon_result_df['images'] = ''
        taxon_result_df = taxon_result_df.to_dict('records')
        taxon_result_dict = []
        for tr in taxon_result_df:
            if Namecode.objects.filter(taxon_name_id=tr['taxon_name_id']).exists():
                namecode = Namecode.objects.get(taxon_name_id=tr['taxon_name_id']).namecode
                url = 'https://data.taieol.tw/eol/endpoint/image/species/{}'.format(namecode)
                r = requests.get(url)
                img = r.json()
                images = []
                for ii in img:
                    foto = {'author':ii['author'], 'src':ii['image_big'], 'provider':ii['provider']}
                    images.append(foto)
                if images:
                    tr['images'] = images[0]
                url = 'https://data.taieol.tw/eol/endpoint/taxondesc/species/{}'.format(namecode)
                r = requests.get(url)
                data = r.json()
                if data:
                    if data.get('tid'):
                        tr['taieol_id'] = data.get('tid')
            taxon_result_dict.append(tr)
                # taxon_result_df.loc[i,'images'] = json.dumps(images)
            
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
        taxon_more = True if taxon_card_len > 4 else False


        response = {
            'taxon': {'rows': taxon_rows, 'count': taxon_card_len, 'card': taxon_result_dict,'more':taxon_more},
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
            'taxon': {'count': 0},
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
        # print(request.POST)
        keyword = request.POST.get('keyword', '')
        key = request.POST.get('key', '')
        value = request.POST.get('value', '')
        record_type = request.POST.get('record_type', '')
        scientific_name = request.POST.get('scientific_name', '')
        limit = int(request.POST.get('limit', -1))
        page = int(request.POST.get('page', 1))
        if request.POST.get('orderby'):
            orderby =  orderby = request.POST.get('orderby')
        else:
            orderby = 'scientificName'
        if request.POST.get('sort'):
            sort =  sort = request.POST.get('sort')
        else:
            sort = 'asc'
        # orderby = request.POST.get('orderby','scientificName')
        # sort = request.POST.get('sort', 'asc')

        # only facet selected field
        if record_type == 'col':
            map_dict = map_collection
            query_list = [('fq','recordType:col')]
            title = '自然史典藏'
            obv_str = '採集'
        else:
            map_dict = map_occurrence
            # core = 'tbia_occurrence'
            query_list = []
            title = '物種出現紀錄'
            obv_str = '紀錄'

        # key = get_key(key, map_dict)
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
        query_list += [('q', q),(key,value),('scientificName',scientific_name), ('rows', 10), ('offset', offset), ('sort', orderby + ' ' + sort)]
        # print(query_list)
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
                    docs.loc[i , 'date'] = f'---<br><small class="color-silver">[原始{obv_str}日期]' + docs.loc[i , 'eventDate'] + '</small>'
            # 經緯度
            user_id = request.user.id if request.user.id else 0
            if row.get('raw_location_rpt') and User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
                if lat := row.get('standardRawLatitude'):
                    docs.loc[i , 'lat'] = lat[0]
                else:
                    if row.get('verbatimRawLatitude'):
                        docs.loc[i , 'lat'] = '---<br><small class="color-silver">>[原始紀錄緯度]' + docs.loc[i , 'verbatimRawLatitude'] + '</small>'

                if lon := row.get('standardRawLongitude'):
                    docs.loc[i , 'lon'] = lon[0]
                else:
                    if row.get('verbatimRawLongitude'):
                        docs.loc[i , 'lon'] = '---<br><small class="color-silver">>[原始紀錄經度]' + docs.loc[i , 'verbatimRawLongitude'] + '</small>'
            else:
                if lat := row.get('standardLatitude'):
                    docs.loc[i , 'lat'] = lat[0]
                else:
                    if row.get('verbatimLatitude'):
                        docs.loc[i , 'lat'] = '---<br><small class="color-silver">>[原始紀錄緯度]' + docs.loc[i , 'verbatimLatitude'] + '</small>'

                if lon := row.get('standardLongitude'):
                    docs.loc[i , 'lon'] = lon[0]
                else:
                    if row.get('verbatimLongitude'):
                        docs.loc[i , 'lon'] = '---<br><small class="color-silver">>[原始紀錄經度]' + docs.loc[i , 'verbatimLongitude'] + '</small>'
            # 數量
            if quantity := row.get('standardOrganismQuantity'):
                docs.loc[i , 'quantity'] = int(quantity[0])
            else:
                if row.get('organismQuantity'):
                    docs.loc[i , 'quantity'] = '---<br><small class="color-silver">>[原始紀錄數量]' + docs.loc[i , 'organismQuantity'] + '</small>'

        docs = docs.replace({np.nan: ''})
        docs = docs.replace({'nan': ''})


        docs = docs.to_dict('records')

        current_page = offset / 10 + 1
        total_page = math.ceil(limit / 10)
        page_list = get_page_list(current_page, total_page)

        if request.POST.getlist('selected_col'):
            selected_col = request.POST.getlist('selected_col')
        else:
            selected_col = ['common_name_c','scientificName', 'recordedBy', 'rightsHolder']

        if orderby not in selected_col:
            selected_col.append(orderby)

        response = {
            'title': title,
            'orderby': orderby,
            'sort': sort,
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
        # print(request.POST)
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
            taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=result_df.val.unique()).values())
            taicol = taicol.rename(columns={'scientificName': 'name', 'scientificNameID': 'taxon_name_id'})

            result_df = pd.merge(result_df,taicol,left_on='val',right_on='taxonID')
            result_df['val'] = result_df['formatted_name']
            result_df['matched_value_ori'] = result_df['matched_value']
            result_df = result_df.replace({np.nan: ''})
            # result_df['val_ori'] = result_df['name']
            result_df['key'] = result_df['matched_col']
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


def get_focus_cards_taxon(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        record_type = request.POST.get('record_type', '')
        key = request.POST.get('key', '')
        
        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        q = f'{key}:/.*{keyword_reg}.*/' 

        title_prefix = '物種 > '

        map_dict = map_occurrence # occ或col沒有差別

        query = {
            "query": '',
            "filter": ['recordType:col'],
            "limit": 0,
            "facet": {},
            "sort":  "scientificName asc"
            }

        facet_list = {'facet': {k: v for k, v in occ_facets['facet'].items() if k == key} }
        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        query.update({'query': q})

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)

        taxon_result = []
        for i in facets:
            if i == key:
                x = facets[i]
                for k in x['buckets']:
                    bucket = k['taxonID']['buckets']
                    taxon_result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
        # 物種整理
        taxon_result_df = pd.DataFrame(taxon_result)

        # occurrence
        query.pop('filter', None)

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)
        
        taxon_result = []
        for i in facets:
            if i == key:
                x = facets[i]
                for k in x['buckets']:
                    bucket = k['taxonID']['buckets']
                    taxon_result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]

        # 物種整理
        taxon_occ_result_df = pd.DataFrame(taxon_result)

        # 這邊要把兩種類型的資料加在一起
        taxon_occ_result_df = taxon_occ_result_df.rename(columns={'count': 'occ_count'})
        taxon_result_df = taxon_result_df.rename(columns={'count': 'col_count'})

        if len(taxon_occ_result_df) and len(taxon_result_df):
            taxon_result_df = taxon_occ_result_df.merge(taxon_result_df,how='left')
        elif len(taxon_occ_result_df) and not len(taxon_result_df):
            taxon_result_df = taxon_occ_result_df
            taxon_result_df['col_count'] = 0
        elif not len(taxon_occ_result_df) and len(taxon_result_df):
            taxon_result_df['occ_count'] = 0


        taxon_card_len = len(taxon_result_df)
        if taxon_card_len:

            taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=taxon_result_df[:4].val.unique()).values())
            taicol = taicol.rename(columns={'scientificName': 'name', 'scientificNameID': 'taxon_name_id'})

            taxon_result_df = pd.merge(taxon_result_df[:4],taicol,left_on='val',right_on='taxonID')
            taxon_result_df['val'] = taxon_result_df['formatted_name']
            taxon_result_df['key'] = taxon_result_df['matched_col']
            taxon_result_df['matched_col'] = taxon_result_df['matched_col'].apply(lambda x: map_collection[x])
            taxon_result_df.occ_count = taxon_result_df.occ_count.replace({np.nan: 0}).astype('int64').apply(lambda x: f"{x:,}")
            taxon_result_df.col_count = taxon_result_df.col_count.replace({np.nan: 0}).astype('int64').apply(lambda x: f"{x:,}")
            taxon_result_df = taxon_result_df.replace({np.nan: ''})
            taxon_result_df['matched_value'] = taxon_result_df['matched_value'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['common_name_c'] = taxon_result_df['common_name_c'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['alternative_name_c'] = taxon_result_df['alternative_name_c'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['formatted_name'] = taxon_result_df['formatted_name'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['formatted_synonyms'] = taxon_result_df['formatted_synonyms'].apply(lambda x: highlight(x,keyword))

        # 照片
        taxon_result_df = taxon_result_df.to_dict('records')
        taxon_result_dict = []
        for tr in taxon_result_df:
            if Namecode.objects.filter(taxon_name_id=tr['taxon_name_id']).exists():
                namecode = Namecode.objects.get(taxon_name_id=tr['taxon_name_id']).namecode
                url = 'https://data.taieol.tw/eol/endpoint/image/species/{}'.format(namecode)
                r = requests.get(url)
                img = r.json()
                images = []
                for ii in img:
                    foto = {'author':ii['author'], 'src':ii['image_big'], 'provider':ii['provider']}
                    images.append(foto)
                if images:
                    tr['images'] = images[0]
                url = 'https://data.taieol.tw/eol/endpoint/taxondesc/species/{}'.format(namecode)
                r = requests.get(url)
                data = r.json()
                if data:
                    if data.get('tid'):
                        tr['taieol_id'] = data.get('tid')
            taxon_result_dict.append(tr)
        
        response = {
            'title': f"{title_prefix}{map_dict[key]}",
            'total_count': taxon_card_len,
            'item_class': f"item_{record_type}_{key}",
            'card_class': f"{record_type}-{key}-card",
            'data': taxon_result_df,
            'has_more': True if taxon_card_len > 4 else False
        }

        return HttpResponse(json.dumps(response), content_type='application/json')


# TODO
def get_more_cards_taxon(request):
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

        # taxon 跟 occ 都算在這裡
        facet_list = occ_facets
        map_dict = map_occurrence

        keyword_reg = ''
        q = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)
        
        if is_sub == 'true':
            facet_list = {'facet': {k: v for k, v in occ_facets['facet'].items() if k == key} }

        for i in facet_list['facet']:
            q += f'{i}:/.*{keyword_reg}.*/ OR ' 
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})

        query.update(facet_list)
        query.update({'query': q[:-4]})

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)      

        taxon_result = []
        if is_sub == 'false':
            for i in facets:
                x = facets[i]
                for k in x['buckets']:
                    bucket = k['taxonID']['buckets']
                    taxon_result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
        else:
            x = facets[key]
            for k in x['buckets']:
                bucket = k['taxonID']['buckets']
                taxon_result += [dict(item, **{'matched_value':k['val'], 'matched_col': key}) for item in bucket]
        taxon_result_df = pd.DataFrame(taxon_result)

        # occurrence
        query.pop('filter', None)

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)

        taxon_result = []
        if is_sub == 'false':
            for i in facets:
                x = facets[i]
                for k in x['buckets']:
                    bucket = k['taxonID']['buckets']
                    taxon_result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
        else:
            x = facets[key]
            for k in x['buckets']:
                bucket = k['taxonID']['buckets']
                taxon_result += [dict(item, **{'matched_value':k['val'], 'matched_col': key}) for item in bucket]

        taxon_occ_result_df = pd.DataFrame(taxon_result)

        # 這邊要把兩種類型的資料加在一起
        taxon_occ_result_df = taxon_occ_result_df.rename(columns={'count': 'occ_count'})
        taxon_result_df = taxon_result_df.rename(columns={'count': 'col_count'})

        if len(taxon_occ_result_df) and len(taxon_result_df):
            taxon_result_df = taxon_occ_result_df.merge(taxon_result_df,how='left')
        elif len(taxon_occ_result_df) and not len(taxon_result_df):
            taxon_result_df = taxon_occ_result_df
            taxon_result_df['col_count'] = 0
        elif not len(taxon_occ_result_df) and len(taxon_result_df):
            taxon_result_df['occ_count'] = 0

        taxon_result_df = taxon_result_df.reset_index(drop=True)
        if is_sub == 'false':
            taxon_result_df_duplicated = taxon_result_df[taxon_result_df.duplicated(['val','col_count','occ_count'])]
            if len(taxon_result_df_duplicated):
                taxon_remove_index = taxon_result_df_duplicated[taxon_result_df_duplicated.matched_col.isin(dup_col)].index
                taxon_result_df = taxon_result_df.loc[~taxon_result_df.index.isin(taxon_remove_index)]

        taxon_card_len = len(taxon_result_df[offset:])
        if taxon_card_len:
            if offset >= 28:
                taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=taxon_result_df[offset:offset+2].val.unique()).values())
            else:
                taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=taxon_result_df[offset:offset+4].val.unique()).values())
            taicol = taicol.rename(columns={'scientificName': 'name', 'scientificNameID': 'taxon_name_id'})

            if offset >= 28:
                taxon_result_df = pd.merge(taxon_result_df[offset:offset+2],taicol,left_on='val',right_on='taxonID')
            else:
                taxon_result_df = pd.merge(taxon_result_df[offset:offset+4],taicol,left_on='val',right_on='taxonID')
            taxon_result_df['val'] = taxon_result_df['formatted_name']
            taxon_result_df['key'] = taxon_result_df['matched_col']
            taxon_result_df['matched_col'] = taxon_result_df['matched_col'].apply(lambda x: map_collection[x])
            taxon_result_df.occ_count = taxon_result_df.occ_count.replace({np.nan: 0}).astype('int64').apply(lambda x: f"{x:,}")
            taxon_result_df.col_count = taxon_result_df.col_count.replace({np.nan: 0}).astype('int64').apply(lambda x: f"{x:,}")
            taxon_result_df = taxon_result_df.replace({np.nan: ''})
            taxon_result_df['matched_value'] = taxon_result_df['matched_value'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['common_name_c'] = taxon_result_df['common_name_c'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['alternative_name_c'] = taxon_result_df['alternative_name_c'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['formatted_name'] = taxon_result_df['formatted_name'].apply(lambda x: highlight(x,keyword))
            taxon_result_df['formatted_synonyms'] = taxon_result_df['formatted_synonyms'].apply(lambda x: highlight(x,keyword))

        # 照片
        taxon_result_df = taxon_result_df.to_dict('records')
        taxon_result_dict = []
        for tr in taxon_result_df:
            if Namecode.objects.filter(taxon_name_id=tr['taxon_name_id']).exists():
                namecode = Namecode.objects.get(taxon_name_id=tr['taxon_name_id']).namecode
                url = 'https://data.taieol.tw/eol/endpoint/image/species/{}'.format(namecode)
                r = requests.get(url)
                img = r.json()
                images = []
                for ii in img:
                    foto = {'author':ii['author'], 'src':ii['image_big'], 'provider':ii['provider']}
                    images.append(foto)
                if images:
                    tr['images'] = images[0]
                url = 'https://data.taieol.tw/eol/endpoint/taxondesc/species/{}'.format(namecode)
                r = requests.get(url)
                data = r.json()
                if data:
                    if data.get('tid'):
                        tr['taieol_id'] = data.get('tid')
            taxon_result_dict.append(tr)
        
        response = {
            'data': taxon_result_dict,
            'has_more': True if taxon_card_len > 4 else False,
            'reach_end': True if offset >= 28 else False
        }

        return HttpResponse(json.dumps(response), content_type='application/json')


# TODO
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
        else: # taxon 跟 occ 都算在這裡
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
                    if card_class.startswith('.taxon'):
                        if i in taxon_cols:
                            for item in bucket:
                                if dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in result:
                                    result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i}))
                            # result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
                    else:
                        if i == 'eventDate':
                            if f_date := convert_date(k['val']):
                                f_date = f_date.strftime('%Y-%m-%d %H:%M:%S')
                                for item in bucket:
                                    if dict(item, **{'matched_value':f_date, 'matched_col': i}) not in result:
                                        result.append(dict(item, **{'matched_value': f_date, 'matched_col': i}))
                                # result += [dict(item, **{'matched_value':f_date, 'matched_col': i}) for item in bucket]
                        else:
                            for item in bucket:
                                if dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in result:
                                    result.append(dict(item, **{'matched_value':k['val'], 'matched_col': i}))
                            # result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
            result_df = pd.DataFrame(result)
            # result_df_duplicated = result_df[result_df.duplicated(['val','count'])]
            # if len(result_df_duplicated):
            #     remove_index = result_df_duplicated[result_df_duplicated.matched_col.isin(dup_col)].index
            #     result_df = result_df.loc[~result_df.index.isin(remove_index)]
        else:
            x = facets[key]
            for k in x['buckets']:
                bucket = k['taxonID']['buckets']
                if i == 'eventDate':
                    if f_date := convert_date(k['val']):
                        f_date = f_date.strftime('%Y-%m-%d %H:%M:%S')
                        for item in bucket:
                            if dict(item, **{'matched_value':f_date, 'matched_col': key}) not in result:
                                result.append(dict(item, **{'matched_value':f_date, 'matched_col': key}))
                        # result += [dict(item, **{'matched_value':f_date, 'matched_col': key}) for item in bucket]
                else:
                    for item in bucket:
                        if dict(item, **{'matched_value':k['val'], 'matched_col': i}) not in result:
                            result.append(dict(item, **{'matched_value':k['val'], 'matched_col': key}))
                    # result += [dict(item, **{'matched_value':k['val'], 'matched_col': key}) for item in bucket]
            result_df = pd.DataFrame(result)

        if len(result_df):
            card_len = len(result_df[offset:])
            if offset >= 27:
                result_df = result_df[offset:offset+3]
            else:
                result_df = result_df[offset:offset+9]
            taicol = pd.DataFrame(Taxon.objects.filter(taxonID__in=result_df.val.unique()).values())
            taicol = taicol.rename(columns={'scientificName': 'name', 'scientificNameID': 'taxon_name_id'})

            result_df = pd.merge(result_df,taicol,left_on='val',right_on='taxonID')
            result_df['val'] = result_df['formatted_name']
            result_df['key'] = result_df['matched_col']
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
            'has_more': True if card_len > 9 else False,
            'reach_end': True if offset >= 27 else False
        }

        return HttpResponse(json.dumps(response), content_type='application/json')


def search_collection(request):

    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0&fq=recordType:col')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list = [f_list[x] for x in range(0, len(f_list),2)]
    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=datasetName&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
    # d_list = response.json()['facet_counts']['facet_fields']['datasetName']
    # dataset_list = [d_list[x] for x in range(0, len(d_list),2)]
    dataset_list = DatasetKey.objects.filter(record_type='col')

    sensitive_list = ['輕度', '重度', '縣市', '座標不開放', '物種不開放', '無']
    rank_list = [('界', 'kingdom'), ('門', 'phylum'), ('綱', 'class'), ('目', 'order'), ('科', 'family'), ('屬', 'genus'), ('種', 'species')]

    return render(request, 'pages/search_collection.html', {'holder_list': holder_list, 'sensitive_list': sensitive_list,
        'rank_list': rank_list, 'dataset_list': dataset_list})
    

def search_occurrence(request):

    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list = [f_list[x] for x in range(0, len(f_list),2)]
    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=datasetName&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
    # d_list = response.json()['facet_counts']['facet_fields']['datasetName']
    # dataset_list = [d_list[x] for x in range(0, len(d_list),2)]
    dataset_list = DatasetKey.objects.filter(record_type='occ')
    # holder_list = ['TBN','TaiBIF','林試所','林務局','海保署']
    sensitive_list = ['輕度', '重度', '縣市', '座標不開放', '物種不開放', '無'] # TODO 物種不開放僅開放有權限的人查詢
    rank_list = [('界', 'kingdom'), ('門', 'phylum'), ('綱', 'class'), ('目', 'order'), ('科', 'family'), ('屬', 'genus'), ('種', 'species')]
    basis_list = basis_dict.values()
        
    return render(request, 'pages/search_occurrence.html', {'holder_list': holder_list, 'sensitive_list': sensitive_list,
        'rank_list': rank_list, 'basis_list': basis_list, 'dataset_list': dataset_list})


def occurrence_detail(request, id):
    solr = SolrQuery('tbia_records')
    logo = ''
    query_list = [('id', id), ('row',1)]
    req = solr.request(query_list)
    row = pd.DataFrame(req['solr_response']['response']['docs'])
    row = row.replace({np.nan: ''})
    row = row.replace({'nan': ''})
    row = row.to_dict('records')
    row = row[0]

    if row.get('taxonRank', ''):
        row.update({'taxonRank': map_occurrence[row['taxonRank']]})

    if am := row.get('associatedMedia'):
        row.update({'associatedMedia': am.split(';')})

    # print(row.get('dataGeneralizations'))
    if str(row.get('dataGeneralizations')):
        if row['dataGeneralizations'] in ['True', True]:
            row.update({'dataGeneralizations': '是'})
        elif row['dataGeneralizations'] in ['False', False]:
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
    user_id = request.user.id if request.user.id else 0
    if row.get('raw_location_rpt') and User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
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
        quantity = int(quantity[0])
    else:
        quantity = None
    row.update({'quantity': quantity})

    # taxon
    path_str = ''
    path = []
    if row.get('taxonID'):
        path_taxon_id = row.get('taxonID')
    elif row.get('parentTaxonID'):
        path_taxon_id = row.get('parentTaxonID')
    if path_taxon_id:
        if Taxon.objects.filter(taxonID=path_taxon_id).exists():
            t_rank = Taxon.objects.filter(taxonID=path_taxon_id).values()[0]
            for r in rank_list:
                if t_rank.get(r):
                    if t_rank.get(f"formatted_{r}"):
                        current_str = t_rank.get(f"formatted_{r}")
                    else:
                        current_str = t_rank.get(r)
                    if t_rank.get(f"{r}_c"):
                        current_str += ' ' + t_rank.get(f"{r}_c")
                    path.append(current_str)

    path_str = ' > '.join(path)

    # logo
    if group := row.get('group'):
        if logo := Partner.objects.filter(group=group).values('logo'):
            # info = info[0]
            # for i in info['info']:
            #     if i.get('subtitle') == row.get('rightsHolder'):
            logo = logo[0]['logo']

    return render(request, 'pages/occurrence_detail.html', {'row': row, 'path_str': path_str, 'logo': logo})


def collection_detail(request, id):
    path_str = ''
    logo = ''
    solr = SolrQuery('tbia_records')
    query_list = [('id', id), ('row',1)]
    req = solr.request(query_list)
    row = pd.DataFrame(req['solr_response']['response']['docs'])
    row = row.replace({np.nan: ''})
    row = row.replace({'nan': ''})
    row = row.to_dict('records')
    row = row[0]
    if row.get('recordType') == ['col']:

        if am := row.get('associatedMedia'):
            row.update({'associatedMedia': am.split(';')})

        if row.get('taxonRank', ''):
            row.update({'taxonRank': map_collection[row['taxonRank']]})

        if str(row.get('dataGeneralizations')):
            if row['dataGeneralizations'] in ['True', True]:
                row.update({'dataGeneralizations': '是'})
            elif row['dataGeneralizations'] in ['False', False]:
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

        # 如果是夥伴單位直接給原始
        user_id = request.user.id if request.user.id else 0
        if row.get('raw_location_rpt') and User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
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
            quantity = int(quantity[0])
        else:
            quantity = None
        row.update({'quantity': quantity})

        # taxon
        path = []
        
        if row.get('taxonID'):
            path_taxon_id = row.get('taxonID')
        elif row.get('parentTaxonID'):
            path_taxon_id = row.get('parentTaxonID')
        if path_taxon_id:
            if Taxon.objects.filter(taxonID=path_taxon_id).exists():
                t_rank = Taxon.objects.filter(taxonID=path_taxon_id).values()[0]
                for r in rank_list:
                    if t_rank.get(r):
                        if t_rank.get(f"formatted_{r}"):
                            current_str = t_rank.get(f"formatted_{r}")
                        else:
                            current_str = t_rank.get(r)
                        if t_rank.get(f"{r}_c"):
                            current_str += ' ' + t_rank.get(f"{r}_c")
                        path.append(current_str)
                        
        path_str = ' > '.join(path)

        # logo
        if group := row.get('group'):
            if logo := Partner.objects.filter(group=group).values('logo'):
                # info = info[0]
                # for i in info['info']:
                #     if i.get('subtitle') == row.get('rightsHolder'):
                logo = logo[0]['logo']

    else:
        row = []

    return render(request, 'pages/collection_detail.html', {'row': row, 'path_str': path_str, 'logo': logo})




def get_conditional_records(request):
    if request.method == 'POST':
        limit = int(request.POST.get('limit', 10))
        orderby = request.POST.get('orderby','scientificName')
        sort = request.POST.get('sort', 'asc')
        
        map_geojson = {}
        map_geojson[f'grid_1'] = {"type":"FeatureCollection","features":[]}
        map_geojson[f'grid_5'] = {"type":"FeatureCollection","features":[]}
        map_geojson[f'grid_10'] = {"type":"FeatureCollection","features":[]}
        map_geojson[f'grid_100'] = {"type":"FeatureCollection","features":[]}

        # selected columns
        if request.POST.getlist('selected_col'):
            selected_col = request.POST.getlist('selected_col')
        else:
            selected_col = ['common_name_c','scientificName', 'recordedBy', 'eventDate', 'rightsHolder']

        if orderby not in selected_col:
            selected_col.append(orderby)
        # use JSON API to avoid overlong query url
        query_list = []

        record_type = request.POST.get('record_type')
        if record_type == 'col': # occurrence include occurrence + collection
            query_list += ['recordType:col']
            map_dict = map_collection
            obv_str = '採集'
        else:
            map_dict = map_occurrence
            obv_str = '紀錄'

        for i in ['locality', 'recordedBy', 'resourceContacts', 'taxonID', 'preservation']:
            if val := request.POST.get(i):
                if val != 'undefined':
                    val = val.strip()
                    keyword_reg = ''
                    for j in val:
                        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
                    if i in ['locality', 'recordedBy', 'resourceContacts', 'preservation']:
                        keyword_reg = get_variants(keyword_reg)
                    query_list += [f'{i}:/.*{keyword_reg}.*/']
        
        if quantity := request.POST.get('organismQuantity'):
            query_list += [f'standardOrganismQuantity: {quantity}']

        # 下拉選單單選
        for i in ['sensitiveCategory', 'taxonRank','typeStatus','rightsHolder','basisOfRecord']: 
            if val := request.POST.get(i):
                if i == 'sensitiveCategory' and val == '無':
                    query_list += [f'-(-{i}:{val} {i}:*)']
                else:
                    query_list += [f'{i}:{val}']

        # 下拉選單多選
        d_list = []
        if val := request.POST.getlist('datasetName'):
            for v in val:
                if DatasetKey.objects.filter(id=v).exists():
                    d_list.append(DatasetKey.objects.get(id=v).name)
        
        if d_list:
            d_list_str = '" OR "'.join(d_list)
            query_list += [f'datasetName:("{d_list_str}")']

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

        if g_id := request.POST.get('geojson_id'):
            try:
                with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
                    geojson = json.loads(j.read())
            except:
                pass

        if circle_radius := request.POST.get('circle_radius'):
            query_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (request.POST.get('center_lat'), request.POST.get('center_lon'), int(circle_radius))]

        if g_list := request.POST.getlist('polygon'):
            try:
                mp = MultiPolygon(map(wkt.loads, g_list))
                query_list += ['{!field f=location_rpt}Intersects(%s)' % mp]
            except:
                pass

        if geojson['features']:
            geo_df = gpd.GeoDataFrame.from_features(geojson)
            g_list = []
            for i in geo_df.to_wkt()['geometry']:
                query_list += ['{!field f=location_rpt}Intersects(%s)' % i]

        if val := request.POST.get('name'):
            val = val.strip()
            # 去除重複空格
            val = re.sub(' +', ' ', val)
            # 去除特殊字元
            val = re.sub('[,，!！?？&＆~～@＠#＃$＄%％^＾*＊()（）、]', '', val)
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
            offset = (page-1)*limit

            query = { "query": "*:*",
                    "offset": offset,
                    "limit": limit,
                    "filter": query_list,
                    "sort":  orderby + ' ' + sort,
                    }

            query2 = { "query": "raw_location_rpt:[* TO *]",
                    "offset": 0,
                    "limit": 0,
                    "filter": query_list,
                    }
            # print()
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
                            # print(current_grid_x, current_grid_y)
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
            response2 = requests.post(f'{SOLR_PREFIX}tbia_records/select?', data=json.dumps(query2), headers={'content-type': "application/json" })
            if response2.json()['response']['numFound'] > 0:
                has_sensitive = True
            else:
                has_sensitive = False


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
                        docs.loc[i , 'eventDate'] = f'---<br><small class="color-silver">>[原始{obv_str}日期]' + docs.loc[i , 'eventDate'] + '</small>'

                #     # date = date[0].replace('T', ' ').replace('Z','')
                #     # 如果是國家公園，原本調查的時間是區段
                #     if row.get('rightsHolder') == '臺灣國家公園生物多樣性資料庫':
                #         docs.loc[i , 'eventDate'] = date[0].split('T')[0] # 只取日期
                #     else:
                #         docs.loc[i , 'eventDate'] = date[0].replace('T', ' ').replace('Z','')
                # else:
                    # if row.get('eventDate'):
                    #     docs.loc[i , 'eventDate'] = '---<br><small class="color-silver">>[原始紀錄日期]' + docs.loc[i , 'eventDate'] + '</small>'
                # 經緯度
                # 如果是夥伴單位直接給原始
                user_id = request.user.id if request.user.id else 0
                if row.get('raw_location_rpt') and User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
                    if lat := row.get('standardRawLatitude'):
                        docs.loc[i , 'verbatimRawLatitude'] = lat[0]
                    else:
                        if row.get('verbatimRawLatitude'):
                            docs.loc[i , 'verbatimRawLatitude'] = '---<br><small class="color-silver">>[原始紀錄緯度]' + docs.loc[i , 'verbatimRawLatitude'] + '</small>'

                    if lon := row.get('standardRawLongitude'):
                        docs.loc[i , 'verbatimRawLongitude'] = lon[0]
                    else:
                        if row.get('verbatimRawLongitude'):
                            docs.loc[i , 'verbatimRawLongitude'] = '---<br><small class="color-silver">>[原始紀錄經度]' + docs.loc[i , 'verbatimRawLongitude'] + '</small>'
                else:
                    if lat := row.get('standardLatitude'):
                        docs.loc[i , 'verbatimLatitude'] = lat[0]
                    else:
                        if row.get('verbatimLatitude'):
                            docs.loc[i , 'verbatimLatitude'] = '---<br><small class="color-silver">>[原始紀錄緯度]' + docs.loc[i , 'verbatimLatitude'] + '</small>'

                    if lon := row.get('standardLongitude'):
                        docs.loc[i , 'verbatimLongitude'] = lon[0]
                    else:
                        if row.get('verbatimLongitude'):
                            docs.loc[i , 'verbatimLongitude'] = '---<br><small class="color-silver">>[原始紀錄經度]' + docs.loc[i , 'verbatimLongitude'] + '</small>'
                # 數量
                if quantity := row.get('standardOrganismQuantity'):
                    docs.loc[i , 'standardOrganismQuantity'] = int(quantity[0])
                else:
                    if row.get('organismQuantity'):
                        docs.loc[i , 'organismQuantity'] = '---<br><small class="color-silver">>[原始紀錄數量]' + docs.loc[i , 'organismQuantity'] + '</small>'

            docs = docs.replace({np.nan: ''})
            docs = docs.replace({'nan': ''})
            
            docs = docs.to_dict('records')

            current_page = offset / limit + 1
            total_page = math.ceil(count / limit)
            page_list = get_page_list(current_page, total_page)

            response = {
                'rows' : docs,
                'count': count,
                'page_list': page_list,
                'current_page' : current_page,
                'total_page' : total_page,
                'selected_col': selected_col,
                'map_dict': map_dict,
                'map_geojson': map_geojson,
                'has_sensitive': has_sensitive,
                'limit': limit,
                'orderby': orderby,
                'sort': sort,
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
                'limit': 10,
                'orderby': orderby,
                'sort': sort,
            }

        return HttpResponse(json.dumps(response, default=str), content_type='application/json')
