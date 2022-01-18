from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('qa', views.qa, name='qa'),
    path('about', views.about, name='about'),
    path('partner/<pk>', views.partner, name='partner'),
]
