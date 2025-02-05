from django.shortcuts import render
from conf.settings import env


class DatabaseCheckMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if env('MAINTENANCE_MODE') == 'True':
            return render(request, '503.html', status=503)
        return self.get_response(request)
