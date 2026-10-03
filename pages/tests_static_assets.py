"""静态资源完整性守卫。

2026-09-30 修复：``get_common_context()`` 在 ``SiteConfig.hero_background`` 为空时会回退到一张
hero 首图。回退文件名必须与实际磁盘文件**逐字符一致**——之前回退到不存在的裸名
``images/hero-main.webp``，导致生产每次 GET 都打 ``no hashed static URL`` 警告并回退 404。

守卫两条不变量：
  1. 幽灵名 ``images/hero-main.webp`` 永远不许再出现在代码里；
  2. 回退目标 ``images/hero-main-1.webp`` 必须真实存在于 static/images。

2026-10-03 v1.9.9 追加：``_list_static_dir()`` 的目录枚举**只能有一个真源**
（``static/``）。把 ``STATIC_ROOT``（collectstatic 陈旧快照）合并进同一集合会让
旧文件名的哈希副本压过新上传的图 → 页面引用磁盘上不存在的文件 → 404。见
``pages/views/utils.py:_list_static_dir`` 的 docstring 与下方
``StaticDirListingSourceOfTruthTests``。
"""
import os

from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings

_PAGES = Path(__file__).resolve().parent
_COMMON = _PAGES / 'views' / 'common.py'
_API_INDEX = _PAGES.parent / 'api' / 'index.py'
_STATIC_IMAGES = _PAGES.parent / 'static' / 'images'

HERO_FALLBACK = 'images/hero-main-1.webp'  # 必须与 common.py:67 回退名一致


class HeroFallbackImageTests(TestCase):
    def test_no_ghost_hero_main_webp_reference(self):
        """common.py / api/index.py 都不得再引用不存在的裸名 hero-main.webp。"""
        for src in (_COMMON, _API_INDEX):
            text = src.read_text(encoding='utf-8')
            self.assertNotIn(
                "'images/hero-main.webp'",
                text,
                f"{src.name} 仍引用了幽灵文件 'images/hero-main.webp'（已修复为 hero-main-1.webp）",
            )

    def test_hero_fallback_target_exists_on_disk(self):
        """回退目标 hero-main-1.webp 必须真实存在于 static/images，否则线上会 404。"""
        target = _STATIC_IMAGES / 'hero-main-1.webp'
        self.assertTrue(
            target.exists(),
            f"hero 回退目标 {target} 在 static/images 中缺失",
        )

    def test_hero_fallback_target_is_referenced_in_template(self):
        """home.html 已使用 hero-main-1.webp（含 1280/portrait 变体），回退名与之一致。"""
        home = _PAGES.parent / 'templates' / 'home.html'
        text = home.read_text(encoding='utf-8')
        self.assertIn(
            "images/hero-main-1.webp",
            text,
            "home.html 未引用 hero-main-1.webp，回退名与模板首图不一致",
        )


