from types import SimpleNamespace

from django.test import SimpleTestCase, TestCase

from pages.admin import ProjectAdmin
from pages.views import _product_image_url, _get_project_detail_from_json, _enrich_project
from django.utils.translation import activate


class ProductImagePathResolutionTests(SimpleTestCase):
    def test_static_fallback_matches_same_stem_with_webp_extension(self):
        product = SimpleNamespace(
            slug='fl4m',
            image=SimpleNamespace(name='products/fl4m-01.webp'),
        )

        url = _product_image_url(product, 'image')

        self.assertIn('/static/images/products/fl4m-01.webp', url)

    def test_static_fallback_prefers_db_relative_canonical_path(self):
        product = SimpleNamespace(
            slug='rt590fl-s',
            banner_image=SimpleNamespace(name='products/vsp/vsp-bar-1.webp'),
        )

        url = _product_image_url(product, 'banner_image')

        self.assertIn('/static/images/products/vsp/vsp-bar-1.webp', url)


class ProjectAdminOrderingTests(SimpleTestCase):
    def test_project_admin_images_section_comes_before_content(self):
        fieldset_names = [name for name, _ in ProjectAdmin.fieldsets]

        self.assertEqual(ProjectAdmin.change_form_template, 'admin/pages/project/change_form.html')
        self.assertLess(fieldset_names.index('Images'), fieldset_names.index('Content'))


class FootballFieldProjectImageTests(TestCase):
    """Verify football-field-led-retrofit project: cover + gallery paths resolve to valid static URLs."""

    def test_cover_and_gallery_resolve(self):
        activate('en')
        slug = 'football-field-led-retrofit'
        project = _get_project_detail_from_json(slug, 'en')
        self.assertIsNotNone(project, f'Project {slug} not found in seed data')
        _enrich_project(project, 'en')

        self.assertTrue(project.image_url, 'Cover image URL should not be empty')
        self.assertTrue(project.image_url.startswith('/static/'),
                        f'Cover should resolve to /static/ URL, got: {project.image_url}')

        self.assertGreaterEqual(len(project.gallery), 3,
                                f'Expected at least 3 gallery images, got {len(project.gallery)}')
        for i, g in enumerate(project.gallery):
            self.assertTrue(g['src'].startswith('/static/'),
                            f'Gallery [{i}] URL should start with /static/: {g["src"]}')
            self.assertIn('football-field-led-retrofit', g['src'],
                          f'Gallery [{i}] URL should contain slug: {g["src"]}')
        print(f'  OK cover={project.image_url}')
        for g in project.gallery:
            print(f'  OK gal={g["src"]}')