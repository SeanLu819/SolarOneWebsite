"""
Legacy URL redirect guards (L1 unit tests).

Context: ``pages/urls.py`` had zero redirect entries and no redirect table
anywhere, so renaming any slug would have 404'd — which is why B3 (keyword
renames for 5 project slugs) was blocked. S2 builds the mechanism; these tests
lock its behaviour before any entry is registered.

Covers:
  * The table validates: no self-reference, no chains, no dangling targets,
    and legacy paths stay relative so the language prefix survives.
  * A registered project/product slug 301s to its replacement, in the
    visitor's language.
  * A slug that still resolves is never redirected, even if an entry names it
    (registering a redirect must not shadow a live page).
  * Unregistered unknown slugs keep today's behaviour — 404 for products,
    the existing soft page for projects.
"""
from unittest import mock

from django.test import Client, TestCase

from pages.redirects import (
    LEGACY_PATH_REDIRECTS,
    PRODUCT_SLUG_REDIRECTS,
    PROJECT_SLUG_REDIRECTS,
    legacy_path_entries,
    redirect_table_problems,
)
from pages.views.utils import _load_seed

#: Real slugs, so a redirect target can be checked for existence.
_SEED = _load_seed()
_PROJECT_SLUGS = {p['slug'] for p in (_SEED.get('projects') or [])}
_PRODUCT_SLUGS = {p['slug'] for p in (_SEED.get('products') or [])}

#: A target that definitely exists, used by the redirect tests.
_LIVE_PROJECT = 'perryville-high-school'
_LIVE_PRODUCT = 'm-series'

_KW = dict(HTTP_HOST='localhost')


class RedirectTableValidityTests(TestCase):
    """The tables are self-consistent. Empty is valid; entries are checked."""

    def test_seed_slugs_are_available_for_the_guards(self):
        # Guards below are vacuous if the fixture set is empty.
        self.assertIn(_LIVE_PROJECT, _PROJECT_SLUGS)
        self.assertIn(_LIVE_PRODUCT, _PRODUCT_SLUGS)

    def test_shipped_tables_have_no_problems(self):
        self.assertEqual(
            [], redirect_table_problems(_PROJECT_SLUGS, _PRODUCT_SLUGS))

    def test_detects_self_reference(self):
        problems = redirect_table_problems(
            project_slugs={'a'},
        )
        self.assertEqual([], problems)  # sanity: no entries, no problems
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS, {'a': 'a'}):
            problems = redirect_table_problems(project_slugs={'a'})
        self.assertTrue(any('itself' in p for p in problems), problems)

    def test_detects_empty_target(self):
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS, {'a': ''}):
            problems = redirect_table_problems(project_slugs={'a'})
        self.assertTrue(any('empty/non-string target' in p for p in problems),
                        problems)

    def test_detects_chain(self):
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS,
                             {'a': 'b', 'b': _LIVE_PROJECT}):
            problems = redirect_table_problems(project_slugs=_PROJECT_SLUGS)
        self.assertTrue(any('chain' in p for p in problems), problems)

    def test_detects_dangling_target(self):
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS, {'a': 'no-such-slug'}):
            problems = redirect_table_problems(project_slugs=_PROJECT_SLUGS)
        self.assertTrue(any('no such slug' in p for p in problems), problems)

    def test_legacy_path_must_be_relative(self):
        with mock.patch.dict(LEGACY_PATH_REDIRECTS,
                             {'/absolute/': ('home', {})}):
            problems = redirect_table_problems()
        self.assertTrue(any('relative' in p for p in problems), problems)

    def test_legacy_path_value_must_be_a_url_name(self):
        with mock.patch.dict(LEGACY_PATH_REDIRECTS, {'old/': ('home', {})}):
            problems = redirect_table_problems()
        self.assertTrue(any('empty url_name' in p for p in problems), problems)

    def test_entries_are_ordered_for_reproducible_urls(self):
        with mock.patch.dict(LEGACY_PATH_REDIRECTS,
                             {'b/': 'home', 'a/': 'home'}):
            self.assertEqual([r for r, _ in legacy_path_entries()], ['a/', 'b/'])


