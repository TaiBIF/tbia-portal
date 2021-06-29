from django.urls import path

from . import views

urlpatterns = [
    path('account/personal-info', views.personal_info, name='personal_info'),
    path('register', views.register, name='register'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),
]
