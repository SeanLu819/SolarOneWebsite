import os
import re
import json
import logging
from types import SimpleNamespace
from pathlib import Path
from django.conf import settings
from django.templatetags.static import static

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


def _build_static_file_set():
    """Build a set of all relative static file paths. Cached after first call.
    Eliminates 20-50 filesystem calls per request."""
    global _static_file_set
    if _static_file_set is not None:
        return _static_file_set

    file_set = set()
    dirs_to_scan = []

    static_root = str(settings.STATIC_ROOT)
    if os.path.isdir(static_root):
        dirs_to_scan.append(static_root)

    # Always scan STATICFILES_DIRS (contains git-committed files) so that
    # _find_static works even when collectstatic has not been run (e.g. Vercel).
    # Deduplication against STATIC_ROOT avoids double-counting.
    for d in getattr(settings, 'STATICFILES_DIRS', []):
        d = str(d)
        if os.path.isdir(d) and d not in dirs_to_scan:
            dirs_to_scan.append(d)

    for base_dir in dirs_to_scan:
        for root, _, files in os.walk(base_dir):
            for f in files:
                full = os.path.join(root, f)
                rel = os.path.relpath(full, base_dir)
                rel = rel.replace('\\', '/')
                file_set.add(rel)

    _static_file_set = file_set
    logger.info(f'Built static file cache: {len(file_set)} files')
    return file_set


def _find_static(rel_path):
    """O(1) lookup in cached static file set. No filesystem I/O after first call."""
    rel_path = rel_path.replace('\\', '/')
    return rel_path in _build_static_file_set()


def _list_static_dir(rel_dir):
    """List files in a static directory with caching. Eliminates repeated os.listdir() calls."""
    if rel_dir in _dir_listing_cache:
        return _dir_listing_cache[rel_dir]

    results = set()
    dirs_to_check = []

    base = os.path.join(settings.BASE_DIR, 'static', rel_dir)
    dirs_to_check.append(base)

    if not settings.DEBUG:
        static_root = os.path.join(str(settings.STATIC_ROOT), rel_dir)
        if static_root not in dirs_to_check:
            dirs_to_check.append(static_root)

    for d in dirs_to_check:
        if os.path.isdir(d):
            for f in os.listdir(d):
                results.add(f)

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


def _clean_hashed_name(name: str) -> str:
    """Strip Django-upload hashed suffix like _yPJsGNE or _jlmQVlR from filename.

    Django's default storage appends a 7-char alphanumeric hash when a file
    with the same name already exists. We match that exact pattern.
    """
    if not name:
        return ''
    try:
        stem = name.rsplit('.', 1)[0]
        ext = name.rsplit('.', 1)[-1]
    except (ValueError, IndexError):
        return name
    m = re.search(r'_([a-zA-Z0-9]{7})$', stem)
    if m:
        stem = stem[:m.start()]
    return f'{stem}.{ext}'


def _static_url(path):
    """Return static URL for a non-empty path. Accepts a wide variety of
    legacy or canonical paths and normalizes them to a Django static URL.
    Falls back gracefully to a URL even if the file is not found (prevents
    blank src attributes — useful while assets are being added)."""
    if not path:
        return ''
    if isinstance(path, str) and path.startswith(('http://', 'https://')):
        return path
    if isinstance(path, str) and path.startswith(('/static/', '/media/')):
        return path
    rel = _normalize_static_rel(path)
    if _find_static(rel):
        return static(rel)
    return static(rel)


