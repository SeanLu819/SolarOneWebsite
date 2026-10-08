import json
import re

from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.translation import get_language
from django.templatetags.static import static
from .common import get_common_context
from .i18n import (
    _get_products_sidebar,
    _resolve_active_labels,
    _resolve_product_sidebar,
)
from .data_loaders import get_products, get_product_detail
from .related_links import application_cases_for_product
from pages.redirects import redirect_target_for_product


# ---------------------------------------------------------------------------
# Product FAQ (B3, SEO/GEO 2026-09; per-category split v1.10.20)
#
# Six high-value Q&A based strictly on confirmed product facts already in the
# repository (seed data / copy). These are CONSTANTS authored by us — never
# user input — so they are safe to inject wholesale into JSON-LD via
# ``{{ product_faq_json|safe }}`` (see the JSON-LD iron law in AGENTS.md: the
# whole blob is built in Python with ``json.dumps``, not concatenated in the
# template, so there is no trailing-comma / escapejs foot-gun).
#
# WHY PER CATEGORY (2026-10-06 audit)
# ----------------------------------
# The single six-entry list shipped identical text on all 24 product pages.
# Measured on /products/fl6m/: the FAQ block was 3721 of 3947 body words —
# **94.3% of the page** — and the same six questions were asked of a 40 W
# floodlight, a 1280 W stadium array and a glare shield. Google sees 24 pages
# competing for the same long-tail questions with the same answer.
#
# So the questions are now chosen by what the buyer actually needs to know for
# THAT product type. Cross-cutting facts that are true everywhere (efficacy,
# L70, IP66, surge, temperature) are kept in every set so no page loses them;
# only the type-specific entries rotate.
#
# NOTE: we deliberately do NOT invent business FAQs (MOQ, lead time, warranty
# years, certification numbers) — that data is absent from the repo. Add those
# only once the business supplies the real numbers.
#
# SAFETY CONSTRAINT (do not relax): every entry below is injected via
# ``{{ product_faq_json|safe }}`` with NO escaping. Keep them literal string
# constants authored by us. Never interpolate user input, form fields,
# or any external/untrusted data into this blob — that would open an XSS /
# JSON-LD injection vector. The qa tests assert no entry contains a
# ``</script>`` sequence precisely to guard this invariant.
# ---------------------------------------------------------------------------

#: Keyed view of the shared entries. Pinned by key (not index) because the
#: accessory set cherry-picks one of them.
#: Facts that hold for every SolarOne luminaire, drawn from the seed energy
#: tables (IP Rating / Surge / Operating Temperature / L70 rows) and the
#: ordering tables (System Wattage). Kept verbatim in all four sets.
_SHARED_FAQ = [
    {
        'question': 'What is the luminous efficacy and rated lifespan?',
        'answer': (
            'Up to 130 lm/W, with an L70 lifetime exceeding 100,000 hours.'
        ),
    },
    {
        'question': 'What ingress and surge protection do the luminaires have?',
        'answer': (
            'IP66 ingress protection, 10 kV surge protection, and an operating '
            'range of −40 °C to +55 °C.'
        ),
    },
    {
        'question': 'Do you provide DIALux photometric studies?',
        'answer': (
            'Yes. Our engineering team delivers a full photometric proposal — '
            'layout, illuminance and uniformity — within 48 hours of receiving '
            'your venue drawing.'
        ),
    },
]

_SHARED_FAQ_BY_KEY = {entry['question']: entry for entry in _SHARED_FAQ}

#: Arena / stadium / broadcast venues: flicker, lux levels, HDTV, the VSP drive.
_SPORTS_FAQ = [
    {
        'question': 'Are SolarOne stadium lights flicker-free for broadcast?',
        'answer': (
            'Yes. Our VSP high-frequency drivers eliminate flicker, so footage '
            'stays clean even in super-slow-motion broadcast replays.'
        ),
    },
    {
        'question': 'Do the luminaires meet sports federation playing standards?',
        'answer': (
            'The RT410 series is Olympic-grade and HDTV-ready, replacing '
            '400–1000 W HID at 20–50 ft mounting heights at a fraction of the '
            'running cost. Every order ships with a photometric layout matched '
            'to your venue drawing.'
        ),
    },
    {
        'question': 'Are the M Series modules field-replaceable?',
        'answer': (
            'Yes. The M Series is modular from 80 W to 1280 W, with '
            'field-replaceable modules that keep maintenance downtime short.'
        ),
    },
]

