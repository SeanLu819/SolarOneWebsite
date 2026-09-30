"""B4 内容深度守卫：产品 description 必须 >=150 字符（喂正文 + JSON-LD description）。

2026-09-30 修复：16/24 产品英文 description 偏短（rt590fl-s/rt390fl 仅 9 字符，就是型号名），
重写为 >=150 质量 SEO 文案。本守卫锁住"不得回退到短描述"。

直接读 seed_data.json（生产唯一真源），不依赖运行时 _load_seed / py 产物。
"""
import json
from pathlib import Path

from django.test import TestCase

_SEED = Path(__file__).resolve().parent.parent / 'seed_data.json'

# B4 紧急项：曾仅 9 字符（型号名），必须已扩写
CRITICAL_SLUGS = ('rt590fl-s', 'rt390fl')
MIN_DESC_LEN = 150


class ProductDescriptionDepthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.products = json.loads(_SEED.read_text(encoding='utf-8'))['products']
        cls.by_slug = {p['slug']: p for p in cls.products}

    def test_all_product_descriptions_at_least_150_chars(self):
        short = [
            (p['slug'], len(p.get('description', '') or ''))
            for p in self.products
            if len(p.get('description', '') or '') < MIN_DESC_LEN
        ]
        self.assertEqual(
            short, [],
            f'以下产品 description 不足 {MIN_DESC_LEN} 字符（B4 内容深度未达标）: {short}',
        )

    def test_critical_products_have_real_prose_not_just_model_name(self):
        for slug in CRITICAL_SLUGS:
            p = self.by_slug[slug]
            desc = (p.get('description', '') or '').strip()
            self.assertGreaterEqual(
                len(desc), MIN_DESC_LEN,
                f'{slug} description 仍过短（B4 紧急项未修复）',
            )
            # 不得仍是裸型号名（如 "RT590FL-S"）
            self.assertNotEqual(
                desc, (p.get('name', '') or '').strip(),
                f'{slug} description 仍是型号名，未扩写为真实文案',
            )

    def test_fl4m_short_translations_cleared_to_fall_back_to_english(self):
        """fl4m 的 ru/ar 短翻译已清空 -> translate() 回退英文（>=150）。

        避免非英文页面拿到 45-65 字符 stub（符合"缺译回退英文绝不空串"）。
        """
        tr = self.by_slug['fl4m'].get('translations', {})
        en_len = len(self.by_slug['fl4m'].get('description', '') or '')
        for lang in ('ru', 'ar'):
            val = (tr.get(lang) or {}).get('description', '')
            # 空 -> 运行时回退英文；若填了则必须 >=150
            if val:
                self.assertGreaterEqual(
                    len(val), MIN_DESC_LEN,
                    f'fl4m[{lang}] description 非空但不足 {MIN_DESC_LEN} 字符',
                )
            else:
                self.assertGreaterEqual(
                    en_len, MIN_DESC_LEN,
                    f'fl4m[{lang}] 清空回退英文，但英文 description 不足 {MIN_DESC_LEN}',
                )
