import json

from django import forms
from django.contrib import admin
from django.conf import settings
from django.core.cache import cache
from django.utils.html import escape, mark_safe
from .models import (
    Product, ProductImage, Project, ProjectImage,
    ContactMessage, SiteConfig, Visitor, DailyStats,
    NewsArticle,
)

# Admin branding with version
admin.site.site_header = f'SolarOne Admin v{settings.APP_VERSION}'
admin.site.site_title = f'SolarOne Admin v{settings.APP_VERSION}'
admin.site.index_title = f'Administration (v{settings.APP_VERSION})'


class SpecsWidget(forms.Widget):
    """Render the flexible specs JSON as 6 label/value input pairs."""

    def render(self, name, value, attrs=None, renderer=None):
        if value is None:
            value = []
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except Exception:
                value = []
        if not isinstance(value, list):
            value = []
        while len(value) < 6:
            value.append({})
        value = value[:6]

        inputs = []
        for i, spec in enumerate(value):
            label = spec.get('label', '') if isinstance(spec, dict) else ''
            val = spec.get('value', '') if isinstance(spec, dict) else ''
            inputs.append(
                f'<input type="text" name="{name}_{i}_label" value="{escape(label)}" '
                f'placeholder="Label {i + 1}" style="padding:6px 8px;border:1px solid #ccc;border-radius:4px;width:100%;box-sizing:border-box;">'
                f'<input type="text" name="{name}_{i}_value" value="{escape(val)}" '
                f'placeholder="Value {i + 1}" style="padding:6px 8px;border:1px solid #ccc;border-radius:4px;width:100%;box-sizing:border-box;">'
            )
        return mark_safe(
            f'<div style="max-width:900px;">'
            f'<p style="margin:0 0 10px;color:#666;font-size:12px;">'
            f'最多 6 组参数，每行 2 组（4 列），共 3 行，与前台显示一致。</p>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px 12px;">'
            f'{"".join(inputs)}'
            f'</div></div>'
        )

    def value_from_datadict(self, data, files, name):
        specs = []
        for i in range(6):
            label = data.get(f'{name}_{i}_label', '').strip()
            value = data.get(f'{name}_{i}_value', '').strip()
            if label or value:
                specs.append({'label': label, 'value': value})
        return specs


class ProductAdminForm(forms.ModelForm):
    """Custom form that renders specs via SpecsWidget."""

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'specs': SpecsWidget,
        }


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


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order')


@admin.register(Product)
class ProductAdmin(CacheClearMixin, admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('name', 'category', 'parent', 'order')
    list_filter = ('category', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']
    search_fields = ['name', 'category', 'description']
    inlines = [ProductImageInline]
    fieldsets = (
        (None, {
            'fields': (('name', 'slug'), 'category', 'parent', 'order')
        }),
        ('Content', {
            'fields': ('description', 'translations')
        }),
        ('Specs (flexible — up to 6, 4 columns × 3 rows)', {
            'fields': ('specs',),
            'description': '每个参数包含 label（名称）和 value（数值）。最多 6 组，每行 2 组（4 列），共 3 行，与前台显示一致。'
        }),
        ('Legacy specs (read-only, will be migrated to Specs above)', {
            'fields': (('power', 'efficacy'), ('output', 'beam_angle', 'protection')),
            'classes': ('collapse',),
        }),
        ('Images', {
            'fields': ('image', 'banner_image', 'dimension_image', 'beam_angle_image'),
            'description': '上传图片时请参考字段下方的尺寸提示。尺寸图请使用“Dimension image”字段，配光曲线请使用“Beam angle image”字段，不要在轮播图中重复上传。'
        }),
    )


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'alt_text', 'order')


@admin.register(Project)
class ProjectAdmin(CacheClearMixin, admin.ModelAdmin):
    list_display = ('title', 'venue_type', 'sport_type', 'location', 'order')
    list_filter = ('venue_type', 'sport_type')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['order']
    search_fields = ['title', 'location', 'description']
    inlines = [ProjectImageInline]
    fieldsets = (
        (None, {
            'fields': (('title', 'slug'), ('venue_type', 'sport_type'), 'location', 'order')
        }),
        ('Content', {
            'fields': ('description', 'results', 'translations')
        }),
        ('Images', {
            'fields': ('image',),
            'description': '上传图片时请参考字段下方的尺寸提示；项目详情页轮播图请在下方“项目轮播图”中添加。'
        }),
    )


@admin.register(NewsArticle)
class NewsArticleAdmin(CacheClearMixin, admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published')
    list_filter = ('is_published',)
    list_editable = ['is_published']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'summary', 'content']
    date_hierarchy = 'published_at'


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
