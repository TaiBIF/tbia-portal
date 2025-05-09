from django.shortcuts import render
from django.http import (
    # request,
    # JsonResponse,
    # HttpResponseRedirect,
    # Http404,
    HttpResponse,
)
import json
from api.models import APIkey
from data.utils import download_cols, sensitive_cols, download_cols_with_sensitive
import requests
from conf.settings import SOLR_PREFIX, datahub_db_settings
from conf.utils import scheme
import shapely.wkt as wkt
from shapely.geometry import MultiPolygon
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from urllib import parse
from manager.models import SearchCount #, SearchStat
# from django.utils import timezone
# from conf.settings import 
import psycopg2
from psycopg2 import sql
from data.utils import backgroud_search_stat, old_taxon_group_map_c, taxon_group_map_c, get_map_geojson, create_search_query
import threading


def check_grid_bound(grid, maxLon, maxLat, minLon, minLat):
    checked = True
    if grid == 1 and ((maxLon - minLon > 1) or (maxLat - minLat > 1)):
        checked = False
    elif grid == 5 and ((maxLon - minLon > 10) or (maxLat - minLat > 10)):
        checked = False
    elif grid == 10 and ((maxLon - minLon > 20) or (maxLat - minLat > 20)):
        checked = False
    elif grid == 100 and ((maxLon - minLon > 40) or (maxLat - minLat > 40)):
        checked = False
    return checked




def check_coor(lon,lat):
    try:
        standardLon = float(lon) if lon not in ['', None, '0', 'WGS84'] else None
    except:
        standardLon = None
    if standardLon:
        if not (-180 <= standardLon  and standardLon <= 180):
            standardLon = None
    try:
        standardLat = float(lat) if lat not in ['', None] else None
    except:
        standardLat = None
    if standardLat:
        if not (-90 <= standardLat and standardLat <= 90):
            standardLat = None
    # if standardLon and standardLat:
    #     # if -180 <= standardLon  and standardLon <= 180 and -90 <= standardLat and standardLat <= 90:
    #     location_rpt = f'POINT({standardLon} {standardLat})' 
    # else:
    #     location_rpt = None
    if not standardLon or not standardLat:
        return False
    else:
        return True

    

def api_doc(request):
    return render(request, 'pages/api_doc.html')


