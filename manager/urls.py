from django.urls import path

from . import views

urlpatterns = [
    path('google/callback', views.get_auth_callback, name='get_auth_callback'),
    path('verify-user/<uidb64>/<token>', views.verify_user, name='verify'),
    path('verify-reset-password/<uidb64>/<token>', views.verify_reset_password, name='verify_reset_password'),
    path('reset_password', views.reset_password, name='reset_password'),
    path('reset_password_submit', views.reset_password_submit, name='reset_password_submit'),
    path('send_reset_password', views.send_reset_password, name='send_reset_password'),
    path('register', views.register, name='register'),
    path('register/verification', views.register_verification, name='register_verification'),
    path('register/success', views.register_success, name='register_success'),
    path('register/resend/verification', views.resend_verification_email, name='resend_verification_email'),
    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),
    path('manager', views.manager, name='manager'),
    path('update_personal_info', views.update_personal_info, name='update_personal_info'),
    path('manager/partner', views.manager_partner, name='manager_partner'),
    path('manager/system', views.manager_system, name='manager_system'),
    path('generate_no_taxon_csv', views.generate_no_taxon_csv, name='generate_no_taxon_csv'),
    path('update_partner_info', views.update_partner_info, name='update_partner_info'),
    # path('manager/personal-info', views.personal_info, name='personal_info'),
    # path('manager/system-feedback', views.system_feedback, name='system_feedback'),
    # path('manager/system-index', views.system_index, name='system_index'),
    # path('manager/system-resource', views.system_resource, name='system_resource'),
    # path('manager/system-review', views.system_review, name='system_review'),
    # path('manager/system-download', views.system_download, name='system_download'),
    # path('manager/unit-download', views.unit_download, name='unit_download'),
    # path('manager/unit-event', views.unit_event, name='unit_event'),
    # path('manager/unit-feedback', views.unit_feedback, name='unit_feedback'),
    # path('manager/unit-index', views.unit_index, name='unit_index'),
    # path('manager/unit-info', views.unit_info, name='unit_info'),
    # path('manager/unit-news', views.unit_news, name='unit_news'),
    # path('manager/unit-project', views.unit_project, name='unit_project'),
    # path('manager/unit-review', views.unit_review, name='unit_review'),

]
