import os
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from django.conf import settings
from django.templatetags.static import static
from pages.static_scan import build_file_set
from pages.utils import (
    strip_hash_suffix, translate, jsonld_property_pairs,
    build_seo_title, build_seo_description, build_project_seo_title,
    build_project_seo_description, build_project_og_description,
    fit_description, get_seo_override,
)

logger = logging.getLogger(__name__)

_SEED_CANDIDATES = [
    os.path.join(settings.BASE_DIR, 'seed_data.json'),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'seed_data.json'),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'seed_data.json'),
]

_seed_cache = None
_static_file_set = None
_dir_listing_cache = {}
_PRODUCT_DIR_IMAGE_CACHE = {}
_static_index = None
_stale_snapshot_cache = None


def clear_static_caches():
    """Drop every process-level static lookup cache. Owner of the state, so the
    dicts are mutated in place rather than rebound.

    🔴 v1.10.15 — this function exists because ``enrich.invalidate_enrichment_cache()``
    tried to do this job with ``_dir_listing_cache = {}`` after a local
    ``from .utils import _dir_listing_cache``. That rebound a *local* name and
    left ``utils``' dict populated, so admin saves never invalidated anything.
    The failure was invisible in tests (each test process starts with empty
    caches) and only showed up in a long-running dev server: upload images via
    the admin, and the freshly written files stayed invisible because the
    directory listing for their slug was cached as empty before the upload.

    ``.clear()`` rather than rebinding to ``{}`` matters — a caller that grabbed
    a reference (or a test that seeded a probe key) must see the flush.

    ``_stale_snapshot_cache`` is included for the same reason: the stale-name
    subtraction reads whatever is on disk at build time, so it has to be
    recomputed after files move.
    """
    global _static_file_set, _static_index, _stale_snapshot_cache
    _dir_listing_cache.clear()
    _PRODUCT_DIR_IMAGE_CACHE.clear()
    _static_file_set = None
    _static_index = None
    _stale_snapshot_cache = None


def _load_static_index():
    """Load the build-time static asset index (pages.static_index_data).

    On Vercel the source `static/` tree is intentionally kept OUT of the
    Python function bundle (see vercel.json -> functions.excludeFiles): the
    ~118 MB of assets are served by the edge CDN from public/static/. Image
    path resolution, however, needs to know which files exist — so build.sh
    writes a names-only index that we import here. Returns {} when the file
    is absent (local dev / CI), in which case disk scanning is authoritative.
    """
    global _static_index
    if _static_index is not None:
        return _static_index
    try:
        from pages.static_index_data import STATIC_INDEX
        _static_index = STATIC_INDEX if isinstance(STATIC_INDEX, dict) else {}
    except Exception:
        _static_index = {}
    return _static_index


def _index_file_set():
    """Set of relative static paths recorded in the generated index."""
    out = set()
    for rel_dir, names in (_load_static_index().get('dirs') or {}).items():
        prefix = (rel_dir + '/') if rel_dir else ''
        for name in names:
            out.add(prefix + name)
    return out


def _index_dir_listing(rel_dir):
    """File names recorded for one directory in the generated index."""
    rel_dir = (rel_dir or '').replace('\\', '/').strip('/')
    names = (_load_static_index().get('dirs') or {}).get(rel_dir) or []
    return set(names)


def _load_seed():
    """Load seed data. On Vercel, import from the embedded Python module
    (pages.seed_data) so no filesystem access is needed. In local dev, fall
    back to reading seed_data.json from disk so the JSON stays the source of
    truth during development."""
    global _seed_cache
    if _seed_cache is not None:
        return _seed_cache
    try:
        from pages.seed_data import SEED_DATA
        _seed_cache = SEED_DATA
    except Exception:
        logger.warning('Could not import pages.seed_data, trying JSON file', exc_info=True)
        for path in _SEED_CANDIDATES:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    _seed_cache = json.load(f)
                break
            except Exception:
                continue
    if _seed_cache is None:
        _seed_cache = {'products': [], 'projects': [], 'site_config': {}}
    return _seed_cache


