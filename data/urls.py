from django.urls import path

from . import views

urlpatterns = [
    path('search/full', views.search_full, name='search_full'),
    # path('search/full/result', views.search_full_result, name='search_full_result'),
    # path('search/full/more_results', views.get_more_results, name='get_more_results'),
    path('search/full/get_records', views.get_records, name='get_records'),
    path('search/full/get_more_docs', views.get_more_docs, name='get_more_docs'),
    path('search/full/get_more_cards', views.get_more_cards, name='get_more_cards'),
    path('search/full/get_focus_cards', views.get_focus_cards, name='get_focus_cards'),
    # path('search/full/doc/<result_type>/<keyword>', views.search_full_doc, name='search_full_doc'),
    # path('search/full/record/<record_type>/<keyword>', views.search_full_record, name='search_full_record'),
    path('search/collection', views.search_collection, name='search_collection'),
    path('search/occurrence', views.search_occurrence, name='search_occurrence'),
    path('collection/<str:tbiauuid>/', views.collection_detail, name='collection_detail'),
    path('occurrence/<str:tbiauuid>/', views.occurrence_detail, name='occurrence_detail'),
]