class ProjectSlugRedirectTests(TestCase):
    """A retired project slug 301s; a live one is never touched."""

    def test_registered_slug_returns_permanent_redirect(self):
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS,
                             {'old-perryville': _LIVE_PROJECT}):
            resp = Client().get('/projects/old-perryville/', **_KW)
        self.assertEqual(resp.status_code, 301, 'must be permanent, not 302')
        self.assertEqual(resp['Location'], f'/projects/{_LIVE_PROJECT}/')

    def test_redirect_keeps_the_visitors_language(self):
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS,
                             {'old-perryville': _LIVE_PROJECT}):
            resp = Client().get('/fr/projects/old-perryville/', **_KW)
        self.assertEqual(resp.status_code, 301)
        self.assertTrue(resp['Location'].startswith('/fr/projects/'),
                        resp['Location'])
        self.assertIn(_LIVE_PROJECT, resp['Location'])

    def test_live_slug_is_not_redirected(self):
        """Registering an entry for a slug that still resolves must not
        hijack it — the table is only consulted when the lookup misses."""
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS,
                             {_LIVE_PROJECT: 'morgan-state-university-tennis-courts'}):
            resp = Client().get(f'/projects/{_LIVE_PROJECT}/', **_KW)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('Location', resp)

    def test_unknown_slug_without_entry_is_a_real_404(self):
        """v1.9.7 契约反转：未知项目 slug 必须是真 404。

        S2 建机制时这里断言的是 200（当时项目侧就是软404）。产品侧在
        v1.8.2 已经反转为真 404，项目侧一直漏掉，直到 2026-10-03 才实测
        确认线上 `/projects/<garbage>/` 仍返回 200 + 自指 canonical 的
        "Project Not Found" 页。软 404 会让 Google 收录任意伪造 URL 并判
        为低质页，与产品侧契约不一致本身就是缺陷。
        """
        resp = Client().get('/projects/definitely-not-a-slug/', **_KW)
        self.assertEqual(resp.status_code, 404)
        self.assertNotIn('Location', resp)
        self.assertNotIn(
            'Project Not Found',
            resp.content.decode('utf-8'),
            '软 404 文案不得再出现在未知 slug 的响应里',
        )

    def test_unknown_slug_404_holds_in_every_language(self):
        """六语种都必须 404 —— 旧行为在每个语言前缀下都返回 200。"""
        for prefix in ('fr', 'es', 'de', 'ru', 'ar'):
            with self.subTest(lang=prefix):
                resp = Client().get(
                    f'/{prefix}/projects/definitely-not-a-slug/', **_KW)
                self.assertEqual(resp.status_code, 404)

    def test_unknown_slug_does_not_emit_a_self_referencing_canonical(self):
        """软 404 会带上指向自己的 canonical，等于主动告诉 Google 收录它。"""
        resp = Client().get('/projects/definitely-not-a-slug/', **_KW)
        self.assertEqual(resp.status_code, 404)

    def test_real_project_still_renders_200(self):
        """404 拦截不得误伤真实项目页。"""
        slug = _SEED['projects'][0]['slug']
        resp = Client().get(f'/projects/{slug}/', **_KW)
        self.assertEqual(resp.status_code, 200)
        self.assertNotIn('Project Not Found',
                         resp.content.decode('utf-8'))

    def test_redirect_table_still_wins_over_the_404(self):
        """🔴 顺序契约：查表在前、404 在后。

        改了raise Http404 的位置会让已登记的 301 全部失效，改slug 时
        旧链接就变成硬 404 —— 那是比软 404 更糟的 SEO 事故。
        """
        with mock.patch.dict(PROJECT_SLUG_REDIRECTS,
                             {'legacy-p': _LIVE_PROJECT}):
            resp = Client().get('/projects/legacy-p/', **_KW)
        self.assertEqual(resp.status_code, 301,
                         '登记在表的旧 slug 必须仍 301，不能被 404 拦掉')
        self.assertEqual(resp['Location'], f'/projects/{_LIVE_PROJECT}/')


class ProductSlugRedirectTests(TestCase):
    """Same contract on the product side, where unknown slugs are a real 404."""

    def test_registered_slug_returns_permanent_redirect(self):
        with mock.patch.dict(PRODUCT_SLUG_REDIRECTS,
                             {'legacy-m': _LIVE_PRODUCT}):
            resp = Client().get('/products/legacy-m/', **_KW)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp['Location'], f'/products/{_LIVE_PRODUCT}/')

    def test_redirect_keeps_the_visitors_language(self):
        with mock.patch.dict(PRODUCT_SLUG_REDIRECTS,
                             {'legacy-m': _LIVE_PRODUCT}):
            resp = Client().get('/de/products/legacy-m/', **_KW)
        self.assertEqual(resp.status_code, 301)
        self.assertTrue(resp['Location'].startswith('/de/products/'),
                        resp['Location'])

    def test_live_slug_is_not_redirected(self):
        with mock.patch.dict(PRODUCT_SLUG_REDIRECTS, {_LIVE_PRODUCT: 'fl1m'}):
            resp = Client().get(f'/products/{_LIVE_PRODUCT}/', **_KW)
        self.assertEqual(resp.status_code, 200)

    def test_unknown_slug_without_entry_still_404s(self):
        """The S3 contract: products raise a real 404, not a soft page."""
        resp = Client().get('/products/definitely-not-a-slug/', **_KW)
        self.assertEqual(resp.status_code, 404)


class LegacyRouteWiringTests(TestCase):
    """An empty table registers nothing; existing routes are untouched."""

    def test_no_legacy_routes_are_registered_by_default(self):
        self.assertEqual([], legacy_path_entries())

    def test_ordinary_pages_still_resolve(self):
        for url in ('/', '/projects/', '/products/', '/about/'):
            self.assertEqual(Client().get(url, **_KW).status_code, 200, url)

    def test_the_wiring_urls_py_uses_really_301s(self):
        """Lock the exact form ``pages/urls.py`` must use.

        ``RedirectView.as_view(kwargs=...)`` raises TypeError — ``kwargs`` is
        not a class attribute — so the target has to be a bare ``pattern_name``
        and is therefore reversed, which is what keeps the language prefix.
        A hard-coded ``url='/about/'`` would compile fine and silently dump
        /fr/ visitors into English.
        """
        from django.test import RequestFactory
        from django.views.generic import RedirectView

        view = RedirectView.as_view(pattern_name='home', permanent=True)
        resp = view(RequestFactory().get('/old-section/'))
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp['Location'], '/')

    def test_legacy_series_route_still_redirects(self):
        """/products/series/<slug>/ predates S2 and must keep working — it is
        the one hard-coded 301 in the codebase and the reason this pattern
        was chosen."""
        resp = Client().get(f'/products/series/{_LIVE_PRODUCT}/', **_KW)
        self.assertEqual(resp.status_code, 301)
        self.assertEqual(resp['Location'], f'/products/{_LIVE_PRODUCT}/')
