from django.urls import path, re_path

from . import views, v2

urlpatterns = [
    # v2（5.2 起；url name 加 api_v2_ 前綴，避免與其他 app 重名）
    path('api/v2/occurrence', v2.occurrence, name='api_v2_occurrence'),
    path('api/v2/dataset', v2.dataset, name='api_v2_dataset'),
    path('api/v2/map', v2.map, name='api_v2_map'),
    path('api/v2/partner', v2.partner, name='api_v2_partner'),
    re_path(r'^api/v2(/.*)?$', v2.not_found, name='api_v2_not_found'),   # 5.5：其他 /api/v2 網址回 JSON 404，須放在 v2 路由最後
    path('api/doc', views.api_doc, name='api_doc'),
    path('api/doc/v1', views.api_doc_v1, name='api_doc_v1'),  # [V1-API-REMOVE]
    path('api/partner-info', views.partner_info, name='api_partner_info'),  # 名稱不可與 manager 的 partner_info 重複
    # [V1-API-REMOVE] v1 路由
    path('api/v1/occurrence', views.occurrence, name='occurrence'),
    path('api/v1/dataset', views.dataset, name='dataset'),
    path('api/v1/map', views.map, name='map'),
]
