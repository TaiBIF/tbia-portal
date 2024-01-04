from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT, MEDIA_ROOT, SOLR_PREFIX
from conf.utils import scheme
from pages.models import Resource, News
from django.db.models import Q, Max
from django.db import connection

from data.utils import *
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
from pages.templatetags.tags import highlight, get_variants
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
import threading
from manager.models import SearchQuery, User, SensitiveDataRequest, SensitiveDataResponse, Partner
from pages.models import Notification
from urllib import parse
from manager.views import send_notification
from django.utils import timezone
from os.path import exists
# from data.models import Namecode, Taxon , DatasetKey
import html
from django.utils.translation import get_language, gettext



def get_geojson(request,id):
    if SearchQuery.objects.filter(id=id).exists():
        sq = SearchQuery.objects.get(id=id)
        search_dict = dict(parse.parse_qsl(sq.query))
        map_json = search_dict.get('geojson')
        response = HttpResponse(map_json, content_type='application/json')
        response['Content-Disposition'] = 'attachment; filename="geojson.json"'
        return response


# 全站搜尋資料分布圖
def get_taxon_dist_init(request):
    taxon_id = request.POST.get('taxonID')
    query_list = [f'taxonID:{taxon_id}','-standardOrganismQuantity:0']


    map_query = {"query": "*:*",
            "offset": 0,
            "limit": 0,
            "filter": query_list}
    
    user_id = request.user.id if request.user.id else 0
    
    map_geojson = get_map_response(map_query=map_query, grid_list=[10, 100], get_raw_map=if_raw_map(user_id))

    return HttpResponse(json.dumps(map_geojson, default=str), content_type='application/json')


# 全站搜尋資料分布圖
def get_taxon_dist(request):

    taxon_id = request.POST.get('taxonID')
    grid = int(request.POST.get('grid'))

    user_id = request.user.id if request.user.id else 0
    
    get_raw_map = if_raw_map(user_id)


    user_id = request.user.id if request.user.id else 0
    get_raw_map =  if_raw_map(user_id)

    map_bound = check_map_bound(request.POST.get('map_bound'))
    
    if get_raw_map:
        query_list = [f"location_rpt:{map_bound} OR raw_location_rpt:{map_bound}"]
        query_list += [ f'taxonID:{taxon_id}','-standardOrganismQuantity:0'] 
    else:
        query_list = [f"location_rpt:{map_bound}"]
        query_list += [ f'taxonID:{taxon_id}','-standardOrganismQuantity:0'] 

    map_query = {"query": "*:*",
            "offset": 0,
            "limit": 0,
            "filter": query_list}
    
    map_geojson = get_map_response(map_query=map_query, grid_list=[grid], get_raw_map=get_raw_map)
    map_geojson = map_geojson[f'grid_{grid}']
    
    return HttpResponse(json.dumps(map_geojson, default=str), content_type='application/json')


def sensitive_agreement(request):
    return render(request, 'pages/agreement.html')


def send_sensitive_request(request):
    if request.method == 'GET':
        # 整理搜尋條件
        search_dict = {}
        for k in request.GET.keys():
            if k != 'lang':
                if tmp_list := request.GET.getlist(k):
                    if len(tmp_list) > 1:
                        search_dict[k] = tmp_list
                    else:
                        search_dict[k] = request.GET.get(k)
        lang = request.GET.get('lang')
        query = create_query_display(search_dict, lang)
        return render(request, 'pages/application.html', {'query': query})


