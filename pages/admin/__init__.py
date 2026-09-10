"""Pages admin: split into per-model modules under ``pages.admin``.

Sub-modules (alphabetical):
    contact       — ContactMessageAdmin (read-mostly contact form triage)
    mixins        — CacheClearMixin (cache invalidation + seed sync)
    news          — NewsArticleAdmin
    product       — ProductAdmin (rich widgets + image sync, 4 widgets)
    products_page — ProductsPageCardAdmin + custom /admin/products-page/ view
    project       — ProjectAdmin (PDF + image sync)
    siteconfig    — SiteConfigAdmin (singleton ~50-field settings)
    translate     — admin_translate POST endpoint (MyMemory bulk translate)
    visitor       — VisitorAdmin + DailyStatsAdmin (read-only analytics)
    widgets       — Specs / EnergyData / OrderingInfo / Translations widgets

Importing this package triggers ``@admin.register`` calls in each sub-module,
which attaches ModelAdmin classes to ``django.contrib.admin.site``.

Re-exports:
    admin_translate  — used by ``solarone/urls.py`` at /admin/translate/
    ProjectAdmin     — used by ``pages/tests.py`` for admin inspection tests

Previously a single ``pages/admin.py`` file (1246 lines, v1.4.6). Split in v1.5.0.
"""
from django.conf import settings
from django.contrib import admin

# Admin branding with version
admin.site.site_header = f'SolarOne Admin v{settings.APP_VERSION}'
admin.site.site_title = f'SolarOne Admin v{settings.APP_VERSION}'
admin.site.index_title = f'Administration (v{settings.APP_VERSION})'

# Trigger @admin.register decorators in each sub-module
from . import (  # noqa: F401, E402  (import for side effects)
    contact,
    news,
    product,
    products_page,
    project,
    siteconfig,
    visitor,
)
# Note: widgets.py / mixins.py / translate.py / products_page.py don't
# register models but contribute widgets / mixins / endpoints / URL hooks.

# Re-export for external callers (kept stable for tests + urls.py)
from .translate import admin_translate  # noqa: E402
from .project import ProjectAdmin  # noqa: E402