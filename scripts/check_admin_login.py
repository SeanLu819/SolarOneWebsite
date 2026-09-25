#!/usr/bin/env python
"""Local Django-admin login / CSRF sanity check.

Run this whenever POSTing in the local admin fails with a CSRF 403. It talks
to the running dev server over plain HTTP with its own cookie jar, so the
verdict separates the two possible culprits:

  * server-side broken   -> a clean cookie jar cannot even log in
  * browser-side stale   -> a clean cookie jar logs in fine, meaning the
                            browser is sending a `csrftoken` cookie that does
                            not match the token in the form it submitted

Why a cookie mismatch is the *only* way to get "CSRF token from POST
incorrect": Django compares the submitted token against the value stored in
the `csrftoken` cookie — SECRET_KEY is not involved at all. Probes
`--probe stale-cookie` prove this by logging in with a deliberately bogus
(but internally consistent) cookie value.

Usage
-----
    python scripts/check_admin_login.py
    python scripts/check_admin_login.py --base http://192.168.1.5:8080
    python scripts/check_admin_login.py --user admin --password admin
    python scripts/check_admin_login.py --probe stale-cookie
    python scripts/check_admin_login.py --probe proxy-header

No Django setup is needed — it is a plain HTTP client.
"""
from __future__ import annotations

import argparse
import http.cookiejar
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

REASON_RE = re.compile(
    r'Reason given for failure:</p>\s*<pre[^>]*>(.*?)</pre>', re.S)
TOKEN_RE = re.compile(r'name="csrfmiddlewaretoken" value="([^"]+)"')


class Result:
    def __init__(self, label, status, detail):
        self.label, self.status, self.detail = label, status, detail

    def __str__(self):
        return '%-42s HTTP %-3s %s' % (self.label, self.status, self.detail)


def _jar(cookie_value=None):
    jar = http.cookiejar.CookieJar()
    if cookie_value is not None:
        jar.set_cookie(http.cookiejar.Cookie(
            version=0, name='csrftoken', value=cookie_value, port=None,
            port_specified=False, domain='127.0.0.1', domain_specified=False,
            domain_initial_dot=False, path='/', path_specified=True,
            secure=False, expires=None, discard=False, comment=None,
            comment_url=None, rest={}, rfc2109=False))
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)), jar


def _render(op, login_url):
    with op.open(login_url, timeout=15) as r:
        html = r.read().decode('utf-8', 'replace')
        headers = r.headers
    match = TOKEN_RE.search(html)
    return (match.group(1) if match else None), headers


def _post(op, login_url, token, user, password, extra_headers=None,
          referer=None):
    body = urllib.parse.urlencode({
        'csrfmiddlewaretoken': token,
        'username': user,
        'password': password,
        'next': '/admin/',
    }).encode()
    headers = {
        'Referer': referer or login_url,
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    headers.update(extra_headers or {})
    req = urllib.request.Request(login_url, data=body, headers=headers)
    try:
        with op.open(req, timeout=15) as r:
            text = r.read().decode('utf-8', 'replace')
            if r.geturl().rstrip('/').endswith('/admin'):
                return 'LOGIN OK (reached /admin/)'
            if 'Please enter the correct' in text:
                return 'rejected: wrong username/password'
            return 'unexpected body (%d bytes)' % len(text)
    except urllib.error.HTTPError as e:
        text = e.read().decode('utf-8', 'replace')
        reason = REASON_RE.search(text)
        if reason:
            return 'CSRF 403 :: %s' % re.sub(r'\s+', ' ', reason.group(1)).strip()
        return 'HTTP %s' % e.code
    except urllib.error.URLError as e:
        return 'cannot reach server (%s)' % e.reason


def probe_clean(login_url, user, password):
    """A fresh jar must be able to log in. Failure here = server-side problem."""
    op, jar = _jar()
    token, headers = _render(op, login_url)
    cookie = next((c.value for c in jar if c.name == 'csrftoken'), None)
    print('Set-Cookie emitted      : %s' % ('yes' if cookie else 'NO'))
    if cookie:
        age = re.search(r'Max-Age=(\d+)', headers.get('Set-Cookie', ''))
        print('csrftoken Max-Age       : %s' % (
            ('%s s (~%.0f days)' % (age.group(1), int(age.group(1)) / 86400))
            if age else 'session-scoped'))
    print('csrfmiddlewaretoken     : %s' % ('present' if token else 'MISSING'))
    print('Cache-Control           : %s' % headers.get('Cache-Control'))
    if not token:
        return 'no csrfmiddlewaretoken in the login form'
    return _post(op, login_url, token, user, password)


def probe_stale_cookie(login_url, user, password):
    """Bogus but *consistent* cookie proves SECRET_KEY is irrelevant."""
    op, _ = _jar('z' * 32)
    token, _ = _render(op, login_url)
    return _post(op, login_url, token, user, password)


def probe_swapped_cookie(login_url, user, password):
    """Reproduce 'CSRF token from POST incorrect' on purpose."""
    op, _ = _jar()
    token, _ = _render(op, login_url)
    op2, _ = _jar('y' * 32)
    return _post(op2, login_url, token, user, password)


def probe_proxy_header(login_url, user, password):
    """SECURE_PROXY_SSL_HEADER makes a local http POST look like https."""
    op, _ = _jar()
    token, _ = _render(op, login_url)
    return _post(op, login_url, token, user, password,
                 extra_headers={'X-Forwarded-Proto': 'https'})


PROBES = {
    'clean': probe_clean,
    'stale-cookie': probe_stale_cookie,
    'swapped-cookie': probe_swapped_cookie,
    'proxy-header': probe_proxy_header,
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--base', default='http://127.0.0.1:8080',
                    help='dev server origin (default: %(default)s)')
    ap.add_argument('--user', default='admin')
    ap.add_argument('--password', default='admin')
    ap.add_argument('--probe', action='append', choices=sorted(PROBES),
                    help='run only these probes (repeatable)')
    args = ap.parse_args(argv)

    login_url = args.base.rstrip('/') + '/admin/login/'
    wanted = args.probe or ['clean', 'stale-cookie', 'swapped-cookie']
    results = []
    for name in wanted:
        print('=== %s ===' % name)
        try:
            detail = PROBES[name](login_url, args.user, args.password)
        except Exception as exc:  # noqa: BLE001 - diagnostic tool
            detail = 'probe crashed: %r' % exc
        print('  %s' % detail)
        results.append((name, detail))
        print()

    clean = dict(results).get('clean', '')
    print('=' * 64)
    if clean.startswith('LOGIN OK'):
        print('VERDICT: server-side CSRF/login is HEALTHY.')
        print('  The 403 you see in the browser is browser state, i.e. the')
        print('  `csrftoken` cookie in that browser does not match the token')
        print('  in the form that was submitted. Fix: load /admin/login/')
        print('  fresh (Ctrl+F5) in ONE tab and submit immediately, or clear')
        print('  the csrftoken + sessionid cookies for this host (or use a')
        print('  brand-new incognito window).')
    elif clean.startswith('rejected'):
        print('VERDICT: CSRF is fine, credentials are wrong.')
    else:
        print('VERDICT: server-side problem — see the clean probe above.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
