from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('qa', views.qa, name='qa'),
    path('about', views.about, name='about'),
    path('resources', views.resources, name='resources'),
    path('news/detail/<news_id>', views.news_detail, name='news_detail'),
    path('news', views.news, name='news'),
    path('get_news_list', views.get_news_list, name='get_news_list'),
    path('get_resources', views.get_resources, name='get_resources'),
    path('partner/<abbr>', views.partner, name='partner'),
    path('agreement', views.agreement, name='agreement'),
    path('application', views.application, name='application'),
]
