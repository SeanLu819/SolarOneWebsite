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