def submit_sensitive_request(request):
    if request.method == 'POST':
        req_dict = dict(request.POST)
        not_query = ['selected_col','applicant','phone','address','affiliation','type','project_name','project_affiliation','abstract','users','csrfmiddlewaretoken','page','from','grid','map_bound']
        for nq in not_query:
            if nq in req_dict.keys():
                req_dict.pop(nq)
        for k in req_dict.keys():
            if len(req_dict[k])==1:
                req_dict[k] = req_dict[k][0]

        query_string = parse.urlencode(req_dict)
        user_id = request.user.id
        query_id = str(ObjectId())

        current_personal_id = SearchQuery.objects.filter(user_id=user_id,type='sensitive').aggregate(Max('personal_id'))
        current_personal_id = current_personal_id.get('personal_id__max') + 1 if current_personal_id.get('personal_id__max') else 1
        
        sq = SearchQuery.objects.create(
            user = User.objects.filter(id=user_id).first(),
            query = query_string,
            status = 'pending', # 如果單位都同意,檔案也製作好,這邊才會變成pass
            type = 'sensitive',
            query_id = query_id,
            personal_id = current_personal_id
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

            query_list = create_search_query(req_dict=req_dict, from_request=False, get_raw_map=True)

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
            if not query_list:
                query.pop('filter')

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
        task = threading.Thread(target=generate_sensitive_csv, args=(request.POST.get('query_id'),scheme,request.get_host()))
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

            query_list = create_search_query(req_dict=req_dict, from_request=False, get_raw_map=True)

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

            if not query_list:
                query.pop('filter')

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

    return JsonResponse({"status": 'success'}, safe=False)


def generate_sensitive_csv(query_id, scheme, host):
    
    if SearchQuery.objects.filter(query_id=query_id).exists():
        sq = SearchQuery.objects.get(query_id=query_id)
        req_dict = dict(parse.parse_qsl(sq.query))

        download_id = f"tbia_{query_id}"

        group = []
        process = None
        file_done = False

        if SensitiveDataResponse.objects.filter(query_id=query_id,status='pass').exclude(is_transferred=True,partner_id__isnull=True).exists():
        #     group = ['*']
        # elif SensitiveDataResponse.objects.filter(query_id=query_id,status='fail',is_transferred=False, partner_id=None).exists():
        #     group = []
        # else:
            # 不給沒通過的
            # 如果是機關委託計畫的話 則全部都給
            ps = list(SensitiveDataResponse.objects.filter(query_id=query_id,status='fail').values_list('partner_id'))
            if ps:
                ps = [p for p in ps[0]]
                group = list(Partner.objects.filter(id__in=ps).values_list('group'))
                group = [g for g in group[0]]

            fl_cols = download_cols + sensitive_cols
            # 先取得筆數，export to csv

            query_list = create_search_query(req_dict=req_dict, from_request=False, get_raw_map=True)

            # 排除掉不同意的單位
            if group:
                group = [ f'group:{g}' for g in group ]
                group_str = ' OR '.join( group )
                query_list += [ '-(' + group_str + ')' ]
            # 

            query = { "query": "*:*",
                    "offset": 0,
                    # "limit": req_dict.get('total_count'),
                    "limit": 2140000000,
                    "filter": query_list,
                    "sort":  "scientificName asc",
                    "fields": fl_cols
                    }

            if not query_list:
                query.pop('filter')

            csv_folder = os.path.join(MEDIA_ROOT, 'download')
            csv_folder = os.path.join(csv_folder, 'sensitive')
            csv_file_path = os.path.join(csv_folder, f'{download_id}.csv')
            zip_file_path = os.path.join(csv_folder, f'{download_id}.zip')
            solr_url = f"{SOLR_PREFIX}tbia_records/select?wt=csv"

            # 等待檔案完成

            commands = f"curl -X POST {solr_url} -d '{json.dumps(query)}' > {csv_file_path}; zip -j {zip_file_path} {csv_file_path}; rm {csv_file_path}"
            process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.communicate()

            file_done = True

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

        else:
            # 沒有帳號通過
            sq.status = 'fail'
            sq.modified = timezone.now()
            sq.save()
            file_done = True


        if file_done:
            nn = Notification.objects.create(
                type = 4,
                content = sq.personal_id,
                user_id = sq.user_id
            )
            content = nn.get_type_display().replace('0000', str(nn.content))
            # content_en = gettext(nn.get_type_display()).replace('0000', str(nn.content))
            content_en = f'The review of one-time sensitive data #{str(nn.content)} is finished. The review comments are as follows:<br><br>'

            # 審查意見
            comment = []
            comment_en = [] # 英文版

            for sdr in SensitiveDataResponse.objects.filter(query_id=query_id).exclude(is_transferred=True, partner_id__isnull=True):
                if sdr.partner:
                    partner_name = sdr.partner.select_title 
                    partner_name_en = sdr.partner.select_title_en
                else:
                    partner_name = 'TBIA 臺灣生物多樣性資訊聯盟'
                    partner_name_en = 'Taiwan Biodiversity Information Alliance'
                comment.append(
                f"""
                <b>審查單位：</b>{partner_name}
                <br>
                <b>審查者姓名：</b>{sdr.reviewer_name}
                <br>
                <b>審查意見：</b>{sdr.comment if sdr.comment else "" }
                <br>
                <b>審查結果：</b>{sdr.get_status_display()}
                """)

                comment_en.append(
                f"""
                <b>Reviewing Agency:</b> {partner_name_en}
                <br>
                <b>Reviewer:</b> {sdr.reviewer_name}
                <br>
                <b>Review Comments:</b> {sdr.comment if sdr.comment else "" }
                <br>
                <b>Review Outcome:</b> {sdr.status.capitalize()}
                """)

            comment = '<hr>'.join(comment) if comment else ''
            comment_en = '<hr>'.join(comment_en) if comment_en else ''
            content = content.replace('請至後台查看','審查意見如下：<br><br>')
            # content_en = content_en.replace(' Check your account panel.','The review comments are as follows:<br><br>')
            content += comment
            content_en += comment_en
            if sq.status == 'pass':
                content += f"<br><br>檔案下載連結：{scheme}://{host}/media/download/sensitive/{download_id}.zip"
                content_en += f"<br><br>Download Link: {scheme}://{host}/media/download/sensitive/{download_id}.zip"
            send_notification([sq.user_id],content,'單次使用敏感資料申請結果通知 Your application of non-blurred sensitive data for one-time use is completed',
                              content_en=content_en)



def save_geojson(request):
    if request.method == 'POST':
        geojson = request.POST.get('geojson_text')
        geojson = gpd.read_file(geojson, driver='GeoJSON')
        # geojson = geojson.dissolve()
        geojson = geojson.to_json()

        oid = str(ObjectId())
        with open(f'/tbia-volumes/media/geojson/{oid}.json', 'w') as f:
            json.dump(json.loads(geojson), f)
        return JsonResponse({"geojson_id": oid, "geojson": geojson}, safe=False)


import shapely

def return_geojson_query(request):
    if request.method == 'POST':
        geojson = request.POST.get('geojson_text')
        geojson = gpd.read_file(geojson, driver='GeoJSON')
        geojson = shapely.force_2d(geojson) # remove z coordinates

    # geo_df = gpd.GeoDataFrame.from_features(geojson)
        g_list = []
        if len(geojson):
            g_list = geojson.geometry.values[0]
        # for i in geojson.to_wkt()['geometry']:
        #     if str(i).startswith('POLYGON'):
        #         g_list += [i]
        # print(g_list)
        return JsonResponse({"polygon": [str(g_list)]}, safe=False)

def send_download_request(request):
    if request.method == 'POST':
        if request.POST.get('from_full'):
            task = threading.Thread(target=generate_download_csv_full, args=(request.POST, request.user.id, scheme, request.get_host()))
            task.start()
        elif request.POST.get('taxon'):
            task = threading.Thread(target=generate_species_csv, args=(request.POST, request.user.id, scheme, request.get_host()))
            task.start()
        else:
            task = threading.Thread(target=generate_download_csv, args=(request.POST, request.user.id, scheme, request.get_host()))
            task.start()
        return JsonResponse({"status": 'success'}, safe=False)


# 進階搜尋資料下載
def generate_download_csv(req_dict, user_id, scheme, host):
    download_id = f"tbia_{str(ObjectId())}"

    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
        fl_cols = download_cols + sensitive_cols
    else:
        fl_cols = download_cols

    get_raw_map = if_raw_map(user_id)

    query_list = create_search_query(req_dict=req_dict, from_request=True, get_raw_map=get_raw_map)

    req_dict = dict(req_dict)
    not_query = ['csrfmiddlewaretoken','page','from','taxon','selected_col','map_bound','grid']
    for nq in not_query:
        if nq in req_dict.keys():
            req_dict.pop(nq)
    for k in req_dict.keys():
        if len(req_dict[k])==1:
            req_dict[k] = req_dict[k][0]
    query_string = parse.urlencode(req_dict)

    current_personal_id = SearchQuery.objects.filter(user_id=user_id,type='record').aggregate(Max('personal_id'))
    current_personal_id = current_personal_id.get('personal_id__max') + 1 if current_personal_id.get('personal_id__max') else 1

    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'record',
        query_id = download_id.split('_')[-1],
        personal_id = current_personal_id
    )

    # 

    query = { "query": "*:*",
            "offset": 0,
            # "limit": req_dict.get('total_count'),
            "limit": 2140000000,
            "filter": query_list,
            "sort":  "scientificName asc",
            "fields": fl_cols
            }

    if not query_list:
        query.pop('filter')
    
    csv_folder = os.path.join(MEDIA_ROOT, 'download')
    csv_folder = os.path.join(csv_folder, 'record')
    csv_file_path = os.path.join(csv_folder, f'{download_id}.csv')
    zip_file_path = os.path.join(csv_folder, f'{download_id}.zip')
    solr_url = f"{SOLR_PREFIX}tbia_records/select?wt=csv"
    
    # 等待檔案完成
    commands = f"curl -X POST {solr_url} -d '{json.dumps(query)}' > {csv_file_path}; zip -j {zip_file_path} {csv_file_path}; rm {csv_file_path}"
    process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate()

    # 儲存到下載統計
    sq.status = 'pass'
    sq.modified = timezone.now()
    sq.save()

    # 寄送通知
    nn = Notification.objects.create(
        type = 1,
        content = sq.personal_id,
        user_id = user_id
    )
    content = nn.get_type_display().replace('0000', str(nn.content))
    content_en = f'The download of records #{str(nn.content)} is ready.<br><br>Download Link: ' + f"{scheme}://{host}/media/download/record/{download_id}.zip <br>"
    content = content.replace("請至後台查看", "")
    content += f"<br><br>檔案下載連結：{scheme}://{host}/media/download/record/{download_id}.zip <br>"
    send_notification([user_id],content,'下載資料已完成通知 Your TBIA records download is ready', content_en=content_en)
