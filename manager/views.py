from django.contrib.auth.backends import ModelBackend
from django.db import connection
from django.http import request
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from conf.decorators import auth_user_should_not_access
from django.contrib.auth import authenticate, login, logout, tokens
from manager.models import *
from pages.models import Feedback, News, Notification, Resource, Link
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from manager.utils import generate_token, check_due
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
from conf.settings import SOLR_PREFIX
import requests
import subprocess
import os
import time
from pages.models import Keyword, Qa
from ckeditor.fields import RichTextField
from django import forms
from django.core.files.storage import FileSystemStorage
from django.utils import timezone, translation
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, DateTimeField, ExpressionWrapper, Max, Sum
from datetime import datetime, timedelta
from urllib import parse
from data.utils import map_collection, map_occurrence, get_key, create_query_display, get_page_list, create_query_a, query_a_href, taxon_group_map_c
from os.path import exists
import math

import pandas as pd
from pathlib import Path
from conf.utils import scheme

import pytz

from django.utils.translation import get_language, gettext


class NewsForm(forms.ModelForm):
    content = RichTextField()
    class Meta:
        model = News
        fields = (
            'content',
        )

class LinkForm(forms.ModelForm):
    content = RichTextField()
    class Meta:
        model  = Link
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


def get_is_authenticated(request):
    check_if_authenticated = False
    if not request.user.is_anonymous:  
        u = request.user
        if u.is_active:
            check_if_authenticated = True
        else:
            check_if_authenticated = False
    return JsonResponse({'is_authenticated': check_if_authenticated}, safe=False)
                

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

        # 先暫時調整成只寄通知給系統管理員
        for u in User.objects.filter(is_system_admin=True):
        # for u in User.objects.filter(Q(is_system_admin=True)|Q(is_partner_admin=True, partner_id=partner_id)|Q(is_partner_account=True, partner_id=partner_id)):
            nn = Notification.objects.create(
                type = 2,
                content = fb.id,
                user = u
            )
            content = nn.get_type_display().replace('0000', str(nn.content))
            content = content.replace("，請至後台查看", "")
            # 加上內容
            # Email	類型	內容
            content += f"<br><br><b>回饋者email：</b>{fb.email}"
            content += f"<br><b>回饋類型：</b>{Feedback.objects.get(id=fb.id).get_type_display()}"
            content += f"<br><b>回饋內容：</b>{fb.content}"
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


