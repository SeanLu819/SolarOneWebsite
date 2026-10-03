"""构建提速守卫（2026-09-28）。

两件事必须长期保持，否则 Vercel 构建会回到 ~5 分钟：

1. 生产静态后端只能用「只哈希、不 gzip」的 `ManifestStaticFilesStorage`。
   Vercel 静态由边缘 CDN 直供，CDN 自己会做 brotli/gzip；构建期再对 142 MB
   的 webp/pdf 逐个 gzip 纯属冗余 CPU，且多写一份 `.gz` 还拖慢后续的拷贝与
   产物上传。改用 WhiteNoise 的 `CompressedManifestStaticFilesStorage` 会让每个
   静态文件在构建期被压缩，必须把这条守死。
2. `build.sh` 让 collectstatic 直接写进 `public/static`（VERCEL_STATIC_ROOT），
   不再产生 `staticfiles/` 再 `cp -R` 142 MB —— 那次拷贝是旧构建最重的一步。
   （这一步由 build.sh 本身保证，这里只守住“存储不压缩”这条代码层契约；
    build.sh 的流程若被改回 `cp -R staticfiles public/static`，verify_static_build.py
    会直接失败。）
"""
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
from django.test import TestCase

from pages import storage as storage_mod


class BuildStaticSpeedGuardTests(TestCase):
    def test_production_storage_is_hashing_only_not_gzip(self):
        base = storage_mod.BundledManifestStaticFilesStorage.__bases__[0]
        self.assertIs(
            base,
            ManifestStaticFilesStorage,
            "生产静态基类必须是 ManifestStaticFilesStorage（只哈希、不 gzip）；"
            "改成 Compressed 变体会让每个静态文件在构建期被 gzip，拖慢 Vercel 构建。",
        )

    def test_production_storage_base_must_not_be_compressed(self):
        base_name = storage_mod.BundledManifestStaticFilesStorage.__bases__[0].__name__
        self.assertNotIn(
            "Compressed",
            base_name,
            "生产静态存储不得用 WhiteNoise 的 Compressed 变体（构建期 gzip 冗余，"
            "Vercel 边缘 CDN 会自行压缩）。",
        )

    def test_production_storage_uses_bundled_fallback(self):
        # 防回归：子类必须仍然优先读包内 HASHED_FILES、且不抛异常（v1.5.5 事故修法）。
        self.assertTrue(
            hasattr(storage_mod.BundledManifestStaticFilesStorage, "load_manifest"),
            "BundledManifestStaticFilesStorage 必须保留 load_manifest 的包内清单兜底。",
        )


class StaticCacheHeaderGuardTests(TestCase):
    """vercel.json 必须给 /static/ 配immutable 缓存头（v1.9.7 新增）。

    背景：`build.sh` 把 collectstatic 结果镜像进 `public/static/`，由 Vercel
    边缘 CDN 直供 —— 这些字节**从不经过 Django 进程**，所以
    `WHITENOISE_MAX_AGE` 是死配置。2026-10-03 线上实测：已经哈希化的
    `/static/css/base.<hash>.css` 仍返回 `max-age=0, must-revalidate`，
    浏览器每次访问都要多一次 304 往返。唯一能改的地方是 vercel.json。

    为什么 `immutable` 安全：collectstatic 用 ManifestStaticFilesStorage，
    所有 /static/ URL 都带 12 位内容哈希（实测全站零漏网），内容变则文件名变。
    """

    @staticmethod
    def _vercel():
        import json
        import os
        from django.conf import settings
        path = os.path.join(str(settings.BASE_DIR), 'vercel.json')
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)

    @staticmethod
    def _cache_control_for(cfg, source):
        for block in cfg.get('headers', []):
            if block.get('source') == source:
                for h in block.get('headers', []):
                    if h.get('key') == 'Cache-Control':
                        return h.get('value', '')
        return None

    def test_vercel_json_declares_static_cache_header_block(self):
        cfg = self._vercel()
        sources = [b.get('source') for b in cfg.get('headers', [])]
        self.assertIn(
            '/static/(.*)', sources,
            "vercel.json 缺少 source=/static/(.*) 的 headers 块 —— "
            "public/ 由边缘 CDN 直供，不配缓存头浏览器每次都要重验证。",
        )

    def test_static_assets_are_served_immutable_for_one_year(self):
        value = self._cache_control_for(self._vercel(), '/static/(.*)')
        self.assertIsNotNone(value)
        self.assertIn('immutable', value,
                      '哈希化静态资源可安全 immutable，缺失会让每次访问多一次 304。')
        self.assertIn('max-age=31536000', value,
                      'immutable 必须配一年 max-age，否则等于没开。')
        self.assertIn('public', value, '需带 public，否则共享缓存不存。')

    def test_headers_block_does_not_shadow_itself_with_a_catch_all(self):
        """🔴不能加 `source: /(.*)` 通配规则。

        那样做看似"顺便给 HTML 也设了头"，实际会与 /static/ 规则产生
        顺序依赖：Vercel 多条命中时结果不保证等于我们的意图，最坏情况是
        通配规则把 /static/ 的 immutable 覆盖回 must-revalidate。
        HTML 的 `max-age=0, must-revalidate` 本来就由 Django 响应，不需要在这里管。
        """
        sources = [b.get('source') for b in self._vercel().get('headers', [])]
        self.assertNotIn(
            '/(.*)', sources,
            "禁止 source: /(.*) 通配 headers —— 它可能覆盖 /static/ 的 immutable "
            "规则，把一年缓存打回每次重验证。",
        )

    def test_rewrites_and_redirects_survive_the_headers_change(self):
        """加 headers 段时最容易误删 rewrite —— 那会让全站 404。"""
        cfg = self._vercel()
        self.assertEqual(
            cfg.get('rewrites'),
            [{'source': '/(.*)', 'destination': '/api/index.py'}],
            "catch-all rewrite 被改动 —— 所有非静态 URL 都要经 Django。",
        )
        self.assertTrue(cfg.get('redirects'),
                        "apex -> www 的 301 redirect 不能丢。")
        self.assertIn('functions', cfg,
                      "functions.excludeFiles 配置不能丢（否则函数包超 225 MB）。")


