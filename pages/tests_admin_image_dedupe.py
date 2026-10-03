"""admin 上传去重守卫 —— v1.9.10

背景（2026-10-04 实测）：`pages/admin/product.py::_sync_product_images`
旧实现对每个字段**无条件** `shutil.copy2` 到 per-slug 目录，于是同一张图被多个产品
各传一次 = 多份字节相同的副本（全站 21 组 / 30 个副本 / 2.02 MB）。
人工删副本没用 —— 后台下次上传立刻反弹，所以修法是在**写入前**按内容哈希查表
（`_static_copy_deduped`）：命中就只记路径不写盘。

本文件锁死这条不变量。
"""
import os
import shutil

from django.conf import settings
from django.test import SimpleTestCase

from pages.admin.product import (
    _static_copy_deduped,
    _static_image_hash_index,
    reset_static_image_hash_index,
)

BASE_DIR = settings.BASE_DIR
# 已存在的真源图片（内容哈希必定命中）
KNOWN_FILE = 'static/images/products/m-series/certifications-ul-dlc-gs-ce-ip66.webp'
PROBE_DIR = os.path.join(BASE_DIR, 'static', 'images', '_dedupe_probe')


class AdminImageDedupeTests(SimpleTestCase):
    """上传同一份内容时：复用既有文件，不写新副本。"""

    def setUp(self):
        super().setUp()
        reset_static_image_hash_index()
        os.makedirs(PROBE_DIR, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(PROBE_DIR, ignore_errors=True)
        reset_static_image_hash_index()
        super().tearDown()

    def test_identical_content_is_reused_not_copied(self):
        """传一张磁盘上已有的图 → 复用原路径，**不在目标目录写新文件**。"""
        src = os.path.join(BASE_DIR, KNOWN_FILE)
        self.assertTrue(os.path.exists(src), f'探针前提变化：{KNOWN_FILE} 不见了')

        rel, reused = _static_copy_deduped(src, PROBE_DIR, 'probe-cert.webp')

        self.assertTrue(reused, '内容相同却没走复用分支（副本会反弹）')
        self.assertNotEqual(rel, 'images/_dedupe_probe/probe-cert.webp',
                            '又写了一份新副本')
        self.assertTrue(
            os.path.exists(os.path.join(BASE_DIR, 'static', rel)),
            f'复用到的路径在真源里不存在：{rel}')
        self.assertFalse(
            os.path.exists(os.path.join(PROBE_DIR, 'probe-cert.webp')),
            '目标目录不该出现新文件')

    def test_reuse_prefers_the_same_filename(self):
        """复用时优先挑同名文件 —— URL 保持可预期，不会莫名其妙换名。"""
        src = os.path.join(BASE_DIR, KNOWN_FILE)
        # 目标文件名与已存在文件同名
        rel, reused = _static_copy_deduped(
            src, PROBE_DIR, 'certifications-ul-dlc-gs-ce-ip66.webp')
        self.assertTrue(reused)
        self.assertEqual(os.path.basename(rel),
                         'certifications-ul-dlc-gs-ce-ip66.webp', rel)

    def test_unique_content_is_still_copied(self):
        """内容确实不同 → 正常拷贝，不能吞掉上传。

        ⚠️ src 必须放在 `static/images/` **之外**（真实上传走 `media/`）：
        放进扫描树里会被哈希索引收录，于是「自己命中自己」被判成重复
        ——第一版就是这么误报的。
        """
        import tempfile
        tmp = tempfile.mkdtemp(prefix='dedupe-src-')
        self.addCleanup(shutil.rmtree, tmp, True)
        src = os.path.join(tmp, 'src-unique.webp')
        with open(src, 'wb') as fh:
            fh.write(os.urandom(4096))          # 随机内容，哈希必然不命中
        dst_dir = os.path.join(PROBE_DIR, 'out')
        rel, reused = _static_copy_deduped(src, dst_dir, 'unique.webp')
        self.assertFalse(reused, '独有内容被误判成重复')
        self.assertEqual(rel, 'images/_dedupe_probe/out/unique.webp')
        self.assertTrue(os.path.exists(os.path.join(dst_dir, 'unique.webp')))

    def test_index_only_trusts_the_true_source(self):
        """哈希索引只认 `static/`，绝不并入 `staticfiles/` 陈旧快照。

        与 `views.utils._list_static_dir` 同一条铁律：混入陈旧快照会让旧哈希副本
        压过刚上传的新图（2026-10-03 事故）。
        """
        index = _static_image_hash_index()
        self.assertGreater(len(index), 50, '索引几乎是空的 —— 扫描范围不对')
        bad = []
        for paths in index.values():
            for rel in paths:
                if not rel.startswith('images/'):
                    bad.append(rel)
                elif not os.path.exists(os.path.join(BASE_DIR, 'static', rel)):
                    bad.append(rel)
        self.assertEqual(bad, [], f'索引里混进了非真源/不存在的路径：{bad[:10]}')