def change_manager_page(request):
    # 這邊和帳號後台相關的要translation active
    lang = request.GET.get('lang')
    translation.activate(lang)
    page = request.GET.get('page')
    menu = request.GET.get('menu')
    offset = (int(page)-1) * 10
    response = {}
    # print(page)
    now = datetime.now()
    now = now.replace(tzinfo=pytz.timezone('UTC'))
    data = []
    if menu == 'notification': # 個人帳號後台通知
        
        notifications = Notification.objects.filter(user_id=request.user.id).order_by('-created')[offset:offset+10]
        # results = ""
        for n in notifications:
            created = n.created + timedelta(hours=8)
            content = '<p>' + gettext(n.get_type_display()).replace('0000', n.content)+ '</p>'
            if not n.is_read:
                content = '<div class="noti-dottt"></div>' + content
                content = f'<div class="d-flex">{content}</div>'
            data.append({'created': created.strftime('%Y-%m-%d %H:%M:%S'), 
                        'content': content})

        total_page = math.ceil(Notification.objects.filter(user_id=request.user.id).count() / 10)

    elif menu == 'download_taxon': # 個人帳號名錄下載

        for t in SearchQuery.objects.filter(user_id=request.user.id,type='taxon').order_by('-id')[offset:offset+10]:
            if t.modified:
                date = t.modified + timedelta(hours=8)
                date = date.strftime('%Y-%m-%d %H:%M:%S')
                if t.status != 'expired':
                    if now - t.modified > timedelta(days=335) and now < t.modified + timedelta(days=365):
                        expired_date = t.modified + timedelta(days=365)
                        date += f'<br><span class="expired-notice">*{gettext("資料下載連結將於")}{expired_date.year}-{expired_date.month}-{expired_date.day}{gettext("後失效")}</span>'
            else:
                date = ''

            # 進階搜尋
            search_dict = dict(parse.parse_qsl(t.query))
            query = create_query_display(search_dict, lang)
            link = ''
            if t.status == 'pass' and t.status != 'expired':
                link = f'<a class="manager_btn" target="_blank" href="/media/download/taxon/tbia_{ t.query_id }.zip">{gettext("下載")}</a>'

            if search_dict.get("record_type") == 'col':
                search_prefix = 'collection'
            else:
                search_prefix = 'occurrence'
            tmp_a = create_query_a(search_dict)
            for i in ['locality','datasetName','rightsHolder','total_count']:
                if i in search_dict.keys():
                    search_dict.pop(i)

            query_a = f'/search/{search_prefix}?' + parse.urlencode(search_dict) + tmp_a

            query = query_a_href(query,query_a)
            
            data.append({
                'id': f"#{t.personal_id}",
                'query_id': t.query_id,
                'date':  date,
                'query':   query,
                'status': gettext(t.get_status_display()),
                'link': link
            })

        total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id,type='taxon').count() / 10)
    
    elif menu == 'sensitive': # 個人帳號敏感資料

        for s in SearchQuery.objects.filter(user_id=request.user.id, type='sensitive').order_by('-id')[offset:offset+10]:
            if s.modified:
                date = s.modified + timedelta(hours=8)
                date = date.strftime('%Y-%m-%d %H:%M:%S')
                if s.status != 'expired':
                    if now - s.modified > timedelta(days=335) and now < s.modified + timedelta(days=365):
                        expired_date = s.modified + timedelta(days=365)
                        date += f'<br><span class="expired-notice">*{gettext("資料下載連結將於")}{expired_date.year}-{expired_date.month}-{expired_date.day}{gettext("後失效")}</span>'
            else:
                date = ''

            # 進階搜尋
            search_dict = dict(parse.parse_qsl(s.query))
            query = create_query_display(search_dict, lang)

            if search_dict.get("record_type") == 'col':
                search_prefix = 'collection'
            else:
                search_prefix = 'occurrence'
            tmp_a = create_query_a(search_dict)
            for i in ['locality','datasetName','rightsHolder','total_count']:
                if i in search_dict.keys():
                    search_dict.pop(i)

            query_a = f'/search/{search_prefix}?' + parse.urlencode(search_dict) + tmp_a

            query = query_a_href(query,query_a)

            # 審查意見
            comment = []

            for sdr in SensitiveDataResponse.objects.filter(query_id=s.query_id).exclude(is_transferred=True, partner_id__isnull=True):
                if sdr.partner:
                    if lang == 'en-us':
                        partner_name = sdr.partner.select_title_en
                    else:
                        partner_name = sdr.partner.select_title 
                else:
                    if lang == 'en-us':
                        partner_name = 'Taiwan Biodiversity Information Alliance'
                    else:
                        partner_name = 'TBIA 臺灣生物多樣性資訊聯盟'
                comment.append(f"""<b>{gettext("審查單位")}{gettext("：")}</b>{partner_name}<br><b>{gettext("審查者姓名")}{gettext("：")}</b>{sdr.reviewer_name}<br><b>{gettext("審查意見")}{gettext("：")}</b>{sdr.comment if sdr.comment else "" }<br><b>{gettext("審查結果")}{gettext("：")}</b>{gettext(sdr.get_status_display())}""")

            link = ''
            if s.status == 'pass' and s.status != 'expired':
                link = f'<a class="manager_btn" target="_blank" href="/media/download/sensitive/tbia_{ s.query_id }.zip">{gettext("下載")}</a>'

            data.append({
                'id': f'#{s.personal_id}',
                'query_id': s.query_id,
                'date':  date,
                'query':   query,
                'comment': '<hr>'.join(comment) if comment else '',
                'status': gettext(s.get_status_display()),
                'link': link
            })
        total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id, type='sensitive').count() / 10)
    
    elif menu == 'download': # 個人帳號資料下載

        for r in SearchQuery.objects.filter(user_id=request.user.id,type='record').order_by('-id')[offset:offset+10]:
            if r.modified:
                date = r.modified + timedelta(hours=8)
                date = date.strftime('%Y-%m-%d %H:%M:%S')
                if r.status != 'expired':
                    if now - r.modified > timedelta(days=335) and now < r.modified + timedelta(days=365):
                        expired_date = r.modified + timedelta(days=365)
                        date += f'<br><span class="expired-notice">*{gettext("資料下載連結將於")}{expired_date.year}-{expired_date.month}-{expired_date.day}{gettext("後失效")}</span>'
            else:
                date = ''

            # 整理搜尋條件
            # 全站搜尋
            query = ''
            if 'from_full=yes' in r.query:
                search_str = dict(parse.parse_qsl(r.query)).get('search_str')
                search_dict = dict(parse.parse_qsl(search_str))
                # print(search_dict)

                query += f"<b>{gettext('關鍵字')}</b>{gettext('：')}{search_dict['keyword']}"
                
                if search_dict.get('record_type') == 'occ':
                    map_dict = map_occurrence
                else:
                    map_dict = map_collection
                key = map_dict.get(search_dict['key'])
                query += f"<br><b>{gettext(key)}</b>{gettext('：')}{search_dict['value']}"
                if search_dict.get('scientific_name'):
                    query += f"<br><b>{gettext('學名')}</b>{gettext('：')}{search_dict['scientific_name']}"
                if 'total_count' in search_dict.keys():
                    search_dict.pop('total_count')
                query_a = '/search/full?' + parse.urlencode(search_dict)

            else:
            # 進階搜尋
                search_dict = dict(parse.parse_qsl(r.query))
                query = create_query_display(search_dict, lang)

                if search_dict.get("record_type") == 'col':
                    search_prefix = 'collection'
                else:
                    search_prefix = 'occurrence'
                tmp_a = create_query_a(search_dict)
                for i in ['locality','datasetName','rightsHolder','total_count']:
                    if i in search_dict.keys():
                        search_dict.pop(i)

                query_a = f'/search/{search_prefix}?' + parse.urlencode(search_dict) + tmp_a

            link = ''
            if r.status == 'pass' and r.status != 'expired':
                link = f'<a class="manager_btn" target="_blank" href="/media/download/record/tbia_{ r.query_id }.zip">{gettext("下載")}</a>'

            query = query_a_href(query,query_a,lang)
            
            data.append({
                'id': f'#{r.personal_id}',
                'query_id': r.query_id,
                'date': date,
                'query': query,
                'status': gettext(r.get_status_display()),
                'link': link,
            })

        total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id,type='record').count() / 10)

    elif menu == 'feedback': # 意見回饋 單位帳號 / 系統帳號
        # 暫時沒有使用
        if request.GET.get('from') == 'partner':
            for f in Feedback.objects.filter(partner_id=request.user.partner.id).order_by('-id')[offset:offset+10]:
                if f.created:
                    date = f.created + timedelta(hours=8)
                    date = date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date = ''

                if f.is_replied:
                    a = f'是<button class=" feedback_btn w-95p updateFeedback" data-fid="{{ f.id }}">修改為未回覆</button>'
                else:
                    a = f'否<button class=" feedback_btn w-95p updateFeedback" data-fid="{{ f.id }}">修改為已回覆</button>'

                data.append({
                    'id': f"#{f.id}",
                    'created': date,
                    'email': f.email,
                    'type': f.get_type_display(),
                    'content': f.content,
                    'a': a
                })

            total_page = math.ceil(Feedback.objects.filter(partner_id=request.user.partner.id).count() / 10)
        else:
            for f in Feedback.objects.all().order_by('-id')[offset:offset+10]:
                if f.created:
                    date = f.created + timedelta(hours=8)
                    date = date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date = ''

                # if f.partner:
                #     partner_title = f.partner.select_title
                # else:
                #     partner_title = 'TBIA 臺灣生物多樣性資訊聯盟'

                if f.partner:
                    if lang == 'en-us':
                        partner_title = f.partner.select_title_en
                    else:
                        partner_title = f.partner.select_title 
                else:
                    if lang == 'en-us':
                        partner_title = 'Taiwan Biodiversity Information Alliance'
                    else:
                        partner_title = 'TBIA 臺灣生物多樣性資訊聯盟'

                # if f.partner:
                #     if f.is_replied:
                #         a = '是'
                #     else:
                #         a = '否'
                # else:
                if f.is_replied:
                    a = f'是<button class=" feedback_btn w-95p updateFeedback" data-fid="{ f.id }">修改為未回覆</button>'
                else:
                    a = f'否<button class=" feedback_btn w-95p updateFeedback" data-fid="{ f.id }">修改為已回覆</button>'

                data.append({
                    'id': f"#{f.id}",
                    'partner': partner_title,
                    'created': date,
                    'email': f.email,
                    'type': f.get_type_display(),
                    'content': f.content,
                    'a': a
                })

            total_page = math.ceil(Feedback.objects.all().count() / 10)

    elif menu == 'sensitive_track': # 系統帳號 敏感資料申請審核追蹤

        
        for s in SensitiveDataResponse.objects.exclude(is_transferred=True).exclude(partner_id__isnull=True).distinct('query_id').order_by('-query_id')[offset:offset+10]:
        # for s in SensitiveDataResponse.objects.exclude(is_transferred=True).exclude(partner_id__isnull=True).order_by('-id')[offset:offset+10]:
            date = ''
            if s.created:
                date = s.created + timedelta(hours=8)
                due = check_due(date.date(),14) # 已經是轉交單位審核的，期限為14天
                date = date.strftime('%Y-%m-%d %H:%M:%S')
            # else:
            #     date = ''

            # 進階搜尋
            # search_dict = dict(parse.parse_qsl(s.query))
            sq = SearchQuery.objects.get(query_id=s.query_id)
            search_dict = dict(parse.parse_qsl(sq.query))
            query = create_query_display(search_dict)

            if search_dict.get("record_type") == 'col':
                search_prefix = 'collection'
            else:
                search_prefix = 'occurrence'
            tmp_a = create_query_a(search_dict)
            for i in ['locality','datasetName','rightsHolder','total_count']:
                if i in search_dict.keys():
                    search_dict.pop(i)

            query_a = f'/search/{search_prefix}?' + parse.urlencode(search_dict) + tmp_a

            a = f'<a class="pointer showRequest manager_btn" data-query_id="{ s.query_id }" data-query="{ query }" data-sdr_id="">查看</a></td>' 
            query = query_a_href(query,query_a)

            # 審查意見
            comment = []

            for sdr in SensitiveDataResponse.objects.filter(query_id=s.query_id).exclude(is_transferred=True).exclude(partner_id__isnull=True):
                # if sdr.partner:
                #     partner_name = sdr.partner.select_title 
                # else:
                #     partner_name = 'TBIA 臺灣生物多樣性資訊聯盟'

                if sdr.partner:
                    if lang == 'en-us':
                        partner_name = sdr.partner.select_title_en
                    else:
                        partner_name = sdr.partner.select_title 
                else:
                    if lang == 'en-us':
                        partner_name = 'Taiwan Biodiversity Information Alliance'
                    else:
                        partner_name = 'TBIA 臺灣生物多樣性資訊聯盟'
                    
                comment.append(f"<b>審查單位：</b>{partner_name}<br><b>審查者姓名：</b>{sdr.reviewer_name}<br><b>審查意見：</b>{sdr.comment if sdr.comment else ''}<br><b>審查結果：</b>{sdr.get_status_display()}")

            data.append({
                'id': f"#{s.id}",
                'query_id': s.query_id,
                'date':  date + '<br>審核期限：' + due,
                'query':   query,
                'comment': '<hr>'.join(comment) if comment else '',
                'status': sq.get_status_display(),
                'a': a,
            })

        total_page = math.ceil(SearchQuery.objects.filter(type='sensitive',query_id__in=SensitiveDataResponse.objects.exclude(partner_id=None).values_list('query_id',flat=True)).count() / 10)

    elif menu == 'sensitive_apply': # 敏感資料申請 單位後台 / 系統後台
        if request.GET.get('from') == 'partner':
            for sdr in SensitiveDataResponse.objects.filter(partner_id=request.user.partner.id).order_by('-id')[offset:offset+10]:
                created = sdr.created + timedelta(hours=8)
                due = check_due(created.date(), 14)
                created = created.strftime('%Y-%m-%d %H:%M:%S')
                # 整理搜尋條件
                if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
                    r = SearchQuery.objects.get(query_id=sdr.query_id)
                    search_dict = dict(parse.parse_qsl(r.query))
                    query = create_query_display(search_dict)
                    if search_dict.get("record_type") == 'col':
                        search_prefix = 'collection'
                    else:
                        search_prefix = 'occurrence'
                    tmp_a = create_query_a(search_dict)
                    for i in ['locality','datasetName','rightsHolder','total_count']:
                        if i in search_dict.keys():
                            search_dict.pop(i)
                    query_a = f'/search/{search_prefix}?' + parse.urlencode(search_dict) + tmp_a
                    a = f'<a class="pointer showRequest manager_btn" data-query_id="{ sdr.query_id }" data-query="{ query }" data-sdr_id="{ sdr.id }">查看</a></td>'
                    query = query_a_href(query,query_a)
                    data.append({
                        'id': f'#{sdr.id}',
                        #'query_id': r.query_id,
                        'created':  created + '<br>審核期限：'+due,
                        'query':   query,
                        'status': sdr.get_status_display(),
                        'a': a,
                    })

            total_page = math.ceil(SensitiveDataResponse.objects.filter(partner_id=request.user.partner.id).count() / 10)

        else:
            # for sdr in SensitiveDataResponse.objects.filter(partner_id=None).order_by('-id')[offset:offset+10]:
            for sdr in SensitiveDataResponse.objects.filter(partner_id__isnull=True).distinct('query_id').order_by('-query_id')[offset:offset+10]:

                created = sdr.created + timedelta(hours=8)

                # 整理搜尋條件
                if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
                    r = SearchQuery.objects.get(query_id=sdr.query_id)
                    search_dict = dict(parse.parse_qsl(r.query))
                    query = create_query_display(search_dict)
                
                    if search_dict.get("record_type") == 'col':
                        search_prefix = 'collection'
                    else:
                        search_prefix = 'occurrence'
                    tmp_a = create_query_a(search_dict)
                    for i in ['locality','datasetName','rightsHolder','total_count']:
                        if i in search_dict.keys():
                            search_dict.pop(i)

                    query_a = f'/search/{search_prefix}?' + parse.urlencode(search_dict) + tmp_a


                    if sdr.is_transferred:
                        status = '已轉交單位審核'
                        due = check_due(created.date(), 14)
                        created = created.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        status = sdr.get_status_display()
                        due = check_due(created.date(), 7)
                        created = created.strftime('%Y-%m-%d %H:%M:%S')
                    
                    date = created + '<br>審核期限：' + due
                    
                    # function_par = f"'{ sdr.query_id }','{ query }', '{ sdr.id }', '{ sdr.is_transferred }'"

                    a = f'<a class="pointer showRequest manager_btn" data-query_id="{ sdr.query_id }" data-query="{ query }" data-sdr_id="{ sdr.id }" data-is_transferred="{ sdr.is_transferred }">查看</a></td>'

                    query = query_a_href(query,query_a)
                    
                    data.append({
                        'id': f'#{sdr.id}',
                        #'query_id': r.query_id,
                        'created':  date,
                        'query':   query,
                        'status': status,
                        'a': a,
                    })

            total_page = math.ceil(SensitiveDataResponse.objects.filter(partner_id=None).count() / 10)
    elif menu == 'account': # 單位帳號管理 單位後台 / 系統後台
        if request.GET.get('from') == 'partner':
            for a in User.objects.filter(partner_id=request.user.partner.id).order_by('-id').exclude(status='withdraw').exclude(id=request.user.id)[offset:offset+10]:

                if a.is_partner_admin:
                    select = f"""<select name="role" class="w-100p" data-id="{ a.id }"><option value="is_partner_admin" selected>單位管理員</option><option value="is_partner_account">單位帳號</option></select>"""
                else:
                    select = f"""<select name="role" class="w-100p" data-id="{ a.id }"><option value="is_partner_admin">單位管理員</option><option value="is_partner_account" selected>單位帳號</option></select>"""

                status = f'<select name="status" class="w-100p" data-id="{ a.id }">'
                
                for s in User._meta.get_field('status').choices[:-1]:
                    if s[0] == a.status:
                        status += f'<option value="{ s[0] }" selected>{ s[1] }</option>'
                    else:
                        status += f'<option value="{ s[0] }">{ s[1] }</option>'

                status +=  '</select>'
                data.append({
                    'id': f"#{a.id}",
                    'name': f"{a.name} ({a.email})",
                    'select': select,
                    'status': status,
                    'a': f'<button class="manager_btn save_btn" data-id="{ a.id }">儲存</button>'
                })
            total_page = math.ceil(User.objects.filter(partner_id=request.user.partner.id).exclude(status='withdraw').exclude(id=request.user.id).count() / 10)

        else:
            for a in User.objects.filter(partner_id__isnull=False).order_by('-id').exclude(status='withdraw')[offset:offset+10]:
                if a.partner:
                    partner_title = a.partner.select_title 
                else:
                    partner_title = ''

                if a.is_partner_admin:
                    select = f"""<select name="role" class="w-100p" data-id="{ a.id }"><option value="is_partner_admin" selected>單位管理員</option><option value="is_partner_account">單位帳號</option></select>"""
                else:
                    select = f"""<select name="role" class="w-100p" data-id="{ a.id }"><option value="is_partner_admin">單位管理員</option><option value="is_partner_account" selected>單位帳號</option></select>"""

                status = f'<select name="status" class="w-100p" data-id="{ a.id }">'
                
                for s in User._meta.get_field('status').choices[:-1]:
                    if s[0] == a.status:
                        status += f'<option value="{ s[0] }" selected>{ s[1] }</option>'
                    else:
                        status += f'<option value="{ s[0] }">{ s[1] }</option>'

                status +=  '</select>'

                data.append({
                    'id': f"#{a.id}",
                    'name': f"{a.name} ({a.email})",
                    'partner_title': partner_title,
                    'select': select,
                    'status': status,
                    'a': f'<button class="manager_btn save_btn saveStatus" data-pmid="{ a.id }">儲存</button>'
                })

            total_page = math.ceil(User.objects.filter(partner_id__isnull=False).exclude(status='withdraw').count() / 10)
    elif menu == 'news_apply':
                        
        for n in News.objects.all().order_by('-modified')[offset:offset+10]:
            if n.partner:
                partner_title = n.partner.select_title
            else:
                partner_title = ''

            if n.modified:
                modified = n.modified + timedelta(hours=8)
                modified = modified.strftime('%Y-%m-%d %H:%M:%S')
            else:
                modified = ''

            if n.publish_date:
                publish_date = n.publish_date
                publish_date = publish_date.strftime('%Y-%m-%d')
            else:
                publish_date = ''

            data.append({
                'id': f'#{n.id}',
                'a': f'<a class="search-again-a" target="_blank" href="/news/detail/{n.id}">{ n.title }</a>',
                'type': n.get_type_display(),
                'lang': n.get_lang_display(),
                'partner_title': partner_title,
                'user': n.user.name if n.user else '',
                'publish_date': publish_date,
                'modified': modified,
                'status': n.get_status_display(),
                'edit': f'<a class="manager_btn" href="/manager/system/news?menu=edit&news_id={ n.id }">編輯</a>'
            })
        total_page = math.ceil(News.objects.all().count() / 10)
    elif menu == 'news': # 
        if request.user.is_partner_admin:
            # 如果是單位管理者 -> 回傳所有
            news_list = News.objects.filter(partner_id=request.user.partner_id).order_by('-modified')
        else:
            # 如果是單位帳號 -> 只回傳自己申請的
            news_list = News.objects.filter(user_id=request.user).order_by('-modified')
        total_page = math.ceil(news_list.count()/10)

        for n in news_list[offset:offset+10]:
            if n.modified:
                modified = n.modified + timedelta(hours=8)
                modified = modified.strftime('%Y-%m-%d %H:%M:%S')
            else:
                modified = ''

            if n.publish_date:
                publish_date = n.publish_date 
                publish_date = publish_date.strftime('%Y-%m-%d')
            else:
                publish_date = ''
            
            if n.status == 'pending':
                a = f'<a class="manager_btn" href="/withdraw_news?news_id={ n.id }">撤回</a>'
            else:
                a = f'<a class="manager_btn" href="/manager/partner/news?menu=edit&news_id={ n.id }">編輯</a>'

            data.append({
                'id': f"#{n.id}",
                'title': f'<a class="search-again-a" target="_blank" href="/news/detail/{n.id}">{ n.title }</a>',
                'type': n.get_type_display(),
                'lang': n.get_lang_display(),
                'user': n.user.name if n.user else '',
                'publish_date': publish_date,
                'modified': modified,
                'status': n.get_status_display(),
                'a': a
            })
    elif menu == 'resource':
        for r in Resource.objects.all().order_by('-modified')[offset:offset+10]:
            # url = r.url.split('resources/')[1] if 'resources/' in r.url else r.url
            data.append({
                'title': r.title,
                'type': r.get_type_display(),
                'lang': r.get_lang_display(),
                # 'filename': f"<a href='/media/{r.url}' target='_blank'>{url}</a>",
                'publish_date': r.publish_date.strftime('%Y-%m-%d'),
                'modified': r.modified.strftime('%Y-%m-%d %H:%M:%S'),
                'edit': f'<a class="manager_btn" href="/manager/system/resource?menu=edit&resource_id={ r.id }">編輯</a>',
                'delete': f'<a class="delete_resource del_btn" data-resource_id="{ r.id }">刪除</a>'
            })
        total_page = math.ceil(Resource.objects.all().count() / 10)
    elif menu == 'qa':
        for q in Qa.objects.all().order_by('order')[offset:offset+10]:
            data.append({
                'type': q.get_type_display(),
                'order': q.order,
                'question': q.question,
                'edit': f'<a class="manager_btn" href="/manager/system/qa?menu=edit&qa_id={q.id}">編輯</a>',
                'delete': f'<a class="delete_qa del_btn" data-qa_id="{q.id}">刪除</a>', 
            })

        total_page = math.ceil(Qa.objects.all().count() / 10)

    df = pd.DataFrame(data)
    html_table = df.to_html(index=False,escape=False)
    page_list = get_page_list(int(page), total_page)
    response['data'] = html_table.split('<tbody>')[1].split('</tbody>')[0]
    response['page_list'] = page_list
    response['total_page'] = total_page
    response['current_page'] = int(page)

    return HttpResponse(json.dumps(response), content_type='application/json')


