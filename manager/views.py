from django.contrib.auth.backends import ModelBackend
from django.db import connection
from django.http import request
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from conf.decorators import auth_user_should_not_access
from django.contrib.auth import authenticate, login, logout, tokens
from manager.models import SearchQuery, SensitiveDataRequest, SensitiveDataResponse, User, Partner, About
from pages.models import Feedback, News, Notification, Resource, Link
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from manager.utils import generate_token, partner_map, check_due
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
from pages.models import Keyword, Qa
from ckeditor.fields import RichTextField
from django import forms
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, F, DateTimeField, ExpressionWrapper
from datetime import datetime, timedelta
from urllib import parse
from data.utils import map_collection, map_occurrence, get_key, create_query_display, get_page_list
from os.path import exists
import math

import pandas as pd
from pathlib import Path

class NewsForm(forms.ModelForm):
    content = RichTextField()
    class Meta:
        model = News
        fields = (
            'content',
        )

# class NewsForm(forms.ModelForm):
#     content = RichTextField()

#     class Meta:
#         model  = News
#         fields = ('content',)


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


def change_manager_page(request):
    page = request.GET.get('page')
    menu = request.GET.get('menu')
    offset = (int(page)-1) * 10
    response = {}
    # print(page)
    data = []
    if menu == 'notification':
        # notis = []
        notifications = Notification.objects.filter(user_id=request.user.id).order_by('-created')[offset:offset+10]
        # results = ""
        for n in notifications:
            created = n.created + timedelta(hours=8)
            content = '<p>' + n.get_type_display().replace('0000', n.content)+ '</p>'
            if not n.is_read:
                content = '<div class="noti-dottt"></div>' + content
            data.append({'created': created.strftime('%Y-%m-%d %H:%M:%S'), 
                        'content': content})
        response['header'] = """
                        <tr>
                    <td>日期</td>
                    <td>內容</td>
                </tr>"""

        total_page = math.ceil(Notification.objects.filter(user_id=request.user.id).count() / 10)

    elif menu == 'download_taxon':
        response['header'] = """
                        <tr>
                            <td class="w-5p">下載編號</td>
                            <td class="w-10p">檔案編號</td>
                            <td class="w-10p">檔案產生日期</td>
                            <td class="w-20p">搜尋條件</td>
                            <td class="w-5p">狀態</td>
                            <td class="w-5p">檔案連結</td>
                        </tr>
                """
        # taxon = []
        for t in SearchQuery.objects.filter(user_id=request.user.id,type='taxon').order_by('-id')[offset:offset+10]:
            if t.modified:
                date = t.modified + timedelta(hours=8)
                date = date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date = ''

            # 進階搜尋
            search_dict = dict(parse.parse_qsl(t.query))
            query = create_query_display(search_dict,t.id)
            link = ''
            if t.status == 'pass':
                link = f'<a class="manager_btn" target="_blank" href="/media/download/taxon/{request.user.id }_{ t.query_id }.zip">下載</a>'

            data.append({
                'id': f"#{t.id}",
                'query_id': t.query_id,
                'date':  date,
                'query':   query,
                'status': t.get_status_display(),
                'link': link
            })

        total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id,type='taxon').count() / 10)
    elif menu == 'sensitive':
        response['header'] = """
                        <tr>
                            <td class="w-5p">下載編號</td>
                            <td class="w-10p">檔案編號</td>
                            <td class="w-10p">檔案產生日期</td>
                            <td class="w-15p">搜尋條件</td>
                            <td class="w-15p">審查意見</td>
                            <td class="w-5p">狀態</td>
                            <td class="w-5p">檔案連結</td>
                        </tr>
        """
        for s in SearchQuery.objects.filter(user_id=request.user.id, type='sensitive').order_by('-id')[offset:offset+10]:
            if s.modified:
                date = s.modified + timedelta(hours=8)
                date = date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date = ''

            # 進階搜尋
            search_dict = dict(parse.parse_qsl(s.query))
            query = create_query_display(search_dict,s.id)

            # 審查意見
            comment = []

            for sdr in SensitiveDataResponse.objects.filter(query_id=s.query_id).exclude(is_transferred=True, partner_id__isnull=True):
                if sdr.partner:
                    partner_name = sdr.partner.select_title 
                else:
                    partner_name = 'TBIA聯盟'
                comment.append(f"""<b>審查單位：</b>{partner_name}<br><b>審查者姓名：</b>{sdr.reviewer_name}<br><b>審查意見：</b>{sdr.comment if sdr.comment else "" }<br><b>審查結果：</b>{sdr.get_status_display()}""")

            link = ''
            if s.status == 'pass':
                link = f'<a class="manager_btn" target="_blank" href="/media/download/sensitive/{ request.user.id }_{ s.query_id }.zip">下載</a>'

            data.append({
                'id': f'#{s.id}',
                'query_id': s.query_id,
                'date':  date,
                'query':   query,
                'comment': '<hr>'.join(comment) if comment else '',
                'status': s.get_status_display(),
                'link': link
            })
        total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id, type='sensitive').count() / 10)
    elif menu == 'download':
        response['header'] = """
                        <tr>
                            <td class="w-5p">下載編號</td>
                            <td class="w-10p">檔案編號</td>
                            <td class="w-10p">檔案產生日期</td>
                            <td class="w-20p">搜尋條件</td>
                            <td class="w-5p">狀態</td>
                            <td class="w-5p">檔案連結</td>
                        </tr>
        """
        for r in SearchQuery.objects.filter(user_id=request.user.id,type='record').order_by('-id')[offset:offset+10]:
            if r.modified:
                date = r.modified + timedelta(hours=8)
                date = date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date = ''

            # 整理搜尋條件
            # 全站搜尋
            query = ''
            if 'from_full=yes' in r.query:
                search_str = dict(parse.parse_qsl(r.query)).get('search_str')
                search_dict = dict(parse.parse_qsl(search_str))
                # print(search_dict)

                query += f"<br><b>關鍵字</b>：{search_dict['keyword']}"
                
                if search_dict.get('record_type') == 'occ':
                    map_dict = map_occurrence
                else:
                    map_dict = map_collection
                key = map_dict.get(search_dict['key'])
                query += f"<br><b>{key}</b>：{search_dict['value']}"
                if search_dict.get('scientificName'):
                    query += f"<br><b>學名</b>：{search_dict['scientificName']}"
            else:
            # 進階搜尋
                search_dict = dict(parse.parse_qsl(r.query))
                query = create_query_display(search_dict,r.id)


            link = ''
            if r.status == 'pass':
                link = f'<a class="manager_btn" target="_blank" href="/media/download/record/{ request.user.id }_{ r.query_id }.zip">下載</a>'

            data.append({
                'id': f'#{r.id}',
                'query_id': r.query_id,
                'date':  date,
                'query':   query,
                'status': r.get_status_display(),
                'link': link
            })

        total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id,type='record').count() / 10)

    elif menu == 'feedback':
        if request.GET.get('from') == 'partner':
            response['header'] = """<tr>
                            <td>編號</td>
                            <td>時間</td>
                            <td>Email</td>
                            <td>類型</td>
                            <td>內容</td>
                            <td class="w-15p">已回覆</td>
                        </tr> 
            """
            for f in Feedback.objects.filter(partner_id=request.user.partner.id).order_by('-id')[offset:offset+10]:
                if f.created:
                    date = f.created + timedelta(hours=8)
                    date = date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date = ''

                if f.is_replied:
                    a = f'是<button class="manager_btn feedback_btn w-95p updateFeedback" data-fid="{{ f.id }}">修改為未回覆</button>'
                else:
                    a = f'否<button class="manager_btn feedback_btn w-95p updateFeedback" data-fid="{{ f.id }}">修改為已回覆</button>'

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
            response['header'] = """
                        <tr>
                            <td>編號</td>
                            <td>單位</td>
                            <td>時間</td>
                            <td>Email</td>
                            <td>類型</td>
                            <td>內容</td>
                            <td>已回覆</td>
                        </tr> 
            """
            for f in Feedback.objects.all().order_by('-id')[offset:offset+10]:
                if f.created:
                    date = f.created + timedelta(hours=8)
                    date = date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    date = ''

                if f.partner:
                    partner_title = f.partner.select_title
                else:
                    partner_title = 'TBIA聯盟'

                if f.partner:
                    if f.is_replied:
                        a = '是'
                    else:
                        a = '否'
                else:
                    if f.is_replied:
                        a = f'是<button class="manager_btn feedback_btn w-95p updateFeedback" data-fid="{{ f.id }}">修改為未回覆</button>'
                    else:
                        a = f'否<button class="manager_btn feedback_btn w-95p updateFeedback" data-fid="{{ f.id }}">修改為已回覆</button>'

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

    elif menu == 'sensitive_track':
        response['header'] = '''
                        <tr>
                            <td class="w-5p">申請編號</td>
                            <td class="w-10p">檔案編號</td>
                            <td class="w-10p">申請時間</td>
                            <td class="w-15p">搜尋條件</td>
                            <td class="w-15p">審查意見</td>
                            <td class="w-5p">狀態</td>
                        </tr>'''

        for s in SensitiveDataResponse.objects.exclude(is_transferred=True, partner_id__isnull=True).order_by('-id')[offset:offset+10]:
        # for s in SearchQuery.objects.filter(type='sensitive',query_id__in=SensitiveDataResponse.objects.exclude(partner_id=None).order_by('-id').values_list('query_id',flat=True))[offset:offset+10]:
            if s.created:
                date = s.created + timedelta(hours=8)
                due = check_due(date.strftime('%Y-%m-%d'),14) # 已經是轉交單位審核的，期限為14天
                date = date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                date = ''

            # 進階搜尋
            # search_dict = dict(parse.parse_qsl(s.query))
            search_dict = dict(parse.parse_qsl(SearchQuery.objects.get(query_id=s.query_id).query))
            query = create_query_display(search_dict,s.id)

            # 審查意見
            comment = []

            for sdr in SensitiveDataResponse.objects.filter(query_id=s.query_id).exclude(is_transferred=True, partner_id__isnull=True):
                if sdr.partner:
                    partner_name = sdr.partner.select_title 
                else:
                    partner_name = 'TBIA聯盟'
                comment.append(f"<b>審查單位：</b>{partner_name}<br><b>審查者姓名：</b>{sdr.reviewer_name}<br><b>審查意見：</b>{sdr.comment if sdr.comment else ''}<br><b>審查結果：</b>{sdr.get_status_display()}")

            data.append({
                'id': f"#{s.id}",
                'query_id': s.query_id,
                'date':  date + '<br>審核期限：' + due,
                'query':   query,
                'comment': '<hr>'.join(comment) if comment else '',
                'status': s.get_status_display(),
            })

        total_page = math.ceil(SearchQuery.objects.filter(type='sensitive',query_id__in=SensitiveDataResponse.objects.exclude(partner_id=None).values_list('query_id',flat=True)).count() / 10)

    elif menu == 'sensitive_apply':
        response['header'] = """<tr>
                            <td class="w-10p">編號</td>
                            <td class="w-30p">申請時間</td>
                            <td class="w-40p">搜尋條件</td>
                            <td class="w-10p">狀態</td>
                            <td class="w-10p"></td>
                        </tr> """
        if request.GET.get('from') == 'partner':
            for sdr in SensitiveDataResponse.objects.filter(partner_id=request.user.partner.id).order_by('-id')[offset:offset+10]:
                created = sdr.created + timedelta(hours=8)
                due = check_due(created.strftime('%Y-%m-%d'), 14)
                created = created.strftime('%Y-%m-%d %H:%M:%S')

                # 整理搜尋條件
                if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
                    r = SearchQuery.objects.get(query_id=sdr.query_id)
                    search_dict = dict(parse.parse_qsl(r.query))
                    query = create_query_display(search_dict,r.id)
                                

                a = f'<a class="pointer showRequest manager_btn" data-query_id="{ sdr.query_id }" data-query="{ query }" data-sdr_id="{ sdr.id }">查看</a></td>'

                data.append({
                    'id': f'#{sdr.id}',
                    #'query_id': r.query_id,
                    'created':  created + '<br>審核期限：'+due,
                    'query':   query,
                    'status': sdr.get_status_display(),
                    'a': a
                })

            total_page = math.ceil(SensitiveDataResponse.objects.filter(partner_id=request.user.partner.id).count() / 10)

        else:
            for sdr in SensitiveDataResponse.objects.filter(partner_id=None).order_by('-id')[offset:offset+10]:
                created = sdr.created + timedelta(hours=8)

                # 整理搜尋條件
                if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
                    r = SearchQuery.objects.get(query_id=sdr.query_id)
                    search_dict = dict(parse.parse_qsl(r.query))
                    query = create_query_display(search_dict,r.id)
                
                if sdr.is_transferred:
                    status = '已轉交單位審核'
                    due = check_due(created.strftime('%Y-%m-%d'), 14)
                    created = created.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    status = sdr.get_status_display()
                    due = check_due(created.strftime('%Y-%m-%d'), 7)
                    created = created.strftime('%Y-%m-%d %H:%M:%S')
                
                date = created + '<br>審核期限：' + due
                
                # function_par = f"'{ sdr.query_id }','{ query }', '{ sdr.id }', '{ sdr.is_transferred }'"

                a = f'<a class="pointer showRequest manager_btn" data-query_id="{ sdr.query_id }" data-query="{ query }" data-sdr_id="{ sdr.id }" data-is_transferred="{ sdr.is_transferred }">查看</a></td>'

                data.append({
                    'id': f'#{sdr.id}',
                    #'query_id': r.query_id,
                    'created':  date,
                    'query':   query,
                    'status': status,
                    'a': a
                })

            total_page = math.ceil(SensitiveDataResponse.objects.filter(partner_id=None).count() / 10)
    elif menu == 'account':
        if request.GET.get('from') == 'partner':
            response['header'] = '''
                        <tr>
                            <td class="w-8p">編號</td>
                            <td class="w-25p">姓名</td>
                            <td class="w-20p">權限</td>
                            <td class="w-15p">狀態</td>
                            <td class="w-15p"></td>
                        </tr> 
            '''
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
                    'a': f'<button class="search_btn save_btn w-100p" data-id="{ a.id }">儲存</button>'
                })
            total_page = math.ceil(User.objects.filter(partner_id=request.user.partner.id).exclude(status='withdraw').exclude(id=request.user.id).count() / 10)

        else:
            response['header'] = '''
                        <tr>
                            <td class="w-8p">編號</td>
                            <td class="w-25p">姓名</td>
                            <td class="w-20p">單位</td>
                            <td class="w-20p">權限</td>
                            <td class="w-15p">狀態</td>
                            <td class="w-15p"></td>
                        </tr> 
            '''
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
                    'a': f'<button class="search_btn save_btn w-100p saveStatus" data-pmid="{ a.id })">儲存</button>'
                })

            total_page = math.ceil(User.objects.filter(partner_id__isnull=False).exclude(status='withdraw').count() / 10)
    elif menu == 'news_apply':
        response['header'] = '''
                        <tr>
                            <td class="w-8p">編號</td>
                            <td class="w-18p">標題</td>
                            <td class="w-8p">類別</td>
                            <td class="w-20p">單位</td>
                            <td class="w-15p">申請者</td>
                            <td class="w-15p">最近修改</td>
                            <td class="w-8p">狀態</td>
                            <td class="w-8p"></td>
                        </tr>'''
                        
        for n in News.objects.all().order_by('-id')[offset:offset+10]:
            if n.partner:
                partner_title = n.partner.select_title
            else:
                partner_title = ''
            if n.modified:
                modified = n.modified + timedelta(hours=8)
                modified = modified.strftime('%Y-%m-%d %H:%M:%S')
            else:
                modified = ''

            data.append({
                'id': f'#{n.id}',
                'a': f'<a target="_blank" href="/news/detail/{n.id}">{ n.title }</a>',
                'type': n.get_type_display(),
                'partner_title': partner_title,
                'user': n.user.name if n.user else '',
                'modified': modified,
                'status': n.get_status_display(),
                'edit': f'<a class="manager_btn" href="/manager/system/news?menu=edit&news_id={ n.id }">編輯</a>'
            })
        total_page = math.ceil(News.objects.all().count() / 10)
    elif menu == 'news':
        response['header'] = '''
                        <tr>
                            <td class="w-5p"></td>
                            <td class="w-20p">標題</td>
                            <td class="w-12p">類別</td>
                            <td class="w-15p">申請者</td>
                            <td class="w-15p">最近修改</td>
                            <td class="w-12p">狀態</td>
                            <td class="w-12p"></td> 
                        </tr>
        ''' 
        if request.user.is_partner_admin:
            # 如果是單位管理者 -> 回傳所有
            news_list = News.objects.filter(partner_id=request.user.partner_id).order_by('-id')
        else:
            # 如果是單位帳號 -> 只回傳自己申請的
            news_list = News.objects.filter(user_id=request.user).order_by('-id')
        total_page = math.ceil(news_list.count()/10)

        for n in news_list[offset:offset+10]:
            if n.modified:
                modified = n.modified + timedelta(hours=8)
                modified = modified.strftime('%Y-%m-%d %H:%M:%S')
            else:
                modified = ''
            
            if n.status == 'pending':
                a = f'<a class="manager_btn" href="/withdraw_news?news_id={ n.id }">撤回申請</a>'
            else:
                a = f'<a class="manager_btn" href="/manager/partner/news?menu=edit&news_id={ n.id }">編輯</a>'

            data.append({
                'id': f"#{n.id}",
                'title': f'<a target="_blank" href="/news/detail/{n.id}">{ n.title }</a>',
                'type': n.get_type_display(),
                'user': n.user.name if n.user else '',
                'modified': modified,
                'status': n.get_status_display(),
                'a': a
            })
    elif menu == 'resource':
        response['header'] = """
                        <tr>
                            <td class="w-18p">標題</td>
                            <td class="w-18p">類型</td>
                            <td class="w-20p">檔名</td>
                            <td class="w-15p">最近修改</td>
                            <td class="w-8p"></td> 
                            <td class="w-8p"></td> 
                        </tr>
        """
        for r in Resource.objects.all().order_by('-id')[offset:offset+10]:
            url = r.url.split('resources/')[1] if 'resources/' in r.url else r.url
            data.append({
                'title': r.title,
                'type': r.get_type_display(),
                'filename': f"<a href='/media/{r.url}' target='_blank'>{url}</a>",
                'modified': r.modified.strftime('%Y-%m-%d %H:%M:%S'),
                'edit': f'<a class="manager_btn" href="/manager/system/resource?menu=edit&resource_id={ r.id }">編輯</a>',
                'delete': f'<a href="javascript:;" class="delete_resource manager_btn" data-resource_id="{ r.id }">刪除</a>'
            })

        total_page = math.ceil(Resource.objects.all().count() / 10)
    elif menu == 'qa':
        response['header'] = """
                        <tr>
                            <td class="w-20p">類別</td>
                            <td class="w-10p">排序</td>
                            <td class="w-50p">問題</td>
                            <td class="w-10p"></td> 
                            <td class="w-10p"></td> 
                        </tr>
        """
        for q in Qa.objects.all().order_by('order')[offset:offset+10]:
            data.append({
                'type': q.get_type_display(),
                'order': q.order,
                'question': q.question,
                'edit': f'<a class="manager_btn" href="/manager/system/qa?menu=edit&qa_id={q.id}">編輯</a>',
                'delete': f'<a href="javascript:;" class="delete_qa manager_btn" data-qa_id="{q.id}">刪除</a>', 
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
    # pr = []
    # if PartnerRequest.objects.filter(user_id=request.user.id,status__in=['pending','pass']).exists():
    #     pr = PartnerRequest.objects.get(user_id=request.user.id)
    # notis = Notification.objects.filter(user_id=request.user.id)

    notis = []
    notifications = Notification.objects.filter(user_id=request.user.id).order_by('-created')[:10]
    # results = ""
    for n in notifications:
        created = n.created + timedelta(hours=8)
        content = n.get_type_display().replace('0000', n.content)
        notis.append({'created': created.strftime('%Y-%m-%d %H:%M:%S'), 'id': n.id,
                    'content': content, 'is_read': n.is_read})

    n_total_page = math.ceil(Notification.objects.filter(user_id=request.user.id).count() / 10)
    n_page_list = get_page_list(1, n_total_page)
    # print(page_list)

    # TODO 未來要考慮檔案是否過期
    record = []
    for r in SearchQuery.objects.filter(user_id=request.user.id,type='record').order_by('-id')[:10]:
        if r.modified:
            date = r.modified + timedelta(hours=8)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = ''
        query = ''
        # 整理搜尋條件
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
            query += f"<br><b>學名</b>：{search_dict.get('scientificName','')}"
        else:
        # 進階搜尋
            search_dict = dict(parse.parse_qsl(r.query))
            query = create_query_display(search_dict,r.id)

        record.append({
            'id': r.id,
            'query_id': r.query_id,
            'date':  date,
            'query':   query,
            'status': r.get_status_display()
        })
    r_total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id,type='record').count() / 10)
    r_page_list = get_page_list(1, r_total_page)

    # print(r_total_page, r_page_list)
    taxon = []
    for t in SearchQuery.objects.filter(user_id=request.user.id,type='taxon').order_by('-id')[:10]:
        query = ''
        if t.modified:
            date = t.modified + timedelta(hours=8)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = ''
        # 進階搜尋
        search_dict = dict(parse.parse_qsl(t.query))
        query = create_query_display(search_dict,t.id)

        taxon.append({
            'id': t.id,
            'query_id': t.query_id,
            'date':  date,
            'query':   query,
            'status': t.get_status_display()
        })

    t_total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id,type='taxon').count()/10)
    t_page_list = get_page_list(1, t_total_page)

    sensitive = []

    for s in SearchQuery.objects.filter(user_id=request.user.id, type='sensitive').order_by('-id')[:10]:
        query = ''

        if s.modified:
            date = s.modified + timedelta(hours=8)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = ''

        # 進階搜尋
        search_dict = dict(parse.parse_qsl(s.query))
        query = create_query_display(search_dict,s.id)

    # for sdr in SensitiveDataResponse.objects.filter(query_id__in=SearchQuery.objects.filter(user_id=request.user.id, type='senstive').values('query_id')):

        # 審查意見
        comment = []

        for sdr in SensitiveDataResponse.objects.filter(query_id=s.query_id).exclude(is_transferred=True, partner_id__isnull=True):
            if sdr.partner:
                partner_name = sdr.partner.select_title 
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

    s_total_page = math.ceil(SearchQuery.objects.filter(user_id=request.user.id, type='sensitive').count()/10)
    s_page_list = get_page_list(1, s_total_page)

    return render(request, 'manager/manager.html', {'partners': partners, 'menu': menu, 'notis': notis,
    'record': record, 'taxon': taxon, 'sensitive': sensitive, 'n_page_list': n_page_list, 'n_total_page': n_total_page,
    't_page_list': t_page_list, 't_total_page': t_total_page, 's_page_list': s_page_list, 's_total_page': s_total_page,
    'r_page_list': r_page_list, 'r_total_page': r_total_page})


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
            )
            new_user.save()
            return redirect('register_success')


