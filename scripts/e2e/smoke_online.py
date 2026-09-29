#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B0 / L2 — online smoke test (run after every deploy).

Asserts the production site's SEO + analytics surface is intact:
  1. Key routes return 200 (/, /products/, /products/<slug>/, /projects/,
     /projects/<slug>/, /news/, /contact/).
  2. Each page has a <title>, a canonical link, and hreflang (6 langs + x-default).
  3. At least one JSON-LD block is present and parses as JSON.
  4. GA4 (G- id) and GSC verification meta are present IF configured (best-effort).
  5. /robots.txt (AI block), /llm.txt, /llms.txt, /news/feed.xml, /sitemap.xml = 200.

Usage:
    python scripts/e2e/smoke_online.py
    BASE_URL=https://www.solaronelighting.com python scripts/e2e/smoke_online.py

Exit code 0 = all checks passed; 1 = one or more failed.
Standard library only.
"""
import json
import os
import re
import sys
import urllib.request

BASE_URL = os.environ.get('BASE_URL', 'https://www.solaronelighting.com').rstrip('/')

ROUTES = [
    ('home', '/'),
    ('products', '/products/'),
    ('product_detail', '/products/m-series/'),
    ('projects', '/projects/'),
    ('project_detail', '/projects/yuanshen-sports-centre-stadium/'),
    ('news', '/news/'),
    ('about', '/about/'),
    ('privacy', '/privacy/'),
    ('terms', '/terms/'),
    ('contact', '/contact/'),
]

ASSETS = [
    ('robots_txt', '/robots.txt'),
    ('llm_txt', '/llm.txt'),
    ('llms_txt', '/llms.txt'),
    ('news_feed', '/news/feed.xml'),
    ('sitemap', '/sitemap.xml'),
    ('manifest', '/static/manifest.json'),
    ('apple_touch_icon', '/static/images/apple-touch-icon.png'),
]

HREFLANG_TAGS = ['hreflang="en"', 'hreflang="fr"', 'hreflang="es"',
                 'hreflang="de"', 'hreflang="ru"', 'hreflang="ar"', 'hreflang="x-default"']


def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'SolarOne-Smoke/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.getcode(), resp.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as exc:
        return exc.code, ''
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write('ERR %s: %s\n' % (url, exc))
        return -1, ''


def _check(name, url, code, html, checks, collector):
    for label, ok in checks:
        status = 'PASS' if ok else 'FAIL'
        print('  [%s] %-14s %-16s %s' % (status, name, label, url))
        if not ok:
            collector.result_failures.append((name, label, url))


class _FailCollector:
    def __init__(self):
        self.result_failures = []


def run():
    fails = _FailCollector()
    print('== Route checks (%s) ==' % BASE_URL)
    for name, path in ROUTES:
        code, html = _get(BASE_URL + path)
        checks = [
            ('status_200', code == 200),
            ('has_title', '<title>' in html and '</title>' in html),
            ('has_canonical', 'rel="canonical"' in html),
        ]
        for tag in HREFLANG_TAGS:
            checks.append(('hreflang:%s' % tag.split('"')[1], tag in html))
        checks.append(('jsonld_present', 'application/ld+json' in html))
        _check(name, path, code, html, checks, fails)
        # JSON-LD parseability
        if 'application/ld+json' in html:
            import re
            blocks = re.findall(r'application/ld\+json">(.*?)</script>', html, re.S)
            parsed_any = False
            for b in blocks:
                try:
                    json.loads(b)
                    parsed_any = True
                except Exception:
                    pass
            ok = parsed_any
            print('  [%s] %-14s %-16s %s' % ('PASS' if ok else 'FAIL', name, 'jsonld_valid', path))
            if not ok:
                fails.result_failures.append((name, 'jsonld_valid', path))

    # B3 — per-page SEO titles must contain the category keyword + brand signature
    # (proves the per-page title formula is live, not the old global/name-only title).
    print('== B3 per-page SEO titles ==')
    seo_targets = [
        ('/products/m-series/', 'M Series', ''),
        ('/products/fl6m/', 'FL6M', ''),
        # SPORTS_LIGHTING 品类词按实测搜索需求重切为 "LED Stadium Lights"
        # （SEMrush US 2026-09-29：stadium lights 2,900/mo、led stadium lights
        # 1,000/mo KD 6）。线上必须看到新措辞，否则说明改动没生效。
        ('/products/vsp-xxxxw-9m-yp/', 'VSP', 'Stadium Lights'),
    ]
    for path, ident, keyword in seo_targets:
        code, html = _get(BASE_URL + path)
        m = re.search(r'<title>(.*?)</title>', html, re.S)
        title = m.group(1) if m else ''
        ok = (code == 200 and ident in title and '| SolarOne' in title
              and (not keyword or keyword in title))
        print('  [%s] %-14s %-16s %s' % ('PASS' if ok else 'FAIL', 'seo_title', path, title))
        if not ok:
            fails.result_failures.append(('seo_title', path, title))

    print('== Asset checks ==')
    for name, path in ASSETS:
        code, _ = _get(BASE_URL + path)
        ok = code == 200
        print('  [%s] %-14s %-16s %s' % ('PASS' if ok else 'FAIL', name, 'status_200', path))
        if not ok:
            fails.result_failures.append((name, 'status_200', path))

    # Best-effort: GA4 / GSC presence (only meaningful if configured on the host).
    _, home_html = _get(BASE_URL + '/')
    ga4 = 'googletagmanager.com/gtag/js' in home_html
    gsc = 'google-site-verification' in home_html
    # Manifest validity (B1/F2): must be reachable AND parse as JSON with a name.
    print('== Manifest (B1/F2) ==')
    code, manifest_body = _get(BASE_URL + '/static/manifest.json')
    manifest_ok = False
    if code == 200:
        try:
            mj = json.loads(manifest_body)
            manifest_ok = bool(mj.get('name') and mj.get('icons'))
        except Exception:
            manifest_ok = False
    print('  [%s] %-14s %-16s %s' % ('PASS' if manifest_ok else 'FAIL', 'manifest', 'valid_json', '/static/manifest.json'))
    if not manifest_ok:
        fails.result_failures.append(('manifest', 'valid_json', '/static/manifest.json'))

    print('== Analytics (best-effort) ==')
    print('  [INFO] GA4 gtag loader present: %s' % ga4)
    print('  [INFO] GSC verification meta present: %s' % gsc)
    if not ga4 or not gsc:
        print('  [NOTE] If GA4/GSC are expected on production, set the env vars in '
              'Vercel (GA4_MEASUREMENT_ID / GSC_VERIFICATION_CODE) — see B0/D1.')

    print('== Summary ==')
    if fails.result_failures:
        for f in fails.result_failures:
            print('  FAIL: %s / %s  (%s)' % f)
        print('RESULT: %d failure(s)' % len(fails.result_failures))
        return 1
    print('RESULT: all checks passed')
    return 0


if __name__ == '__main__':
    sys.exit(run())
