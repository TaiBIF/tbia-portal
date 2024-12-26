from django.http import HttpResponse, JsonResponse #request, 
from django.shortcuts import render#, redirect
from pages.models import *
from conf.settings import SOLR_PREFIX, env
from manager.models import Partner, About, SearchQuery, Ark
import json
import math
from data.utils import get_page_list, get_resource_cate
from django.utils import timezone, translation
from conf.utils import notif_map, scheme
from datetime import datetime, timedelta
from django.utils.translation import get_language, gettext
import requests
from pages.templatetags.tags import var_df, var_df_2


news_type_map = {
    'news':'green',
    'event': 'yellow',
    'project': 'red',
    'datathon': 'blue',
    'themeyear': 'silver',
}

news_type_c_map = {
    'news':'新聞公告',
    'event': '活動訊息',
    'project': '徵求公告',
    'datathon': '數據松成果',
    'themeyear': '主題年活動',
}


# 從js呼叫API
def get_variants(request):
  if request.method == 'GET':
    string = request.GET.get('string')
    new_string = ''
    # 單個異體字
    for s in string:    
      if len(var_df[var_df['char']==s]):
        new_string += var_df[var_df['char']==s].pattern.values[0]
      else:
        new_string += s
    # 兩個異體字
    for i in var_df_2.index:
      char = var_df_2.loc[i, 'char']
      if char in new_string:
        new_string = new_string.replace(char,f"{var_df_2.loc[i, 'pattern']}")
    return JsonResponse({'new_string': new_string}, safe=False) 


def get_current_notif(request):
    translation.activate(request.GET.get('lang'))
    count = 0
    results = []
    if not request.user.is_anonymous:  
        count = Notification.objects.filter(user_id=request.user.id,is_read=False).count()
        notifications = Notification.objects.filter(user_id=request.user.id).order_by('-created')[:10]
        results = ""
        for n in notifications:
            if n.type in notif_map.keys(): 
                href = notif_map[n.type]
            elif n.type == 2:
                if User.objects.filter(id=request.user.id,is_system_admin=True).exists():
                    href = '/manager/system/info?menu=feedback'
                else:
                    href = '/manager/partner/info?menu=feedback'
            elif n.type == 3:
                if User.objects.filter(id=request.user.id,is_system_admin=True).exists():
                    href = '/manager/system/info?menu=sensitive'
                else:
                    href = '/manager/partner/info?menu=sensitive'
            elif n.type == 5:
                if User.objects.filter(id=request.user.id,is_system_admin=True).exists():
                    href = '/manager/system/info?menu=account'
                else:
                    href = '/manager/partner/info?menu=account'
            else:
                href = '/manager'

            created_8 = n.created + timedelta(hours=8)
            if not n.is_read: 
                is_read = '<div class="dottt"></div>'
            else:
                is_read = ''
            # print(gettext(n.get_type_display()))
            results += f"""
                        <li class="redirectToAdmin" data-nid="{n.id}" data-href="{href}">
                        {is_read}
                        <div class="txtcont">
                        <p class="date">{created_8.strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p>{ gettext(n.get_type_display()).replace('0000',n.content)}</p>
                        </div>
                    </li>
                    """
        if not results:
            results = f"""
                        <li>
                        <div class="txtcont">
                        <p class="date"></p>
                        <p>{gettext('暫無通知')}</p>
                        </div>
                    </li>
                    """        
    return JsonResponse({'count': count, 'notif': results}, safe=False) 


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
    type = request.GET.get('type', 'all')
    return render(request, 'pages/news.html', {'type': type})


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
            news = News.objects.filter(type=type,status='pass',lang=request.LANGUAGE_CODE)
        else:
            # news = News.objects.all().order_by('-publish_date')[offset:offset+limit]
            news = News.objects.filter(status='pass',lang=request.LANGUAGE_CODE)
        if request.POST.get('start_date') and request.POST.get('end_date'):
            news = news.filter(publish_date__gte=request.POST.get('start_date'),publish_date__lte=datetime.strptime(request.POST.get('end_date'),'%Y-%m-%d')+timedelta(days=1))
        total_page = math.ceil(news.count() / limit)
        page_list = get_page_list(current_page,total_page,5)
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


def qa(request):
    qa_options = [{'type': 2, 'value': '網頁內容'}, {'type': 1, 'value': '網頁操作'},{'type': 3, 'value': '聯盟相關'},]
    type = request.GET.get('type', 2)
    qa_page = None
    if qa_id := request.GET.get('qa_id'):
        # 要先確認是在哪個type的的哪一頁
        if Qa.objects.filter(id=qa_id).exists():
            type = Qa.objects.get(id=qa_id).type
            qa_list = list(Qa.objects.filter(type=type).order_by('order').values_list('id', flat=True))
            position_index = qa_list.index(int(qa_id)) + 1
            qa_page = math.ceil(position_index / 10)

    return render(request, 'pages/qa.html', {'qa_options': qa_options, 'type': type, 'qa_page': qa_page})


def get_qa_list(request):
    if request.method == 'POST':
        translation.activate(request.POST.get('lang'))
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
        page_list = get_page_list(current_page,total_page,5)

        qa_list = []
        for q in qa[offset:offset+limit]:
            ques = q.question_en if get_language() == 'en-us' and q.question_en else q.question
            ans = q.answer_en if get_language() == 'en-us' and q.answer_en else q.answer
            qa_list.append({'question': ques, 'answer': ans, 'id': q.id})
        response['data'] = qa_list
        response['page_list'] = page_list
        response['current_page'] = current_page
        response['total_page'] = total_page

        return JsonResponse(response, safe=False)


