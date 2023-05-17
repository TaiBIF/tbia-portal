from django.http import request, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from pages.models import *
from utils.solr_query import SolrQuery
from manager.models import Partner, About
import json
import math
from data.utils import get_page_list
from django.utils import timezone

from datetime import datetime, timedelta

news_type_map = {
    'news':'green',
    'event': 'yellow',
    'project': 'red',
}

news_type_c_map = {
    'news':'消息公告',
    'event': '活動訊息',
    'project': '計畫徵求',

}


def policy(request):
    return render(request, 'pages/policy.html')


def terms(request):
    return render(request, 'pages/terms.html')


def update_is_read(request):
    if request.method == 'GET':
        if user_id := request.user.id:
            Notification.objects.filter(user_id=user_id).update(is_read=True)
            return JsonResponse({'data': 'success'}, safe=False) 
        else:
            return JsonResponse({'data': 'fail'}, safe=False) 


def update_this_read(request):
    if request.method == 'GET':
        if n_id := request.GET.get('n_id'):
            if user_id := request.user.id:
                Notification.objects.filter(id=n_id,user_id=user_id).update(is_read=True)
                count = Notification.objects.filter(user_id=user_id,is_read=False).count()
                return JsonResponse({'count': count}, safe=False) 


def page_not_found_view(request, exception):
    return render(request, '404.html', status=404)


def error_view(request):
    return render(request, '404.html', status=500)


def news(request):
    if type := request.GET.get('type'):
        news = News.objects.filter(status='pass',type=type)
    else:
        type = 'all'
        news = News.objects.filter(status='pass')
    news_list = news.order_by('-publish_date')[:10]
    current_page = 0 / 10 + 1
    total_page = math.ceil(news.count() / 10)
    page_list = get_page_list(current_page,total_page)

    return render(request, 'pages/news.html', {'news_list': news_list, 'page_list': page_list,
           'total_page': total_page, 'current_page': current_page, 'type': type})


def news_detail(request, news_id):
    if News.objects.filter(id=news_id).exists():
        n = News.objects.get(id=news_id)
        color = news_type_map[n.type]
        # 系統管理員, 單位帳號, 單位管理者
        is_authorized = False
        if not request.user.is_anonymous:  
            u = request.user
            if u.is_system_admin:
                is_authorized = True
            elif u.id == n.user_id:
                is_authorized = True
            elif u.partner_id == n.partner_id:
                is_authorized = True
                
        return render(request, 'pages/news_detail.html', {'n': n, 'color': color, 'is_authorized': is_authorized})


def get_news_list(request):
    if request.method == 'POST':
        response = {}
        type = request.POST.get('type')
        try:
            current_page = int(request.POST.get('page',1))
        except:
            current_page = 1
        if request.POST.get('from_index'):
            limit = 4
        else:
            limit = 10
        offset = limit*(current_page-1)
        if type != 'all':
            # news = News.objects.filter(type=type).order_by('-publish_date')[:limit]
            news = News.objects.filter(type=type,status='pass')
        else:
            # news = News.objects.all().order_by('-publish_date')[offset:offset+limit]
            news = News.objects.filter(status='pass')
        if request.POST.get('start_date') and request.POST.get('end_date'):
            news = news.filter(publish_date__range=[request.POST.get('start_date'), request.POST.get('end_date')])
        total_page = math.ceil(news.count() / limit)
        page_list = get_page_list(current_page,total_page,3)
        news = news.order_by('-publish_date')[offset:offset+limit]
        news_list = []
        for n in news:
            if n.publish_date:
                n.publish_date = n.publish_date.strftime("%Y-%m-%d")
            else:
                n.publish_date = ''
            n.color = news_type_map[n.type]
            n.type_c = news_type_c_map[n.type]
            if n.image:
                n.image = '/media/news/' + n.image
            else:
                n.image = '/static/image/news_ub_img.jpg'
            news_list.append({'id': n.id,'image':n.image,'color':n.color, 
                                'type_c':n.type_c,'publish_date':n.publish_date,'title':n.title})
        response['data'] = news_list
        response['page_list'] = page_list
        response['current_page'] = current_page
        response['total_page'] = total_page

        return JsonResponse(response, safe=False)



def get_resource_cate(extension):
    if extension.lower() in ['docx','csv','json','xlsx', 'xls']:
        cate = 'doc'
    elif extension.lower() in ['ppt','doc','pdf','xml']:
        cate = extension.lower()
    else:
        cate = 'other'
    return cate