def manager(request):
    menu = request.GET.get('menu','info')
    partners = Partner.objects.all().order_by('abbreviation','id')

    from_google = User.objects.filter(id=request.user.id, register_method='google').exists()

    return render(request, 'manager/manager.html', {'partners': partners, 'menu': menu, 'from_google': from_google})


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
    next2 = request.GET.get('next2','/')
    for k in request.GET.keys():
        if k != 'next2':
            for kk in request.GET.getlist(k):
                next2 += f'&{k}={kk}'
    if email := request.user.email:
        if User.objects.filter(email=email).exists():
            u = User.objects.filter(email=email).first()
            if not u.first_login:
                login(request, u, backend='django.contrib.auth.backends.ModelBackend')
                return redirect(next2)
            else:
                if SocialAccount.objects.filter(user=request.user).exists():
                    data = SocialAccount.objects.get(user=request.user).extra_data
                    u.name = data.get('name')
                u.first_login = False
                u.username = email
                # u.name = u.first_name +  ' ' + u.last_name
                u.save()
                login(request, u, backend='django.contrib.auth.backends.ModelBackend')
                return redirect('register_success')
        else:
            data = SocialAccount.objects.get(user=request.user).extra_data
            new_user = User(
                name = data.get('name'),
                email = data.get('email'),
                username = data.get('email'),
                last_name = data.get('family_name'),
                first_name = data.get('given_name'),
                is_email_verified = True,
                is_active = True,
                register_method = 'google',
            )
            new_user.save()
            return redirect('register_success')


