"""响应式图片 srcset 守卫 —— 批次 C (v1.10.18)

背景（实测结论，2026-10-06）
---------------------------
`static/images/` 下 262 张源图里绝大多数是 1920px 宽，而列表卡在桌面端
的实际渲染宽度只有 ~342px（实测：`(1280-64-26*2)/3 - 2 - 22*2 = 342.00px`）。
单 `src` 意味着**每张卡片都在下载 1920px 原图**再让浏览器缩小 —— 4~10 倍
的无效字节，且 2x/3x retina 上反而模糊。

批次 C 的修法：为每张源图生成 360/720/1248 三档变体，模板输出
`<img srcset sizes>`，让浏览器按 DPR × CSS 槽宽自选。

本守卫锁死的不变量
----------------
1. **变体不能落在源图旁边。** 🔴 真实踩过的坑：`_variant_abs()` 早期用
   `src_abs.replace('static/images/', ...)` 拼路径，Windows 下
   `os.path.join` 产出反斜杠 ⇒ replace 静默 no-op ⇒ 786 个 `@<w>w.webp`
   被写进 `static/images/<cat>/<slug>/`。而
   `pages/views/utils.py` 的画廊/封面枚举是 `os.listdir` per-slug 目录的
   ⇒ 变体会被当成真实图集图片被列表化和可能选为封面。
   现在 `_variant_abs()` 按路径组件切分（分隔符无关），并在
   `ensure_variants()` 入口加了硬闸：变体路径不含 `_variants` 组件就
   **抛 ValueError**，绝不静默产出 0 个。
2. **模板真的接上了 filter。** 只断言"模板里有 srcset 字样"会被
   `{% load %}` 缺失 / filter 名拼错 / 属性在注释里骗过去；这里断言
   **渲染后的 HTML**。
3. **变体文件真的在磁盘上。** 断言由 `_load_seed()` / 实际目录派生，
   不写死数量（铁律 7）。
4. **URL 反推 + 哈希剥离。** 生产 `image_url` 可能带
   ManifestStaticFilesStorage 哈希段；变体 URL 必须走 Django `static()`
   才能同时适配 dev(无哈希)/prod(有哈希)。
"""
import os
import re

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.templatetags.static import static
from django.urls import reverse
from django.utils import translation

from pages.image_variants import (
    CATEGORIES,
    SRCSET_WIDTHS,
    _VARIANT_ROOT,
    _variant_abs,
    build_src,
    build_srcset,
    canonical_rel_from_url,
    ensure_variants,
    strip_hash_suffix,
    variant_rel,
)

_IMAGES_DIR = os.path.join(str(settings.BASE_DIR), 'static', 'images')
_VARIANTS_DIR = os.path.join(_IMAGES_DIR, _VARIANT_ROOT)

# 卡片内容框实测宽度见模块 docstring；sizes 里用 vw 表达同一意图
# 🔴 Hard-coded on purpose. An earlier version imported CATEGORIES / asserted
# against SRCSET_WIDTHS from the implementation, which made both checks
# tautologies: mutating either constant moved the expectation with it and the
# guards stayed green (mutation probes P4 and P6 proved it). Widths and coverage
# are product decisions (360 = card 1x, 720 = card 2x, 1248 = max render
# width), so the test states them independently of the code.
_EXPECTED_CATEGORIES = ('products', 'projects', 'news', 'products_page')
_EXPECTED_WIDTHS = (360, 720, 1248)
_CATEGORIES = _EXPECTED_CATEGORIES


