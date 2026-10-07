"""Guards for the sitemap ``<lastmod>`` policy (v1.10.24, supersedes v1.10.16).

History
-------
v1.10.16 replaced a hardcoded ``2018-10-20`` with a build stamp written by
``build.sh`` into ``pages/build_meta.py``, because Vercel's serverless checkout
rewrites file mtimes and ``os.path.getmtime`` collapsed every URL to a stale
2018 date. That fixed the 2018 bug but introduced a subtler one: **all 60 URLs
carried the same date**, which reads as "every page changed on every deploy".
Google discounts a ``lastmod`` it learns to distrust.

v1.10.24 measured what real data exists. On the seed snapshot:

* ``news`` carries ``published_at`` — real, per-article, already rendered on
  the page. 3 articles.
* ``products`` and ``projects`` carry **no time field at all** — no
  ``updated_at``, no ``created_at``, no ``published_at``. 24 + 22 pages.
* The 11 collection/static pages have no per-page content signal either.

So 57 of 60 URLs have no honest date available. ``<lastmod>`` is optional in the
sitemap schema, so the policy is now: **emit it only where a real date exists.**
A new article then advertises a genuine recent date; everything else falls back
to the crawler's own crawl-frequency heuristics instead of a fiction.

The v1.10.16 helper ``_site_last_modified()`` is retained but no longer called
by the sitemap — ``test_the_helper_is_no_longer_wired_into_the_sitemap``
pins that, so nobody reads this file and assumes otherwise.

These guards assert the *values*, because a missing or wrong ``<lastmod>`` is
perfectly valid XML and no syntax check can see it.
"""
import re
import sys
import types

from django.test import TestCase

from pages.views.views_other import _news_lastmod, _site_last_modified

STAMP_MODULE = 'pages.build_meta'
DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


class _StampMixin:
    """Install / remove a fake ``pages.build_meta`` module safely."""

    def install_stamp(self, value):
        mod = types.ModuleType(STAMP_MODULE)
        mod.SITE_LAST_MODIFIED = value
        self._saved = sys.modules.get(STAMP_MODULE, KeyError)
        sys.modules[STAMP_MODULE] = mod

    def restore_stamp(self):
        saved = getattr(self, '_saved', KeyError)
        if saved is KeyError:
            sys.modules.pop(STAMP_MODULE, None)
        else:
            sys.modules[STAMP_MODULE] = saved


class NewsLastmodHelperTests(TestCase):
    """Unit level: the per-article date helper."""

    class _Obj:
        """Stand-in for a model instance (the DB path's shape)."""

        def __init__(self, published_at):
            self.published_at = published_at

    def test_reads_a_real_datetime(self):
        from datetime import datetime, timezone
        value = datetime(2026, 9, 13, 16, 0, tzinfo=timezone.utc)
        self.assertEqual(
            '2026-09-13', _news_lastmod(self._Obj(value)))

    def test_reads_a_plain_dict(self):
        """``get_news_detail`` returns a **plain dict**, so ``getattr`` alone
        silently yields nothing. That was a real bug: the first run of this work
        rendered zero ``<lastmod>`` elements because the helper used
        ``getattr`` on a dict."""
        self.assertEqual(
            '2026-09-13', _news_lastmod({'published_at': '2026-09-13T16:00:00+00:00'}))

    def test_drops_the_time_part(self):
        """``<lastmod>`` accepts a full ISO timestamp, but a bare date is what
        the rest of this sitemap emits. Truncating keeps the values comparable
        across builds and stops a tz-offset from leaking into the XML.

        Both input shapes matter. ``get_news_detail`` hands back a real
        ``datetime`` on the seed path (the string is parsed in the loader), so
        the ``isinstance`` branch is the one that actually runs in production —
        a guard that only fed it strings would never exercise it, and an
        ``.isoformat()`` regression there would ship a ``2026-09-13T16:00:00
        +00:00`` into the sitemap unnoticed.
        """
        from datetime import datetime, timezone
        self.assertEqual(
            '2026-09-13',
            _news_lastmod({'published_at': '2026-09-13T16:00:00+00:00'}),
            'ISO string input must be truncated to a date')
        self.assertEqual(
            '2026-08-31',
            _news_lastmod({'published_at': '2026-08-31T00:00:00+00:00'}))
        self.assertEqual(
            '2026-09-13',
            _news_lastmod(self._Obj(
                datetime(2026, 9, 13, 16, 0, tzinfo=timezone.utc))),
            'datetime input must be truncated to a date')
        self.assertEqual(
            '2026-08-31',
            _news_lastmod(self._Obj(datetime(2026, 8, 31, 0, 0))),
            'naive datetime input must be truncated too')

    def test_missing_value_yields_nothing_rather_than_a_guess(self):
        """No date is not the same as "today". Emitting the build stamp for an
        article with no publication date would reintroduce exactly the
        dishonesty v1.10.24 removed."""
        self.assertEqual('', _news_lastmod({}))
        self.assertEqual('', _news_lastmod({'published_at': ''}))
        self.assertEqual('', _news_lastmod({'published_at': None}))
        self.assertEqual('', _news_lastmod(self._Obj(None)))

    def test_unparseable_value_yields_nothing(self):
        """A malformed date must not reach the XML — ``<lastmod>2026-13-45</lastmod>``
        is invalid and the schema has no "unknown" value."""
        self.assertEqual('', _news_lastmod({'published_at': 'not-a-date'}))
        self.assertEqual('', _news_lastmod({'published_at': '2026-13-45'}))


