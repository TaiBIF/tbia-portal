from manager.models import SensitiveDataResponse, Workday
# from pages.models import Notification
from django.db import connection
from datetime import datetime, timedelta
# import pandas as pd
# from os.path import exists
# from manager.views import send_notification
from data.views import generate_sensitive_csv
import threading
# import glob
# import os
from conf.settings import env
from django.db.models import Max

web_mode = env('ENV')
if web_mode == 'stag':
    scheme = 'https'
    host = 'dev.tbiadata.tw'
elif web_mode == 'prod':
    scheme = 'https'
    host = 'tbiadata.tw'
else:
    scheme = 'http'
    host = '127.0.0.1:8000'

# 從notification裡面去撈每個user最新的request時間

# 系統管理員 如果7天後狀態是pending的話就直接通過
# 夥伴單位 如果14天後狀態是pending的話就直接通過


today = datetime.today() + timedelta(hours=8)
today = today.date()

# 系統管理員負責的
query = """
select sdr.id, (sdr.created AT TIME ZONE 'Asia/Taipei')::DATE, sdr.query_id from manager_sensitivedataresponse sdr
    where sdr.is_transferred = 'f' and sdr.status = 'pending' and sdr.partner_id is null;
"""
with connection.cursor() as cursor:
    cursor.execute(query)
    data = cursor.fetchall()

max_day = Workday.objects.all().aggregate(Max('date'))['date__max']

for d in data:
    # 找到當日的row
    c = 0
    # row_i = c_cal[c_cal.西元日期 == int(d[1])].index[0]
    row_date = d[1]
    while c < 7:
        row_date += timedelta(days=1)
        if not row_date > max_day:
            if Workday.objects.get(date=row_date).is_dayoff == 0:
                due = row_date
                c += 1
    if today >= due:
        sdr_id = d[0]
        if SensitiveDataResponse.objects.filter(id=sdr_id).exists():
            sdr = SensitiveDataResponse.objects.get(id=sdr_id)
            sdr.status = 'fail'
            sdr.reviewer_name = ''
            sdr.comment = ''
            sdr.save()
        # 確認是不是最後一個單位審核, 如果是的話產生下載檔案
        # 排除已轉移給各單位審核的機關計畫
        if not SensitiveDataResponse.objects.filter(query_id=d[2],status='pending').exclude(is_transferred=True).exists():
            task = threading.Thread(target=generate_sensitive_csv, args=(d[2],scheme,host))
            task.start()



# 夥伴單位負責的
# query = """
# select sdr.id, (sdr.created AT TIME ZONE 'Asia/Taipei')::DATE, sdr.query_id from manager_sensitivedataresponse sdr
# where sdr.is_transferred = 'f' and sdr.status = 'pending' and sdr.partner_id is not null;
# """

query = """
select sdr.id, (sdr.created AT TIME ZONE 'Asia/Taipei')::DATE, sdr.query_id from manager_sensitivedataresponse sdr
where sdr.status = 'pending' and sdr.partner_id is not null;
"""

with connection.cursor() as cursor:
    cursor.execute(query)
    data = cursor.fetchall()

for d in data:
    # 找到當日的row
    c = 0
    row_date = d[1]
    while c < 7:
        row_date += timedelta(days=1)
        if not row_date > max_day:
            if Workday.objects.get(date=row_date).is_dayoff == 0:
                due = row_date
                c += 1
    if today >= due:
        sdr_id = d[0]
        if SensitiveDataResponse.objects.filter(id=sdr_id).exists():
            sdr = SensitiveDataResponse.objects.get(id=sdr_id)
            sdr.status = 'fail'
            sdr.reviewer_name = ''
            sdr.comment = ''
            sdr.save()
        # 確認是不是最後一個單位審核, 如果是的話產生下載檔案
        # 排除已轉移給各單位審核的機關計畫
        if not SensitiveDataResponse.objects.filter(query_id=d[2],status='pending').exclude(is_transferred=True).exists():
            task = threading.Thread(target=generate_sensitive_csv, args=(d[2],scheme,host))
            task.start()