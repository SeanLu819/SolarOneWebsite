"""Text processing filters.

`linebreaktospaces` strips <br> tags (and any stray carriage returns) from
already-linebreaked HTML so the text wraps naturally across the full
container width. Use it after the `linebreaks` filter to keep paragraph
splits (</p><p>) but drop the hard line-breaks that admins paste from
Word/PDF.
"""
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
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


@register.filter(name='nl2para', needs_autoescape=True)
def nl2para(value, autoescape=True):
    """Convert plain text with newlines into HTML paragraphs.

    Unlike Django's built-in ``linebreaks``, this preserves any inline HTML
    already in the text (e.g. ``<strong>``, ``<em>`` pasted by admins).

    Rules:
      - Blank-line separated blocks become ``<p>...</p>``
      - Single newlines within a block become ``<br>``
      - Carriage returns (``\\r``) are stripped
      - Empty input returns empty string
    """
    if not value:
        return ''
    text = str(value).replace('\r', '')
    # Split on blank lines to get paragraph blocks
    blocks = re.split(r'\n{2,}', text)
    paras = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Single newlines inside a block become <br>
        block_html = re.sub(r'\n', '<br>', block)
        paras.append(f'<p>{block_html}</p>')
    result = '\n'.join(paras)
    return mark_safe(result)