#: Area, site and general-purpose floodlighting: retrofit economics, mounting,
#: which beam angle to pick.
_FLOOD_FAQ = [
    {
        'question': 'How much energy can we save versus existing HID / metal-halide lighting?',
        'answer': (
            'Retrofits typically cut energy use by 50% or more while improving '
            'uniformity.'
        ),
    },
    {
        'question': 'Which beam angle should I choose for my application?',
        'answer': (
            'Narrow 30–50° beams concentrate light for tall facades and signage, '
            'while 100–120° options cover yards, loading lots and perimeter '
            'poles. Each ordering code lists the available angles for that '
            'series.'
        ),
    },
    {
        'question': 'What mounting options are available?',
        'answer': (
            'U = hang-mount bracket and L = sitting-mount bracket, both '
            'available across the floodlight range. Finish and dimming '
            'options (1.0-10V, DMX, DALI, Zigbee) are listed in the ordering '
            'table.'
        ),
    },
]

#: High-bay / low-bay and roadway: lumen-per-watt at height, pole heights,
#: road photometric criteria.
_HIGHBAY_ROADWAY_FAQ = [
    {
        'question': 'What mounting height are these luminaires designed for?',
        'answer': (
            'The high-bay and low-bay series cover the 30–90° beam family used '
            'from warehouses and sports halls up to high-bay applications, and '
            'the roadway series ships with an asymmetric 70° × 140° '
            'distribution for street lighting.'
        ),
    },
    {
        'question': 'Can you match an existing installation footprint?',
        'answer': (
            'Yes — send us the existing photometric report or IES file and we '
            'will confirm whether the same mounting positions and aiming '
            'angles work, or supply a replacement layout.'
        ),
    },
    {
        'question': 'How do I order the right configuration?',
        'answer': (
            'Every ordering code follows the same pattern: series name, system '
            'wattage, CCT, input voltage, beam angle, finish, dimming and '
            'bracket. The ordering table on this page lists every option for '
            'this model.'
        ),
    },
]

#: Glare shields and other accessories: fit, purpose, what they do to the
#: photometric result.
_ACCESSORY_FAQ = [
    {
        'question': 'What does a glare shield actually do?',
        'answer': (
            'A glare shield cuts the light spilling above the horizontal, '
            'directing more of the output toward the ground or the playing '
            'surface. That reduces skyglow and improves contrast for drivers, '
            'players and neighbours.'
        ),
    },
    {
        'question': 'Will a glare shield fit my existing fixtures?',
        'answer': (
            'We supply shield lengths for the M Series and the RT410. Send the '
            'fixture model and mounting height and we will confirm the '
            'matching shield before you order.'
        ),
    },
    {
        'question': 'Does a shield change the host luminaire ratings?',
        'answer': (
            'No. A shield is a mechanical accessory: it changes where the '
            'light goes, not the electrical rating. IP66 ingress protection, '
            '10 kV surge protection and the L70 lifetime of the host fixture '
            'are all unchanged.'
        ),
    },
    {
        'question': 'Can you check a shield against our installation drawing?',
        'answer': (
            'Yes — send the fixture model, the pole or facade mounting '
            'height, and the site drawing. Our engineers confirm the shield '
            'length and the resulting aiming angle before you order.'
        ),
    },
    {
        'question': 'What efficacy and lifetime does the host fixture keep?',
        'answer': (
            'The host luminaires are rated up to 130 lm/W with an L70 lifetime '
            'exceeding 100,000 hours at 25 °C. A shield changes where the '
            'light goes, not how much the fixture produces.'
        ),
    },
]

#: ``Product.category`` -> the FAQ set that page shows. Every category present
#: in the seed data must appear here; ``pages/tests_product_data_integrity.py``
#: asserts the mapping stays complete.
PRODUCT_FAQ_BY_CATEGORY = {
    'SPORTS_LIGHTING': _SHARED_FAQ + _SPORTS_FAQ,
    'AREA_SITE': _SHARED_FAQ + _FLOOD_FAQ,
    'FLOODLIGHT': _SHARED_FAQ + _FLOOD_FAQ,
    'HIGHBAY_LOWBAY': _SHARED_FAQ + _HIGHBAY_ROADWAY_FAQ,
    'ROADWAY': _SHARED_FAQ + _HIGHBAY_ROADWAY_FAQ,
    # Accessories skip the DIALux and HID-saving entries (a glare shield is
    # neither a luminaire nor a retrofit), but keep the efficacy/lifetime
    # answer — buyers ask it of the host fixture. Spelled out by
    # name rather than sliced, so reordering _SHARED_FAQ cannot silently
    # change which entries an accessory page shows.
    'ACCESSORY': [_SHARED_FAQ_BY_KEY[
        'What is the luminous efficacy and rated lifespan?']] + _ACCESSORY_FAQ,
}

