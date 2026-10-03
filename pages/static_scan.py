"""Shared static-file discovery — the ONE place that decides which directories
hold static assets and walks them into a set of relative paths.

Two callers with different execution contexts previously carried byte-identical
copies of this logic (Ponytail audit A5):

* ``pages.views.utils`` — request-time resolution. Django is always configured,
  and on Vercel the ``static/`` tree is NOT in the function bundle, so it seeds
  the set with the build-time index (``pages.static_index_data``) in addition to
  walking whatever directories exist on disk.
* ``pages.seed_sync`` — build-time / CLI seed generation. It may run with **no
  Django settings at all** (``build.sh`` invoking ``python -m pages.seed_sync``)
  and therefore accepts an explicit ``base_dir`` to fall back on.

This module is pure computation: it deliberately does NOT cache. Each caller
keeps its own cache so that existing invalidation behaviour (notably
``invalidate_enrichment_cache`` after an admin upload) is preserved unchanged.

Imports nothing from ``pages.*`` — no circular-import risk.
"""
import os


def static_dirs(base_dir=None):
    """Return the static roots to scan, de-duplicated, in priority order.

    With Django configured: ``STATIC_ROOT`` (only if it exists) followed by every
    existing ``STATICFILES_DIRS`` entry. When importing/configuring Django raises,
    fall back to the conventional ``static``, ``staticfiles`` and
    ``public/static`` directories under ``base_dir`` (default: cwd) so the CLI
    can run without Django.
    """
    dirs = []
    try:
        from django.conf import settings
        static_root = str(getattr(settings, 'STATIC_ROOT', ''))
        if static_root and os.path.isdir(static_root):
            dirs.append(static_root)
        for d in getattr(settings, 'STATICFILES_DIRS', []):
            d = str(d)
            if os.path.isdir(d) and d not in dirs:
                dirs.append(d)
    except Exception:
        if base_dir is None:
            base_dir = os.getcwd()
        for subdir in ('static', 'staticfiles', 'public/static'):
            d = os.path.join(base_dir, subdir)
            if os.path.isdir(d) and d not in dirs:
                dirs.append(d)
    return dirs


def source_file_set(base_dir=None):
    """只扫**真源**目录（STATICFILES_DIRS，即仓库里的 ``static/``）的相对路径集合。

    🔴 v1.9.9 — 与 ``pages.views.utils._list_static_dir`` 同源的规则：
    ``STATIC_ROOT`` 是 collectstatic 的**上一轮产物**，把它算进"文件存在"的
    判定，会让旧文件名压过刚上传的新文件。

    2026-10-03 事故现场：``pages/seed_sync._resolve_static_path()`` 为产品认证图
    生成候选 ``images/products/<slug>/certifications-ul-dlc-...webp``，
    命中判定被 ``staticfiles/`` 里的陈旧副本喂成 True（真源 ``static/`` 里该文件
    在 2026-10-03 已被删），于是 seed 里写入 19 条磁盘上并不存在的路径 →
    产品页认证标识条全 404。
    """
    dirs = []
    try:
        from django.conf import settings
        for d in getattr(settings, 'STATICFILES_DIRS', []):
            d = str(d)
            if os.path.isdir(d) and d not in dirs:
                dirs.append(d)
    except Exception:
        dirs = []
    if not dirs:
        base = base_dir or os.getcwd()
        for sub in ('static', 'public/static'):
            d = os.path.join(base, sub)
            if os.path.isdir(d) and d not in dirs:
                dirs.append(d)

    file_set = set()
    for base in dirs:
        for _root, _dirs, files in os.walk(base):
            for name in files:
                rel = os.path.relpath(os.path.join(_root, name), base).replace('\\', '/')
                file_set.add(rel)
    return file_set


def build_file_set(base_dir=None, extra=()):
    """Return the set of relative static paths found under the static roots.

    ``extra`` pre-seeds the set with paths that are not on disk in this process
    (e.g. the Vercel build-time index). Relative paths always use forward
    slashes, matching how templates and the static index name files.
    """
    file_set = set(extra or ())
    for base in static_dirs(base_dir):
        for root, _, files in os.walk(base):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, base).replace('\\', '/')
                file_set.add(rel)
    return file_set
