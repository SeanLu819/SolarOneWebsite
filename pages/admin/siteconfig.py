"""SiteConfigAdmin: singleton settings admin (brand / typography / hero / etc).

The SiteConfig model holds ~50 fields split across 9 fieldsets:
  Brand & Meta / Typography / Hero Section / Hero Stats /
  Products Section / Projects Section / About Section /
  Contact Section / Social Media / Footer

Only one instance is allowed (``has_add_permission`` blocks a 2nd,
``has_delete_permission`` blocks the first from being deleted).

Inherits CacheClearMixin — any change to brand / typography invalidates the
frontend ``site_config`` cache key.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
from django.contrib import admin

from .mixins import CacheClearMixin
from pages.models import SiteConfig


@admin.register(SiteConfig)
class SiteConfigAdmin(CacheClearMixin, admin.ModelAdmin):
    fieldsets = (
        ('Brand & Meta', {
            'fields': ('brand_name', 'logo', 'meta_title', 'meta_description', 'og_image')
        }),
        ('Typography', {
            'fields': (
                ('font_family_body', 'font_family_heading'),
                ('font_size_base', 'font_size_nav'),
                ('font_size_hero_title', 'font_size_hero_subtitle'),
                ('font_size_section_title', 'font_size_body'),
                ('font_size_card_title', 'font_size_card_desc'),
                'accent_color',
            ),
            'classes': ('collapse',),
        }),
        ('Hero Section', {
            'fields': ('hero_title', 'hero_subtitle', 'hero_background')
        }),
        ('Hero Stats', {
            'fields': (
                ('stat_projects', 'stat_projects_label'),
                ('stat_countries', 'stat_countries_label'),
                ('stat_energy', 'stat_energy_label'),
                ('stat_support', 'stat_support_label'),
            )
        }),
        ('Products Section', {
            'fields': ('products_title', 'products_subtitle')
        }),
        ('Projects Section', {
            'fields': ('projects_title', 'projects_subtitle')
        }),
        ('About Section', {
            'fields': (
                'about_title', 'about_text_1', 'about_text_2',
                ('about_stat_years', 'about_stat_years_label'),
                ('about_stat_projects', 'about_stat_projects_label'),
                ('about_stat_countries', 'about_stat_countries_label'),
                ('about_stat_clients', 'about_stat_clients_label'),
            )
        }),
        ('Contact Section', {
            'fields': (
                'contact_title', 'contact_subtitle',
                'contact_email', 'contact_phone_1', 'contact_phone_2',
                'contact_whatsapp', 'contact_address',
            )
        }),
        ('Social Media', {
            'fields': ('social_facebook', 'social_instagram', 'social_youtube', 'social_tiktok', 'social_linkedin')
        }),
        ('Footer', {
            'fields': ('footer_description',)
        }),
    )

    def has_add_permission(self, request):
        # Only allow one instance
        if SiteConfig.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False