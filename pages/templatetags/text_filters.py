"""Text processing filters.

`linebreaktospaces` strips <br> tags (and any stray carriage returns) from
already-linebreaked HTML so the text wraps naturally across the full
container width. Use it after the `linebreaks` filter to keep paragraph
splits (</p><p>) but drop the hard line-breaks that admins paste from
Word/PDF.

Both filters are XSS-safe: text content is HTML-escaped before any
structural markup (<p>/<br>) generated here is added. Admin-entered
markup is rendered literally, never executed. If rich text is ever
needed, sanitize with a dedicated library (e.g. bleach) instead.
"""
from django import template
from django.utils.html import conditional_escape, escape
from django.utils.safestring import mark_safe, SafeData
import re

register = template.Library()

_BR_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)
_CR_RE = re.compile(r'\r')


@register.filter(name='linebreaktospaces')
def linebreaktospaces(value):
    """Replace <br> tags (and \\r) with a space. Returns safe HTML.

    Expects HTML produced by Django's `linebreaks` filter (SafeString).
    Raw, unescaped strings are escaped before output, so user-supplied
    markup can never pass through (XSS-safe, #10).
    """
    if not value:
        return value
    if not isinstance(value, SafeData):
        # Raw input (not from a safe producer like `linebreaks`): escape it.
        # There are no real <br> tags in escaped plain text, which is the
        # correct outcome for raw strings.
        return mark_safe(escape(str(value)).replace('\r', ''))
    cleaned = _BR_RE.sub(' ', str(value))
    cleaned = _CR_RE.sub('', cleaned)
    return mark_safe(cleaned)


@register.filter(name='nl2para', needs_autoescape=True)
def nl2para(value, autoescape=True):
    """Convert plain text with newlines into HTML paragraphs.

    All text content is HTML-escaped first (#9) — inline markup such as
    ``<script>`` is rendered literally, never executed. Only the
    structural ``<p>``/``<br>`` tags generated here are real HTML.

    Rules:
      - Blank-line separated blocks become ``<p>...</p>``
      - Single newlines within a block become ``<br>``
      - Carriage returns (``\\r``) are stripped
      - Empty input returns empty string
    """
    if not value:
        return ''
    if autoescape:
        # conditional_escape passes SafeStrings through untouched and
        # escapes raw str values — prevents double-escaping as well.
        text = str(conditional_escape(value))
    else:
        text = str(value)
    text = text.replace('\r', '')
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
