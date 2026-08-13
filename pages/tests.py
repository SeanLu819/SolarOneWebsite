from types import SimpleNamespace

from django.test import SimpleTestCase

from pages.admin import ProjectAdmin
from pages.views import _product_image_url


class ProductImagePathResolutionTests(SimpleTestCase):
    def test_static_fallback_matches_same_stem_with_webp_extension(self):
        product = SimpleNamespace(
            slug='fl4m',
            image=SimpleNamespace(name='products/fl4m-01.png'),
        )

        url = _product_image_url(product, 'image')

        self.assertIn('/static/images/products/fl4m/fl4m-01.webp', url)

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
