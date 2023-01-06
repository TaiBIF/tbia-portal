from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six

class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)

generate_token = TokenGenerator()

# TODO 這邊好像其實就是subtitle
partner_source_map = {
    'tesri': ['台灣生物多樣性網絡 TBN'],
    'brcas': ['臺灣生物多樣性資訊機構 TaiBIF','中央研究院生物多樣性中心植物標本資料庫'],
    'forest': ['生態調查資料庫系統'],
    'cpami': ['臺灣國家公園生物多樣性資料庫'],
    'tcd': ['濕地環境資料庫'], # 城鄉發展分署
    'oca': ['iOcean海洋保育網'],
    'tfri': ['林業試驗所植物標本資料庫'],
}

from datetime import datetime, tzinfo,timedelta
import pandas as pd
from os.path import exists
import os

lst = os.listdir('/tbia-volumes/bucket/calendar/')
lst.sort()

# today = datetime.today() + timedelta(hours=8)

# this_year = today.year
# c_cal = pd.read_csv(f'/tbia-volumes/bucket/calendar/calendar_{this_year}.csv')
# if exists(f'/tbia-volumes/bucket/calendar/calendar_{this_year+1}.csv'):
#     c_cal_1 = pd.read_csv(f'/tbia-volumes/bucket/calendar/calendar_{this_year+1}.csv')
#     c_cal = c_cal.append(c_cal_1, ignore_index=True)

c_cal = pd.DataFrame()
for l in lst:
    c = pd.read_csv(f'/tbia-volumes/bucket/calendar/{l}')
    c_cal = c_cal.append(c, ignore_index=True)


def check_due(checked_date, review_days): # 日期, 審核期限
    final_due = ''
    checked_date = checked_date.replace('-','')
    c = 0
    row_i = c_cal[c_cal.西元日期 == int(checked_date)].index[0]
    while c < review_days:
        row_i += 1
        if not row_i > c_cal.index.max():
            if c_cal.iloc[row_i].是否放假 == 0:
                due = c_cal.iloc[row_i]
                final_due = str(due.西元日期)
                final_due = datetime.strptime(final_due,'%Y%m%d').strftime('%Y-%m-%d')
                c += 1
    return final_due

