"""NewsArticleAdmin: news/article list admin.

Smallest admin in the project — list + filter + search + date hierarchy.
Inherits CacheClearMixin so saving a published article invalidates site caches
and re-syncs seed files.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
from django.contrib import admin
from django import forms

from .mixins import CacheClearMixin
from .widgets import TranslationsWidget
from pages.models import NewsArticle, NewsImage


class ImageInline(admin.TabularInline):
    """Gallery photos rendered as figures on the news card.

    The card layout shows every image at its native size, so the editor controls
    which photos appear and in what order — not a single cropped cover image.
    """
    model = NewsImage
    extra = 1
    fields = ('image', 'alt_text', 'caption', 'order')


@admin.register(NewsArticle)
class NewsArticleAdmin(CacheClearMixin, admin.ModelAdmin):
    list_display = ('title', 'category', 'published_at', 'is_published')
    list_filter = ('category', 'is_published')
    list_editable = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'summary', 'content']
    date_hierarchy = 'published_at'
    inlines = (ImageInline,)
    fields = ('title', 'slug', 'category', 'summary', 'content', 'image', 'published_at', 'is_published', 'translations')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        """Attach the per-language widget to ``translations`` only.

        Only title/summary/content are translatable (see
        ``NEWS_TRANSLATABLE_FIELDS`` in pages/views/data_loaders.py) — ``slug``
        stays a URL fragment and the gallery photos' alt/caption stay English.
        Done via ``formfield_for_dbfield`` rather than ``formfield_overrides``
        because the latter is model-wide and would leak into Product/Project admin.

        Width fix (news admin tweak): ``summary``/``content`` are plain
        ``TextField`` textareas whose default ``cols=40`` is too narrow. They
        fill the form field area with a 900px floor (``min-width``), so they
        are never narrower than — and on desktop wider than — the 900px
        ``translations`` textareas. ``summary`` height is halved to 5 rows
        (default is 10) per request.
        """
        if db_field.name == 'translations':
            # Mirror the Project admin's multi-language textboxes: the
            # TranslationsWidget renders each language textarea at
            # width:100%; max-width:900px (hard-coded in widgets.py). Keep that
            # 900px cap and bump rows to 10 to match ProjectAdminForm. Do NOT
            # shrink these — content/summary are widened *past* this, not the
            # other way around.
            kwargs['widget'] = TranslationsWidget(attrs={'rows': '10'})
        elif db_field.name == 'summary':
            # Wider than the 900px translations boxes: fill the form field area
            # and never drop below 900px (min-width floor). Height halved to 5
            # rows (default Textarea is 10) per request.
            kwargs['widget'] = forms.Textarea(attrs={
                'rows': '5',
                'style': 'width:100% !important;min-width:900px;box-sizing:border-box;',
            })
        elif db_field.name == 'content':
            # Wider than the translations boxes (fill the field area, min 900px)
            # per request — content should exceed the 900px translations
            # textareas, not be capped down to match them.
            kwargs['widget'] = forms.Textarea(attrs={
                'rows': '10',
                'style': 'width:100% !important;min-width:900px;box-sizing:border-box;',
            })
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    class Media:
        # Mirror the Project/Product admin: admin_overrides.css is what stacks
        # the per-language translation blocks VERTICALLY and lets them use the
        # full column width. Without it Django admin's default flex-container
        # lays the five .translation-lang blocks out as one horizontal row of
        # narrow columns (the bug this fixes). auto_translate.js powers the
        # Auto-Translate buttons rendered by TranslationsWidget — they were
        # dead on this page before because the script was never loaded here.
        css = {'all': ('admin/css/admin_overrides.css',)}
        js = ('admin/js/auto_translate.js',)