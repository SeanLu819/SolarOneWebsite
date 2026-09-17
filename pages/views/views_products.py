from django.shortcuts import render
from django.utils.translation import get_language
from django.templatetags.static import static
from .common import get_common_context
from .i18n import (
    _get_products_sidebar,
    _resolve_active_labels,
    _resolve_product_sidebar,
)
from .data_loaders import get_products, get_product_detail


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
        cards = None
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


def product_detail(request, slug):
    """Unified product detail page for both series and sub-series."""
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
        context['show_certs'] = (
            product.slug in ('m-series', 'rt410-series') or
            product.parent_slug == 'm-series'
        )

    return render(request, 'product_detail.html', context)


def product_series(request, slug):
    """Legacy sub-series URL: now uses the same unified detail template."""
    return product_detail(request, slug)