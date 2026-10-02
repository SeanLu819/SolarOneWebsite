import json

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


# ---------------------------------------------------------------------------
# Product FAQ (B3, SEO/GEO 2026-09)
#
# Six high-value Q&A based strictly on confirmed product facts already in the
# repository (seed data / copy). These are CONSTANTS authored by us — never
# user input — so they are safe to inject wholesale into JSON-LD via
# ``{{ product_faq_json|safe }}`` (see the JSON-LD iron law in AGENTS.md: the
# whole blob is built in Python with ``json.dumps``, not concatenated in the
# template, so there is no trailing-comma / escapejs foot-gun).
#
# NOTE: we deliberately do NOT invent business FAQs (MOQ, lead time, warranty
# years, certification numbers) — that data is absent from the repo. Add those
# only once the business supplies the real numbers.
#
# SAFETY CONSTRAINT (do not relax): PRODUCT_FAQ is injected via
# ``{{ product_faq_json|safe }}`` with NO escaping. Keep it a list of literal
# string constants authored by us. Never interpolate user input, form fields,
# or any external/untrusted data into this blob — that would open an XSS /
# JSON-LD injection vector. The qa tests assert none of the 6 entries contain
# a ``</script>`` sequence precisely to guard this invariant.
# ---------------------------------------------------------------------------
PRODUCT_FAQ = [
    {
        'question': 'Are SolarOne stadium lights flicker-free for broadcast?',
        'answer': (
            'Yes. Our VSP high-frequency drivers eliminate flicker, so footage '
            'stays clean even in super-slow-motion broadcast replays.'
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
        'question': (
            'How much energy can we save versus existing HID / metal-halide '
            'lighting?'
        ),
        'answer': (
            'Retrofits typically cut energy use by 50% or more while improving '
            'uniformity.'
        ),
    },
    {
        'question': 'Are the luminaires modular and field-serviceable?',
        'answer': (
            'The M Series is modular from 80 W to 1280 W, with '
            'field-replaceable modules that keep maintenance downtime short.'
        ),
    },
]


def build_product_faq_jsonld(faq_list):
    """Build a schema.org FAQPage dict from ``faq_list`` (list of
    ``{"question": ..., "answer": ...}``). Returned as a Python dict so the
    caller can ``json.dumps(..., ensure_ascii=False)`` it for injection."""
    return {
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


def _sports_landing(request, template_name):
    """Shared loader for the sports keyword landing pages (hub / football /
    tennis): sidebar + merged SPORTS_LIGHTING & FLOODLIGHT grid. The pages
    differentiate through their own template copy, titles and URL keywords."""
    context = get_common_context()
    lang = get_language()

    product_categories = _get_products_sidebar(lang)
    context['product_categories'] = product_categories
    context['active_category'] = ''
    context['active_series'] = ''

    # Merge the two sports-relevant categories, dedupe by slug. VSP poles come
    # first (SPORTS_LIGHTING), then the RT floodlights (FLOODLIGHT) — stable,
    # intentional order so the grid reads "stadium systems → sports floodlights".
    merged = {}
    for cat in ('SPORTS_LIGHTING', 'FLOODLIGHT'):
        for p in get_products(lang, cat):
            slug = getattr(p, 'slug', '')
            if slug and slug not in merged:
                merged[slug] = p
    context['products'] = list(merged.values())

    return render(request, template_name, context)


def sports_lighting(request):
    """Sports & Stadium Lighting hub — Tier-1 SEMrush keyword landing page.

    Consolidates the four head SEMrush terms (stadium lights 2,900/mo KD18,
    led stadium lights 1,000/mo KD6, stadium light 720/mo KD12, led sports
    lighting 390/mo KD15) onto one clean static URL instead of funneling them
    to the generic /products/ listing (which had no keyword in its title and
    could not rank for those queries). Showcases the products that actually
    match: stadium-light poles (VSP, SPORTS_LIGHTING) and the sports
    floodlights (RT590FL-S / RT390FL / RT220UB / RT420FS-S, FLOODLIGHT).
    """
    return _sports_landing(request, 'sports_lighting.html')


def football_stadium_lights(request):
    """Tier-2 landing page for ``football stadium lights`` (480/mo) — the
    football-intent slice of the sports range: high-mast poles and floodlights
    for football pitches, with DIALux pitch-layout copy."""
    return _sports_landing(request, 'football_stadium_lights.html')


def tennis_court_lighting(request):
    """Tier-2 landing page for ``tennis court lighting`` (590/mo) — covers
    both outdoor and indoor tennis court lighting intents on one page."""
    return _sports_landing(request, 'tennis_court_lighting.html')


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
        context['banner_label'] = product.category_t
        context['gallery'] = product.gallery
        context['is_variant'] = bool(product.parent_slug)
        context['parent_slug'] = parent_slug or product.parent_slug
        # B3: product FAQ (FAQPage JSON-LD + visible section). Built in Python
        # and injected as one safe blob — never concatenated in the template.
        context['product_faq'] = PRODUCT_FAQ
        context['product_faq_json'] = json.dumps(
            build_product_faq_jsonld(PRODUCT_FAQ),
            ensure_ascii=False,
        )

    # Unknown slug → real 404. Previously this rendered product_detail.html's
    # "Product Not Found" branch with HTTP 200 (a soft 404): Google indexes
    # unlimited bogus URLs and ranks them as thin content.
    if product is None:
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