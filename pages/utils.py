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


#: Ordered ``(PropertyValue.name, Product attribute)`` pairs emitted as the
#: Product JSON-LD ``additionalProperty`` array. Order is part of the emitted
#: contract — search engines surface the values in array order — so the pair
#: order here IS the output order.
#:
#: ``category_t`` is the translated display label the templates already render
#: (set by ``_enrich_product``); the rest are raw spec fields.
JSONLD_PROPERTY_FIELDS = (
    ('Power', 'power'),
    ('Efficacy', 'efficacy'),
    ('Output', 'output'),
    ('Beam Angle', 'beam_angle'),
    ('Protection', 'protection'),
    ('Category', 'category_t'),
)


def jsonld_property_pairs(obj):
    """Return the non-empty ``(label, value)`` pairs for Product JSON-LD.

    A6 single source for the Product ``additionalProperty`` array, which the
    two product templates used to hand-assemble in Django template syntax:
    each intermediate entry carried its own trailing ``{% if %},`` and only the
    final ``Category`` entry was unconditional, so deleting or re-ordering that
    last entry reproduced the P0-1 trailing-comma bug verbatim.

    Building the list in Python means an empty field is simply absent and the
    template can never emit a trailing comma. Empty/falsy values are skipped so
    the advertised property set tracks real data.

    Pure Python (no Django import) so both ``pages.models.Product`` and the
    seed shim ``pages.views.utils._DictProduct`` can use it without circular
    imports — see ``translate`` above for the same constraint.
    """
    pairs = []
    for label, field in JSONLD_PROPERTY_FIELDS:
        value = getattr(obj, field, '')
        if not value:
            continue
        pairs.append((label, str(value)))
    return pairs


# ---------------------------------------------------------------------------
# Per-page SEO (B3 batch): category keyword map + title/description formulas.
#
# Pure-Python (no Django import) so ``pages.models.Product`` / ``Project`` and
# the seed shims ``_DictProduct`` / ``_DictProject`` can import them without
# circular imports — same constraint as ``translate`` above.
#
# Design note (deliberate): ``seo_title`` / ``seo_description`` are stored
# inside the existing ``translations`` JSON (per language) — NOT as new DB
# columns. This reuses the established 3rd i18n mechanism, needs no migration,
# and needs no seed_sync schema change (``translations`` is already synced
# DB<->seed). The formulas below are the *fallback* when no explicit
# translation is set, so editors can override any page later (B4/C1 content
# work) without touching code.
# ---------------------------------------------------------------------------

#: Category -> SEO keyword phrase (English). Leading token of the product
#: <title> and folded into the meta description. Mirrors the 8
#: ``Product.CATEGORY_CHOICES`` keys; an unmapped category falls back to ''.
#:
#: Phrases are chosen against measured search demand, not internal taxonomy.
#: SPORTS_LIGHTING used to read "LED Sports Stadium Lighting" (internal label
#: 'Sports Lighting System'); SEMrush US data (2026-09-29) shows the demand sits
#: on ``stadium lights`` (2,900/mo) and ``led stadium lights`` (1,000/mo, KD 6 —
#: our best difficulty/volume trade), so the phrase was re-cut to the wording
#: buyers actually type. The old wording ranked for neither phrase exactly.
#: 2026-09-30: singular "LED Stadium Light" — the PLURAL head phrase belongs to
#: the /products/sports-lighting/ hub (one keyword, one page); product-detail
#: titles take the singular family so the two page types stop bidding on the
#: same query. Descriptions keep a natural "stadium lights" mention.
CATEGORY_KEYWORD = {
    'AREA_SITE': 'LED Area & Site Lighting',
    'SPORTS_LIGHTING': 'LED Stadium Light',
    'FLOODLIGHT': 'LED Flood Lights',
    'HIGHBAY_LOWBAY': 'High Bay & Low Bay LED Lights',
    'ROADWAY': 'LED Roadway & Street Lights',
    'ACCESSORY': 'LED Lighting Accessories',
    'MODULAR': 'Modular LED Lighting',
    'OTHER': 'LED Lighting Solutions',
}

