"""Custom template tags for SEO: hreflang links, etc."""
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


def _strip_lang_prefix(path):
    """Strip the language prefix from a URL path.

    E.g., '/fr/products/'  -> '/products/'
          '/fr/'           -> '/'
          '/'              -> '/'
          '/products/'     -> '/products/'
    """
    for code, _ in settings.LANGUAGES:
        if code == 'en':
            continue
        prefix = f'/{code}'
        if path == prefix or path.startswith(f'{prefix}/'):
            stripped = path[len(prefix):]
            return stripped if stripped else '/'
    return path


@register.simple_tag(takes_context=True)
def hreflang_links(context):
    """Render <link rel="alternate" hreflang="..."> tags for all languages."""
    request = context.get('request')
    if not request:
        return ''

    origin = settings.CANONICAL_ORIGIN
    clean_path = _strip_lang_prefix(request.path)

    links = []
    for code, _name in settings.LANGUAGES:
        if code == 'en':
            url = f'{origin}{clean_path}'
        else:
            url = f'{origin}/{code}{clean_path}'
        links.append(f'<link rel="alternate" hreflang="{code}" href="{url}">')

    # x-default points to the English (default) version
    x_default_url = f'{origin}{clean_path}'
    links.append(f'<link rel="alternate" hreflang="x-default" href="{x_default_url}">')

    return mark_safe('\n  '.join(links))