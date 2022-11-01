from asyncio import staggered
from pickle import NONE
from venv import create
from django.contrib.auth.backends import ModelBackend
from django.http import request
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from conf.decorators import auth_user_should_not_access
from django.contrib.auth import authenticate, login, logout, tokens
from manager.models import SearchQuery, SensitiveDataRequest, SensitiveDataResponse, User, Partner, About
from pages.models import Feedback, News, Notification
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from manager.utils import generate_token, partner_source_map
from django.conf import settings
import threading
from django.http import (
    request,
    JsonResponse,
    HttpResponseRedirect,
    Http404,
    HttpResponse,
)
import json
from allauth.socialaccount.models import SocialAccount
from utils.solr_query import SOLR_PREFIX
import requests
from utils.solr_query import SolrQuery
import subprocess
import os
import time
from pages.models import Keyword
from ckeditor.fields import RichTextField
from django import forms
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, DateTimeField, ExpressionWrapper
from datetime import datetime, timedelta
from urllib import parse
from data.utils import map_collection, map_occurrence, get_key, create_query_display
from os.path import exists


class NewsForm(forms.ModelForm):
    content = RichTextField()

    class Meta:
        model  = News
        fields = ('content',)


class registerBackend(ModelBackend):
    def authenticate(self, email):
        user = User.objects.get(email=email, is_email_verified=True)
        if user:
            return user


class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)
    def run(self):
        self.email.send()


def send_feedback(request):
    if request.method == 'POST':
        # print(request.POST)
        partner_id = request.POST.get('partner_id')
        if partner_id == '0':
            partner_id = None
        email = request.POST.get('email')
        content = request.POST.get('content')
        type = request.POST.get('type')
        fb = Feedback.objects.create(
            partner_id = partner_id,
            email= email,
            content= content,
            type = type
        )

        for u in User.objects.filter(Q(is_system_admin=True)|Q(is_partner_admin=True, partner_id=partner_id)|Q(is_partner_account=True, partner_id=partner_id)):
            nn = Notification.objects.create(
                type = 2,
                content = fb.id,
                user = u
            )
            content = nn.get_type_display().replace('0000', str(nn.content))
            send_notification([u.id],content,'意見回饋通知')

        return JsonResponse({'status': 'success'}, safe=False)


def update_feedback(request):
    if request.method == 'POST':
        # print(request.POST)
        current_id = request.POST.get('current_id')
        if Feedback.objects.filter(id=current_id).exists():
            fb = Feedback.objects.get(id=current_id)
            if fb.is_replied:
                fb.is_replied = False
            else:
                fb.is_replied = True
            fb.save()

        return JsonResponse({'status': 'success'}, safe=False)