class SitemapLastmodRenderingTests(_StampMixin, TestCase):
    """End-to-end: what the rendered XML actually carries."""

    def _sitemap(self):
        resp = self.client.get('/sitemap.xml', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode('utf-8')

    def _pairs(self, body):
        """``[(loc, lastmod_or_None), ...]`` for every ``<url>`` block."""
        pairs = []
        for block in re.findall(r'<url>(.*?)</url>', body, re.S):
            loc = re.search(r'<loc>([^<]+)</loc>', block)
            mod = re.search(r'<lastmod>([^<]+)</lastmod>', block)
            self.assertIsNotNone(loc, f'sitemap <url> block without <loc>: {block[:120]}')
            pairs.append((loc.group(1), mod.group(1) if mod else None))
        return pairs

    def test_the_sitemap_is_still_complete(self):
        """The policy change must not have dropped any URL. Every product,
        project and news slug still has to be listed — only its ``<lastmod>``
        is optional now."""
        body = self._sitemap()
        locs = re.findall(r'<loc>([^<]+)</loc>', body)
        self.assertTrue(locs, 'sitemap rendered no <loc> at all')
        self.assertEqual(60, len(locs),
                         f'sitemap URL count changed: {len(locs)} (expected 60)')
        for expected in ('/', '/products/', '/stadium-lighting/', '/news/'):
            self.assertIn(
                f'https://www.solaronelighting.com{expected}', locs,
                f'sitemap lost the collection page {expected}')

    def test_only_news_urls_carry_a_lastmod(self):
        """The whole point of the change.

        A ``<lastmod>`` on a product or project URL is the fabrication we are
        removing, so this asserts the *absence* on those paths as well as the
        presence on news.
        """
        from pages.views.utils import _load_seed

        pairs = self._pairs(self._sitemap())
        seed = _load_seed()

        news_slugs = {
            a['slug'] for a in seed['news']
            if a.get('is_published', True)
        }
        product_slugs = {p['slug'] for p in seed['products'] if p.get('slug')}
        project_slugs = {p['slug'] for p in seed['projects'] if p.get('slug')}

        for loc, lastmod in pairs:
            path = loc.replace('https://www.solaronelighting.com', '')
            if any(path == f'/news/{s}/' for s in news_slugs):
                self.assertIsNotNone(
                    lastmod, f'news URL 缺 lastmod: {path}')
                self.assertRegex(lastmod, DATE_RE)
            elif (any(path == f'/products/{s}/' for s in product_slugs)
                  or any(path == f'/projects/{s}/' for s in project_slugs)):
                self.assertIsNone(
                    lastmod,
                    f'{path} 输出了 lastmod={lastmod!r}，但 seed 里该对象没有任何'
                    '时间字段可推导真实修改日期')

    def test_news_lastmod_equals_the_article_published_date(self):
        """The emitted date must be the article's own, taken from the seed —
        not a constant and not the build stamp.

        Derived from the seed rather than hardcoded, so a new article published
        tomorrow is covered without editing this test. The anti-fabrication
        assertions live in ``test_only_news_urls_carry_a_lastmod``; this one
        checks the mapping is correct.
        """
        from pages.views.utils import _load_seed

        expected = {}
        for article in _load_seed()['news']:
            if not article.get('is_published', True):
                continue
            expected[article['slug']] = str(
                article['published_at'])[:10]

        pairs = dict(self._pairs(self._sitemap()))
        seen = 0
        for slug, want in expected.items():
            key = f'https://www.solaronelighting.com/news/{slug}/'
            if key in pairs:
                self.assertEqual(
                    want, pairs[key],
                    f'news/{slug}/ 的 lastmod 与 seed published_at 不一致')
                seen += 1
        self.assertTrue(
            seen, 'no news URL found in the sitemap to verify')

    def test_the_three_news_dates_are_not_all_identical(self):
        """A regression guard for the original bug in a new shape.

        The three publication dates are genuinely different (2026-08-31,
        2026-09-13, 2026-09-28). If a future change ever collapses them back
        to one value, the policy is broken again even though every news URL
        still has *a* lastmod.

        "Different" is not enough on its own: a mapping that shuffles the three
        dates onto the wrong articles would also pass. So this pairs each
        article with the date the seed says it was published, which is the
        assertion that actually pins the behaviour.
        """
        from pages.views.utils import _load_seed

        expected = {
            a['slug']: str(a['published_at'])[:10]
            for a in _load_seed()['news']
            if a.get('is_published', True)
        }
        self.assertGreater(
            len(set(expected.values())), 1,
            f'the seed no longer has distinct publication dates, so this '
            f'test cannot detect a collapse: {expected}')

        paired = {}
        for block in re.findall(r'<url>(.*?)</url>', self._sitemap(), re.S):
            loc = re.search(r'<loc>([^<]+)</loc>', block)
            mod = re.search(r'<lastmod>([^<]+)</lastmod>', block)
            if loc and '/news/' in loc.group(1) and mod:
                paired[loc.group(1)] = mod.group(1)
        self.assertTrue(paired, 'no news <lastmod> found at all')
        self.assertEqual(
            len(paired), len(set(paired.values())),
            f'all news lastmod collapsed to one value: {paired}')

        for slug, want in expected.items():
            key = f'https://www.solaronelighting.com/news/{slug}/'
            if key in paired:
                with self.subTest(slug=slug):
                    self.assertEqual(
                        want, paired[key],
                        f'news/{slug}/ 报的是别的文章的日期，或被换成了统一值')

    def test_the_helper_is_no_longer_wired_into_the_sitemap(self):
        """``_site_last_modified`` (the v1.10.16 build stamp) is retained but
        unused. This pins that, so a reader of the module does not assume the
        sitemap still stamps a deploy date on every URL — and so a future
        re-wiring has to update this test deliberately.

        The build stamp itself is still injected with a recognisable value; if
        any URL reports it, the policy is violated.
        """
        self.install_stamp('1999-01-01')
        try:
            body = self._sitemap()
        finally:
            self.restore_stamp()
        self.assertNotIn(
            '1999-01-01', body,
            'the v1.10.16 build stamp leaked back into the sitemap — every '
            'URL must either carry a real per-article date or no date at all')

    def test_no_url_carries_the_stale_2018_date(self):
        """Regression guard: 2018-10-20 was the hardcoded value shipped to prod."""
        for _loc, lastmod in self._pairs(self._sitemap()):
            if lastmod is None:
                continue
            self.assertNotEqual(lastmod, '2018-10-20')
            self.assertRegex(lastmod, DATE_RE)

    def test_every_emitted_lastmod_is_a_valid_date_not_a_datetime(self):
        """A full ``2026-09-13T16:00:00+00:00`` is legal in the schema but this
        sitemap emits bare dates; pinning the format keeps the values
        diffable and comparable across builds."""
        for loc, lastmod in self._pairs(self._sitemap()):
            if lastmod is None:
                continue
            with self.subTest(loc=loc):
                self.assertNotIn('T', lastmod,
                                 f'{loc} 的 lastmod 含时间部分：{lastmod!r}')
                self.assertNotIn('+', lastmod,
                                 f'{loc} 的 lastmod 含时区偏移：{lastmod!r}')


class SiteLastModifiedHelperTests(_StampMixin, TestCase):
    """The v1.10.16 helper still works; it just has no caller left.

    Kept because it is the thing that fixed the 2018 bug, and if a future batch
    finds a legitimate use for a site-wide timestamp (an IndexNow payload, a
    cache header) it should not have to be rewritten.
    """

    def test_build_stamp_wins_over_seed_mtime(self):
        self.install_stamp('2026-10-06')
        try:
            self.assertEqual(_site_last_modified(), '2026-10-06')
        finally:
            self.restore_stamp()

    def test_falls_back_to_seed_mtime_without_stamp(self):
        saved = sys.modules.get(STAMP_MODULE, KeyError)
        sys.modules[STAMP_MODULE] = None
        try:
            value = _site_last_modified()
        finally:
            if saved is KeyError:
                sys.modules.pop(STAMP_MODULE, None)
            else:
                sys.modules[STAMP_MODULE] = saved
        self.assertTrue(value, 'fallback must never be empty')
        self.assertRegex(value, DATE_RE)