def _stale_snapshot_rel_paths():
    """相对路径中「只存在于 STATIC_ROOT 收集快照、真源 static/ 里没有」的那部分。

    🔴 v1.9.9 — 与 ``_list_static_dir`` 同源的事故（docstring 在那一侧，讲的是
    目录枚举）：``pages.static_scan.static_dirs()`` 会把 ``STATIC_ROOT`` 和
    ``STATICFILES_DIRS`` **都**扫进来，所以 ``_find_static()`` 会对一个只躺在
    陈旧 collectstatic 快照里的文件名返回 ``True``，调用方据此拼出 URL → 浏览器 404。
    2026-10-03 的现场： ``staticfiles/.../bitc-tennis-01.webp`` 已随旧图删除，
    但 ``_find_static('images/projects/beijing-international-tennis-center/
    bitc-tennis-01.webp')`` 依然 HIT。

    构建期索引（``pages.static_index``）**不动** —— Vercel 上函数包里既没有
    ``static/`` 也没有 ``staticfiles/``，索引是唯一真源，不能按本机快照裁剪。
    这里只在真源目录存在时做减法，因此生产路径完全不受影响。

    🔴 v1.10.15 — 结果按进程缓存（此前每个调用都重走两棵树，而
    ``_build_static_file_set`` 每请求调它一次）。用
    ``clear_static_caches()`` 失效：磁盘上的文件集合变了，减法结果也得重算。
    """
    global _stale_snapshot_cache
    if _stale_snapshot_cache is not None:
        return _stale_snapshot_cache
    try:
        sources = [str(d) for d in settings.STATICFILES_DIRS if os.path.isdir(d)]
        root = str(settings.STATIC_ROOT)
    except Exception:
        _stale_snapshot_cache = set()
        return _stale_snapshot_cache
    if not sources or not root or not os.path.isdir(root):
        _stale_snapshot_cache = set()
        return _stale_snapshot_cache

    source_rels = set()
    for base in sources:
        for _root, _dirs, files in os.walk(base):
            for name in files:
                rel = os.path.relpath(os.path.join(_root, name), base).replace('\\', '/')
                source_rels.add(rel)

    stale = set()
    for _root, _dirs, files in os.walk(root):
        for name in files:
            full = os.path.join(_root, name)
            rel = os.path.relpath(full, root).replace('\\', '/')
            if rel not in source_rels:
                stale.add(rel)
    _stale_snapshot_cache = stale
    return stale


def _build_static_file_set():
    """Build a set of all relative static file paths. Cached after first call.
    Eliminates 20-50 filesystem calls per request."""
    global _static_file_set
    if _static_file_set is not None:
        return _static_file_set

    # A5: directory discovery + walk live in pages.static_scan (shared with
    # pages.seed_sync). Names-only build-time index first: on Vercel neither
    # STATIC_ROOT nor STATICFILES_DIRS exists inside the function bundle.
    file_set = build_file_set(extra=_index_file_set())

    # 运行时解析只信真源；陈旧 collectstatic 快照里的幽灵名不许混进来。
    file_set -= _stale_snapshot_rel_paths()

    _static_file_set = file_set
    logger.info(f'Built static file cache: {len(file_set)} files')
    return file_set


def _find_static(rel_path):
    """O(1) lookup in cached static file set. No filesystem I/O after first call."""
    rel_path = rel_path.replace('\\', '/')
    return rel_path in _build_static_file_set()


def _passthrough_url(path):
    """Return ``path`` when it must NOT be re-resolved against static/.

    A3 single source: ``_static_url`` and ``_dict_product_image_url`` carried
    the same two guards — an already-absolute URL, or a rooted
    ``/static/``/``/media/`` path, must be returned verbatim. Returns ``''``
    for falsy input so callers can write
    ``url = _passthrough_url(p); if url: return url``.
    """
    if not path:
        return ''
    if isinstance(path, str) and path.startswith(
        ('http://', 'https://', '/static/', '/media/')
    ):
        return path
    return ''