#: Back-compat alias: the flood set is the most representative one and is
#: what ``tests_qa_bgroup`` imports. New code should call
#: :func:`product_faq_for` instead.
PRODUCT_FAQ = PRODUCT_FAQ_BY_CATEGORY['AREA_SITE']


def product_faq_for(product):
    """Return the FAQ list for ``product`` — 6 entries, chosen by category.

    Falls back to the shared-only core if a category ever arrives that is not
    in the map, so a new ``CATEGORY_CHOICES`` value degrades to fewer
    questions rather than an empty section or a KeyError.
    """
    category = getattr(product, 'category', '') or ''
    return PRODUCT_FAQ_BY_CATEGORY.get(category) or _SHARED_FAQ


def build_product_faq_jsonld(faq_list, entity_id=None):
    """Build a schema.org FAQPage dict from ``faq_list`` (list of
    ``{"question": ..., "answer": ...}``). Returned as a Python dict so the
    caller can ``json.dumps(..., ensure_ascii=False)`` it for injection.

    ``entity_id`` (v1.10.24) is the value for ``@id``. It is optional so
    existing callers keep working, but every call site should pass it: a
    page-level FAQ describes that page, so its anchor is the page URL plus
    a fragment. Left unset the node is identified only by its contents,
    which is what let two pages' FAQ blocks merge into one entity.
    """
    node = {
        '@context': 'https://schema.org',
        '@type': 'FAQPage',
        'mainEntity': [
            {
                '@type': 'Question',
                'name': item['question'],
                'acceptedAnswer': {
                    '@type': 'Answer',
                    'text': item['answer'],
                },
            }
            for item in (faq_list or [])
        ],
    }
    if entity_id:
        node['@id'] = entity_id
    return node


def _resolve_ppc_image(card):
    """Resolve a ProductsPageCard image URL, mirroring the same
    static-priority + hash-stripping logic used for Product/Project.

    Priority (same pattern as _product_image_url / _dict_product_image_url):
      1. cleaned (hash stripped) path under static/images/products_page/
      2. raw (with hash) static path
      3. media URL (only if static asset missing, e.g. right after upload)
    """
    from .utils import _first_static, strip_hash_suffix
    import os

    field = getattr(card, 'image', None)
    db_name = getattr(field, 'name', None)
    if not db_name:
        return ''
    db_name = str(db_name).replace('\\', '/')
    base = os.path.basename(db_name)
    clean = strip_hash_suffix(base)

    # A3: candidate loop收口到 utils._first_static
    hit = _first_static([
        f'images/products_page/{clean}',
        f'images/products_page/{base}',
        f'images/{db_name}',
    ])
    if hit:
        return hit

    try:
        url = field.url
    except Exception:
        url = ''
    return url


def _dict_ppc_image(card_data):
    """Resolve image URL for a seed-dict ProductsPageCard entry."""
    from .utils import _first_static, _passthrough_url, strip_hash_suffix
    import os

    raw = card_data.get('image', '') or ''
    passthrough = _passthrough_url(raw)
    if passthrough:
        return passthrough
    raw = str(raw).replace('\\', '/')
    base = os.path.basename(raw)
    clean = strip_hash_suffix(base)
    # A3: candidate loop收口到 utils._first_static
    hit = _first_static([
        f'images/products_page/{clean}',
        f'images/products_page/{base}',
        raw if raw.startswith('images/') else f'images/{raw}',
    ])
    if hit:
        return hit
    return static(raw) if raw else ''


