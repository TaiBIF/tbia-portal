from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from manager.models import Workday #Partner, 
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

max_day = Workday.objects.all().aggregate(Max('date'))['date__max']

def check_due(checked_date, review_days): # 日期, 審核期限
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