def _first_static(candidates):
    """Return ``static(c)`` for the first candidate that exists, else ``''``.

    A3 single source for the "ordered candidate list -> first hit -> static()"
    loop that ``_dict_product_image_url``, ``_product_image_url``,
    ``views_products._resolve_ppc_image`` and ``views_products._dict_ppc_image``
    each hand-rolled. Blank and duplicate candidates are skipped; the caller's
    ordering stays authoritative, so behaviour is unchanged.
    """
    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if _find_static(candidate):
            return static(candidate)
    return ''


def _list_static_dir(rel_dir):
    """List files in a static directory with caching. Eliminates repeated os.listdir() calls.

    🔴 v1.9.9 — 目录枚举**只能有一个真源**。

    旧实现把 `static/<dir>` 与 `STATIC_ROOT/<dir>`（collectstatic 产物）*合并*进
    同一个集合，谁先进集合谁优先。后果（2026-10-03 事故，见
    `static/images/projects/beijing-international-tennis-center/`）：

    * 用户在后台上传了 4 张新图 → 落到 `static/images/projects/<slug>/`
      （`bitc-tennis-court-light-720p-0{1..4}.webp`），本地 `ls` 只看得到它们；
    * 但 `staticfiles/` 里躺着**上一轮 collectstatic 的陈旧快照**，同一个 slug
      目录下既有旧图 `bitc-tennis-0{1..4}.webp`、也有它们的**哈希副本**
      `bitc-tennis-01.d5801a84901f.webp`；
    * 而 `settings.py:72` 让**本地默认 `DEBUG=False`**，`STATIC_ROOT` 分支照常
      生效 → 陈旧名和真源名被并进同一集合；
    * `_find_project_cover_path()` 的「精确同名」分支用
      `strip_hash_suffix(f) == clean_name` 比对，`sorted()` 里
      `bitc-tennis-01.d5801a84901f.webp` 排在 `bitc-tennis-01.webp` 之前，
      于是页面 8 个 `<img>` 全指向磁盘上并不存在的哈希名 → **404**，
      而用户刚传的新图一张都不显示（本地明明有文件）。

    新规则：该目录在 `static/` 里存在 → **只看 `static/`**，陈旧快照彻底不参与；
    只有 `static/` 根本没有这个目录（生产形态：`vercel.json` 的 `excludeFiles`
    把 `static/` 与 `staticfiles/` 都排除出函数包）时才回退 `STATIC_ROOT`。

    🔴 v1.10.15 — 回退来的名字仍要过一遍「陈旧快照减法」，与
    ``_build_static_file_set()`` 对齐。那边早就减了（v1.9.9），这边一直没减，
    于是同一个「只有一个真源」的原则在两个枚举入口上表现不一致，
    后果是 2026-10-04 的源深体育场事故：

    * 用户在 admin 重新上传 5 张图 → 正确落到
      `static/images/projects/yuanshen-sports-centre-stadium/`，磁盘上确实有；
    * `static/images/projects/gallery` **不存在**，但
      `staticfiles/images/projects/gallery`（旧 collectstatic 快照）里有同名
      `shys-soccer-0{1..5}.webp` —— 源深最早就是按 `gallery/` 传的；
    * 本地 `DEBUG=False` ⇒ `elif not settings.DEBUG` 分支生效，
      于是「回退目录」命中，5 张图被解析成
      `/static/images/projects/gallery/shys-soccer-0N.webp`；
    * 该路径只存在于 collectstatic 快照、dev server 不服务 ⇒ 页面 5 张图全 404，
      而用户刚传的文件一张都没被引用。

    减法在生产是空操作：`STATICFILES_DIRS` 与 `STATIC_ROOT` 都不在函数包里，
    `_stale_snapshot_rel_paths()` 直接返回空集，构建期索引原样保留。

    减法**无条件**剔除，不需要按 `static/` 的存在性豁免：走到这里要么是生产形态
    （`stale` 为空集，不裁剪任何东西），要么 `static/<rel>` 目录压根不存在（否则
    上面 `if os.path.isdir(base)` 已命中，`STATIC_ROOT` 分支不会执行）。而
    `_stale_snapshot_rel_paths()` 的定义就是「`STATIC_ROOT` 里有、真源 `static/`
    里没有」—— 在这个分支下它与「快照里的名字」完全重合，豁免条件永远为假。
    """
    if rel_dir in _dir_listing_cache:
        return _dir_listing_cache[rel_dir]

    results = set(_index_dir_listing(rel_dir))
    dirs_to_check = []

    base = os.path.join(settings.BASE_DIR, 'static', rel_dir)
    if os.path.isdir(base):
        dirs_to_check.append(base)
    elif not settings.DEBUG:
        # 回退仅在真源目录不存在时成立（生产）/ 目录名变了还没跑 collectstatic。
        static_root = os.path.join(str(settings.STATIC_ROOT), rel_dir)
        if os.path.isdir(static_root):
            dirs_to_check.append(static_root)

    for d in dirs_to_check:
        if os.path.isdir(d):
            for f in os.listdir(d):
                results.add(f)

    # 只在真源 static/ 里没有同名文件时才把回退带来的名字剔掉 —— 与
    # _build_static_file_set() 的减法同源，避免两条枚举路径给出不同答案。
    prefix = rel_dir.rstrip('/') + '/'
    results = {f for f in results if prefix + f not in _stale_snapshot_rel_paths()}

    _dir_listing_cache[rel_dir] = results
    return results


