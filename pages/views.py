from django.http import request
from django.shortcuts import render, redirect
from .models import *


def qa(request):
    # 加上now class 如果有request get指定是哪個問題
    return render(request, 'pages/qa.html')


def index(request):
    # recommended keyword
    keywords = Keyword.objects.filter(displayed=True).values_list('keyword', flat=True)

    # resource
    resource = Resource.objects.order_by('-modified')
    resource_rows = []
    for x in resource[:6]:
        resource_rows.append({
            'title': x.title,
            'extension': x.extension,
            'url': x.url,
            'date': x.modified.strftime("%Y.%m.%d")
        })
    return render(request, 'pages/index.html', {'resource': resource_rows, 'keywords': keywords})