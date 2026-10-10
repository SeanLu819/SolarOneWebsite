"""认证图（cert badge）路径守卫 —— v1.9.8

背景：产品详情页的认证标识图此前有3 个坑，全部由本文件锁死：

1. `DEFAULT_CERT_IMAGE` 曾指向 `m-series-flood-light-certifications.webp`，
   该文件在磁盘上根本不存在（线上实测404）⇒ 所有 `cert_image` 为空的产品
   静默不渲染任何认证图。`test_cert_fallback_points_at_a_real_file` 守卫。
2. 同一张标识图曾以 18 份字节相同的副本躺在 18 个产品目录里。
   `test_cert_image_is_not_duplicated_across_product_dirs` 守卫。
3. seed 里的 `cert_image` 必须是真实存在的文件，否则前台图裂。
   `test_every_seed_cert_image_resolves_to_a_real_file` 守卫。

v1.9.9 追加（第4 个坑，本轮实测修掉）：

4. v1.9.8 把19 份重复副本删掉、把 seed 指向 m-series / rgb-rgbw 两份共享文件，
   **但 DB 里的 `cert_image` 还停在 `products/certs/<name>`**。该路径规范化后是
   `static/images/products/certs/…` —— 这个目录根本不存在 ⇒ `_product_image_url`
   所有静态候选全 MISS ⇒ 回落到 `field.url`（`/media/…`）。本地 runserver 会伺服
   media/ 所以肉眼看不出问题，但 Vercel 的 `excludeFiles` 把 media/ 排除出函数包
   ⇒ **线上 19 个产品的认证徽标全部 404**。本地能显示、生产必坏，是最难自查的一类。
   修法见 `CertDatabasePathTests`：UL 产品的 `cert_image` 清空（走
   `DEFAULT_CERT_IMAGE` 兜底，本来就是 admin 帮助文本写的用法），RGBW 产品的路径
   改成 `products/rgb-rgbw/<file>` 让 `images/{field_name_value}` 候选命中。
   守卫 `test_no_product_cert_image_resolves_only_via_media`。
"""
import unittest
import glob
import hashlib
import io
import json
import os
import re

from django.conf import settings
from django.test import SimpleTestCase, TestCase

from pages.views.enrich import DEFAULT_CERT_IMAGE
from pages.views.utils import _product_image_url, _dict_product_image_url

BASE_DIR = settings.BASE_DIR
SEED_JSON = os.path.join(BASE_DIR, 'seed_data.json')
STATIC_IMAGES = os.path.join(BASE_DIR, 'static', 'images')
STATICFILES = os.path.join(BASE_DIR, 'staticfiles')

# 后台上传 cert 图时 Django 会追加 8 位随机后缀，见 admin/product.py
HASH_SUFFIX_RE = re.compile(r'_[A-Za-z0-9]{8}(?=\.\w+$)')


def _load_seed():
    with io.open(SEED_JSON, encoding='utf-8') as fh:
        return json.load(fh)


def _static_exists(rel_path):
    """一个 seed 路径必须落在**真源** `static/` 里。

    🔴 v1.9.9：原实现还兜底查 `staticfiles/`（collectstatic 的陈旧快照），
    那正是「19 份 cert 副本」能被误判成活路径的原因。真源没有就是没有。
    """
    return os.path.exists(os.path.join(STATIC_IMAGES, rel_path.replace('images/', '', 1)))


class CertFallbackGuardTests(SimpleTestCase):
    def test_cert_fallback_points_at_a_real_file(self):
        """兜底常量必须指向磁盘上真实存在的文件。

        变异探针：把它改回 `m-series-flood-light-certifications.webp` 应变红。
        """
        self.assertTrue(
            _static_exists(DEFAULT_CERT_IMAGE),
            f'DEFAULT_CERT_IMAGE 指向不存在的文件：{DEFAULT_CERT_IMAGE!r} —— '
            f'cert_image 为空的产品将静默不显示认证图')

    def test_no_dead_cert_fallback_literal_remains_in_code(self):
        """曾经写死的错误路径不得以任何形式回到代码里。"""
        dead = 'm-series-flood-light-certifications.webp'
        for rel in ('pages/views/enrich.py',):
            body = io.open(os.path.join(BASE_DIR, rel), encoding='utf-8').read()
            # 允许出现在解释性注释里，但不得作为路径字面量参与逻辑
            code_only = '\n'.join(
                line for line in body.split('\n')
                if not line.lstrip().startswith('#')
            )
            self.assertNotIn(
                dead, code_only,
                f'{rel} 的可执行代码里仍残留已失效的 cert 兜底路径 {dead!r}')

    def test_cert_fallback_is_actually_used_by_a_product_with_empty_cert(self):
        """至少要有一个产品真的依赖兜底，否则这段逻辑是死代码。"""
        seed = _load_seed()
        empties = [p for p in seed.get('products', []) if not (p.get('cert_image') or '')]
        self.assertTrue(
            empties,
            'seed 里已无 cert_image 为空的产品 —— test_cert_fallback_* '
            '失去了被测对象，请重新评估是否删除兜底逻辑')
        # ACCESSORY 类目按设计不显示认证图，其余必须有可用兜底
        non_accessory = [
            p for p in empties
            if (p.get('category') or '').upper() != 'ACCESSORY'
        ]
        self.assertTrue(
            non_accessory or all(
                (p.get('category') or '').upper() == 'ACCESSORY' for p in empties),
            '存在非 ACCESSORY 产品 cert_image 为空且无兜底 —— 认证图会整块消失')


