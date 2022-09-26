from email import message
from django.contrib.auth.backends import ModelBackend
from django.http import request
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from conf.decorators import auth_user_should_not_access
from django.contrib.auth import authenticate, login, logout, tokens
from .models import User, Partner
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from .utils import generate_token, partner_source_map
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


def manager(request):
    partners = Partner.objects.all()
    return render(request, 'manager/manager.html', {'partners': partners})


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
                name = name,
                email = request.user.email,
                username = request.user.email,
                last_name =request.user.last_name,
                first_name =request.user.first_name,
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

    email = EmailMessage(subject=email_subject, body=email_body, from_email='no-reply@tbiadata.tw',to=[user.email])

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

            email = EmailMessage(subject=email_subject, body=email_body, from_email='no-reply@tbiadata.tw',to=[user.email])

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

            email = EmailMessage(subject=email_subject, body=email_body, from_email='no-reply@tbiadata.tw',to=[user.email])

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

    return redirect(request.META.get('HTTP_REFERER')) # return to previous page


def manager_partner(request):
    p_count = 0
    total_count = 0
    no_taxon = 0
    has_taxon = 0
    partner_admin = ''
    if not request.user.is_anonymous:
        current_user = request.user
        download_url = generate_no_taxon_csv(current_user.partner.group,request.scheme,request.META['HTTP_HOST'])
        # TODO 這邊會有問題
        partner_admin = User.objects.filter(partner_id=current_user.partner.id, is_partner_admin=True).values_list('name')
        partner_admin = [p[0] for p in partner_admin]
        partner_admin = ','.join(partner_admin)
        if current_user.partner.id:
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
            data_total = []
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



def manager_system(request):
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
                                                            'data_total':data_total,})


def generate_no_taxon_csv(p_name,scheme,host,update=False):
    CSV_MEDIA_FOLDER = 'no_taxon'
    csv_folder = os.path.join(settings.MEDIA_ROOT, CSV_MEDIA_FOLDER)
    filename = f'{p_name}_no_taxon.csv'
    csv_file_path = os.path.join(csv_folder, filename)
    
    solr_url = f"{SOLR_PREFIX}tbia_records/select?q=-taxonID:*&wt=csv&indent=true&fq=group:{p_name}&start=0&rows=2000000000&fl=occurrenceID"

    downloadURL = scheme+"://"+host+settings.MEDIA_URL+os.path.join(CSV_MEDIA_FOLDER, filename)
    if update or not os.path.exists(csv_file_path): # 指定要更新或沒有檔案才執行
        commands = f'curl "{solr_url}"  > {csv_file_path} '
        process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return downloadURL
    # curl "http://localhost:8888/solr/collection1/select?q=*%3A*&wt=cvs&indent=true&start=0&rows=2000000000&fl=id,title" > full-output-of-my-solr-index.csv


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
