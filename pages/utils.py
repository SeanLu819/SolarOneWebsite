"""Shared static-path helpers (v1.5.9, D3).

A single canonical implementation of the Django-upload hash-suffix stripper,
previously duplicated in three places
(``pages.views.utils._clean_hashed_name``,
 ``pages.models._clean_hashed_filename``,
 ``pages.seed_sync._strip_hash_suffix``).

Keeping it here (pure stdlib, no Django imports) avoids circular-import risk
and lets those modules delegate to one source of truth.
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
