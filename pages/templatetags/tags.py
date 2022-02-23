from django import template
from django.utils.safestring import mark_safe 
import re

from data.utils import get_variants

register = template.Library()


@register.filter
def highlight(text, keyword, autoescape=True):
    # first compile the regex pattern using the keyword
    keyword = get_variants(keyword)
    pattern = re.compile(keyword, re.IGNORECASE)
    # now replace
    new_value = pattern.sub('<span class="col_red">\g<0></span>', text)
    return mark_safe(new_value)


