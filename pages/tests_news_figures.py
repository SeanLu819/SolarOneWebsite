"""Guards for v1.10.4 — in-body figures on news detail + one uniform news card.

Two changes are guarded here, and they fail in the same "nothing errors, the
page just quietly drifts" way, which is why both are pinned:

1. **Figures inside the body.** Until v1.10.4 every gallery photo rendered in
   one bento grid *above* the text, so a market article showed all five images
   before the first sentence. Editors asked for each figure to sit with the
   paragraph it illustrates. That only works if the body is rendered in pieces
   (``pages.views.news_body.build_article_body``), and the pieces are driven by
   ``{{figure:…}}`` markers in the copy — so the markers themselves, the
   "unknown marker must not eat a paragraph" rule, and the "a photo with no
   marker still renders" fallback all need pins.

2. **One card size on /news/.** The latest article used to be a featured card
   spanning two columns with a horizontal layout — roughly twice the area of
   every other card. The class survives as a styling hook, so nothing in the
   template would complain if the geometry came back; only a source-level
   assertion catches it.

Run: ``E:/Python/python3/python.exe manage.py test pages.tests_news_figures``
"""

import re

from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings

from pages.views.news_body import build_article_body


def _image(pk, url, alt='', caption=''):
    """One gallery entry shaped like `_normalize_news_image` output."""
    return {'id': pk, 'name': '', 'url': url, 'alt': alt,
            'caption': caption, 'width': None, 'height': None}


# ═════════════════════════════════════════════════════════════════════════
# build_article_body — the pure function, no DB, no templates
# ═════════════════════════════════════════════════════════════════════════
class BuildArticleBodyTests(SimpleTestCase):
    """A broken figure must cost one photo, never a paragraph of copy."""

    def _blocks(self, content, images):
        return build_article_body(content, images)

    def test_a_marker_lands_after_the_paragraph_it_follows(self):
        """A marker at the end of a sentence means "after this paragraph" —
        the figure illustrates what was just said, so it must follow it."""
        blocks, unused = self._blocks(
            'First para.\n\nSecond para. {{figure:one.webp}}\n\nThird para.',
            [_image(1, '/static/one.webp')])
        self.assertEqual(
            ['p', 'p', 'figure', 'p'],
            [b['type'] for b in blocks])
        self.assertEqual('First para.', blocks[0]['text'])
        self.assertEqual('Second para.', blocks[1]['text'])
        self.assertEqual('Third para.', blocks[3]['text'])
        self.assertEqual(unused, [])

    def test_a_marker_on_its_own_line_precedes_the_paragraph(self):
        blocks, _ = self._blocks(
            'Alpha.\n\n{{figure:one.webp}}\n\nBeta.',
            [_image(1, '/static/one.webp')])
        self.assertEqual(['p', 'figure', 'p'], [b['type'] for b in blocks])
        self.assertEqual('Beta.', blocks[2]['text'])

    def test_an_unknown_marker_drops_only_the_marker(self):
        """The load-bearing case: a typo must never swallow body copy."""
        blocks, unused = self._blocks(
            'Keep me. {{figure:typo.webp}}\n\nKeep me too.',
            [_image(1, '/static/one.webp')])
        self.assertEqual(['p', 'p'], [b['type'] for b in blocks])
        self.assertEqual('Keep me.', blocks[0]['text'])
        self.assertEqual('Keep me too.', blocks[1]['text'])
        # The unreferenced photo is handed back so the caller can still show it.
        self.assertEqual(unused, [0])

    def test_a_repeated_marker_places_the_photo_once(self):
        blocks, unused = self._blocks(
            'One. {{figure:a.webp}}\n\nTwo. {{figure:a.webp}}',
            [_image(1, '/static/a.webp')])
        self.assertEqual(['p', 'figure', 'p'], [b['type'] for b in blocks])
        self.assertEqual(unused, [])

    def test_only_the_first_figure_is_eager(self):
        """A lazy LCP candidate delays the article's largest paint."""
        blocks, _ = self._blocks(
            'A {{figure:a.webp}}\n\nB {{figure:b.webp}}\n\nC {{figure:c.webp}}',
            [_image(1, '/static/a.webp'), _image(2, '/static/b.webp'),
             _image(3, '/static/c.webp')])
        eager = [b['eager'] for b in blocks if b['type'] == 'figure']
        self.assertEqual([True, False, False], eager)

    def test_every_image_carries_at_least_one_bindable_alias(self):
        """A marker can only bind by id / name / file name / alt / URL.

        If `_image_key` were ever narrowed to a field the DB path does not send,
        every marker would silently stop resolving and all photos would fall
        back to the top grid. This pins that at least one alias always exists.
        """
        for images, expected in (
            ([_image(7, '/static/x.webp')], '7'),
            ([{'url': '/static/images/news/s/pic.webp', 'alt': '', 'caption': '',
               'width': None, 'height': None, 'id': '', 'name': ''}],
             'pic.webp'),
        ):
            blocks, unused = build_article_body(
                'Body. {{figure:%s}}' % expected, images)
            self.assertEqual(['p', 'figure'], [b['type'] for b in blocks],
                             f'no alias bound for {expected!r}')
            self.assertEqual(unused, [])

    def test_crlf_and_bare_newlines_split_the_same_way(self):
        """Windows-authored copy arrives with CRLF; the admin textarea adds LF."""
        for eol in ('\r\n\r\n', '\n\n'):
            blocks, _ = self._blocks(
                'One.%sTwo. {{figure:a.webp}}' % eol, [_image(1, '/a.webp')])
            self.assertEqual(['p', 'p', 'figure'], [b['type'] for b in blocks],
                             f'eol {eol!r} did not split')

    def test_no_images_or_no_paragraphs_degrade_to_plain_text(self):
        blocks, unused = self._blocks('Just a paragraph.', [])
        self.assertEqual([{'type': 'p', 'text': 'Just a paragraph.'}], blocks)
        self.assertEqual(unused, [])

    def test_markers_never_survive_into_the_rendered_text(self):
        """The template must never see a marker — that is the whole point of
        consuming them in Python. A leftover `{{figure:` in a paragraph means
        the split failed and raw markup would reach the page."""
        blocks, _ = self._blocks(
            'Alpha. {{figure:a.webp}}\n\nBeta.', [_image(1, '/a.webp')])
        for b in blocks:
            if b['type'] == 'p':
                self.assertNotIn('{{figure:', b['text'])


