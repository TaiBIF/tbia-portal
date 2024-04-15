from django.urls import path

from . import views

urlpatterns = [
    # 確認是否登入
    path('get_is_authenticated', views.get_is_authenticated, name='get_is_authenticated'),
    # 後台頁面
    path('manager', views.manager, name='manager'),
    path('manager/partner', views.manager_partner, name='manager_partner'),
    path('manager/partner/news', views.partner_news, name='partner_news'),
    path('manager/partner/info', views.partner_info, name='partner_info'),
    path('manager/system', views.manager_system, name='manager_system'),
    path('manager/system/news', views.system_news, name='system_news'),
    path('manager/system/info', views.system_info, name='system_info'),
    path('manager/system/keyword', views.system_keyword, name='system_keyword'),
    path('manager/system/resource', views.system_resource, name='system_resource'),
    path('manager/system/qa', views.system_qa, name='system_qa'),
    # 登入 / 登出
    path('login', views.login_user, name='login'),
    path('logout', views.logout_user, name='logout'),
    path('login/google/callback', views.get_auth_callback, name='get_auth_callback'),
    # 驗證連結: 註冊email / 重設密碼
    path('verify-user/<uidb64>/<token>', views.verify_user, name='verify'),
    path('verify-reset-password/<uidb64>/<token>', views.verify_reset_password, name='verify_reset_password'),
    # 重設密碼
    path('reset_password', views.reset_password, name='reset_password'),
    path('reset_password_submit', views.reset_password_submit, name='reset_password_submit'),
    path('send_reset_password', views.send_reset_password, name='send_reset_password'),
    # 註冊
    path('register', views.register, name='register'),
    path('register/verification', views.register_verification, name='register_verification'),
    path('register/success', views.register_success, name='register_success'),
    path('register/resend/verification', views.resend_verification_email, name='resend_verification_email'),
    # 個人資料修改 / 單位帳號申請
    path('update_personal_info', views.update_personal_info, name='update_personal_info'),
    path('send_partner_request', views.send_partner_request, name='send_partner_request'),
    path('withdraw_partner_request', views.withdraw_partner_request, name='withdraw_partner_request'),
    # 帳號後台
    path('update_user_status', views.update_user_status, name='update_user_status'), 
    path('update_partner_info', views.update_partner_info, name='update_partner_info'), 
    # 系統後台 關鍵字 / TBIA設定
    path('update_keywords', views.update_keywords, name='update_keywords'),
    path('update_tbia_about', views.update_tbia_about, name='update_tbia_about'),
    # 取得資料 後台統計圖 / 敏感資料申請內容
    path('get_partner_stat', views.get_partner_stat, name='get_partner_stat'),
    path('get_system_stat', views.get_system_stat, name='get_system_stat'),
    path('get_request_detail', views.get_request_detail, name='get_request_detail'), 
    path('get_keyword_stat', views.get_keyword_stat, name='get_keyword_stat'), 
    path('get_checklist_stat', views.get_checklist_stat, name='get_checklist_stat'), 
    path('get_data_stat', views.get_data_stat, name='get_data_stat'), 
    path('get_taxon_group_list', views.get_taxon_group_list, name='get_taxon_group_list'), 
    # link 管理
    path('edit_link', views.edit_link, name='edit_link'),
    path('get_link_content', views.get_link_content, name='get_link_content'),
    # resource 管理
    path('save_resource_file', views.save_resource_file, name='save_resource_file'),
    path('submit_resource', views.submit_resource, name='submit_resource'),
    path('delete_resource', views.delete_resource, name='delete_resource'),
    # news 管理
    path('submit_news', views.submit_news, name='submit_news'),
    path('withdraw_news', views.withdraw_news, name='withdraw_news'),
    path('get_news_content', views.get_news_content, name='get_news_content'),
    path('save_news_image', views.save_news_image, name='save_news_image'),
    # feedback 通知 / 管理
    path('send_feedback', views.send_feedback, name='send_feedback'),
    path('update_feedback', views.update_feedback, name='update_feedback'),
    # QA 管理
    path('submit_qa', views.submit_qa, name='submit_qa'),
    path('delete_qa', views.delete_qa, name='delete_qa'),
    # 各表格換頁
    path('change_manager_page', views.change_manager_page, name='change_manager_page'),
    # 敏感資料申請報表
    path('download_sensitive_report', views.download_sensitive_report, name='download_sensitive_report'),
]
