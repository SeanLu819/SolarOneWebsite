"""NewsArticleAdmin: news/article list admin.

Smallest admin in the project — list + filter + search + date hierarchy.
Inherits CacheClearMixin so saving a published article invalidates site caches
and re-syncs seed files.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
from django.contrib import admin

from .mixins import CacheClearMixin
from pages.models import NewsArticle


@admin.register(NewsArticle)
class NewsArticleAdmin(CacheClearMixin, admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published')
    list_filter = ('is_published',)
    list_editable = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'summary', 'content']
    date_hierarchy = 'published_at'