def _normalize_static_rel(path):
    """Rewrite legacy seed paths (projects/x.webp, products/x.webp, ...) into
    canonical paths under images/ that match the committed static/ directory
    layout."""
    if not path:
        return ''
    path = str(path).strip().lstrip('/\\')
    path = path.replace('\\', '/')
    for prefix in ('static/', 'media/'):
        if path.startswith(prefix):
            path = path[len(prefix):]
    if path.startswith(('images/', 'css/', 'files/', 'admin/', 'js/')):
        return path
    legacy_map = {
        'projects/': 'images/projects/',
        'products/': 'images/products/',
        'processed/': 'images/processed/',
    }
    for old, new in legacy_map.items():
        if path.startswith(old):
            return new + path[len(old):]
    return f'images/{path}'


def _static_url(path):
    """Return static URL for a non-empty path. Accepts a wide variety of
    legacy or canonical paths and normalizes them to a Django static URL.
    Falls back gracefully to a URL even if the file is not found (prevents
    blank src attributes — useful while assets are being added)."""
    if not path:
        return ''
    passthrough = _passthrough_url(path)
    if passthrough:
        return passthrough
    rel = _normalize_static_rel(path)
    return static(rel)


def _dict_product_image_url(path, slug):
    """Return static URL for a _DictProduct image field, trying multiple path combinations."""
    if not path:
        return ''
    passthrough = _passthrough_url(path)
    if passthrough:
        return passthrough

    path = str(path).replace('\\', '/')
    filename = Path(path).name
    stem = Path(filename).stem
    clean_filename = strip_hash_suffix(filename)
    clean_stem = Path(clean_filename).stem if clean_filename else ''

    candidates = []
    if slug and clean_filename and clean_filename != filename:
        candidates.append(f'images/products/{slug}/{clean_filename}')
    if clean_filename and clean_filename != filename:
        candidates.append(f'images/products/{clean_filename}')
    if slug and clean_stem and clean_stem != stem:
        candidates.append(f'images/products/{slug}/{clean_stem}.webp')
    if path.startswith('images/'):
        candidates.append(path)
    if slug and filename:
        candidates.append(f'images/products/{slug}/{filename}')
    if slug and stem:
        candidates.append(f'images/products/{slug}/{stem}.webp')
    # Legacy normalized path LAST: the curated layout is per-slug dirs, and
    # legacy segments (e.g. products/gallery/x.webp) may only exist as stale
    # copies in STATIC_ROOT (which the dev server does not serve) — preferring
    # them first produced 404ing URLs even when the slug-dir file exists.
    if path.startswith('products/'):
        candidates.append(f'images/{path}')

    hit = _first_static(candidates)
    if hit:
        return hit

    rel = _normalize_static_rel(path)
    return static(rel)


