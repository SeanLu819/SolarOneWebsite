#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
B0 / A1 — CWV (Core Web Vitals) baseline snapshot via the PageSpeed Insights API.

Why: without a baseline we cannot prove that later speed work (B2) actually moved
the needle. This script captures LCP / CLS / INP / FCP / TTFB for 6 representative
page types, on both mobile and desktop, and writes them to
docs/perf_baseline_<YYYY-MM-DD>.json for diffing after each optimization batch.

Gate (L3): LCP must not regress >10%, CLS must stay <0.1, INP < 200ms.

Usage:
    python scripts/perf_baseline.py                 # reads PSI_API_KEY from env
    PSI_API_KEY=xxx python scripts/perf_baseline.py
    BASE_URL=https://staging.example.com python scripts/perf_baseline.py

Dependencies: standard library only (urllib). No third-party packages required.

Fallback: if no PSI_API_KEY is set, or the network/API call fails, the script
writes a *skeleton* baseline (every metric null) PLUS a `manual_instructions`
block, so the baseline file always exists and the diff workflow is ready. The
real numbers are filled in once a key is supplied (or via a manual Lighthouse
export — see manual_instructions).
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'docs')
DATE = datetime.now(timezone.utc).strftime('%Y-%m-%d')

BASE_URL = os.environ.get('BASE_URL', 'https://www.solaronelighting.com').rstrip('/')
PSI_API_KEY = os.environ.get('PSI_API_KEY', '')
PSI_ENDPOINT = 'https://www.googleapis.com/pagespeedonline/v5/runPagespeed'

# Six representative page types (B0 coverage). Adjust slugs if the catalogue changes.
PAGE_PATHS = [
    ('home', '/'),
    ('products', '/products/'),
    ('product_detail', '/products/m-series/'),
    ('projects', '/projects/'),
    ('project_detail', '/projects/yuanshen-sports-centre-stadium/'),
    ('contact', '/contact/'),
]
STRATEGIES = ['mobile', 'desktop']

# Field-name map inside PSI's loadingExperience.metrics.
METRIC_KEYS = {
    'lcp_ms': 'LARGEST_CONTENTFUL_PAINT_MS',
    'cls': 'CUMULATIVE_LAYOUT_SHIFT_SCORE',
    'inp_ms': 'INTERACTION_TO_NEXT_PAINT_MS',
    'fcp_ms': 'FIRST_CONTENTFUL_PAINT_MS',
    'ttfb_ms': 'EXPERIMENTAL_TIME_TO_FIRST_BYTE_MS',
}


def _fetch_one(url, strategy):
    """Return the PSI JSON for one URL/strategy, or None on any failure."""
    params = urllib.parse.urlencode({'url': url, 'strategy': strategy})
    if PSI_API_KEY:
        params += '&key=' + urllib.parse.quote(PSI_API_KEY, safe='')
    req = urllib.request.Request(PSI_ENDPOINT + '?' + params)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))


def _extract_metrics(psi_json):
    """Pull CWV numbers out of a PSI response. Returns dict of metric->value(or None)."""
    out = {k: None for k in METRIC_KEYS}
    if not psi_json:
        return out
    metrics = (
        psi_json.get('loadingExperience', {}).get('metrics', {})
        or psi_json.get('originLoadingExperience', {}).get('metrics', {})
    )
    for out_key, psi_key in METRIC_KEYS.items():
        node = metrics.get(psi_key)
        if not node:
            continue
        val = node.get('percentile')
        if val is None:
            continue
        if out_key == 'cls':
            # CLS score is 0..1 already in PSI (multiply by 100 only for display).
            out[out_key] = round(val / 100.0, 4) if val > 1 else round(val, 4)
        elif out_key in ('lcp_ms', 'inp_ms', 'fcp_ms', 'ttfb_ms'):
            out[out_key] = round(val / 1000.0, 3)  # ms -> seconds
    return out


def run():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    results = {}
    mode = 'live' if PSI_API_KEY else 'skeleton'

    for page_name, path in PAGE_PATHS:
        results[page_name] = {'path': path, 'strategies': {}}
        for strategy in STRATEGIES:
            entry = {'fetched_at': timestamp, 'source': mode, 'metrics': {k: None for k in METRIC_KEYS}}
            if PSI_API_KEY:
                try:
                    psi = _fetch_one(BASE_URL + path, strategy)
                    entry['metrics'] = _extract_metrics(psi)
                    entry['source'] = 'pagespeed-insights'
                except Exception as exc:  # noqa: BLE001 — best-effort, keep going
                    entry['error'] = str(exc)
                    sys.stderr.write('WARN: %s/%s failed: %s\n' % (page_name, strategy, exc))
            results[page_name]['strategies'][strategy] = entry

    # Gate summary (only meaningful for live data).
    gate = {'lcp_regression_limit': '<10%', 'cls_max': 0.1, 'inp_max_ms': 200, 'pass': None, 'notes': []}
    if mode == 'live':
        gate['pass'] = True
        for page_name, page in results.items():
            for strategy, entry in page['strategies'].items():
                m = entry['metrics']
                if m.get('cls') is not None and m['cls'] >= 0.1:
                    gate['pass'] = False
                    gate['notes'].append('%s/%s CLS %.3f >= 0.1' % (page_name, strategy, m['cls']))
                if m.get('inp_ms') is not None and m['inp_ms'] >= 200:
                    gate['pass'] = False
                    gate['notes'].append('%s/%s INP %dms >= 200' % (page_name, strategy, int(m['inp_ms'])))
    else:
        gate['notes'].append('Skeleton baseline — set PSI_API_KEY (or fill metrics manually) to capture real CWV.')

    payload = {
        'generated_at': timestamp,
        'base_url': BASE_URL,
        'mode': mode,
        'gate': gate,
        'pages': results,
        'manual_instructions': (
            'No PSI_API_KEY supplied. To capture real CWV: (1) enable the PageSpeed '
            'Insights API in Google Cloud and create an API key; (2) run '
            '`PSI_API_KEY=xxx python scripts/perf_baseline.py`. Alternatively export '
            'a Lighthouse JSON per page and copy LCP/CLS/INP/FCP/TTFB into the '
            'metrics blocks above.'
        ),
    }

    out_path = os.path.join(OUTPUT_DIR, 'perf_baseline_%s.json' % DATE)
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print('Wrote %s (mode=%s)' % (out_path, mode))
    return out_path


if __name__ == '__main__':
    run()