#: Optional per-slug keyword override for exceptional products whose category
#: label is a poor search phrase. Empty by default — B3 wires the mechanism,
#: individual overrides land with B4/C1 content work.
SLUG_KEYWORD_OVERRIDE = {}

#: Brand token — never translated (project convention: ``SolarOne`` stays).
_SEO_BRAND = 'SolarOne'


def get_seo_override(obj, field, lang='en'):
    """Read an explicit ``seo_title`` / ``seo_description`` override from the
    object's ``translations`` map — WITHOUT going through ``translate()``.

    Why not ``translate()`` / ``obj.t()``: those fall back to
    ``getattr(obj, field)`` for English, and ``obj`` now has a method named
    ``seo_title`` / ``seo_description``, so ``getattr`` would return the bound
    method (truthy) and the override check would never fall through to the
    formula. Reading the ``translations`` dict directly sidesteps that name
    collision entirely.
    """
    translations = getattr(obj, 'translations', None)
    if not isinstance(translations, dict):
        return ''
    entry = translations.get(lang) or {}
    return (entry or {}).get(field, '') or ''


def _seo_keyword(obj, lang='en'):
    """Localized SEO keyword phrase for ``obj``.

    Slug override wins (English only), then the category map. For non-English
    the category keyword is localized via the object's translated category
    label; full per-language keyword phrasing is B8/E2 (later batch).
    """
    slug = getattr(obj, 'slug', '') or ''
    override = SLUG_KEYWORD_OVERRIDE.get(slug)
    if override and lang == 'en':
        return override
    cat = getattr(obj, 'category', '') or ''
    kw = CATEGORY_KEYWORD.get(cat, '')
    if lang == 'en' or not kw:
        return kw
    localized = obj.t('category', lang) if hasattr(obj, 't') else kw
    return localized or kw


def _seo_identifier(obj):
    """The unique token guaranteeing title/description uniqueness."""
    return (getattr(obj, 'model_number', '')
            or getattr(obj, 'name', '')
            or getattr(obj, 'title', '')
            or '')


def build_seo_title(obj, lang='en'):
    """B4 title formula: ``{品类词} {型号} — {关键参数} | SolarOne``.

    Keyword leads so the page ranks for the category phrase; the model/name
    identifier follows; power is appended only when not already inside the
    identifier (some ``model_number`` codes embed wattage).
    """
    kw = _seo_keyword(obj, lang)
    identifier = _seo_identifier(obj)
    power = (getattr(obj, 'power', '') or '').strip()
    if kw and identifier:
        core = f'{kw} {identifier}'
    elif identifier:
        core = identifier
    elif kw:
        core = kw
    else:
        core = _SEO_BRAND
    if power and power not in core:
        core = f'{core} — {power}'
    return f'{core} | {_SEO_BRAND}'


def build_seo_description(obj, lang='en'):
    """B5 description formula: unique, 50–160 chars (English baseline).

    The identifier is always embedded, guaranteeing uniqueness across the 24
    product pages even when specs are sparse. Non-English callers fall back to
    the translated ``description`` at the model-method level, not here. B4/C1
    will replace these with richer, hand-written per-page prose.
    """
    kw = _seo_keyword(obj, lang)
    identifier = _seo_identifier(obj)
    power = (getattr(obj, 'power', '') or '').strip()
    bit = f'{_SEO_BRAND} {identifier}'.rstrip()
    if kw:
        bit = f'{bit} {kw}'.rstrip()
    desc = bit
    if power:
        desc = f'{desc} delivers {power} of high-efficiency LED output'
    desc = (f'{desc} for professional sports, industrial and commercial '
            f'lighting projects.')
    if len(desc) > 160:
        desc = desc[:157].rstrip() + '...'
    return desc
