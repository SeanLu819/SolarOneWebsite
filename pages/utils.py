"""Shared static-path helpers — single source of truth for hash-suffix stripping.

``strip_hash_suffix`` is the ONE canonical implementation (pure stdlib, no Django
imports) of the Django-upload hash-suffix stripper. ``pages.models._clean_hashed_filename``
is a retained convenience wrapper that additionally applies ``os.path.basename`` so
callers re-add the slug directory themselves. The two pure pass-through wrappers
(``pages.views.utils._clean_hashed_name`` and ``pages.seed_sync._strip_hash_suffix``)
were removed in A8 — their call sites now use ``strip_hash_suffix`` directly. The
inline ``re``-based ``_dest_name`` helpers in ``pages.models`` / ``pages.admin.project``
were also removed in A8 and routed to ``_clean_hashed_filename``. Keeping the logic
here avoids circular-import risk.
"""
import os
import re

# Django's default storage appends a 7-char alphanumeric hash when a file with
# the same name already exists, e.g. "fl1m-01_abcX123.webp".
_HASH_SUFFIX_RE = re.compile(r'_([a-zA-Z0-9]{7})$')


def strip_hash_suffix(name):
    """Strip a Django upload hash suffix from a file name.

    Matches the ``_<7 alphanumeric chars>`` token at the end of the file stem
    (e.g. ``fl1m-01_abcX123.webp`` -> ``fl1m-01.webp``). Preserves any directory
    component and returns '' for empty/None input. The extension is rejoined
    exactly as-is, so the function is safe for both bare file names and
    relative paths.
    """
    if not name:
        return ''
    name = str(name)
    stem, ext = os.path.splitext(name)
    match = _HASH_SUFFIX_RE.search(stem)
    if match:
        stem = stem[:match.start()]
    return f'{stem}{ext}'


def translate(obj, field, lang='en'):
    """Return ``obj``'s ``field`` translated into ``lang``, else the default value.

    A7 single source: ``Product.t`` / ``Project.t`` (pages.models) and the seed
    shims ``_DictProduct.t`` / ``_DictProject.t`` (pages.views.utils) all carried
    a byte-identical body. ``obj`` must expose ``.translations`` (a
    ``{lang: {field: value}}`` map) and ``field`` as an attribute; missing/empty
    translations fall back to the attribute value, so behaviour is unchanged.
    Pure stdlib (no Django import) — safe to import from models and views alike.
    """
    translations = getattr(obj, 'translations', None)
    if lang == 'en' or not translations:
        return getattr(obj, field, '')
    val = (translations.get(lang) or {}).get(field, '')
    return val if val else getattr(obj, field, '')
