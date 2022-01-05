from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT
from utils.solr_query import SolrQuery, col_facets, occ_facets, SOLR_PREFIX
from pages.models import Resource, News
from django.db.models import Q
from .utils import *
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

def get_records(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        key = request.POST.get('key', '')
        value = request.POST.get('value', '')
        record_type = request.POST.get('record_type', '')
        scientific_name = request.POST.get('scientific_name', '')
        limit = int(request.POST.get('limit', -1))
        page = int(request.POST.get('page', 1))
        print(keyword, key, value, record_type, scientific_name, limit, page)

        # only facet selected field
        if record_type == 'col':
            map_dict = map_collection
            core = 'tbia_collection'
            title = '自然史典藏'
        else:
            map_dict = map_occurrence
            core = 'tbia_occurrence'
            title = '物種出現紀錄'

        key = get_key(key, map_dict)

        if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isnumeric() for i in keyword ]):
            keyword_str = f'"{keyword}"'
        else:
            keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isnumeric() else f"{keyword}"
            keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isnumeric() else ""
        
        offset = (page-1)*10
        solr = SolrQuery(core)
        query_list = [('q', keyword_str),(key,value),('scientificName',scientific_name), ('rows', 10), ('offset', offset)]
        # query_list = []
        req = solr.request(query_list)
        docs = pd.DataFrame(req['solr_response']['response']['docs'])
        docs = docs.replace({np.nan: ''})
        docs = docs.replace({'nan': ''})
        docs = docs.to_dict('records')

        current_page = offset / 10 + 1
        total_page = math.ceil(limit / 10)

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
        }

        # print(response)

        return HttpResponse(json.dumps(response), content_type='application/json')