def occurrence(request):

    final_response = {}

    if request.method == 'GET':
        fq_list = []
        req = request.GET
        url_query_string = parse.urlencode(req)

        # TODO 未來考慮把訊息寫在一起

        # id={string}
        # 如果有id則忽略其他參數
        if id := req.get('id'):
            fq_list.append(f"id:{req.get('id')}")

        else:

            # 可聯集參數
            union_list = ['tbiaDatasetID','rightsHolder','locality','datasetName']
            for u in union_list:
                if values := req.get(u):
                    values = values.split(',')
                    values = [f'"{v}"' for v in values]
                    fq_list.append(f'{u}: ({(" OR ").join(values)})')

            # for k in ['occurrenceID', 'catalogNumber']:
            #     if req.get(k):
            #         fq_list.append(f'{k}:"{req.get(k)}"')

            # eventDate, created, modified
            if eventDate := req.get('eventDate'):
                date_list = eventDate.split(',')
                if len(date_list) == 2: # 起迄
                    try:
                        start_date = datetime.strptime(date_list[0], '%Y-%m-%d').isoformat() + 'Z'
                        end_date = datetime.strptime(date_list[1], '%Y-%m-%d').isoformat() + 'Z'
                        end_date = end_date.replace('00:00:00','23:59:59')
                        fq_list += [f'standardDate:[{start_date} TO {end_date}]']
                    except:
                        pass
                else:
                    date = date_list[0]
                    try:
                        date = datetime.strptime(date, '%Y-%m-%d').isoformat() + 'Z'
                        end_date = date.replace('00:00:00','23:59:59')
                        fq_list += [f'standardDate:[{date} TO {end_date}]']
                    except:
                        final_response['status'] = {'code': 400, 'message': f'Invalid date format'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')

            for k in ['created','modified']:
                if k_date := req.get(k):
                    date_list = k_date.split(',')
                    if len(date_list) == 2: # 起迄
                        try:
                            start_date = datetime.strptime(date_list[0], '%Y-%m-%d').isoformat() + 'Z'
                            end_date = datetime.strptime(date_list[1], '%Y-%m-%d').isoformat() + 'Z'
                            end_date = end_date.replace('00:00:00','23:59:59')
                            fq_list += [f'{k}:[{start_date} TO {end_date}]']
                        except:
                            final_response['status'] = {'code': 400, 'message': f'Invalid date format'}
                            return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
                    else:
                        date = date_list[0]
                        try:
                            date = datetime.strptime(date, '%Y-%m-%d').isoformat() + 'Z'
                            end_date = date.replace('00:00:00','23:59:59')
                            fq_list += [f'{k}:[{date} TO {end_date}]']
                        except:
                            final_response['status'] = {'code': 400, 'message': f'Invalid date format'}
                            return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')



            # polygon
            if polygon := req.get('polygon'):
                try:
                    mp = wkt.loads(polygon)
                    # TODO 如果是限制型API要修改成raw_location_rpt
                    fq_list += ['location_rpt: "Within(%s)"' % mp]
                except:
                    final_response['status'] = {'code': 400, 'message': f'Invalid polygon format'}
                    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')


            # 圓中心框選 - 對查詢來說是控制詞彙
            if circle := req.get('circle'):
                # lon, lat, radius
                circle = circle.split(',')
                if len(circle) == 3:
                    try:
                        int(circle[2])
                    except:
                        final_response['status'] = {'code': 400, 'message': f'Invalid circle format'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
                
                    if not check_coor(lon=circle[0], lat=circle[1]):
                        final_response['status'] = {'code': 400, 'message': f'Invalid circle format'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')

                    # TODO 如果是限制型API要修改成raw_location_rpt
                    fq_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (circle[1].strip(), circle[0].strip(), circle[2])]
                else:
                    final_response['status'] = {'code': 400, 'message': f'Invalid circle format'}
                    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')



            # boundedBy={string} -> 網頁沒有 # 121,23,122,24
            if boundedBy := req.get('boundedBy'): # maxLon, maxLat , minLon, minLat
                # [lat1, lon1 TO lat2, lon2]
                # [lat1, lon1 TO lat2, lon2]
                # [23,121 TO 24,122]
                boundedBy = boundedBy.split(',')
                if len(boundedBy) == 4:
                    try:
                        maxLon = int(boundedBy[0])
                        maxLat = int(boundedBy[1])
                        minLon = int(boundedBy[2])
                        minLat = int(boundedBy[3])
                        if not check_coor(maxLon,maxLat) or not check_coor(minLon, minLat) or not (maxLat >= minLat) or not(maxLon >= minLon):
                            final_response['status'] = {'code': 400, 'message': f'Invalid boundedBy format'}
                            return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
                    except:
                        final_response['status'] = {'code': 400, 'message': f'Invalid boundedBy format'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
                    # TODO 如果是限制型API要修改成raw_location_rpt
                    fq_list += [f'location_rpt:[{minLat},{minLon} TO {maxLat},{maxLon}]']
                else:
                    final_response['status'] = {'code': 400, 'message': f'Invalid boundedBy format'}
                    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')

            # is_collection={boolean}
            if isCollection := req.get('isCollection'):
                if isCollection == 'false': # 非自然史典藏
                    fq_list.append('recordType:occ')
                elif isCollection == 'true':
                    fq_list.append('recordType:col')
                else:
                    final_response['status'] = {'code': 400, 'message': f'Invalid isCollection value'}
                    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')



        limit = req.get('limit', 20)

        try:
            limit = int(limit)
        except:
            limit = 20

        if limit > 1000: # 最高為1000
            limit = 1000

        # if req.get('cursor'):
        cursor = req.get('cursor', '*')
        

        # offset = req.get('offset', 0)
        # try:
        #     offset = int(offset)
        # except:
        #     offset = 0

        fl_cols = download_cols


        now_dict = dict(req)

        for k in now_dict.keys():
            if len(now_dict[k])==1:
                now_dict[k] = now_dict[k][0]


        # req_dict = dict(req)
        # # 修改成對應的參數名 & 參數值
        if now_dict.get('bioGroup'):
            now_dict['taxonGroup'] = now_dict.get('bioGroup')
            now_dict.pop('bioGroup')

        if now_dict.get('higherTaxon'):
            now_dict['higherTaxa'] = now_dict.get('higherTaxon')
            now_dict.pop('higherTaxon')

        if now_dict.get('isNative'):
            now_dict['is_native'] =  now_dict.get('isNative')
            now_dict.pop('isNative')

        if now_dict.get('isProtected'):
            now_dict['is_protected'] = now_dict.get('isProtected')
            now_dict.pop('isProtected')

        if now_dict.get('imagePresence'):
            now_dict['has_image'] = now_dict.get('imagePresence')
            now_dict.pop('imagePresence')

        for k in ['rightsHolder','locality','datasetName']:
            if k in now_dict.keys():
                now_dict.pop(k)


        # 限制型API
        has_api_key = False

        if apikey := req.get('apikey'):
            if APIkey.objects.filter(key=apikey,status='pass').exists():
                has_api_key = True
                fl_cols = download_cols_with_sensitive
                # 部分統一使用create_search_query
                
                fq_list += create_search_query(req_dict=now_dict, from_request=False, get_raw_map=True)

            else:
                final_response['status'] = {'code': 400, 'message': 'Invalid API key'}
                return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
        else:
            fq_list += create_search_query(req_dict=now_dict, from_request=False, get_raw_map=True)


        query = { "query": "*:*",
                "params": {"cursorMark": cursor}, 
                "limit": limit,
                "filter": fq_list,
                "sort":  "id asc",
                "fields": fl_cols
                }

        if not fq_list:
            aaa = query.pop('filter', None)

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        response = response.json()

        next_cursor = response.get('nextCursorMark')

        # 整理欄位

        total = response['response']['numFound']
        data = response['response']['docs']

        df = pd.DataFrame(data)

        if not has_api_key:
            df = df.drop(columns=sensitive_cols, errors='ignore')

        if len(df):
            # modified
            # created
            # sourceCreated
            # sourceModified
            # standardDate
            # standardLatitude
            # standardLongitude
            # standardRawLatitude
            # standardRawLongitude
            # standardOrganismQuantity

            df = df.replace({np.nan: None})

            df['created'] = df['created'].apply(lambda x: x[0].split('T')[0])
            df['modified'] = df['modified'].apply(lambda x: x[0].split('T')[0])

            for s in ['sourceCreated','sourceModified','standardDate']:
                if s in df.keys():
                    df[s] = df[s].apply(lambda x: x[0].split('T')[0] if x else None)

            for s in ['standardLatitude','standardLongitude','standardRawLatitude','standardRawLongitude','standardOrganismQuantity']:
                if s in df.keys():
                    df[s] = df[s].apply(lambda x: x[0] if x else None)

            df = df.replace({np.nan: None})

        aaa = now_dict.pop('cursor', None)
    
        
        query_string = parse.urlencode(now_dict)

        next_url = ''

        # 確認還有沒有下一頁
        if next_cursor != cursor and len(df) == limit:
            if url_query_string:
                next_url = f'{scheme}://{request.get_host()}/api/v1/occurrence?' + url_query_string + '&cursor=' + next_cursor
            else:
                next_url = f'{scheme}://{request.get_host()}/api/v1/occurrence?' + 'cursor=' + next_cursor

        if url_query_string:
            now_url = f'{scheme}://{request.get_host()}/api/v1/occurrence?' + url_query_string + '&cursor=' + cursor
        else:
            now_url = f'{scheme}://{request.get_host()}/api/v1/occurrence?' + 'cursor=' + cursor

        # 記錄在SearchStat
        # if offset == 0:
        if cursor == '*':
            task = threading.Thread(target=backgroud_search_stat, args=(fq_list,'api_occ', query_string))
            task.start()

        obj, created = SearchCount.objects.update_or_create(
                search_location='api_occ'
            )
        obj.count += 1
        obj.save()

        # metadata
        final_response['status'] = {'code': 200, 'message': 'Success'}
        final_response['meta'] = {'total': total, 'limit': limit}
        final_response['links'] = {'self': now_url, 'next': next_url}
        final_response['data'] = df.to_dict('records')

    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')




def dataset(request):
    final_response = {}

    if request.method == 'GET':

        results = []

        req = request.GET

        limit = req.get('limit', 20)

        try:
            limit = int(limit)
        except:
            limit = 20

        if limit > 1000: # 最高為1000
            limit = 1000

        now_cursor = int(req.get('cursor', 0))

        # 篩選條件

        conn = psycopg2.connect(**datahub_db_settings)
    
        query_value = []
        query_pair = []
        query_identifier = []


        # 這邊會改成用中文搜尋 但要讓中英文都可以通
        if group_value := req.get('datasetTaxonGroup'):

            if group_value in taxon_group_map_c.keys():
                group_value = taxon_group_map_c[group_value]
            if group_value in old_taxon_group_map_c.keys():
                group_value = old_taxon_group_map_c[group_value]

            if group_value == '維管束植物':
                query_value.append('%維管束植物%')
                query_value.append('%蕨類植物%')
                query_pair.append('({} like %s OR {} like %s)')
                query_identifier.append('datasetTaxonGroup')
                query_identifier.append('datasetTaxonGroup')
            else:
                query_value.append('%{}%'.format(group_value))
                query_pair.append('{} like %s')
                query_identifier.append('datasetTaxonGroup')

        for k in ['datasetName', 'rightsHolder']:
            tmp_list = []
            if k == 'rightsHolder':
                key = 'rights_holder'
                for kk in req.getlist(k):
                    tmp_list.append('{} = %s')
                    query_value.append(kk)
                    query_identifier.append(key)
            else:
                key = 'name'
                for kk in req.getlist(k):
                    tmp_list.append('{} like %s')
                    query_value.append(f'%{kk}%')
                    query_identifier.append(key)
            if tmp_list:
                query_pair.append("(" + ' OR '.join(tmp_list) + ")")


        for k in ['sourceDatasetID','tbiaDatasetID','gbifDatasetID']:
            if req.get(k):
                query_pair.append('{} = %s')
                query_value.append(req.get(k))
                query_identifier.append(k)


        for k in ['created','modified']:
            if k_date := req.get(k):
                date_list = k_date.split(',')
                if len(date_list) == 2: # 起迄
                    # 區間
                    try:
                        start_date = datetime.strptime(date_list[0], '%Y-%m-%d')
                        start_date = start_date.strftime('%Y-%m-%d')
                        end_date = datetime.strptime(date_list[1], '%Y-%m-%d')
                        end_date = end_date + timedelta(days=1)
                        end_date = end_date.strftime('%Y-%m-%d')
                        query_pair.append('{} >= %s')
                        query_value.append(start_date)
                        query_identifier.append(k)
                        query_pair.append('{} < %s')
                        query_value.append(end_date)
                        query_identifier.append(k)
                    except:
                        final_response['status'] = {'code': 400, 'message': f'Invalid date format'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
                else:
                    # 當天
                    date = date_list[0]
                    try:
                        start_date = datetime.strptime(date, '%Y-%m-%d')
                        end_date = start_date + timedelta(days=1)
                        start_date = start_date.strftime('%Y-%m-%d')
                        end_date = end_date.strftime('%Y-%m-%d')
                        query_pair.append('{} >= %s')
                        query_value.append(start_date)
                        query_identifier.append(k)
                        query_pair.append('{} < %s')
                        query_value.append(end_date)
                        query_identifier.append(k)
                    except:
                        final_response['status'] = {'code': 400, 'message': f'Invalid date format'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')


        query_str = '''SELECT "id", "name" as "datasetName", "rights_holder" as "rightsHolder","tbiaDatasetID","sourceDatasetID","gbifDatasetID","resourceContacts",
                          "occurrenceCount","datasetDateStart","datasetDateEnd","datasetURL","datasetPublisher","datasetLicense","datasetTaxonGroup",
                        TO_CHAR(created, 'yyyy-mm-dd') AS created , TO_CHAR(modified, 'yyyy-mm-dd') AS modified,
                        COUNT(*) OVER() AS total
                        FROM dataset WHERE deprecated = 'f' 
                        '''

        if len(query_pair):
            query_str += ' AND ' + (' AND ').join(query_pair)

        query_str += ' AND id > %s'

        query_value.append(now_cursor)

        query_str += ' ORDER BY id LIMIT %s'

        query_value.append(limit)

        query = sql.SQL(query_str).format(*[sql.Identifier(field) for field in query_identifier])

        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(query, query_value)
            results = cursor.fetchall()
            conn.close()

        data = []
        total = 0
        id_list = []
        for row in results:
            total = dict(row).get('total')
            id_list.append(dict(row).get('id'))
            row = dict(row)
            aaa = row.pop('total', None)
            aaa = row.pop('id', None)
            data.append(row)

        if len(data):
            next_cursor = max(id_list)
        else:
            next_cursor = now_cursor # 代表沒有資料了
        
        now_dict = dict(req)

        for k in now_dict.keys():
            if len(now_dict[k])==1:
                now_dict[k] = now_dict[k][0]

        aaa = now_dict.pop('cursor', None)
        query_string = parse.urlencode(now_dict)

        next_url = ''

        # 確認還有沒有下一頁
        if next_cursor != now_cursor and len(data) == limit:
            if query_string:
                next_url = f'{scheme}://{request.get_host()}/api/v1/dataset?' + query_string + '&cursor=' + str(next_cursor)
            else:
                next_url = f'{scheme}://{request.get_host()}/api/v1/dataset?' + 'cursor=' + str(next_cursor)

        if query_string:
            now_url = f'{scheme}://{request.get_host()}/api/v1/dataset?' + query_string + '&cursor=' + str(now_cursor)
        else:
            now_url = f'{scheme}://{request.get_host()}/api/v1/dataset?' + '&cursor=' + str(now_cursor)


        obj, created = SearchCount.objects.update_or_create(
                search_location='dataset'
            )
        obj.count += 1
        obj.save()

        final_response['status'] = {'code': 200, 'message': 'Success'}
        final_response['meta'] = {'total': total, 'limit': limit}
        final_response['links'] = {'self': now_url, 'next': next_url}
        final_response['data'] = data

    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')



def map(request):

    final_response = {}
    map_geojson = {}

    if request.method == 'GET':
        fq_list = []
        req = request.GET

        # 可聯集參數
        union_list = ['taxonID']
        for u in union_list:
            if values := req.getlist(u):
                values = [f'"{v}"' for v in values]
                fq_list.append(f'{u}: ({(" OR ").join(values)})')

        if group_values := req.getlist('bioGroup'):
            values = []
            for group_value in group_values:

                if group_value in taxon_group_map_c.keys():
                    group_value = taxon_group_map_c[group_value]
                if group_value in old_taxon_group_map_c.keys():
                    group_value = old_taxon_group_map_c[group_value]


                if group_value == '維管束植物':
                    values.append('維管束植物')
                    values.append('蕨類植物')
                else:
                    values.append(group_value)
            fq_list.append(f'bioGroup: ({(" OR ").join(values)})')

        #  年份區間
        if year := req.get('year'):
            year_list = year.split(',')
            if len(year_list) == 2: # 起迄
                try:
                    start_year = int(year_list[0])
                    end_year = int(year_list[1])
                    fq_list += [f'year:[{start_year} TO {end_year}]']
                except:
                    pass
            else:
                try:
                    year = int(year_list[0])
                    fq_list += [f'year:[{year} TO *]']
                except:
                    final_response['status'] = {'code': 400, 'message': f'Invalid year format'}
                    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')


        # 網格大小 // 需搭配地理範圍
        # 先統一使用模糊化座標
        if grid := req.get('grid', 1):

            try:
                grid = int(grid)
                grid = [g for g in [1,5,10,100] if g == grid][0]
            except:
                final_response['status'] = {'code': 400, 'message': f'Invalid grid value'}
                return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')


            facet_grid = f'grid_{grid}_blurred'

            if boundedBy := req.get('boundedBy'): # maxLon, maxLat , minLon, minLat
                boundedBy = boundedBy.split(',')
                if len(boundedBy) == 4:
                    try:
                        maxLon = int(boundedBy[0])
                        maxLat = int(boundedBy[1])
                        minLon = int(boundedBy[2])
                        minLat = int(boundedBy[3])
                        if not check_coor(maxLon,maxLat) or not check_coor(minLon, minLat) or not (maxLat >= minLat) or not(maxLon >= minLon):
                            final_response['status'] = {'code': 400, 'message': f'Invalid boundedBy format'}
                            return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
                    except:
                        final_response['status'] = {'code': 400, 'message': f'Invalid boundedBy format'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')
                    
                    if not check_grid_bound(grid, maxLon, maxLat, minLon, minLat):
                        final_response['status'] = {'code': 400, 'message': f'Invalid boundedBy value according to grid size'}
                        return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')

                    fq_list += [f'location_rpt:[{minLat},{minLon} TO {maxLat},{maxLon}]']

                else:
                    final_response['status'] = {'code': 400, 'message': f'Invalid boundedBy format'}
                    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')

            else:
                final_response['status'] = {'code': 400, 'message': f'Parameter boundedBy is required'}
                return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')


        query = { "query": "location_rpt:*",
                 "limit": 0,
                "filter": fq_list,
                "facet": {
                        facet_grid: {
                            'field': facet_grid,
                            'mincount': 1,
                            "type": "terms",
                            "limit": -1,
                        },
                }
        }


        if not fq_list:
            aaa = query.pop('filter', None)


        query_req = json.dumps(query)
        response = requests.post(f'{SOLR_PREFIX}tbia_records/select?', data=query_req, headers={'content-type': "application/json" })
        resp = response.json()

        if resp['facets']['count']:

            map_geojson = get_map_geojson(data_c=resp['facets'][facet_grid]['buckets'], grid=grid)
            map_geojson = map_geojson['grid_'+str(grid)]

        # # 記錄在SearchStat
        now_dict = dict(req)

        for k in now_dict.keys():
            if len(now_dict[k])==1:
                now_dict[k] = now_dict[k][0]

        query_string = parse.urlencode(now_dict)


        task = threading.Thread(target=backgroud_search_stat, args=(fq_list,'map', query_string))
        task.start()

        obj, created = SearchCount.objects.update_or_create(
                search_location='map'
            )
        obj.count += 1
        obj.save()

        # metadata
        final_response['status'] = {'code': 200, 'message': 'Success'}
        final_response['data'] = map_geojson

    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')