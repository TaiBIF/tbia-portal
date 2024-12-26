from django.urls import path

from . import views

urlpatterns = [
    # 頁面
    path('', views.index, name='index'),
    path('qa', views.qa, name='qa'),
    path('about', views.about, name='about'),
    path('resources', views.resources, name='resources'),
    path('resources/link', views.resources_link, name='resources_link'),
    path('news/detail/<news_id>', views.news_detail, name='news_detail'),
    path('news', views.news, name='news'),
    path('datagap', views.datagap, name='datagap'),
    path('partner/<abbr>', views.partner, name='partner'),
    path('collaboration/<abbr>', views.partner, name='collaboration'),
    path('agreement', views.agreement, name='agreement'),
    path('application', views.application, name='application'),
    path('terms', views.terms, name='terms'),
    path('policy', views.policy, name='policy'),
    path('ark/ids', views.ark_ids, name='ark_ids'),
    # 取得頁面資料
    path('get_qa_list', views.get_qa_list, name='get_qa_list'),
    path('get_news_list', views.get_news_list, name='get_news_list'),
    path('get_resource_list', views.get_resource_list, name='get_resource_list'),
    path('get_ark_list', views.get_ark_list, name='get_ark_list'),
    path('get_current_notif', views.get_current_notif, name='get_current_notif'),
    # 取得異體字
    path('get_variants', views.get_variants, name='get_variants'),
    # 通知管理
    path('update_is_read', views.update_is_read, name='update_is_read'),
    path('update_this_read', views.update_this_read, name='update_this_read'),
    # 不再顯示首頁教學
    path('update_not_show', views.update_not_show, name='update_not_show'),
]
