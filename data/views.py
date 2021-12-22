from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT
from utils.solr_query import SolrQuery
from pages.models import Resource, News
from django.db.models import Q
from .utils import taicol, facet_collection, facet_occurrence, map_occurrence, map_collection
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
dup_col = ['kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species', 'kingdom_c',
            'phylum_c', 'class_c', 'order_c', 'family_c', 'genus_c', 'scientificName', 'common_name_c', 
            'alternative_name_c', 'synonyms']

def get_key(val, my_dict):
    for key, value in my_dict.items():
         if val == value:
             return key
 
    return "key doesn't exist"


def get_more_results(request):
    if request.method == 'POST':
        search_field = request.POST.get('search_field', '')
        keyword = request.POST.get('keyword', '')
        record_type = request.POST.get('record_type', '')
        record_type = 'occ'
        search_field = '界' 
        search_field = get_key(search_field, map_collection) if record_type == 'col' else get_key(search_field, map_occurrence)
        keyword = 'Animalia'


        core = 'tbia_collection' if record_type == 'col' else 'tbia_occurrence'
        solr = SolrQuery(core)
        query_list = [('q', f'"{keyword}"'), ('rows', 10)]        
        req = solr.request(query_list)

        count_result = req['solr_response']['response']['numFound']
        docs = pd.DataFrame(req['solr_response']['response']['docs'])
    return JsonResponse({'message': 'success'})


def get_more_cards(request):
    if request.method == 'POST':
        keyword = request.POST.get('keyword', '')
        record_type = request.POST.get('record_type', '')
        offset = request.POST.get('offset', '')
        if offset:
            offset = int(offset)
        # append 9 cards a time
        query_list = [('q', f'"{keyword}"'), ('rows', 0)]

        if record_type == '.col_card':
            solr = SolrQuery('tbia_collection',facet_collection)
            req = solr.request(query_list)
            c_collection = req['solr_response']['response']['numFound']
            collection_rows = []
            facets = req['solr_response']['facets']
            facets.pop('count', None)
            collection_card = []
            result = []
            for i in facets:
                x = facets[i]
                tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
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
                col_card_len = len(col_result_df[offset:])
                col_result_df = col_result_df[offset:offset+9]
                col_result_df['matched_col'] = col_result_df['matched_col'].apply(lambda x: map_collection[x])
                col_result_df['matched_value'] = col_result_df['matched_value'].apply(lambda x: highlight(x,keyword))
                col_result_df['val'] = col_result_df['val'].apply(lambda x: highlight(x,keyword))
                col_result_df['common_name_c'] = col_result_df['common_name_c'].apply(lambda x: highlight(x,keyword))
            else:
                col_card_len = 0
            
            response = {
                'data': col_result_df.to_dict('records'),
                'has_more': True if col_card_len > 9 else False
            }

            return HttpResponse(json.dumps(response), content_type='application/json')

        else:
            solr = SolrQuery('tbia_occurrence',facet_occurrence)
            req = solr.request(query_list)
            c_occurrence = req['solr_response']['response']['numFound']
            occurrence_rows = []
            facets = req['solr_response']['facets']
            facets.pop('count', None)
            occurrence_card = []
            result = []
            for i in facets:
                x = facets[i]
                tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
                for k in tmp:
                    bucket = k['scientificName']['buckets']
                    result += [dict(item, **{'matched_value':k['val'], 'matched_col': i}) for item in bucket]
            occ_result_df = pd.DataFrame(result)
            occ_result_df_duplicated = occ_result_df[occ_result_df.duplicated(['val','count'])]
            if len(occ_result_df_duplicated):
                occ_remove_index = occ_result_df_duplicated[occ_result_df_duplicated.matched_col.isin(dup_col)].index
                occ_result_df = occ_result_df.loc[~occ_result_df.index.isin(occ_remove_index)]
            if len(occ_result_df):
                occ_result_df = pd.merge(occ_result_df,taicol,left_on='val',right_on='name')
                occ_card_len = len(occ_result_df[offset:])
                occ_result_df = occ_result_df[offset:offset+9]
                occ_result_df['matched_col'] = occ_result_df['matched_col'].apply(lambda x: map_occurrence[x])
                occ_result_df['matched_value'] = occ_result_df['matched_value'].apply(lambda x: highlight(x,keyword))
                occ_result_df['val'] = occ_result_df['val'].apply(lambda x: highlight(x,keyword))
                occ_result_df['common_name_c'] = occ_result_df['common_name_c'].apply(lambda x: highlight(x,keyword))
            else:
                occ_card_len = 0

            response = {
                'data': occ_result_df.to_dict('records'),
                'has_more': True if occ_card_len > 9 else False
            }

            
            # return JsonResponse(occ_result_df.to_dict('records'))
            return HttpResponse(json.dumps(response), content_type='application/json')


