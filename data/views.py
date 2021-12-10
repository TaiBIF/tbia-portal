from django.http import request
from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT
from utils.solr_query import SOLR_PREFIX, SolrQuery
from pages.models import Resource, News
from django.db.models import Q

facet_collection = ['scientificName', 'common_name_c', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'typeStatus', 'preservation', 'datasetName', 'license']

facet_occurrence = ['scientificName', 'common_name_c', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'license']

facet_map_occurrence = {
    'scientificName': '學名',
    'common_name_c': '主要中文俗名', 
    'rightsHolder': '來源資料庫', 
    'sensitiveCategory': '敏感層級', 
    'taxonRank': '分類層級', 
    'locality': '出現地', 
    'recordedBy': '紀錄者', 
    'basisOfRecord': '資料基底', 
    'datasetName': '資料集名稱', 
    'license': '授權狀況'
}

facet_map_collection = {
    'scientificName': '學名', 
    'common_name_c': '主要中文俗名', 
    'rightsHolder': '典藏單位', 
    'sensitiveCategory': '敏感層級', 
    'taxonRank': '分類層級', 
    'locality': '採集地', 
    'recordedBy': '採集者', 
    'typeStatus': '標本類型', 
    'preservation': '保存方式', 
    'datasetName': '資料集名稱', 
    'license': '授權狀況'
}

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


def search_full(request):
    keyword = request.GET.get('keyword', '')
    # 如果查中文俗名，包含所有別名的結果
    # 如果查同物異名，回傳正式學名結果

    if keyword:
        # TODO
        query_list = [('q', f'"{keyword}"'),('fl', 'scientificName'), ('fl','common_name_c')]
        # collection
        solr = SolrQuery('tbia_collection',facet_collection)
        req = solr.request(query_list)
        c_collection = req['solr_response']['response']['numFound']
        collection_rows = []
        facets = req['solr_response']['facets']
        facets.pop('count', None)
        collection_card = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword in i['val'] ]
            if tmp:
                collection_card += [dict(item, **{'title':facet_map_collection[i]}) for item in tmp]
                collection_rows.append({
                    'title': facet_map_occurrence[i],
                    'buckets': tmp,
                    'total_count': sum(item['count'] for item in tmp)
                })
        # occurrence
        solr = SolrQuery('tbia_occurrence',facet_occurrence)
        req = solr.request(query_list)
        c_occurrence = req['solr_response']['response']['numFound']
        occurrence_rows = []
        facets = req['solr_response']['facets']
        facets.pop('count', None)
        occurrence_card = []
        for i in facets:
            x = facets[i]
            tmp = [ i for i in x['buckets'] if keyword in i['val'] ]
            if tmp:
                occurrence_card += [dict(item, **{'title':facet_map_occurrence[i]}) for item in tmp]
                occurrence_rows.append({
                    'title': facet_map_occurrence[i],
                    'buckets': tmp,
                    'total_count': sum(item['count'] for item in tmp)
                })
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
        
        occurrence_more = True if len(occurrence_card) > 9 else False
        collection_more = True if len(collection_card) > 9 else False
        
        response = {
            'keyword': keyword,
            'occurrence': {'rows': occurrence_rows, 'count': c_occurrence, 'card': occurrence_card[:9], 'has_more': occurrence_more},
            'collection': {'rows': collection_rows, 'count': c_collection, 'card': collection_card[:9], 'has_more': collection_card},
            'news': {'rows': news_rows, 'count': c_news},
            'event': {'rows': event_rows, 'count': c_event},
            'project': {'rows': project_rows, 'count': c_project},
            'resource': {'rows': resource_rows, 'count': c_resource},
            }
    else:
        response = {

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