def manager(request):
    menu = request.GET.get('menu','info')
    partners = Partner.objects.all()
    # pr = []
    # if PartnerRequest.objects.filter(user_id=request.user.id,status__in=['pending','pass']).exists():
    #     pr = PartnerRequest.objects.get(user_id=request.user.id)
    notis = Notification.objects.filter(user_id=request.user.id)
    # TODO 未來要考慮檔案是否過期
    record = []
    for r in SearchQuery.objects.filter(user_id=request.user.id,type='record'):
        if r.modified:
            date = r.modified + timedelta(hours=8)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = ''

        # 整理查詢條件
        # 全站搜尋
        if 'from_full=yes' in r.query:
            search_str = dict(parse.parse_qsl(r.query)).get('search_str')
            search_dict = dict(parse.parse_qsl(search_str))

            query += f"<b>關鍵字</b>：{search_dict['keyword']}"
            
            if search_dict.get('record_type') == 'occ':
                map_dict = map_occurrence
            else:
                map_dict = map_collection
            key = map_dict.get(search_dict['key'])
            query += f"<br><b>{key}</b>：{search_dict['value']}"
            query += f"<br><b>學名</b>：{search_dict['scientificName']}"
        else:
        # 條件搜尋
            search_dict = dict(parse.parse_qsl(r.query))
            query = create_query_display(search_dict)

        record.append({
            'id': r.id,
            'query_id': r.query_id,
            'date':  date,
            'query':   query,
            'status': r.get_status_display()
        })



    taxon = []
    for t in SearchQuery.objects.filter(user_id=request.user.id,type='taxon'):
        if t.modified:
            date = t.modified + timedelta(hours=8)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = ''

        # 條件搜尋
        search_dict = dict(parse.parse_qsl(t.query))
        query = create_query_display(search_dict)

        taxon.append({
            'id': t.id,
            'query_id': t.query_id,
            'date':  date,
            'query':   query,
            'status': t.get_status_display()
        })


    sensitive = []

    for s in SearchQuery.objects.filter(user_id=request.user.id, type='sensitive'):
        if s.modified:
            date = s.modified + timedelta(hours=8)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = ''

        # 條件搜尋
        search_dict = dict(parse.parse_qsl(s.query))
        query = create_query_display(search_dict)

    # for sdr in SensitiveDataResponse.objects.filter(query_id__in=SearchQuery.objects.filter(user_id=request.user.id, type='senstive').values('query_id')):

        # 審查意見
        comment = []

        for sdr in SensitiveDataResponse.objects.filter(query_id=s.query_id):
            if sdr.partner:
                partner_name = '內政部營建署城鄉發展分署' if sdr.partner.id == 4 else sdr.partner.breadtitle 
            else:
                partner_name = 'TBIA聯盟'
            comment.append(f"""
            <b>審查單位：</b>{partner_name}
            <br>
            <b>審查者姓名：</b>{sdr.reviewer_name}
            <br>
            <b>審查意見：</b>{sdr.comment if sdr.comment else "" }
            <br>
            <b>審查結果：</b>{sdr.get_status_display()}
            """)

        sensitive.append({
            'id': s.id,
            'query_id': s.query_id,
            'date':  date,
            'query':   query,
            'status': s.get_status_display(),
            'comment': '<hr>'.join(comment) if comment else ''
        })

    return render(request, 'manager/manager.html', {'partners': partners, 'menu': menu, 'notis': notis,
    'record': record, 'taxon': taxon, 'sensitive': sensitive})


def update_personal_info(request):
    if request.method == 'POST':
        user = User.objects.get(email=request.POST.get('email'))
        user.name = request.POST.get('name')
        user.save()
        response = {'message': '修改完成'}
        # 不一定要修改密碼
        if request.POST.get('has_password') == 'true':
        # 確定密碼是否正確
            if user.check_password(request.POST.get('now_password')):
                user.set_password(request.POST.get('new_password'))
                user.save()
                logout(request)
                response = {'message': '修改完成！請重新登入'}
            else:
                response = {'message': '現在的密碼錯誤'}
        
        return JsonResponse(response, safe=False)


def get_auth_callback(request):
    if email := request.user.email:
        if User.objects.filter(email=email).exists():
            u = User.objects.filter(email=email).first()
            if not u.first_login:
                login(request, u, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('index')
            else:
                u.first_login = False
                u.username = email
                u.name = u.first_name +  ' ' + u.last_name
                u.save()
                login(request, u, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('register_success')
        else:
            data = SocialAccount.objects.get(user=request.user).extra_data
            name = data.get('name')
            new_user = User(
                name = data.get('name'),
                email = data.get('email'),
                username = data.get('email'),
                last_name = data.get('family_name'),
                first_name = data.get('given_name'),
                is_email_verified = True,
                is_active = True,
            )
            new_user.save()
            return redirect('register_success')


def send_verification_email(user, request):
    current_site = get_current_site(request)  # the domain user is on

    email_subject = '[生物多樣性資料庫共通查詢系統] 驗證您的帳號'
    email_body = render_to_string('manager/verification.html',{
        'scheme': request.scheme,
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)), # encrypt userid for security
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject=email_subject, body=email_body, from_email='TBIA <no-reply@tbiadata.tw>',to=[user.email])

    EmailThread(email).start()



def resend_verification_email(request):
    if request.method == 'POST':
        if User.objects.filter(email=request.POST.get('email','')).exists():
            user = User.objects.get(email=request.POST.get('email',''))
            current_site = get_current_site(request)  # the domain user is on

            email_subject = '[生物多樣性資料庫共通查詢系統] 驗證您的帳號'
            email_body = render_to_string('manager/verification.html',{
                'scheme': request.scheme,
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)), # encrypt userid for security
                'token': generate_token.make_token(user)
            })

            email = EmailMessage(subject=email_subject, body=email_body, from_email='TBIA <no-reply@tbiadata.tw>',to=[user.email])

            EmailThread(email).start()
            return JsonResponse({"status": 'success'}, safe=False)
        else:
            return JsonResponse({"status": 'fail'}, safe=False)