def _product_image_url(product, field_name):
    """Return the best image URL for a product field.

    We prefer committed static assets under static/images/ because those are the
    canonical images checked into the repo and are stable across local dev and
    Vercel. If no static asset exists, fall back to the uploaded media file URL.

    When field_name is 'image' (product card) and the stored path looks like
    a banner image (contains 'bar'/'banner'), prefer non-banner files in the
    slug directory to prevent banner leaks into card slots.
    """
    field = getattr(product, field_name, None)
    if not field or not getattr(field, 'name', None):
        return ''

    slug = getattr(product, 'slug', '')
    field_name_value = str(field.name).replace('\\', '/')
    filename = Path(field_name_value).name
    stem = Path(filename).stem
    clean_filename = strip_hash_suffix(filename)
    clean_stem = Path(clean_filename).stem if clean_filename else ''

    is_banner_like = any(kw in clean_filename.lower() for kw in ('bar', 'banner', 'barnner'))

    candidates = []
    if field_name == 'image' and slug and is_banner_like:
        dir_images = _list_product_dir_images(slug)
        non_banner = [f for f in dir_images
                      if not any(kw in f.lower() for kw in ('bar', 'banner', 'barnner', '3d-view', 'dimension', 'beamangle', 'ordering', 'cert'))]
        if non_banner:
            non_banner.sort(key=lambda f: (0 if clean_stem.lower() in f.lower() else 1, f))
            candidates.append(f'images/products/{slug}/{non_banner[0]}')

    if slug and clean_filename and clean_filename != filename:
        candidates.append(f'images/products/{slug}/{clean_filename}')
    if clean_filename and clean_filename != filename:
        candidates.append(f'images/products/{clean_filename}')
    if slug and clean_stem and clean_stem != stem:
        candidates.append(f'images/products/{slug}/{clean_stem}.webp')
    # Slug-dir candidates BEFORE legacy normalized paths: see
    # _dict_product_image_url — legacy segments may only exist as stale
    # STATIC_ROOT copies the dev server never serves.
    if slug and filename:
        candidates.append(f'images/products/{slug}/{filename}')
    if filename:
        candidates.append(f'images/products/{filename}')
    if slug and stem:
        candidates.append(f'images/products/{slug}/{stem}.webp')
    if field_name_value.startswith('products/'):
        candidates.append(f'images/{field_name_value}')
    if stem and field_name_value.startswith('products/'):
        candidates.append(f'images/{field_name_value.rsplit(".", 1)[0]}.webp')

    hit = _first_static(candidates)
    if hit:
        return hit

    media_url = getattr(field, 'url', '')
    if media_url:
        return media_url

    media_full = os.path.join(settings.MEDIA_ROOT, field_name_value)
    if os.path.isfile(media_full):
        return f'/media/{field_name_value.lstrip("/")}'
    return ''


def _list_product_dir_images(slug):
    """List image files in a product's static directory (cached).

    Delegates to _list_static_dir so the build-time static index is honoured
    when static/ is not present in the function bundle (Vercel).
    """
    if slug in _PRODUCT_DIR_IMAGE_CACHE:
        return _PRODUCT_DIR_IMAGE_CACHE[slug]
    names = _list_static_dir(f'images/products/{slug}')
    results = sorted(
        f for f in names
        if f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif'))
    )
    _PRODUCT_DIR_IMAGE_CACHE[slug] = results
    return results


