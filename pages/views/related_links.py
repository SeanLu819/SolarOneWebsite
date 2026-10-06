"""Cross-linking bridges between products, projects and news (SEO batch B2).

There is no foreign key between ``Product`` and ``Project`` in the seed data, so
"related" items are derived *deterministically* from the existing taxonomy:

* a project's ``sport_type`` / ``venue_type`` maps to one or more product
  ``category`` codes (sports venues -> SPORTS_LIGHTING, roadways -> ROADWAY,
  airports/infrastructure -> AREA_SITE, indoor venues -> HIGHBAY_LOWBAY, ...);
* the reverse map sends a product ``category`` back to the project
  ``sport_type`` / ``venue_type`` values it serves.

Both the database path and the seed-JSON path are served through
``get_products`` / ``get_projects`` (which enrich the objects identically), so
the same helper produces correct links on Vercel and in local dev without any
model dual-path duplication. News links are keyword-matched against explicit
product model numbers / project slugs so we never emit a weak generic link.
"""
from pages.views.data_loaders import get_products, get_projects, get_all_products


# sport_type -> product category codes (a venue of this sport needs these lights)
#
# Refined with the client's real-world association rule (batch B2): venue size
# drives the recommendation. Large outdoor venues (football / soccer / baseball
# / track / velodrome) use high-power sports lighting (VSP / M series ->
# SPORTS_LIGHTING); small outdoor venues (tennis / basketball / fencing /
# pickleball) use small / medium floods (RT410 / flood lights -> FLOODLIGHT);
# indoor venues additionally pull High Bay (HIGHBAY_LOWBAY). Large indoor
# venues (ice / aquatics / multi-sport) keep SPORTS_LIGHTING for the high-power
# requirement plus HIGHBAY_LOWBAY. There is deliberately no fixed 1:1 rule --
# these are the general heuristics the business actually uses.
PROJECT_SPORT_TO_PRODUCT_CATEGORIES = {
    'FOOTBALL_FIELD': ['SPORTS_LIGHTING'],
    'SOCCER_FIELD': ['SPORTS_LIGHTING'],
    'BASEBALL_FIELD': ['SPORTS_LIGHTING'],
    'TRACK_FIELD': ['SPORTS_LIGHTING'],
    'VELODROME': ['SPORTS_LIGHTING'],
    'MULTI_SPORT': ['SPORTS_LIGHTING', 'HIGHBAY_LOWBAY'],
    'ICE_ARENA': ['SPORTS_LIGHTING', 'HIGHBAY_LOWBAY'],
    'AQUATICS_CENTRE': ['SPORTS_LIGHTING', 'HIGHBAY_LOWBAY'],
    'KARTING': ['SPORTS_LIGHTING', 'FLOODLIGHT'],
    'SKI_AREA': ['SPORTS_LIGHTING', 'FLOODLIGHT'],
    'TENNIS_COURTS': ['FLOODLIGHT'],
    'TENNIS': ['FLOODLIGHT', 'HIGHBAY_LOWBAY'],
    'BASKETBALL': ['FLOODLIGHT', 'HIGHBAY_LOWBAY'],
    'FENCING': ['FLOODLIGHT', 'HIGHBAY_LOWBAY'],
    'PICKLEBALL': ['FLOODLIGHT', 'HIGHBAY_LOWBAY'],
    'AIRPORT': ['AREA_SITE', 'FLOODLIGHT'],
    'CITY_EXPRESSWAY': ['ROADWAY', 'FLOODLIGHT'],
    'ROADWAY': ['ROADWAY', 'FLOODLIGHT'],
}

# venue_type -> product category codes (fallback for non-sport venues)
PROJECT_VENUE_TO_PRODUCT_CATEGORIES = {
    'INFRASTRUCTURE': ['AREA_SITE', 'FLOODLIGHT'],
    'ROADWAY': ['ROADWAY', 'FLOODLIGHT'],
    'INDOOR': ['HIGHBAY_LOWBAY'],
    'OUTDOOR': [],
}

# reverse: product category -> project sport_types that use it
#
# Kept consistent with PROJECT_SPORT_TO_PRODUCT_CATEGORIES: every sport listed
# here maps back to a category that lists it, so a product's "Application Cases"
# and a project's "Related Products" are each other's inverse.
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


def related_products_for_project(project, lang='en', limit=3):
    """Products whose category matches this project's sport/venue type."""
    cats = set(PROJECT_SPORT_TO_PRODUCT_CATEGORIES.get(
        getattr(project, 'sport_type', ''), []))
    cats |= set(PROJECT_VENUE_TO_PRODUCT_CATEGORIES.get(
        getattr(project, 'venue_type', ''), []))
    if not cats:
        return []
    seen = set()
    out = []
    for cat in cats:
        for p in get_products(lang, active_category=cat):
            if p.slug in seen:
                continue
            seen.add(p.slug)
            out.append(p)
            if len(out) >= limit:
                return out
    return out


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
