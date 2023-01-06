from django import template
from django.utils.safestring import mark_safe 
import re
from datetime import timedelta

from data.utils import get_variants
from pages.models import Notification

register = template.Library()


@register.filter
def highlight(text, keyword, autoescape=True):
    keyword = get_variants(re.escape(keyword))
    # text_after = re.sub(regex_search_term, regex_replacement, text_before)
    new_value = re.sub(keyword, '<span class="col_red">\g<0></span>', text)
    return mark_safe(new_value)


@register.filter
def get_notif(user_id):
    notifications = Notification.objects.filter(user_id=user_id).order_by('-created')[:10]
    results = ""
    for n in notifications:
        created_8 = n.created + timedelta(hours=8)
        if not n.is_read: 
            is_read = '<div class="dottt"></div>'
        else:
            is_read = ''
        results += f"""
                    <li class="updateThisRead" data-nid="{n.id}">
                    {is_read}
                    <div class="txtcont">
                      <p class="date">{created_8.strftime('%Y-%m-%d %H:%M:%S')}</p>
                      <p>{n.get_type_display().replace('0000', n.content)}</p>
                    </div>
                  </li>
                """
    if not results:
        results = """
                    <li>
                    <div class="txtcont">
                      <p class="date"></p>
                      <p>暫無通知</p>
                    </div>
                  </li>
                """
    return mark_safe(results)


@register.filter
def get_notif_count(user_id):
    count = Notification.objects.filter(user_id=user_id,is_read=False).count()
    return count