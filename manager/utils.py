from django.contrib.auth.tokens import PasswordResetTokenGenerator
import six
from manager.models import Partner

class TokenGenerator(PasswordResetTokenGenerator):

    def _make_hash_value(self, user, timestamp):
        return six.text_type(user.pk)+six.text_type(timestamp)+six.text_type(user.is_email_verified)

generate_token = TokenGenerator()

# key: group, value: rightsHolder
partner_map = {}
p_colors = ['#76A578','#DEE9DE','#3F5146','#E2A460','#f4e2c7','#888','#ead065', '#555','#3B86C0','#304237','#C65454','#ccc' ]
c = 0
for p in Partner.objects.all():
    tmp_list = []
    for pp in p.info:
        tmp_list.append({'dbname': pp.get('subtitle'), 'color': p_colors[c]})
        c += 1
    partner_map[p.group] = tmp_list


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

