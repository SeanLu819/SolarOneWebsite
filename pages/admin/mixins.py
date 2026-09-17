"""CacheClearMixin: shared admin behavior for clearing frontend caches.

Used by ProductAdmin / ProjectAdmin / NewsArticleAdmin / SiteConfigAdmin /
ProductsPageCardAdmin. Any save/delete invalidates:
  1. ``cache['site_config']`` and ``cache['seed_data_json']`` (CACHE backend)
  2. ``pages.views.invalidate_enrichment_cache()`` (in-memory caches)
  3. Regenerates ``seed_data.py`` + ``seed_data.json`` via
     ``pages.seed_sync.sync_seed_data()`` so Vercel deploys stay in sync.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
import logging

from django.core.cache import cache
from django.utils.html import mark_safe

logger = logging.getLogger(__name__)


def admin_image_preview(src, size=(60, 45), placeholder='(no image)'):
    """Return an inline ``<img>`` thumbnail (or the placeholder) for admin list views.

    B9 single source: ``ProductAdmin.image_preview`` and
    ``ProductsPageCardAdmin.image_preview`` hardcoded byte-identical 60x45
    ``object-fit:contain`` thumbnail markup. ``src`` must be a ready-to-use URL
    (callers resolve static vs media differently); a falsy ``src`` yields
    ``placeholder`` unchanged.
    """
    if not src:
        return placeholder
    width, height = size
    return mark_safe(
        f'<img src="{src}" style="width:{width}px;height:{height}px;'
        f'object-fit:contain;border:1px solid #ddd;border-radius:4px;'
        f'background:#f9f9f9;" />'
    )


class CacheClearMixin:
    """Mixin that clears cached frontend data and syncs seed files after any save/delete in admin."""

    def _clear_cache(self):
        cache.delete('site_config')
        cache.delete('seed_data_json')
        try:
            from pages.views import invalidate_enrichment_cache
            invalidate_enrichment_cache()
        except Exception:
            pass

    def _sync_seed_files(self):
        """Sync database data to seed_data.py and seed_data.json for Vercel deployment."""
        try:
            from pages.seed_sync import sync_seed_data
            sync_seed_data()
        except Exception as e:
            logger.error(f'Failed to sync seed files: {e}', exc_info=True)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._clear_cache()
        self._sync_seed_files()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        self._clear_cache()
        self._sync_seed_files()

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        self._clear_cache()
        self._sync_seed_files()