# facet.pivot=taxonID,scientificName

# 進階搜尋名錄下載
def generate_species_csv(req_dict, user_id, scheme, host):
    download_id = f"tbia_{str(ObjectId())}"

    get_raw_map = if_raw_map(user_id)
    query_list = create_search_query(req_dict=req_dict, from_request=True, get_raw_map=get_raw_map)

    req_dict = dict(req_dict)
    not_query = ['csrfmiddlewaretoken','page','from','taxon','selected_col', 'grid', 'map_bound']
    for nq in not_query:
        if nq in req_dict.keys():
            req_dict.pop(nq)
    for k in req_dict.keys():
        if len(req_dict[k])==1:
            req_dict[k] = req_dict[k][0]
    query_string = parse.urlencode(req_dict)

    current_personal_id = SearchQuery.objects.filter(user_id=user_id,type='taxon').aggregate(Max('personal_id'))
    current_personal_id = current_personal_id.get('personal_id__max') + 1 if current_personal_id.get('personal_id__max') else 1

    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'taxon',
        query_id = download_id.split('_')[-1],
        personal_id = current_personal_id
    )

    # 

    query_list += ['taxonID:*']

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
    # if not query_list:
    #     query.pop('filter')

    df = pd.DataFrame(columns=['taxonID','scientificName'])

    response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
    if response.json()['facets']['count']:
        data = response.json()['facets']['scientificName']['buckets']
        for d in data:
            if d['taxonID']['buckets']:
                df = df.append({'taxonID':d['taxonID']['buckets'][0]['val'] ,'scientificName':d['val'] },ignore_index=True)
        if len(df):
            subset_taxon = pd.DataFrame()
            subset_taxon_list = []
            taxon_ids = [f"id:{d}" for d in df.taxonID.unique()]
            for tt in range(0, len(taxon_ids), 20):
                taxa_query = {'query': " OR ".join(taxon_ids[tt:tt+20]), 'limit': 20}
                response = requests.post(f'{SOLR_PREFIX}taxa/select', data=json.dumps(taxa_query), headers={'content-type': "application/json" })
                if response.status_code == 200:
                    resp = response.json()
                    if data := resp['response']['docs']:
                        subset_taxon_list += data
            subset_taxon = pd.DataFrame(subset_taxon_list)
            used_cols = ['common_name_c','alternative_name_c','synonyms','misapplied','id','cites','iucn','redlist','protected','sensitive','alien_type','is_endemic',
                        'is_fossil', 'is_terrestrial', 'is_freshwater', 'is_brackish', 'is_marine']
            subset_taxon = subset_taxon[[u for u in used_cols if u in subset_taxon.keys()]]
            for u in used_cols:
                if u not in subset_taxon.keys():
                    subset_taxon[u] = ''
            # 整理順序
            subset_taxon = subset_taxon[used_cols]
            subset_taxon = subset_taxon.rename(columns={'id': 'taxonID'})
            df = df.merge(subset_taxon, how='left')
            is_list = ['is_endemic', 'is_fossil', 'is_terrestrial', 'is_freshwater', 'is_brackish', 'is_marine']
            df[is_list] = df[is_list].replace({1: 'true', 0: 'false'})
    csv_folder = os.path.join(MEDIA_ROOT, 'download')
    csv_folder = os.path.join(csv_folder, 'taxon')
    zip_file_path = os.path.join(csv_folder, f'{download_id}.zip')
    compression_options = dict(method='zip', archive_name=f'{download_id}.csv')
    df.to_csv(zip_file_path, compression=compression_options, index=False)

    # 儲存到下載統計
    sq.status = 'pass'
    sq.modified = timezone.now()
    sq.save()

    # 寄送通知
    nn = Notification.objects.create(
        type = 0,
        content = sq.personal_id,
        user_id = user_id
    )
    # content = nn.get_type_display().replace('0000', str(nn.content))
    # content = content.replace("請至後台查看", f"檔案下載連結：{scheme}://{host}/media/download/taxon/{download_id}.zip")
    # send_notification([user_id],content,'下載名錄已完成通知')

    content = nn.get_type_display().replace('0000', str(nn.content))
    content_en = f'The download of checklist #{str(nn.content)} is ready.<br><br>Download Link: ' + f"{scheme}://{host}/media/download/taxon/{download_id}.zip <br>"
    content = content.replace("請至後台查看", "")
    content += f"<br><br>檔案下載連結：{scheme}://{host}/media/download/taxon/{download_id}.zip <br>"
    send_notification([user_id],content,'下載名錄已完成通知 Your TBIA checklist download is ready', content_en=content_en)


