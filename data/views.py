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

        if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isdigit() for i in keyword ]):
            keyword_str = f'"{keyword}"'
        else:
            keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isdigit() else f"{keyword}"
            keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isdigit() else ""
        
        offset = (page-1)*10
        solr = SolrQuery(core)
        query_list = [('q', keyword_str),(key,value),('scientificName',scientific_name), ('rows', 10), ('offset', offset)]
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
            facet_list = {'facet': {k: v for k, v in col_facets['facet'].items() if k == key} }
            map_dict = map_collection
            core = 'tbia_collection'
            title_prefix = '自然史典藏 > '
        else:
            facet_list = {'facet': {k: v for k, v in occ_facets['facet'].items() if k == key} }
            map_dict = map_occurrence
            core = 'tbia_occurrence'
            title_prefix = '物種出現紀錄 > '

        query = {
            "query": f'"{keyword}"',
            "limit": 0,
            "facet": {}
            }

        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else j
        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        response = requests.post(f'{SOLR_PREFIX}{core}/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)

        x = facets[key]
        total_count =  sum(item['count'] for item in x['buckets'])
        result = []
        for k in x['buckets']:
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
        
        if card_class.startswith('.col'):
            facet_list = col_facets
            map_dict = map_collection
            core = 'tbia_collection'
        elif card_class.startswith('.occ'):
            facet_list = occ_facets
            map_dict = map_occurrence
            core = 'tbia_occurrence'

        if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isdigit() for i in keyword ]):
            keyword_str = f'"{keyword}"'
        else:
            keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isdigit() else f"{keyword}"
            keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isdigit() else ""

        query = {
            "query": keyword_str,
            "limit": 0,
            "facet": {}
            }

        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else j
        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        response = requests.post(f'{SOLR_PREFIX}{core}/select', data=json.dumps(query), headers={'content-type': "application/json" })
        facets = response.json()['facets']
        facets.pop('count', None)      

        result = []
        if is_sub == 'false':
            for i in facets:
                x = facets[i]
                for k in x['buckets']:
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
            for k in x['buckets']:
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
        # 如果keyword全部是中文 -> 加雙引號, 如果前後不是中文,加米字號
        if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isdigit() for i in keyword ]):
            keyword_str = f'"{keyword}"'
        else:
            keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isdigit() else f"{keyword}"
            keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isdigit() else ""

        query = {
            "query": keyword_str,
            "limit": 0,
            "facet": {}
            }

        keyword_reg = ''
        for j in keyword:
            keyword_reg += f"[{j.upper()}{j.lower()}]" if is_alpha(j) else j

        # collection
        facet_list = col_facets
        for i in facet_list['facet']:
            facet_list['facet'][i].update({'domain': { 'query': f'{i}:/.*{keyword_reg}.*/'}})
        query.update(facet_list)

        s = time.time()
        response = requests.post(f'{SOLR_PREFIX}tbia_collection/select', data=json.dumps(query), headers={'content-type': "application/json" })
        print('get collection', time.time() - s)
        facets = response.json()['facets']
        facets.pop('count', None)

        c_collection = response.json()['response']['numFound']
        collection_rows = []
        result = []
        for i in facets:
            x = facets[i]
            if x['buckets']:
                collection_rows.append({
                    'title': map_collection[i],
                    'total_count': sum(item['count'] for item in x['buckets']),
                    'key': i
                })
            for k in x['buckets']:
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
        print('get occurrence', time.time() - s)
        facets = response.json()['facets']
        facets.pop('count', None)
        
        c_occurrence = response.json()['response']['numFound']
        occurrence_rows = []
        result = []
        for i in facets:
            x = facets[i]
            if x['buckets']:
                occurrence_rows.append({
                    'title': map_occurrence[i],
                    'total_count': sum(item['count'] for item in x['buckets']),
                    'key': i
                })
            for k in x['buckets']:
                bucket = k['scientificName']['buckets']
                result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
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

    # occ
    response = requests.get(f'{SOLR_PREFIX}tbia_occurrence/select?facet.field=rightsHolder&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list = [f_list[x] for x in range(0, len(f_list),2)]
    # col
    response = requests.get(f'{SOLR_PREFIX}tbia_collection/select?facet.field=rightsHolder&facet.mincount=1&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0')
    f_list = response.json()['facet_counts']['facet_fields']['rightsHolder']
    holder_list += [f_list[x] for x in range(0, len(f_list),2)]
    # unique
    holder_list = list(set(holder_list))

    sensitive_list = ['輕度', '重度', '縣市', '座標不開放', '物種不開放', '無']
    rank_list = ['界', '門', '綱', '目', '科', '屬', '種']
        

    return render(request, 'pages/search_occurrence.html', {'holder_list': holder_list, 'sensitive_list': sensitive_list,
        'rank_list': rank_list})


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


def get_conditional_records(request):
    if request.method == 'POST':
        print(request.POST)
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
            core = 'tbia_collection'
            title = '自然史典藏'
        else:
            map_dict = map_occurrence
            core = 'tbia_occurrence'
            title = '物種出現紀錄'

        key = get_key(key, map_dict)

        if not any([ is_alpha(i) for i in keyword ]) and not any([ i.isdigit() for i in keyword ]):
            keyword_str = f'"{keyword}"'
        else:
            keyword_str = f"*{keyword}" if is_alpha(keyword[0]) or keyword[0].isdigit() else f"{keyword}"
            keyword_str += "*" if is_alpha(keyword[-1]) or keyword[-1].isdigit() else ""
        
        offset = (page-1)*10
        solr = SolrQuery(core)
        query_list = [('q', keyword_str),(key,value),('scientificName',scientific_name), ('rows', 10), ('offset', offset)]
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

        return HttpResponse(json.dumps(response), content_type='application/json')