def send_verification_email(user, request):
    # current_site = get_current_site(request)  # the domain user is on

    email_subject = '[生物多樣性資料庫共通查詢系統] 驗證您的帳號'
    email_body = render_to_string('manager/verification.html',{
        'scheme': request.scheme,
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

            email_subject = '[生物多樣性資料庫共通查詢系統] 驗證您的帳號'
            email_body = render_to_string('manager/verification.html',{
                'scheme': request.scheme,
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
            # current_site = get_current_site(request)  # the domain user is on

            email_subject = '[生物多樣性資料庫共通查詢系統] 重設您的密碼'
            email_body = render_to_string('manager/verification_reset_password.html',{
                'scheme': request.scheme,
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
        else:
            if not User.objects.filter(email=email).exists():
                user = User.objects.create_user(email=email, name=name, password=password, is_email_verified=False, is_active=False)
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
                # 'logo': request.POST.get(f'logo'),
                'image': i['image'],
                'subtitle': request.POST.get(f'subtitle_{l}'),
                'description': request.POST.get(f'description_{l}'),
            })
        p = Partner.objects.get(id=partner_id)
        p.info = new_info
        p.save()
        response = {'message': '修改完成'}
        
        return JsonResponse(response, safe=False)


# #  這邊改成再比對的時候就先產生好
# def generate_no_taxon_csv(p_name,scheme,host,update):
#     CSV_MEDIA_FOLDER = 'match_log'
#     csv_folder = os.path.join(settings.MEDIA_ROOT, CSV_MEDIA_FOLDER)
#     filename = f'{p_name}_match_log.csv'
#     csv_file_path = os.path.join(csv_folder, filename)
#     # solr_url = f"{SOLR_PREFIX}tbia_records/select?q=-taxonID:*&wt=csv&indent=true&fq=group:{p_name}&start=0&rows=2000000000&fl=occurrenceID,rightsHolder"
#     # occurrenceID	id	sourceScientificName	taxonID	parentTaxonID	taxonRank	scientificName	match_stage	stage_1	stage_2	stage_3	stage_4	stage_5	is_matched
#     downloadURL = scheme+"://"+host+settings.MEDIA_URL+os.path.join(CSV_MEDIA_FOLDER, filename)
#     if update or not os.path.exists(csv_file_path): # 指定要更新或沒有檔案才執行
#         sql = """
#         copy (
#             SELECT mm."tbiaID", mm."occurrenceID", mm."sourceScientificName", mm."taxonID",
#             mm."parentTaxonID", mm.is_matched, dt."scientificName", dt."taxonRank",
#             mm.match_stage, mm.stage_1, mm.stage_2, mm.stage_3, mm.stage_4, mm.stage_5
#             FROM manager_matchlog mm
#             LEFT JOIN data_taxon dt ON mm."taxonID" = dt."taxonID"
#             WHERE mm."group" = '{}'
#         ) to stdout with delimiter ',' csv header;
#         """.format(p_name)
#         with connection.cursor() as cursor:
#             with open(f'/tbia-volumes/media/match_log/{p_name}_match_log.csv', 'w+') as fp:
#                 cursor.copy_expert(sql, fp)
#         # commands = f'curl "{solr_url}"  > {csv_file_path} '
#         # process = subprocess.Popen(commands, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     return downloadURL
#     # curl "http://localhost:8888/solr/collection1/select?q=*%3A*&wt=cvs&indent=true&start=0&rows=2000000000&fl=id,title" > full-output-of-my-solr-index.csv


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
    User.objects.filter(id=user_id).update(status='withdraw',is_partner_account=False,is_partner_admin=False)
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
            news_list = News.objects.filter(partner_id=current_user.partner_id).order_by('-id')
        else:
            # 如果是單位帳號 -> 只回傳自己申請的
            news_list = News.objects.filter(user_id=current_user).order_by('-id')
        n_total_page = math.ceil(news_list.count()/10)
        n_page_list = get_page_list(1, n_total_page)

        news_list = news_list[:10]
        news_list.annotate(
                modified_8=ExpressionWrapper(
                    F('modified') + timedelta(hours=8),
                    output_field=DateTimeField()
                ))


    return render(request, 'manager/partner/news.html', {'form':form, 'menu': menu, 'n': n, 'news_list': news_list,
                'n_total_page': n_total_page, 'n_page_list': n_page_list})


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

            partner_members = User.objects.filter(partner_id=current_user.partner.id).order_by('-id').exclude(status='withdraw').exclude(id=current_user.id)
            
            a_total_page = math.ceil(partner_members.count() / 10)
            a_page_list = get_page_list(1, a_total_page)

            status_choice = User._meta.get_field('status').choices[:-1]
            feedback = Feedback.objects.filter(partner_id=current_user.partner.id).order_by('-id')[:10].annotate(
                created_8=ExpressionWrapper(
                    F('created') + timedelta(hours=8),
                    output_field=DateTimeField()
                ))
            f_total_page = math.ceil(Feedback.objects.filter(partner_id=current_user.partner.id).count() / 10)
            f_page_list = get_page_list(1, f_total_page)

    sensitive = []
    for sdr in SensitiveDataResponse.objects.filter(partner_id=current_user.partner.id).order_by('-id')[:10]:
        created = sdr.created + timedelta(hours=8)
        due = check_due(created.strftime('%Y-%m-%d'),14)
        created = created.strftime('%Y-%m-%d %H:%M:%S')

        # 整理搜尋條件
        if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
            r = SearchQuery.objects.get(query_id=sdr.query_id)
            search_dict = dict(parse.parse_qsl(r.query))
            query = create_query_display(search_dict,r.id)

        sensitive.append({
            'id': sdr.id,
            'query_id': r.query_id,
            'created':  created,
            'query':   query,
            'status': sdr.get_status_display(),
            'due': due
        })
    s_total_page = math.ceil(SensitiveDataResponse.objects.filter(partner_id=current_user.partner.id).count()/10)
    s_page_list = get_page_list(1, s_total_page)

    return render(request, 'manager/partner/info.html', {'partner_admin': partner_admin,  'info': info, 'feedback': feedback,
                                    'menu': menu, 'partner_members': partner_members, 'status_choice': status_choice, 'sensitive': sensitive,
                                    'f_total_page': f_total_page, 'f_page_list': f_page_list, 's_total_page':s_total_page, 's_page_list': s_page_list,
                                    'a_total_page': a_total_page, 'a_page_list': a_page_list})


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
    download_url = ''
    info = []
    if not request.user.is_anonymous:
        current_user = request.user
        if current_user.partner:
            if exists(os.path.join('/tbia-volumes/media/match_log', f'{current_user.partner.group}_match_log.zip')):
                download_url = os.path.join('/media/match_log', f'{current_user.partner.group}_match_log.zip')
            # download_url = generate_no_taxon_csv(current_user.partner.group,request.scheme,request.META['HTTP_HOST'],False)
            partner_admin = User.objects.filter(partner_id=current_user.partner.id, is_partner_admin=True).values_list('name')
            partner_admin = [p[0] for p in partner_admin]
            partner_admin = ','.join(partner_admin)
            # info
            info = Partner.objects.filter(group=current_user.partner.group).values_list('info')
    return render(request, 'manager/partner/manager.html',{'partner_admin': partner_admin, 'download_url': download_url,
                                                            'info': info})


def get_partner_stat(request):
    p_count = 0
    total_count = 0
    no_taxon = 0
    has_taxon = 0
    data_total = []

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
            url = f"{SOLR_PREFIX}tbia_records/select?facet.field=rightsHolder&facet=true&indent=true&q.op=OR&q=group%3A{group}&rows=0&start=0"
            data = requests.get(url).json()
            if data['responseHeader']['status'] == 0:
                facets = data['facet_counts']['facet_fields']['rightsHolder']
                for r in range(0,len(facets),2):
                    p_count += facets[r+1]
                    if facets[r+1] > 0 :
                        for pg in partner_map[group]:
                            if pg['dbname'] == facets[r]:
                                p_color = pg['color']
                                break
                        data_total.append({'name': facets[r],'y': facets[r+1], 'color': p_color})
            solr = SolrQuery('tbia_records')
            query_list = [('q', '*:*'),('rows', 0)]
            req = solr.request(query_list)
            total_count = req['solr_response']['response']['numFound']
            total_count = total_count - p_count
            data_total += [{'name': '其他單位','y': total_count, 'color': '#ddd'}]
            has_taxon = p_count - no_taxon
    response = {
        'data_total': data_total,
        'has_taxon': has_taxon,
        'no_taxon': no_taxon
    }
    return JsonResponse(response, safe=False)


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
        match_logs = []
        for g in Partner.objects.all():
            if os.path.exists(f'/tbia-volumes/media/match_log/{g.group}_match_log.zip'):
                match_logs.append({'url': f'/media/match_log/{g.group}_match_log.zip','name':f"{g.breadtitle} - {g.info[0]['subtitle']}"})
    return render(request, 'manager/system/manager.html',{'partner_admin': partner_admin, 'no_taxon': no_taxon, 'has_taxon': has_taxon,
                                                            'data_total':data_total,'keywords': keywords, 'match_logs': match_logs})


def get_system_stat(request):
    no_taxon = 0
    has_taxon = 0
    # partner_admin = ''
    data_total = []
    # if not request.user.is_anonymous:
        # 資料筆數 - 改成用單位?
    url = f"{SOLR_PREFIX}tbia_records/select?facet.pivot=group,rightsHolder&facet=true&indent=true&q.op=OR&q=*%3A*&rows=0&start=0"
    data = requests.get(url).json()
    if data['responseHeader']['status'] == 0:
        facets = data['facet_counts']['facet_pivot']['group,rightsHolder']
        for f in facets:
            p_group = f.get('value')
            for fp in f.get('pivot'):
                p_dbname = fp.get('value')
                p_count = fp.get('count')
                for pg in partner_map[p_group]:
                    if pg['dbname'] == p_dbname:
                        p_color = pg['color']
                        break
                data_total.append({'name': p_dbname,'y': p_count, 'color': p_color})

            # if data['responseHeader']['status'] == 0:
            #     facets = data['facet_counts']['facet_fields']['rightsHolder']
            #     for r in range(0,len(facets),2):
            #         p_count += facets[r+1]
            #         if facets[r+1] > 0 :
            #             for pg in partner_map[group]:
            #                 if pg['dbname'] == facets[r]:
            #                     p_color = pg['color']
            #                     break
            #             data_total.append({'name': facets[r],'y': facets[r+1], 'color': p_color})


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
    response = {
        'data_total': data_total,
        'has_taxon': has_taxon,
        'no_taxon': no_taxon
    }
    return JsonResponse(response, safe=False)



def update_tbia_about(request):
    if request.method == 'POST':
        content = request.POST.get('about_content')
        a = About.objects.all().first()
        a.content = content
        a.save()
        return JsonResponse({"status": 'success'}, safe=False)


def system_news(request):
    menu = request.GET.get('menu','list')
    form = NewsForm()
    # if current_a:
    #     form.fields["content"].initial = current_a.content
    news_list = News.objects.all().order_by('-id')[:10].annotate(
                modified_8=ExpressionWrapper(
                    F('modified') + timedelta(hours=8),
                    output_field=DateTimeField()
                ))
    n_total_page = math.ceil(News.objects.all().count()/10)
    n_page_list = get_page_list(1, n_total_page)

    status_list = News.status.field.choices
    n = []
    if news_id:= request.GET.get('news_id'):
        if News.objects.filter(id=news_id).exists():
            n = News.objects.get(id=news_id)
            form.fields["content"].initial = n.content
    return render(request, 'manager/system/news.html', {'form':form, 'menu': menu, 'news_list': news_list, 'status_list': status_list, 'n': n,
    'n_total_page': n_total_page, 'n_page_list': n_page_list})


def system_info(request):
    system_admin = ''
    system_admin = User.objects.filter(is_system_admin=True).values_list('name')
    system_admin = [s[0] for s in system_admin]
    system_admin = ','.join(system_admin)

    content = About.objects.all().first().content
    menu = request.GET.get('menu','info')
    partner_members = User.objects.filter(partner_id__isnull=False).order_by('-id').exclude(status='withdraw')[:10]

    a_total_page = math.ceil(User.objects.filter(partner_id__isnull=False).exclude(status='withdraw').count()/10)
    a_page_list = get_page_list(1, a_total_page)


    status_choice = User._meta.get_field('status').choices[:-1]
    feedback = Feedback.objects.all().order_by('-id')[:10].annotate(
        created_8=ExpressionWrapper(
            F('created') + timedelta(hours=8),
            output_field=DateTimeField()
        ))
    f_total_page = math.ceil(Feedback.objects.all().count() / 10)
    f_page_list = get_page_list(1, f_total_page)

    sensitive = []
    for sdr in SensitiveDataResponse.objects.filter(partner_id=None).order_by('-id')[:10]:
        created = sdr.created + timedelta(hours=8)
        if sdr.is_transferred:
            due = check_due(created.strftime('%Y-%m-%d'),14)
        else:
            due = check_due(created.strftime('%Y-%m-%d'),7)
        created = created.strftime('%Y-%m-%d %H:%M:%S')
        # 整理搜尋條件
        if SearchQuery.objects.filter(query_id=sdr.query_id).exists():
            r = SearchQuery.objects.get(query_id=sdr.query_id)
            search_dict = dict(parse.parse_qsl(r.query))
            query = create_query_display(search_dict,r.id)
        sensitive.append({
            'id': sdr.id,
            'query_id': r.query_id,
            'created':  created,
            'query':   query,
            'status': sdr.get_status_display(),
            'is_transferred': sdr.is_transferred,
            'due': due,
        })

    s_total_page = math.ceil(SensitiveDataResponse.objects.filter(partner_id=None).count()/10)
    s_page_list = get_page_list(1, s_total_page)

    # print(len(sensitive),s_total_page,s_page_list)

    sensitive_track = []
    for s in SensitiveDataResponse.objects.filter(partner_id__isnull=False).order_by('-id')[:10]:
    # for s in SearchQuery.objects.filter(type='sensitive',query_id__in=SensitiveDataResponse.objects.exclude(partner_id=None).values_list('query_id',flat=True)).order_by('-id')[:10]:
        if s.created:
            date = s.created + timedelta(hours=8)
            due = check_due(date.strftime('%Y-%m-%d'), 14)
            date = date.strftime('%Y-%m-%d %H:%M:%S')
        else:
            date = ''
            due = ''

        # 進階搜尋
        
        search_dict = dict(parse.parse_qsl(SearchQuery.objects.get(query_id=s.query_id).query))
        query = create_query_display(search_dict,s.id)

        # 審查意見
        comment = []

        for sdr in SensitiveDataResponse.objects.filter(query_id=s.query_id).exclude(is_transferred=True, partner_id__isnull=True):
            if sdr.partner:
                partner_name = sdr.partner.select_title 
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

        sensitive_track.append({
            'id': s.id,
            'query_id': s.query_id,
            'date':  date,
            'query':   query,
            'status': s.get_status_display(),
            'comment': '<hr>'.join(comment) if comment else '',
            'due': due
        })

    sr_total_page = math.ceil(SearchQuery.objects.filter(type='sensitive',query_id__in=SensitiveDataResponse.objects.exclude(partner_id=None).values_list('query_id',flat=True)).count()/10)
    sr_page_list = get_page_list(1, sr_total_page)

    return render(request, 'manager/system/info.html', {'menu': menu, 'content': content, 
                        'system_admin': system_admin, 'partner_members': partner_members,
                        'status_choice': status_choice, 'feedback': feedback, 'sensitive': sensitive, 'sensitive_track': sensitive_track,
                        'f_page_list': f_page_list, 'f_total_page': f_total_page, 'sr_page_list': sr_page_list, 'sr_total_page': sr_total_page,
                        's_page_list': s_page_list, 's_total_page': s_total_page,'a_page_list': a_page_list, 'a_total_page': a_total_page,})


def system_resource(request):
    menu = request.GET.get('menu','list')

    resource_list = []
    for r in Resource.objects.all().order_by('-id')[:10]:
        resource_list.append({'type': r.get_type_display(),'id': r.id, 'modified': r.modified, 'title': r.title, 'filename': r.url.split('resources/')[1] if 'resources/' in r.url else r.url })
    r_total_page = math.ceil(Resource.objects.all().count()/10)
    r_page_list = get_page_list(1, r_total_page)
    type_choice = Resource._meta.get_field('type').choices

    current_r = []
    if request.GET.get('resource_id'):
        if Resource.objects.filter(id=request.GET.get('resource_id')).exists():
            current_r = Resource.objects.get(id=request.GET.get('resource_id'))
            if 'resources/' in current_r.url:
                current_r.filename =  current_r.url.split('resources/')[1]
            else:
                current_r.filename =  current_r.url

    # form = LinkForm()
    # n = []
    # if n := Link.objects.all().first():
    #     form.fields["content"].initial = n.content
    # if Link.objects.all().first():
    #     n = Link.objects.all().first()

    return render(request, 'manager/system/resource.html', {'menu': menu, 'resource_list': resource_list,
    'r_total_page': r_total_page, 'r_page_list': r_page_list, 'type_choice': type_choice, 'current_r': current_r})


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
        content = request.POST.get('content')

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
            if status == 'pass' and ori_status != 'pass':
                publish_date = timezone.now() + timedelta(hours=8)
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
                publish_date = timezone.now() + timedelta(hours=8)
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
                    content = content.replace("請至後台查看", f"查看發布內容：{request.scheme}://{request.get_host()}/news/detail/{n.id}")
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
                    content = content.replace("請至後台查看", f"查看發布內容：{request.scheme}://{request.get_host()}/news/detail/{n.id}")
                    send_notification([u.id],content,'消息發布申請結果')

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
        <br>
        臺灣生物多樣性資訊聯盟
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
        extension = url.split('.')[-1]
        if request.POST.get('resource_id'):
            resource_id = int(request.POST.get('resource_id'))
        else:
            resource_id = 0

        if Resource.objects.filter(id=resource_id).exists():
            Resource.objects.filter(id=resource_id).update(
                type = request.POST.get('type'),
                title = request.POST.get('title'),
                url = url,
                extension = extension,
                modified = now
            )
        else: 
            Resource.objects.create(
                type = request.POST.get('type'),
                title = request.POST.get('title'),
                url = url,
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
    menu = request.GET.get('menu', 'list')
    qa_list = Qa.objects.all().order_by('order')[:10]
    q_total_page = math.ceil(Qa.objects.all().count()/10)
    q_page_list = get_page_list(1, q_total_page)
    type_choice = Qa._meta.get_field('type').choices
    current_q = []
    if request.GET.get('qa_id'):
        if Qa.objects.filter(id=request.GET.get('qa_id')).exists():
            current_q = Qa.objects.get(id=request.GET.get('qa_id'))

    return render(request, 'manager/system/qa.html', {'qa_list': qa_list, 'type_choice': type_choice,
    'q_total_page': q_total_page, 'q_page_list': q_page_list, 'menu': menu, 'current_q': current_q})


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
                answer = request.POST.get('answer'),
                order = order
            )

        else: 
            # 在新增的問答 order之後的要加+1
            for q in Qa.objects.filter(order__gte=order):
                q.order += 1
                q.save()
            Qa.objects.create(
                type = request.POST.get('type'),
                question = request.POST.get('question'),
                answer = request.POST.get('answer'),
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