def _find_project_gallery_files(slug: str):
    """Return list of relative static paths for all gallery images of a project slug.

    Convention: every project keeps its images in images/projects/<slug>/.
    There is intentionally NO cross-directory fallback here: the former
    gallery/ slug-token matching could never match (the concatenated slug is
    always longer than any filename token), so it was dead code. When a
    project directory is missing or empty this returns [] and the caller
    falls back to the raw DB/seed paths; pages/seed_sync.py reports any
    unresolved seed paths at build time so missing assets are committed
    before deploy.
    """
    results = []
    slug_dir = f'images/projects/{slug}'
    slug_files = _list_static_dir(slug_dir)
    exclude = {'old-hid-lighting.webp', 'new-led-lighting.webp'}
    for f in sorted(slug_files):
        fl = f.lower()
        if fl in {e.lower() for e in exclude}:
            continue
        if fl.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
            results.append(f'{slug_dir}/{f}')
    return results


def _find_project_cover_path(slug: str, db_path: str = ''):
    """Find the cover image static path for a project slug.

    A6 note — this is the *display* resolver and deliberately differs from
    ``pages.seed_sync._discover_project_cover``, which is a *repair* helper for
    broken paths. See that function's docstring before attempting to merge them.

    Priority order (highest to lowest):
      1. Exact match on DB-specified filename (clean_name) in slug directory.
      2. Prefix heuristic (cover/main/01/1/hero).
      3. First non-excluded image in slug directory.
      4. Legacy processed/ seed placeholders.
      5. Gallery directory fallback (exact filename match only).
    """
    name = Path(db_path).name if db_path else ''
    clean_name = strip_hash_suffix(name) if name else ''
    slug_dir = f'images/projects/{slug}'
    slug_files = _list_static_dir(slug_dir)
    exclude = {'old-hid-lighting.webp', 'new-led-lighting.webp'}
    priority_prefixes = ['cover', 'main', '01', '1', 'hero']
    if slug_files:
        if clean_name:
            clean_lower = clean_name.lower()
            for f in sorted(slug_files):
                fl = f.lower()
                if not fl.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                    continue
                if fl in exclude:
                    continue
                if strip_hash_suffix(f).lower() == clean_lower:
                    return f'{slug_dir}/{f}'
        for prefix in priority_prefixes:
            for f in sorted(slug_files):
                fl = f.lower()
                if not fl.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                    continue
                if fl in exclude:
                    continue
                stem = fl.rsplit('.', 1)[0]
                if stem.startswith(prefix):
                    return f'{slug_dir}/{f}'
        for f in sorted(slug_files):
            fl = f.lower()
            if not fl.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                continue
            if fl in exclude:
                continue
            return f'{slug_dir}/{f}'
    if clean_name in ('footballfield.webp', 'Baseball.webp', 'basketball.webp', 'soccerfield.webp'):
        processed = f'images/processed/{clean_name}'
        if _find_static(processed):
            return processed
    gallery_dir = 'images/projects/gallery'
    gal_files = _list_static_dir(gallery_dir)
    if gal_files and clean_name:
        # Exact filename match only — no fuzzy slug matching. The former
        # slug-token containment loop could never match (dead code), so it was
        # removed. This exact match still rescues the "DB path is stale but a
        # file with the same (hash-cleaned) name exists in gallery/" case.
        clean_lower = clean_name.lower()
        for f in gal_files:
            if strip_hash_suffix(f).lower() == clean_lower:
                return f'{gallery_dir}/{f}'
    if db_path and db_path.startswith('images/'):
        if _find_static(db_path):
            return db_path
    return ''