# 全站搜尋資料下載
def generate_download_csv_full(req_dict, user_id, scheme, host):
    if User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
        fl_cols = download_cols + sensitive_cols
    else:
        fl_cols = download_cols
    download_id = f"tbia_{str(ObjectId())}"
    req_dict_query = dict(parse.parse_qsl(req_dict.get('search_str')))

    keyword = req_dict_query.get('keyword', '')
    key = req_dict_query.get('key', '')
    value = req_dict_query.get('value', '')
    record_type = req_dict_query.get('record_type', 'occ')
    scientific_name = req_dict_query.get('scientific_name', '')

    # only facet selected field
    query_list = []
    fq_list = [] 

    if record_type == 'col':
        fq_list = ['recordType:col']

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


    if key == 'taxonID':
        for k in taxon_facets:
            query_list += [f'{k}:/.*{keyword_name_reg}.*/']
        q = ' OR '.join(query_list)
    else:
        if key in taxon_keyword_list:
            q = f'{key}:/.*{keyword_name_reg}.*/'
        else:
            q = f'{key}:/.*{keyword_reg}.*/'

    if key == 'sourceScientificName': # 若前後有<i>也算進去
        q = f'sourceScientificName: (/.*[<i>]{value}[<\/i>].*/ OR "{value}")'
    else:
        fq_list.append(f'{key}:{value}')
    if scientific_name and scientific_name != 'undefined':
        fq_list.append(f'scientificName:{scientific_name}')

    req_dict = dict(req_dict)
    not_query = ['csrfmiddlewaretoken','page','from','taxon','selected_col', 'grid', 'map_bound']
    for nq in not_query:
        if nq in req_dict.keys():
            req_dict.pop(nq)
    for k in req_dict.keys():
        if len(req_dict[k])==1:
            req_dict[k] = req_dict[k][0]

    current_personal_id = SearchQuery.objects.filter(user_id=user_id,type='record').aggregate(Max('personal_id'))
    current_personal_id = current_personal_id.get('personal_id__max') + 1 if current_personal_id.get('personal_id__max') else 1

    query_string = parse.urlencode(req_dict)

    sq = SearchQuery.objects.create(
        user = User.objects.filter(id=user_id).first(),
        query = query_string,
        status = 'pending',
        type = 'record',
        query_id = download_id.split('_')[-1],
        personal_id = current_personal_id
    )

    query = { "query": q,
            "offset": 0,
            # "limit": req_dict.get('total_count'),
            "limit": 2140000000,
            "filter": fq_list,
            "sort":  "scientificName asc",
            "fields": fl_cols,
            }


    if not fq_list:
        query.pop('filter')

    csv_folder = os.path.join(MEDIA_ROOT, 'download')
    csv_folder = os.path.join(csv_folder, 'record')
    csv_file_path = os.path.join(csv_folder, f'{download_id}.csv')
    zip_file_path = os.path.join(csv_folder, f'{download_id}.zip')
    solr_url = f"{SOLR_PREFIX}tbia_records/select?wt=csv"

    # 等待檔案完成

    commands = f"curl -X POST {solr_url} -d '{json.dumps(query)}' > {csv_file_path}; zip -j {zip_file_path} {csv_file_path}; rm {csv_file_path}"
    process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.communicate()

    # 儲存到下載統計
    sq.status = 'pass'
    sq.modified = timezone.now()
    sq.save()

    # 寄送通知
    nn = Notification.objects.create(
        type = 1,
        content = sq.personal_id,
        user_id = user_id
    )
    # content = nn.get_type_display().replace('0000', str(nn.content))
    # content = content.replace("請至後台查看", f"檔案下載連結：{scheme}://{host}/media/download/record/{download_id}.zip")
    # send_notification([user_id],content,'下載資料已完成通知 Your TBIA records download is ready')

    content = nn.get_type_display().replace('0000', str(nn.content))
    content_en = f'The download of records #{str(nn.content)} is ready.<br><br>Download Link: ' + f"{scheme}://{host}/media/download/record/{download_id}.zip <br>"
    content = content.replace("請至後台查看", "")
    content += f"<br><br>檔案下載連結：{scheme}://{host}/media/download/record/{download_id}.zip <br>"
    send_notification([user_id],content,'下載資料已完成通知 Your TBIA records download is ready', content_en=content_en)


