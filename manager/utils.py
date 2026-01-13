from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from manager.models import Workday, SensitiveDataResponse #Partner, 
from django.db.models import Max
from bs4 import BeautifulSoup
from datetime import timedelta #, datetime, tzinfo,
# import pandas as pd
# from os.path import exists
# import os

class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)

generate_token = TokenGenerator()


def check_due(checked_date, review_days): # 日期, 審核期限
    max_day = Workday.objects.all().aggregate(Max('date'))['date__max']
    final_due = ''
    c = 0
    while c < review_days:
        checked_date += timedelta(days=1)
        if not checked_date > max_day:
            if Workday.objects.get(date=checked_date).is_dayoff == 0:
                final_due = checked_date
                final_due = final_due.strftime('%Y-%m-%d')
                c += 1
    return final_due


def clean_quill_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')
    # 移除所有 h1~h6，保留內文
    for i in range(1, 7):
        for tag in soup.find_all(f'h{i}'):
            tag.name = 'p' 
    return str(soup)


def get_sensitive_status(query_id):
    # 通過、不通過、部分通過
    SensitiveDataResponse.objects.filter(query_id=query_id).exclude(is_transferred=True)

    qs = SensitiveDataResponse.objects.filter(query_id=query_id).exclude(is_transferred=True)

    # 2. 取出所有 status 並轉為不重複的集合 (Set)
    # flat=True 會讓結果變成 ['pass', 'fail', 'pass'...] 而不是 tuple 列表
    status_set = set(qs.values_list('status', flat=True))

    # 3. 邏輯判斷
    if not status_set:
        result = '' # 處理沒有 query_id 的情況
    elif status_set == {'pass'}:
        result = "通過"
    elif status_set == {'fail'}:
        result = "不通過"
    elif 'pass' in status_set and 'fail' in status_set:
        result = "部分通過"
    else:
        # 這裡處理防呆，例如如果有 'pending' 或其他狀態混在裡面
        result = "等待審核"

    return result