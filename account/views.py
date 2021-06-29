from django.http import request
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from conf.decorators import auth_user_should_not_access
from django.contrib.auth import authenticate, login, logout
from .models import User
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages


# https://www.youtube.com/watch?v=FFLp_FmbKj0&list=PLx-q4INfd95ESFMQ1Je3Z0gFdQLhrEuY7&index=22
# https://www.youtube.com/watch?v=Rbkc-0rqSw8
@auth_user_should_not_access
def register(request):
    if request.method == 'POST':
        context = {'has_error': False, 'data': request.POST}
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # make sure email is unique
        if User.objects.filter(username=email).exists():
            print('此帳號已註冊過')
            # return to register page
            #---- return error message ---#
            return render(request,'account/register.html', context, status=409) # conflict
        
        user=User.objects.create_user(username=email, first_name=first_name, last_name=last_name)
        user.save()
        #---- return success message ---#

    return render(request,'account/register.html')


@auth_user_should_not_access
def login_user(request):
    if request.method == 'POST':
        context = {'data': request.POST}
        email = request.POST.get('email')
        password = request.POST.get('password')

        print(email, password)

        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            return redirect('home')


        # if user and not user.is_email_verified:
        #     messages.add_message(request, messages.ERROR,
        #                          'Email is not verified, please check your email inbox')
        #     return render(request, 'authentication/login.html', context, status=401)

        # if not user:
        #     messages.add_message(request, messages.ERROR,
        #                          'Invalid credentials, try again')
        #     return render(request, 'authentication/login.html', context, status=401)

        # login(request, user)

        # messages.add_message(request, messages.SUCCESS,
        #                      f'Welcome {user.username}')

        # return redirect(reverse('home'))

    return render(request, 'account/login.html')


def logout_user(request):

    logout(request)

    return redirect(reverse('login'))


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
