from django import template
from django.utils.safestring import mark_safe 
import re

register = template.Library()


@register.filter
def highlight(text, keyword, autoescape=True):
    # first compile the regex pattern using the keyword
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    # now replace
    new_value = pattern.sub('<span class="col_red">\g<0></span>', text)
    return mark_safe(new_value)
