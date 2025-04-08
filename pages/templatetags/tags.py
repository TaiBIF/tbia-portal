from django import template
from django.utils.safestring import mark_safe 
import re
from datetime import timedelta
from pages.models import Notification
from manager.models import User
from conf.utils import notif_map
from django.utils.translation import get_language, gettext
import pandas as pd
import json
from typing import List, Dict

register = template.Library()


with open('/code/data/variants.json', 'r', encoding='utf-8') as f:
    var_dict = json.load(f)

with open('/code/data/composites.json', 'r', encoding='utf-8') as f:
    comp_dict = json.load(f)


# 1. 異體字群組

variant_groups: List[List[str]] = var_dict

# 2. 會意字 ↔ 合成組合 映射
composite_map: Dict[str, str] = comp_dict
reverse_composite_map: Dict[str, str] = {v: k for k, v in composite_map.items()}

# 3. 查詢某個字的異體群組
def get_word_variants(char: str) -> List[str]:
    for group in variant_groups:
        if char in group:
            return group
    return [char]

# 4. 對一串文字生成正則 pattern，例如「台灣」→ [台臺]灣
def generate_pattern_from_word(word: str) -> str:
    return ''.join(
        f"[{''.join(get_word_variants(c))}]" if len(get_word_variants(c)) > 1 else c
        for c in word
    )

# 5. 主處理函式：將輸入文字轉換為包含異體字與會意字 pattern 的版本
def process_text_variants(text: str) -> str:
    result = ''
    i = 0
    while i < len(text):
        matched = False
        # 處理會意字組合：優先處理最長的詞組
        for composite, composed in composite_map.items():
            if text.startswith(composite, i):
                pattern = f"({composite}|{generate_pattern_from_word(composed)})"
                result += pattern
                i += len(composite)
                matched = True
                break
            elif text.startswith(composed, i):
                pattern = f"({composite}|{generate_pattern_from_word(composed)})"
                result += pattern
                i += len(composed)
                matched = True
                break
        if not matched:
            char = text[i]
            variants = get_word_variants(char)
            if len(variants) > 1:
                result += f"[{''.join(variants)}]"
            else:
                result += char
            i += 1
    return result


@register.simple_tag
def highlight(text, keyword, taxon_related=0):
    if taxon_related == '1':
        keyword = re.sub(' +', ' ', keyword)
    keyword = process_text_variants(re.escape(keyword))
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