class CertSeedPathTests(SimpleTestCase):
    def test_every_seed_cert_image_resolves_to_a_real_file(self):
        missing = []
        for p in _load_seed().get('products', []):
            ci = p.get('cert_image') or ''
            if not ci:
                continue
            if not _static_exists(ci):
                missing.append((p.get('slug'), ci))
        self.assertEqual(
            missing, [],
            f'seed 里的 cert_image 指向不存在的文件：{missing}')

    def test_cert_image_paths_are_normalised_to_the_shared_file(self):
        """同一张标识图只应有一个路径；所有产品共用它，而不是各指各的副本。

        注意：多个产品指向**同一个**路径是正确的，断言的是「不同路径数 == 1」，
        而不是「产品数 == 1」——后者会误杀共享引用。
        """
        by_basename = {}
        for p in _load_seed().get('products', []):
            ci = p.get('cert_image') or ''
            if not ci:
                continue
            by_basename.setdefault(os.path.basename(ci), set()).add(ci)
        for name, paths in by_basename.items():
            self.assertEqual(
                len(paths), 1,
                f'{name} 被指向了 {len(paths)} 个不同路径：{sorted(paths)} —— '
                f'同一张图应统一到一个路径，否则磁盘上必然出现重复副本')


class CertDuplicateFileTests(SimpleTestCase):
    """磁盘上不应再有字节完全相同的多份 cert 图。"""

    def _cert_files(self):
        pats = ('certifications-ul-dlc-gs-ce-ip66.webp', 'rgbw-interface-*.webp')
        out = []
        for pat in pats:
            out += glob.glob(os.path.join(STATIC_IMAGES, 'products', '*', pat))
        return [os.path.normpath(p) for p in out]

    def test_cert_image_is_not_duplicated_across_product_dirs(self):
        groups = {}
        for p in self._cert_files():
            h = hashlib.md5(io.open(p, 'rb').read()).hexdigest()
            groups.setdefault(h, []).append(os.path.relpath(p, BASE_DIR).replace('\\', '/'))
        dupes = {h: v for h, v in groups.items() if len(v) > 1}
        self.assertEqual(
            dupes, {},
            f'以下 cert 图存在字节相同的重复副本，请让它们指向同一份共享文件：{list(dupes.values())}')

    def test_no_empty_product_dir_left_behind(self):
        """删除重复副本后不应留下空目录（空目录会让部署产物多出无意义条目）。

        `guard-product` 是本次改动之前就已存在的空目录（历史遗留、无任何图片），
        不属于 cert 去重范围，登记在此豁免，避免误报。
        """
        pre_existing_empty = {'guard-product'}
        empties = []
        for d in glob.glob(os.path.join(STATIC_IMAGES, 'products', '*')):
            if not os.path.isdir(d):
                continue
            name = os.path.basename(d)
            if name in pre_existing_empty:
                continue
            has_image = (glob.glob(os.path.join(d, '*.webp'))
                         or glob.glob(os.path.join(d, '*.png'))
                         or glob.glob(os.path.join(d, '*.jpg')))
            if not has_image:
                empties.append(os.path.relpath(d, BASE_DIR).replace('\\', '/'))
        self.assertEqual(
            empties, [],
            f'以下产品图片目录已空，应一并移除：{empties}')


