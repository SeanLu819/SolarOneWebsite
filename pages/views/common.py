import logging
from django.conf import settings
from django.core.cache import cache
from django.templatetags.static import static
from django.utils.translation import get_language
from pages.models import SiteConfig
from .utils import _load_seed
from .i18n import _t

logger = logging.getLogger(__name__)


def _build_siteconfig_from_seed():
    """Build an in-memory SiteConfig from the committed seed JSON — no DB access.

    Used in production (IS_VERCEL), where content must come from the seed and the
    database is never touched for content, and as a fallback locally when the
    SiteConfig singleton is missing or the DB query fails.

    Image fields (hero_background / logo / og_image) are skipped here because they
    are resolved to static URLs later in get_common_context(); carrying the raw
    upload path on an unsaved instance would make ``config.hero_background.name``
    blow up the enrichment block. All other (scalar) fields are assigned if present.
    """
    data = _load_seed()
    cfg = data.get('siteconfig', {})
    config = SiteConfig()
    _image_fields = {'hero_background', 'logo', 'og_image'}
    for key, val in cfg.items():
        if key in _image_fields:
            continue
        if hasattr(config, key):
            try:
                setattr(config, key, val)
            except Exception:
                pass
    return config


def get_common_context():
    """Get context shared across all pages"""
    config = cache.get('site_config')
    if not config:
        if getattr(settings, 'IS_VERCEL', False):
            # Production is fully stateless: load content from the committed seed
            # JSON and never touch the database for content (A1 / B4).
            config = _build_siteconfig_from_seed()
            cache.set('site_config', config, timeout=300)
        else:
            try:
                config = SiteConfig.objects.first()
                if not config:
                    # Do NOT auto-create a DB row on a GET (that was a hidden write
                    # to the database). Fall back to seed defaults instead (B4).
                    config = _build_siteconfig_from_seed()
                cache.set('site_config', config, timeout=300)
            except Exception:
                logger.warning('DB SiteConfig query failed, building from seed JSON', exc_info=True)
                config = _build_siteconfig_from_seed()
                cache.set('site_config', config, timeout=300)

    hero_bg = getattr(config, 'hero_background', '')
    hero_name = getattr(hero_bg, 'name', hero_bg) if hero_bg else ''
    if hero_name:
        config.hero_bg_url = static(hero_name)
    else:
        config.hero_bg_url = static('images/hero-main.webp')

    logo = getattr(config, 'logo', '')
    logo_name = getattr(logo, 'name', logo) if logo else ''
    if logo_name:
        config.logo_url = static(logo_name)
    else:
        config.logo_url = static('images/logo.webp')

    lang = get_language()
    config.hero_title = _t(config.hero_title, lang)
    config.hero_subtitle = _t(config.hero_subtitle, lang)
    config.products_title = _t(config.products_title, lang)
    config.products_subtitle = _t(config.products_subtitle, lang)
    config.projects_title = _t(config.projects_title, lang)
    config.projects_subtitle = _t(config.projects_subtitle, lang)
    # N-43 (P0 SEO): meta_title / meta_description are the global default for every
    # page's <title> and meta description (base.html). They were previously English-only
    # in all five languages — now routed through _t() so the CSV importer can localize them
    # via _SIDEBAR_I18N (same channel as the six fields above).
    config.meta_title = _t(config.meta_title, lang)
    config.meta_description = _t(config.meta_description, lang)

    return {'config': config}