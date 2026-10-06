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
FEATURED_PRODUCT_SLUGS = ('vsp-xxxxw-9m-yp', 'vsp-xxxxw-12m-yp')


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
    by_slug = {p.slug: p for p in category_products}
    featured = [by_slug[s] for s in FEATURED_PRODUCT_SLUGS if s in by_slug]
    for product in featured:
        product.is_stadium_featured = True

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
        'stadium_products': featured,
        'stadium_venues': venues,
        'stadium_sport_types': sports,
        'stadium_product_count': len(category_products),
    })
    return render(request, 'stadium_lighting.html', context)


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