class CertDatabasePathTests(TestCase):
    """🔴 v1.9.9 —— DB 侧 `cert_image` 不得只靠 media 兜底。

    背景见模块 docstring 第4 条：DB 停在 `products/certs/<name>`，而该目录在
    v1.9.8 去重后已不存在⇒ 解析全 MISS ⇒ 回落 `/media/` ⇒ 线上 404。
    本地 runserver 会伺服 media/，所以这类故障**在本地永远看不出来**。

    🔴 读**真实 db.sqlite3 文件**而不是 `Product.objects`：本项目测试库是空的
    （内容真源是 seed/DB 而非 fixtures），走 ORM 拿到0 行 → 断言恒绿 = 假守卫。
    铁律同款：「守卫只测一条路径 = 假绿」。用只读 URI 连接，绝不写。
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import sqlite3
        db = os.path.join(BASE_DIR, 'db.sqlite3')
        if not os.path.exists(db):
            raise unittest.SkipTest(
                'db.sqlite3 不存在（生产为无状态部署）—— 本守卫只适用于有本地 DB 的开发环境')
        cls._con = sqlite3.connect('file:%s?mode=ro' % db.replace('\\', '/'), uri=True)
        cls.rows = cls._con.execute(
            "select slug, cert_image from pages_product "
            "where cert_image is not null and cert_image <> '' order by slug"
        ).fetchall()

    @classmethod
    def tearDownClass(cls):
        try:
            cls._con.close()
        finally:
            super().tearDownClass()

    def test_db_actually_has_products_to_check(self):
        """先证明被测对象存在，否则下面几条断言全是空转。"""
        self.assertGreater(
            len(self.rows), 0,
            'db.sqlite3 里没有任何 cert_image 非空的产品 —— '
            'DB 守卫失去被测对象，请重新评估')

    def test_no_product_cert_image_resolves_only_via_media(self):
        """每个有 cert_image 的产品都必须解析成 /static/ URL。"""
        from types import SimpleNamespace

        offenders = []
        for slug, ci in self.rows:
            fake = SimpleNamespace(
                slug=slug, cert_image=SimpleNamespace(name=str(ci), url='/media/' + str(ci)))
            url = _product_image_url(fake, 'cert_image')
            if not url.startswith('/static/'):
                offenders.append((slug, str(ci), url))
        self.assertEqual(
            offenders, [],
            '以下产品 cert_image 只能回落到 media（线上 404）：'
            f'{offenders}。UL 产品应留空走 DEFAULT_CERT_IMAGE 兜底，'
            'RGBW 产品应指向 products/rgb-rgbw/<file>')

    def test_no_seed_cert_image_resolves_only_via_media(self):
        """同一条规则在 seed 分支（生产真源）上也必须成立。"""
        offenders = []
        for p in _load_seed().get('products', []):
            ci = p.get('cert_image') or ''
            if not ci:
                continue
            url = _dict_product_image_url(ci, p.get('slug', ''))
            if not url.startswith('/static/'):
                offenders.append((p.get('slug'), ci, url))
        self.assertEqual(
            offenders, [],
            f'seed cert_image 只能回落到 media（线上 404）：{offenders}')

    def test_db_and_seed_agree_on_which_products_have_a_cert_badge(self):
        """DB 与 seed 对「哪些产品显式指定徽标」的判断必须一致。

        两处真源漂移过一次：DB 21 个非空 / seed 2 个非空。任何一边多出
        `products/certs/...` 这类已删目录，前后台徽标就会长得不一样。
        """
        db_explicit = {slug for slug, _ci in self.rows}
        seed_explicit = {
            p.get('slug') for p in _load_seed().get('products', [])
            if p.get('cert_image')
        }
        self.assertEqual(
            db_explicit, seed_explicit,
            'DB 与 seed 的 cert_image 显式集合不一致；'
            f'仅 DB 有={sorted(db_explicit - seed_explicit)}，'
            f'仅 seed 有={sorted(seed_explicit - db_explicit)}')

    def test_no_cert_image_points_at_the_deleted_certs_dir(self):
        """`products/certs/` 已在v1.9.8 去重时整体消失，任何指向它的新写入都是回归。

        这条比「解析结果」更直接：它拦住的是**写入侧**（后台上传又把徽标存回
        旧目录），而解析侧只能看到已经写进去的结果。
        """
        dead_prefix = 'products/certs/'
        db_bad = [
            (slug, str(ci)) for slug, ci in self.rows
            if str(ci).startswith(dead_prefix)
        ]
        seed_bad = [
            (p.get('slug'), p.get('cert_image'))
            for p in _load_seed().get('products', [])
            if str(p.get('cert_image') or '').replace('images/', '', 1)
            .startswith(dead_prefix)
        ]
        self.assertEqual(db_bad, [], f'DB 仍有产品指向已删除的 {dead_prefix}：{db_bad}')
        self.assertEqual(seed_bad, [], f'seed 仍有产品指向已删除的 {dead_prefix}：{seed_bad}')