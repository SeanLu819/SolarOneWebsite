"""Cross-linking bridges between products, projects and news (SEO batch B2).

There is no foreign key between ``Product`` and ``Project`` in the seed data, so
"related" items are derived *deterministically* from the existing taxonomy:

* a product ``category`` maps back to the project ``sport_type`` / ``venue_type``
  values it serves (the product page's "Application Cases");

* a project's "Related Products" is **manual only** -- the editor picks the
  luminaires in the admin (``Project.related_products``). The old category-based
  auto match was deleted: it iterated a ``set`` (so the same project showed
  different products between processes) and paired venues with luminaires the
  business never used there. No pick means no section at all.

Both the database path and the seed-JSON path are served through
``get_projects`` / ``get_all_products`` (which enrich the objects identically),
so the same helper produces correct links on Vercel and in local dev without
any model dual-path duplication. News links are keyword-matched against
explicit product model numbers / project slugs so we never emit a weak generic
link.
"""
from pages.views.data_loaders import get_projects, get_all_products


# reverse: product category -> project sport_types that use it
#
# Used by ``related_projects_for_product`` (a product page's "Application
# Cases"). It is no longer the inverse of anything: a project's "Related
# Products" is picked by hand, so these two directions are independent.
PRODUCT_CATEGORY_TO_PROJECT_SPORTS = {
    'SPORTS_LIGHTING': [
        'FOOTBALL_FIELD', 'SOCCER_FIELD', 'BASEBALL_FIELD', 'TRACK_FIELD',
        'VELODROME', 'MULTI_SPORT', 'ICE_ARENA', 'AQUATICS_CENTRE',
        'KARTING', 'SKI_AREA',
    ],
    'ROADWAY': ['ROADWAY', 'CITY_EXPRESSWAY'],
    'AREA_SITE': ['AIRPORT'],
    'FLOODLIGHT': [
        'TENNIS_COURTS', 'TENNIS', 'BASKETBALL', 'FENCING', 'PICKLEBALL',
        'KARTING', 'SKI_AREA', 'CITY_EXPRESSWAY', 'ROADWAY', 'AIRPORT',
    ],
    'HIGHBAY_LOWBAY': [
        'MULTI_SPORT', 'ICE_ARENA', 'AQUATICS_CENTRE', 'TENNIS', 'BASKETBALL',
        'FENCING', 'PICKLEBALL',
    ],
    'ACCESSORY': [],
    'MODULAR': [],
    'OTHER': [],
}

# reverse: product category -> project venue_types that use it
PRODUCT_CATEGORY_TO_PROJECT_VENUES = {
    'AREA_SITE': ['INFRASTRUCTURE'],
    'ROADWAY': ['ROADWAY'],
    'HIGHBAY_LOWBAY': ['INDOOR'],
}


def related_products_for_project(project, lang='en'):
    """The products an editor picked for this project — manual only.

    No automatic matching and no fallback: when nothing is picked the section
    must disappear from the page. The DB path reads the M2M (ordered by
    ``Product.Meta``); the seed path reads the exported ``related_product_slugs``
    list. Both are plain ordered sequences — the previous ``set`` iteration made
    the same project show different products on every process start.
    """
    manager = getattr(project, 'related_products', None)
    if manager is not None and hasattr(manager, 'all'):
        slugs = [p.slug for p in manager.all()]
    else:
        slugs = list(getattr(project, 'related_product_slugs', None) or [])
    if not slugs:
        return []
    by_slug = {p.slug: p for p in get_all_products(lang)}
    return [by_slug[s] for s in slugs if s in by_slug]


def related_projects_for_product(product, lang='en', limit=3):
    """Projects whose sport/venue type matches this product's category."""
    sports = PRODUCT_CATEGORY_TO_PROJECT_SPORTS.get(
        getattr(product, 'category', ''), [])
    venues = PRODUCT_CATEGORY_TO_PROJECT_VENUES.get(
        getattr(product, 'category', ''), [])
    if not sports and not venues:
        return []
    sport_filter = ','.join(sports) if sports else ''
    venue_filter = venues[0] if venues else ''
    seen = set()
    out = []
    for p in get_projects(lang, active_venue_type=venue_filter,
                          active_sport_type=sport_filter):
        if p.slug in seen:
            continue
        seen.add(p.slug)
        out.append(p)
        if len(out) >= limit:
            break
    return out


def _news_text(article):
    return ((article.get('title') or '') + ' ' + (article.get('content') or '')).lower()


def related_items_for_news(article, lang='en', limit=2):
    """Products/projects explicitly named in a news article.

    Only emits a link when the article text contains a real product model
    number / slug or a project's exact slug or title. ``get_all_products``
    includes sub-series, so a model number like ``FL6M-480W`` resolves to the
    ``/products/fl6m/`` page. We never invent a weak generic link -- the bare
    word "airport" must not pull in an unrelated airport project, so a Tianjin
    airport case study does not fabricate a Beijing airport link.
    """
    text = _news_text(article)
    if not text:
        return [], []

    rel_products, pseen = [], set()
    for p in get_all_products(lang):
        terms = {p.slug}
        mn = (getattr(p, 'model_number', '') or '').lower()
        if mn:
            terms.add(mn)
            # Progressive leading prefixes of the model number so an article that
            # names "FL6M-480W" matches the product whose model is
            # "FL6M-480W-30K-S", but a trailing fragment like "YP" (or any
            # non-leading token) can never match on its own and fabricate a link.
            segs = mn.split('-')
            for i in range(len(segs), 0, -1):
                prefix = '-'.join(segs[:i])
                if len(prefix) >= 3:
                    terms.add(prefix)
        if '-' in p.slug:
            terms.add(p.slug.replace('-', ' '))
        if any(t and t in text for t in terms) and p.slug not in pseen:
            pseen.add(p.slug)
            rel_products.append(p)
            if len(rel_products) >= limit:
                break

    rel_projects, jseen = [], set()
    for p in get_projects(lang):
        # Exact slug or exact title only -- never a generic keyword, so a
        # Tianjin-airport case study does not fabricate a Beijing-airport link.
        terms = {p.slug, (p.title or '').lower()}
        if any(t and t in text for t in terms) and p.slug not in jseen:
            jseen.add(p.slug)
            rel_projects.append(p)
            if len(rel_projects) >= limit:
                break

    return rel_products, rel_projects
