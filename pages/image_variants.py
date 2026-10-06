"""Responsive image variant generation + srcset helpers (SEO/GEO batch C, v1.10.18).

Problem
-------
`static/images/` holds 295 images / 34.7 MB. The render box is at most 1248px
wide, yet 241 source images are 1920px wide and are served 1:1 to cards/hero via
a single ``src``. A card shown at ~342px on desktop (or ~360px on a phone)
downloads the full 1920px file, then the browser downscales it — 4–10x more
bytes than necessary, and blurry on 2x/3x retina.

Approach
--------
For every source image we generate up to three width variants
(``360 / 720 / 1248``) and emit ``<img srcset sizes>`` so the browser picks the
right one for the device pixel ratio and the CSS slot.

Variant files live in a **separate, mirrored** directory tree
``static/images/_variants/<cat>/<slug>/<name>@<w>w.webp`` — NEVER next to the
source. Rationale (see pages/views/utils.py gallery/cover enumeration): project
gallery + cover resolution still ``os.listdir`` the per-slug directory
(``images/projects/<slug>/``), so putting ``@<w>w`` files beside the originals
would pollute the gallery and could be chosen as a cover. The mirrored
``_variants`` tree is never enumerated by any of that code, and it does not
touch ``test_listing_matches_live_static_dir_exactly`` (which only inspects a
specific slug directory).

The variants are **build-time artifacts, not committed** (added to .gitignore);
``scripts/gen_image_variants.py`` runs in ``build.sh`` *before* collectstatic so
the hashed manifest includes them, and locally before preview.

URLs
----
``image_url`` (already a ``/static/...`` URL, possibly content-hashed in
production) is reversed to a canonical relative path (``images/...`` with the
hash stripped), then the variant relative path is derived and run through
Django's ``static()`` so it resolves correctly in both dev (unhashed) and prod
(hashed) — no runtime filesystem existence check (the function bundle on Vercel
excludes ``static/``).
"""
import os
import re

# Width candidates offered to the browser. 360 = card 1x, 720 = card 2x,
# 1248 = hero / large (matches the site's max render width).
SRCSET_WIDTHS = (360, 720, 1248)

# Variants live under this mirrored sub-tree of static/images.
_VARIANT_ROOT = '_variants'

# Width marker inserted before the extension. 🔴 Must be URL-safe: an earlier
# `@360w` marker got percent-encoded by Django's static() into `%40360w`,
# producing URLs that the width-descriptor parser (and the CDN) mis-handle.
# `~` is in RFC 3986's unreserved set and is left untouched by static().
_WIDTH_SEP = '~'

# Source category sub-directories under static/images that get variants.
# 🔴 `products_page` is NOT optional — /products/ renders its banner from
# static/images/products_page/, and omitting it left those cards srcset-less.
CATEGORIES = ('products', 'projects', 'news', 'products_page')

# Content-hash segment inserted by ManifestStaticFilesStorage: name.<hash>.ext.
_HASH_RE = re.compile(r'\.([a-f0-9]{8,32})\.')


def _lanczos():
    res = getattr(__import__('PIL.Image', fromlist=['Resampling']), 'Resampling', None)
    if res is not None:
        return res.LANCZOS
    import PIL.Image as _IM  # noqa: WPS433 - fallback for older Pillow
    return _IM.LANCZOS


def strip_hash_suffix(name):
    """Remove a ManifestStaticFilesStorage hash segment from a filename.

    ``hero-main-1.abc123.webp`` -> ``hero-main-1.webp``. Idempotent for names
    that already have no hash.
    """
    return _HASH_RE.sub('.', name, 1)


