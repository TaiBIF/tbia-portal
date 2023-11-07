from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from manager.models import Partner, Workday
from django.db.models import Max

class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)

generate_token = TokenGenerator()

# key: group, value: rightsHolder
# partner_map = {}
# holders = {
# 'brcas': '臺灣生物多樣性資訊機構 TaiBIF',
# 'brmas': '中央研究院生物多樣性中心植物標本資料庫',
# 'tbri': '台灣生物多樣性網絡 TBN',
# 'forest': '生態調查資料庫系統',
# 'cpami': '臺灣國家公園生物多樣性資料庫',
# 'tcd': '濕地環境資料庫',
# 'oca': '海洋保育資料倉儲系統',
# 'taif': '林業試驗所植物標本資料庫',
# 'fact':  '林業試驗所昆蟲標本館',
# 'ntm': '國立臺灣博物館典藏',
# 'wra': '河川環境資料庫',
# 'gbif': 'GBIF'}

# p_colors = ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065', '#555','#3B86C0','#304237','#C65454','#ccc' ]

# c = 0
# for h in holders.keys():
#     tmp_list = []
#     # for pp in p.info:
#     tmp_list.append({'dbname': holders[h], 'color': p_colors[c]})
#     c += 1
#     partner_map[h] = tmp_list



from datetime import datetime, tzinfo,timedelta
import pandas as pd
from os.path import exists
import os

lst = os.listdir('/tbia-volumes/bucket/calendar/')
lst.sort()

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