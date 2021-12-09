from django import template
from django.utils.safestring import mark_safe 

register = template.Library()

@register.filter
def highlight(text, keyword):
    highlighted = text.replace(keyword, '<span class="col_red">{}</span>'.format(keyword))
    return mark_safe(highlighted)