def get_more_docs(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        doc_type = request.POST.get('doc_type', '')
        offset = request.POST.get('offset', '')
        if offset:
            offset = int(offset)

        rows = []
        if doc_type == 'resource':
            resource = Resource.objects.filter(title__icontains=keyword)
            for x in resource.all()[offset:offset+6]:
                rows.append({
                    'title': highlight(x.title,keyword),
                    'extension': x.extension,
                    'url': x.url,
                    'date': x.modified.strftime("%Y.%m.%d")
                })
            has_more = True if resource.all()[offset+6:].count() > 0 else False
        else:
            news = News.objects.filter(type=doc_type).filter(Q(title__icontains=keyword)|Q(content__icontains=keyword))
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

        if record_type == 'col':
            facet_list = col_facets
            map_dict = map_collection
            core = 'tbia_collection'
        else:
            facet_list = occ_facets
            map_dict = map_occurrence
            core = 'tbia_occurrence'

        # solr = SolrQuery(core, facet_list)
        # query_list = [('q', f'"{keyword}"'),('rows', 0)]
        # req = solr.request(query_list)
        # facets = req['solr_response']['facets']


        query = {
        "query": f'"{keyword}"',
        "limit": 0,
        "facet": {}}

        keyword_reg = ''
        for j in keyword:
            if is_alpha(j):
                keyword_reg += f"[{j.upper()}{j.lower()}]"
            else:
                keyword_reg += j

        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        response = requests.post(f'{SOLR_PREFIX}{core}/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']

        facets.pop('count', None)

        result = []

        x = facets[key]
        tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
        total_count =  sum(item['count'] for item in tmp)
        for k in tmp:
            bucket = k['scientificName']['buckets']
            result += [dict(item, **{'matched_value':k['val'], 'matched_col': key}) for item in bucket]
        result_df = pd.DataFrame(result)
        if len(result_df):
            result_df = pd.merge(result_df,taicol,left_on='val',right_on='name')
            card_len = len(result_df)
            result_df = result_df[:9]
            result_df['matched_col'] = result_df['matched_col'].apply(lambda x: map_dict[x])
            result_df['matched_value_ori'] = result_df['matched_value']
            result_df['val_ori'] = result_df['val']
            result_df['matched_value'] = result_df['matched_value'].apply(lambda x: highlight(x,keyword))
            result_df['val'] = result_df['val'].apply(lambda x: highlight(x,keyword))
            result_df['common_name_c'] = result_df['common_name_c'].apply(lambda x: highlight(x,keyword))
        else:
            card_len = 0
        
        response = {
            'title': map_dict[key],
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
        print(keyword, card_class, is_sub, offset)

        if offset:
            offset = int(offset)
        
        if card_class.startswith('.col'):
            facet_list = col_facets
            map_dict = map_collection
            core = 'tbia_collection'
        elif card_class.startswith('.occ'):
            facet_list = occ_facets
            map_dict = map_occurrence
            core = 'tbia_occurrence'

        result = []
        # solr = SolrQuery(core, facet_list)
        # query_list = [('q', f'"{keyword}"'), ('rows', 0)]        
        # req = solr.request(query_list)
        # facets = req['solr_response']['facets']

        if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isnumeric() for i in keyword ]):
            keyword_str = f'"{keyword}"'
        else:
            keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isnumeric() else f"{keyword}"
            keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isnumeric() else ""

        query = {
            "query": keyword_str,
            "limit": 0,
            "facet": {}
            }

        keyword_reg = ''
        for j in keyword:
            if is_alpha(j):
                keyword_reg += f"[{j.upper()}{j.lower()}]"
            else:
                keyword_reg += j

        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        response = requests.post(f'{SOLR_PREFIX}{core}/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']

        facets.pop('count', None)        
        if is_sub == 'false':
            for i in facets:
                x = facets[i]
                tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
                for k in tmp:
                    bucket = k['scientificName']['buckets']
                    result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
            result_df = pd.DataFrame(result)
            result_df_duplicated = result_df[result_df.duplicated(['val','count'])]
            if len(result_df_duplicated):
                remove_index = result_df_duplicated[result_df_duplicated.matched_col.isin(dup_col)].index
                result_df = result_df.loc[~result_df.index.isin(remove_index)]
        else:
            key = card_class.split('-')[1]
            x = facets[key]
            tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
            total_count =  sum(item['count'] for item in tmp)
            for k in tmp:
                bucket = k['scientificName']['buckets']
                result += [dict(item, **{'matched_value':k['val'], 'matched_col': key}) for item in bucket]
            result_df = pd.DataFrame(result)

        if len(result_df):
            result_df = pd.merge(result_df,taicol,left_on='val',right_on='name')
            card_len = len(result_df[offset:])
            result_df = result_df[offset:offset+9]
            result_df['matched_col'] = result_df['matched_col'].apply(lambda x: map_dict[x])
            result_df['matched_value_ori'] = result_df['matched_value']
            result_df['val_ori'] = result_df['val']
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


