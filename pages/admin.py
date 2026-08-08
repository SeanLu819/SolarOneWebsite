import json
import os
import shutil

from django import forms
from django.contrib import admin
from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.html import escape, mark_safe
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
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


ENERGY_DATA_FIELDS = [
    'Series Name',
    'Lumen Output',
    'System Wattage',
    'CRI',
    'Color Temperature (Kevin)',
    'Input Voltage (High Voltage)',
    'Input Voltage (Low Voltage)',
    'L70 Hours',
    'Operating Temperature Range',
    'Surge (Common Mode / Differential Mode)',
    'IP Rating',
    'Effective Projected Area (EPA) at 90°',
    'L" × W" × H"',
    'Approximate Weight',
    'Material',
    'LED Brand',
    'LED Driver',
]


class EnergyDataWidget(forms.Widget):
    """Render the energy & performance data JSON as 17 pre-labeled input rows."""

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

        # Build a dict from existing data for quick lookup
        data_dict = {}
        for item in value:
            if isinstance(item, dict) and item.get('label'):
                data_dict[item['label']] = item.get('value', '')

        rows = []
        for i, label in enumerate(ENERGY_DATA_FIELDS):
            val = escape(data_dict.get(label, ''))
            rows.append(
                f'<div style="display:flex;gap:8px;align-items:center;margin-bottom:4px;">'
                f'<input type="hidden" name="{name}_{i}_label" value="{escape(label)}">'
                f'<span style="width:320px;font-size:12px;color:#333;flex-shrink:0;">{escape(label)}</span>'
                f'<input type="text" name="{name}_{i}_value" value="{val}" '
                f'placeholder="输入值…" style="flex:1;padding:5px 8px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;font-size:12px;">'
                f'</div>'
            )
        return mark_safe(
            f'<div style="max-width:760px;padding:8px 0;">'
            f'<p style="margin:0 0 10px;color:#666;font-size:12px;">'
            f'以下是 17 个标准参数，填写 value（值）即可。留空则不显示该行。</p>'
            f'{"".join(rows)}'
            f'</div>'
        )

    def value_from_datadict(self, data, files, name):
        specs = []
        for i in range(len(ENERGY_DATA_FIELDS)):
            label = data.get(f'{name}_{i}_label', '').strip()
            value = data.get(f'{name}_{i}_value', '').strip()
            if value:  # Only include rows that have a value filled in
                specs.append({'label': label, 'value': value})
        return specs


ORDERING_COLUMNS = [
    'Series Name',
    'System Power',
    'CCT',
    'Voltage',
    'Beam Angle',
    'Fixture Color(option)',
    'Controls (Option)',
    'Bracket Type (option)',
    'Power Driver Location',
]


class OrderingInfoWidget(forms.Widget):
    """Render the ordering_info JSON as 9 columns matching the frontend table layout."""

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
        while len(value) < 9:
            value.append('')

        columns_html = []
        for i, header in enumerate(ORDERING_COLUMNS):
            val = escape(value[i] if i < len(value) else '')
            columns_html.append(
                f'<div style="min-width:110px;flex:1;">'
                f'<div style="font-size:10px;font-weight:700;color:#333;text-align:center;margin-bottom:4px;min-height:28px;display:flex;align-items:flex-end;justify-content:center;">{escape(header)}</div>'
                f'<textarea name="{name}_{i}" rows="4" '
                f'style="width:100%;padding:4px 6px;border:1px solid #ccc;border-radius:3px;'
                f'box-sizing:border-box;font-size:11px;font-family:monospace;resize:vertical;text-align:center;">{val}</textarea>'
                f'</div>'
            )
        return mark_safe(
            f'<div style="max-width:100%;padding:8px 0;overflow-x:auto;">'
            f'<p style="margin:0 0 10px;color:#666;font-size:12px;">'
            f'每列支持多行（换行分隔），留空列不显示。横向滚动查看全部 9 列。</p>'
            f'<div style="display:flex;gap:6px;min-width:1000px;">'
            f'{"".join(columns_html)}'
            f'</div></div>'
        )

    def value_from_datadict(self, data, files, name):
        values = []
        for i in range(9):
            val = data.get(f'{name}_{i}', '').strip()
            values.append(val)
        while values and not values[-1]:
            values.pop()
        return values