def search_full_doc(request, result_type, keyword):
    # TODO 要帶著occurrence & collection的count & facet
    print(result_type, keyword)
    if result_type != 'resource':
        news = News.objects.filter(type=result_type).filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        count = news.count()
        rows = []
        for x in news.all():
            rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
    else:
        resource = Resource.objects.filter(title__contains=keyword)
        count = resource.count()
        rows = []
        for x in resource.all():
            rows.append({
                'title': x.title,
                'extension': x.extension,
                'url': x.url,
                'date': x.modified.strftime("%Y.%m.%d")
            })

    response = {
        'type': result_type,
        'count': count,
        'rows': rows,
        'keyword': keyword
    }
    return render(request, 'pages/search_full_doc.html', response)


def search_full_record(request, record_type, keyword):
    print(record_type, keyword)
    return render(request, 'pages/search_full_record.html', {})


def search_full(request):
    keyword = request.GET.get('keyword', '')
    # 如果查中文俗名，包含所有別名的結果
    # 如果查同物異名，回傳正式學名結果

    if keyword:
        # TODO 階層
        query_list = [('q', f'"{keyword}"'), ('rows', 0)]
        # collection
        solr = SolrQuery('tbia_collection',facet_collection)
        req = solr.request(query_list)
        c_collection = req['solr_response']['response']['numFound']
        collection_rows = []
        facets = req['solr_response']['facets']
        facets.pop('count', None)
        collection_card = []
        result = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
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
        solr = SolrQuery('tbia_occurrence',facet_occurrence)
        req = solr.request(query_list)
        c_occurrence = req['solr_response']['response']['numFound']
        occurrence_rows = []
        facets = req['solr_response']['facets']
        facets.pop('count', None)
        occurrence_card = []
        result = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword.lower() in i['val'].lower() ]
            for k in tmp:
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
        news = News.objects.filter(type='news').filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        c_news = news.count()
        news_rows = []
        for x in news.all()[:6]:
            news_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        event = News.objects.filter(type='event').filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        c_event = event.count()
        event_rows = []
        for x in event.all()[:6]:
            event_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        project = News.objects.filter(type='project').filter(Q(title__contains=keyword)|Q(content__contains=keyword))
        c_project = project.count()
        project_rows = []
        for x in project.all()[:6]:
            project_rows.append({
                'title': x.title,
                'content': x.content,
                'id': x.id
            })
        # resource
        resource = Resource.objects.filter(title__contains=keyword)
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


def search_full_result(request):
    print(request)
    response = {}



    # 先不考慮階層
    # http://127.0.0.1:8983/solr/tbia_records/select?q=*species*&hl=on&hl.fl=*
    return render(request, 'pages/search_full_result.html')




def search_collection(request):
    return render(request, 'pages/search_collection.html')


def search_collection_details(request, tbiauuid):
    return render(request, 'pages/search_collection_details.html')


def search_occurrence(request):
    return render(request, 'pages/search_occurrence.html')


def search_occurrence_details(request, tbiauuid):
    return render(request, 'pages/search_occurrence_details.html')



