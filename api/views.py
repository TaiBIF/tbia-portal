from django.shortcuts import render
from django.http import (
    request,
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponse,
)
import json
from api.models import APIkey
from data.utils import *
import requests
from utils.solr_query import SOLR_PREFIX
import shapely.wkt as wkt
from shapely.geometry import MultiPolygon


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

        # TODO 未來考慮把訊息寫在一起

        # id={string}
        # 如果有id則忽略其他參數
        if id := req.get('id'):
            fq_list.append(f"id:{req.get('id')}")

        else:

            # 可聯集參數
            # taxonID={string}
            # rightsHolder={string}
            # datasetName={string}
            union_list = ['taxonID', 'rightsHolder','datasetName']
            for u in union_list:
                if values := req.getlist(u):
                    values = [f'"{v}"' for v in values]
                    fq_list.append(f'{u}: ({(" OR ").join(values)})')

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
            if polygon := req.getlist('polygon'):
                try:
                    mp = MultiPolygon(map(wkt.loads, polygon))
                    fq_list += ['location_rpt: "Within(%s)"' % mp]
                except:
                    final_response['status'] = {'code': 400, 'message': f'Invalid polygon format'}
                    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')

            # 上傳polygon - 對查詢來說是控制詞彙
            # if g_id := request.POST.get('geojson_id'):
            #     try:
            #         with open(f'/tbia-volumes/media/geojson/{g_id}.json', 'r') as j:
            #             geojson = json.loads(j.read())
            #             geo_df = gpd.GeoDataFrame.from_features(geojson)
            #             g_list = []
            #             for i in geo_df.to_wkt()['geometry']:
            #                 g_list += ['"Within(%s)"' % i]
            #             query_list += [ f"location_rpt: ({' OR '.join(g_list)})" ]
            #     except:
            #         pass

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

                    fq_list += ['{!geofilt pt=%s,%s sfield=location_rpt d=%s}' %  (circle[1], circle[0], circle[2])]
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

        
            # # is_deleted={boolean}
            # if is_deleted := req.get('isDeleted'):
            #     if is_deleted in ['true', 'false']:
            #         fq_list.append({'is_deleted', is_deleted})


        limit = req.get('limit', 20)

        try:
            limit = int(limit)
        except:
            limit = 20

        if limit > 300: # 最高為300
            limit = 300

        offset = req.get('offset', 0)
        try:
            offset = int(offset)
        except:
            offset = 0



        # 限制型API
        fl_cols = download_cols
        if apikey := req.get('apikey'):
            if APIkey.objects.filter(key=apikey,status='pass').exists():
                fl_cols += sensitive_cols
            else:
                # fl_cols = download_cols
                final_response['status'] = {'code': 400, 'message': 'Invalid API key'}


    
        query = { "query": "*:*",
                "offset": offset,
                "limit": limit,
                "filter": fq_list,
                "sort":  "scientificName asc",
                "fields": fl_cols
                }

        if not fq_list:
            query.pop('filter')

        response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
        response = response.json()

        # 整理欄位

        total = response['response']['numFound']
        data = response['response']['docs']

        df = pd.DataFrame(data)

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

        # metadata
        final_response['status'] = {'code': 200, 'message': 'Success'}
        final_response['meta'] = {'total': total, 'limit': limit, 'offset': offset}
        final_response['data'] = df.to_dict('records')

    
    return HttpResponse(json.dumps(final_response, default=str), content_type='application/json')