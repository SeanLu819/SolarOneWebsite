"""Regression guards for Django admin rendering of product/project forms.

A stray literal HTML tag (e.g. ``<title>``) in a ``help_text`` string is not
escaped by the current admin templates, so it breaks the browser's HTML parser
and swallows the submit-row (Save button) as text content. These tests prevent
that regression.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

from pages.models import Product


class AdminProductRenderTests(TestCase):
    """Guard the product admin change-form HTML."""

    @classmethod
    def setUpTestData(cls):
        cls.superuser = get_user_model().objects.create_superuser(
            'admin_render', 'render@test.local', 'renderpass')
        cls.product = Product.objects.create(
            name='Guard Product',
            slug='guard-product',
            category='AREA_SITE',
            description='Guard description.',
            order=1,
            is_active=True,
            page_layout='detail',
        )

    def test_model_number_help_text_contains_no_raw_html_tag(self):
        """Help text must not contain unescaped HTML tags that break parsing."""
        help_text = Product._meta.get_field('model_number').help_text
        self.assertNotRegex(help_text, r'<[a-zA-Z][a-zA-Z0-9]*\b')

    def test_product_change_page_has_exactly_one_title_tag(self):
        """A stray <title> in help_text would create a second <title> in body."""
        self.client.force_login(self.superuser)
        url = reverse('admin:pages_product_change', args=[self.product.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')
        # The real <title> lives once in <head>. Any unescaped <title> in body
        # help_text makes the count > 1 and breaks the Save button rendering.
        self.assertEqual(html.lower().count('<title'), 1)
        # And the submit-row must be present as real HTML, not escaped text.
        self.assertIn('<div class="submit-row">', html)
