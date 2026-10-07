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
import shutil
import unittest.mock as mock

from django.conf import settings
from django.test import RequestFactory, TestCase

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
