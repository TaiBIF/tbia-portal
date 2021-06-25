from django.http import request
from django.shortcuts import render

# Create your views here.

def home(request):
    return render(request,'pages/home.html')

#https://www.youtube.com/watch?v=FFLp_FmbKj0&list=PLx-q4INfd95ESFMQ1Je3Z0gFdQLhrEuY7&index=22
# https://www.youtube.com/watch?v=Rbkc-0rqSw8
def register(request):
    return render(request,'pages/register.html')