"""生产静态存储 —— 保证「清单缺失」永远不会把整站变成 500。

为什么需要这个文件
------------------
生产用内容哈希（`CompressedManifestStaticFilesStorage`）换取 Vercel 边缘 CDN 的
`Cache-Control: immutable, max-age=31536000`。代价是运行时 `{% static %}` /
`static()` **必须**能查到「原名 → 哈希名」映射：

* 清单在 → `/static/css/base.280e03822c88.css`，CDN 命中 immutable 缓存；
* 清单不在 → Django/WhiteNoise 回退去磁盘找原文件，而 `static/`、`staticfiles/`
  已被 `vercel.json -> functions.excludeFiles` 排除出函数包 → 抛
  `ValueError: The file 'css/base.css' could not be found with <...>`。

`base.html` 每个页面都要 `{% static 'css/base.css' %}`，所以清单一旦缺失就是
**全站 500**（2026-09-12 v1.5.4 线上事故，见 CHANGELOG）。

解决办法分两层
--------------
1. **不依赖会被排除的文件**：构建期把 `staticfiles.json` 的 paths 写进
   `pages/static_index_data.py`（源码文件，必在函数包内），这里直接 import。
2. **兜底不抛异常**：`stored_name()` 出错时退回**未哈希 URL**，即 v1.5.2 之前的
   行为（边缘 CDN 上未哈希文件同样存在，WhiteNoise 的
   `keep_only_hashed_files=False` 会同时保留哈希与原始副本）。
   宁可少一层缓存，也不能 500。
"""

import logging

from whitenoise.storage import CompressedManifestStaticFilesStorage

logger = logging.getLogger(__name__)

_bundled_cache = None


def bundled_hashed_files():
    """构建期写在 `pages/static_index_data.py` 里的哈希映射（缺则空字典）。"""
    global _bundled_cache
    if _bundled_cache is None:
        try:
            from pages.static_index_data import HASHED_FILES
            _bundled_cache = dict(HASHED_FILES) if HASHED_FILES else {}
        except Exception as exc:  # 本地开发 / 生成物缺失，属正常情况
            logger.debug('bundled static manifest unavailable: %s', exc)
            _bundled_cache = {}
        if _bundled_cache:
            logger.info('bundled static manifest: %d entries', len(_bundled_cache))
    return _bundled_cache


class BundledManifestStaticFilesStorage(CompressedManifestStaticFilesStorage):
    """优先读包内 Python 清单，且任何情况下都不因查不到文件名而抛异常。"""

    # WhiteNoise 会从 settings.WHITENOISE_MANIFEST_STRICT 覆盖这个属性；
    # 显式设一次，保证即使该设置被误改也不会走上「strict 抛错」的分支。
    manifest_strict = False

    # 逐名告警只在前几次输出，之后降为 DEBUG —— 清单整体缺失时每张图都会命中
    # 这条路径，保留全量日志只会淹没有效信息（真正的信号是下面那条 error）。
    _MISS_WARN_LIMIT = 5

    def load_manifest(self):
        bundled = bundled_hashed_files()
        if bundled:
            return bundled, ''
        manifest = {}
        try:
            manifest, manifest_hash = super().load_manifest()
        except Exception as exc:  # 清单损坏 / 版本不符
            logger.error('static manifest unusable (%s) — serving un-hashed URLs', exc)
            return {}, ''
        if not manifest:
            # 这是需要关注的信号：包内 Python 清单缺失，磁盘清单也没有。
            # 站点仍可用（退回未哈希 URL），但会丢失 immutable 缓存。
            logger.error(
                'no static manifest available — falling back to un-hashed static URLs. '
                'Check that build.sh ran `python -m pages.static_index` and that '
                'pages/static_index_data.py is inside the function bundle.'
            )
        return manifest, manifest_hash

    def stored_name(self, name):
        try:
            return super().stored_name(name)
        except Exception as exc:
            # 不再让一个查不到的文件名毁掉整个页面（事故复盘的核心教训）。
            self._miss_count = self.__dict__.get('_miss_count', 0) + 1
            if self._miss_count <= self._MISS_WARN_LIMIT:
                logger.warning(
                    'no hashed static URL for %r (%s) — serving un-hashed URL',
                    name, exc)
            else:
                logger.debug('un-hashed static fallback for %r', name)
            return name