def canonical_rel_from_url(url):
    """Reverse a ``/static/...`` (possibly hashed) URL to a canonical relative
    static path such as ``images/products/<slug>/<name>.webp``.

    Returns '' for empty / non-static URLs.

    🔴 v1.10.23 — a ``/media/...`` URL must return '' here, not its own path.
    The variant generator only ever wrote files under ``static/images/``, so a
    media upload has no ``~360w`` sibling anywhere. The earlier version passed
    the path straight through, ``static()`` then prefixed it, and the browser
    was handed ``/static/media/products_page/VSP9M-01~360w.webp`` — a 404 the
    crawler and the visitor both see, because a browser that supports ``srcset``
    picks a candidate from it rather than the ``src`` beside it. It rendered on
    ``/products/`` and on the new stadium page, whose VSP card resolves through
    the media fallback on the local DB path. Returning '' makes ``build_srcset``
    emit nothing, so the template omits the attribute and the browser falls
    back to the working ``src``.

    Production note: ``media/`` is excluded from the Vercel function bundle, so
    a media-backed image is broken online regardless. That is a separate,
    already-recorded problem — this function just stops making it worse.
    """
    if not url:
        return ''
    if url.startswith('/media/') or url.startswith('media/'):
        return ''
    if url.startswith(('http://', 'https://', '//')):
        # A CDN or third-party URL. It is already absolute and final; there is
        # no local variant to point at, and ``static()`` would turn it into
        # ``/static/https:/...``. ``_passthrough_url`` hands these through
        # verbatim, so they really do reach this function.
        return ''
    if '/static/' in url:
        rel = url.split('/static/', 1)[1]
    elif url.startswith('/'):
        # An absolute path that is neither /static/ nor /media/ is a CDN or
        # third-party URL; it has no local variant either.
        return ''
    else:
        rel = url
    head, tail = os.path.splitext(rel) if '/' in rel else ('', rel)
    # split into dir + filename for hash stripping
    if '/' in rel:
        d, fn = rel.rsplit('/', 1)
        fn = strip_hash_suffix(fn)
        rel = d + '/' + fn
    else:
        rel = strip_hash_suffix(rel)
    return rel


def variant_rel(canonical_rel, width):
    """Canonical relative path -> variant relative path under ``_variants/``.

    ``images/products/x/name.webp`` -> ``images/_variants/products/x/name~360w.webp``.
    """
    if not canonical_rel:
        return ''
    mirrored = canonical_rel.replace('images/', 'images/%s/' % _VARIANT_ROOT, 1)
    d, ext = os.path.splitext(mirrored)
    return '%s%s%dw%s' % (d, _WIDTH_SEP, width, ext)


def _variant_abs(src_abs, width):
    """Source absolute path -> variant absolute path (mirrored, with ~<w>w).

    Separator-agnostic on purpose: the mirrored ``_variants`` segment is
    inserted by splitting the path on its components. A naive
    ``src_abs.replace('static/images/', ...)`` silently no-ops on Windows,
    where ``os.path.join`` yields backslashes — that writes the variants NEXT
    TO THE SOURCE and pollutes the gallery enumeration, which is exactly what
    this layout exists to prevent.
    """
    parts = os.path.normpath(src_abs).split(os.sep)
    if 'images' not in parts:
        return ''
    i = len(parts) - 1 - parts[::-1].index('images')
    mirrored = parts[:i + 1] + [_VARIANT_ROOT] + parts[i + 1:]
    d, ext = os.path.splitext(os.sep.join(mirrored))
    return '%s%s%dw%s' % (d, _WIDTH_SEP, width, ext)


def ensure_variants(src_abs, widths=SRCSET_WIDTHS, quality=82):
    """Generate missing responsive variants for one source image on disk.

    Idempotent: skips widths whose variant file already exists. A variant is
    never upscaled — its width is ``min(width, source_width)`` — so small source
    images still get valid (same-size) variants instead of blurry enlargements.
    Returns the list of variant paths created (empty if none / source missing).
    """
    if not os.path.isfile(src_abs):
        return []
    # Layout guard: a variant MUST land inside a `_variants` directory. If the
    # mirror computation ever degrades (e.g. a path without an `images`
    # component), fail loudly instead of writing next to the source — a silent
    # no-op here would report "0 variants" and read as a green run.
    probe = _variant_abs(src_abs, widths[0])
    if not probe or _VARIANT_ROOT not in probe.split(os.sep):
        raise ValueError(
            'variant path escaped the _variants tree: src=%r -> %r' % (src_abs, probe))
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover - Pillow is a hard dep at build time
        return []
    try:
        with Image.open(src_abs) as im:
            src_w, src_h = im.size
            created = []
            for w in widths:
                tw = min(w, src_w)
                if tw <= 0:
                    continue
                vabs = _variant_abs(src_abs, w)
                if os.path.exists(vabs):
                    continue
                scale = tw / float(src_w)
                th = max(1, int(round(src_h * scale)))
                resized = im.resize((tw, th), _lanczos())
                os.makedirs(os.path.dirname(vabs), exist_ok=True)
                resized.save(vabs, 'WEBP', quality=quality)
                created.append(vabs)
            return created
    except Exception:  # noqa: BLE001 - generation is best-effort; never fatal
        return []