# ═════════════════════════════════════════════════════════════════════════
# The real article — both stores must agree
# ═════════════════════════════════════════════════════════════════════════
ART = 'global-led-lighting-market-2034'


class NewsInBodyFigureTests(TestCase):
    """The shipped market article must actually interleave its five figures."""

    @classmethod
    def setUpTestData(cls):
        """Mirror the seed article into the test DB.

        The test database starts empty, so the DB code path has nothing to read
        unless we materialise a row. It is built **from the seed** on purpose:
        then "the two paths agree" compares the same content serialised two
        ways, which is exactly the contract AGENTS.md §3 asks for.
        """
        from django.utils.timezone import now
        from pages.models import NewsArticle, NewsImage
        from pages.views.data_loaders import _load_seed

        seed = _load_seed()
        article = next(a for a in seed['news'] if a['slug'] == ART)
        cls.row = NewsArticle.objects.create(
            slug=ART,
            title=article['title'],
            summary=article['summary'],
            content=article['content'],
            category=article.get('category') or 'Company News',
            image=article['image'],
            published_at=now(),
            is_published=True,
            translations=article.get('translations') or {},
        )
        for image in article['images']:
            NewsImage.objects.create(
                article=cls.row, image=image['image'],
                alt_text=image.get('alt') or '',
                caption=image.get('caption') or '',
                order=image.get('order') or 1,
                width=image.get('width'), height=image.get('height'),
            )

    def _db_row(self):
        from pages.views.data_loaders import _get_news_from_db
        rows = _get_news_from_db('en')
        return next(r for r in rows if r['slug'] == ART)

    def _seed_row(self):
        from pages.views.data_loaders import _get_news_from_json
        rows = _get_news_from_json('en')
        return next(r for r in rows if r['slug'] == ART)

    @override_settings(IS_VERCEL=True)
    def test_seed_path_places_every_gallery_figure_in_the_body(self):
        row = self._seed_row()
        self.assertTrue(row['images'], '文章没有图集，这条守卫失去意义')
        self.assertEqual(
            [], row['unplaced_images'],
            '有图没被 marker 引用 —— 会退回顶部网格，段落内插图等于没做')
        placed = [b for b in row['body_blocks'] if b['type'] == 'figure']
        self.assertEqual(len(row['images']), len(placed))

    def test_db_and_seed_paths_agree(self):
        """AGENTS.md §3: production reads the seed, local dev reads the DB.

        If the two drift, a fix verified on localhost does nothing on Vercel.
        `setUpTestData` built the DB row from the same seed content, so any
        difference here is a serialiser difference, not a content one.
        """
        db, seed = self._db_row(), self._seed_row()

        def shape(row):
            return [(b['type'],
                     b.get('text') or b.get('image', {}).get('url', ''))
                    for b in row['body_blocks']]

        self.assertEqual(shape(db), shape(seed),
                         'DB 路径与 seed 路径的正文块序列不一致')
        self.assertEqual(
            [i['url'] for i in db['images']],
            [i['url'] for i in seed['images']],
            '两条路径的图集 URL 不一致')

    @override_settings(IS_VERCEL=True)
    def test_every_gallery_image_url_resolves_under_static(self):
        """v1.10.4 regression: the DB path used `field.url`, i.e. MEDIA_URL
        (`/media/…`), while every photo lives in `static/images/…` — so locally
        the news page rendered five broken images while products were fine."""
        for row in (self._db_row(), self._seed_row()):
            urls = [row['image_url']] + [i['url'] for i in row['images']]
            for url in filter(None, urls):
                self.assertTrue(
                    url.startswith('/static/'),
                    f'图 URL 未走 static/，本地会 404: {url}')

    def test_both_stores_carry_matching_markers(self):
        """A JSON-only edit is silently overwritten by seed_sync; a DB-only edit
        never reaches production. The two must hold the same marker set.

        Compares the committed `seed_data.json` (what Vercel builds from) with
        the row this test materialised from it, so a marker added to one store
        and forgotten in the other fails here.
        """
        from pages.views.data_loaders import _load_seed
        import json
        import io

        path = settings.BASE_DIR / 'seed_data.json'
        with io.open(str(path), encoding='utf-8') as f:
            data = json.load(f)
        json_content = next(a for a in data['news']
                            if a['slug'] == ART)['content']
        pattern = r'\{\{\s*figure\s*:[A-Za-z0-9_.-]+\s*\}\}'
        self.assertEqual(
            sorted(re.findall(pattern, json_content)),
            sorted(re.findall(pattern, self.row.content)),
            'seed_data.json 与数据库的 figure marker 不一致')
        self.assertTrue(re.findall(pattern, json_content),
                        'seed_data.json 的正文里一个 marker 都没有')

    def test_every_registered_gallery_file_exists_on_disk(self):
        from pages.views.data_loaders import _load_seed
        seed = _load_seed()
        article = next(a for a in seed['news'] if a['slug'] == ART)
        base = settings.BASE_DIR / 'static'
        for image in article['images']:
            path = base / image['image']
            self.assertTrue(
                path.exists(),
                f'图集文件不存在，线上必然 404: {image["image"]}')

    def test_alt_text_describes_each_figure(self):
        """Charts carry meaning, so a generic alt would hide the data from
        screen readers and from image search."""
        from pages.views.data_loaders import _load_seed
        seed = _load_seed()
        article = next(a for a in seed['news'] if a['slug'] == ART)
        for image in article['images']:
            self.assertGreater(
                len(image.get('alt') or ''), 20,
                f'图 {image["image"]} 的 alt 过短，图表内容对读屏不可见')


