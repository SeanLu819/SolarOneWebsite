"""Guards: JSON-LD ``image`` must be an absolute URL (A2 / v1.10.16).

Regression: ``templates/project_detail.html`` emitted
``"image": "/static/images/..."`` — a relative path. Google treats a relative
image URL in structured data as invalid, so 22 projects x 6 languages = 132
pages silently lost their rich-result image and any AI citation that needs a
resolvable image. Product / news / product-overview templates already used
``{{ canonical_origin }}``; only the project template was missing it.

These guards assert the **rendered value**, because a missing prefix is still
perfectly valid JSON-LD — a syntax-level check cannot catch it.
"""
import json
import os
import re
import tempfile
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings

from pages.models import Project
from pages.views import utils

LD_BLOCK_RE = re.compile(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
# The `nonce` attribute on the <script> tag is why the plain
# `<script type="application/ld+json">` regex silently matched nothing.


def _jsonld_blocks(html):
    out = []
    for raw in LD_BLOCK_RE.findall(html):
        raw = raw.strip()
        if not raw:
            continue
        try:
            out.append(json.loads(raw))
        except ValueError:
            continue
    return out


class ProjectJsonLdAbsoluteImageTests(TestCase):
    """Project detail JSON-LD must carry a fully-qualified image URL."""

    slug = 'qa-jsonld-cover'

    def _render(self, project):
        resp = self.client.get('/projects/%s/' % self.slug,
                               HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200,
                         'project detail page must render for the assertion to mean anything')
        return resp.content.decode('utf-8')

    def test_article_image_is_absolute(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            static_root = base / 'static'
            slug_dir = static_root / 'images' / 'projects' / self.slug
            slug_dir.mkdir(parents=True, exist_ok=True)
            (slug_dir / 'cover.webp').write_bytes(b'fake-webp-bytes')
            self.addCleanup(utils.clear_static_caches)

            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(static_root)],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                project = Project.objects.create(
                    title='QA JSON-LD Cover', slug=self.slug, order=999,
                    image='projects/%s/cover.webp' % self.slug)
                try:
                    utils.clear_static_caches()
                    html = self._render(project)
                finally:
                    # delete() MUST stay inside the override block: post_delete
                    # syncs media -> static using settings.BASE_DIR, and outside
                    # the block that is the REAL static/ tree (empty dir leak).
                    project.delete()

        blocks = _jsonld_blocks(html)
        self.assertTrue(blocks, 'no JSON-LD block rendered at all')

        articles = [b for b in blocks if b.get('@type') == 'Article']
        self.assertTrue(articles, 'no Article JSON-LD on the project detail page')

        image = articles[0].get('image')
        self.assertTrue(image, 'Article JSON-LD has an empty image')
        self.assertTrue(
            image.startswith('http://') or image.startswith('https://'),
            'Article JSON-LD image must be absolute, got %r' % image)
        self.assertIn('cover.webp', image,
                      'image should point at the project cover, got %r' % image)

    def test_every_jsonld_image_is_absolute(self):
        """No template may emit a root-relative image in structured data."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            static_root = base / 'static'
            slug_dir = static_root / 'images' / 'projects' / self.slug
            slug_dir.mkdir(parents=True, exist_ok=True)
            (slug_dir / 'cover.webp').write_bytes(b'fake-webp-bytes')
            self.addCleanup(utils.clear_static_caches)

            with override_settings(
                BASE_DIR=base,
                STATICFILES_DIRS=[str(static_root)],
                STATIC_ROOT=str(base / 'staticfiles'),
                DEBUG=False,
            ):
                project = Project.objects.create(
                    title='QA JSON-LD Cover', slug=self.slug, order=999,
                    image='projects/%s/cover.webp' % self.slug)
                try:
                    utils.clear_static_caches()
                    html = self._render(project)
                finally:
                    project.delete()

        for block in _jsonld_blocks(html):
            image = block.get('image')
            if not image:
                continue
            for one in (image if isinstance(image, list) else [image]):
                self.assertTrue(
                    str(one).startswith(('http://', 'https://')),
                    '%s JSON-LD emitted a relative image: %r'
                    % (block.get('@type'), one))

    def test_project_template_prefixes_the_image_with_canonical_origin(self):
        """Source-level guard: catches a regression even with an empty image_url."""
        body = Path('templates/project_detail.html').read_text(encoding='utf-8')
        self.assertIn(
            '"image": "{{ canonical_origin }}{{ project.image_url',
            body,
            'project_detail.html must prefix the JSON-LD image with canonical_origin')

    def test_no_template_emits_a_root_relative_jsonld_image(self):
        src_dir = Path('templates')
        offenders = []
        for path in sorted(src_dir.rglob('*.html')):
            text = path.read_text(encoding='utf-8')
            for raw in LD_BLOCK_RE.findall(text):
                for m in re.finditer(r'"image"\s*:\s*"\{\{([^}]*)\}\}', raw):
                    expr = m.group(1)
                    if 'canonical_origin' not in expr and expr.strip():
                        offenders.append('%s: %s' % (path.as_posix(), expr))
        self.assertEqual(offenders, [],
                         'JSON-LD image without canonical_origin: %s' % offenders)