def _markup(text):
    """剥掉 HTML / Django / CSS 注释，避免断言被自己写的注释反噬（铁律 13）。"""
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\{#.*?#\}', '', text, flags=re.S)
    text = re.sub(r'\{% comment %\}.*?\{% endcomment %\}', '', text, flags=re.S)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return text


def _tag_imgs(html):
    """返回渲染 HTML 里所有 <img ...> 开标签。"""
    return re.findall(r'<img\b[^>]*>', _markup(html), flags=re.I)


def _has_srcset(img_tag):
    return re.search(r'\bsrcset\s*=\s*"([^"]*)"', img_tag, flags=re.I) is not None


def _srcset_widths(img_tag):
    """Parse ONLY the width descriptors out of a srcset attribute.

    A srcset is a comma-separated candidate list where each candidate is
    ``<url> <descriptor>``. The URL itself ends in the ``~<w>w`` marker, so a
    naive ``(\\d+)w`` regex over the whole attribute double-counts (once from
    the URL, once from the descriptor). Split candidates and read the trailing
    token instead. The ``(?<![\\d%])`` guard additionally rejects percent-encoded
    markers (``%40360w`` used to parse as a bogus 40360w descriptor).
    """
    m = re.search(r'\bsrcset\s*=\s*"([^"]*)"', img_tag, flags=re.I)
    if not m:
        return []
    widths = []
    for candidate in m.group(1).split(','):
        tokens = candidate.split()
        if len(tokens) < 2:
            continue
        dm = re.fullmatch(r'(?<![\d%])(\d+)w', tokens[-1])
        if dm:
            widths.append(int(dm.group(1)))
    return sorted(widths)


class VariantLayoutTests(SimpleTestCase):
    """纯函数层：路径推导 / 哈希剥离 / 变体目录隔离。"""

    def test_variant_path_never_lands_next_to_source(self):
        """🔴 分隔符回归：Windows 反斜杠不得让镜像拼装退化。

        这是 786 文件污染事故的根因。逐个平台形态都断言变体目录里
        一定含 `_variants`，且**不等于**源目录。
        """
        for src in (
            os.path.join('E:\\proj', 'static', 'images', 'products', 'rt410', 'a.webp'),
            'static/images/projects/foo/bar.webp',
            '/abs/posix/static/images/news/slug/cover.png',
        ):
            with self.subTest(src=src):
                v = _variant_abs(src, 360)
                self.assertIn(_VARIANT_ROOT, v.split(os.sep),
                              'variant escaped the _variants tree: %r -> %r' % (src, v))
                self.assertNotEqual(os.path.dirname(v), os.path.dirname(src))
                self.assertIn('~360w', v)

    def test_ensure_variants_raises_when_layout_escapes(self):
        """闸必须**大声失败**，不能静默返回 []（静默 = 假绿）。"""
        import tempfile

        from PIL import Image

        d = tempfile.mkdtemp()
        src = os.path.join(d, 'x.webp')  # 路径里没有 images 组件
        Image.new('RGB', (1920, 1080), (10, 20, 30)).save(src, 'WEBP')
        with self.assertRaises(ValueError):
            ensure_variants(src)

    def test_hash_suffix_is_stripped_once(self):
        self.assertEqual(strip_hash_suffix('rt410-a.abc123de.webp'), 'rt410-a.webp')
        # 幂等：已无哈希的名字不能被再剥一刀
        self.assertEqual(strip_hash_suffix('rt410-a.webp'), 'rt410-a.webp')
        # 目录名里的点不该被当成哈希
        self.assertEqual(
            strip_hash_suffix('my.project.webp'), 'my.project.webp')

    def test_canonical_rel_reverses_static_url(self):
        self.assertEqual(
            canonical_rel_from_url(
                '/static/images/products/rt410/rt410-a.abc123de.webp'),
            'images/products/rt410/rt410-a.webp')
        # 非 static / 空 URL → 空串（模板据此省略属性）
        self.assertEqual(canonical_rel_from_url(''), '')
        self.assertEqual(canonical_rel_from_url(None), '')

    def test_media_and_cdn_urls_get_no_variant(self):
        """🔴 v1.10.23 — only ``static/images/`` has variant siblings.

        The variant generator writes exclusively under
        ``static/images/_variants/``. A media upload or a CDN URL therefore has
        no ``~360w`` file anywhere, and the earlier version passed its path
        straight through — ``static()`` then produced
        ``/static/media/products_page/VSP9M-01~360w.webp``, a 404. The browser
        picks a candidate from ``srcset`` rather than the ``src`` beside it, so
        the image was visibly broken on ``/products/`` and on the stadium page
        (whose VSP card resolves through the media fallback locally).

        Returning '' makes ``build_srcset`` emit nothing, the template omits the
        attribute, and the browser falls back to the working ``src``.
        """
        for url in ('/media/products_page/VSP9M-01.webp',
                    'media/products_page/VSP9M-01.webp',
                    'https://cdn.example.com/a.webp',
                    '//cdn.example.com/a.webp'):
            with self.subTest(url=url):
                self.assertEqual(
                    canonical_rel_from_url(url), '',
                    '%s has no local variant and must not be resolved to one'
                    % url)
                self.assertEqual(
                    build_srcset(url), '',
                    '%s produced a srcset pointing at files that do not exist'
                    % url)

    def test_a_relative_static_path_still_resolves(self):
        """The fix must not swallow the seed-shaped relative form."""
        self.assertEqual(
            canonical_rel_from_url('images/products/rt410/rt410-a.webp'),
            'images/products/rt410/rt410-a.webp')
        self.assertNotEqual(
            build_srcset('images/products/rt410/rt410-a.webp'), '')

    def test_implementation_covers_every_declared_category(self):
        """Implementation must cover exactly the categories we promise to cover.

        Without this, dropping a category is invisible: the on-disk tests would
        scan the same reduced set the generator walks (tautology).
        """
        for cat in _EXPECTED_CATEGORIES:
            self.assertIn(
                cat, CATEGORIES,
                'category %r is expected to get responsive variants but is not '
                'in pages.image_variants.CATEGORIES' % cat)
        self.assertTrue(
            set(CATEGORIES) >= set(_EXPECTED_CATEGORIES),
            'CATEGORIES lost coverage: %s' % (set(_EXPECTED_CATEGORIES) - set(CATEGORIES),))

    def test_implementation_ships_the_declared_widths(self):
        """The shipped width ladder must match the declared one, exactly.

        Guards the srcset contract: dropping 1248 would silently cap every
        hero/lightbox at 720 (probe P6 showed an SRCSET_WIDTHS-derived
        assertion could not see this).
        """
        self.assertEqual(
            tuple(SRCSET_WIDTHS), _EXPECTED_WIDTHS,
            'SRCSET_WIDTHS drifted from the declared responsive ladder')

    def test_no_upscale_for_small_source(self):
        """🔴 A 200px-wide source must NOT be blown up to 1248px.

        Asserted by *running* the generator on a synthetic small image, not by
        inspecting the pre-generated files — mutating the `min(w, src_w)` clamp
        left those files untouched and the guard stayed green (probe P5).
        """
        import tempfile

        from PIL import Image

        d = tempfile.mkdtemp()
        # the path must contain an `images` component for the mirror to work
        img_dir = os.path.join(d, 'images', 'products', 'tiny')
        os.makedirs(img_dir)
        src = os.path.join(img_dir, 'tiny.webp')
        Image.new('RGB', (200, 150), (12, 34, 56)).save(src, 'WEBP')

        created = ensure_variants(src, widths=(360, 720, 1248))
        self.assertTrue(created, 'generator produced no variants for a small source')
        for path in created:
            with Image.open(path) as im:
                vw = im.size[0]
            self.assertEqual(
                vw, 200,
                'small source was UPSCALED to %dpx (must clamp to source width)' % vw)
            self.assertLessEqual(vw, 200)

    def test_variant_rel_mirrors_into_variants_root(self):
        self.assertEqual(
            variant_rel('images/products/x/n.webp', 720),
            'images/_variants/products/x/n~720w.webp')

    def test_build_srcset_uses_static_and_all_widths(self):
        """变体 URL 必须走 `static()`：dev 无哈希、prod 有哈希，统一入口。"""
        url = '/static/images/products/rt410/rt410-a.abc123de.webp'
        out = build_srcset(url)
        self.assertTrue(out)
        for w in _EXPECTED_WIDTHS:
            self.assertIn('%dw' % w, out)
        # 走 static() => 以 STATIC_URL 开头
        self.assertIn(static('images/_variants/products/rt410/rt410-a~720w.webp'), out)

    def test_build_srcset_empty_url_returns_empty(self):
        self.assertEqual(build_srcset(''), '')
        self.assertEqual(build_src(None), '')

    def test_build_src_default_width(self):
        url = '/static/images/products/rt410/rt410-a.webp'
        self.assertIn('~720w', build_src(url))
        self.assertIn('~1248w', build_src(url, 1248))


class VariantOnDiskTests(SimpleTestCase):
    """磁盘层：变体确实存在于隔离目录，且源目录没被污染。"""

    def test_no_variant_file_next_to_source(self):
        """🔴 污染守卫：per-slug 源目录里不允许出现 `@<w>w` 文件。"""
        bad = []
        for cat in _CATEGORIES:
            cat_dir = os.path.join(_IMAGES_DIR, cat)
            if not os.path.isdir(cat_dir):
                continue
            for dirpath, dirnames, filenames in os.walk(cat_dir):
                dirnames[:] = [d for d in dirnames
                               if d not in (_VARIANT_ROOT, '_source', 'processed')]
                for fn in filenames:
                    if re.search(r'[@~]\d+w\.(webp|png|jpg|jpeg)$', fn, re.I):
                        bad.append(os.path.join(dirpath, fn))
        self.assertEqual(
            bad, [],
            'variants leaked into source dirs (breaks gallery/cover enumeration): '
            '%s' % bad[:5])

    def test_variants_exist_for_every_source(self):
        """每个源图的每一档变体都必须在磁盘上（数量从目录派生，不写死）。"""
        if not os.path.isdir(_VARIANTS_DIR):
            self.skipTest('variants not generated yet — run scripts/gen_image_variants.py')
        missing = []
        expected = 0
        for cat in _CATEGORIES:
            cat_dir = os.path.join(_IMAGES_DIR, cat)
            if not os.path.isdir(cat_dir):
                continue
            for dirpath, dirnames, filenames in os.walk(cat_dir):
                dirnames[:] = [d for d in dirnames
                               if d not in (_VARIANT_ROOT, '_source', 'processed')]
                for fn in filenames:
                    if not fn.lower().endswith(
                            ('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                        continue
                    for w in _EXPECTED_WIDTHS:
                        expected += 1
                        v = _variant_abs(os.path.join(dirpath, fn), w)
                        if not os.path.isfile(v):
                            missing.append(v)
        self.assertTrue(expected > 0, 'no source images found — guard would be vacuous')
        self.assertEqual(
            missing, [],
            '%d variant(s) missing (run scripts/gen_image_variants.py): %s'
            % (len(missing), missing[:5]))

    def test_variants_are_never_upscaled(self):
        """变体宽度 = min(档位, 源宽) —— 小图不许被放大糊掉。"""
        if not os.path.isdir(_VARIANTS_DIR):
            self.skipTest('variants not generated yet')
        from PIL import Image

        for cat in _CATEGORIES:
            cat_dir = os.path.join(_IMAGES_DIR, cat)
            if not os.path.isdir(cat_dir):
                continue
            for dirpath, dirnames, filenames in os.walk(cat_dir):
                dirnames[:] = [d for d in dirnames
                               if d not in (_VARIANT_ROOT, '_source', 'processed')]
                for fn in filenames:
                    if not fn.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
                        continue
                    src = os.path.join(dirpath, fn)
                    with Image.open(src) as im:
                        src_w = im.size[0]
                    for w in _EXPECTED_WIDTHS:
                        v = _variant_abs(src, w)
                        if not os.path.isfile(v):
                            continue
                        with Image.open(v) as vim:
                            vw = vim.size[0]
                        self.assertEqual(
                            vw, min(w, src_w),
                            '%s: variant width drifted from min(%d, %d)'
                            % (v, w, src_w))
                        self.assertLessEqual(
                            vw, src_w, '%s was UPSCALED beyond its source' % v)


class RenderedSrcsetTests(SimpleTestCase):
    """🔴 渲染层：断言渲染出的 HTML 真的带 srcset/sizes（铁律 22）。

    只查模板源码会被 `{% load %}` 缺失 / filter 拼错骗过去；必须打真页面。

    🔴 铁律 19：测试库是**空的**，且本地 `IS_VERCEL=False` ⇒ 新闻列表走
    `_get_news_from_db()` ⇒ `articles=[]` ⇒ 模板**正确地**渲染零张卡片。
    那样这条断言会恒绿（假守卫）。所以整组跑在 `IS_VERCEL=True` 下 ——
    这既是**生产真实路径**（生产零 DB 走 seed），也让列表页有内容可断言。
    """

    LIST_URLS = (
        ('en', '/products/'),
        ('en', '/projects/'),
        ('en', '/news/'),
    )

    def _get(self, path, lang='en'):
        with translation.override(lang):
            with override_settings(IS_VERCEL=True):
                return self.client.get(path, HTTP_HOST='localhost').content.decode('utf-8')

    def test_list_pages_cards_carry_srcset(self):
        for lang, path in self.LIST_URLS:
            with self.subTest(path=path):
                html = _markup(self._get(path, lang))
                imgs = _tag_imgs(html)
                self.assertTrue(imgs, 'no <img> rendered on %s' % path)
                # Non-vacuity: the page must actually have rendered repeated
                # card images, otherwise a filter regression could hide behind
                # an empty list (iron rule 19).
                self.assertGreaterEqual(
                    len(imgs), 3,
                    '%s rendered only %d img(s) — likely an empty list, so the '
                    'srcset assertion below would be vacuous' % (path, len(imgs)))
                responsive = [t for t in imgs if _has_srcset(t)]
                self.assertTrue(
                    responsive,
                    '%s rendered %d img(s) but none carried srcset — batch C '
                    'filter is not wired' % (path, len(imgs)))
                for tag in responsive:
                    self.assertEqual(
                        _srcset_widths(tag), sorted(_EXPECTED_WIDTHS),
                        'srcset width descriptors incomplete on %s: %s' % (path, tag[:120]))
                    self.assertIn('sizes=', tag, 'srcset without sizes defeats DPR picking')

    def test_responsive_srcset_urls_are_static_urls(self):
        """srcset 里的 URL 必须以 STATIC_URL 开头（不是裸相对路径）。"""
        html = _markup(self._get('/products/'))
        found = 0
        for tag in _tag_imgs(html):
            m = re.search(r'\bsrcset\s*=\s*"([^"]*)"', tag, flags=re.I)
            if not m:
                continue
            for candidate in m.group(1).split(','):
                url = candidate.strip().split(' ')[0]
                if not url:
                    continue
                found += 1
                self.assertTrue(
                    url.startswith(settings.STATIC_URL),
                    'srcset candidate not a static URL: %r' % url)
                self.assertIn(
                    _VARIANT_ROOT, url,
                    'srcset candidate not pointing at the _variants tree: %r' % url)
                # 🔴 regression: the width marker was '@', which static()
                # percent-encoded to %40, yielding '%40360w'. The browser then
                # sees a 40360w descriptor. The marker must stay literal.
                self.assertNotIn(
                    '%40', url,
                    'width marker got percent-encoded (marker must be URL-safe): %r' % url)
                self.assertNotIn(
                    '%', url,
                    'srcset candidate contains percent-encoding: %r' % url)
                self.assertRegex(
                    url, r'~\d+w\.[a-z]+$',
                    'variant URL must end in the literal ~<width>w marker: %r' % url)
        self.assertTrue(found, 'no srcset candidates found on /products/')

    def test_lazy_loading_preserved_on_cards(self):
        """批次 C 不得回退既有 lazy：首屏下卡片仍需 lazy。"""
        html = _markup(self._get('/products/'))
        tags = [t for t in _tag_imgs(html) if _has_srcset(t)]
        self.assertTrue(tags)
        self.assertTrue(
            all('loading="lazy"' in t for t in tags),
            'a responsive product card lost loading="lazy"')

    def test_detail_pages_carry_srcset(self):
        for path in ('/projects/football-field-led-retrofit/',):
            with self.subTest(path=path):
                url = reverse('project_detail', kwargs={'slug': 'football-field-led-retrofit'})
                html = _markup(self._get(url))
                imgs = _tag_imgs(html)
                self.assertTrue(imgs, 'no <img> rendered on %s' % url)
                self.assertTrue(
                    any(_has_srcset(t) for t in imgs),
                    '%s has no responsive image at all' % url)