class TranslationsWidget(forms.Textarea):
    """Custom textarea that includes an auto-translate button right after it."""

    def __init__(self, attrs=None):
        default_attrs = {
            'rows': 12,
            'style': 'width:100%;max-width:900px;min-height:240px;'
                     'box-sizing:border-box;font-family:monospace;font-size:12px;',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs)

    def render(self, name, value, attrs=None, renderer=None):
        textarea_html = super().render(name, value, attrs, renderer)
        attrs = attrs or {}
        target_id = attrs.get('id', 'id_translations')
        return mark_safe(
            f'{textarea_html}'
            f'<div class="auto-translate-row" style="margin:8px 0 12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">'
            f'<button type="button" class="button auto-translate-btn" data-target-id="{target_id}" '
            f'style="white-space:nowrap;">🔄 Auto-Translate Description</button>'
            f'<span class="auto-translate-status" style="font-size:12px;color:#666;"></span>'
            f'</div>'
        )


class ProductAdminForm(forms.ModelForm):
    """Custom form that renders specs, energy_data, and ordering_info via custom widgets."""

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'specs': SpecsWidget,
            'energy_data': EnergyDataWidget,
            'ordering_info': OrderingInfoWidget,
            'description': forms.Textarea(attrs={'rows': 4, 'style': 'width:100%;max-width:900px;box-sizing:border-box;'}),
            'translations': TranslationsWidget(),
        }


class CacheClearMixin:
    """Mixin that clears cached frontend data and syncs seed files after any save/delete in admin."""
    def _clear_cache(self):
        cache.delete('site_config')
        cache.delete('seed_data_json')

    def _sync_seed_files(self):
        """Sync database data to seed_data.py and seed_data.json for Vercel deployment."""
        try:
            from pages.seed_sync import sync_seed_data
            sync_seed_data()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
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
            'fields': ('description', 'model_number', 'translations')
        }),
        ('Images', {
            'fields': ('image', 'banner_image', 'dimension_image', 'beam_angle_image'),
            'description': '上传图片时请参考字段下方的尺寸提示。尺寸图请使用\u201cDimension image\u201d字段，配光曲线请使用\u201cBeam angle image\u201d字段，不要在轮播图中重复上传。'
        }),
        ('Specs (flexible — up to 6, 4 columns × 3 rows)', {
            'fields': ('specs',),
            'description': '每个参数包含 label（名称）和 value（数值）。最多 6 组，每行 2 组（4 列），共 3 行，与前台显示一致。'
        }),
        ('Energy & Performance Data (17 standard parameters)', {
            'fields': ('energy_data',),
            'description': '详情页 ENERGY AND PERFORMANCE DATA 表格的 17 个标准参数。填写 value（值）即可，留空的行不会显示。'
        }),
        ('Ordering Information (订购信息表格)', {
            'fields': ('ordering_info',),
            'description': '产品详情页 ORDERING INFORMATION 表格，共 9 列。每列可输入多行（换行分隔）。留空则整列不显示。'
        }),
        ('Legacy specs (read-only, will be migrated to Specs above)', {
            'fields': (('power', 'efficacy'), ('output', 'beam_angle', 'protection')),
            'classes': ('collapse',),
        }),
    )

    class Media:
        css = {'all': ('admin/css/admin_overrides.css',)}
        js = ('admin/js/auto_translate.js',)


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'alt_text', 'order')


class ProjectAdminForm(forms.ModelForm):
    """Custom form: smaller results textarea, wider translations with auto-translate button."""

    class Meta:
        model = Project
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'style': 'width:100%;max-width:900px;box-sizing:border-box;'}),
            'results': forms.Textarea(attrs={'rows': 3, 'style': 'width:100%;max-width:900px;box-sizing:border-box;'}),
            'translations': TranslationsWidget(attrs={'rows': 10}),
        }


