# -*- coding: utf-8 -*-
"""Locale-safe test runner.

Django's ``LocaleMiddleware`` activates the request language in
``process_request`` and never restores it (verified against
django/middleware/locale.py — ``process_response`` has no deactivate), so
any test that GETs ``/fr/…`` leaves ``fr`` active for the rest of the
process. ``reverse()`` then emits ``/fr/``-prefixed URLs, and a later
English-expecting test silently fetches the localized page.

That is exactly how ``pages.tests.StatelessProductionTests.
test_products_page_prod_no_db_and_shows_curated_subset`` went red in a full
run while passing alone: a preceding class requested ``/fr/sitemap.xml``,
``reverse('products')`` returned ``/fr/products/``, and the curated cards
rendered as ``Série M`` instead of ``M Series``. Iron law 19 — when a guard
goes red, probe the data before doubting the implementation.

``pages/tests_project_collections.py`` already restores ``en`` in tearDown
for its own classes; this runner does it after *every* test in the suite,
including future ones, so the fix is not order-dependent.
"""
import unittest

from django.test.runner import DiscoverRunner
from django.utils import translation


class LocaleSafeDiscoverRunner(DiscoverRunner):
    """Restore the active language after each test case."""

    def get_resultclass(self):
        # Django's default returns None (only debug_sql/pdb override it);
        # TextTestRunner then falls back to unittest.TextTestResult.
        base = super().get_resultclass() or unittest.TextTestResult

        class LocaleRestoringResult(base):
            def stopTest(self, test):
                translation.activate('en')
                super().stopTest(test)

        return LocaleRestoringResult
