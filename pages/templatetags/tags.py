from django import template
from django.utils.safestring import mark_safe 
import re

from data.utils import get_variants

register = template.Library()


@register.filter
def highlight(text, keyword, autoescape=True):
    keyword = get_variants(re.escape(keyword))
    # text_after = re.sub(regex_search_term, regex_replacement, text_before)
    new_value = re.sub(keyword, '<span class="col_red">\g<0></span>', text)
    return mark_safe(new_value)