@admin.register(Project)
class ProjectAdmin(CacheClearMixin, admin.ModelAdmin):
    form = ProjectAdminForm
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
            'description': '主图。轮播图片请在下方 "Reference images" 区域添加。'
        }),
        ('PDF Document', {
            'fields': ('pdf_static', 'pdf_file'),
            'description': '推荐使用 pdf_static 字段（输入路径如 "files/project-name.pdf"），文件请手动放入 static/files/ 目录。pdf_file 仅供本地开发预览使用，上传后 Vercel 无法访问。',
            'classes': ('collapse',),
        }),
    )

    def _update_seed_pdf_url(slug, pdf_static):
        """Update pdf_url in seed_data.json for the given project slug."""
        import json
        seed_path = os.path.join(settings.BASE_DIR, 'seed_data.json')
        try:
            with open(seed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for p in data.get('projects', []):
                if p.get('slug') == slug:
                    p['pdf_url'] = pdf_static
                    break
            with open(seed_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')
        except Exception:
            pass

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # If a new PDF was uploaded via pdf_file, copy it to static/files/ and
        # set pdf_static so it's accessible on Vercel.
        if obj.pdf_file and not getattr(obj, '_pdf_copied', False):
            src = obj.pdf_file.path
            dst_dir = os.path.join(settings.BASE_DIR, 'static', 'files')
            os.makedirs(dst_dir, exist_ok=True)
            safe_name = obj.slug.replace('-', '_')
            _, ext = os.path.splitext(os.path.basename(src))
            dst_name = f'{safe_name}{ext}'
            dst = os.path.join(dst_dir, dst_name)
            shutil.copy2(src, dst)
            obj.pdf_static = f'files/{dst_name}'
            obj.save(update_fields=['pdf_static'])
            obj._pdf_copied = True
        # Sync pdf_static to seed_data.json so Vercel uses the correct path
        if obj.pdf_static:
            _update_seed_pdf_url(obj.slug, obj.pdf_static)

    class Media:
        css = {'all': ('admin/css/admin_overrides.css',)}
        js = ('admin/js/auto_translate.js',)


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
        ('References Section', {
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


# ---------------------------------------------------------------------------
# Auto-translate admin view
# ---------------------------------------------------------------------------
TARGET_LANGS = ['fr', 'es', 'de', 'ru', 'ar']

LANG_NAMES = {
    'fr': 'French',
    'es': 'Spanish',
    'de': 'German',
    'ru': 'Russian',
    'ar': 'Arabic',
}


@require_POST
@csrf_exempt
def admin_translate(request):
    """Translate text to all target languages using MyMemory (free, no API key)."""
    import json as _json
    import logging
    logger = logging.getLogger(__name__)

    try:
        data = _json.loads(request.body)
        fields = data.get('fields', {})
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not fields:
        return JsonResponse({'error': 'No fields to translate'}, status=400)

    from deep_translator import MyMemoryTranslator

    LANG_MAP = {
        'fr': 'fr-FR',
        'es': 'es-ES',
        'de': 'de-DE',
        'ru': 'ru-RU',
        'ar': 'ar-SA',
    }

    def _split_text(text, max_len=480):
        """Split text into chunks at sentence boundaries, max 480 chars each."""
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            split_at = text.rfind('. ', 0, max_len)
            if split_at == -1:
                split_at = text.rfind('; ', 0, max_len)
            if split_at == -1:
                split_at = text.rfind(' ', 0, max_len)
            if split_at == -1:
                split_at = max_len
            chunks.append(text[:split_at + 1])
            text = text[split_at + 1:].lstrip()
        return chunks

    def _translate_chunk(translator, text):
        """Translate a single chunk, auto-splitting if needed."""
        chunks = _split_text(text)
        translated_parts = []
        for chunk in chunks:
            for attempt in range(2):
                try:
                    translated_parts.append(translator.translate(chunk))
                    break
                except Exception as e:
                    if attempt == 0:
                        import time
                        time.sleep(1)
                        continue
                    logger.error(f'Chunk translate error: {e}')
                    translated_parts.append(f'[Error: {str(e)[:60]}]')
        return ' '.join(translated_parts)

    result = {}
    for lang in TARGET_LANGS:
        result[lang] = {}
        target_code = LANG_MAP.get(lang, lang)
        for field_name, text in fields.items():
            text = (text or '').strip()
            if not text:
                result[lang][field_name] = ''
                continue
            try:
                translator = MyMemoryTranslator(source='en-GB', target=target_code)
                translated = _translate_chunk(translator, text)
                result[lang][field_name] = translated
            except Exception as e:
                logger.error(f'Translate error [{lang}/{field_name}]: {e}')
                result[lang][field_name] = f'[Error: {str(e)[:80]}]'

    return JsonResponse({'translations': result})