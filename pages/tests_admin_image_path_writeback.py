"""守卫：后台保存产品后，DB 里的图片路径必须能解析到 ``static/`` 真实文件。

🔴 根因（v1.10.24 修复）：``ImageField.upload_to`` 决定上传落点
（``products/`` / ``products/gallery/``），Django 把那个相对路径自动存进 DB；
而 ``_sync_product_images()`` 把文件复制到 ``static/images/products/<slug>/``。
两者结构不同 ⇒ DB 路径指向磁盘上不存在的目录 ⇒ 前台 ``srcset`` 全 404
（主图裂图）。此前 ``seed_paths`` 算完就丢弃、从不回写，故每传一次图复现一次。

覆盖生产真正走的两个钩子：
  - ``ProductAdmin._sync_product_images()``  → image/banner/dimension/beam_angle
  - ``ProductAdmin.save_related()``          → inline gallery（在 save_formset 之后）

⚠️ 本测试会真的往 ``static/images/products/<slug>/`` 写样本图，因此：
  ① 用唯一 slug 便于清理；② ``_sync_seed_files`` 必须 mock 掉，
  否则测试会覆盖真实的 ``seed_data.json``。
"""
import os
import random
import shutil
import tempfile
import unittest.mock as mock

from django.conf import settings
from django.test import RequestFactory, TestCase, override_settings

from pages.models import Product, ProductImage

DIAG_SLUG = 'zz-diag-writeback'


def _static_exists(rel_path):
    """DB 路径（如 ``images/products/x/y.webp``）是否在 ``static/`` 下真实存在。"""
    if not rel_path:
        return False
    static_root = os.path.join(settings.BASE_DIR, 'static')
    stem, _ext = os.path.splitext(rel_path.replace('\\', '/'))
    for e in ('.webp', '.jpg', '.jpeg', '.png', '.gif', '.avif'):
        if os.path.isfile(os.path.join(static_root, stem + e)):
            return True
    return False


def _any_product_image():
    """取 static/images/products 下任意一张样本图（期望值从磁盘派生，铁律 #7）。"""
    root = os.path.join(settings.BASE_DIR, 'static', 'images', 'products')
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != '_variants']
        for fn in sorted(filenames):
            if fn.lower().endswith(('.webp', '.jpg', '.png')):
                return os.path.join(dirpath, fn)
    return None


def _registered_product_admin():
    """取已注册的 ProductAdmin 实例（避免重复 register 触发 AlreadyRegistered）。"""
    from django.contrib import admin as dj_admin
    return dj_admin.site._registry[Product]


class _FakeForm:
    """``save_related`` 只需要 ``instance`` 与 ``save_m2m``。"""

    def __init__(self, instance):
        self.instance = instance

    def save_m2m(self):
        pass


