from django.http import request, HttpResponse
from django.shortcuts import render, redirect
from pages.models import *
from utils.solr_query import SolrQuery
from manager.models import Partner
import json
import math


def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)


def news_detail(request):
    return render(request, 'pages/news_detail.html')


def get_resource_cate(extension):
    if extension.lower() in ['docs','csv','json','.xlsx', '.xls']:
        cate = 'doc'
    elif extension.lower() in ['ppt','doc','pdf','xml']:
        cate = extension.lower()
    else:
        cate = 'other'
    return cate


def qa(request):
    # 加上now class 如果有request get指定是哪個問題
    return render(request, 'pages/qa.html')

def index(request):
    # recommended keyword
    keywords = Keyword.objects.filter(displayed=True).values_list('keyword', flat=True)

    # count of data
    solr = SolrQuery('tbia_records')
    query_list = [('q', '*:*'),('rows', 0)]
    req = solr.request(query_list)
    count_occurrence = req['solr_response']['response']['numFound']
    count_occurrence = "{:,}".format(count_occurrence)

    solr = SolrQuery('tbia_records')
    query_list = [('q', '*:*'),('rows', 0), ('fq','recordType:col')]
    req = solr.request(query_list)
    count_collection = req['solr_response']['response']['numFound']
    count_collection = "{:,}".format(count_collection)

    # resource
    resource = Resource.objects.order_by('-modified')
    resource_rows = []
    for x in resource[:8]:
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': x.modified.strftime("%Y.%m.%d")})
    return render(request, 'pages/index.html', {'resource': resource_rows, 'keywords': keywords, 'count_occurrence': count_occurrence, 
                                                'count_collection': count_collection})


def get_resources(request):
    type = request.POST.get('type')
    if type == 'all':
        resource = Resource.objects.order_by('-modified')
    else:
        resource = Resource.objects.filter(type=type).order_by('-modified')
    
    if request.POST.get('start_date') and request.POST.get('end_date'):
        try:
            resource = resource.filter(modified__range=[request.POST.get('start_date'),request.POST.get('end_date')])
        except:
            response = {
                'rows': [],
            }
            return HttpResponse(json.dumps(response), content_type='application/json')

    total_page = math.ceil(resource.count() / 12)

    get_page = int(request.POST.get('get_page', 1))
    print(get_page)

    resource_rows = []
    limit = get_page*12 if request.POST.get('from') == 'resource' else 8
    offset = (get_page-1)*12 if request.POST.get('from') == 'resource' else 0
    for x in resource[offset:limit]:
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': x.modified.strftime("%Y.%m.%d")})
    
    response = {
        'rows': resource_rows,
        'current_page': get_page,
        'total_page': total_page
    }
    return HttpResponse(json.dumps(response), content_type='application/json')


def about(request):
    return render(request, 'pages/about.html')


def partner(request, abbr): 
    rows = []
    pt = Partner.objects.filter(abbreviation=abbr).order_by('id')
    for p in pt:
        for pi in p.info:
            pi['title'] = p.title
            rows += [pi]
    breadtitle = Partner.objects.filter(abbreviation=abbr).first().breadtitle
    return render(request, 'pages/partner.html', {'rows': rows, 'breadtitle': breadtitle})


def resources(request):
    if type := request.GET.get('type'):
        resource = Resource.objects.filter(type=type).order_by('-modified')
    else:
        type = 'all'
        resource = Resource.objects.order_by('-modified')
    resource_rows = []
    resource_count = resource.count()
    has_more = True if resource_count > 12 else False
    total_page = math.ceil(resource_count / 12)
    for x in resource[:12]:
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': x.modified.strftime("%Y.%m.%d")})
    return render(request, 'pages/resources.html', {'resource': resource_rows, 'has_more': has_more,
            'total_page': total_page, 'type': type})