def index(request):

    # recommended keyword
    keywords = Keyword.objects.filter(lang=get_language()).order_by('order').values_list('keyword', flat=True)

    # count of data

    count_occurrence = 0
    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q=*:*&rows=0')
    if response.status_code == 200:
        count_occurrence = response.json()['response']['numFound']

    count_occurrence = "{:,}".format(count_occurrence)

    count_collection = 0
    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q=*:*&rows=0&fq=recordType:col')
    if response.status_code == 200:
        count_collection = response.json()['response']['numFound']

    count_collection = "{:,}".format(count_collection)

    # resource
    resource = Resource.objects.filter(lang=request.LANGUAGE_CODE).order_by('-publish_date')
    resource_rows = []
    for x in resource[:5]:
        # modified =  x.modified + timedelta(hours=8)
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'doc_url': x.doc_url,
            'date': x.publish_date.strftime("%Y-%m-%d")})
        
    news = News.objects.filter(status='pass',lang=request.LANGUAGE_CODE).order_by('-publish_date')[:4]

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


def get_resource_list(request):
    type = request.POST.get('type')
    lang = request.POST.get('lang', 'zh-hant')
    if type == 'all':
        resource = Resource.objects.filter(lang=lang).order_by('-publish_date')
    else:
        resource = Resource.objects.filter(type=type,lang=lang).order_by('-publish_date')
    
    if request.POST.get('start_date') and request.POST.get('end_date'):
        try:
            resource = resource.filter(publish_date__gte=request.POST.get('start_date'),publish_date__lte=datetime.strptime(request.POST.get('end_date'),'%Y-%m-%d')+timedelta(days=1))
        except:
            response = {
                'rows': [],
            }
            return HttpResponse(json.dumps(response), content_type='application/json')

    total_page = math.ceil(resource.count() / 12)

    current_page = int(request.POST.get('get_page', 1))
    page_list = get_page_list(current_page,total_page,5)

    resource_rows = []
    req_from = request.POST.get('from') # 首頁或開放資源頁面
    limit = current_page*12 if req_from == 'resource' else 8
    if req_from != 'resource' and type =='all':
        limit = 5
    offset = (current_page-1)*12 if req_from == 'resource' else 0

    for x in resource[offset:limit]:
        # modified = x.modified + timedelta(hours=8)
        resource_rows.append({
            'cate': get_resource_cate(x.extension),
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'doc_url': x.doc_url,
            'date': x.publish_date.strftime("%Y-%m-%d")})

    response = {
        'rows': resource_rows,
        'current_page': current_page,
        'total_page': total_page,
        'page_list' : page_list
    }
    return HttpResponse(json.dumps(response), content_type='application/json')


def about(request):
    if get_language() == 'en-us':
        content = About.objects.all().first().content_en
    else:
        content = About.objects.all().first().content
    
    url = None
    if Resource.objects.filter(title='臺灣生物多樣性資訊聯盟章程').exists():
        url = Resource.objects.get(title='臺灣生物多樣性資訊聯盟章程').url
    return render(request, 'pages/about.html',{'url': url, 'content': content})


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
            # pi['title'] = p.title
            pi.update({'id': p.id})
            pi.update({'logo': p.logo})
            rows += [pi]
    partner = Partner.objects.filter(abbreviation=abbr).first()
    return render(request, 'pages/partner.html', {'rows': rows, 'partner': partner})


def resources(request):
    type = request.GET.get('type', 'all')
    return render(request, 'pages/resources.html', {'type': type})


def resources_link(request):
    n = Link.objects.all().first()
    return render(request, 'pages/resources_link.html', {'n': n})


def update_not_show(request):
    request.session['not_show_tech'] = True
    return JsonResponse({}, safe=False) 


def ark_ids(request):
    type = request.GET.get('type', 'news')
    return render(request, 'pages/ark_ids.html', {'type': type})


def get_ark_list(request):
    type = request.POST.get('type')
    lang = request.POST.get('lang', 'zh-hant')

    limit = 10
    
    query_obj = []

    query_obj = Ark.objects.filter(type=type).order_by('-modified')

    current_page = int(request.POST.get('get_page', 1))
    total_page = math.ceil(query_obj.count() / limit)
    page_list = get_page_list(current_page,total_page,5)

    rows = []
    offset = (current_page-1)*limit

    for x in query_obj[offset:offset+limit]:

        modified = x.modified + timedelta(hours=8) if x.modified else x.modified
        created = x.created + timedelta(hours=8)

        if type == 'news':
            url = f"{scheme}://{request.get_host()}/news/detail/{x.model_id}"
        else:
            url = f"{scheme}://{request.get_host()}/media/download/storage/tbia_{x.ark}.zip"
            
        rows.append({
            'ark_href': f'{env("TBIA_ARKLET_PUBLIC")}ark:/{env("ARK_NAAN")}/{x.ark}',
            'ark': f'ark:/{env("ARK_NAAN")}/{x.ark}',
            'url': url,
            'created': created.strftime("%Y-%m-%d"),
            'modified': modified.strftime("%Y-%m-%d"),    
        })

    response = {
        'rows': rows,
        'current_page': current_page,
        'total_page': total_page,
        'page_list' : page_list
    }

    return HttpResponse(json.dumps(response), content_type='application/json')


def datagap(request):
    # type = request.GET.get('type', 'all')
    return render(request, 'pages/datagap.html')
