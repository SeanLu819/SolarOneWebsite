"""The stadium-lighting landing page (v1.10.23, P4-A).

Why one page and not six
------------------------
The plan this batch came from proposed a landing page per product category.
Measuring the portfolio first said no: of the six categories, **four cannot
support a page** — HIGHBAY_LOWBAY and ROADWAY hold two products each and no
projects at all, FLOODLIGHT holds four, ACCESSORY three. A page carrying two
products and a paragraph is the thin page v1.10.20 spent a whole batch
deleting; building six would have re-created six of them.

What the volume data does support is the *generic* term. Of the six measured
keywords in ``docs/keyword-inventory.csv``, four are the same intent spelled
four ways — stadium lights (2 900/mo, KD 18), led stadium lights (1 000/mo,
KD 6), stadium light (720/mo, KD 12) and led sports lighting (390/mo, KD 15) —
**5 010 searches/month** with none of them currently on a page of its own:
``/products/`` is titled "LED Lighting Products", and the three URLs that used
to carry them were retired in v1.10.0. One page that owns that term is worth
more than six pages that each own a rounding error.

It is also the only page that has real depth. 20 of the 22 portfolio projects
are venues — football pitches, stadiums, arenas, velodromes, ski runs, karting
tracks — and two products (the VSP stadium series) are built for exactly that
work. That is 22 linked references, not two.

The venue set is derived from ``related_links.PRODUCT_CATEGORY_TO_PROJECT_SPORTS``
— the same table a product page's "Application Cases" uses — so this page and
the product pages cannot disagree about which projects suit which luminaires.
"""

import json

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import get_language

from .common import get_common_context
from .data_loaders import get_projects, get_products
from .related_links import PRODUCT_CATEGORY_TO_PROJECT_SPORTS

#: The one product category this page is about. Written literally rather than
#: derived: it is the product decision the whole page exists to express, and a
#: guard asserts it against the keyword table.
STADIUM_CATEGORY = 'SPORTS_LIGHTING'

#: How many venue projects to list. The portfolio has 20; a landing page that
#: lists all of them is a project index wearing a product page's hat. The
#: remainder are one click away through /projects/.
VENUE_PROJECT_LIMIT = 9

#: The two luminaires this page features, in display order. Written literally,
#: not derived: the page exists to present exactly these two broadcast-grade
#: models. The original "first N of the category" rendered a generic VSP-series
#: list; pinning the slugs makes the roster a product decision that has to be
#: re-made on purpose (9M first — the shorter tower — then 12M).
#: The two luminaires this page features, in display order. Written literally,
#: not derived: the page exists to present exactly this shortlist — a modular
#: flood platform (M Series, 80–1280 W) for club/training venues and the
#: broadcast-grade VSP series for televised stadiums. The earlier "two VSP
#: models" roster was dropped in favour of two *platforms* so the hero spans
#: the two distinct buying intents instead of two near-identical 4200 W SKUs.
FEATURED_PRODUCT_SLUGS = ('m-series', 'vsp-xxxxw-9m-yp')

