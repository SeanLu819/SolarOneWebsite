"""Guard for the HTML edge-cache policy (v1.10.3).

The policy itself lives in ``pages/edge_cache.py`` because Vercel's
``headers.source`` matches the pathname only (excluding the querystring) and
``missing`` has no wildcard — see that module's docstring.

These tests are written against *behaviour* (what header does this request
actually get) rather than against the constants, because the constants are the
thing most likely to be edited carelessly. A pure constant assertion would keep
passing after somebody adds an unsafe path.

Both request-level invariants that the whole design rests on are pinned here as
live re-verification of things measured on production:

* a query string changes the rendered HTML for some views, and
* the language lives in the URL, not in ``Accept-Language``.

If either ever stops being true the safety argument in the module docstring
needs re-doing, and these two tests are what will notice.
"""

import os

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from pages.edge_cache import (
    CACHEABLE_HTML_PREFIXES,
    CDN_CACHE_CONTROL,
    EDGE_S_MAXAGE,
    EDGE_SWR,
    EdgeCacheHeaderMiddleware,
    UNCACHEABLE_EXACT,
    UNCACHEABLE_PREFIXES,
)

HEADER = 'Vercel-CDN-Cache-Control'


class EdgeCachePolicyTests(TestCase):
    """The middleware is off unless explicitly enabled."""

    def test_disabled_by_default(self):
        """Local dev and the test suite must not cache.

        A cached local response would hide code changes during runserver.
        """
        self.assertFalse(getattr(settings, 'EDGE_CACHE_ENABLED', False),
                         'EDGE_CACHE_ENABLED must default to False off Vercel')
        resp = self.client.get('/', HTTP_HOST='localhost')
        self.assertEqual(200, resp.status_code)
        self.assertNotIn(HEADER, resp.headers)


class EdgeCacheWiringTests(TestCase):
    """🔴 The middleware must actually be *installed*, and only on Vercel.

    Every other case in this file drives ``EdgeCacheHeaderMiddleware``
    directly. That is deliberate — it makes the query-string cases
    expressible — but it means all of them would keep passing if the class
    were never added to ``MIDDLEWARE`` at all, i.e. if the feature were
    silently inert in production.

    This is not hypothetical: the first implementation run produced zero
    headers on real requests for exactly this reason. Django builds the
    handler chain when the settings module is imported, so
    ``override_settings(EDGE_CACHE_ENABLED=True)`` flips the flag but cannot
    insert a middleware that ``settings.py`` skipped because ``IS_VERCEL``
    was False locally.

    ``IS_VERCEL`` is read from the ``VERCEL`` env var at import time
    (``settings.py:38``), so the install path is asserted against the real
    settings module rather than by re-implementing the condition.
    """

    def test_middleware_is_installed_on_vercel(self):
        # `IS_VERCEL` is read from the VERCEL env var at import time, so this
        # asserts against the real wiring in settings.py rather than
        # re-implementing the condition here.
        if not settings.IS_VERCEL:
            self.assertNotIn(
                'pages.edge_cache.EdgeCacheHeaderMiddleware',
                settings.MIDDLEWARE,
                '非 Vercel 环境不应挂边缘缓存中间件（本地会缓存住旧代码）')
            return
        self.assertIn('pages.edge_cache.EdgeCacheHeaderMiddleware',
                      settings.MIDDLEWARE)

    def test_middleware_sits_last_so_it_can_veto(self):
        """It must run last, i.e. see the final response.

        Placed earlier it would run before SessionMiddleware/CSRFView had a
        chance to add ``Set-Cookie``, and could cache a response that turns
        out to be per-visitor.
        """
        if 'pages.edge_cache.EdgeCacheHeaderMiddleware' not in settings.MIDDLEWARE:
            self.skipTest('非 Vercel 环境不挂该中间件')
        self.assertEqual(
            'pages.edge_cache.EdgeCacheHeaderMiddleware',
            settings.MIDDLEWARE[-1],
            '边缘缓存中间件必须是最后一项，才能看到最终响应')

    def test_settings_module_wires_the_middleware_under_is_vercel(self):
        """Read settings.py as source and assert the *install* is there.

        A live ``settings.MIDDLEWARE`` check can only ever observe the
        environment the tests happen to run in (here: not Vercel), which is
        exactly the situation where the middleware is absent by design. This
        asserts the branch that production takes.

        The first implementation run shipped with the middleware silently
        inert: every direct-call test passed while real requests carried no
        header at all. So the wiring itself needs a guard.
        """
        import pathlib
        source = (pathlib.Path(str(settings.BASE_DIR)) / 'solarone'
                  / 'settings.py').read_text(encoding='utf-8')
        self.assertIn('pages.edge_cache.EdgeCacheHeaderMiddleware', source,
                      'settings.py 必须在 IS_VERCEL 分支里安装边缘缓存中间件')
        self.assertRegex(
            source,
            r"MIDDLEWARE\.append\(\s*'pages\.edge_cache\.EdgeCacheHeaderMiddleware'",
            '安装语句应写作 MIDDLEWARE.append(...)')