def get_records(request): # 全站搜尋
    if request.method == 'POST':
        from_str = request.POST.get('from', '')
        keyword = request.POST.get('keyword', '')
        key = request.POST.get('key', '')
        value = request.POST.get('value', '')
        record_type = request.POST.get('record_type', '')
        scientific_name = request.POST.get('scientific_name', '')
        limit = int(request.POST.get('limit', -1))
        page = int(request.POST.get('page', 1))
        user_id = request.user.id if request.user.id else 0

        if request.POST.get('orderby'):
            orderby =  orderby = request.POST.get('orderby')
        else:
            orderby = 'scientificName'
        if request.POST.get('sort'):
            sort =  sort = request.POST.get('sort')
        else:
            sort = 'asc'

        # only facet selected field
        fq_list = []
        query_list = []
        if record_type == 'col':
            map_dict = map_collection
            fq_list.append('recordType:col')
            title = '自然史典藏'
            obv_str = '採集'
        else:
            map_dict = map_occurrence
            title = '物種出現紀錄'
            obv_str = '紀錄'

        
        keyword = html.unescape(keyword)

        if key in taxon_keyword_list:
            keyword = re.sub(' +', ' ', keyword)

        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
        keyword_reg = get_variants(keyword_reg)

        search_str = f'keyword={keyword}&key={key}&value={value}&record_type={record_type}&orderby={orderby}&sort={sort}&limit={limit}&page={page}&from={from_str}&get_record=true'

        if 'scientific_name' not in search_str and scientific_name and scientific_name != 'undefined':
            search_str += f'&scientific_name={scientific_name}'

        offset = (page-1)*10

        if key == 'taxonID':
            for k in taxon_facets:
                query_list += [f'{k}:/.*{keyword_reg}.*/']
            q = ' OR '.join(query_list)
        else:
            q = f'{key}:/.*{keyword_reg}.*/'

        # if key == 'sourceScientificName': # 若前後有<i>也算進去
        #     q = f'sourceScientificName: (/.*{keyword_reg}.*/ AND (/.*[<i>]{value}[<\/i>].*/ OR {value}))'
        # else:
        fq_list.append(f'{key}:"{value}"')
        if scientific_name and scientific_name != 'undefined':
            fq_list.append(f'scientificName:"{scientific_name}"')

        if orderby == 'eventDate':
            solr_orderby = 'standardDate' + ' ' + sort
        elif orderby == 'organismQuantity':
            solr_orderby =  'standardOrganismQuantity' + ' ' + sort
        elif orderby == 'verbatimLatitude':
            if if_raw_map(user_id):
                solr_orderby = 'standardRawLatitude' + ' ' + sort + ',' +  'standardLatitude' + ' ' + sort 
            else:
                solr_orderby = 'standardLatitude' + ' ' + sort
        elif orderby == 'verbatimLongitude':
            if if_raw_map(user_id):
                solr_orderby = 'standardRawLongitude' + ' ' + sort + ',' +  'standardLongitude' + ' ' + sort 
            else:
                solr_orderby = 'standardLongitude' + ' ' + sort
        else:
            solr_orderby = orderby + ' ' + sort

        query = {
            "query": q,
            "filter": fq_list,
            "limit": 10,
            "offset": offset,
            "sort":  solr_orderby
            }
        
        if not fq_list:
            query.pop('filter')

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        response = response.json()
        docs = pd.DataFrame(response['response']['docs'])

        docs = docs.replace({np.nan: ''})
        docs = docs.replace({'nan': ''})

        rows = create_data_table(docs, user_id, obv_str)

        current_page = offset / 10 + 1
        total_page = math.ceil(limit / 10)
        page_list = get_page_list(current_page, total_page)

        if request.POST.getlist('selected_col'):
            selected_col = request.POST.getlist('selected_col')
        else:
            selected_col = ['scientificName','common_name_c','alternative_name_c','recordedBy','rightsHolder']

        if orderby not in selected_col:
            selected_col.append(orderby)
        
        response = {
            'title': title,
            'orderby': orderby,
            'sort': sort,
            'rows' : rows,
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
        keyword = html.unescape(keyword)
        for j in keyword:    
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else re.escape(j)
        keyword_reg = get_variants(keyword_reg)

        doc_type = request.POST.get('doc_type', '')
        offset = request.POST.get('offset', '')
        if offset:
            offset = int(offset)

        rows = []
        if doc_type == 'resource':
            resource = Resource.objects.filter(title__regex=keyword_reg).order_by('-modified')
            for x in resource[offset:offset+6]:
                rows.append({
                    'title': highlight(x.title,keyword),
                    'extension': x.extension,
                    'cate': get_resource_cate(x.extension),
                    'url': x.url,
                    'date': x.modified.strftime("%Y.%m.%d")
                })
            has_more = True if resource[offset+6:].count() > 0 else False
        else:
            news = News.objects.filter(status='pass',type=doc_type).filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
            for x in news[offset:offset+6]:
                rows.append({
                    'title': highlight(x.title,keyword),
                    'content': highlight(x.content,keyword),
                    'id': x.id
                })
            has_more = True if news[offset+6:].count() > 0 else False

        response = {
            'rows': rows,
            'has_more': has_more
        }

        return HttpResponse(json.dumps(response), content_type='application/json')



def get_focus_cards(request):
    if request.method == 'POST':
        # has_more = False
        keyword = request.POST.get('keyword', '')
        record_type = request.POST.get('record_type', '')
        key = request.POST.get('key', '')
        lang = request.POST.get('lang', 'zh-hant')

        response = get_search_full_cards(keyword=keyword, card_class=f".{record_type}-{key}-card",
                              is_sub='true', offset=0, key=key, lang=lang)

        return HttpResponse(json.dumps(response), content_type='application/json')


def get_focus_cards_taxon(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        record_type = request.POST.get('record_type', '')
        key = request.POST.get('key', '')
        lang = request.POST.get('lang', 'zh-hant')

        response = get_search_full_cards_taxon(keyword=keyword, card_class=f"{record_type}-{key}-card", is_sub='true', 
                                               offset=0, lang=lang)
        return HttpResponse(json.dumps(response), content_type='application/json')


def get_more_cards_taxon(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        card_class = request.POST.get('card_class', '')
        is_sub = request.POST.get('is_sub', '')
        offset = request.POST.get('offset', '')
        lang = request.POST.get('lang', 'zh-hant')

        response = get_search_full_cards_taxon(keyword=keyword, card_class=card_class, is_sub=is_sub, offset=offset, lang=lang)

        return HttpResponse(json.dumps(response), content_type='application/json')


def get_more_cards(request):
    if request.method == 'POST':
        # has_more = False
        keyword = request.POST.get('keyword', '')
        card_class = request.POST.get('card_class', '')
        is_sub = request.POST.get('is_sub', '')
        offset = request.POST.get('offset', '')
        offset = int(offset) if offset else offset
        if card_class not in ['.occ-card', '.col-card']:
            key = card_class.split('-')[1]
        else:
            key = None

        lang = request.POST.get('lang', 'zh-hant')

        response = get_search_full_cards(keyword=keyword, card_class=card_class, is_sub=is_sub, offset=offset, key=key, lang=lang)

        return HttpResponse(json.dumps(response), content_type='application/json')


def search_collection(request):

    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet.mincount=1&facet.limit=-1&facet=true&q.op=OR&q=*%3A*&rows=0&fq=recordType:col')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list = [f_list[x] for x in range(0, len(f_list),2)]
    rank_list = [('界', 'kingdom'), ('門', 'phylum'), ('綱', 'class'), ('目', 'order'), ('科', 'family'), ('屬', 'genus'), ('種', 'species')]

    return render(request, 'data/search_collection.html', {'holder_list': holder_list, #'sensitive_list': sensitive_list,
        'rank_list': rank_list})
    

def search_occurrence(request):

    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet.mincount=1&facet.limit=-1&facet=true&q.op=OR&q=*%3A*&rows=0')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list = [f_list[x] for x in range(0, len(f_list),2)]
    rank_list = [('界', 'kingdom'), ('門', 'phylum'), ('綱', 'class'), ('目', 'order'), ('科', 'family'), ('屬', 'genus'), ('種', 'species'), ('種下', 'sub')]

    return render(request, 'data/search_occurrence.html', {'holder_list': holder_list, # 'sensitive_list': sensitive_list,
        'rank_list': rank_list, 'basis_map': basis_map, #'dataset_list': dataset_list
        })


def occurrence_detail(request, id):

    user_id = request.user.id if request.user.id else 0
    row, path_str, logo = create_data_detail(id, user_id, 'occ')

    return render(request, 'data/occurrence_detail.html', {'row': row, 'path_str': path_str, 'logo': logo})


def collection_detail(request, id):

    user_id = request.user.id if request.user.id else 0
    row, path_str, logo = create_data_detail(id, user_id, 'col')

    return render(request, 'data/collection_detail.html', {'row': row, 'path_str': path_str, 'logo': logo})



def get_map_grid(request):
    if request.method == 'POST':
        req_dict = request.POST
        grid = int(req_dict.get('grid'))

        user_id = request.user.id if request.user.id else 0
        get_raw_map =  if_raw_map(user_id)

        query_list = create_search_query(req_dict=req_dict, from_request=True, get_raw_map=get_raw_map)
        map_query_list = query_list + ['-standardOrganismQuantity:0']
        map_bound = check_map_bound(req_dict.get('map_bound'))
        
        if get_raw_map:
            facet_grid = f'grid_{grid}'
            map_query_list += [f"location_rpt:{map_bound} OR raw_location_rpt:{map_bound} "]
        else:
            facet_grid = f'grid_{grid}_blurred'
            map_query_list += [f"location_rpt:{map_bound}"]

        query = { "query": "*:*",
                "filter": query_list,
                "facet": {
                        facet_grid: {
                            'field': facet_grid,
                            'mincount': 1,
                            "type": "terms",
                            "limit": -1,
                            'domain': { 'query': "*:*", 'filter': map_query_list}
                        },
                }
        }

        if not query_list:
            query.pop('filter')

        query_req = json.dumps(query)
        response = requests.post(f'{SOLR_PREFIX}tbia_records/select?', data=query_req, headers={'content-type': "application/json" })
        resp = response.json()

        map_geojson = get_map_geojson(data_c=resp['facets'][facet_grid]['buckets'], grid=grid)
        map_geojson = map_geojson[f'grid_{grid}']


        return HttpResponse(json.dumps(map_geojson, default=str), content_type='application/json')


def get_conditional_records(request):
    if request.method == 'POST':
        req_dict = request.POST
        limit = int(req_dict.get('limit', 10))
        orderby = req_dict.get('orderby','scientificName')
        # if orderby == 'eventDate':
        #     orderby = 'standardDate'
        sort = req_dict.get('sort', 'asc')
        user_id = request.user.id if request.user.id else 0
        get_raw_map = if_raw_map(user_id)

        # selected columns
        if req_dict.getlist('selected_col'):
            selected_col = req_dict.getlist('selected_col')
        else:
            selected_col = ['scientificName','common_name_c','alternative_name_c', 'recordedBy', 'eventDate']

        if orderby not in selected_col:
            selected_col.append(orderby)
        # use JSON API to avoid overlong query url

        query_list = create_search_query(req_dict=req_dict, from_request=True, get_raw_map=get_raw_map)

        record_type = req_dict.get('record_type')

        if record_type == 'col': # occurrence include occurrence + collection
            query_list += ['recordType:col']
            map_dict = map_collection
            obv_str = '採集'
        else:
            map_dict = map_occurrence
            obv_str = '紀錄'

        # solr_orderby = 'standardDate' if orderby == 'eventDate' else orderby
        if orderby == 'eventDate':
            solr_orderby = 'standardDate' + ' ' + sort
        elif orderby == 'organismQuantity':
            solr_orderby =  'standardOrganismQuantity' + ' ' + sort
        elif orderby == 'verbatimLatitude':
            if get_raw_map:
                solr_orderby = 'standardRawLatitude' + ' ' + sort + ',' +  'standardLatitude' + ' ' + sort 
            else:
                solr_orderby = 'standardLatitude' + ' ' + sort
        elif orderby == 'verbatimLongitude':
            if get_raw_map:
                solr_orderby = 'standardRawLongitude' + ' ' + sort + ',' +  'standardLongitude' + ' ' + sort 
            else:
                solr_orderby = 'standardLongitude' + ' ' + sort
        else:
            solr_orderby = orderby + ' ' + sort


        page = int(req_dict.get('page', 1))
        offset = (page-1)*limit


        grid = int(req_dict.get('grid', 10))

        map_query_list = query_list + ['-standardOrganismQuantity:0']
        map_bound = check_map_bound(req_dict.get('map_bound'))

        if get_raw_map:
            facet_grid = f'grid_{grid}'
            map_query_list += [f"location_rpt:{map_bound} OR raw_location_rpt:{map_bound} "]
        else:
            facet_grid = f'grid_{grid}_blurred'
            map_query_list += [f"location_rpt:{map_bound}"]

        
        query = { "query": "*:*",
                "offset": offset,
                "limit": limit,
                "filter": query_list,
                "sort":  solr_orderby,
                "facet": {
                        # 確認是否有敏感資料
                        'has_sensitive': {
                            "q": "raw_location_rpt:*",
                            "type": "query",
                        },
                        # 確認是否有物種名錄
                        'has_species': {
                            "q": "taxonID:*",
                            "type": "query",
                        },
                    }
                }
        
        
        if not query_list:
            query.pop('filter')

        map_geojson = {}
        # 新搜尋的才重新query地圖資訊
        if req_dict.get('from') not in ['page','orderby']:
            query['facet'][facet_grid] = {
                            'field': facet_grid,
                            'mincount': 1,
                            "type": "terms",
                            "limit": -1,
                            'domain': { 'query': "*:*", 'filter': map_query_list}
                        }

        query_req = json.dumps(query)

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select?', data=query_req, headers={'content-type': "application/json" })
        resp = response.json()

        count = resp['response']['numFound']
        has_sensitive = False
        has_species = False

        if count > 0 :
        
            if resp['facets']['has_sensitive']['count'] > 0:
                has_sensitive = True

            if resp['facets']['has_species']['count'] > 0:
                has_species = True

            if req_dict.get('from') not in ['page','orderby']:
                data_c = resp['facets'][facet_grid]['buckets']
                map_geojson = get_map_geojson(data_c=data_c, grid=grid)

        docs = pd.DataFrame(response.json()['response']['docs'])
        docs = docs.replace({np.nan: ''})
        docs = docs.replace({'nan': ''})

        # 如果是夥伴單位 / 系統管理員 帳號，disable敏感資料申請按鈕
        if user_id:
            if User.objects.filter(id=user_id).filter(Q(is_partner_account=True)| Q(is_partner_admin=True)| Q(is_system_admin=True)).exists():
                has_sensitive = False

        rows = create_data_table(docs, user_id, obv_str)

        current_page = offset / limit + 1
        total_page = math.ceil(count / limit)
        page_list = get_page_list(current_page, total_page)

        response = {
            'rows' : rows,
            'count': count,
            'page_list': page_list,
            'current_page' : current_page,
            'total_page' : total_page,
            'selected_col': selected_col,
            'map_dict': map_dict,
            'map_geojson': map_geojson,
            'has_sensitive': has_sensitive,
            'has_species': has_species,
            'limit': limit,
            'orderby': orderby,
            'sort': sort,
        }
        
        return HttpResponse(json.dumps(response, default=str), content_type='application/json')


def change_dataset(request):
    ds = []
    results = []

    record_type = ''
    if request.GET.get('record_type') == 'col':
        record_type = '&fq=record_type:col'


    if datasetKey := request.GET.getlist('datasetKey'):
        datasetKey = [int(d) for d in datasetKey]
        results = get_dataset_by_key(key_list=datasetKey)
        for d in results:
            ds += [{'value': d[0], 'text': d[1]}]
    elif holder := request.GET.getlist('holder'): # 有指定rightsHolder
        for h in holder:
            response = requests.get(f'{SOLR_PREFIX}dataset/select?q=*:*&q.op=OR&rows=20{record_type}&fq=rights_holder:"{h}"&fq=deprecated:false')
            d_list = response.json()['response']['docs']
            # solr內的id和datahub的postgres互通
            for l in d_list:
                if l['name'] not in [d['text'] for d in ds]:
                    ds.append({'text': l['name'], 'value': l['id']})
            # response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=datasetName&facet.mincount=1&facet.limit=20&facet=true&q.op=OR&q=*%3A*&rows=0&fq=rightsHolder:{h}')
            # d_list = response.json()['facet_counts']['facet_fields']['datasetName']
            # dataset_list = [d_list[x] for x in range(0, len(d_list),2)]
            # if len(dataset_list):
            #     if request.GET.get('record_type') == 'col':
            #         results = get_dataset_list(record_type='col',rights_holder=h,dataset_list=dataset_list)
            #     else:
            #         results = get_dataset_list(rights_holder=h,dataset_list=dataset_list)
            # for d in results:
            #     ds += [{'value': d[0], 'text': d[1]}]
    else:
        # 起始
        response = requests.get(f'{SOLR_PREFIX}dataset/select?q=*:*&q.op=OR&rows=20{record_type}&fq=deprecated:false')
        d_list = response.json()['response']['docs']
        # solr內的id和datahub的postgres互通
        for l in d_list:
            if l['name'] not in [d['text'] for d in ds]:
                ds.append({'text': l['name'], 'value': l['id']})

        # response = requests.get(f'{SOLR_PREFIX}tbia_records/select?facet.field=datasetName&facet.mincount=1&facet.limit=20&facet=true&q.op=OR&q=*%3A*&rows=0')
        # d_list = response.json()['facet_counts']['facet_fields']['datasetName']
        # dataset_list = [d_list[x] for x in range(0, len(d_list),2)]
        # if len(dataset_list):
        #     if request.GET.get('record_type') == 'col':
        #         results = get_dataset_list(record_type='col',dataset_list=dataset_list)
        #     else:
        #         results = get_dataset_list(dataset_list=dataset_list)

        # for d in results:
        #     ds += [{'value': d[0], 'text': d[1]}]

    return HttpResponse(json.dumps(ds), content_type='application/json')



def get_locality(request):
    keyword = request.GET.get('locality') if request.GET.getlist('locality') != 'null' else ''

    keyword_reg = ''
    keyword = html.unescape(keyword)
    for j in keyword:
        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
    keyword_reg = get_variants(keyword_reg)

    record_type = ''
    if request.GET.get('record_type') == 'col':
        record_type = '&fq=record_type:col'

    locality_str = f'locality:"{keyword}"^5 OR locality:/{escape_solr_query(keyword)}.*/^4 OR locality:/{keyword_reg}/^3 OR locality:/{keyword_reg}.*/^2 OR locality:/.*{escape_solr_query(keyword)}.*/^1 OR locality:/.*{keyword_reg}.*/'

    ds = []
    if keyword_reg:
        response = requests.get(f'{SOLR_PREFIX}locality/select?q.op=OR&q={locality_str}{record_type}&rows=20')
    else:
        response = requests.get(f'{SOLR_PREFIX}locality/select?q.op=OR&q=*%3A*{record_type}&rows=20&sort=locality%20desc&start=10')

    l_list = response.json()['response']['docs']
    # solr內的id和datahub的postgres互通
    for l in l_list:
        if l['locality'] not in [d['text'] for d in ds]:
            ds.append({'text': l['locality'], 'value': l['locality']})
    
    return HttpResponse(json.dumps(ds), content_type='application/json')

# 有帶出現地參數進去的時候
def get_locality_init(request):
    keyword = request.GET.getlist('locality')

    if request.GET.get('record_type') == 'col':
        record_type = '&fq=record_type:col'
    else:
        record_type = ''

    ds = []
    keyword = [f'"{k}"' for k in keyword if k ]
    if keyword:
        f_str = ' OR '.join(keyword)
        response = requests.get(f'{SOLR_PREFIX}locality/select?q.op=OR&q=*%3A*{record_type}&fq=locality:({f_str})&rows=20')
    else:
        response = requests.get(f'{SOLR_PREFIX}locality/select?q.op=OR&q=*%3A*{record_type}&rows=20&sort=locality%20desc&start=10')

    l_list = response.json()['response']['docs']
    for l in l_list:
        if l['locality'] not in [d['text'] for d in ds]:
            ds.append({'text': l['locality'], 'value': l['locality']})

    return HttpResponse(json.dumps(ds), content_type='application/json')

# 併到change_dataset中
# def get_dataset_init(request):

#     record_type = ''
#     if request.GET.get('record_type') == 'col':
#         record_type = '&fq=recordType:col'
#     else:
#         record_type = ''

#     ds = []
#     response = requests.get(f'{SOLR_PREFIX}dataset/select?facet.field=datasetName&facet.mincount=1&facet.limit=20&facet=true&q.op=OR&q=*%3A*&rows=0{record_type}')
#     d_list = response.json()['facet_counts']['facet_fields']['datasetName']
#     dataset_list = [d_list[x] for x in range(0, len(d_list),2)]
#     if len(dataset_list):
#         dataset_list = get_dataset_list(dataset_list=dataset_list,record_type=None)

#         for l in dataset_list:
#             ds.append({'text': l[1], 'value': l[0]})

#     return HttpResponse(json.dumps(ds), content_type='application/json')

def get_dataset(request):

    # datasetlist = request.GET.getlist('datasetName')
    keyword = request.GET.get('keyword')
    rights_holder = request.GET.getlist('holder')
    h_str = ''
    if len(rights_holder) > 1:
        rights_holder = ' OR '.join(rights_holder)
        h_str = f'&fq=rights_holder:({rights_holder})'
    elif len(rights_holder) == 1:
        h_str = f'&fq=rights_holder:"{rights_holder[0]}"'

    record_type = ''
    if request.GET.get('record_type') == 'col':
        record_type = '&fq=record_type:col'

    keyword_reg = ''
    for j in keyword:
        keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
    keyword_reg = get_variants(keyword_reg)

    # 完全相同 -> 相同但有大小寫跟異體字的差別 -> 開頭相同, 有大小寫跟異體字的差別  -> 包含, 有大小寫跟異體字的差別 
    dataset_str = f'name:"{keyword}"^5 OR name:/{escape_solr_query(keyword)}.*/^4 OR name:/{keyword_reg}/^3 OR name:/{keyword_reg}.*/^2 OR name:/.*{escape_solr_query(keyword)}.*/^1 OR name:/.*{keyword_reg}.*/'
    ds = []
    response = requests.get(f'{SOLR_PREFIX}dataset/select?q.op=OR&q={dataset_str}{h_str}&rows=20{record_type}&fq=deprecated:false')
    d_list = response.json()['response']['docs']
    # solr內的id和datahub的postgres互通
    for l in d_list:
        if l['name'] not in [d['text'] for d in ds]:
            ds.append({'text': l['name'], 'value': l['id']})
    
    # if len(ds):
    #     ds = pd.DataFrame(ds)
    #     ds = ds[ds['text'].drop_duplicates()].to_dict('records')

    return HttpResponse(json.dumps(ds), content_type='application/json')


def get_higher_taxa(request):
    lang = request.GET.get('lang','zh-hant')
    translation.activate(lang)
    taxon_id = request.GET.get('taxon_id','')
    ds = '[]'
    if keyword_str := request.GET.get('keyword','').strip():
        keyword_str = get_variants(keyword_str)
        # 中文搜尋包含 英文搜尋開頭為
        with connection.cursor() as cursor:
            query = f"""SELECT "taxonID", CONCAT_WS (' ',"accepted_name", CONCAT_WS(',', accepted_common_name_c, accepted_alternative_name_c)), "name",  name_status FROM data_name
            WHERE accepted_common_name_c ~ '{keyword_str}' OR accepted_alternative_name_c ~ '{keyword_str}' OR "name" ILIKE '{keyword_str}%' LIMIT 10 """
            cursor.execute(query)
            results = cursor.fetchall()
            ds = pd.DataFrame(results, columns=['value','text','name','name_status'])

        if len(ds):
            if lang == 'en-us':
                ds['text'] = ds.apply(lambda x: x['name'] + f" ({gettext(name_status_map[x['name_status']])} {x['text']})" if x['name_status'] != 'accepted' else x['text'], axis=1)
            else:
                ds['text'] = ds.apply(lambda x: x['name'] + f" ({x['text']} {name_status_map[x['name_status']]})" if x['name_status'] != 'accepted' else x['text'], axis=1)

            ds = ds[['text','value']].to_json(orient='records')
    elif taxon_id and taxon_id != 'null':
        # 如果是有taxonID的話 就一定是回傳接受名
        with connection.cursor() as cursor:
            query = f"""SELECT "taxonID", CONCAT_WS (' ',"accepted_name", CONCAT_WS(',', accepted_common_name_c, accepted_alternative_name_c)), "name",  name_status FROM data_name
            WHERE "taxonID" = '{taxon_id}' AND name_status = 'accepted'; """
            cursor.execute(query)
            results = cursor.fetchall()
            ds = pd.DataFrame(results, columns=['value','text','name','name_status'])
            ds['has_taxonID'] = True
            ds = ds[['text','value','has_taxonID']].to_json(orient='records')
    else:
        default_taxon = ('t0005214','t0004179','t0004102','t0003149','t0005573','t0005890','t0004034','t0005763','t0002476','t0004051')

        with connection.cursor() as cursor:
            query = f"""SELECT "taxonID", CONCAT_WS (' ',"accepted_name", CONCAT_WS(',', accepted_common_name_c, accepted_alternative_name_c)), "name",  name_status FROM data_name
            WHERE "taxonID" IN {str(default_taxon)} AND name_status = 'accepted'; """
            cursor.execute(query)
            results = cursor.fetchall()
            ds = pd.DataFrame(results, columns=['value','text','name','name_status'])
            ds = ds[['text','value']].to_json(orient='records')
        

    return HttpResponse(ds, content_type='application/json')


def search_full(request):
    s = time.time()
    keyword = request.GET.get('keyword', '')

    if keyword and len(keyword) < 2000:
        ## collection

        col_resp = get_search_full_cards(keyword=keyword, card_class='.col', is_sub='false', offset=0, key=None)
        collection_rows = col_resp['menu_rows']
        c_collection = col_resp['total_count']
        col_cards = col_resp['data']
        collection_more = col_resp['has_more']

        # print('b', time.time()-s)

        # s = time.time()

        ## occurrence

        occ_resp = get_search_full_cards(keyword=keyword, card_class='.occ', is_sub='false', offset=0, key=None)
        occurrence_rows = occ_resp['menu_rows']
        c_occurrence = occ_resp['total_count']
        occ_cards = occ_resp['data']
        occurrence_more = occ_resp['has_more']

        # print('d', time.time()-s)

        # s = time.time()

        ## taxon

        taxon_resp = get_search_full_cards_taxon(keyword=keyword, card_class=None, is_sub='false', offset=0)
        taxon_rows = taxon_resp['menu_rows']
        c_taxon = taxon_resp['total_count']
        taxon_cards = taxon_resp['data']
        taxon_more = taxon_resp['has_more']
            
        # print('e', time.time()-s)

        # s = time.time()

        keyword = keyword.strip()

        keyword = html.unescape(keyword)
        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else escape_solr_query(j)
        keyword_reg = get_variants(keyword_reg)

        # news
        news = News.objects.filter(status='pass',type='news').filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
        c_news = news.count()
        news_rows = []
        for x in news[:6]:
            news_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        event = News.objects.filter(status='pass',type='event').filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
        c_event = event.count()
        event_rows = []
        for x in event[:6]:
            event_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        project = News.objects.filter(status='pass',type='project').filter(Q(title__regex=keyword_reg)|Q(content__regex=keyword_reg))
        c_project = project.count()
        project_rows = []
        for x in project[:6]:
            project_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        # resource
        resource = Resource.objects.filter(title__regex=keyword_reg).order_by('-modified')
        c_resource = resource.count()
        resource_rows = []
        for x in resource[:6]:
            resource_rows.append({
                'title': x.title,
                'extension': x.extension,
                'cate': get_resource_cate(x.extension),
                'url': x.url,
                'date': x.modified.strftime("%Y.%m.%d")
            })
        
        # taxon_more = True if taxon_card_len > 4 else False

        response = {
            'keyword': keyword,
            'taxon': {'rows': taxon_rows, 'count': c_taxon, 'card': taxon_cards, 'more': taxon_more},
            'occurrence': {'rows': occurrence_rows, 'count': c_occurrence, 'card': occ_cards, 'more': occurrence_more},
            'collection': {'rows': collection_rows, 'count': c_collection, 'card': col_cards, 'more': collection_more},
            'news': {'rows': news_rows, 'count': c_news},
            'event': {'rows': event_rows, 'count': c_event},
            'project': {'rows': project_rows, 'count': c_project},
            'resource': {'rows': resource_rows, 'count': c_resource},
            }
    else:
        response = {
            'keyword': keyword,
            'taxon': {'count': 0},
            'occurrence': {'count': 0},
            'collection': {'count': 0},
            'news': {'count': 0},
            'event': {'count': 0},
            'project': {'count': 0},
            'resource': {'count': 0},
        }

    return render(request, 'data/search_full.html', response)