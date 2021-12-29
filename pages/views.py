from django.http import request
from django.shortcuts import render, redirect
from .models import *
from utils.solr_query import SolrQuery


def qa(request):
    # 加上now class 如果有request get指定是哪個問題
    return render(request, 'pages/qa.html')


def index(request):
    # recommended keyword
    keywords = Keyword.objects.filter(displayed=True).values_list('keyword', flat=True)

    # count of data
    solr = SolrQuery('tbia_occurrence')
    query_list = [('q', '*:*'),('rows', 0)]
    req = solr.request(query_list)
    count_occurrence = req['solr_response']['response']['numFound']
    count_occurrence = "{:,}".format(count_occurrence)

    solr = SolrQuery('tbia_collection')
    query_list = [('q', '*:*'),('rows', 0)]
    req = solr.request(query_list)
    count_collection = req['solr_response']['response']['numFound']
    count_collection = "{:,}".format(count_collection)

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
    return render(request, 'pages/index.html', {'resource': resource_rows, 'keywords': keywords, 'count_occurrence': count_occurrence, 
                                                'count_collection': count_collection})