# ═════════════════════════════════════════════════════════════════════════
# Rendered detail page
# ═════════════════════════════════════════════════════════════════════════
class NewsDetailFigureRenderTests(NewsInBodyFigureTests):
    """Renders the real page.

    Inherits `setUpTestData` so the local (DB) code path has the article to
    read — without it the detail view 404s and every assertion below would be
    measuring an error page. The inherited test methods re-run here, which is
    harmless (they are pure assertions) and keeps one fixture to maintain.
    """

    def test_figures_render_inside_the_body_not_above_it(self):
        resp = self.client.get(f'/news/{ART}/', HTTP_HOST='localhost')
        self.assertEqual(200, resp.status_code)
        html = resp.content.decode('utf-8')
        body = re.search(
            r'<div class="news-detail-body">(.*?)</div>\s*</article>', html, re.S)
        self.assertIsNotNone(body, '正文容器没渲染出来')
        inner = body.group(1)
        self.assertIn('news-detail-figure', inner,
                      '正文里没有 figure —— 图仍被渲染在正文上方')
        self.assertNotIn('{{figure:', html,
                         'marker 泄漏到页面上了')
        # Every gallery photo must sit in the body. The top grid keeps the
        # cover only (it is the article's own image, and the og:image), so it
        # must not still hold any *gallery* photo.
        top = re.search(
            r'<div class="news-detail-media">(.*?)</div>', html, re.S)
        self.assertIsNotNone(top, '顶部封面网格没渲染 —— 封面图丢失')
        self.assertNotIn('news-detail-media-cell', top.group(1).replace(
            'news-detail-media-cell news-detail-media-cell--large', ''),
            '顶部网格里还留着图集照片，说明有图没落进正文')
        self.assertEqual(
            5, inner.count('class="news-detail-figure"'),
            '正文内的图数量不对')
        # Text and figures must interleave, not figure-after-figure.
        # Counted with `re.S` because the <figure> open tag spans several lines
        # (each conditional attribute gets its own line), so a `.` without it
        # cannot cross the tag.
        preceded = len(re.findall(r'</p>\s*<figure', inner, re.S))
        self.assertEqual(
            4, preceded,
            f'只有 {preceded}/5 张图紧跟在段落之后，正文没有真正交错')
        # And the first figure must not be a bare stack at the very top: the
        # market-size paragraph is what introduces it.
        self.assertNotRegex(
            inner, r'^\s*(?:<figure.*?</figure>\s*)+<p>',
            '正文开头是一串图，没有正文')


