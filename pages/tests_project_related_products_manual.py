"""Guards for the manual "Related Products" picker on project pages (v1.10.25).

The category-based auto match was deleted on purpose. It iterated a ``set``, so
the same project showed different products on every process start, and it paired
venues with luminaires the business never installed there. From now on the editor
picks the luminaires in the admin; **no pick means no section** — there is no
fallback to guess with.
"""
import inspect
import re
from types import SimpleNamespace
from unittest import mock

from django.contrib import admin
from django.test import TestCase

from pages import seed_sync
from pages.models import Product, Project
from pages.views import related_links
from pages.views.enrich import (
    _enriched_product_detail_cache,
    _enriched_products_cache,
    _enriched_project_detail_cache,
    _enriched_projects_cache,
)


def _drop_enrichment_caches():
    """The catalogue caches are process-global and outlive a TestCase.

    The objects this module creates (``rp-a`` / ``rp-project``) would otherwise
    stay cached and quietly become the entire catalogue for whichever module
    runs next: that is exactly how ``HubInternalLinkTests`` went red in a
    combined run while passing on its own. Iron law 19 — when a guard goes red,
    probe the data before doubting the implementation.
    """
    _enriched_products_cache.clear()
    _enriched_projects_cache.clear()
    _enriched_product_detail_cache.clear()
    _enriched_project_detail_cache.clear()
    clear_static_caches()


class _CacheIsolationMixin:
    """Flush the global catalogue caches after every case in this module."""

    def tearDown(self):
        _drop_enrichment_caches()
        super().tearDown()
from pages.views.related_links import related_products_for_project
from pages.views.utils import clear_static_caches
from pages.views.utils import _DictProject, _load_seed


def _seed_product_slugs(count=2):
    """Real product slugs taken from the production source of truth.

    Iron law 7: never hard-code a slug here — derive it from ``_load_seed()``.
    """
    out = []
    for p in _load_seed().get('products', []) or []:
        slug = p.get('slug') if hasattr(p, 'get') else getattr(p, 'slug', '')
        if slug and slug not in out:
            out.append(slug)
        if len(out) >= count:
            break
    return out


class ManualRelatedProductsFieldTests(_CacheIsolationMixin, TestCase):
    """The change form must offer a picker, and the field must be optional."""

    def test_the_field_exists_and_is_optional(self):
        field = Project._meta.get_field('related_products')
        self.assertTrue(field.many_to_many)
        self.assertTrue(field.blank, 'picking nothing must stay legal')
        self.assertEqual('Product', field.related_model.__name__)

    def test_the_admin_offers_a_picker(self):
        model_admin = admin.site._registry[Project]
        fields = []
        for _label, opts in model_admin.fieldsets:
            for item in opts['fields']:
                if isinstance(item, (list, tuple)):
                    fields.extend(item)
                else:
                    fields.append(item)
        self.assertIn('related_products', fields,
                      'the field is missing from the project change form')
        self.assertIn('related_products', model_admin.filter_horizontal,
                      'a bare multi-select is unusable with ~24 products')


class ManualRelatedProductsSeedPathTests(_CacheIsolationMixin, TestCase):
    """Vercel reads the seed, which carries slugs rather than a M2M manager."""

    def setUp(self):
        self.slugs = _seed_product_slugs(2)
        self.catalogue = [SimpleNamespace(slug=s) for s in self.slugs]

    def _resolve(self, slugs):
        """Resolve with the catalogue pinned — the guard is about the picks."""
        project = _DictProject({'slug': 'seed-path',
                                'related_product_slugs': list(slugs)})
        with mock.patch.object(related_links, 'get_all_products',
                               return_value=self.catalogue):
            return related_products_for_project(project, 'en')

    def test_the_seed_really_carries_products(self):
        """Guards the guard: silence here would make everything below green."""
        self.assertEqual(2, len(self.slugs), 'the seed has no products')

    def test_the_picks_come_back_in_the_exported_order(self):
        got = self._resolve(list(reversed(self.slugs)))
        self.assertEqual(list(reversed(self.slugs)), [p.slug for p in got])

    def test_only_the_picks_come_back(self):
        """Picking one of two must not drag the rest of the catalogue in."""
        got = self._resolve(self.slugs[:1])
        self.assertEqual(self.slugs[:1], [p.slug for p in got])

    def test_nothing_picked_means_nothing_rendered(self):
        self.assertEqual([], self._resolve([]))

    def test_a_missing_key_is_treated_as_no_pick(self):
        """``_load_seed()`` has no such key yet; the page must not break."""
        project = _DictProject({'slug': 'seed-path'})
        with mock.patch.object(related_links, 'get_all_products',
                               return_value=self.catalogue):
            self.assertEqual([], related_products_for_project(project, 'en'))

    def test_the_exporter_writes_the_manual_picks(self):
        """Iron law 1: the DB -> JSON exporter must not drop the field."""
        src = inspect.getsource(seed_sync._project_to_dict)
        self.assertIn("'related_product_slugs': related_slugs", src,
                      'the seed exporter no longer writes the manual picks')