def _project_image_url(field, project_slug: str = ''):
    """Return image URL, preferring committed static assets when available."""
    if not field or not getattr(field, 'name', None):
        return ''
    db_path = str(field.name)
    # B1/B2: both arms of the former `if _find_static(...)` / bare-`return`
    # pairs returned the same `static(...)` URL — collapsed to one statement.
    if db_path.startswith('images/'):
        return static(db_path)
    cover = _find_project_cover_path(project_slug, db_path)
    if cover:
        return static(cover)
    media_full = os.path.join(settings.MEDIA_ROOT, db_path)
    if os.path.exists(media_full):
        try:
            return field.url
        except Exception:
            return f'{settings.MEDIA_URL}{db_path.lstrip("/")}'
    try:
        return field.url
    except Exception:
        return ''


def _db_product_cover_url(product):
    """Cover URL for a DB ``Product``: cover_image (FK) -> image -> first gallery.

    Mirrors the seed-path resolver (`_dict_product_image_url` fed with the
    cover_image path) so the two paths agree. Reusing a gallery image as the
    cover means no separate file is served — the URL points at the already-
    committed carousel asset.
    """
    slug = getattr(product, 'slug', '')
    cover = getattr(product, 'cover_image', None)
    if cover and getattr(cover, 'image', None):
        u = _product_image_url(SimpleNamespace(slug=slug, image=cover.image), 'image')
        if u:
            return u
    if getattr(product, 'image', None) and getattr(product.image, 'name', ''):
        u = _product_image_url(product, 'image')
        if u:
            return u
    for img in product.images.all():
        f = getattr(img, 'image', None)
        if f and getattr(f, 'name', ''):
            u = _product_image_url(SimpleNamespace(slug=slug, image=f), 'image')
            if u:
                return u
    return ''


def _db_project_cover_url(project):
    """Cover URL for a DB ``Project``: cover_image (FK) -> image -> first gallery.

    See ``_db_product_cover_url`` for the rationale; same contract as the seed
    path's ``_find_project_cover_path`` (which already falls back to gallery[0]).
    """
    slug = getattr(project, 'slug', '')
    cover = getattr(project, 'cover_image', None)
    if cover and getattr(cover, 'image', None):
        u = _project_image_url(cover.image, slug)
        if u:
            return u
    if getattr(project, 'image', None) and getattr(project.image, 'name', ''):
        u = _project_image_url(project.image, slug)
        if u:
            return u
    for img in project.images.all():
        f = getattr(img, 'image', None)
        if f and getattr(f, 'name', ''):
            u = _project_image_url(f, slug)
            if u:
                return u
    return ''


def _project_gallery_urls(project):
    """Return gallery image URLs for a Project or slug string.

    Always prefers static-committed images so Vercel renders consistently
    with local dev.
    """
    slug = getattr(project, 'slug', project) if not isinstance(project, str) else project
    static_gallery = _find_project_gallery_files(slug)
    urls = [_static_url(p) for p in static_gallery]
    if not isinstance(project, str) and hasattr(project, 'images'):
        try:
            for img in project.images.all():
                fname = getattr(img.image, 'name', '')
                if not fname:
                    continue
                clean = strip_hash_suffix(Path(fname).name)
                found = False
                for u in urls:
                    if clean and clean in u:
                        found = True
                        break
                    if Path(fname).name and Path(fname).name in u:
                        found = True
                        break
                if not found:
                    u = _project_image_url(img.image, slug)
                    if u:
                        urls.append(u)
        except Exception:
            pass
    seen = set()
    deduped = []
    for u in urls:
        if not u or u in seen:
            continue
        seen.add(u)
        deduped.append(u)
    return deduped


