from django.http import request
from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT

def index(request):
    return render(request, 'pages/index.html')

def search_full(request):
    print(request)
    # http://127.0.0.1:8983/solr/tbia_records/select?q=*species*&hl=on&hl.fl=*
    return render(request, 'pages/search_full.html')


def search_full_result(request):
    print(request)
    # http://127.0.0.1:8983/solr/tbia_records/select?q=*species*&hl=on&hl.fl=*
    return render(request, 'pages/search_full_result.html')


def qa(request):
    # 加上now class 如果有request get指定是哪個問題
    return render(request, 'pages/qa.html')


def search_collection(request):
    return render(request, 'pages/search_collection.html')


def search_collection_details(request, tbiauuid):
    return render(request, 'pages/search_collection_details.html')


def search_occurrence(request):
    return render(request, 'pages/search_occurrence.html')


def search_occurrence_details(request, tbiauuid):
    return render(request, 'pages/search_occurrence_details.html')
