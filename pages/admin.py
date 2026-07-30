from django.contrib import admin
from django.conf import settings
from django.core.cache import cache
from .models import Product, Project, ContactMessage, SiteConfig, Visitor, DailyStats

# Admin branding with version
admin.site.site_header = f'SolarOne Admin v{settings.APP_VERSION}'
admin.site.site_title = f'SolarOne Admin v{settings.APP_VERSION}'
admin.site.index_title = f'Administration (v{settings.APP_VERSION})'


class CacheClearMixin:
    """Mixin that clears cached frontend data after any save/delete in admin."""
    def _clear_cache(self):
        cache.delete('site_config')
        cache.delete('seed_data_json')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._clear_cache()

    def delete_model(self, request, obj):
        super().delete_model(request, obj)
        self._clear_cache()

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        self._clear_cache()


@admin.register(Product)
class ProductAdmin(CacheClearMixin, admin.ModelAdmin):
    list_display = ('name', 'category', 'power', 'order')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']
    search_fields = ['name', 'category']


@admin.register(Project)
class ProjectAdmin(CacheClearMixin, admin.ModelAdmin):
    list_display = ('title', 'location', 'order')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['order']
    search_fields = ['title', 'location']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read',)
    list_editable = ['is_read']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


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


from django.db.models import Count, Sum, F
from django.utils.html import format_html


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'path', 'browser', 'os', 'device', 'country', 'is_unique', 'visited_at')
    list_filter = ('is_unique', 'device', 'browser', 'os', 'visited_at')
    search_fields = ('ip_address', 'path', 'country')
    date_hierarchy = 'visited_at'
    readonly_fields = ('ip_address', 'path', 'referrer', 'user_agent', 'browser', 'browser_version', 'os', 'device', 'country', 'city', 'session_key', 'is_unique', 'visited_at')
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_visits', 'unique_visits', 'bounce_rate')
    readonly_fields = ('date', 'total_visits', 'unique_visits')
    list_per_page = 30
    ordering = ['-date']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def bounce_rate(self, obj):
        if obj.total_visits == 0:
            return "N/A"
        rate = ((obj.total_visits - obj.unique_visits) / obj.total_visits) * 100
        return f"{rate:.1f}%"
    bounce_rate.short_description = "Return Rate"
