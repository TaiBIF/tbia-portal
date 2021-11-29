from django.http import request
from django.shortcuts import render, redirect
from conf.settings import STATIC_ROOT

def index(request):
    return render(request,'pages/index.html')