def verify_user(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        user.is_email_verified = True
        user.is_active = True
        user.first_login = False
        user.save()

        # messages.add_message(request, messages.SUCCESS,
        #                     '驗證成功！請立即設定您的密碼')
        login(request, user, backend='manager.views.registerBackend') 
        return redirect(register_success)

    return render(request, 'manager/verification-fail.html', {"user": user})



def send_reset_password(request):
    if request.method == 'POST':
        if User.objects.filter(email=request.POST.get('email','')).exists():
            user = User.objects.get(email=request.POST.get('email',''))
            current_site = get_current_site(request)  # the domain user is on

            email_subject = '[生物多樣性資料庫共通查詢系統] 重設您的密碼'
            email_body = render_to_string('manager/verification_reset_password.html',{
                'scheme': request.scheme,
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)), # encrypt userid for security
                'token': generate_token.make_token(user)
            })

            email = EmailMessage(subject=email_subject, body=email_body, from_email='TBIA <no-reply@tbiadata.tw>',to=[user.email])

            EmailThread(email).start()
            return JsonResponse({"message": '已送出重設密碼信件'}, safe=False)
        else:
            return JsonResponse({"message": '輸入的Email錯誤'}, safe=False)



def verify_reset_password(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        request.session['email'] = user.email
        return redirect(reset_password)

    return render(request, 'manager/verification-fail.html', {"user": user})


def reset_password(request):
    email = request.session['email']
    return render(request, 'manager/reset_password.html', {'email': email})


def reset_password_submit(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if User.objects.filter(email=email).exists():
            u = User.objects.filter(email=email).get()
            u.set_password(password)
            u.save()
            response = {'status':'success', 'message': '重設密碼成功，請重新登入'}
        else:
            response = {'status':'fail', 'message': '發生未知錯誤！請聯絡管理員'}

        return HttpResponse(json.dumps(response), content_type='application/json')


# @auth_user_should_not_access
def register(request):
    if request.method == 'POST':
        context = {'has_error': False, 'data': request.POST}
        email = request.POST.get('email')
        request.session['email'] = email
        name = request.POST.get('name')
        password = request.POST.get('password')
        
        # make sure email is unique
        if User.objects.filter(email=email,is_email_verified=True).exists():
            # messages.add_message(request, messages.ERROR, '此信箱已註冊過')
            response = {'status':'fail', 'message': '此信箱已註冊過，請直接登入'}
            # return render(request,'account/register.html', context, status=409) # conflict
        else:
            if not User.objects.filter(email=email).exists():
                user=User.objects.create_user(email=email, name=name, password=password, is_email_verified=False, is_active=False)
                user.save()
            else:
                user = User.objects.get(email=email)
            send_verification_email(user, request)
            # messages.add_message(request, messages.SUCCESS,
            # '註冊成功，請至註冊信箱收信進行驗證')
            response = {'status':'success', 'message': '註冊成功，請至註冊信箱收信進行驗證'}
            # return redirect(register_verification)
        return HttpResponse(json.dumps(response), content_type='application/json')



def register_verification(request):
    email = request.session['email']
    return render(request, 'manager/register_verification.html', {'email': email})


def register_success(request):
    return render(request, 'manager/register_success.html')


# @auth_user_should_not_access
def login_user(request):
    if request.method == 'POST':
        # username是django用來登入的default
        email = request.POST.get('email')
        if User.objects.filter(email=email).exists():
            username = User.objects.get(email=email).username
            password = request.POST.get('password')
            rememberme = request.POST.get('rememberme')
            user = authenticate(request, username=username, password=password)
            if user and user.is_email_verified:
                if not rememberme:
                    request.session.set_expiry(0)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                # return redirect('index')
                response = {'status':'success', 'message': '登入成功'}

            if user and not user.is_email_verified:
                # messages.add_message(request, messages.ERROR,
                #                      'Email尚未驗證，請至信箱進行驗證')
                response = {'status':'unverified', 'message': 'Email尚未驗證，請至信箱進行驗證'}
                # return render(request, 'account/login.html', context, status=401)
            if not user:
                # messages.add_message(request, messages.ERROR,
                #                      'Email或密碼錯誤，或此帳號停用')
                response = {'status':'fail', 'message': '密碼錯誤，或此帳號停用'}
                # return render(request, 'account/login.html', context, status=401)
        else:
            response = {'status':'fail', 'message': '此Email不存在，請先註冊'}

    return HttpResponse(json.dumps(response), content_type='application/json')


def logout_user(request):

    logout(request)

    return redirect('index') # return to previous page



def update_partner_info(request):
    if request.method == 'POST':
        # 先取得原本的dictionary
        partner_id = request.POST.get('partner_id')
        info = Partner.objects.get(id=partner_id).info
        new_info = []
        for l in range(len(info)):
            i = info[l]
            new_info.append({
                'id': i['id'],
                'link': request.POST.get(f'link_{l}'),
                'logo': i['logo'],
                'image': i['image'],
                'subtitle': i['subtitle'],
                'description': request.POST.get(f'description_{l}'),
            })
        p = Partner.objects.get(id=partner_id)
        p.info = new_info
        p.save()
        response = {'message': '修改完成'}
        
        return JsonResponse(response, safe=False)


def generate_no_taxon_csv(p_name,scheme,host,update=False):
    CSV_MEDIA_FOLDER = 'no_taxon'
    csv_folder = os.path.join(settings.MEDIA_ROOT, CSV_MEDIA_FOLDER)
    filename = f'{p_name}_no_taxon.csv'
    csv_file_path = os.path.join(csv_folder, filename)
    
    solr_url = f"{SOLR_PREFIX}tbia_records/select?q=-taxonID:*&wt=csv&indent=true&fq=group:{p_name}&start=0&rows=2000000000&fl=occurrenceID,rightsHolder"

    downloadURL = scheme+"://"+host+settings.MEDIA_URL+os.path.join(CSV_MEDIA_FOLDER, filename)
    if update or not os.path.exists(csv_file_path): # 指定要更新或沒有檔案才執行
        commands = f'curl "{solr_url}"  > {csv_file_path} '
        process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return downloadURL
    # curl "http://localhost:8888/solr/collection1/select?q=*%3A*&wt=cvs&indent=true&start=0&rows=2000000000&fl=id,title" > full-output-of-my-solr-index.csv


def update_keywords(request):
    if request.method == 'POST':
        for i in range(3):
            order = i+1
            Keyword.objects.filter(order=order).update(keyword=request.POST.get(f"keyword_{order}"))
        return JsonResponse({"status": 'success'}, safe=False)


def send_partner_request(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        partner_id = request.POST.get('partner_id')
        u = User.objects.get(id=user_id)
        u.partner_id = partner_id
        u.status = 'pending'
        u.save()
        # 寄送通知給系統管理員 & 單位管理員
        # type = 5
        for u in User.objects.filter(Q(is_system_admin=True)|Q(is_partner_admin=True, partner_id=partner_id)):
            nn = Notification.objects.create(
                type = 5,
                content = user_id,
                user = u
            )
            content = nn.get_type_display().replace('0000', str(nn.content))
            send_notification([u.id],content,'單位帳號申請通知')
        response = {'message': '申請已送出'}
        return JsonResponse(response, safe=False)


def withdraw_partner_request(request):
    user_id = request.POST.get('user_id')
    User.objects.filter(id=user_id).update(status='withdraw')
    response = {'message': '申請已撤回'}
    return JsonResponse(response, safe=False)


def partner_news(request):
    menu = request.GET.get('menu','list')
    form = NewsForm()
    n = []
    if news_id := request.GET.get('news_id'):
        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            form.fields["content"].initial = n.content
    if not request.user.is_anonymous:
        current_user = request.user
        if current_user.is_partner_admin:
            # 如果是單位管理者 -> 回傳所有
            news_list = News.objects.filter(partner_id=current_user.partner_id).order_by('-modified')
        else:
            # 如果是單位帳號 -> 只回傳自己申請的
            news_list = News.objects.filter(user_id=current_user).order_by('-modified')

    return render(request, 'manager/partner/news.html', {'form':form, 'menu': menu, 'n': n, 'news_list': news_list})


def partner_info(request):
    menu = request.GET.get('menu','info')
    partner_admin = ''
    info = []
    partner_members = []
    # pr = []
    if not request.user.is_anonymous:
        current_user = request.user
        if current_user.partner:
            # TODO 這邊會有問題
            partner_admin = User.objects.filter(partner_id=current_user.partner.id, is_partner_admin=True).values_list('name')
            partner_admin = [p[0] for p in partner_admin]
            partner_admin = ','.join(partner_admin)
            # info
            info = Partner.objects.filter(group=current_user.partner.group).values_list('info')
            # 單位帳號管理，統一由partner request判斷，但還要加partner_admin進去
            # pr = PartnerRequest.objects.filter(partner_id=current_user.partner.id)

            partner_members = User.objects.filter(partner_id=current_user.partner.id).exclude(status='withdraw').exclude(id=current_user.id)
            status_choice = User._meta.get_field('status').choices[:-1]
            feedback = Feedback.objects.filter(partner_id=current_user.partner.id).annotate(
                created_8=ExpressionWrapper(
                    F('created') + timedelta(hours=8),
                    output_field=DateTimeField()
                ))
            
    sensitive = []
    for sdr in SensitiveDataResponse.objects.filter(partner_id=current_user.partner.id):
        created = sdr.created + timedelta(hours=8)
        created = created.strftime('%Y-%m-%d %H:%M:%S')

        # 整理查詢條件
        if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
            r = SearchQuery.objects.get(query_id=sdr.query_id)
            search_dict = dict(parse.parse_qsl(r.query))
            query = create_query_display(search_dict)

        sensitive.append({
            'id': sdr.id,
            'query_id': r.query_id,
            'created':  created,
            'query':   query,
            'status': sdr.get_status_display()
        })

    return render(request, 'manager/partner/info.html', {'partner_admin': partner_admin,  'info': info, 'feedback': feedback,
                                    'menu': menu, 'partner_members': partner_members, 'status_choice': status_choice, 'sensitive': sensitive})


def get_request_detail(request):
    detail = {}
    review = {}
    if query_id := request.GET.get('query_id'):
        if SensitiveDataRequest.objects.filter(query_id=query_id).exists():
            detail = SensitiveDataRequest.objects.filter(query_id=query_id).values()[0]
    if sdr_id := request.GET.get('sdr_id'):
        if SensitiveDataResponse.objects.filter(id=sdr_id).exists():
            review = SensitiveDataResponse.objects.filter(id=sdr_id).values()[0]
    return JsonResponse({'detail': detail, 'review': review}, safe=False)


def manager_partner(request):
    # TODO 根據權限給使用者審核的部分
    p_count = 0
    total_count = 0
    no_taxon = 0
    has_taxon = 0
    partner_admin = ''
    download_url = ''
    info = []
    data_total = []
    if not request.user.is_anonymous:
        current_user = request.user
        if current_user.partner:
            download_url = generate_no_taxon_csv(current_user.partner.group,request.scheme,request.META['HTTP_HOST'])
            # TODO 這邊會有問題
            partner_admin = User.objects.filter(partner_id=current_user.partner.id, is_partner_admin=True).values_list('name')
            partner_admin = [p[0] for p in partner_admin]
            partner_admin = ','.join(partner_admin)
            # info
            info = Partner.objects.filter(group=current_user.partner.group).values_list('info')
            # TODO subtitle 和 rightsHolder寫法可能不同
            # partner_db = Partner.objects.filter(group=current_user.partner.group).values_list('subtitle')
            # partner_db = [p[0] for p in partner_db]
            # f = []
            # f += [f'rightsHolder:"{pdb}"']
            f = ['-taxonID:*',f'group:{current_user.partner.group}']
            # TaiCOL對應狀況
            query = {
                "query": '*:*',
                "filter": f,
                "limit": 0,
                "facet": {},
                }
            response = requests.post(f'{SOLR_PREFIX}tbia_records/select', data=json.dumps(query), headers={'content-type': "application/json" })
            no_taxon = response.json()['response']['numFound']
            # 資料筆數
            url = f"{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet=true&indent=true&q.op=OR&q=group%3A{current_user.partner.group}&rows=0&start=0"
            data = requests.get(url).json()
            if data['responseHeader']['status'] == 0:
                facets = data['facet_counts']['facet_fields']['rightsHolder']
                for r in range(0,len(facets),2):
                    p_count += facets[r+1]

            url = f"{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet=true&indent=true&q.op=OR&q=group%3A{current_user.partner.group}&rows=0&start=0"
            data = requests.get(url).json()
            if data['responseHeader']['status'] == 0:
                facets = data['facet_counts']['facet_fields']['rightsHolder']
                for r in range(0,len(facets),2):
                    if facets[r+1] > 0 :
                        data_total.append({'name': facets[r],'y': facets[r+1]})
            solr = SolrQuery('tbia_records')
            query_list = [('q', '*:*'),('rows', 0)]
            req = solr.request(query_list)
            total_count = req['solr_response']['response']['numFound']
            total_count = total_count - p_count
            data_total += [{'name':'其他單位','y':total_count}]
            has_taxon = p_count-no_taxon
    return render(request, 'manager/partner/manager.html',{'partner_admin': partner_admin, 'no_taxon': no_taxon, 'has_taxon': has_taxon,
                                                            'total_count': total_count, 'p_count': p_count, 'download_url': download_url,
                                                            'info': info, 'data_total': data_total})


def manager_system(request):
    keywords = Keyword.objects.all().order_by('order').values_list('keyword', flat=True)
    no_taxon = 0
    has_taxon = 0
    partner_admin = ''
    data_total = []
    if not request.user.is_anonymous:
        # 資料筆數 - 改成用單位?
        url = f"{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0&start=0"
        data = requests.get(url).json()
        if data['responseHeader']['status'] == 0:
            facets = data['facet_counts']['facet_fields']['rightsHolder']
            for r in range(0,len(facets),2):
                data_total.append({'name': facets[r],'y': facets[r+1]})
        # TaiCOL對應狀況
        solr = SolrQuery('tbia_records')
        query_list = [('q', '*:*'),('rows', 0)]
        req = solr.request(query_list)
        total_count = req['solr_response']['response']['numFound']
        solr = SolrQuery('tbia_records')
        query_list = [('q', '-taxonID:*'),('rows', 0)]
        req = solr.request(query_list)
        no_taxon = req['solr_response']['response']['numFound']
        has_taxon = total_count - no_taxon
    return render(request, 'manager/system/manager.html',{'partner_admin': partner_admin, 'no_taxon': no_taxon, 'has_taxon': has_taxon,
                                                            'data_total':data_total,'keywords': keywords})


def update_tbia_about(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        a = About.objects.all().first()
        a.content = content
        a.save()
        return JsonResponse({"status": 'success'}, safe=False)


def system_news(request):
    menu = request.GET.get('menu','list')
    form = NewsForm()
    # if current_a:
    #     form.fields["content"].initial = current_a.content
    news_list = News.objects.all().order_by('-modified')
    status_list = News.status.field.choices
    n = []
    if news_id:= request.GET.get('news_id'):
        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            form.fields["content"].initial = n.content
    return render(request, 'manager/system/news.html', {'form':form, 'menu': menu, 'news_list': news_list, 'status_list': status_list, 'n': n})


def system_info(request):
    system_admin = ''
    system_admin = User.objects.filter(is_system_admin=True).values_list('name')
    system_admin = [s[0] for s in system_admin]
    system_admin = ','.join(system_admin)

    content = About.objects.all().first().content
    menu = request.GET.get('menu','list')
    partner_members = User.objects.filter(partner_id__isnull=False).exclude(status='withdraw')
    status_choice = User._meta.get_field('status').choices[:-1]
    feedback = Feedback.objects.all().annotate(
        created_8=ExpressionWrapper(
            F('created') + timedelta(hours=8),
            output_field=DateTimeField()
        ))

    sensitive = []
    for sdr in SensitiveDataResponse.objects.filter(partner_id=None):
        created = sdr.created + timedelta(hours=8)
        created = created.strftime('%Y-%m-%d %H:%M:%S')

        # 整理查詢條件
        if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
            r = SearchQuery.objects.get(query_id=sdr.query_id)
            search_dict = dict(parse.parse_qsl(r.query))
            query = create_query_display(search_dict)

        sensitive.append({
            'id': sdr.id,
            'query_id': r.query_id,
            'created':  created,
            'query':   query,
            'status': sdr.get_status_display(),
            'is_transferred': sdr.is_transferred
        })
    return render(request, 'manager/system/info.html', {'menu': menu, 'content': content, 
                        'system_admin': system_admin, 'partner_members': partner_members,
                        'status_choice': status_choice, 'feedback': feedback, 'sensitive': sensitive})


def system_resource(request):
    menu = request.GET.get('menu','list')
    return render(request, 'manager/system/resource.html', {'menu': menu})


def system_keyword(request):
    keywords = Keyword.objects.all().order_by('order').values_list('keyword', flat=True)
    return render(request, 'manager/system/keyword.html', {'keywords':keywords})


def submit_news(request):
    if request.method == 'POST':
        current_user = request.user
        title = request.POST.get('title')
        type = request.POST.get('type')
        news_id = request.POST.get('news_id') if request.POST.get('news_id') else 0
        status = request.POST.get('status','pending')

        if request.POST.get('from_system'):
            # status = 'pass'
            partner_id = None
        else:
            # status = 'pending'
            partner_id = current_user.partner

        form = NewsForm(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']

        image_name = None
        if image := request.FILES.get('image'):
            fs = FileSystemStorage()
            image_name = fs.save(f'news/' + image.name, image)

        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            ori_status = n.status
            if status == 'pass' and ori_status != 'pass':
                publish_date = timezone.now()
            elif status == 'pass' and ori_status == 'pass':
                publish_date = n.publish_date
            else:
                publish_date = None
            if n.image and not image_name: # 原本就有的
                image_name = n.image
            elif image_name:
                image_name = image.name
            if image_name:
                n.type = type
                n.title = title
                n.content = content
                n.image = image_name
                n.status = status
                n.modified = timezone.now()
                n.publish_date = publish_date
                n.save()
            else:
                n.type = type
                n.title = title
                n.content = content
                n.image = None
                n.status = status
                n.publish_date = publish_date
                n.modified = timezone.now()
                n.save()
        else:
            ori_status = 'pending'
            if status == 'pass':
                publish_date = timezone.now()
            else:
                publish_date = None

            if image_name:
                n = News.objects.create(
                    type = type,
                    user = current_user,
                    partner = partner_id,
                    title = title,
                    content = content,
                    image = image.name,
                    status = status,
                    publish_date = publish_date
                )
            else:
                n = News.objects.create(
                    type = type,
                    user = current_user,
                    partner = partner_id,
                    title = title,
                    content = content,
                    status = status,
                    publish_date = publish_date
                )
        if request.POST.get('from_system'):
            if ori_status =='pending' and status in ['pass', 'fail']:
                for u in User.objects.filter(is_system_admin=True):
                    nn = Notification.objects.create(
                        type = 8,
                        content = n.id,
                        user = u
                    )
                    content = nn.get_type_display().replace('0000', str(nn.content))
                    send_notification([u.id],content,'消息發布申請結果')
            return redirect('system_news')
        else:
            # 新增送審通知
            if status == 'pending':
                for u in User.objects.filter(is_system_admin=True):
                    nn = Notification.objects.create(
                        type = 7,
                        content = n.id,
                        user = u
                    )
                    content = nn.get_type_display().replace('0000', str(nn.content))
                    send_notification([u.id],content,'消息發布申請通知')
            if ori_status =='pending' and status in ['pass', 'fail']:
                for u in User.objects.filter(is_system_admin=True):
                    nn = Notification.objects.create(
                        type = 8,
                        content = n.id,
                        user = u
                    )
                    content = nn.get_type_display().replace('0000', str(nn.content))
                    send_notification([u.id],content,'消息發布申請結果')

            return redirect('partner_news')


def withdraw_news(request):
    if news_id := request.GET.get('news_id'):
        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            n.status = 'withdraw'
            n.save()
    return redirect('partner_news')


def send_msg(msg):
    msg.send()


@csrf_exempt
def send_notification(user_list, content, title):
    try:
        email_list = []
        email = User.objects.filter(id__in=user_list).values('email')
        for e in email:
            email_list += [e['email']]

        # send email
        html_content = f"""
        您好：
        <br>
        <br>
        {content}
        <br>

        """
        subject = '[生物多樣性資料庫共通查詢系統] ' + title

        msg = EmailMessage(subject=subject, body=html_content, from_email='TBIA <no-reply@tbiadata.tw>', to=email_list)
        msg.content_subtype = "html"  # Main content is now text/html
        # 改成背景執行
        task = threading.Thread(target=send_msg, args=(msg,))
        # task.daemon = True
        task.start()
        return {"status": 'success'}
    except:
        return {"status": 'fail'}


def update_user_status(request):
    if request.method == 'POST':
        status = request.POST.get('status')
        if User.objects.filter(id=request.POST.get('user_id')).exists():
            u = User.objects.get(id=request.POST.get('user_id'))
            u.status = status
            if status == 'pass':
                if request.POST.get('role') == 'is_partner_account':
                    u.is_partner_account = True
                    u.is_partner_admin = False
                    u.is_staff = True
                else:
                    u.is_partner_account = False
                    u.is_partner_admin = True
                    u.is_staff = True
            else:
                u.is_partner_account = False
                u.is_partner_admin = False
                u.is_staff = False
            u.save()

            if status != 'pending':
                nn = Notification.objects.create(
                    type = 6,
                    content = u.get_status_display(),
                    user = u
                )
                content = nn.get_type_display().replace('0000', str(nn.content))
                send_notification([u.id],content,'單位帳號申請結果通知')


        return JsonResponse({"status": 'success'}, safe=False)



# # ---- system ---- #
# @login_required
# def system_feedback(request):
#     return render(request, 'manager/system/feedback.html')


# @login_required
# def system_index(request):
#     return render(request, 'manager/system/index.html')


# @login_required
# def system_resource(request):
#     return render(request, 'manager/system/resource.html')


# @login_required
# def system_review(request):
#     return render(request, 'manager/system/review.html')


# @login_required
# def system_download(request):
#     return render(request, 'manager/system/download.html')


# # ---- unit ---- #
# @login_required
# def unit_feedback(request):
#     return render(request, 'manager/unit/feedback.html')


# @login_required
# def unit_index(request):
#     return render(request, 'manager/unit/index.html')


# @login_required
# def unit_resource(request):
#     return render(request, 'manager/unit/resource.html')


# @login_required
# def unit_review(request):
#     return render(request, 'manager/unit/review.html')


# @login_required
# def unit_download(request):
#     return render(request, 'manager/unit/download.html')


# @login_required
# def unit_event(request):
#     return render(request, 'manager/unit/event.html')


# @login_required
# def unit_info(request):
#     return render(request, 'manager/unit/info.html')


# @login_required
# def unit_news(request):
#     return render(request, 'manager/unit/news.html')


# @login_required
# def unit_project(request):
#     return render(request, 'manager/unit/project.html')