def _dict_product_image_url(path, slug):
    """Return static URL for a _DictProduct image field, trying multiple path combinations."""
    if not path:
        return ''
    if isinstance(path, str) and path.startswith(('http://', 'https://')):
        return path
    if isinstance(path, str) and path.startswith(('/static/', '/media/')):
        return path

    path = str(path).replace('\\', '/')
    filename = Path(path).name
    stem = Path(filename).stem
    clean_filename = _clean_hashed_name(filename)
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
    if path.startswith('products/'):
        candidates.append(f'images/{path}')
    if slug and filename:
        candidates.append(f'images/products/{slug}/{filename}')
    if slug and stem:
        candidates.append(f'images/products/{slug}/{stem}.webp')

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if _find_static(candidate):
            return static(candidate)

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
    clean_filename = _clean_hashed_name(filename)
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
    if field_name_value.startswith('products/'):
        candidates.append(f'images/{field_name_value}')
    if slug and filename:
        candidates.append(f'images/products/{slug}/{filename}')
    if filename:
        candidates.append(f'images/products/{filename}')
    if slug and stem:
        candidates.append(f'images/products/{slug}/{stem}.webp')
    if stem and field_name_value.startswith('products/'):
        candidates.append(f'images/{field_name_value.rsplit(".", 1)[0]}.webp')

    seen = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if _find_static(candidate):
            return static(candidate)

    media_url = getattr(field, 'url', '')
    if media_url:
        return media_url

    media_full = os.path.join(settings.MEDIA_ROOT, field_name_value)
    if os.path.isfile(media_full):
        return f'/media/{field_name_value.lstrip("/")}'
    return ''


def _list_product_dir_images(slug):
    """List image files in a product's static directory (cached)."""
    if slug in _PRODUCT_DIR_IMAGE_CACHE:
        return _PRODUCT_DIR_IMAGE_CACHE[slug]
    results = []
    dirs_to_check = []
    static_root = str(getattr(settings, 'STATIC_ROOT', ''))
    if static_root:
        dirs_to_check.append(os.path.join(static_root, 'images', 'products', slug))
    for d in getattr(settings, 'STATICFILES_DIRS', []):
        dirs_to_check.append(os.path.join(str(d), 'images', 'products', slug))
    for d in dirs_to_check:
        if os.path.isdir(d):
            try:
                for f in os.listdir(d):
                    if f.lower().endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                        results.append(f)
                break
            except OSError:
                pass
    _PRODUCT_DIR_IMAGE_CACHE[slug] = results
    return results


def _find_project_gallery_files(slug: str):
    """Return list of relative static paths for all gallery images of a project slug.

    Resolution order:
      1. images/projects/<slug>/ directory (primary — every project should have its own dir)
      2. images/projects/gallery/ fallback (slug-token matching for legacy projects)
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
    if not results:
        gallery_dir = 'images/projects/gallery'
        gal_files = _list_static_dir(gallery_dir)
        slug_token = slug.replace('-', '').replace('_', '').lower()
        matched = []
        for f in sorted(gal_files):
            fl = f.lower()
            if not fl.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                continue
            f_token = fl.rsplit('.', 1)[0].replace('-', '').replace('_', '').lower()
            if slug_token and slug_token in f_token:
                matched.append(f'{gallery_dir}/{f}')
        if matched:
            results = matched
    return results


def _find_project_cover_path(slug: str, db_path: str = ''):
    """Find the cover image static path for a project slug.

    Priority order (highest to lowest):
      1. Exact match on DB-specified filename (clean_name) in slug directory.
      2. Prefix heuristic (cover/main/01/1/hero).
      3. First non-excluded image in slug directory.
      4. Legacy processed/ seed placeholders.
      5. Gallery directory fallback (exact name then slug token match).
    """
    name = Path(db_path).name if db_path else ''
    clean_name = _clean_hashed_name(name) if name else ''
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
                if _clean_hashed_name(f).lower() == clean_lower:
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
    if gal_files:
        if clean_name:
            clean_lower = clean_name.lower()
            for f in gal_files:
                if _clean_hashed_name(f).lower() == clean_lower:
                    return f'{gallery_dir}/{f}'
        slug_token = slug.replace('-', '').replace('_', '').lower()
        for f in sorted(gal_files):
            fl = f.lower()
            if not fl.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                continue
            f_token = fl.rsplit('.', 1)[0].replace('-', '').replace('_', '').lower()
            if slug_token and slug_token in f_token:
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
    if db_path.startswith('images/'):
        if _find_static(db_path):
            return static(db_path)
        return static(db_path)
    cover = _find_project_cover_path(project_slug, db_path)
    if cover and _find_static(cover):
        return static(cover)
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
                clean = _clean_hashed_name(Path(fname).name)
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

    def t(self, field_name, lang='en'):
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')


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

    def t(self, field_name, lang='en'):
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')