"""Push site URLs to IndexNow (Bing / Yandex / Seznam / Naver).

Why: without IndexNow, Bing only discovers new or changed pages on its own
crawl schedule. With it we can tell it the moment we deploy.

The key file is served by the Django view `pages.views.views_other.indexnow_key`
at ``https://<host>/<key>.txt`` (route name `indexnow_key`). IndexNow validates
that file before accepting pushes, so it must be reachable first.

Usage (from the repo root):
    E:/Python/python3/python.exe scripts/indexnow_ping.py              # dry run
    E:/Python/python3/python.exe scripts/indexnow_ping.py --live       # actually push
    E:/Python/python3/python.exe scripts/indexnow_ping.py --lang en    # one language only
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')

import django  # noqa: E402
django.setup()

from django.conf import settings  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils.translation import override  # noqa: E402

from pages.views.utils import _load_seed  # noqa: E402

ENDPOINT = 'https://api.indexnow.org/indexnow'
MAX_URLS_PER_CALL = 10000
HEX_KEY_RE = re.compile(r'^[a-f0-9]{8,128}$')


def build_urls(langs):
    """Every indexable URL, in every requested language."""
    urls = []
    seen = set()

    def add(path_with_slash):
        url = settings.CANONICAL_ORIGIN + path_with_slash
        if url not in seen:
            seen.add(url)
            urls.append(url)

    seed = _load_seed()
    product_slugs = [p.get('slug') for p in seed.get('products', []) if p.get('slug')]
    project_slugs = [p.get('slug') for p in seed.get('projects', []) if p.get('slug')]
    news_slugs = [a.get('slug') for a in seed.get('news', []) if a.get('slug')]

    for code in langs:
        with override(code):
            for name in (
                'home', 'products', 'projects', 'projects_football',
                'projects_tennis', 'news', 'about', 'privacy', 'terms',
                'contact',
            ):
                add(reverse(name))
            for slug in product_slugs:
                add(reverse('product_detail', args=[slug]))
            for slug in project_slugs:
                add(reverse('project_detail', args=[slug]))
            for slug in news_slugs:
                add(reverse('news_detail', args=[slug]))
    return urls


def push(host, key, urls):
    payload = json.dumps({
        'host': host,
        'key': key,
        'urlList': urls,
    }).encode('utf-8')
    req = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'User-Agent': 'SolarOne-IndexNow/1.0',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode('utf-8', 'replace')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--live', action='store_true',
                    help='actually POST to IndexNow (default is a dry run)')
    ap.add_argument('--lang', action='append', default=None,
                    help='limit to a language code (repeatable); default: all')
    args = ap.parse_args()

    key = getattr(settings, 'INDEXNOW_KEY', '')
    if not key:
        print('ERROR: INDEXNOW_KEY is not configured')
        return 2
    if not HEX_KEY_RE.match(key):
        print('ERROR: key must be 8-128 hex chars, got %r' % key)
        return 2

    host = re.sub(r'^https?://', '', settings.CANONICAL_ORIGIN)
    langs = args.lang or [c for c, _ in settings.LANGUAGES]
    urls = build_urls(langs)

    print('host        :', host)
    print('key file    :', settings.CANONICAL_ORIGIN + '/' + key + '.txt')
    print('languages   :', ', '.join(langs))
    print('urls        :', len(urls))
    print('endpoint    :', ENDPOINT)

    if not args.live:
        print()
        print('-- DRY RUN (pass --live to actually push) --')
        for u in urls[:10]:
            print('  ', u)
        if len(urls) > 10:
            print('   ... and %d more' % (len(urls) - 10))
        return 0

    if len(urls) > MAX_URLS_PER_CALL:
        print('ERROR: %d urls exceeds the %d limit'
              % (len(urls), MAX_URLS_PER_CALL))
        return 2

    try:
        status, body = push(host, key, urls)
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode('utf-8', 'replace')
    except Exception as exc:  # network down / DNS
        print('ERROR: push failed:', exc)
        return 1

    print()
    print('HTTP', status, body[:400])
    return 0 if status in (200, 202) else 1


if __name__ == '__main__':
    sys.exit(main())
