from django.urls import path

from . import views

urlpatterns = [
    path('api/doc', views.api_doc, name='api_doc'),
    path('api/partner-info', views.partner_info, name='api_partner_info'),  # 名稱不可與 manager 的 partner_info 重複
    # [V1-API-REMOVE] v1 路由
    path('api/v1/occurrence', views.occurrence, name='occurrence'),
    path('api/v1/dataset', views.dataset, name='dataset'),
    path('api/v1/map', views.map, name='map'),
]
