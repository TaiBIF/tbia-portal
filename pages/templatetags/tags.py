from django import template
from django.utils.safestring import mark_safe 
import re
from datetime import timedelta

# from data.utils import get_variants
from pages.models import Notification
from manager.models import User
from conf.utils import notif_map
from django.utils.translation import get_language, gettext
import pandas as pd
import json

register = template.Library()


with open('/code/data/variants.json', 'r', encoding='utf-8') as f:
    var_dict = json.load(f)

var_df = pd.DataFrame([{'char': index, 'pattern': value} for index, value in var_dict.items() if len(index) == 1])

var_df['idx'] = var_df.groupby(['pattern']).ngroup()
var_df_2 = pd.DataFrame([{'char': index, 'pattern': value} for index, value in var_dict.items() if len(index) == 2])

# 先對一個字再對兩個字

def get_variants(string):
  new_string = ''
  # 單個異體字
  for s in string:    
    if len(var_df[var_df['char']==s]):
      new_string += var_df[var_df['char']==s].pattern.values[0]
    else:
      new_string += s
  # 兩個異體字
  for i in var_df_2.index:
    char = var_df_2.loc[i, 'char']
    if char in new_string:
      new_string = new_string.replace(char,f"{var_df_2.loc[i, 'pattern']}")
  return new_string


@register.simple_tag
def highlight(text, keyword, taxon_related=0):
    if taxon_related == '1':
        keyword = re.sub(' +', ' ', keyword)
    keyword = get_variants(re.escape(keyword))
    new_value = re.sub(keyword, '<span class="col_red">\g<0></span>', text, flags=re.IGNORECASE)
    return mark_safe(new_value)


@register.filter
def get_notif(user_id):
    notifications = Notification.objects.filter(user_id=user_id).order_by('-created')[:10]

    results = ""
    for n in notifications:
      if n.type in notif_map.keys(): 
        href = notif_map[n.type]
      elif n.type == 2:
          if User.objects.filter(id=user_id,is_system_admin=True).exists():
              href = '/manager/system/info?menu=feedback'
          else:
              href = '/manager/partner/info?menu=feedback'
      elif n.type == 3:
          if User.objects.filter(id=user_id,is_system_admin=True).exists():
              href = '/manager/system/info?menu=sensitive'
          else:
              href = '/manager/partner/info?menu=sensitive'
      elif n.type == 5:
          if User.objects.filter(id=user_id,is_system_admin=True).exists():
              href = '/manager/system/info?menu=account'
          else:
              href = '/manager/partner/info?menu=account'
      else:
          href = '/manager'

      created_8 = n.created + timedelta(hours=8)
      if not n.is_read: 
          is_read = '<div class="dottt"></div>'
      else:
          is_read = ''
      results += f"""
                  <li class="redirectToAdmin" data-nid="{n.id}" data-href="{href}">
                  {is_read}
                  <div class="txtcont">
                    <p class="date">{created_8.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>{gettext(n.get_type_display()).replace('0000', n.content)}</p>
                  </div>
                </li>
              """
    if not results:
        results = f"""
                    <li>
                    <div class="txtcont">
                      <p class="date"></p>
                      <p>{gettext('暫無通知')}</p>
                    </div>
                  </li>
                """
    return mark_safe(results)


@register.filter
def get_notif_count(user_id):
    count = Notification.objects.filter(user_id=user_id,is_read=False).count()
    return count