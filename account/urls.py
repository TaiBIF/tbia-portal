from django.urls import path

from . import views

urlpatterns = [
    path('verify-user/<uidb64>/<token>', views.verify_user, name='verify'),
    path('account/personal-info', views.personal_info, name='personal_info'),
    path('register', views.register, name='register'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),
    path('account/system-feedback', views.system_feedback, name='system_feedback'),
    path('account/system-index', views.system_index, name='system_index'),
    path('account/system-resource', views.system_resource, name='system_resource'),
    path('account/system-review', views.system_review, name='system_review'),
    path('account/system-download', views.system_download, name='system_download'),
    path('account/unit-download', views.unit_download, name='unit_download'),
    path('account/unit-event', views.unit_event, name='unit_event'),
    path('account/unit-feedback', views.unit_feedback, name='unit_feedback'),
    path('account/unit-index', views.unit_index, name='unit_index'),
    path('account/unit-info', views.unit_info, name='unit_info'),
    path('account/unit-news', views.unit_news, name='unit_news'),
    path('account/unit-project', views.unit_project, name='unit_project'),
    path('account/unit-review', views.unit_review, name='unit_review'),

]
