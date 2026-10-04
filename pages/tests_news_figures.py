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
   every other article. The class survives as a styling hook, so nothing in the
   template would complain if the geometry came back; only a source-level
   assertion catches it.

3. **A card cover that exists** (v1.10.8). An article with no cover of its own
   fell through to a grey gradient block, which an editor reported as "the
   cover is not visible". The card now borrows the first gallery image, in the
   same order as `social_image_url`, so card / og:image / JSON-LD agree.

4. **The category rename and the centred cover** (v1.10.10).
   ``NewsCategoryTaxonomyTests`` pins that ``Company News`` ->
   ``Exhibition Information`` landed on all five surfaces that hold the literal
   (choices / ``_SIDEBAR_I18N`` / seed rows / view fallbacks / seed default) --
   every one of which degrades silently. ``NewsCoverCentringTests`` measures the
   cover's inked pixels, because the v1.10.9 cover was a geometrically perfect
   16:9 canvas with 47% of its width baked in as white space.

Run: ``E:/Python/python3/python.exe manage.py test pages.tests_news_figures``
"""

import json
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
    """The shipped market article must actually interleave every figure it carries."""

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
            category=article.get('category') or 'Exhibition Information',
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
        """Derived from the article, never hard-coded to a count.

        v1.10.4 shipped this with `5` / `4` written into the assertion, which
        broke the moment the article lost three photos (v1.10.6). The count the
        page should show *is* the gallery length, so read it from there:
        hard-coding it only converts a content edit into a test edit.
        """
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

        expected = len(self.row.images.all())
        self.assertGreater(expected, 0, '这篇已经没有图集了，守卫失去意义')
        self.assertEqual(
            expected, inner.count('class="news-detail-figure"'),
            '正文内的图数量与图集条目数不一致')
        # Text and figures must interleave, not figure-after-figure.
        # Counted with `re.S` because the <figure> open tag spans several lines
        # (each conditional attribute gets its own line), so a `.` without it
        # cannot cross the tag.
        preceded = len(re.findall(r'</p>\s*<figure', inner, re.S))
        self.assertEqual(
            expected, preceded,
            f'只有 {preceded}/{expected} 张图紧跟在段落之后，正文没有真正交错')
        # The top grid is the cover's, and only renders while a cover exists.
        # v1.10.6: this article's three photographs were removed, so it has no
        # cover -- an empty 16:9 shell would be worse than no grid at all.
        top = re.search(
            r'<div class="news-detail-media">(.*?)</div>', html, re.S)
        if top:
            self.assertIn('news-detail-media-cell--large', top.group(1),
                          '顶部网格渲染了却没有封面')
            rest = top.group(1).replace(
                'news-detail-media-cell news-detail-media-cell--large', '')
            self.assertNotIn('<figure class="news-detail-media-cell"', rest,
                             '顶部网格里混进了图集照片，说明有图没落进正文')
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


class NewsDetailFigureLayoutTests(SimpleTestCase):
    """v1.10.5 / v1.10.8 — body figures render at a fixed share of the column,
    centred.

    The first image on the page is the article cover (`.news-detail-media-cell
    --large`); it keeps its full-bleed grid cell. Everything the body inserts is
    scaled down and centred, which is what makes an inserted photo read as an
    illustration rather than a page-wide banner.

    v1.10.5 shipped 50%. The editor then asked for ~120% of that on the strength
    of the three market charts, whose 1639px originals put their 8–13px labels
    at 3.0–4.8px once squeezed into 608px. 60% (≈730px of the 1216px content
    box) lifts those labels to ≈3.6–5.8px. Still small — the real fix is to
    re-render the charts at their display size — but it is the size that was
    asked for, so the number is pinned here rather than left to drift.

    Like the card guards above this is a *source-level* assertion: a
    centre-scaled image is perfectly valid markup, so nothing else in the suite
    would notice the rule drift.
    """

    #: v1.10.8 — 50% × 1.2. Keep in sync with `.news-detail-figure img` in
    #: `templates/news_detail.html`.
    EXPECTED_FIGURE_WIDTH = 'width: 60%'

    def _template(self):
        return (settings.BASE_DIR / 'templates' / 'news_detail.html').read_text(
            encoding='utf-8')

    def _css(self):
        """Comments stripped, so prose about a declaration cannot satisfy it."""
        return re.sub(r'/\*.*?\*/', '', self._template(), flags=re.S)

    def _rule(self, selector):
        block = re.search(re.escape(selector) + r'\s*\{(.*?)\}',
                          self._css(), re.S)
        self.assertIsNotNone(block, f'找不到 {selector} 规则')
        return block.group(1)

    def test_figures_render_at_the_expected_share_of_the_column(self):
        body = self._rule('.news-detail-figure img')
        self.assertIn(self.EXPECTED_FIGURE_WIDTH, body,
                      '插图宽度不是约定的 60%，正文里的图尺寸漂了')
        self.assertIn('height: auto', body,
                      '高度被写死就不是"长宽同比缩放"了')

    def test_figures_are_centred_in_the_column(self):
        body = self._rule('.news-detail-figure img')
        self.assertIn('margin-inline: auto', body,
                      '图没有水平居中（img 是块级盒，不居中就靠左）')

    def test_both_axes_scale_together(self):
        """A percentage width on its own would letterbox a portrait photo.

        With `height: auto` the browser keeps the intrinsic ratio, so scaling the
        width scales the height as well. If someone pins a height instead of
        leaving it auto, a chart gets cropped.
        """
        body = self._rule('.news-detail-figure img')
        self.assertIn('height: auto', body, 'height 不是 auto')
        self.assertNotIn('object-fit: cover', body,
                         '插图用了 cover 会裁掉图表左右两侧')

    def test_the_first_image_keeps_its_full_width(self):
        """Only the body figures change size; the cover must stay full-bleed."""
        hero = self._rule('.news-detail-media-cell img')
        self.assertIn('width: 100%', hero, '封面被一起缩小了')
        self.assertIn('object-fit: cover', hero, '封面没有 cover')
        self.assertNotIn(self.EXPECTED_FIGURE_WIDTH, hero,
                         '封面规则里出现了插图宽度，第一张图没被排除掉')

    def test_the_caption_follows_the_image_to_the_centre(self):
        """A left-aligned caption under a centred photo reads as a bug."""
        caption = self._rule('.news-detail-figure figcaption')
        self.assertIn('text-align: center', caption,
                      '图居中了但图注还在左边，视觉像错位')

    def test_phones_get_the_full_width_back(self):
        """60% of a ~360px content box is ~216px — a chart label lands at 1px.

        Anchor the assertion inside the 767 block so a `width: 100%` anywhere
        else in the sheet cannot satisfy it.
        """
        css = self._css()
        blocks = re.findall(r'@media\s*\(max-width:\s*767px\)\s*\{(.*?)\n  \}',
                            css, re.S)
        self.assertTrue(blocks, '找不到 767px 断点块')
        phone = ' '.join(blocks)
        self.assertIn('.news-detail-figure img', phone,
                      '767px 块里没有给插图恢复通栏')
        self.assertIn('width: 100%', phone,
                      '767px 块里没有把插图恢复成通栏')


# ═════════════════════════════════════════════════════════════════════════
# v1.10.7 — social card / JSON-LD image survives an article without a cover
# ═════════════════════════════════════════════════════════════════════════
class NewsSocialImageTests(NewsDetailFigureRenderTests):
    """v1.10.7 regression, found by actually reading the rendered page.

    v1.10.6 removed the market article's cover. The template advertised
    `{{ article.image_url }}`, so the ``NewsArticle`` block degraded to
    ``"image": "https://www.solaronelighting.com"`` — a bare origin, which
    consumers reject — and ``og:image`` disappeared entirely, because the
    site-wide fallback in ``base.html`` is empty too. Neither showed up as an
    error: the page still returned 200 and the JSON still parsed, which is
    exactly why `JsonLdValidityTests` (parsability only) let it through.

    These guards assert the *value*, not the syntax.
    """

    ORIGIN = 'https://www.solaronelighting.com'

    def _detail(self):
        resp = self.client.get(f'/news/{ART}/', HTTP_HOST='localhost')
        self.assertEqual(200, resp.status_code)
        return resp.content.decode('utf-8')

    def _article_jsonld(self, html):
        for raw in re.findall(
                r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
                html, re.S | re.I):
            obj = json.loads(raw)
            if obj.get('@type') == 'NewsArticle':
                return obj
        self.fail('页面里没有 NewsArticle 结构化数据块')

    def test_the_article_block_advertises_a_real_image(self):
        obj = self._article_jsonld(self._detail())
        image = obj.get('image')
        self.assertTrue(image, 'NewsArticle 块没有 image —— 分享出去没有预览图')
        self.assertNotEqual(
            self.ORIGIN, image,
            f'JSON-LD 的 image 退化成了裸域名：{image!r}（消费者会判为无效）')
        self.assertRegex(
            image, r'^https://www\.solaronelighting\.com/static/.+\.(webp|png|jpg)$',
            f'JSON-LD 的 image 不是站点下的真实图片文件：{image!r}')

    def test_og_image_points_at_the_same_file(self):
        """A card image and structured data that disagree confuse crawlers."""
        html = self._detail()
        obj = self._article_jsonld(html)
        meta = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        self.assertIsNotNone(meta, '页面没有 og:image（分享/抓取都没有预览图）')
        self.assertEqual(
            obj['image'], meta.group(1),
            'og:image 与 JSON-LD image 不一致，两处应指向同一张图')

    def test_social_image_falls_back_to_the_first_gallery_entry(self):
        from pages.views.data_loaders import _get_news_from_json
        row = next(r for r in _get_news_from_json('en') if r['slug'] == ART)
        self.assertEqual('', row['image_url'],
                         '这篇已经不该有封面了（否则本组守卫的前提失效）')
        self.assertTrue(row['images'], '这篇不该一张图都没有')
        self.assertEqual(
            row['images'][0]['url'], row['social_image_url'],
            '没有封面时 social_image_url 应回落到第一张图集图')

    def test_both_paths_derive_the_same_social_image(self):
        db, seed = self._db_row(), self._seed_row()
        self.assertEqual(
            db['social_image_url'], seed['social_image_url'],
            'DB 路径与 seed 路径的 social_image_url 不一致')

    def test_every_seeded_article_advertises_something(self):
        """No article may end up advertising a bare origin, whichever path.

        An article with no images at all is allowed to have an empty value --
        the template then omits the JSON key instead of emitting a broken URL.
        """
        from pages.views.data_loaders import _get_news_from_json
        for row in _get_news_from_json('en'):
            value = row.get('social_image_url', '')
            if not row['image_url'] and not row['images']:
                self.assertEqual('', value,
                                 f'{row["slug"]}: 无图文章应留空，而不是编一个值')
                continue
            self.assertTrue(
                value.startswith('/static/'),
                f'{row["slug"]}: social_image_url 不是 static 下的真实图片：{value!r}')


# ═════════════════════════════════════════════════════════════════════════
# v1.10.8 — a /news/ card without a cover borrows the article's first figure
# ═════════════════════════════════════════════════════════════════════════
class NewsCardCoverFallbackTests(TestCase):
    """v1.10.8, raised by an editor: "the cover of *Global LED Market to Triple
    by 2034* is not visible."

    What was actually on screen was not a broken image — it was
    `.news-card-cover-fallback`, a grey gradient block, because v1.10.6 removed
    that article's cover and the card only ever looked at `article.image_url`.
    The card rendered, the HTTP status was 200, and nothing in the suite failed.

    So the guard is on the rendered list page: for an article that has gallery
    images, the cover box must contain a real `<img>` pointing at one of them,
    and the gradient placeholder must be reserved for articles that have no
    picture at all.
    """

    GALLERY = ART  # the market article: no cover, three charts

    @classmethod
    def setUpTestData(cls):
        from django.utils.timezone import now
        from pages.models import NewsArticle, NewsImage
        from pages.views.data_loaders import _load_seed

        seed = _load_seed()
        market = next(a for a in seed['news'] if a['slug'] == cls.GALLERY)
        cls.market = NewsArticle.objects.create(
            slug=market['slug'],
            title=market['title'],
            summary=market['summary'],
            content=market['content'],
            category=market.get('category') or 'Exhibition Information',
            image=market['image'],
            published_at=now(),
            is_published=True,
            translations=market.get('translations') or {},
        )
        for image in market['images']:
            NewsImage.objects.create(
                article=cls.market, image=image['image'],
                alt_text=image.get('alt') or '',
                caption=image.get('caption') or '',
                order=image.get('order') or 1,
                width=image.get('width'), height=image.get('height'),
            )

        # A second article that *does* have a cover of its own, so the guard
        # also proves the fallback does not hijack a healthy cover.
        cls.covered = NewsArticle.objects.create(
            slug='covered-article',
            title='An article with a cover',
            summary='Cover regression fixture.',
            content='<p>Body copy.</p>',
            category='Exhibition Information',
            image='images/news/global-led-lighting-market-2034/'
                  'chart-by-segment-2026.webp',
            published_at=now(),
            is_published=True,
            translations={},
        )

    def _cards(self):
        """Return `{slug: cover_html}` for every card on /news/.

        Two things about the real markup, both learned by dumping it:

        - the card is an `<a>` *wrapping* the cover, so matching only
          `<div class="news-card-cover">…</div>` loses the href that says which
          article a cover belongs to — grab the anchor first, slice the cover
          out of it;
        - the template wraps attributes across lines, so `href` is preceded by
          a newline. `\\s*` around the attribute boundary is not optional.
        """
        resp = self.client.get('/news/', HTTP_HOST='localhost')
        self.assertEqual(200, resp.status_code)
        html = resp.content.decode('utf-8')
        cards = {}
        for href, inner in re.findall(
                r'<a class="news-card[^"]*"\s*href="([^"]+)"\s*>(.*?)</a>',
                html, re.S):
            slug = href.rstrip('/').rsplit('/', 1)[-1]
            cover = re.search(
                r'<div class="news-card-cover">(.*?)</div>\s*'
                r'<div class="news-card-body">', inner, re.S)
            self.assertIsNotNone(cover, f'{slug}: 卡片没有封面容器')
            cards[slug] = cover.group(1)
        self.assertTrue(cards, '列表页没有渲染任何卡片')
        return cards

    def _card_for(self, slug):
        cards = self._cards()
        self.assertIn(slug, cards, f'列表页里找不到 {slug} 的卡片')
        return cards[slug]

    def test_the_coverless_article_still_shows_a_picture(self):
        card = self._card_for(self.GALLERY)
        self.assertIn('<img', card,
                      '无封面文章的卡片仍是占位块——这就是"封面不可见"')
        self.assertNotIn('news-card-cover-fallback', card,
                         '有图集却仍渲染渐变占位块')

    def test_the_borrowed_cover_is_one_of_the_article_figures(self):
        from pages.views.data_loaders import _get_news_from_db
        row = next(r for r in _get_news_from_db('en') if r['slug'] == self.GALLERY)
        self.assertEqual('', row['image_url'],
                         '这篇已经不该有封面了（否则本组守卫的前提失效）')
        gallery = [i['url'] for i in row['images']]
        self.assertTrue(gallery, '这篇不该一张图都没有')
        src = re.search(r'<img src="([^"]+)"', self._card_for(self.GALLERY))
        self.assertIsNotNone(src, '卡片封面里没有 img 标签')
        self.assertIn(src.group(1), gallery,
                      f'卡片封面用的不是本文的图集图：{src.group(1)!r}')

    def test_an_article_with_its_own_cover_keeps_it(self):
        card = self._card_for(self.covered.slug)
        src = re.search(r'<img src="([^"]+)"', card)
        self.assertIsNotNone(src, '有封面的文章没有渲染封面图')
        self.assertIn('chart-by-segment-2026.webp', src.group(1),
                      '回落逻辑把文章自己的封面顶掉了')
        self.assertNotIn('news-card-cover-fallback', card,
                         '有封面却仍渲染渐变占位块')

    def test_the_placeholder_is_reserved_for_articles_with_no_picture(self):
        """The gradient block must stay reachable, or a pictureless article
        would render an empty 16:9 box instead."""
        from django.utils.timezone import now
        from pages.models import NewsArticle
        NewsArticle.objects.create(
            slug='no-pictures-at-all',
            title='No images whatsoever',
            summary='Placeholder regression fixture.',
            content='<p>Body copy.</p>',
            category='Exhibition Information',
            image='',
            published_at=now(),
            is_published=True,
            translations={},
        )
        card = self._card_for('no-pictures-at-all')
        self.assertNotIn('<img', card, '无图文章不该凭空造出 img')
        self.assertIn('news-card-cover-fallback', card,
                      '无图文章没有回落到渐变占位块')

    def test_the_template_falls_back_before_rendering_the_placeholder(self):
        """Source-level pin for the branch order.

        `{% firstof article.image_url article.images.0.url %}` only falls back
        while `article.image_url` is empty; reversing the two arguments, or
        testing the gallery first, quietly changes which picture a card shows
        without any test noticing.
        """
        src = (settings.BASE_DIR / 'templates' / 'news.html').read_text(
            encoding='utf-8')
        block = re.search(
            r'\{% if article\.image_url or article\.images\.0\.url %\}'
            r'(.*?)\{% else %\}', src, re.S)
        self.assertIsNotNone(block, '卡片封面没有"有图就渲染 img"的分支')
        firstof = re.search(r'\{% firstof ([^%]+) %\}', block.group(1))
        self.assertIsNotNone(firstof, '分支里没有 firstof')
        self.assertEqual(
            'article.image_url article.images.0.url',
            ' '.join(firstof.group(1).split()),
            '回落顺序变了：自有封面必须优先于图集首图')

    def test_the_card_shows_the_same_file_as_og_and_structured_data(self):
        """One picture, three places: card / og:image / NewsArticle `image`.

        The template computes the fallback itself (`firstof`) while the other two
        read the derived `social_image_url`. Those are two implementations of one
        rule, so they can drift — and a crawler that sees a different preview
        image than the page is exactly the kind of quiet mismatch nothing else
        reports. Compare the card's *path* against the derived value, since the
        template emits it relative and JSON-LD absolutises it.
        """
        from pages.views.data_loaders import _get_news_from_db
        row = next(r for r in _get_news_from_db('en') if r['slug'] == self.GALLERY)
        src = re.search(r'<img src="([^"]+)"', self._card_for(self.GALLERY))
        self.assertIsNotNone(src, '卡片封面里没有 img 标签')
        self.assertEqual(
            row['social_image_url'], src.group(1),
            '卡片封面与 social_image_url 不是同一张图：'
            'og:image / JSON-LD 会指向另一张')


# ═════════════════════════════════════════════════════════════════════════
# v1.10.9 — the HKTEX 2026 article: cover geometry and SERP budgets
# ═════════════════════════════════════════════════════════════════════════
HKTEX = 'hk-outdoor-tech-light-expo-2026'


class NewsCoverGeometryTests(SimpleTestCase):
    """v1.10.9 — a cover must survive the 16:9 crop both surfaces apply.

    The HKTEX cover is a 1470x240 strip (6.13:1) carrying the show wordmark, the
    dates and the venue on one line. Both news surfaces put the cover in a 16:9
    box with `object-fit: cover`, so the raw strip would be scaled to fill the
    height and ~71% of its width cropped away -- the wordmark and the dates
    would be gone and the page would still return 200.

    So the file itself is matted to 16:9. That is a property of the asset, which
    no template assertion can see, and a later re-export would silently undo it
    -- hence reading the real pixel dimensions here.
    """

    RATIO = 16 / 9
    #: How much of the canvas height the matted strip may occupy. The source is
    #: 6.13:1, so at full canvas width it fills 1/6.13 ≈ 16%; 45% leaves room for
    #: a re-export that is less wide without silently cropping the content.
    MAX_HEIGHT_SHARE = 0.45

    def _cover_path(self):
        from pages.views.data_loaders import _load_seed
        article = next(a for a in _load_seed()['news'] if a['slug'] == HKTEX)
        return settings.BASE_DIR / 'static' / article['image']

    def _webp_size(self, path):
        """Read VP8/VP8L/VP8X dimensions without a decoder dependency."""
        data = path.read_bytes()
        self.assertEqual(data[:4], b'RIFF', '不是 RIFF/WebP 容器')
        self.assertEqual(data[8:12], b'WEBP', 'RIFF 容器不是 WebP')
        fourcc = data[12:16]
        if fourcc == b'VP8 ':
            # Lossy: 3-byte frame tag, 3-byte sync code, then 14-bit w/h.
            off = 26
            w = int.from_bytes(data[off:off + 2], 'little') & 0x3FFF
            h = int.from_bytes(data[off + 2:off + 4], 'little') & 0x3FFF
            return w, h
        if fourcc == b'VP8L':
            bits = int.from_bytes(data[21:25], 'little')
            return (bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1
        if fourcc == b'VP8X':
            w = int.from_bytes(data[24:27], 'little') + 1
            h = int.from_bytes(data[27:30], 'little') + 1
            return w, h
        self.fail(f'未处理的 WebP 编码: {fourcc!r}')

    def test_the_cover_file_exists(self):
        self.assertTrue(self._cover_path().exists(),
                        f'封面文件不存在: {self._cover_path()}')

    def test_the_cover_is_already_sixteen_by_nine(self):
        w, h = self._webp_size(self._cover_path())
        ratio = w / h
        self.assertAlmostEqual(
            self.RATIO, ratio, delta=0.02,
            msg=f'封面 {w}x{h}（{ratio:.3f}）不是 16:9（{self.RATIO:.3f}）——'
                '16:9 容器 + object-fit:cover 会把它裁掉两侧')

    def test_the_cover_is_wide_enough_to_stay_legible(self):
        """A 16:9 canvas small enough to fit on the card still has to be sharp."""
        w, h = self._webp_size(self._cover_path())
        self.assertGreaterEqual(
            w, 1200, f'封面只有 {w}px 宽，卡片上会发虚')
        self.assertLessEqual(
            h * self.RATIO, w, '画布宽高关系异常')


class NewsArticleSeoBudgetTests(SimpleTestCase):
    """v1.10.9 — the HKTEX article must not push the site over its SERP budgets.

    Two numbers, both enforced elsewhere for other templates:
    `<title>` = ``{title} — SolarOne News`` must stay at 60 characters or fewer
    (`SiteTitleBudgetTests`, which already fails on the 80-char Tianjin title, so
    a new article going over would add a *second* failure to a debt we are trying
    to shrink), and the summary is rendered through `|truncatechars:160` --
    anything past 160 is markup the SERP never shows.
    """

    SUFFIX = ' — SolarOne News'
    MAX_TITLE = 60
    MAX_SUMMARY = 160

    def _article(self):
        from pages.views.data_loaders import _load_seed
        return next(a for a in _load_seed()['news'] if a['slug'] == HKTEX)

    def test_the_rendered_title_fits_the_budget(self):
        title = self._article()['title']
        total = len(title) + len(self.SUFFIX)
        self.assertLessEqual(
            total, self.MAX_TITLE,
            f'news <title> 渲染 {total} 字符，超预算: {title!r}')

    def test_the_summary_survives_truncation(self):
        summary = self._article()['summary']
        self.assertLessEqual(
            len(summary), self.MAX_SUMMARY,
            f'summary {len(summary)} 字符，模板 truncatechars:160 会截掉尾巴')

    def test_both_seed_mirrors_carry_the_same_article(self):
        """`_load_seed()` prefers the build artifact, so a JSON-only edit never
        reaches production and an artifact-only edit is lost on the next build."""
        import json
        path = settings.BASE_DIR / 'seed_data.json'
        js = next(a for a in json.loads(path.read_text(encoding='utf-8'))['news']
                  if a['slug'] == HKTEX)
        art = self._article()
        for field in ('title', 'summary', 'content', 'image', 'published_at'):
            with self.subTest(field=field):
                self.assertEqual(
                    js[field], art[field],
                    f'seed_data.json 与 pages/seed_data.py 的 {field} 不一致')

    def test_the_article_publishes_in_the_five_other_languages_as_empty(self):
        """Base fields stay English; the five translations start empty and fall
        back rather than rendering a blank. An accidental non-empty value here
        would be an unreviewed translation shipping to five locales."""
        for lang, value in (self._article().get('translations') or {}).items():
            with self.subTest(lang=lang):
                self.assertEqual(
                    {}, value, f'{lang} 译文非空但未复核：{value!r}')

    def test_the_body_carries_no_figure_markers_it_cannot_resolve(self):
        """The article ships a cover and no gallery, so any marker left in the
        copy would render a dropped marker or, worse, a half-empty figure."""
        article = self._article()
        self.assertEqual([], article.get('images'),
                         '这篇应当只有封面、没有图集')
        self.assertNotIn(
            'figure:', article['content'],
            '正文里残留 figure 标记，但没有图集可对应')


# ═════════════════════════════════════════════════════════════════════════
# v1.10.10 — 'Company News' -> 'Exhibition Information', and a centred cover
# ═════════════════════════════════════════════════════════════════════════
class NewsCategoryTaxonomyTests(SimpleTestCase):
    """v1.10.10 — the category rename has to land on every surface at once.

    Renaming a `choices` entry looks like a one-line change but the literal
    lives in five independent places, and every one of them fails *silently*:

    | where | what breaks if it is missed |
    |---|---|
    | `NewsArticle.NEWS_CATEGORIES` | admin dropdown offers a value the feed does not use |
    | `_SIDEBAR_I18N` | chip shows the bare English key in all five locales |
    | seed rows (`category`) | article filed under a key absent from `choices` |
    | `_t()` fallbacks in the views | an article with no `category` key renders an untranslated chip |
    | `data_loaders` seed default | same, one layer down |

    The old name is asserted *absent* from the source, because the one failure
    mode a positive assertion cannot catch is a half-finished rename: `choices`
    updated, `_SIDEBAR_I18N` forgotten -> the chip degrades to English in fr/es/
    de/ru/ar with no error anywhere.
    """

    RENAMED_FROM = 'Company News'
    #: The exact set the editors asked for: case studies, industry news and
    #: exhibition information. Pinned so a stray bucket cannot reappear.
    EXPECTED = {
        'Exhibition Information',
        'Product News',
        'Case Studies',
        'Industry Insights',
    }

    def _choices(self):
        from pages.models import NewsArticle
        return {key for key, _label in NewsArticle.NEWS_CATEGORIES}

    def _source_files(self):
        return [
            settings.BASE_DIR / 'pages' / 'models.py',
            settings.BASE_DIR / 'pages' / 'views' / 'i18n.py',
            settings.BASE_DIR / 'pages' / 'views' / 'views_other.py',
            settings.BASE_DIR / 'pages' / 'views' / 'data_loaders.py',
            settings.BASE_DIR / 'seed_data.json',
        ]

    def test_the_choices_are_exactly_the_agreed_taxonomy(self):
        self.assertEqual(self.EXPECTED, self._choices())

    def test_the_field_default_is_a_valid_choice(self):
        """`default` feeds the admin's "add article" form. A default outside
        `choices` renders a select whose value matches no option."""
        from pages.models import NewsArticle
        default = NewsArticle._meta.get_field('category').default
        self.assertIn(
            default, self._choices(),
            f'category default {default!r} 不在 NEWS_CATEGORIES 里')

    def test_every_choice_has_a_translation_in_all_five_locales(self):
        """`_t()` falls back to the English key when a locale is missing, so an
        incomplete entry ships a half-English chip row with nothing logged."""
        from pages.views.i18n import _SIDEBAR_I18N
        for key in sorted(self._choices()):
            with self.subTest(category=key):
                entry = _SIDEBAR_I18N.get(key)
                self.assertIsNotNone(
                    entry, f'_SIDEBAR_I18N 缺 {key!r}，五个语种都会退回英文')
                for lang in ('fr', 'es', 'de', 'ru', 'ar'):
                    value = entry.get(lang)
                    self.assertTrue(
                        value and value.strip(),
                        f'{key!r} 的 {lang} 译文为空')
                    self.assertNotEqual(
                        key, value,
                        f'{key!r} 的 {lang} 译文等于英文原文，等于没翻')

    def test_the_old_name_is_gone_from_every_surface(self):
        """The half-rename guard: `choices` says one thing, something else says
        another, and the only symptom is an English chip in five locales."""
        for path in self._source_files():
            with self.subTest(path=path.name):
                src = path.read_text(encoding='utf-8')
                # Prose in a comment may legitimately name the old value while
                # explaining the rename; only executable lines are pinned.
                code = '\n'.join(
                    line for line in src.splitlines()
                    if not line.lstrip().startswith('#'))
                self.assertNotIn(
                    self.RENAMED_FROM, code,
                    f'{path.name} 仍带旧分类名（半程改名：chips 会退回英文）')

    def test_every_seeded_article_uses_a_declared_category(self):
        """Seed rows are the production source of truth; a value outside
        `choices` renders as a chip that `?category=` filtering can never
        match, so the article shows up in "All News" and in no bucket."""
        from pages.views.data_loaders import _load_seed
        allowed = self._choices()
        for article in _load_seed()['news']:
            with self.subTest(slug=article['slug']):
                category = article.get('category')
                self.assertIn(
                    category, allowed,
                    f'{article["slug"]} 的 category={category!r} 不在 NEWS_CATEGORIES')

    def test_the_hktex_article_is_filed_under_the_renamed_category(self):
        """The rename exists for this article -- it is the exhibition notice
        that was being labelled corporate news."""
        from pages.views.data_loaders import _load_seed
        article = next(a for a in _load_seed()['news'] if a['slug'] == HKTEX)
        self.assertEqual('Exhibition Information', article.get('category'))

    def test_both_seed_mirrors_agree_on_the_category(self):
        """`_load_seed()` prefers `pages/seed_data.py` over `seed_data.json`, so
        a JSON-only edit never reaches production while local renders look right.
        This is the exact failure that produced two false-green probe rounds in
        v1.10.9."""
        import json
        path = settings.BASE_DIR / 'seed_data.json'
        from_js = next(a for a in json.loads(path.read_text(encoding='utf-8'))['news']
                       if a['slug'] == HKTEX)
        from pages.views.data_loaders import _load_seed
        artifact = next(a for a in _load_seed()['news'] if a['slug'] == HKTEX)
        self.assertEqual(
            from_js['category'], artifact['category'],
            'seed_data.json 与 pages/seed_data.py 的 category 不一致——'
            '本地看 JSON 对，线上读构建产物不对')


class NewsCoverCentringTests(SimpleTestCase):
    """v1.10.10 — the cover must sit centred, and this is a pixel question.

    v1.10.9 scaled the whole 1470px screenshot and pasted it at x=0. The file's
    alpha channel only covers x=2..775, so 695px -- 47% of the canvas -- was
    transparent, and that transparent block was baked into the WebP as a white
    slab on the right. An editor saw "the picture is too far left, there is a
    lot of empty space on the right".

    Geometry assertions cannot see that: the canvas *was* a clean 1600x900 and
    `NewsCoverGeometryTests` stayed green. Only inked-pixel measurement catches
    it, so this reads the decoded image rather than the file header.
    """

    #: Anything this close to white counts as bare canvas.
    BLANK = 250
    #: Tolerance for antialiasing and lossy ringing at the content edge (the
    #: measured cover sits at L=0 / R=1, i.e. off by one column).
    MARGIN_TOLERANCE_PX = 4

    def _cover(self):
        from pages.views.data_loaders import _load_seed
        article = next(a for a in _load_seed()['news'] if a['slug'] == HKTEX)
        return settings.BASE_DIR / 'static' / article['image']

    def _content_box(self):
        """(left, right, top, bottom) inked pixel bounds, inclusive."""
        from PIL import Image
        with Image.open(self._cover()) as im:
            rgb = im.convert('RGB')
            w, h = rgb.size
            px = rgb.load()

            def inked(px_, limit):
                return min(px_) < limit

            cols = [x for x in range(w)
                    if any(inked(px[x, y], self.BLANK) for y in range(h))]
            rows = [y for y in range(h)
                    if any(inked(px[x, y], self.BLANK) for x in range(w))]
            return cols[0], cols[-1], rows[0], rows[-1], w, h

    def test_the_content_is_centred_horizontally(self):
        left, right, _top, _bottom, w, _h = self._content_box()
        left_margin, right_margin = left, w - 1 - right
        self.assertLessEqual(
            abs(left_margin - right_margin), self.MARGIN_TOLERANCE_PX,
            f'封面左右留白不对称：左 {left_margin}px / 右 {right_margin}px'
            '（v1.10.9 的故障模式：整图左对齐 + 右侧 47% 透明区）')

    def test_the_content_actually_spans_the_canvas(self):
        """Symmetry alone is satisfiable by a centred postage stamp. The cover
        is a wide wordmark strip; it has to use the width it is given."""
        left, right, _top, _bottom, w, _h = self._content_box()
        self.assertLessEqual(
            left, self.MARGIN_TOLERANCE_PX,
            f'封面左侧空出 {left}px，横幅没有铺满画幅')
        self.assertLessEqual(
            w - 1 - right, self.MARGIN_TOLERANCE_PX,
            f'封面右侧空出 {w - 1 - right}px，横幅没有铺满画幅')

    def test_the_content_is_centred_vertically_too(self):
        """Same reason vertically: the strip is matted into 16:9, and a strip
        pinned to the top reads as a layout bug rather than a matte."""
        _left, _right, top, bottom, _w, h = self._content_box()
        top_margin, bottom_margin = top, h - 1 - bottom
        self.assertLessEqual(
            abs(top_margin - bottom_margin), self.MARGIN_TOLERANCE_PX + 6,
            f'封面上下留白不对称：上 {top_margin}px / 下 {bottom_margin}px')

