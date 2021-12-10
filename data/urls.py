from django.urls import path

from . import views

urlpatterns = [
    path('search/full', views.search_full, name='search_full'),
    path('search/full/result', views.search_full_result, name='search_full_result'),
    path('search/full/doc/<result_type>/<keyword>', views.search_full_doc, name='search_full_doc'),
    path('search/collection', views.search_collection, name='search_collection'),
    path('search/collection-details/<int:tbiauuid>/', views.search_collection_details, name='search_collection_details'),
    path('search/occurrence', views.search_occurrence, name='search_occurrence'),
    path('search/occurrence-details/<int:tbiauuid>/', views.search_occurrence_details, name='search_occurrence_details'),
]
