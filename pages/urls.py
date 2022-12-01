from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('qa', views.qa, name='qa'),
    path('about', views.about, name='about'),
    path('resources', views.resources, name='resources'),
    path('resources/link', views.resources_link, name='resources_link'),
    path('news/detail/<news_id>', views.news_detail, name='news_detail'),
    path('news', views.news, name='news'),
    path('get_news_list', views.get_news_list, name='get_news_list'),
    path('get_resources', views.get_resources, name='get_resources'),
    path('partner/<abbr>', views.partner, name='partner'),
    path('agreement', views.agreement, name='agreement'),
    path('application', views.application, name='application'),
    path('update_is_read', views.update_is_read, name='update_is_read'),
    path('update_this_read', views.update_this_read, name='update_this_read'),
    path('terms', views.terms, name='terms'),
    path('policy', views.policy, name='policy'),
    path('update_not_show', views.update_not_show, name='update_not_show'),
]
