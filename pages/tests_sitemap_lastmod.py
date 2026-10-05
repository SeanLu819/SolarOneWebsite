"""Guards for the sitemap <lastmod> build-stamp mechanism (A1 / v1.10.16).

Background: on Vercel the serverless checkout rewrites file mtimes, so
``os.path.getmtime(seed_data.json)`` collapsed every <lastmod> to a stale
2018 date (59/59 URLs). build.sh now stamps the deploy date into the
git-ignored artifact ``pages/build_meta.py``; ``_site_last_modified()``
prefers it and falls back to the seed mtime where that file is absent.

These guards assert the *value*, not just the syntax — a missing or stale
<lastmod> is perfectly valid XML, so a syntax-level check cannot catch it.
"""
import re
import sys
import types

from django.test import TestCase

from pages.views.views_other import _site_last_modified

STAMP_MODULE = 'pages.build_meta'
FALLBACK_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


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


class SiteLastModifiedHelperTests(_StampMixin, TestCase):
    """Unit level: the helper's precedence and fallback."""

    def test_build_stamp_wins_over_seed_mtime(self):
        """When pages/build_meta.py exists, its value must be used verbatim."""
        self.install_stamp('2026-10-06')
        try:
            self.assertEqual(_site_last_modified(), '2026-10-06')
        finally:
            self.restore_stamp()

    def test_falls_back_to_seed_mtime_without_stamp(self):
        """Without the build artifact the seed mtime is used, format YYYY-MM-DD.

        ``sys.modules[name] = None`` makes the import raise ImportError, which
        is exactly the production-fallback condition we want to exercise.
        """
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
        self.assertRegex(value, FALLBACK_RE)


class SitemapLastmodRenderingTests(_StampMixin, TestCase):
    """End-to-end: the rendered XML must carry the helper's value."""

    def _lastmods(self):
        resp = self.client.get('/sitemap.xml', HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        body = resp.content.decode('utf-8')
        return re.findall(r'<lastmod>([^<]+)</lastmod>', body), body

    def test_sitemap_emits_a_lastmod_for_every_url(self):
        values, body = self._lastmods()
        locs = re.findall(r'<loc>([^<]+)</loc>', body)
        self.assertTrue(locs, 'sitemap rendered no <loc> at all')
        self.assertTrue(values, 'sitemap rendered no <lastmod> at all')
        self.assertEqual(len(values), len(locs),
                         'every <url> must carry a <lastmod>')

    def test_sitemap_lastmod_matches_helper_not_a_stale_constant(self):
        """The rendered date must equal the helper output — never a hardcoded one."""
        self.install_stamp('2026-10-06')
        try:
            values, body = self._lastmods()
        finally:
            self.restore_stamp()
        self.assertTrue(values, 'no <lastmod> rendered')
        self.assertEqual(set(values), {'2026-10-06'},
                         'rendered <lastmod> must follow the build stamp')

    def test_sitemap_never_emits_the_stale_2018_date(self):
        """Regression guard: 2018-10-20 was the hardcoded value shipped to prod."""
        values, _ = self._lastmods()
        for v in values:
            self.assertNotEqual(v, '2018-10-20',
                                'stale hardcoded lastmod leaked into the sitemap')
            self.assertRegex(v, FALLBACK_RE)
