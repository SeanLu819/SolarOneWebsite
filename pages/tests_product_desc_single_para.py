"""回归守卫：所有产品详情页 description 必须是单段（不含换行）。

对应 v1.10.x 内容精简任务——去掉第二段技术参数描述，使详情页文字与
主图高度协调。守卫直接断言 seed 真源（``_load_seed()`` 即生产走的路径）
的结构，不写死任何文案关键词。

铁律 #3：附变异探针，临时插入第二段确认守卫变红，再还原字节（绝不 git checkout）。
"""
import json

from django.conf import settings
from django.test import TestCase

from pages.views.utils import _load_seed


class ProductDescSingleParagraphTest(TestCase):
    def setUp(self):
        # 清 _load_seed 缓存，强制从 seed_data.json 重新读取
        import pages.views.utils as u
        u._seed_cache = None

    def test_all_product_descriptions_single_paragraph(self):
        products = _load_seed()['products']
        self.assertGreater(len(products), 0, 'seed 里没有任何产品')
        for p in products:
            desc = p.get('description') or ''
            self.assertNotIn(
                '\n', desc,
                f"{p['slug']} 的 description 仍含换行（多段），应精简为单段、去掉第二段技术参数描述"
            )

    def test_guard_catches_injected_second_paragraph(self):
        """变异探针：临时给某产品 description 插入第二段，断言守卫会变红（非空转）。

        🔴 v1.10.25 —— 探针曾失效（恒绿）：``_load_seed()`` **优先 import 构建产物
        ``pages.seed_data``**，只有产物不存在时才回落到 ``seed_data.json``
        （``pages/views/utils.py:98-120``）。原来探针只改 JSON ⇒ 注入根本没被读到
        ⇒ 守卫恒绿，探针变成空转。现在两边都覆盖：产物在内存里改（同一 dict 对象，
        ``_load_seed`` 返回的正是它），产物不在才落盘改 JSON。
        """
        import pages.views.utils as u

        try:
            from pages import seed_data as sd
        except Exception:
            sd = None

        if sd is not None:
            products = sd.SEED_DATA['products']
            self.assertGreater(len(products), 0)
            target = products[0]
            original = target.get('description') or ''
            try:
                target['description'] = original + '\nINJECTED SECOND PARAGRAPH'
                u._seed_cache = None
                with self.assertRaises(AssertionError):
                    for p in _load_seed()['products']:
                        self.assertNotIn('\n', p.get('description') or '')
            finally:
                target['description'] = original  # 还原内存对象，不碰 git
                u._seed_cache = None
            return

        path = settings.BASE_DIR / 'seed_data.json'
        raw = path.read_bytes()  # 先备份原始字节，finally 还原
        try:
            d = json.loads(raw.decode('utf-8'))
            for p in d['products']:
                if p['slug'] == 'rt590fl-s':
                    p['description'] = (p.get('description') or '') + '\nINJECTED SECOND PARAGRAPH'
                    break
            out = json.dumps(d, indent=2, ensure_ascii=False)
            if b'\r\n' in raw:
                out = out.replace('\n', '\r\n')
            out += '\r\n' if b'\r\n' in raw else '\n'
            path.write_bytes(out.encode('utf-8'))
            u._seed_cache = None
            with self.assertRaises(AssertionError):
                for p in _load_seed()['products']:
                    self.assertNotIn('\n', p.get('description') or '')
        finally:
            path.write_bytes(raw)  # 还原原始字节，不碰 git
            u._seed_cache = None