def search_full(request):
    keyword = request.GET.get('keyword', '')

    if keyword:
        # TODO 階層
        # query_list = [('q', f'"{keyword}"'), ('rows', 0)]
        # # collection
        # solr = SolrQuery('tbia_collection',facet_collection)
        # req = solr.request(query_list)
        # c_collection = req['solr_response']['response']['numFound']
        # facets = req['solr_response']['facets']

        # 如果keyword全部是中文 -> 加雙引號, 如果前後不是中文,加米字號

        if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isnumeric() for i in keyword ]):
            keyword_str = f'"{keyword}"'
        else:
            keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isnumeric() else f"{keyword}"
            keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isnumeric() else ""

        query = {
            "query": keyword_str,
            "limit": 0,
            "facet": {}
            }

        keyword_reg = ''
        for j in keyword:
            if is_alpha(j):
                keyword_reg += f"[{j.upper()}{j.lower()}]"
            else:
                keyword_reg += j

        # collection
        facet_list = col_facets
        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        s = time.time()
        response = requests.post(f'{SOLR_PREFIX}tbia_collection/select', data=json.dumps(query), headers={'content-type': "application/json" })
        print(time.time() - s)
        facets = response.json()['facets']

        facets.pop('count', None)
        c_collection = response.json()['response']['numFound']
        collection_rows = []
        result = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
            if tmp:
                collection_rows.append({
                    'title': map_collection[i],
                    'total_count': sum(item['count'] for item in tmp),
                    'key': i
                })
            for k in tmp:
                bucket = k['scientificName']['buckets']
                result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
        col_result_df = pd.DataFrame(result)
        col_result_df_duplicated = col_result_df[col_result_df.duplicated(['val','count'])]
        if len(col_result_df_duplicated):
            col_remove_index = col_result_df_duplicated[col_result_df_duplicated.matched_col.isin(dup_col)].index
            col_result_df = col_result_df.loc[~col_result_df.index.isin(col_remove_index)]
        if len(col_result_df):
            col_result_df = pd.merge(col_result_df,taicol,left_on='val',right_on='name')
            col_card_len = len(col_result_df)
            col_result_df = col_result_df[:9]
            col_result_df['matched_col'] = col_result_df['matched_col'].apply(lambda x: map_collection[x])
        else:
            col_card_len = 0


        # occurrence
        facet_list = occ_facets
        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        s = time.time()
        response = requests.post(f'{SOLR_PREFIX}tbia_occurrence/select', data=json.dumps(query), headers={'content-type': "application/json" })
        print(time.time() - s)
        facets = response.json()['facets']
        
        # solr = SolrQuery('tbia_occurrence',facet_occurrence)
        # req = solr.request(query_list)
        c_occurrence = response.json()['response']['numFound']
        occurrence_rows = []
        # facets = req['solr_response']['facets']
        facets.pop('count', None)
        result = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
            if tmp:
                occurrence_rows.append({
                    'title': map_occurrence[i],
                    'total_count': sum(item['count'] for item in tmp),
                    'key': i
                })
            for k in tmp:
                bucket = k['scientificName']['buckets']
                result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
                # TODO: 如果超過九就停止，但要怎麼判斷起始？
        occ_result_df = pd.DataFrame(result)
        occ_result_df_duplicated = occ_result_df[occ_result_df.duplicated(['val','count'])]
        if len(occ_result_df_duplicated):
            occ_remove_index = occ_result_df_duplicated[occ_result_df_duplicated.matched_col.isin(dup_col)].index
            occ_result_df = occ_result_df.loc[~occ_result_df.index.isin(occ_remove_index)]
        if len(occ_result_df):
            occ_result_df = pd.merge(occ_result_df,taicol,left_on='val',right_on='name')
            occ_card_len = len(occ_result_df)
            occ_result_df = occ_result_df[:9]
            occ_result_df['matched_col'] = occ_result_df['matched_col'].apply(lambda x: map_occurrence[x])
        else:
            occ_card_len = 0

        # news
        news = News.objects.filter(type='news').filter(Q(title__icontains=keyword)|Q(content__icontains=keyword))
        c_news = news.count()
        news_rows = []
        for x in news.all()[:6]:
            news_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        event = News.objects.filter(type='event').filter(Q(title__icontains=keyword)|Q(content__icontains=keyword))
        c_event = event.count()
        event_rows = []
        for x in event.all()[:6]:
            event_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        project = News.objects.filter(type='project').filter(Q(title__icontains=keyword)|Q(content__icontains=keyword))
        c_project = project.count()
        project_rows = []
        for x in project.all()[:6]:
            project_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        # resource
        resource = Resource.objects.filter(title__icontains=keyword)
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



def search_collection(request):
    return render(request, 'pages/search_collection.html')
    

def search_occurrence(request):
    return render(request, 'pages/search_occurrence.html')


def occurrence_detail(request, id):

    solr = SolrQuery('tbia_occurrence')
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

    return render(request, 'pages/occurrence_detail.html', {'row': row})


def collection_detail(request, id):

    solr = SolrQuery('tbia_collection')
    query_list = [('id', id), ('row',1)]
    req = solr.request(query_list)
    row = pd.DataFrame(req['solr_response']['response']['docs'])
    row = row.replace({np.nan: ''})
    row = row.replace({'nan': ''})
    row = row.to_dict('records')
    row = row[0]

    if row.get('taxonRank', ''):
        row.update({'taxonRank': map_collection[row['taxonRank']]})

    if row.get('dataGeneralizations', ''):
        if row['dataGeneralizations'] == 'True':
            row.update({'dataGeneralizations': '是'})
        elif row['dataGeneralizations'] == 'False':
            row.update({'dataGeneralizations': '否'})
        else:
            pass

    return render(request, 'pages/collection_detail.html', {'row': row})