def qa(request):
    type = request.GET.get('type')
    limit = 10
    if type:
        qa_list = Qa.objects.filter(type=type).order_by('order')
    else:
        qa_list = Qa.objects.filter(type=2).order_by('order')

    current_page = 0 / limit + 1
    total_page = math.ceil(qa_list.count()/limit)
    page_list = get_page_list(1, total_page)
    qa_list = qa_list[:limit]

    return render(request, 'pages/qa.html', {'qa_list': qa_list, 'type': type, 'total_page': total_page,
                                             'page_list': page_list, 'current_page': current_page})


def get_qa_list(request):
    if request.method == 'POST':
        response = {}
        type = request.POST.get('type')
        try:
            current_page = int(request.POST.get('page',1))
        except:
            current_page = 1
        
        limit = 10
        offset = limit * (current_page-1)
        qa = Qa.objects.filter(type=type).order_by('order')

        total_page = math.ceil(qa.count() / limit)
        page_list = get_page_list(current_page,total_page,3)

        qa_list = []
        for q in qa[offset:offset+limit]:
            qa_list.append({'question': q.question, 'answer': q.answer})
        response['data'] = qa_list
        response['page_list'] = page_list
        response['current_page'] = current_page
        response['total_page'] = total_page

        return JsonResponse(response, safe=False)


def news_detail(request, news_id):
    if News.objects.filter(id=news_id).exists():
        n = News.objects.get(id=news_id)
        color = news_type_map[n.type]
        # 系統管理員, 單位帳號, 單位管理者
        is_authorized = False
        if not request.user.is_anonymous:  
            u = request.user
            if u.is_system_admin:
                is_authorized = True
            elif u.id == n.user_id:
                is_authorized = True
            elif u.partner_id == n.partner_id:
                is_authorized = True
                
        return render(request, 'pages/news_detail.html', {'n': n, 'color': color, 'is_authorized': is_authorized})


def index(request):
    # recommended keyword
    keywords = Keyword.objects.all().order_by('order').values_list('keyword', flat=True)

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
        # modified =  x.modified + timedelta(hours=8)
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': x.modified.strftime("%Y.%m.%d")})
    news = News.objects.filter(status='pass').order_by('-publish_date')[:4]

    news_list = []
    for n in news:
        if n.publish_date:
            n.publish_date = n.publish_date.strftime("%Y-%m-%d")
        else:
            n.publish_date = ''
        n.color = news_type_map[n.type]
        n.type_c = news_type_c_map[n.type]
        if n.image:
            n.image = '/media/news/' + n.image
        else:
            n.image = '/static/image/news_ub_img.jpg'
        news_list.append({'id': n.id,'image':n.image,'color':n.color, 
                            'type_c':n.type_c,'publish_date':n.publish_date,'title':n.title})


    return render(request, 'pages/index.html', {'resource': resource_rows, 'keywords': keywords, 'count_occurrence': count_occurrence, 
                                                'count_collection': count_collection, 'news_list': news_list})


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

    current_page = int(request.POST.get('get_page', 1))
    page_list = get_page_list(current_page,total_page,3)

    resource_rows = []
    limit = current_page*12 if request.POST.get('from') == 'resource' else 8
    offset = (current_page-1)*12 if request.POST.get('from') == 'resource' else 0
    for x in resource[offset:limit]:
        # modified = x.modified + timedelta(hours=8)
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': x.modified.strftime("%Y.%m.%d")})

    response = {
        'rows': resource_rows,
        'current_page': current_page,
        'total_page': total_page,
        'page_list' : page_list
    }
    return HttpResponse(json.dumps(response), content_type='application/json')


def about(request):
    content = About.objects.all().first().content
    return render(request, 'pages/about.html',{'content': content})


def agreement(request):
    return render(request, 'pages/agreement.html')


def application(request):
    today = timezone.now() + timedelta(hours=8)
    today = today.strftime('%Y-%m-%d')
    return render(request, 'pages/application.html', {'today': today})


def partner(request, abbr): 
    rows = []
    pt = Partner.objects.filter(abbreviation=abbr).order_by('id')
    for p in pt:
        for pi in p.info:
            pi['title'] = p.title
            pi.update({'id': p.id})
            pi.update({'logo': p.logo})
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
        modified = x.modified + timedelta(hours=8)
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': modified.strftime("%Y.%m.%d")})
    return render(request, 'pages/resources.html', {'resource': resource_rows, 'has_more': has_more,
            'total_page': total_page, 'type': type})


def resources_link(request):
    n = Link.objects.all().first()
    return render(request, 'pages/resources_link.html', {'n': n})


def update_not_show(request):
    request.session['not_show_tech'] = True
    return JsonResponse({}, safe=False) 