class AdminImagePathWritebackTest(TestCase):
    def setUp(self):
        self.admin_obj = _registered_product_admin()
        self.fixture = _any_product_image()
        if not self.fixture:
            self.skipTest('static/images/products 下没有可用样本图')
        self.slug = DIAG_SLUG
        self.static_dir = os.path.join(
            settings.BASE_DIR, 'static', 'images', 'products', self.slug)
        self.media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
        os.makedirs(self.media_dir, exist_ok=True)
        self.product = Product.objects.create(
            slug=self.slug, name='diag writeback', category='AREA_SITE',
            page_layout='detail')
        self._sync_patch = mock.patch.object(
            type(self.admin_obj), '_sync_seed_files', lambda self, request=None: None)
        self._sync_patch.start()
        self.addCleanup(self._sync_patch.stop)

    def tearDown(self):
        ProductImage.objects.filter(product=self.product).delete()
        Product.objects.filter(pk=self.product.pk).delete()
        # 清理本测试可能复制到 static/ 的样本
        if os.path.isdir(self.static_dir):
            shutil.rmtree(self.static_dir, ignore_errors=True)
        for tmp in (os.path.join(self.media_dir, 'diag-fixture.webp'),
                    os.path.join(self.media_dir, 'gallery', 'diag-gallery.webp')):
            if os.path.isfile(tmp):
                os.remove(tmp)

    def _stage_media(self, rel_name):
        """把样本图放进 media/ 的指定相对位置，返回该绝对路径。"""
        abs_path = os.path.join(settings.MEDIA_ROOT, rel_name)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        shutil.copy2(self.fixture, abs_path)
        self.addCleanup(lambda: os.path.isfile(abs_path) and os.remove(abs_path))
        return abs_path

    def test_image_field_is_written_back_to_a_resolvable_path(self):
        """``_sync_product_images`` 必须把 static 相对路径写回 DB。"""
        self._stage_media('products/diag-fixture.webp')
        self.product.image = 'products/diag-fixture.webp'
        self.product.save(update_fields=['image'])

        self.admin_obj._sync_product_images(self.product)

        self.product.refresh_from_db()
        stored = self.product.image.name
        self.assertTrue(
            _static_exists(stored),
            'image 写回的路径在 static/ 下找不到对应文件: %r' % stored)
        self.assertIn(
            'images/products/%s/' % self.slug, stored,
            '写回路径未落到 static/images/products/<slug>/ 约定下: %r' % stored)

    def test_gallery_is_written_back_in_save_related(self):
        """Gallery inline 只在 save_formset 之后存在，必须在 save_related 写回。"""
        self._stage_media('products/gallery/diag-gallery.webp')
        img = ProductImage.objects.create(
            product=self.product, image='products/gallery/diag-gallery.webp', order=99)

        request = RequestFactory().post('/admin/')
        self.admin_obj.save_related(request, _FakeForm(self.product), [], change=True)

        img.refresh_from_db()
        self.assertTrue(
            _static_exists(img.image.name),
            'gallery 写回的路径在 static/ 下找不到对应文件: %r' % img.image.name)

    def test_mutation_probe_writeback_to_wrong_dir_turns_guard_red(self):
        """变异探针：把路径写回到错误目录，确认守卫生效（非空转）。

        做法：patch ``_static_copy_deduped`` 返回一个**磁盘上不存在**的路径
        （模拟写回逻辑指向了错误目录），然后跑与 test_image_field_… 完全相同的
        断言 —— 期望它失败。断言变红即证明守卫真的在检测「路径不可解析」。
        """
        self._stage_media('products/diag-fixture.webp')
        self.product.image = 'products/diag-fixture.webp'
        self.product.save(update_fields=['image'])

        bogus = 'images/products/wrong-dir-should-not-exist/diag-fixture.webp'
        with mock.patch(
            'pages.admin.product._static_copy_deduped',
            return_value=(bogus, True),
        ):
            self.admin_obj._sync_product_images(self.product)
            self.product.refresh_from_db()
            stored = self.product.image.name
            # 变异后 DB 被写成磁盘不存在的路径 → 守卫生效
            self.assertEqual(
                stored, bogus,
                '探针失效：写回未被 patch 拦截，变异没生效')
            self.assertFalse(
                _static_exists(stored),
                '探针 BROKEN：指向不存在目录的路径竟被判定为可解析')
            # 这正是主守卫的断言 —— 它必须在这里失败
            with self.assertRaises(AssertionError):
                self.assertTrue(_static_exists(stored))


# 🔴 期望值一律硬编码为「产品决策」而非从实现派生（铁律 4b）：
# 360 = 新闻/产品卡片 1x，720 = 卡片 2x，1248 = 站点最大渲染宽度（hero/详情主图）。
VARIANT_WIDTHS = (360, 720, 1248)
VARIANT_SEP = '~'          # URL 安全的宽度标记（早期 '@' 会被 static() 转义成 %40）
VARIANT_ROOT = '_variants'  # 镜像目录：变体绝不能落在源图旁边（会污染 gallery 枚举）


