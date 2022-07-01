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

class registerBackend(ModelBackend):
    def authenticate(self, username):
        user = User.objects.get(username=username, is_email_verified=True)
        if user:
            return user


class EmailThread(threading.Thread):

    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)

    def run(self):
        self.email.send()


def send_verification_email(user, request):
    current_site = get_current_site(request)  # the domain user is on

    email_subject = '[生物多樣性資料庫共通查詢系統] 驗證您的帳號'
    email_body = render_to_string('account/verification.html',{
        'user': user,
        'domain': current_site,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)), # encrypt userid for security
        'token': generate_token.make_token(user)
    })

    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,
    to=[user.username])

    EmailThread(email).start()


def verify_user(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except Exception as e:
        user = None

    if user and generate_token.check_token(user, token):
        user.is_email_verified = True
        user.is_active = True
        user.save()

        messages.add_message(request, messages.SUCCESS,
                            '驗證成功！請立即設定您的密碼')
        login(request, user, backend='account.views.registerBackend') 
        return redirect(reverse('personal_info'))

    return render(request, 'account/verification-fail.html', {"user": user})



# @auth_user_should_not_access
def register(request):
    print('hi')
    if request.method == 'POST':
        context = {'has_error': False, 'data': request.POST}
        email = request.POST.get('email')
        name = request.POST.get('name')
        password = request.POST.get('password')
        
        # make sure email is unique
        if User.objects.filter(username=email).exists():
            # messages.add_message(request, messages.ERROR, '此信箱已註冊過')
            response = {'status':'fail', 'message': '此信箱已註冊過'}
            # return render(request,'account/register.html', context, status=409) # conflict
        else:
            user=User.objects.create_user(username=email, name=name)
            user.save()
            send_verification_email(user, request)
            # messages.add_message(request, messages.SUCCESS,
            # '註冊成功，請至註冊信箱收信進行驗證')
            response = {'status':'success', 'message': '註冊成功，請至註冊信箱收信進行驗證'}
            # return redirect(reverse('login'))

    return HttpResponse(json.dumps(response), content_type='application/json')


# @auth_user_should_not_access
def login_user(request):
    if request.method == 'POST':
        # context = {'data': request.POST}
        email = request.POST.get('email')
        password = request.POST.get('password')
        rememberme = request.POST.get('rememberme')
        user = authenticate(request, username=email, password=password)
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
            response = {'status':'fail', 'message': 'Email或密碼錯誤，或此帳號停用'}
            # return render(request, 'account/login.html', context, status=401)
        
        print(response)

    return HttpResponse(json.dumps(response), content_type='application/json')


def logout_user(request):

    logout(request)

    return redirect(request.META.get('HTTP_REFERER')) # return to previous page


@login_required
def personal_info(request):
    return render(request, 'account/personal-info.html')

# ---- system ---- #
@login_required
def system_feedback(request):
    return render(request, 'account/system/feedback.html')


@login_required
def system_index(request):
    return render(request, 'account/system/index.html')


@login_required
def system_resource(request):
    return render(request, 'account/system/resource.html')


@login_required
def system_review(request):
    return render(request, 'account/system/review.html')


@login_required
def system_download(request):
    return render(request, 'account/system/download.html')


# ---- unit ---- #
@login_required
def unit_feedback(request):
    return render(request, 'account/unit/feedback.html')


@login_required
def unit_index(request):
    return render(request, 'account/unit/index.html')


@login_required
def unit_resource(request):
    return render(request, 'account/unit/resource.html')


@login_required
def unit_review(request):
    return render(request, 'account/unit/review.html')


@login_required
def unit_download(request):
    return render(request, 'account/unit/download.html')


@login_required
def unit_event(request):
    return render(request, 'account/unit/event.html')


@login_required
def unit_info(request):
    return render(request, 'account/unit/info.html')


@login_required
def unit_news(request):
    return render(request, 'account/unit/news.html')


@login_required
def unit_project(request):
    return render(request, 'account/unit/project.html')
