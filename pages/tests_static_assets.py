"""静态资源完整性守卫。

2026-09-30 修复：``get_common_context()`` 在 ``SiteConfig.hero_background`` 为空时会回退到一张
hero 首图。回退文件名必须与实际磁盘文件**逐字符一致**——之前回退到不存在的裸名
``images/hero-main.webp``，导致生产每次 GET 都打 ``no hashed static URL`` 警告并回退 404。

守卫两条不变量：
  1. 幽灵名 ``images/hero-main.webp`` 永远不许再出现在代码里；
  2. 回退目标 ``images/hero-main-1.webp`` 必须真实存在于 static/images。
"""
from pathlib import Path

from django.test import TestCase

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
