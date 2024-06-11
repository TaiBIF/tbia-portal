from django.urls import path

from . import views

urlpatterns = [
    # 頁面
    path('search/full', views.search_full, name='search_full'),
    path('search/collection', views.search_collection, name='search_collection'),
    path('search/occurrence', views.search_occurrence, name='search_occurrence'),
    path('collection/<str:id>/', views.collection_detail, name='collection_detail'),
    path('occurrence/<str:id>/', views.occurrence_detail, name='occurrence_detail'),
    # 全站搜尋
    path('get_records', views.get_records, name='get_records'),
    path('get_more_docs', views.get_more_docs, name='get_more_docs'),
    path('get_more_cards', views.get_more_cards, name='get_more_cards'),
    path('get_more_cards_taxon', views.get_more_cards_taxon, name='get_more_cards_taxon'),
    path('get_focus_cards', views.get_focus_cards, name='get_focus_cards'),
    path('get_focus_cards_taxon', views.get_focus_cards_taxon, name='get_focus_cards_taxon'),
    path('get_taxon_dist', views.get_taxon_dist, name='get_taxon_dist'),
    path('get_taxon_dist_init', views.get_taxon_dist_init, name='get_taxon_dist_init'),
    # 進階搜尋 取得篩選條件
    path('save_geojson', views.save_geojson, name='save_geojson'),
    path('return_geojson_query', views.return_geojson_query, name='return_geojson_query'),
    path('get_geojson/<str:id>/', views.get_geojson, name='get_geojson'),
    path('change_dataset', views.change_dataset, name='change_dataset'),
    path('get_higher_taxa', views.get_higher_taxa, name='get_higher_taxa'),
    path('get_locality', views.get_locality, name='get_locality'),
    path('get_locality_init', views.get_locality_init, name='get_locality_init'),
    path('get_dataset', views.get_dataset, name='get_dataset'),
    # path('get_dataset_init', views.get_dataset_init, name='get_dataset_init'),
    # 進階搜尋 取得結果
    path('get_conditional_records', views.get_conditional_records, name='get_conditional_records'),
    path('get_map_grid', views.get_map_grid, name='get_map_grid'),
    # 下載 / 敏感資料
    path('send_download_request', views.send_download_request, name='send_download_request'),
    path('send_sensitive_request', views.send_sensitive_request, name='send_sensitive_request'),
    path('submit_sensitive_request', views.submit_sensitive_request, name='submit_sensitive_request'),
    path('sensitive_agreement', views.sensitive_agreement, name='sensitive_agreement'),
    path('submit_sensitive_response', views.submit_sensitive_response, name='submit_sensitive_response'),
    path('transfer_sensitive_response', views.transfer_sensitive_response, name='transfer_sensitive_response'),
    path('partial_transfer_sensitive_response', views.partial_transfer_sensitive_response, name='partial_transfer_sensitive_response'),
]