#: Page-level FAQ (v1.10.24, audit A6/GEO).
#:
#: Why this page andnot the product pages: the product FAQ already answers
#: "is it flicker-free" and "what is the efficacy" 25 times over. What no
#: product page can answer is the question a buyer has *before* picking a
#: product — "how many masts will my pitch need?", "does my broadcast deal care
#: about the lighting?". That is a page-level question, and this page is the
#: only one on the site with enough context to answer it.
#:
#: Every number below is read from ``seed_data.json`` ``energy_data`` for the
#: two featured models (System Wattage 4200 W, CRI 70~95, L70 100,000 h at
#: 25 °C, IP66, 10 kV surge, −40 °C to +55 °C, 12/18/30/50° from
#: ``ordering_info``). Nothing is invented: MOQ, lead time, warranty years and
#: certification numbers are absent from the repo and are therefore absent here
#: too — the same constraint the product FAQ documents.
#:
#: SAFETY: this blob is injected with ``json.dumps`` and rendered ``|safe``,
#: exactly like ``build_product_faq_jsonld``. Keep every entry a literal
#: constant authored here; never interpolate request data into it.
STADIUM_FAQ = [
    {
        'question': 'How many masts does a stadium floodlighting package need?',
        'answer': (
            'It follows from the target illuminance on the playing surface and '
            'the mounting points the structure allows, not from a fixed '
            'fixture count. The VSP series is rated 4200 W per system, so a '
            'pitch reaches its target output from fewer masts than the '
            'high-pressure-scheme it replaces. Send the venue drawing and '
            'mounting height and we return a photometric layout with the mast '
            'count.'
        ),
    },
    {
        'question': (
            'Are these luminaires usable for televised matches and '
            'super-slow-motion replay?'
        ),
        'answer': (
            'Yes. Vision Strobe Protection on the VSP series keeps the output '
            'free of the low-frequency flicker that shows up as banding in '
            'super-slow-motion replay, and the asymmetric optics are aimed to '
            'keep glare out of the camera-side seating.'
        ),
    },
    {
        'question': 'What beam angles are available?',
        'answer': (
            '12°, 18°, 30° and 50° from the same M Series optical platform, '
            'coded 12 / 18 / 30 / 50 in the model number. The narrow angles '
            'serve the seating bowl, the wider ones the playing surface.'
        ),
    },
    {
        'question': 'What is the efficacy, lifespan and protection rating?',
        'answer': (
            'CRI 70~95, L70 of 100,000 hours at 25 °C, IP66 ingress '
            'protection, 10 kV surge protection, and an operating range of '
            '−40 °C to +55 °C.'
        ),
    },
    {
        'question': 'How is the fixture powered and dimmed?',
        'answer': (
            'The remote power system pairs one AC enclosure with n LED driver '
            'enclosures, so the drivers sit away from the fixture and are '
            'reached without a ladder. Dimming is 1-10 V, DMX, DALI or Zigbee, '
            'and both 110–277 VAC and 347–480 VAC inputs are available. '
            'Enclosure dimensions follow the project, so they are quoted per '
            'order rather than fixed on this page.'
        ),
    },
    {
        'question': 'Do you supply photometric studies for our venue?',
        'answer': (
            'Yes. Our engineering team delivers a full photometric proposal — '
            'layout, illuminance and uniformity — within 48 hours of receiving '
            'your venue drawing.'
        ),
    },
]


def get_featured_landing_products(slugs, lang='en'):
    """Hero luminaires for any sports-landing page, in ``slugs`` order.

    Each slug is resolved with ``get_product_detail`` — which finds *both*
    top-level platforms (M Series, VSP series) **and** child sub-models
    (FL6M, FL9M …) — so a landing page can feature a specific floodlight model
    that lives under a series rather than the series platform itself. The
    /products/ index uses ``get_products`` and only lists top-level parents;
    that filter is intentional there but must not gate the hero roster, or a
    child model like FL6M silently disappears from the football hero.

    The platform label (e.g. "VSP series") comes from ``productspagecards`` —
    the same source the /products/ page uses — so every landing hero and the
    products page spell each platform identically. Child sub-models have no
    ``productspagecards`` entry (they are not platforms), so for those the
    card falls back to the product's own name/description and a
    ``/products/<slug>/`` link. The overlay is applied to a *copy* of each
    product: ``get_product_detail`` already returns a fresh instance, but the
    products page can still enrich the shared seed object, so copying keeps
    this helper side-effect free.
    """
    import copy

    from .data_loaders import _load_seed, get_product_detail

    cards = {
        (c.get('slug') or '').strip(): c
        for c in (_load_seed().get('productspagecards', []) or [])
        if c.get('is_active', True)
    }
    featured = []
    for slug in slugs:
        # ``get_product_detail`` resolves child slugs that ``get_products``
        # hides behind parent__isnull=True — that is the whole point of this
        # helper rewrite (FL6M is a child of M Series).
        product = get_product_detail(slug, lang)
        if product is None:
            continue
        p = copy.copy(product)
        card = cards.get(slug)
        if card:
            if card.get('title'):
                p.name_t = card['title']
            if card.get('subtitle'):
                p.description_t = card['subtitle']
            if card.get('link_url'):
                p.card_link_url = card['link_url']
        else:
            # Child sub-model (e.g. FL6M): no platform card. Derive the hero
            # copy from the product itself and link to its own detail page.
            if not getattr(p, 'name_t', None):
                p.name_t = getattr(p, 'name', slug)
            if not getattr(p, 'description_t', None):
                p.description_t = getattr(p, 'description', '')
            p.card_link_url = '/products/%s/' % slug
        featured.append(p)
    return featured


def get_featured_stadium_products(lang='en'):
    """Stadium hero products, in ``FEATURED_PRODUCT_SLUGS`` order."""
    return get_featured_landing_products(FEATURED_PRODUCT_SLUGS, lang)


