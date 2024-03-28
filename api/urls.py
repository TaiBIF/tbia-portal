from django.urls import path

from . import views

urlpatterns = [
    path('api/doc', views.api_doc, name='api_doc'),
    path('api/v1/occurrence', views.occurrence, name='occurrence'),
    path('api/v1/dataset', views.dataset, name='dataset'),
]