class EdgeCacheOnVercelSubprocessTests(SimpleTestCase):
    """End-to-end proof under the real production settings, in a fresh process.

    ``IS_VERCEL`` is read from the ``VERCEL`` env var while the settings
    module is imported, and Django builds the middleware chain once at that
    moment. No amount of ``override_settings`` in-process can reproduce the
    production chain — the first implementation run therefore looked green
    while every real request carried no cache header at all.

    Spawning ``VERCEL=1 python -c …`` is the only way to import the settings
    module the way production imports it. A subprocess also keeps the
    IS_VERCEL-dependent values (DEBUG, storage backends) from leaking into
    the rest of the suite.
    """

    #: Runs inside the child process, where VERCEL=1 is already in os.environ.
    #:
    #: `secure=True` is required: IS_VERCEL turns on SECURE_SSL_REDIRECT, so a
    #: plain http test request gets 301'd to https://localhost/ and never
    #: reaches a view. (Same mechanism as the live apex->www 308.)
    CHILD = """
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
django.setup()
from django.conf import settings
from django.test import Client
from django.test.utils import setup_test_environment
setup_test_environment()
assert settings.IS_VERCEL, 'VERCEL=1 未生效'
assert 'pages.edge_cache.EdgeCacheHeaderMiddleware' in settings.MIDDLEWARE, \\
    '中间件未挂载'
c = Client()
H = 'Vercel-CDN-Cache-Control'
HOST = 'www.solaronelighting.com'
print('MIDDLEWARE_LAST=%s' % settings.MIDDLEWARE[-1])
for path in ('/', '/news/', '/de/', '/products/rt410-series/'):
    r = c.get(path, HTTP_HOST=HOST, secure=True)
    print('CACHE %s %s %s' % (path, r.status_code, r.headers.get(H, 'NONE')))
for path in ('/contact/', '/admin/', '/news/?category=Case+Studies',
             '/static/css/base.css', '/news/feed.xml'):
    r = c.get(path, HTTP_HOST=HOST, secure=True)
    print('NOCACHE %s %s %s' % (path, r.status_code, r.headers.get(H, 'NONE')))
"""

    def _run_child(self):
        import subprocess
        import sys
        env = dict(os.environ)
        env['VERCEL'] = '1'
        # Local dev server must not be running: it holds the sqlite lock and
        # the middleware chain differs under DEBUG.
        env.pop('DEBUG', None)
        return subprocess.run(
            [sys.executable, '-c', self.CHILD],
            capture_output=True, text=True, env=env,
            cwd=str(settings.BASE_DIR), timeout=180,
        )

    def test_middleware_installed_and_headers_correct_under_vercel(self):
        proc = self._run_child()
        self.assertEqual(
            0, proc.returncode,
            f'子进程失败\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}')

        lines = proc.stdout.strip().splitlines()
        self.assertIn('MIDDLEWARE_LAST=pages.edge_cache.EdgeCacheHeaderMiddleware',
                      lines,
                      '生产环境下中间件必须是最后一项，才能看到最终响应')

        for line in lines:
            if line.startswith('CACHE '):
                _, path, status, header = line.split(' ', 3)
                self.assertEqual('200', status, f'{path} 应返回 200')
                self.assertNotEqual('NONE', header,
                                    f'{path} 在生产配置下必须带 {HEADER}')
            elif line.startswith('NOCACHE '):
                _, path, _status, header = line.split(' ', 3)
                self.assertEqual(
                    'NONE', header,
                    f'{path} 绝不能带 {HEADER}'
                    '（/contact/ 有 CSRF token、query 有多版本、'
                    '/static/ 归vercel.json 管）')

        # Nothing may be silently skipped: prove the loop actually ran.
        self.assertGreaterEqual(
            sum(1 for x in lines if x.startswith(('CACHE ', 'NOCACHE '))), 9,
            f'子进程未跑完预期的探测项：\n{proc.stdout}')


