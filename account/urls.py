from django.urls import path

from . import views

urlpatterns = [
    path('account/personal-info', views.personal_info, name='personal_info'),
]