def products(request):
    context = get_common_context()
    lang = get_language()
    # Read at call time (not as a module constant) so @override_settings works
    # in tests — same pattern as data_loaders.
    is_prod = getattr(settings, 'IS_VERCEL', False)

    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories

    active_category = request.GET.get('category', '')
    active_series = request.GET.get('series', '')
    context['active_category'] = active_category
    context['active_series'] = active_series

    # A2: label lookup收口到 i18n._resolve_active_labels
    active_category_label, active_series_label = _resolve_active_labels(
        product_categories, active_category, active_series,
    )
    context['active_category_label'] = active_category_label
    context['active_series_label'] = active_series_label

    # ---- Build a product lookup map (slug -> enriched product) ----
    raw_products = get_products(lang, active_category, active_series)
    product_by_slug = {}
    for p in raw_products:
        s = getattr(p, 'slug', '')
        if s:
            product_by_slug[s] = p

    # Collect card slugs upfront so the fallback can use them
    all_card_slugs = []
    if not is_prod:
        try:
            from pages.cards import ProductsPageCard
            all_card_slugs = list(
                ProductsPageCard.objects.filter(is_active=True)
                .values_list('slug', flat=True)
            )
        except Exception:
            pass

    # ---- Products page card order/visibility is now driven by ProductsPageCard ----
    # ProductsPageCard is the SOURCE OF TRUTH for:
    #   * which products appear (is_active + slug match)
    #   * in what order (order, pk)
    #   * the card title/subtitle/image/link (override)
    #
    # When a category/series filter is active, we fall back to the filtered
    # product list (so sidebar navigation still works for categories).
    cards_ok = False
    final_products = []
    card_order_count = 0

    if not active_category and not active_series:
        # On Vercel the DB is an empty /tmp SQLite, so this query would raise on
        # every request and be swallowed by the `except`, leaving `cards = None`
        # and letting the seed fallback below take over. Skip the doomed
        # round-trip instead: verified byte-identical output, and it honours the
        # "production never touches the DB" contract from v1.6.0.
        # NOTE: only the query is skipped — the seed fallback must still run,
        # otherwise final_products stays empty and the page exposes all
        # products instead of the curated subset.
        cards = None
        if not is_prod:
            try:
                from pages.cards import ProductsPageCard as PPC
                cards = list(PPC.objects.filter(is_active=True).order_by('order', 'pk'))
            except Exception:
                cards = None

        if cards:
            cards_ok = True
            for card in cards:
                slug = (card.slug or '').strip()
                product = product_by_slug.get(slug)
                if product is None:
                    continue
                card_order_count += 1
                if card.title:
                    product.name_t = card.title
                if card.subtitle:
                    product.description_t = card.subtitle
                img_url = _resolve_ppc_image(card)
                if img_url:
                    product.image_url = img_url
                if card.link_url:
                    product.card_link_url = card.link_url
                final_products.append(product)

        if not final_products:
            try:
                from .utils import _load_seed
                data = _load_seed()
            except Exception:
                data = {}
            seed_cards = [c for c in data.get('productspagecards', []) if c.get('is_active', True)]
            if seed_cards:
                seed_cards.sort(key=lambda c: (c.get('order', 0) or 0,))
                for card in seed_cards:
                    slug = (card.get('slug') or '').strip() or \
                           (card.get('link_url') or '').strip('/').split('/')[-1]
                    product = product_by_slug.get(slug)
                    if product is None:
                        continue
                    card_order_count += 1
                    if card.get('title'):
                        product.name_t = card['title']
                    if card.get('subtitle'):
                        product.description_t = card['subtitle']
                    img_url = _dict_ppc_image(card)
                    if img_url:
                        product.image_url = img_url
                    if card.get('link_url'):
                        product.card_link_url = card['link_url']
                    final_products.append(product)

    # When neither card path produced results AND there are no category/series
    # filters, only show products that have a card slug match — never expose
    # all products accidentally (avoids the fallback returning 12 instead of 6).
    if not final_products and not active_category and not active_series and all_card_slugs:
        all_cs_lower = {c.lower() for c in all_card_slugs if c}
        final_products = [
            p for s, p in product_by_slug.items()
            if s.lower() in all_cs_lower
        ]

    # Last resort: raw product list (preserves sidebar filtering UX)
    if not final_products:
        final_products = list(raw_products)

    context['products'] = final_products
    return render(request, 'products.html', context)