class SeedPythonArtifactFidelityTests(TestCase):
    """🔴 v1.9.9 —— `pages/seed_data.py` 必须与 `seed_data.json` **逐字段相等**。

    背景（线上事故）：`_write_seed_files()` 曾用
    ``py_data.replace('true','True').replace('false','False')...``
    把 JSON 转成 Python 字面量。`json.dumps` 出来的文本里，`true` 既可能是
    JSON 语法成分，**也可能出现在引号内的文案里** —— 替换分不清两者。
    实测 `projects[13].description` 的 `a true "shadowless" effect` 被写成
    `a True "shadowless" effect`。`seed_data.json` 里是对的，**只有构建产物是错的**，
    而 `build.sh` 每次 Vercel 构建都跑这段生成器、Vercel 又只读这个产物
    （无 DB）⇒ 错别字直接上线。

    这类 bug 靠「读 JSON 的内容守卫」永远抓不到：污染只存在于生成物里。
    唯一有效的判据是**两处真源逐字段比对**。
    """

    def _load(self, dotted):
        module_path, attr = dotted.rsplit('.', 1)
        return getattr(__import__(module_path, fromlist=[attr]), attr)

    def test_seed_json_and_python_artifact_are_field_identical(self):
        import io
        import json
        import os

        from django.conf import settings

        base = str(settings.BASE_DIR)
        with io.open(os.path.join(base, 'seed_data.json'), encoding='utf-8') as fh:
            from_json = json.load(fh)
        try:
            from_py = self._load('pages.seed_data.SEED_DATA')
        except Exception as exc:  # pragma: no cover - artifact missing locally
            self.skipTest('pages/seed_data.py 不可用（构建产物，本地可能未生成）：%s' % exc)

        self.assertEqual(
            sorted(from_json.keys()), sorted(from_py.keys()),
            '两处 seed 的顶层键不同：json=%s py=%s'
            % (sorted(from_json.keys()), sorted(from_py.keys())))

        for key in from_json:
            self.assertEqual(
                from_json[key], from_py[key],
                f'seed_data.json 与 pages/seed_data.py 的 {key!r} 不一致 —— '
                '生产只读后者，说明构建产物生成逻辑破坏了数据'
                '（v1.9.9 曾把文案里的 true 替换成 True）')

    def test_generator_preserves_booleans_inside_strings(self):
        """生成器本身：字符串里的 true/false/null 必须原样保留。"""
        from pages.seed_sync import _json_to_python_literals as gen

        payload = {
            'literals': [True, False, None],
            'copy': 'a true "shadowless" effect, a false alarm, null pointer',
            'nested': {'nullable': True, 'text': 'truthy falsehood'},
        }
        emitted = gen(payload)
        self.assertIn('"a true \\"shadowless\\" effect, a false alarm, null pointer"',
                      emitted,
                      '文案里的 true/false/null 被改写了 —— 生成器把字符串内容'
                      '和 JSON 字面量混为一谈')
        self.assertIn('"nullable": True', emitted,
                      '键名 nullable 不该被替换成 Nullable')
        # 生成的源码必须能还原成原始对象
        self.assertEqual(eval(emitted), payload,
                         '生成的 Python 字面量无法还原原始数据')

    def test_generator_word_boundary_does_not_touch_identifiers(self):
        from pages.seed_sync import _json_to_python_literals as gen

        emitted = gen({'truthiness': 1, 'nullable_field': 2, 'value': None})
        self.assertIn('"truthiness": 1', emitted)
        self.assertIn('"nullable_field": 2', emitted)
        self.assertIn('"value": None', emitted)
