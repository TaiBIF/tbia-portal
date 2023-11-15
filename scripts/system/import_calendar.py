from manager.models import Workday
from django.db import connection
from datetime import datetime, tzinfo,timedelta
import pandas as pd
from os.path import exists
import threading
import glob
import os
from conf.settings import env

# 從政府開放資料平台匯入工作日曆
# today = datetime.today() + timedelta(hours=8)

folder = '/tbia-volumes/bucket/calendar'
extension = 'csv'
os.chdir(folder)
files = glob.glob('calendar_*.{}'.format(extension))

c_cal = pd.DataFrame(columns=['西元日期','是否放假'])
for f in files:
    tmp_f = pd.read_csv(f'/tbia-volumes/bucket/calendar/{f}', usecols=['西元日期','是否放假'])
    c_cal = pd.concat([c_cal, tmp_f], ignore_index=True)

c_cal = c_cal.sort_values('西元日期').reset_index(drop=True)

c_cal = c_cal.rename(columns={'西元日期': 'date', '是否放假': 'is_dayoff'})

c_cal['is_dayoff'] = c_cal['is_dayoff'].replace({0: False, 2: True})
c_cal['date'] = c_cal['date'].apply(lambda x: datetime.strptime(str(x), "%Y%m%d").date())

for i in c_cal.index:
    row = c_cal.loc[i]
    p, created = Workday.objects.get_or_create(
        date=row.date,
        is_dayoff=row.is_dayoff,
    )