class _DictProduct:
    def __init__(self, item):
        self.slug = item.get('slug', '')
        self.name = item.get('name', '')
        self.category = item.get('category', '')
        self.description = item.get('description', '')
        self.power = item.get('power', '')
        self.efficacy = item.get('efficacy', '')
        self.protection = item.get('protection', '')
        self.output = item.get('output', '')
        self.beam_angle = item.get('beam_angle', '')
        self.image = item.get('image', '')
        self.banner_image = item.get('banner_image', '')
        self.dimension_image = item.get('dimension_image', '')
        self.beam_angle_image = item.get('beam_angle_image', '')
        self.order = item.get('order', 0)
        self.translations = item.get('translations', {}) or {}
        self.parent_slug = item.get('parent_slug', '')
        self.gallery_paths = item.get('gallery', [])
        self.specs = item.get('specs', []) or []
        self.energy_data = item.get('energy_data', []) or []
        self.model_number = item.get('model_number', '')
        self.ordering_info = item.get('ordering_info', []) or []
        self.ordering_image = item.get('ordering_image', '')
        self.cert_image = item.get('cert_image', '')
        # 'detail' | 'overview' — picks the public template (see Product.page_layout).
        self.page_layout = item.get('page_layout', 'detail') or 'detail'

    def t(self, field_name, lang='en'):
        return translate(self, field_name, lang)

    def seo_title(self, lang='en'):
        """Seed-path mirror of ``pages.models.Product.seo_title``."""
        explicit = get_seo_override(self, 'seo_title', lang)
        if explicit:
            return explicit
        return build_seo_title(self, lang)

    def seo_description(self, lang='en'):
        """Seed-path mirror of ``pages.models.Product.seo_description``."""
        explicit = get_seo_override(self, 'seo_description', lang)
        if explicit:
            return explicit
        if lang == 'en':
            return build_seo_description(self, lang)
        # Raw body copy is 168-387 chars; the non-English snippet is clamped
        # instead of shipped whole, or /fr/ pages outrun the SERP budget.
        return fit_description(self.t('description', lang))

    @property
    def jsonld_properties(self):
        """Seed-path mirror of ``pages.models.Product.jsonld_properties``.

        Both paths must expose the same attribute name so the two product
        templates render one identical array whether the object came from the
        database or from the committed seed JSON.
        """
        return jsonld_property_pairs(self)


class _DictProject:
    def __init__(self, item):
        self.slug = item.get('slug', '')
        self.title = item.get('title', '')
        self.location = item.get('location', '')
        self.venue_type = item.get('venue_type', '')
        self.sport_type = item.get('sport_type', '')
        self.description = item.get('description', '')
        self.results = item.get('results', '')
        self.image = item.get('image', '')
        self.order = item.get('order', 0)
        self.translations = item.get('translations', {}) or {}
        self.gallery_paths = item.get('gallery', [])
        self.pdf_url = item.get('pdf_url', '')
        # Manual 'Related Products' picked in the admin. Iron law 33:
        # ``getattr`` cannot read a plain dict, so the seed path carries the
        # slugs as a real attribute instead of relying on a M2M manager.
        self.related_product_slugs = item.get('related_product_slugs', []) or []

    def t(self, field_name, lang='en'):
        return translate(self, field_name, lang)

    def seo_title(self, lang='en'):
        """Seed-path mirror of ``pages.models.Project.seo_title``.

        Formula must stay byte-identical to the model: this class backs
        ``IS_VERCEL`` production (``_load_seed()``), so a drift here would show
        the old generic title online only.
        """
        explicit = get_seo_override(self, 'seo_title', lang)
        if explicit:
            return explicit
        return build_project_seo_title(self.title, self.sport_type, lang)

    def seo_description(self, lang='en'):
        """Seed-path mirror of ``pages.models.Project.seo_description``.

        Formula must stay byte-identical to the model — this class backs
        ``IS_VERCEL`` production, so drift here would ship the raw 600-1200
        char body copy online only.
        """
        explicit = get_seo_override(self, 'seo_description', lang)
        if explicit:
            return explicit
        return build_project_seo_description(self.t('description', lang),
                                             self.sport_type, lang)

    def og_description(self, lang='en'):
        """Seed-path mirror of ``pages.models.Project.og_description``."""
        return build_project_og_description(self.title, self.sport_type, lang)