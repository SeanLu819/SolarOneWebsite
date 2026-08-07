"""Text processing filters.

`linebreaktospaces` strips <br> tags (and any stray carriage returns) from
already-linebreaked HTML so the text wraps naturally across the full
container width. Use it after the `linebreaks` filter to keep paragraph
splits (</p><p>) but drop the hard line-breaks that admins paste from
Word/PDF.
"""
from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

_BR_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)
_CR_RE = re.compile(r'\r')


@register.filter(name='linebreaktospaces')
def linebreaktospaces(value):
    """Replace <br> tags (and \r) with a space. Returns safe HTML."""
    if not value:
        return value
    cleaned = _BR_RE.sub(' ', str(value))
    cleaned = _CR_RE.sub('', cleaned)
    return mark_safe(cleaned)