@override_settings(EDGE_CACHE_ENABLED=True)
class EdgeCacheHeaderTests(TestCase):
    """Each case drives the middleware directly with a fake request/response.

    Driving the middleware rather than making real HTTP requests keeps the
    query-string cases expressible: a real `/news/?category=…` request goes
    through LocaleMiddleware and template rendering, which obscures what is
    actually being asserted.
    """

    @staticmethod
    def _request(path='/', method='GET', query=''):
        class _Req:
            pass
        req = _Req()
        req.method = method
        req.path = path
        req.META = {'QUERY_STRING': query}
        return req

    @staticmethod
    def _response(status=200, set_cookie=False):
        from django.http import HttpResponse
        resp = HttpResponse('x', status=status)
        if set_cookie:
            resp['Set-Cookie'] = 'sessionid=abc; Path=/'
        return resp

    def _run(self, path='/', method='GET', query='', status=200,
             set_cookie=False):
        mw = EdgeCacheHeaderMiddleware(
            lambda r: self._response(status=status, set_cookie=set_cookie))
        resp = mw(self._request(path=path, method=method, query=query))
        return resp

    # ---- the positive case ------------------------------------------------
    def test_public_html_pages_are_cacheable(self):
        for path in ('/', '/news/', '/products/', '/projects/',
                     '/about/', '/privacy/', '/terms/',
                     '/products/rt410-series/', '/projects/yuanshen-sports-centre-stadium/',
                     '/de/', '/ar/projects/'):
            with self.subTest(path=path):
                self.assertIn(HEADER, self._run(path=path).headers,
                              f'{path} 应可边缘缓存')

    def test_header_carries_both_directives(self):
        """s-maxage is the edge window; SWR is consumed by Vercel's proxy.

        Losing s-maxage silently turns the whole feature off while still
        looking configured, so assert on both parts.
        """
        value = self._run().headers[HEADER]
        self.assertIn(f's-maxage={EDGE_S_MAXAGE}', value)
        self.assertIn(f'stale-while-revalidate={EDGE_SWR}', value)
        self.assertIn('public', value)

    def test_uses_the_cdn_only_header_not_plain_cache_control(self):
        """🔴 Plain `Cache-Control: s-maxage` would also make the *browser*
        hold the page for max-age seconds, which delays a deploy and risks
        content-flash. The edge-only header is what keeps the browser
        revalidating."""
        resp = self._run()
        self.assertNotIn('s-maxage', resp.headers.get('Cache-Control', ''),
                         '浏览器侧 Cache-Control 不得含 s-maxage')

    # ---- the exclusions that make it safe ---------------------------------
    def test_contact_page_is_never_cached(self):
        """🔴 /contact/ renders {% csrf_token %}. A cached copy hands the next
        visitor a token bound to someone else's cookie → their POST 403s."""
        self.assertIn('/contact/', UNCACHEABLE_PREFIXES)
        self.assertNotIn(HEADER, self._run(path='/contact/').headers)

    def test_admin_and_diag_are_never_cached(self):
        for path in ('/admin/', '/admin/products/product/1/change/',
                     '/__diag__/'):
            with self.subTest(path=path):
                self.assertNotIn(HEADER, self._run(path=path).headers)

    def test_any_query_string_disables_caching(self):
        """🔴 The whole reason this policy cannot live in vercel.json.

        `/news/?category=…` renders a different page per value (verified by
        md5), and Vercel's headers.source cannot see the querystring — so a
        cached `/news/?category=X` would be handed to plain `/news/`.
        """
        for query in ('category=Case+Studies', 'page=2', 'q=led'):
            with self.subTest(query=query):
                self.assertNotIn(
                    HEADER,
                    self._run(path='/news/', query=query).headers,
                    '带 query 的请求不得被缓存')

    def test_post_is_never_cached(self):
        self.assertNotIn(
            HEADER,
            self._run(path='/contact/', method='POST').headers)

    def test_set_cookie_response_is_not_cached(self):
        """A response that starts a session is per-visitor by definition."""
        self.assertNotIn(
            HEADER,
            self._run(path='/', set_cookie=True).headers)

    def test_error_and_redirect_statuses_are_not_cached(self):
        """🔴 Caching a 301 would freeze the apex->www target into the edge
        forever; caching a 404 would pin a page that has since been created."""
        for status in (301, 302, 404, 500):
            with self.subTest(status=status):
                self.assertNotIn(
                    HEADER,
                    self._run(path='/', status=status).headers)

    def test_static_is_left_to_vercel_json(self):
        """/static/ already carries a one-year immutable rule from
        vercel.json; matching it here would replace that header."""
        self.assertNotIn(
            HEADER, self._run(path='/static/css/base.css').headers)

    # ---- path lists are allowlists, not suggestions -----------------------
    def test_rss_feed_is_not_cached(self):
        """🔴 `/news/feed.xml` startswith the cacheable `/news/` prefix, so a
        startswith-based exclusion list cannot catch it.

        Found by the subprocess guard on the first implementation: the feed was
        being cached, which would hold a newly published article back from
        every RSS subscriber for up to ``EDGE_S_MAXAGE`` seconds. On a feed,
        freshness is the entire product.
        """
        self.assertIn('/news/feed.xml', UNCACHEABLE_EXACT,
                      'feed 必须走精确匹配排除 —— 它 startswith /news/')
        self.assertNotIn(
            HEADER, self._run(path='/news/feed.xml').headers,
            'RSS feed 不得被边缘缓存')

    def test_uncacheable_exact_paths_are_really_under_a_cacheable_prefix(self):
        """This is *why* the two lists exist separately.

        If an entry in ``UNCACHEABLE_EXACT`` no longer sits under a cacheable
        prefix, it belongs in ``UNCACHEABLE_PREFIXES`` (or nowhere) — keeping
        it in the exact list is harmless but misleading, and the docstring
        claiming "startswith cannot express these" would have become false.
        """
        for path in UNCACHEABLE_EXACT:
            with self.subTest(path=path):
                self.assertTrue(
                    any(path.startswith(p) for p in CACHEABLE_HTML_PREFIXES),
                    f'{path} 已不在任何可缓存前缀下，应移出 UNCACHEABLE_EXACT')

    def test_uncacheable_prefixes_cannot_also_be_cacheable(self):
        """A path in both lists is a contradiction that would silently pick
        one winner depending on prefix ordering."""
        overlap = [p for p in CACHEABLE_HTML_PREFIXES
                   if p in UNCACHEABLE_PREFIXES or any(
                       p.startswith(u) for u in UNCACHEABLE_PREFIXES)]
        self.assertEqual([], overlap,
                         f'同一路径同时出现在两个列表里：{overlap}')
        exact_overlap = [p for p in UNCACHEABLE_EXACT
                         if p in CACHEABLE_HTML_PREFIXES]
        self.assertEqual([], exact_overlap,
                         f'精确排除项不该同时是可缓存前缀：{exact_overlap}')

    def test_cacheable_list_is_not_a_bare_root_catch_all(self):
        """`/` is a prefix, so `/<anything>` technically startswith it.

        Keep the intent explicit: the list must name real page prefixes, and
        must not have been replaced by a single catch-all like `/(.*)`-style
        entries beyond what is deliberate. This test documents that `/` is the
        only prefix that is also a prefix of arbitrary paths.
        """
        self.assertIn('/', CACHEABLE_HTML_PREFIXES)
        for prefix in CACHEABLE_HTML_PREFIXES:
            with self.subTest(prefix=prefix):
                self.assertTrue(
                    prefix == '/' or prefix.endswith('/'),
                    '非根前缀应以 / 结尾，避免 /product 误匹配 /products')

    # ---- the two assumptions the design rests on --------------------------
    def test_language_comes_from_the_url_not_accept_language(self):
        """Re-verify on production terms: `/` returned `<html lang="en">` for
        fr/de/ar `Accept-Language` headers alike. If a future change made the
        response depend on that header, edge caching would serve one language
        to another language's visitors.

        Two things to pin: every prefixed URL resolves (the language really is
        part of the path), and the same URL renders the same ``<html lang>``
        whatever ``Accept-Language`` says.
        """
        from django.urls import reverse

        self.assertEqual(reverse('home'), '/')
        # Do NOT call resolve('/fr/') here: i18n_patterns prefix matching goes
        # through LocaleMiddleware, not the currently activated language, so
        # resolve() raises Resolver404 for every prefix regardless of
        # translation.activate(). Actually request the pages instead — that is
        # the behaviour that matters and cannot be faked.
        for lang in ('fr', 'es', 'de', 'ru', 'ar'):
            with self.subTest(lang=lang):
                resp = self.client.get(f'/{lang}/', HTTP_HOST='localhost')
                self.assertEqual(200, resp.status_code)
                body = resp.content.decode('utf-8')
                self.assertIn(
                    f'<html lang="{lang}"', body,
                    f'/{lang}/ 必须渲染成 {lang} —— 语言在**路径**里，'
                    '这正是边缘缓存不会串语种的原因')

        for accept_language in ('fr-FR,fr;q=0.9', 'de-DE,de;q=0.9',
                                'ar-SA,ar;q=0.9'):
            with self.subTest(accept_language=accept_language):
                resp = self.client.get('/', HTTP_HOST='localhost',
                                       headers={'accept-language': accept_language})
                self.assertEqual(200, resp.status_code)
                body = resp.content.decode('utf-8')
                self.assertIn(
                    '<html lang="en"', body,
                    f'Accept-Language={accept_language} 不应改变英文首页的语言'
                    ' —— 若它改变了，边缘缓存会把一种语言发给另一种语言的访客')

    def test_query_driven_news_view_really_varies(self):
        """🔴 The exclusion of query strings is only necessary because some
        view actually varies. Pin that so the rule cannot be deleted as
        "unnecessary" without a red test.

        Runs against the real seed with ``IS_VERCEL`` forced on so the list
        page renders from committed data, not the (empty) test database.
        """
        from django.test import override_settings as _ov
        with _ov(IS_VERCEL=True):
            plain = self.client.get('/news/', HTTP_HOST='localhost')
            self.assertEqual(200, plain.status_code)
            self.assertNotIn(HEADER, plain.headers,
                             '本地/测试不应带边缘缓存头')

        html_plain = plain.content.decode('utf-8')
        filtered = self.client.get('/news/?category=Company+News',
                                   HTTP_HOST='localhost')
        html_filtered = filtered.content.decode('utf-8')
        self.assertNotEqual(
            html_plain, html_filtered,
            '若 /news/?category= 与 /news/ 内容已相同，则 query 排除规则应重新评估')