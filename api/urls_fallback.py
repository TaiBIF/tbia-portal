"""5.5：/api/v2 底下不存在的網址回 JSON 404。

只能在 conf/urls.py「不帶語言前綴」的 urlpatterns 裡 include，不能放進 api/urls.py：
api/urls.py 也掛在 i18n_patterns 底下，若 /zh-hant/api/v2/<任何> 也是有效網址，
LocaleMiddleware 遇到 /api/v2/abc 的 404 會判斷「加上語言前綴的網址有效」而 302 轉址（11/23 測試站發現）。
"""
from django.urls import re_path

from . import v2

urlpatterns = [
    re_path(r'^api/v2(/.*)?$', v2.not_found, name='api_v2_not_found'),
]