class ManualRelatedProductsDbPathTests(_CacheIsolationMixin, TestCase):
    """Local dev and the admin read the M2M."""

    def setUp(self):
        self.a = Product.objects.create(
            slug='rp-a', name='A', category='SPORTS_LIGHTING', description='a')
        self.b = Product.objects.create(
            slug='rp-b', name='B', category='FLOODLIGHT', description='b')
        self.project = Project.objects.create(
            slug='rp-project', title='P', location='L',
            venue_type='OUTDOOR', sport_type='FOOTBALL_FIELD', description='d')

    def _resolve(self):
        with mock.patch.object(related_links, 'get_all_products',
                               return_value=[self.a, self.b]):
            return related_products_for_project(self.project, 'en')

    def test_the_picks_come_back(self):
        self.project.related_products.set([self.b, self.a])
        self.assertEqual(['rp-a', 'rp-b'], [p.slug for p in self._resolve()])

    def test_nothing_picked_means_nothing_rendered(self):
        self.assertEqual([], self._resolve())

    def test_the_result_does_not_depend_on_the_venue_type(self):
        """Regression: the old code derived the links from sport/venue type."""
        self.project.related_products.set([self.a])
        first = [p.slug for p in self._resolve()]
        self.project.sport_type = 'AQUATICS_CENTRE'
        self.project.venue_type = 'INDOOR'
        self.project.save()
        self.assertEqual(['rp-a'], first)
        self.assertEqual(first, [p.slug for p in self._resolve()],
                         'changing the venue type changed the manual picks')


class TemplateSectionIsConditionalTests(_CacheIsolationMixin, TestCase):
    """The section must be gated on the pick itself.

    Iron law 32: asserting the *value* of a rendered page is ideal, but the
    project view reads the DB/seed catalogue through process-global caches,
    so an end-to-end case here leaks state into unrelated modules. What the
    template does with an empty list is deterministic, so assert the gate
    itself: no pick -> ``related_products`` is ``[]`` (guarded above) -> the
    whole block is skipped.
    """

    def _markup(self):
        with open("templates/project_detail.html", encoding="utf-8") as fh:
            text = fh.read()
        # Iron law 13: a comment mentioning a tag must not satisfy the guard.
        text = re.sub(r"{#.*?#}", "", text, flags=re.S)
        return re.sub(r"{%\s*comment\s*%}.*?{%\s*endcomment\s*%}", "", text, flags=re.S)

    def test_the_section_is_wrapped_in_the_conditional(self):
        markup = self._markup()
        self.assertIn("{% if related_products %}", markup,
                      "the section is no longer gated on the pick")
        block = markup.split("{% if related_products %}", 1)[1].split("{% endif %}", 1)[0]
        self.assertIn("related-products", block)
        self.assertIn("related-product-card", block)
        self.assertIn("{% url 'product_detail'", block,
                      "the cards no longer link to the product pages")


class AutomaticMatchIsGoneTests(_CacheIsolationMixin, TestCase):
    """The heuristic that produced the wrong (and unstable) links is deleted."""

    def test_the_auto_match_tables_are_gone(self):
        src = inspect.getsource(related_links)
        self.assertNotIn('PROJECT_SPORT_TO_PRODUCT_CATEGORIES', src)
        self.assertNotIn('PROJECT_VENUE_TO_PRODUCT_CATEGORIES', src)

    def test_the_helper_never_looks_at_the_taxonomy(self):
        """A pick must be the only input — no sport/venue fallback anywhere."""
        src = inspect.getsource(related_products_for_project)
        self.assertNotIn('sport_type', src)
        self.assertNotIn('venue_type', src)
        self.assertNotIn('category', src)