def _series_children(parent_slug, lang):
    """The sub-models of one series, enriched and ordered as the data is.

    Reads ``parent_slug`` from the *seed/DB* rows rather than the sidebar
    tree, so the list can never disagree with what ``get_products`` hides.
    Returns ``[]`` for a leaf — the template then renders nothing.
    """
    if not parent_slug:
        return []
    from .data_loaders import get_all_products

    children = [p for p in (get_all_products(lang) or [])
                 if getattr(p, 'parent_slug', '') == parent_slug]
    # Natural sort on the slug's digit runs, so FL4M comes before FL12M
    # (plain lexicographic order puts FL12M/FL16M ahead of FL1M because
    # '2' < 'm'). Non-digit runs stay string-compared.
    children.sort(key=lambda p: [int(t) if t.isdigit() else t
                                 for t in re.split(r'(\d+)', p.slug)])
    return children


def product_detail(request, slug):
    """Unified product page for both series and sub-series.

    Two public templates, picked by ``Product.page_layout`` (admin:
    Product → Page template):

      * ``detail``   → ``product_detail.html``  — full technical spec
        (beam angle, dimensions, energy + ordering tables, sample CTA).
      * ``overview`` → ``product_overview.html`` — series landing page
        (banner, gallery carousel, copy, free-form image/copy slot).

    ``is_variant`` / ``parent_slug`` are still published for callers that need
    the parent series; the templates themselves read ``active_*`` only.
    """
    context = get_common_context()
    lang = get_language()

    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories

    product = get_product_detail(slug, lang)

    active_series, active_subseries, parent_slug = _resolve_product_sidebar(slug, lang)
    context['active_series'] = active_series
    context['active_subseries'] = active_subseries

    if product:
        context['product'] = product
        context['banner_image'] = product.banner_image_url
        context['banner_label'] = product.category_display
        context['gallery'] = product.gallery
        context['is_variant'] = bool(product.parent_slug)
        context['parent_slug'] = parent_slug or product.parent_slug
        # B3: product FAQ (FAQPage JSON-LD + visible section). Built in Python
        # and injected as one safe blob — never concatenated in the template.
        # v1.10.20: the set is chosen per product category instead of one
        # shared list — see the block comment above PRODUCT_FAQ_BY_CATEGORY.
        faq = product_faq_for(product)
        context['product_faq'] = faq
        context['product_faq_json'] = json.dumps(
            build_product_faq_jsonld(
                faq,
                entity_id=f'{settings.CANONICAL_ORIGIN}'
                f'{request.path}#faq'),
            ensure_ascii=False,
        )
        # B2 -> v1.10.26: Application Cases is now hand-picked in the admin
        # (Product.application_cases). No auto match, no fallback -- an empty
        # pick hides the whole section (template: {% if related_projects %}).
        context['related_projects'] = application_cases_for_product(product, lang)

        # v1.10.23 (P4-B): the sub-model selector's data.
        #
        # The filter sidebar already links every sub-model, so this is NOT
        # about reachability — the first version of this comment
        # claimed the hub was a dead end, which was a measurement error (the
        # scan stripped <nav>, and the series navigation is a <nav>). What
        # the selector adds is the wattage and the per-module search phrase
        # in the content area, where a buyer is actually looking. Empty list
        # for a leaf product, so the template needs no category knowledge.
        context['series_children'] = _series_children(slug, lang)


    # Unknown slug → real 404. Previously this rendered product_detail.html's
    # "Product Not Found" branch with HTTP 200 (a soft 404): Google indexes
    # unlimited bogus URLs and ranks them as thin content.
    if product is None:
        # S2: renamed page → 301 before the 404. Keeps the language prefix
        # (redirect() reverses; a hand-built path would drop /fr/).
        moved = redirect_target_for_product(slug)
        if moved:
            return redirect('product_detail', moved, permanent=True)
        raise Http404(f'No product matches slug {slug!r}')

    template = ('product_overview.html'
                if getattr(product, 'page_layout', 'detail') == 'overview'
                else 'product_detail.html')
    return render(request, template, context)


def product_series(request, slug):
    """Legacy /products/series/<slug>/ URL.

    These URLs render the exact same product as /products/<slug>/ (the slug
    resolves to the same product), so serving both is duplicate content.
    301-redirect to the canonical product_detail URL to consolidate ranking
    signals and crawl budget (SEO P1b). The active language prefix is preserved
    because this view runs inside i18n_patterns.
    """
    return redirect('product_detail', slug, permanent=True)