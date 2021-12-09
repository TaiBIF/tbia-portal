from django.http import request
from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT
from utils.solr_query import SOLR_PREFIX, SolrQuery
from .models import *
from django.db.models import Q

facet_collection = ['scientificName', 'common_name_c', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'typeStatus', 'preservation', 'datasetName', 'license']

facet_occurrence = ['scientificName', 'common_name_c', 'rightsHolder', 'sensitiveCategory', 'taxonRank', 
                    'locality', 'recordedBy', 'basisOfRecord', 'datasetName', 'license']

def index(request):
    # resource
    resource = Resource.objects.order_by('-modified')
    resource_rows = []
    for x in resource[:6]:
        resource_rows.append({
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': x.modified.strftime("%Y.%m.%d")
        })
    return render(request, 'pages/index.html', {'resource': resource_rows})

def search_full(request):
    query_list = [('keyword')]
    keyword = request.GET.get('keyword', '')

    if keyword:
        query_list = [('q', f'"{keyword}"')]
        solr = SolrQuery('tbia_collection',facet_collection)
        req = solr.request(query_list)
        solr = SolrQuery('tbia_occurrence',facet_occurrence)
        req = solr.request(query_list)
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
        
        response = {
            'keyword': keyword,
            'occurrence': {'rows': [], 'count': 0},
            'collection': {'rows': [], 'count': 0},
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


def qa(request):
    # 加上now class 如果有request get指定是哪個問題
    return render(request, 'pages/qa.html')


def search_collection(request):
    return render(request, 'pages/search_collection.html')


def search_collection_details(request, tbiauuid):
    return render(request, 'pages/search_collection_details.html')


def search_occurrence(request):
    return render(request, 'pages/search_occurrence.html')


def search_occurrence_details(request, tbiauuid):
    return render(request, 'pages/search_occurrence_details.html')