class AdminImageVariantHookTests(TestCase):
    """守卫 v1.10.27：后台保存新图片后必须**自动生成** srcset 变体。

    根因（fl6m / fl9m 两次实测）：批次 C 的响应式变体是构建期产物，
    ``_sync_product_images`` 只把上传复制到 ``static/``，从不为新文件名补变体
    ⇒ 本地预览必裂（浏览器优先取 srcset 候选，全部 404）。

    ⚠️ 非假绿的关键设计（否则守卫会恒绿、白跑）：
      ① 用**随机噪声合成图**当上传样本 —— ``_static_copy_deduped`` 按内容 md5
         复用既有文件，若拿真源图当样本，目标路径会复用已存在的图（其变体早已
         存在），守卫就会「什么都不做也是绿的」。
      ② 独立 ``tmp`` BASE_DIR/MEDIA_ROOT —— 测试根本不碰仓库真实 static/ 树。
      ③ 保存前断言变体目录尚不存在（前提检查，避免前置污染导致假绿）。
      ④ 文件内探针：禁用钩子后再跑同一断言必须**拿不到**任何变体。
    """

    def setUp(self):
        self.admin_obj = _registered_product_admin()
        from pages.admin.product import reset_static_image_hash_index
        reset_static_image_hash_index()
        self.addCleanup(reset_static_image_hash_index)

        self.tmp_root = tempfile.mkdtemp(prefix='zz-variant-hook-')
        self.static_root = os.path.join(self.tmp_root, 'static')
        self.media_root = os.path.join(self.tmp_root, 'media')
        os.makedirs(self.static_root, exist_ok=True)
        os.makedirs(self.media_root, exist_ok=True)

        self._override = override_settings(
            BASE_DIR=self.tmp_root, MEDIA_ROOT=self.media_root)
        self._override.enable()
        self.addCleanup(self._override.disable)
        self.addCleanup(lambda: shutil.rmtree(self.tmp_root, ignore_errors=True))

        # 后台保存的两个副作用与本守卫无关，且会把真实 seed_data.json 覆盖 /
        # 触发耗时的 collectstatic ⇒ 一律 mock 掉。
        self._seed_patch = mock.patch.object(
            type(self.admin_obj), '_sync_seed_files', lambda self, request=None: None)
        self._seed_patch.start()
        self.addCleanup(self._seed_patch.stop)
        self._collect_patch = mock.patch(
            'pages.admin.product.subprocess.run', lambda *a, **k: None)
        self._collect_patch.start()
        self.addCleanup(self._collect_patch.stop)

        self.slug = 'zz-diag-variants'
        self.product = Product.objects.create(
            slug=self.slug, name='diag variants', category='AREA_SITE',
            page_layout='detail')

    # --- helpers ---

    def _stage_unique_image(self, rel_name, size=(1400, 900)):
        """生成一张**内容唯一**的 webp 放进 media/，充当本次上传。"""
        try:
            from PIL import Image
        except ImportError:  # pragma: no cover
            self.skipTest('需要 Pillow')
        abs_path = os.path.join(self.media_root, rel_name)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        Image.effect_noise(size, random.randint(1, 250)).convert('RGB').save(
            abs_path, 'WEBP')
        return abs_path

    def _expected_variant_paths(self, source_rel):
        """期望值（硬编码约定）：``images/_variants/<同路径>/<名字>~<w>w.<ext>``。"""
        self.assertTrue(
            source_rel.startswith('images/'),
            '源路径应已是 static 相对路径: %r' % source_rel)
        mirrored = source_rel.replace('images/', 'images/%s/' % VARIANT_ROOT, 1)
        stem, ext = os.path.splitext(mirrored)
        out = {}
        for w in VARIANT_WIDTHS:
            rel = '%s%s%dw%s' % (stem, VARIANT_SEP, w, ext)
            # 逐段 join：期望值里不能出现混合分隔符（否则 Windows 下
            # split(os.sep) 出一个 ``images/_variants/...`` 整块，后续断言失真）
            out[w] = os.path.join(self.static_root, *rel.split('/'))
        return out

    def _assert_variants_generated(self, source_rel):
        """主断���：三档变体必须都已落在磁盘且非空。"""
        variants = self._expected_variant_paths(source_rel)
        for width, abs_path in variants.items():
            self.assertTrue(
                os.path.isfile(abs_path),
                '缺 %dw 变体（后台保存没自动生成 ⇒ 本地预览必裂）: %s' % (width, abs_path))
            self.assertGreater(
                os.path.getsize(abs_path), 0,
                '%dw 变体是空文件（生成失败且被静默吞掉）: %s' % (width, abs_path))
        return variants

    def _assert_no_variant_yet(self):
        """前提检查：保存前变体目录必须不存在（否则本守卫就是假绿）。"""
        variant_root = os.path.join(self.static_root, 'images', VARIANT_ROOT)
        self.assertFalse(
            os.path.isdir(variant_root),
            '探针前提失效：变体目录在保存前就已存在，守卫可能恒绿')

    # --- 守卫 ---

    def test_main_image_save_generates_all_variant_widths(self):
        """``_sync_product_images`` 必须给新主图补出三档变体。"""
        self._stage_unique_image('products/diag-main.webp')
        self.product.image = 'products/diag-main.webp'
        self.product.save(update_fields=['image'])

        self._assert_no_variant_yet()
        self.admin_obj._sync_product_images(self.product)

        self.product.refresh_from_db()
        self._assert_variants_generated(self.product.image.name)

    def test_gallery_save_generates_all_variant_widths(self):
        """``save_related`` 必须给新轮播图（gallery inline）补出三档变体。"""
        self._stage_unique_image('products/gallery/diag-gallery.webp')
        img = ProductImage.objects.create(
            product=self.product, image='products/gallery/diag-gallery.webp',
            order=99)

        self._assert_no_variant_yet()
        request = RequestFactory().post('/admin/')
        self.admin_obj.save_related(request, _FakeForm(self.product), [], change=True)

        img.refresh_from_db()
        self._assert_variants_generated(img.image.name)

    def test_variants_land_in_mirrored_tree_never_beside_the_source(self):
        """变体必须落在 ``_variants/`` 镜像树里，绝不能和源图同目录。

        与源图同目录会被 gallery / cover 的 ``os.listdir`` 枚举当作普通图片，
        变成幽灵轮播图（这正是镜像目录存在的全部理由）。
        """
        self._stage_unique_image('products/diag-mirror.webp')
        self.product.image = 'products/diag-mirror.webp'
        self.product.save(update_fields=['image'])
        self.admin_obj._sync_product_images(self.product)
        self.product.refresh_from_db()

        for width, abs_path in self._expected_variant_paths(
                self.product.image.name).items():
            self.assertIn(
                VARIANT_ROOT, abs_path.split(os.sep),
                '%dw 变体离开镜像树: %s' % (width, abs_path))

        source_dir = os.path.join(self.static_root, 'images', 'products', self.slug)
        leaked = [fn for fn in os.listdir(source_dir)
                  if '%s%sw' % (VARIANT_SEP, '') in fn or any(
                      '%s%dw' % (VARIANT_SEP, w) in fn for w in VARIANT_WIDTHS)]
        self.assertEqual(
            leaked, [],
            '变体泄漏到源图目录（会污染 gallery 枚举）: %s' % leaked)

    def test_expected_widths_match_the_implementation_contract(self):
        """实现 == 期望（铁律 4b 的另一半）：档位变了必须先改上面的硬编码期待。"""
        from pages.image_variants import SRCSET_WIDTHS
        self.assertEqual(
            tuple(SRCSET_WIDTHS), VARIANT_WIDTHS,
            'SRCSET_WIDTHS 与本文件的硬编码期望值不一致 —— 先确认这是有意的产品变更，'
            '再同步更新 VARIANT_WIDTHS（否则本文件的守卫会变成另一回事）')

    # --- 文件内探针 ---

    def test_probe_no_variant_when_the_hook_is_disabled(self):
        """变异探针：禁用钩子后，同一断言必须**拿不到**任何变体。

        这证明变体确实来自新加的钩子，而不是别的地方（例如
        ``_static_copy_deduped`` 顺带产出、或目录早已存在）顺出的。
        """
        self._stage_unique_image('products/diag-probe.webp')
        self.product.image = 'products/diag-probe.webp'
        self.product.save(update_fields=['image'])

        with mock.patch(
            'pages.admin.product._ensure_variants_for_static_rels',
            lambda *a, **k: 0,
        ):
            self.admin_obj._sync_product_images(self.product)
            self.product.refresh_from_db()

        generated = [p for p in self._expected_variant_paths(
            self.product.image.name).values() if os.path.isfile(p)]
        self.assertEqual(
            generated, [],
            '探针 BROKEN：钩子被禁用后仍生成了变体 ⇒ 主守卫可能恒绿（假绿）')