def send_verification_email(user, request):
    # current_site = get_current_site(request)  # the domain user is on
    email_subject = '[TBIA 生物多樣性資料庫共通查詢系統] 驗證您的帳號 Verify your account'
    email_body = render_to_string('email/verification.html',{
        'scheme': scheme,
        'user': user,
        'domain': request.get_host(),
        'uid': urlsafe_base64_encode(force_bytes(user.pk)), # encrypt userid for security
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject=email_subject, body=email_body, from_email='TBIA <no-reply@tbiadata.tw>',to=[user.email])

    EmailThread(email).start()



def resend_verification_email(request):
    if request.method == 'POST':
        if User.objects.filter(email=request.POST.get('email','')).exists():
            user = User.objects.get(email=request.POST.get('email',''))
            # current_site = get_current_site(request)  # the domain user is on
            email_subject = '[TBIA 生物多樣性資料庫共通查詢系統] 驗證您的帳號 Verify your account'
            email_body = render_to_string('email/verification.html',{
                'scheme': scheme,
                'user': user,
                'domain': request.get_host(),
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
        uid = force_str(urlsafe_base64_decode(uidb64))
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

    return render(request, 'email/verification-fail.html', {"user": user})



def send_reset_password(request):
    if request.method == 'POST':
        if User.objects.filter(email=request.POST.get('email','')).exists():
            user = User.objects.get(email=request.POST.get('email',''))
            # current_site = get_current_site(request)  # the domain user is on
            email_subject = '[TBIA 生物多樣性資料庫共通查詢系統] 重設您的密碼 Reset your password'
            email_body = render_to_string('email/verification_reset_password.html',{
                'scheme': scheme,
                'user': user,
                'domain': request.get_host(),
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
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        request.session['email'] = user.email
        return redirect(reset_password)

    return render(request, 'email/verification-fail.html', {"user": user})


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
        else:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(email=email, name=name, password=password, is_email_verified=False, is_active=False, register_method='portal')
                user.username = email
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
                response = {'status':'success', 'message': ''}

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
            i['link'] = request.POST.get(f'link_{l}')
            i['description'] = request.POST.get(f'description_{l}')
            i['description_en'] = request.POST.get(f'description_en_{l}')
            new_info.append(i)
            # new_info.append({
            #     'id': i['id'],
            #     'link': request.POST.get(f'link_{l}'),
            #     # 'logo': request.POST.get(f'logo'),
            #     # 'image': i['image'],
            #     # 'subtitle': request.POST.get(f'subtitle_{l}'),
            #     'description': request.POST.get(f'description_{l}'),
            # })
        p = Partner.objects.get(id=partner_id)
        p.info = new_info
        p.save()
        response = {'message': '修改完成'}
        
        return JsonResponse(response, safe=False)

def update_keywords(request):
    if request.method == 'POST':
        for i in range(3):
            order = i+1
            Keyword.objects.filter(order=order,lang='zh-hant').update(keyword=request.POST.get(f"keyword_{order}"))
        for i in range(3):
            order = i+1
            Keyword.objects.filter(order=order,lang='en-us').update(keyword=request.POST.get(f"keyword_en_{order}"))
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
    User.objects.filter(id=user_id).update(status='withdraw',is_partner_account=False,is_partner_admin=False)
    response = {'message': '申請已撤回'}
    return JsonResponse(response, safe=False)


def partner_news(request):
    menu = request.GET.get('menu','news')
    form = NewsForm()
    n = []
    if news_id := request.GET.get('news_id'):
        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            form.fields["content"].initial = n.content

    return render(request, 'manager/partner/news.html', {'form':form, 'menu': menu, 'n': n })


def partner_info(request):
    menu = request.GET.get('menu','info')
    partner_admin = ''
    info = []

    if not request.user.is_anonymous:
        current_user = request.user
        if current_user.partner:
            if User.objects.filter(partner_id=current_user.partner.id, is_partner_admin=True).exists():
                partner_admin = User.objects.filter(partner_id=current_user.partner.id, is_partner_admin=True).values_list('name')
                partner_admin = [p[0] for p in partner_admin]
                partner_admin = ','.join(partner_admin)
            # info
            info = Partner.objects.filter(group=current_user.partner.group).values_list('info')

    return render(request, 'manager/partner/info.html', {'partner_admin': partner_admin, 'info': info, 'menu': menu,})



def download_sensitive_report(request):
    now = timezone.now() + timedelta(hours=8)
    now = now.strftime('%Y-%m-%d')
    df = pd.DataFrame()

    sensitive_response = []
    if not request.user.is_anonymous:
        current_user = request.user
        if request.POST.get('from') == 'partner':
            if current_user.partner:
                if User.objects.filter(id=current_user.id, is_partner_admin=True).exists():
                    sensitive_response = SensitiveDataResponse.objects.filter(partner_id=current_user.partner)
        elif request.POST.get('from') == 'system':
            if User.objects.filter(id=current_user.id, is_system_admin=True).exists():
                sensitive_response = SensitiveDataResponse.objects.filter(partner_id__isnull=True)
        elif request.POST.get('from') == 'track':
            if User.objects.filter(id=current_user.id, is_system_admin=True).exists():
                sensitive_response = SensitiveDataResponse.objects.exclude(is_transferred=True).exclude(partner_id__isnull=True)

    if len(sensitive_response):
        # 申請請求
        sensitive_query = SearchQuery.objects.filter(query_id__in=sensitive_response.values_list('query_id',flat=True))
        for s in sensitive_query:
            # 進階搜尋
            # search_dict = dict(parse.parse_qsl(s.query))
            search_dict = dict(parse.parse_qsl(s.query))
            query = create_query_display(search_dict)
            query = query.replace('<b>','').replace('</b>','')
            query = query.replace('<br>','\n')

            date = s.created + timedelta(hours=8)
            date = date.strftime('%Y-%m-%d %H:%M:%S')

            # request
            detail =  SensitiveDataRequest.objects.get(query_id=s.query_id)

            users = []
            for u in detail.users:
                users.append(f"姓名：{u.get('user_name')}\n單位：{u.get('user_affiliation')}\n職稱：{u.get('user_job_title')}")

            # response
            comment = []
            for sdr in sensitive_response.filter(query_id=s.query_id):
                if sdr.is_transferred:
                    comment.append('已轉交單位審核')
                else:
                    if sdr.partner:
                        partner_name = sdr.partner.select_title 
                    else:
                        partner_name = 'TBIA 臺灣生物多樣性資訊聯盟'
                    comment.append(f"審查單位：{partner_name}\n審查者姓名：{sdr.reviewer_name}\n審查意見：{sdr.comment if sdr.comment else ''}\n審查結果：{sdr.get_status_display()}")

            comment_str = '\n---\n'.join(comment)

            df = pd.concat([df, pd.DataFrame([{'申請時間': date,
                                                '搜尋條件': query,
                                                '申請人姓名': detail.applicant,
                                                '聯絡電話': detail.phone,
                                                '聯絡地址': detail.address,
                                                '申請人所屬單位': detail.affiliation,
                                                '計畫類型': detail.get_type_display(),
                                                '計畫名稱': detail.project_name,
                                                '委託計畫單位': detail.project_affiliation,
                                                '計畫摘要': detail.abstract,
                                                '此批申請資料其他使用者': '\n---\n'.join(users),
                                                '審查意見': comment_str,
                                                # '通過與否': ,
                                                '檔案狀態': s.get_status_display(),
                                                }])],ignore_index=True)


    response = HttpResponse(content_type='application/xlsx')
    response['Content-Disposition'] = f'attachment; filename="tbia_sensitive_report_{now}.xlsx"'
    with pd.ExcelWriter(response) as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=None)

    return response

def get_request_detail(request):
    detail = {}
    review = {}
    if query_id := request.GET.get('query_id'):
        if SensitiveDataRequest.objects.filter(query_id=query_id).exists():
            detail = SensitiveDataRequest.objects.filter(query_id=query_id).values()[0]
    if sdr_id := request.GET.get('sdr_id'):
        if SensitiveDataResponse.objects.filter(id=sdr_id).exclude(is_transferred=True, partner_id__isnull=True).exists():
            review = SensitiveDataResponse.objects.filter(id=sdr_id).exclude(is_transferred=True, partner_id__isnull=True).values()[0]
    return JsonResponse({'detail': detail, 'review': review}, safe=False)


def manager_partner(request):
    partner_admin = ''
    download_url = []
    info = []
    stat_year = [*range(2023, timezone.now().year+1)]
    stat_month = [*range(1, 13, 1)]

    if not request.user.is_anonymous:
        current_user = request.user
        if current_user.partner:
            # for p in current_user.partner:
            for pp in current_user.partner.info:
                if exists(os.path.join('/tbia-volumes/media/match_log',f'/tbia-volumes/media/match_log/{current_user.partner.group}_{pp["id"]}_match_log.zip')):
                    download_url.append({'url': f'/media/match_log/{current_user.partner.group}_{pp["id"]}_match_log.zip', 'name': pp['subtitle']})
            # download_url = generate_no_taxon_csv(current_user.partner.group,request.scheme,request.META['HTTP_HOST'],False)
            partner_admin = User.objects.filter(partner_id=current_user.partner.id, is_partner_admin=True).values_list('name')
            partner_admin = [p[0] for p in partner_admin]
            partner_admin = ','.join(partner_admin)
            # info
            info = Partner.objects.filter(group=current_user.partner.group).values_list('info')
            data_year = int(DataStat.objects.filter(type='data').aggregate(Max('year_month'))['year_month__max'].split('-')[0])

    return render(request, 'manager/partner/manager.html',{'partner_admin': partner_admin, 'download_url': download_url,
                                                            'info': info, 'data_year': data_year, 'stat_year': stat_year, 'stat_month': stat_month})


def get_partner_stat(request):
    p_count = 0
    total_count = 0
    no_taxon = 0
    has_taxon = 0
    data_total = []
    image_data_total = []
    taxon_group_stat = []

    if partner_id := request.GET.get('partner_id'):

        if Partner.objects.filter(id=partner_id).exists():
            group = Partner.objects.get(id=partner_id).group

            f = ['-taxonID:*',f'group:{group}']
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
            url = f"{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet=true&q.op=OR&q=group%3A{group}&rows=0&start=0"
            data = requests.get(url).json()
            if data['responseHeader']['status'] == 0:
                facets = data['facet_counts']['facet_fields']['rightsHolder']
                for r in range(0,len(facets),2):
                    p_count += facets[r+1]
                    if facets[r+1] > 0 :
                        if Partner.objects.filter(group=group).exists():
                            for pp in Partner.objects.get(group=group).info:
                                if pp['dbname'] == facets[r]:
                                    p_color = pp['color']
                                    break
                            data_total.append({'name': facets[r],'y': facets[r+1], 'color': p_color})
                            
            response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q=*:*&rows=0')
            if response.status_code == 200:
                total_count = response.json()['response']['numFound']
                total_count = total_count - p_count
                data_total += [{'name': '其他單位','y': total_count, 'color': '#ddd'}]
                has_taxon = p_count - no_taxon

            # 影像資料筆數
            url = f"{SOLR_PREFIX}tbia_records/select?facet.pivot=group,rightsHolder&facet=true&q.op=OR&q=associatedMedia:*&rows=0&start=0"
            image_data = requests.get(url).json()
            other_image_count = 0
            if image_data['responseHeader']['status'] == 0:
                facets = image_data['facet_counts']['facet_pivot']['group,rightsHolder']
                for f in facets:
                    p_group = f.get('value')
                    for fp in f.get('pivot'):
                        p_dbname = fp.get('value')
                        p_count = fp.get('count')
                        if p_group == group:
                            if Partner.objects.filter(group=p_group).exists():
                                for pp in Partner.objects.get(group=p_group).info:
                                    if pp['dbname'] == p_dbname:
                                        p_color = pp['color']
                                        break
                                image_data_total.append({'name': p_dbname,'y': p_count, 'color': p_color})
                        else:
                            other_image_count += p_count

            image_data_total.append({'name': '其他單位','y': other_image_count, 'color': '#ddd'})


            # 物種類群資料筆數
            taxon_group_stat = [ {'name': taxon_group_map_c[d['name']], 'y': d['count']} for d in list(TaxonStat.objects.filter(rights_holder='total',type='taxon_group').order_by('-count').values('name','count')) ]


    response = {
        'data_total': data_total,
        'has_taxon': has_taxon,
        'no_taxon': no_taxon,
        'image_data_total': image_data_total,
        'taxon_group_stat': taxon_group_stat
    }
    return JsonResponse(response, safe=False)


def manager_system(request):
    no_taxon = 0
    has_taxon = 0
    partner_admin = ''
    stat_year = [*range(2023, timezone.now().year+1)]
    stat_month = [*range(1, 13, 1)]
    if not request.user.is_anonymous:
        holder_list = ['total', 'GBIF']
        for ii in Partner.objects.all().values_list('info', flat=True):
            holder_list += [iii['dbname'] for iii in ii]
        # TaiCOL對應狀況
        response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q=*:*&rows=0')
        if response.status_code == 200:
            total_count = response.json()['response']['numFound']
        response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q=-taxonID:*&rows=0')
        if response.status_code == 200:
            no_taxon = response.json()['response']['numFound']
        has_taxon = total_count - no_taxon
        match_logs = []
        for p in Partner.objects.all():
            for pp in p.info:
                if os.path.exists(f'/tbia-volumes/media/match_log/{p.group}_{pp["id"]}_match_log.zip'):
                    match_logs.append({'url': f'/media/match_log/{p.group}_{pp["id"]}_match_log.zip','name':f"{p.title} - {pp['subtitle']}"})
        keyword_year = int(KeywordStat.objects.aggregate(Max('year_month'))['year_month__max'].split('-')[0])
        keyword_month = int(KeywordStat.objects.aggregate(Max('year_month'))['year_month__max'].split('-')[1])
        checklist_year = int(ChecklistStat.objects.aggregate(Max('year_month'))['year_month__max'].split('-')[0])
        data_year = int(DataStat.objects.filter(type='data').aggregate(Max('year_month'))['year_month__max'].split('-')[0])
        
    return render(request, 'manager/system/manager.html',{'partner_admin': partner_admin, 'no_taxon': no_taxon, 'has_taxon': has_taxon,
                                                          'match_logs': match_logs, 'stat_year': stat_year, 'stat_month': stat_month,
                                                          'keyword_year': keyword_year, 'keyword_month': keyword_month, 'checklist_year': checklist_year,
                                                          'holder_list': holder_list, 'data_year': data_year})



def get_keyword_stat(request):

    month = int(request.GET.get('month'))
    year = int(request.GET.get('year'))
    year_month = f'{year}-{"{:02d}".format(month)}'
    keyword_list = list(KeywordStat.objects.filter(year_month=year_month).order_by('-count')[:10].values('keyword','count'))

    return HttpResponse(json.dumps(keyword_list), content_type='application/json')


def get_checklist_stat(request):

    year = int(request.GET.get('year'))
    checklist_list = list(ChecklistStat.objects.filter(year_month__contains=f'{year}-').order_by('year_month').values('count','year_month'))
    month_list = [*range(1,13)]

    df = pd.DataFrame(checklist_list, columns=['count','year_month'])


    for mm in month_list:
        now_year_month = f'{year}-{"{:02d}".format(mm)}'
        if not len(df[df.year_month==now_year_month]):
            df = pd.concat([df, pd.DataFrame([{'count': 0, 'year_month': now_year_month}])])
    df = df.reset_index(drop=True)


    resp = {}
    resp['data'] = df.sort_values('year_month')['count'].to_list()
    resp['categories'] = list(df.sort_values('year_month').year_month.unique())

    return HttpResponse(json.dumps(resp), content_type='application/json')


def get_data_stat(request):

    year = int(request.GET.get('year'))
    rights_holder = request.GET.get('rights_holder')
    type = request.GET.get('type')

    if rights_holder := request.GET.get('rights_holder'):
        data_list = list(DataStat.objects.filter(year_month__contains=f'{year}-', rights_holder=rights_holder, type=type).order_by('year_month').values('count','year_month'))
    elif group :=  request.GET.get('group'):
        data_list = list(DataStat.objects.filter(year_month__contains=f'{year}-', group=group, type=type).order_by('year_month').values('count','year_month','rights_holder'))

    # print()
    colors = ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065',
    '#555','#3B86C0','#304237','#C65454','#ccc' ]


    if type == 'data':
        month_list = [1,3,5,7,9,11]
    else:
        month_list = [*range(1,13)]

    resp = {}
    if request.GET.get('group'):
        
        df = pd.DataFrame(data_list, columns=['count','year_month','rights_holder'])
        df['count'] = df['count'].astype('int')
        r_list = df.rights_holder.unique()
        r_list.sort() # 確保同一個來源資料庫是同一個顏色
        new_data_list = []

        c = 0
        for x in r_list:
            for mm in month_list:
                now_year_month = f'{year}-{"{:02d}".format(mm)}'
                if not len(df[(df.rights_holder==x)&(df.year_month==now_year_month)]):
                    df = pd.concat([df, pd.DataFrame([{'rights_holder': x, 'count': 0, 'year_month': now_year_month}])])
            df = df.reset_index(drop=True)
            new_data_list.append({'name': x, 'data': df[df.rights_holder==x].sort_values('year_month')['count'].to_list(), 'color': colors[c] })
            c += 1

        resp['data'] = new_data_list
        resp['categories'] = list(df.sort_values('year_month').year_month.unique())

    else:
        df = pd.DataFrame(data_list, columns=['count','year_month'])

        df['count'] = df['count'].astype('int')

        for mm in month_list:
            now_year_month = f'{year}-{"{:02d}".format(mm)}'
            if not len(df[df.year_month==now_year_month]):
                df = pd.concat([df, pd.DataFrame([{'count': 0, 'year_month': now_year_month}])])
        df = df.reset_index(drop=True)


        resp['data'] = df.sort_values('year_month')['count'].to_list()
        resp['categories'] = list(df.sort_values('year_month').year_month.unique())

    return HttpResponse(json.dumps(resp), content_type='application/json')



def get_taxon_group_list(request):

    name = request.GET.get('name')
    selected_name = [i for i in taxon_group_map_c if taxon_group_map_c[i]==name]
    if selected_name:
        selected_name = selected_name[0]

    total_count = TaxonStat.objects.get(type='taxon_group', name=selected_name, group='total').count
    
    if current_group := request.GET.get('group'):
        taxon_list = list(TaxonStat.objects.filter(type='taxon_group', name=selected_name, group=current_group).order_by('-count').values('rights_holder','count'))
    else:
        taxon_list = list(TaxonStat.objects.filter(type='taxon_group', name=selected_name).exclude(rights_holder='total').order_by('-count').values('rights_holder','count'))

    final_list = [{'rights_holder': t['rights_holder'], 'count': t['count'], 'percent': round((t['count'] / total_count)*100, 2) } for t in taxon_list ]

    return HttpResponse(json.dumps(final_list), content_type='application/json')




def get_system_stat(request):
    no_taxon = 0
    has_taxon = 0
    # partner_admin = ''
    data_total = []
    image_data_total = []
    # 資料筆數 - 
    url = f"{SOLR_PREFIX}tbia_records/select?facet.pivot=group,rightsHolder&facet=true&q.op=OR&q=*%3A*&rows=0&start=0"
    data = requests.get(url).json()
    if data['responseHeader']['status'] == 0:
        facets = data['facet_counts']['facet_pivot']['group,rightsHolder']
        for f in facets:
            p_group = f.get('value')
            for fp in f.get('pivot'):
                p_dbname = fp.get('value')
                p_count = fp.get('count')
                
                if Partner.objects.filter(group=p_group).exists():
                    for pp in Partner.objects.get(group=p_group).info:
                        if pp['dbname'] == p_dbname:
                            p_color = pp['color']
                            break
                    data_total.append({'name': p_dbname,'y': p_count, 'color': p_color})
                elif p_group == 'gbif':
                    data_total.append({'name': 'GBIF','y': p_count, 'color': "#ccc"})
    # 影像資料筆數
    url = f"{SOLR_PREFIX}tbia_records/select?facet.pivot=group,rightsHolder&facet=true&q.op=OR&q=associatedMedia:*&rows=0&start=0"
    image_data = requests.get(url).json()
    if image_data['responseHeader']['status'] == 0:
        facets = image_data['facet_counts']['facet_pivot']['group,rightsHolder']
        for f in facets:
            p_group = f.get('value')
            for fp in f.get('pivot'):
                p_dbname = fp.get('value')
                p_count = fp.get('count')
                if Partner.objects.filter(group=p_group).exists():
                    for pp in Partner.objects.get(group=p_group).info:
                        if pp['dbname'] == p_dbname:
                            p_color = pp['color']
                            break
                    image_data_total.append({'name': p_dbname,'y': p_count, 'color': p_color})
                elif p_group == 'gbif':
                    image_data_total.append({'name': 'GBIF','y': p_count, 'color': "#ccc"})


    # TaiCOL對應狀況

    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q=*:*&rows=0')
    if response.status_code == 200:
        total_count = response.json()['response']['numFound']
    response = requests.get(f'{SOLR_PREFIX}tbia_records/select?q=-taxonID:*&rows=0')
    if response.status_code == 200:
        no_taxon = response.json()['response']['numFound']

    # 物種類群資料筆數
    taxon_group_stat = [ {'name': taxon_group_map_c[d['name']], 'y': d['count']} for d in list(TaxonStat.objects.filter(rights_holder='total',type='taxon_group').order_by('-count').values('name','count')) ]

    # 各單位前三類群
    top3_taxon_list = []
    top3_taxon_group = pd.DataFrame(TaxonStat.objects.filter(type='taxon_group').exclude(rights_holder='total').values('rights_holder','name','count'))
    for h in top3_taxon_group.rights_holder.unique():
        data = []
        for tt in top3_taxon_group[top3_taxon_group.rights_holder==h].sort_values('count',ascending=False)[['name','count']].values[:3]:
            # data.append({'name': taxon_group_map_c[tt[0]], 'count': tt[1]})
            data.append(f'{taxon_group_map_c[tt[0]]} ({tt[1]})')
        top3_taxon_list.append({'rights_holder': h, 'data': ('、').join(data)})

    top5_family_list = []
    top5_family = pd.DataFrame(TaxonStat.objects.filter(type='family').exclude(rights_holder='total').values('rights_holder','name','count'))
    for h in top5_family.rights_holder.unique():
        data = []
        for tt in top5_family[top5_family.rights_holder==h].sort_values('count',ascending=False)[['name','count']].values[:5]:
            # data.append({'name': taxon_group_map_c[tt[0]], 'count': tt[1]})
            data.append(f'{tt[0]} ({tt[1]})')
        top5_family_list.append({'rights_holder': h, 'data': ('、').join(data)})

    has_taxon = total_count - no_taxon
    response = {
        'data_total': data_total,
        'has_taxon': has_taxon,
        'no_taxon': no_taxon,
        'image_data_total': image_data_total,
        'taxon_group_stat': taxon_group_stat,
        'top3_taxon_list': top3_taxon_list,
        'top5_family_list': top5_family_list
    }
    return JsonResponse(response, safe=False)


def update_tbia_about(request):
    if request.method == 'POST':
        content = request.POST.get('about_content')
        content_en = request.POST.get('about_content_en')
        a = About.objects.all().first()
        a.content = content
        a.content_en = content_en
        a.save()
        return JsonResponse({"status": 'success'}, safe=False)


def system_news(request):
    menu = request.GET.get('menu','news_apply')

    status_list = News.status.field.choices
    n = []
    form = NewsForm()
    if news_id := request.GET.get('news_id'):
        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            form.fields["content"].initial = n.content

    return render(request, 'manager/system/news.html', {'form':form, 'menu': menu, 'status_list': status_list, 'n': n })


def system_info(request):
    system_admin = ''
    system_admin = User.objects.filter(is_system_admin=True).values_list('name')
    system_admin = [s[0] for s in system_admin]
    system_admin = ','.join(system_admin)

    content = About.objects.all().first().content
    content_en = About.objects.all().first().content_en
    menu = request.GET.get('menu','info')

    return render(request, 'manager/system/info.html', {'menu': menu, 'content': content, 'content_en': content_en, 'system_admin': system_admin })


def system_resource(request):
    menu = request.GET.get('menu','resource')

    type_choice = Resource._meta.get_field('type').choices

    current_r = []
    if request.GET.get('resource_id'):
        if Resource.objects.filter(id=request.GET.get('resource_id')).exists():
            current_r = Resource.objects.get(id=request.GET.get('resource_id'))
            if 'resources/' in current_r.url:
                current_r.filename =  current_r.url.split('resources/')[1]
            else:
                current_r.filename =  current_r.url

    return render(request, 'manager/system/resource.html', {'menu': menu, 'type_choice': type_choice, 'current_r': current_r })


def system_keyword(request):
    keywords = Keyword.objects.filter(lang='zh-hant').order_by('order').values_list('keyword', flat=True)
    keywords_en = Keyword.objects.filter(lang='en-us').order_by('order').values_list('keyword', flat=True)
    return render(request, 'manager/system/keyword.html', {'keywords':keywords,'keywords_en': keywords_en})


def submit_news(request):
    if request.method == 'POST':
        current_user = request.user
        title = request.POST.get('title')
        type = request.POST.get('type')
        news_id = request.POST.get('news_id') if request.POST.get('news_id') else 0
        status = request.POST.get('status','pending')
        content = request.POST.get('content')
        publish_date = request.POST.get('publish_date')
        lang = request.POST.get('news_lang')

        # author_use_tbia = None
        author_use_tbia = request.POST.get('author_use_tbia')

        # tmp = {"delta":'{"ops":[]}',"html":""}
        # tmp['html'] = content
        # html = '<ul><li>GBIF</li><li>TaiBIF</li><li>TBN</li></ul><p><img src=\\"/media/news/ntm_logo_j9SJDgw.png\\"></p>"'   
        # #  = Quill('{"delta":"{\\"ops\\":"","html":"' + content + '"}')
        # tmp = {"delta":'{"ops":[]}',"html":html}
        # content = Quill(tmp)

        if request.POST.get('from_system'):
            # status = 'pass'
            partner_id = None
        else:
            # status = 'pending'
            partner_id = current_user.partner

        # form = NewsForm(request.POST)
        # if form.is_valid():
        #     content = form.cleaned_data['content']

        image_name = None
        if image := request.FILES.get('image'):
            fs = FileSystemStorage()
            image_name = fs.save(f'news/' + image.name, image)

        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            ori_status = n.status
            
            if request.POST.get('from_system'):
                if author_use_tbia == 'on':
                    n.author_use_tbia = True
                else:
                    n.author_use_tbia = False

            # if status == 'pass' and ori_status != 'pass':
            #     publish_date = timezone.now() + timedelta(hours=8)
            # elif status == 'pass' and ori_status == 'pass':
            #     publish_date = n.publish_date
            # else:
            #     publish_date = None
            if n.image and not image_name: # 原本就有的
                image_name = n.image
            elif image_name:
                image_name = image.name
            
            if image_name:
                # n.type = type
                # n.title = title
                # n.content = content
                n.image = image_name
                # n.status = status
                # n.modified = timezone.now()
                # n.publish_date = publish_date
                # n.save()
            else:
                n.image = None
            n.type = type
            n.title = title
            n.content = content
            n.status = status
            n.publish_date = publish_date
            n.modified = timezone.now()
            n.lang = lang
            n.save()
        else:
            ori_status = 'pending'
            # if status == 'pass':
            #     publish_date = timezone.now() + timedelta(hours=8)
            # else:
            #     publish_date = None


            if image_name:
                n = News.objects.create(
                    type = type,
                    user = current_user,
                    partner = partner_id,
                    title = title,
                    content = content,
                    image = image.name,
                    status = status,
                    publish_date = publish_date,
                    lang=lang
                )
            else:
                n = News.objects.create(
                    type = type,
                    user = current_user,
                    partner = partner_id,
                    title = title,
                    content = content,
                    status = status,
                    publish_date = publish_date,
                    lang=lang
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
                    content = content.replace("請至後台查看", f"查看發布內容：{scheme}://{request.get_host()}/news/detail/{n.id}")
                    send_notification([u.id],content,'消息發布申請結果通知')
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
                    content = content.replace("請至後台查看", f"查看發布內容：{scheme}://{request.get_host()}/news/detail/{n.id}")
                    send_notification([u.id],content,'消息發布申請結果通知')

            return redirect('partner_news')


def withdraw_news(request):
    if news_id := request.GET.get('news_id'):
        # user_id = request.user.id
        if user_id := request.user.id:
            # 確認撤回的人是不是申請的人 或者單位管理者
            if News.objects.filter(id=news_id).exists():
                n = News.objects.get(id=news_id)
                partner_id = n.partner_id
                if n.user_id == user_id or User.objects.filter(is_partner_account=True,id=user_id,partner_id=partner_id).exists():
                    n.status = 'withdraw'
                    n.save()
            return redirect('partner_news')
        else:
            return JsonResponse({'message': '權限不足'}, safe=False)


def send_msg(msg):
    msg.send()


@csrf_exempt
def send_notification(user_list, content, title, content_en=None):
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

        if content_en:
            html_content += "<br><br>Hello,<br><br>"
            html_content += content_en
            html_content += "<br>"

        signature = """
                    <br>
                    臺灣生物多樣性資訊聯盟
                    <br>
                    Taiwan Biodiversity Information Alliance
                    """

        html_content += signature

        subject = '[TBIA 生物多樣性資料庫共通查詢系統] ' + title

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
        exceed_ten = False
        if User.objects.filter(id=request.POST.get('user_id')).exists():
            u = User.objects.get(id=request.POST.get('user_id'))
            partner_id = u.partner_id
            
            # 要確認是不是單位帳號是不是超過十個人 而且現在是要修改成pass (原本不是pass)
            if u.status != 'pass' and status == 'pass' and User.objects.filter(partner_id=partner_id,status='pass').count() >= 10:
                # status 改為pending
                status = 'pending'
                exceed_ten = True
            
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

            u.status = status
            u.save()

            if status != 'pending':
                nn = Notification.objects.create(
                    type = 6,
                    content = u.get_status_display(),
                    user = u
                )
                content = nn.get_type_display().replace('0000', str(nn.content))
                send_notification([u.id],content,'單位帳號申請結果通知')

        return JsonResponse({"status": 'success',"exceed_ten": exceed_ten}, safe=False)


def save_resource_file(request):
    response = {'file': None}
    if file := request.FILES.get('file'):
        fs = FileSystemStorage()
        file_name = fs.save(f'resources/' + file.name, file)
        response['url'] = file_name
        response['filename'] = file.name

    return JsonResponse(response, safe=False)


def submit_resource(request):
    if request.method == 'POST':
        now = timezone.now() + timedelta(hours=8)
        url = request.POST.get('url')
        # url = 'resources/' + filename
        if request.POST.get('file_type') == 'link':
            extension = 'link'
        else:
            extension = url.split('.')[-1]
        if request.POST.get('resource_id'):
            resource_id = int(request.POST.get('resource_id'))
        else:
            resource_id = 0

        if Resource.objects.filter(id=resource_id).exists():
            Resource.objects.filter(id=resource_id).update(
                type = request.POST.get('type'),
                title = request.POST.get('title'),
                lang = request.POST.get('lang'),
                publish_date = request.POST.get('publish_date'),
                url = url,
                doc_url = request.POST.get('doc_url'),
                extension = extension,
                modified = now
            )
        else: 
            Resource.objects.create(
                type = request.POST.get('type'),
                title = request.POST.get('title'),
                lang = request.POST.get('lang'),
                publish_date = request.POST.get('publish_date'),
                url = url,
                doc_url = request.POST.get('doc_url'),
                extension = extension,
                created = now,
                modified = now
            )
        return redirect('system_resource')


def delete_resource(request):
    if request.method == 'POST':
        if resource_id := request.POST.get('resource_id'):
            if Resource.objects.filter(id=resource_id).exists():
                r = Resource.objects.get(id=resource_id)
                my_file = Path(os.path.join('/tbia-volumes/media',r.url))
                my_file.unlink(missing_ok=True)
                r.delete()
                return JsonResponse({}, safe=False)


def edit_link(request):
    if request.method == 'POST':
        # content = ''
        content = request.POST.get('content')
        # form = LinkForm(request.POST)
        # if form.is_valid():
        #     content = form.cleaned_data['content']      

        if Link.objects.exists():
            n = Link.objects.all().first()
            n.modified = timezone.now()
            n.content = content
            n.save()
        else:
            Link.objects.create(
                content = content
            )
        return redirect('resources_link')


def get_news_content(request):
    response = {}
    response['content'] = ''
    news_id = request.GET.get('news_id')
    if News.objects.filter(id=news_id).exists():
        n = News.objects.get(id=news_id)
        response['content'] = n.content
    return JsonResponse(response, safe=False)


def save_news_image(request):
    # print(request.POST, request.FILES)
    image_name = ''
    if image := request.FILES.get('image'):
        fs = FileSystemStorage()
        image_name = fs.save(f'news/' + image.name, image)
    return JsonResponse({'data':{'url': image_name}}, safe=False)


def get_link_content(request):
    response = {}
    response['content'] = ''
    # news_id = request.GET.get('news_id')
    if l := Link.objects.all().first():
        # l = News.objects.get(id=news_id)
        response['content'] = l.content
    return JsonResponse(response, safe=False)


def system_qa(request):
    menu = request.GET.get('menu', 'qa')
    # qa_list = Qa.objects.all().order_by('order')[:10]
    # q_total_page = math.ceil(Qa.objects.all().count()/10)
    # q_page_list = get_page_list(1, q_total_page)
    type_choice = Qa._meta.get_field('type').choices
    current_q = []
    if request.GET.get('qa_id'):
        if Qa.objects.filter(id=request.GET.get('qa_id')).exists():
            current_q = Qa.objects.get(id=request.GET.get('qa_id'))

    return render(request, 'manager/system/qa.html', {'menu': menu, 'type_choice': type_choice, 'current_q': current_q})
    # 'q_total_page': q_total_page, 'q_page_list': q_page_list, 'qa_list': qa_list, })


def submit_qa(request):
    if request.method == 'POST':
        if request.POST.get('qa_id'):
            qa_id = int(request.POST.get('qa_id'))
        else:
            qa_id = 0

        if request.POST.get('order'):
            order = int(request.POST.get('order'))
        else:
            if not len(Qa.objects.all()):
                order = 0
            else:
                order = Qa.objects.latest('order').order + 1

        if Qa.objects.filter(id=qa_id).exists():
            old_order = Qa.objects.get(id=qa_id).order
            if old_order != order:
                # 如果修改後排序前進
                if old_order > order:
                    # 原本在此order之前的要加1
                    for q in Qa.objects.filter(order__lte=old_order,order__gte=order).exclude(id=qa_id):
                        q.order += 1
                        q.save()
                # 如果修改後排序後退
                else:
                    for q in Qa.objects.filter(order__lte=order,order__gte=old_order).exclude(id=qa_id):
                        q.order -= 1
                        q.save()
            Qa.objects.filter(id=qa_id).update(
                type = request.POST.get('type'),
                question = request.POST.get('question'),
                question_en = request.POST.get('question_en'),
                answer = request.POST.get('answer'),
                answer_en = request.POST.get('answer_en'),
                order = order
            )

        else: 
            # 在新增的問答 order之後的要加+1
            for q in Qa.objects.filter(order__gte=order):
                q.order += 1
                q.save()
            Qa.objects.create(
                id = Qa.objects.all().aggregate(Max('id'))['id__max']+1,
                type = request.POST.get('type'),
                question = request.POST.get('question'),
                question_en = request.POST.get('question_en'),
                answer = request.POST.get('answer'),
                answer_en = request.POST.get('answer_en'),
                order = order
            )
        return redirect('system_qa')


def delete_qa(request):
    if request.method == 'POST':
        if qa_id := request.POST.get('qa_id'):
            if Qa.objects.filter(id=qa_id).exists():
                q = Qa.objects.get(id=qa_id)
                q.delete()
                return JsonResponse({}, safe=False)