from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('qa', views.qa, name='qa'),
    path('about', views.about, name='about'),
    path('resources', views.resources, name='resources'),
    path('get_resources', views.get_resources, name='get_resources'),
    path('partner/<abbr>', views.partner, name='partner'),
]
