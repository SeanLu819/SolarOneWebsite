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

from django.conf import settings
from django.contrib import messages
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

    def _sync_seed_files(self, request=None):
        """Export the DB to ``seed_data.json`` + ``seed_data.py``.

        Production (Vercel) serves content from the committed seed JSON, not from
        the database, so this export is what makes an admin edit *able* to reach
        the live site.

        Why it warns instead of staying silent (2026-09-17): the export used to
        report failures only via ``logger.error``. A failure here means the edit
        never reaches production — invisible breakage that can hide for weeks.
        Failures (and the production-only no-op) now surface as an admin warning.
        """
        if getattr(settings, 'IS_VERCEL', False):
            # Production FS is read-only and its DB is an ephemeral /tmp SQLite,
            # so an export here can never persist. Say so instead of implying
            # that the save went live.
            if request is not None:
                messages.warning(
                    request,
                    '生产环境的内容以 seed_data.json 为准：此处的修改不会自动上线。'
                    '请在本地编辑后提交推送，由 Vercel 重新构建发布。'
                )
            return
        try:
            from pages.seed_sync import sync_seed_data
            if sync_seed_data() is False:
                raise RuntimeError('sync_seed_data() returned False (see seed_sync log)')
        except Exception as e:
            logger.error(f'Failed to sync seed files: {e}', exc_info=True)
            if request is not None:
                messages.warning(
                    request,
                    f'⚠️ seed_data.json 导出失败，本次修改不会上线：{e}'
                )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._clear_cache()
        self._sync_seed_files(request)

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        self._clear_cache()
        self._sync_seed_files(request)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        self._clear_cache()
        self._sync_seed_files(request)