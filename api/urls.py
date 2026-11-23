from django.urls import path

from . import views, v2

urlpatterns = [
    # v2（5.2 起；url name 加 api_v2_ 前綴，避免與其他 app 重名）
    path('api/v2/occurrence', v2.occurrence, name='api_v2_occurrence'),
    path('api/doc', views.api_doc, name='api_doc'),
    path('api/partner-info', views.partner_info, name='api_partner_info'),  # 名稱不可與 manager 的 partner_info 重複
    # [V1-API-REMOVE] v1 路由
    path('api/v1/occurrence', views.occurrence, name='occurrence'),
    path('api/v1/dataset', views.dataset, name='dataset'),
    path('api/v1/map', views.map, name='map'),
]
