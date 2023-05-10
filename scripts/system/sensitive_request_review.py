from manager.models import User, SensitiveDataResponse
from pages.models import Notification
from django.db import connection
from datetime import datetime, tzinfo,timedelta
import pandas as pd
from os.path import exists
from manager.views import send_notification
from data.views import generate_sensitive_csv
import threading
import glob
import os
# 從notification裡面去撈每個user最新的request時間

# 系統管理員 如果7天後狀態是pending的話就直接通過
# 夥伴單位 如果14天後狀態是pending的話就直接通過


today = datetime.today() + timedelta(hours=8)

folder = '/tbia-volumes/bucket/calendar'
extension = 'csv'
os.chdir(folder)
files = glob.glob('calendar_*.{}'.format(extension))

c_cal = pd.DataFrame(columns=['西元日期','星期','是否放假','備註'])
for f in files:
    tmp_f = pd.read_csv(f'/tbia-volumes/bucket/calendar/{f}')
    c_cal = c_cal.append(tmp_f, ignore_index=True)


c_cal = c_cal.sort_values('西元日期').reset_index(drop=True)

# 系統管理員負責的
query = """
select sdr.id, to_char(sdr.created AT TIME ZONE 'Asia/Taipei', 'YYYYMMDD'), sdr.query_id from manager_sensitivedataresponse sdr
where sdr.is_transferred = 'f' and sdr.status = 'pending' and sdr.partner_id is null;
"""

with connection.cursor() as cursor:
    cursor.execute(query)
    data = cursor.fetchall()

for d in data:
    # 找到當日的row
    c = 0
    row_i = c_cal[c_cal.西元日期 == int(d[1])].index[0]
    while c < 7:
        row_i += 1
        if not row_i > c_cal.index.max():
            if c_cal.iloc[row_i].是否放假 == 0:
                due = c_cal.iloc[row_i]
                c += 1
    if today.strftime('%Y%m%d') >= str(due.西元日期):
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
            task = threading.Thread(target=generate_sensitive_csv, args=(d[2],))
            task.start()



# 夥伴單位負責的
query = """
select sdr.id, to_char(sdr.created AT TIME ZONE 'Asia/Taipei', 'YYYYMMDD'), sdr.query_id from manager_sensitivedataresponse sdr
where sdr.is_transferred = 'f' and sdr.status = 'pending' and sdr.partner_id is not null;
"""

with connection.cursor() as cursor:
    cursor.execute(query)
    data = cursor.fetchall()

for d in data:
    # 找到當日的row
    c = 0
    row_i = c_cal[c_cal.西元日期 == int(d[1])].index[0]
    while c < 14:
        row_i += 1
        if not row_i > c_cal.index.max():
            if c_cal.iloc[row_i].是否放假 == 0:
                due = c_cal.iloc[row_i]
                c += 1
    if today.strftime('%Y%m%d') >= str(due.西元日期):
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
            task = threading.Thread(target=generate_sensitive_csv, args=(d[2],))
            task.start()