# ═════════════════════════════════════════════════════════════════════════
# /news/ card grid — one size
# ═════════════════════════════════════════════════════════════════════════
class NewsCardUniformSizeTests(SimpleTestCase):
    """Source-level: the featured class is only a styling hook now.

    A rendered-HTML assertion cannot see this — a card that spans two columns
    produces perfectly valid markup, it is just twice the size of its
    neighbours. So the geometry is pinned in the <style> block.
    """

    def _template(self):
        return (settings.BASE_DIR / 'templates' / 'news.html').read_text(
            encoding='utf-8')

    def _css(self):
        """The <style> block with CSS comments taken out.

        Without this the assertions below are satisfied by *documentation*: this
        file comments ``grid-auto-rows: 1fr`` and ``.news-card-more { margin-top:
        auto }`` in prose explaining why they exist. A probe that deletes the
        real declaration still left the comment behind, the assertions stayed
        green, and the guard was decoration while the page regressed. Stripping
        comments makes the assertion test the declaration and nothing else.
        """
        return re.sub(r'/\*.*?\*/', '', self._template(), flags=re.S)

    def test_featured_card_does_not_change_geometry(self):
        src = self._template()
        # The regression, stated as the exact rules that must not come back.
        self.assertNotIn('grid-column: span 2', src)
        self.assertNotIn('.news-card--featured { flex-direction: row', src)
        self.assertNotIn('.news-card--featured .news-card-cover {', src)
        self.assertNotIn('min-height: 300px', src)

    def test_grid_pins_a_uniform_row_height(self):
        css = self._css()
        self.assertIn('grid-auto-rows: 1fr', css,
                      '网格没有钉住行高，卡片会按各自内容伸缩')
        self.assertIn('height: 100%', css,
                      '卡片没有撑满行高，同一行内仍会高低不一')

    def test_card_body_pushes_the_footer_to_the_bottom(self):
        """With one card height, "Read article" must align across the row.

        Checked inside the `.news-card-more` rule, not against the whole sheet,
        so `margin-top: auto` on some other selector cannot satisfy it.
        """
        css = self._css()
        block = re.search(r'\.news-card-more\s*\{(.*?)\}', css, re.S)
        self.assertIsNotNone(block, '找不到 .news-card-more 规则')
        self.assertIn('margin-top: auto', block.group(1),
                      '.news-card-more 没有 margin-top:auto，footer 不会对齐')

    def test_only_whitelisted_breakpoints_are_used(self):
        src = self._template()
        for value in re.findall(r'max-width:\s*(\d+)px', src):
            self.assertIn(value, {'767', '1024', '1199'},
                          f'{value}px 不在 N-31 断点白名单里')