def recompress_if_oversize(src_abs, threshold=200 * 1024, quality=82):
    """C0 precursor: shrink source images that exceed the >200KB budget.

    Only re-encodes in place (same extension, so existing references stay
    valid): webp -> webp q82, png -> png optimize, jpg -> jpg q82. Skips files
    already at/under the threshold and files we cannot safely re-encode.
    Returns True if the file was rewritten.
    """
    if not os.path.isfile(src_abs):
        return False
    if os.path.getsize(src_abs) <= threshold:
        return False
    ext = os.path.splitext(src_abs)[1].lower()
    try:
        from PIL import Image
    except ImportError:  # pragma: no cover
        return False
    try:
        with Image.open(src_abs) as im:
            if ext == '.webp':
                im.save(src_abs, 'WEBP', quality=quality)
            elif ext == '.png':
                im.save(src_abs, 'PNG', optimize=True)
            elif ext in ('.jpg', '.jpeg'):
                im.save(src_abs, 'JPEG', quality=quality)
            else:
                return False
        return True
    except Exception:  # noqa: BLE001
        return False


def generate_all(base_dir=None, categories=CATEGORIES,
                widths=SRCSET_WIDTHS, quality=82, threshold=200 * 1024,
                skip_dirs=('_variants', '_source', 'processed'),
                recompress=False):
    """Walk the source image categories and (re)generate all variants.

    ``recompress`` is opt-in: when True, oversize SOURCE images are also
    re-encoded in place (part of the separate C0 size budget). It defaults to
    False so a local/batch-C run only ADDS variant files and never dirties the
    tracked source images in the working tree. (The C0 source recompression is
    a deliberate, separately-reviewed change.)
    """
    """Walk the source image categories and (re)generate all variants + recompress
    oversize sources. Returns a summary dict (counts). Safe to run repeatedly.
    """
    if base_dir is None:
        # pages/image_variants.py -> repo root
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'images')
    summary = {'sources': 0, 'variants_created': 0, 'recompressed': 0, 'skipped': 0}
    for cat in categories:
        cat_dir = os.path.join(base_dir, cat)
        if not os.path.isdir(cat_dir):
            continue
        for dirpath, dirnames, filenames in os.walk(cat_dir):
            # prune skipped sub-trees in place so we never recurse into _variants
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fn in filenames:
                if not fn.lower().endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                    continue
                src = os.path.join(dirpath, fn)
                summary['sources'] += 1
                if recompress and recompress_if_oversize(src, threshold=threshold, quality=quality):
                    summary['recompressed'] += 1
                made = ensure_variants(src, widths=widths, quality=quality)
                summary['variants_created'] += len(made)
    return summary


# --- Django-side helpers (only call these inside a Django process) ---

def build_srcset(image_url, widths=SRCSET_WIDTHS):
    """Return an ``srcset`` attribute value (no ``srcset=`` prefix) for an
    ``image_url``. Each candidate is ``<static-url> <w>w``. Returns '' when the
    url is empty (caller should then omit the attribute)."""
    if not image_url:
        return ''
    from django.templatetags.static import static
    canonical = canonical_rel_from_url(image_url)
    if not canonical:
        return ''
    parts = []
    for w in widths:
        rel = variant_rel(canonical, w)
        if not rel:
            continue
        parts.append('%s %dw' % (static(rel), w))
    return ', '.join(parts)


def build_src(image_url, default_width=720):
    """Return the ``src`` attribute value (a single variant URL) for an
    ``image_url``. Defaults to the 720w variant (good 1x/2x fallback); callers
    may pass 1248 for a hero slot."""
    if not image_url:
        return ''
    from django.templatetags.static import static
    canonical = canonical_rel_from_url(image_url)
    if not canonical:
        return ''
    return static(variant_rel(canonical, default_width))
