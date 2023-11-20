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

register = template.Library()

var_df = pd.DataFrame([
('鲃','[鲃䰾]'),
('䰾','[鲃䰾]'),
('刺','[刺刺]'),
('刺','[刺刺]'),
('葉','[葉葉]'),
('葉','[葉葉]'),
('鈎','[鈎鉤]'),
('鉤','[鈎鉤]'),
('臺','[臺台]'),
('台','[臺台]'),
('螺','[螺螺]'),
('螺','[螺螺]'),
('羣','[群羣]'),
('群','[群羣]'),
('峯','[峯峰]'),
('峰','[峯峰]'),
('曬','[晒曬]'),
('晒','[晒曬]'),
('裏','[裏裡]'),
('裡','[裏裡]'),
('薦','[荐薦]'),
('荐','[荐薦]'),
('艷','[豔艷]'),
('豔','[豔艷]'),
('粧','[妝粧]'),
('妝','[妝粧]'),
('濕','[溼濕]'),
('溼','[溼濕]'),
('樑','[梁樑]'),
('梁','[梁樑]'),
('秘','[祕秘]'),
('祕','[祕秘]'),
('污','[汙污]'),
('汙','[汙污]'),
('册','[冊册]'),
('冊','[冊册]'),
('唇','[脣唇]'),
('脣','[脣唇]'),
('朶','[朵朶]'),
('朵','[朵朶]'),
('鷄','[雞鷄]'),
('雞','[雞鷄]'),
('猫','[貓猫]'),
('貓','[貓猫]'),
('踪','[蹤踪]'),
('蹤','[蹤踪]'),
('恒','[恆恒]'),
('恆','[恆恒]'),
('獾','[貛獾]'),
('貛','[貛獾]'),
('万','[萬万]'),
('萬','[萬万]'),
('两','[兩两]'),
('兩','[兩两]'),
('椮','[槮椮]'),
('槮','[槮椮]'),
('体','[體体]'),
('體','[體体]'),
('鳗','[鰻鳗]'),
('鰻','[鰻鳗]'),
('蝨','[虱蝨]'),
('虱','[虱蝨]'),
('鲹','[鰺鲹]'),
('鰺','[鰺鲹]'),
('鳞','[鱗鳞]'),
('鱗','[鱗鳞]'),
('鳊','[鯿鳊]'),
('鯿','[鯿鳊]'),
('鯵','[鰺鯵]'),
('鰺','[鰺鯵]'),
('鲨','[鯊鲨]'),
('鯊','[鯊鲨]'),
('鹮','[䴉鹮]'),
('䴉','[䴉鹮]'),
('鴴','(行鳥|鴴)'),
('鵐','(鵐|巫鳥)'),
('䱵','(䱵|魚翁)'),
('䲗','(䲗|魚銜)'),
('䱀','(䱀|魚央)'),
('䳭','(䳭|即鳥)'),
('鱼','[魚鱼]'),
('魚','[魚鱼]'), 
('万','[萬万]'),
('萬','[萬万]'),
('鹨','[鷚鹨]'),
('鷚','[鷚鹨]'),
('蓟','[薊蓟]'),
('薊','[薊蓟]'),
('黒','[黑黒]'),
('黑','[黑黒]'),
('隠','[隱隠]'),
('隱','[隱隠]'),
('黄','[黃黄]'),
('黃','[黃黄]'),
('囓','[嚙囓]'),
('嚙','[嚙囓]'),
('莨','[茛莨]'),
('茛','[茛莨]'),
('霉','[黴霉]'),
('黴','[黴霉]'),
('莓','[苺莓]'),  
('苺','[苺莓]'),  
('藥','[葯藥]'),  
('葯','[葯藥]'),  
('菫','[堇菫]'),
('堇','[堇菫]')], columns=['char','pattern'])
var_df['idx'] = var_df.groupby(['pattern']).ngroup()

var_df_2 = pd.DataFrame([('行鳥','(行鳥|鴴)'),
('蝦虎','[鰕蝦]虎'),
('鰕虎','[鰕蝦]虎'),
('巫鳥','(鵐|巫鳥)'),
('魚翁','(䱵|魚翁)'),
('魚銜','(䲗|魚銜)'),
('魚央','(䱀|魚央)'),
('游蛇','[遊游]蛇'),
('遊蛇','[遊游]蛇'),
('即鳥','(䳭|即鳥)'),
('椿象','[蝽椿]象'),
('蝽象','[蝽椿]象')], columns=['char','pattern'])


# 產生javascript使用的dict
# dict(zip(var_df.char, var_df.pattern))
# dict(zip(var_df_2.char, var_df_2.pattern))


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
    # text_after = re.sub(regex_search_term, regex_replacement, text_before)
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