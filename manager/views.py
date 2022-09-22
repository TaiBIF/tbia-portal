from email import message
from django.contrib.auth.backends import ModelBackend
from django.http import request
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from conf.decorators import auth_user_should_not_access
from django.contrib.auth import authenticate, login, logout, tokens
from .models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.core.mail import EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, force_text, DjangoUnicodeDecodeError
from .utils import generate_token
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
    partners = User._meta.get_field('partner').choices
    partners = [i for i in partners if i[0] != 'none']
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

        print(response)

    return HttpResponse(json.dumps(response), content_type='application/json')


def logout_user(request):

    logout(request)

    return redirect(request.META.get('HTTP_REFERER')) # return to previous page



# ---- system ---- #
@login_required
def system_feedback(request):
    return render(request, 'manager/system/feedback.html')


@login_required
def system_index(request):
    return render(request, 'manager/system/index.html')


@login_required
def system_resource(request):
    return render(request, 'manager/system/resource.html')


@login_required
def system_review(request):
    return render(request, 'manager/system/review.html')


@login_required
def system_download(request):
    return render(request, 'manager/system/download.html')


# ---- unit ---- #
@login_required
def unit_feedback(request):
    return render(request, 'manager/unit/feedback.html')


@login_required
def unit_index(request):
    return render(request, 'manager/unit/index.html')


@login_required
def unit_resource(request):
    return render(request, 'manager/unit/resource.html')


@login_required
def unit_review(request):
    return render(request, 'manager/unit/review.html')


@login_required
def unit_download(request):
    return render(request, 'manager/unit/download.html')


@login_required
def unit_event(request):
    return render(request, 'manager/unit/event.html')


@login_required
def unit_info(request):
    return render(request, 'manager/unit/info.html')


@login_required
def unit_news(request):
    return render(request, 'manager/unit/news.html')


@login_required
def unit_project(request):
    return render(request, 'manager/unit/project.html')