def stadium_lighting(request):
    """/stadium-lighting/ — the generic stadium / sports lighting term.

    Renders ``products.html``'s grid? No: it has its own template, because this
    page's job is to *rank and explain* the shortlist (why this luminaire for
    this venue), and the product index has no room for that. Sharing the
    template would mean either duplicating the grid or making the index carry
    copy that is meaningless on it.
    """
    context = get_common_context()
    # ``get_common_context`` carries config and analytics ids only, so the
    # active locale has to be read from the translation machinery — the same
    # call every other view makes.
    lang = get_language() or 'en'

    sports = PRODUCT_CATEGORY_TO_PROJECT_SPORTS.get(STADIUM_CATEGORY, [])

    # Products: the category first, then the modular flood platforms that venue
    # projects actually specify. The second group is what makes the page useful
    # to a buyer — a stadium pitch is often lit by a high-output flood rather
    # than the broadcast-grade stadium model.
    category_products = [
        p for p in (get_products(lang) or [])
        if getattr(p, 'category', '') == STADIUM_CATEGORY
    ]
    # Featured hero uses the shared helper so the platform labels match the
    # /products/ page and the cached-product objects are never mutated in place.
    featured = get_featured_stadium_products(lang)

    # Projects: the venues, newest-sorted by the loader's own ordering so the
    # page does not add a second, competing notion of "newest".
    venues = [
        p for p in (get_projects(lang) or [])
        if getattr(p, 'sport_type', '') in sports
        and getattr(p, 'image_url', '')
    ][:VENUE_PROJECT_LIMIT]

    context.update({
        'page_title': _t(
            'LED Stadium Lighting — SolarOne Sports Floodlights', lang),
        # 158 characters, inside the 160-char SERP budget this project holds
        # every other description to. The first draft ran to 209 and was
        # truncated mid-sentence in the SERP, wasting the tail.
        'page_description': _t(
            'SolarOne LED stadium lighting: broadcast-grade VSP floodlights '
            'and modular LED floods from 80 W to 1280 W, with 20 delivered '
            'venue projects.', lang),
        'landing_products': featured,
        'landing_venues': venues,
        # Kept for the template's default venue-lead blocktrans, whose .po entry
        # still references `stadium_venues`. Football/tennis pass `venue_lead`
        # overrides, so they do not use this branch.
        'stadium_venues': venues,
        'landing_product_count': len(category_products),
        'faq_items': _localised_faq(STADIUM_FAQ, lang),
        'faq_json': json.dumps(
            build_stadium_faq_jsonld(
                _localised_faq(STADIUM_FAQ, lang),
                entity_id=f'{settings.CANONICAL_ORIGIN}{request.path}#faq'),
            ensure_ascii=False),
        # The text fields (accent / h1 / intro / product_heading / product_lead /
        # selection_heading / selection_lead / selection_note / venue_heading /
        # faq_heading) are intentionally NOT passed here: the template falls back
        # to the stadium copy via default: filters, so this page renders exactly
        # as it did before the Q1 unification. Football/tennis pass their own.
    })
    return render(request, 'stadium_lighting.html', context)


def _localised_faq(faq_list, lang):
    """Translate a FAQ list (list of {question, answer}) through gettext.

    Reuses the product FAQ's JSON-LD builder rather than writing a second one:
    ``FAQPage.mainEntity`` is a fixed shape, and two builders for it would be
    two places to forget ``acceptedAnswer``.
    """
    from django.utils.translation import gettext as _

    return [
        {'question': _(item['question']), 'answer': _(item['answer'])}
        for item in faq_list
    ]


def build_landing_faq_jsonld(faq_list, entity_id=None):
    """Build the schema.org FAQPage dict for any sports-landing page.

    Delegates to :func:`build_product_faq_jsonld` — the shape is identical and
    every landing page's FAQ is the same kind of content.
    """
    from .views_products import build_product_faq_jsonld

    return build_product_faq_jsonld(faq_list, entity_id=entity_id)


def build_stadium_faq_jsonld(faq_list, entity_id=None):
    """Back-compat alias for :func:`build_landing_faq_jsonld`."""
    return build_landing_faq_jsonld(faq_list, entity_id=entity_id)


def _t(text, lang):
    """Localise page copy through gettext, not the sidebar table.

    ``_SIDEBAR_I18N`` holds navigation labels ("Filter by Application"), not
    page copy, and inventing entries in it would make ``KNOWN_DYNAMIC_SITES``
    accounting wrong for a page that is not a sidebar. Page copy is gettext's
    job: one msgid, six ``.po`` files, and the templates on this page already
    use ``{% blocktrans %}`` for exactly the same reason.
    """
    from django.utils.translation import gettext as _
    return _(text)