class StaticDirListingSourceOfTruthTests(TestCase):
    """目录枚举必须以 static/ 为唯一真源（v1.9.9，防陈旧 collectstatic 快照抢占）。

    事故现场：``static/images/projects/beijing-international-tennis-center/`` 只有
    4 张新上传的 ``bitc-tennis-court-light-720p-0{1..4}.webp``，而 ``staticfiles/``
    里躺着上一轮 collectstatic 的陈旧快照（旧图 + 它们的哈希副本
    ``bitc-tennis-01.d5801a84901f.webp``）。旧实现把两边合并进同一集合，
    精确同名分支先命中哈希副本 → 页面 8 个 ``<img>`` 全 404，新图一张不显示。
    """

    def setUp(self):
        # 目录列表是进程级缓存，不清会串到后续用例。
        from pages.views import utils
        self.utils = utils
        utils._dir_listing_cache.clear()
        self.addCleanup(utils._dir_listing_cache.clear)

    def test_listing_matches_live_static_dir_exactly(self):
        """目录在 static/ 里存在时，枚举结果必须等于该目录的真实内容。"""
        rel = 'images/projects/beijing-international-tennis-center'
        src = Path(settings.BASE_DIR) / 'static' / rel
        if not src.is_dir():
            self.skipTest(f'{rel} 不在 static/ 下，跳过')
        expected = set(os.listdir(src))
        with override_settings(DEBUG=False):  # 本地默认就是 False（settings.py:72）
            got = self.utils._list_static_dir(rel)
        self.assertEqual(
            set(got), expected,
            '目录枚举混入了 static/ 之外的文件名（陈旧 staticfiles 快照会抢占新图）',
        )

    def test_no_stale_snapshot_name_survives_exact_match(self):
        """精确同名解析不得返回只存在于 staticfiles/ 的哈希副本名。

        用真实数据回归：该 slug 的封面必须解析到 static/ 里真实存在的那一张。
        """
        rel = 'images/projects/beijing-international-tennis-center'
        src = Path(settings.BASE_DIR) / 'static' / rel
        if not src.is_dir():
            self.skipTest(f'{rel} 不在 static/ 下，跳过')
        names = os.listdir(src)
        # 只存在于 staticfiles/ 的名字（即陈旧快照独有、磁盘真源没有的）
        stale_only = {
            n for n in names
            if not (src / n).exists()
        }
        with override_settings(DEBUG=False):
            listing = self.utils._list_static_dir(rel)
        self.assertEqual(
            listing & stale_only, set(),
            f'陈旧快照独有文件名混进枚举：{sorted(listing & stale_only)[:3]}',
        )
        cover = self.utils._find_project_cover_path(
            'beijing-international-tennis-center', 'projects/bitc-tennis-01.webp')
        self.assertTrue(
            cover and (Path(settings.BASE_DIR) / 'static' / cover).exists(),
            f'封面解析到不存在的文件：{cover!r}',
        )

    def test_falls_back_to_static_root_when_source_dir_absent(self):
        """真源目录不存在（生产形态）时仍要回退 STATIC_ROOT，不能退化成空列表。"""
        rel = 'images/projects/gallery'  # static/ 下不存在，仅 staticfiles/ 有
        if not (Path(settings.BASE_DIR) / 'staticfiles' / rel).is_dir():
            self.skipTest('staticfiles/images/projects/gallery 不存在，跳过回退用例')
        self.assertFalse(
            (Path(settings.BASE_DIR) / 'static' / rel).exists(),
            '用例前提变化：static/images/projects/gallery 现在存在了',
        )
        with override_settings(DEBUG=False):
            got = self.utils._list_static_dir(rel)
        self.assertTrue(got, '回退 STATIC_ROOT 的分支被误删，生产目录枚举会退化为空')

    def test_find_static_ignores_stale_snapshot_only_paths(self):
        """``_find_static()`` 不得因为陈旧快照就把磁盘上不存在的文件判成 HIT。"""
        from pages.views import utils
        old = 'images/projects/beijing-international-tennis-center/bitc-tennis-01.webp'
        new = 'images/projects/beijing-international-tennis-center/' \
              'bitc-tennis-court-light-720p-01.webp'
        src = Path(settings.BASE_DIR) / 'static' / 'images/projects' \
            / 'beijing-international-tennis-center'
        if not src.is_dir():
            self.skipTest('用例依赖目录不存在，跳过')
        # 前提：旧名已从真源删除、新名真源存在（v1.9.9 事故现场）。
        self.assertFalse((src / 'bitc-tennis-01.webp').exists(), '用例前提变化：旧名又回来了')
        self.assertTrue((src / 'bitc-tennis-court-light-720p-01.webp').exists())
        self.assertFalse(
            utils._find_static(old),
            '_find_static 被陈旧 staticfiles 快照欺骗，会拼出 404 的 URL',
        )
        self.assertTrue(
            utils._find_static(new),
            '减法误伤了真源文件（真源存在却被判 MISS）',
        )
