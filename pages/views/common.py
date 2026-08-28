import logging
from django.core.cache import cache
from django.templatetags.static import static
from django.utils.translation import get_language
from pages.models import SiteConfig
from .utils import _load_seed
from .i18n import _t

logger = logging.getLogger(__name__)


def get_common_context():
    """Get context shared across all pages"""
    config = cache.get('site_config')
    if not config:
        try:
            config = SiteConfig.objects.first()
            if not config:
                config = SiteConfig.objects.create()
            cache.set('site_config', config, timeout=300)
        except Exception:
            logger.warning('DB SiteConfig query failed, building from seed JSON', exc_info=True)
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

    return {'config': config}