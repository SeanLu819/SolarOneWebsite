"""ProductAdmin: full product model admin with rich widgets + image sync.

The most complex ModelAdmin in the project:
  - 4 custom widgets (Specs / EnergyData / OrderingInfo / Translations)
  - Custom form (ProductAdminForm) wiring those widgets into the JSON fields
  - Inline ``ProductImage`` gallery
  - ``_sync_product_images()``: copies media/ → static/, strips hash suffixes,
    rewrites paths in seed_data.json + seed_data.py
  - ``is_active`` column highlights the 6 products that have public-facing
    ProductsPage entries (``m-series / rt410-series / vsp-xxxxw-9m-yp /
    rt590fl-s / rt400hb / rt600sl-t``)

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
import json
import os
import re
import shutil
import subprocess
import sys

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import mark_safe

from .mixins import CacheClearMixin
from .widgets import (
    EnergyDataWidget,
    OrderingInfoWidget,
    SpecsWidget,
    TranslationsWidget,
)
from pages.models import (
    Product, ProductImage,
    _clean_hashed_filename,
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
            'description': forms.Textarea(attrs={'rows': 2, 'style': 'width:100%;max-width:900px;box-sizing:border-box;'}),
            'translations': TranslationsWidget(attrs={'rows': '2'}),
        }


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order')


@admin.register(Product)
class ProductAdmin(CacheClearMixin, admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('image_preview', 'name', 'category', 'parent', 'order', 'is_active')
    list_filter = ('category', 'parent')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']
    search_fields = ['name', 'category', 'description']
    inlines = [ProductImageInline]
    list_per_page = 25
    ordering = ('order', 'pk')
    change_list_template = 'admin/pages/product/change_list.html'

    def image_preview(self, obj):
        field = getattr(obj, 'image', None)
        if field and getattr(field, 'name', ''):
            from pages.seed_sync import _resolve_static_path
            path = _resolve_static_path(field.name, obj.slug, 'products', field_name='image')
            return mark_safe(
                f'<img src="/static/{path}" style="width:60px;height:45px;object-fit:contain;'
                f'border:1px solid #ddd;border-radius:4px;background:#f9f9f9;" />'
            )
        return mark_safe('<span style="color:#999;">(no image)</span>')
    image_preview.short_description = 'Card Image'

    def is_active(self, obj):
        wl = {'m-series','rt410-series','vsp-xxxxw-9m-yp','rt590fl-s','rt400hb','rt600sl-t'}
        if obj.parent is None and obj.slug in wl:
            return mark_safe('<span style="color:#28a745;font-weight:bold;">PAGE</span>')
        return mark_safe('<span style="color:#999;">detail</span>')
    is_active.short_description = 'Products Page'
    fieldsets = (
        (None, {
            'fields': (('name', 'slug'), 'category', 'parent', 'order')
        }),
        ('Content', {
            # Put translations on its own row so it can span full width
            'fields': ('description', 'translations')
        }),
        ('Images', {
            'fields': ('image', 'banner_image', 'dimension_image', 'beam_angle_image', 'ordering_image', 'cert_image'),
            'description': '上传图片时请参考字段下方的尺寸提示。尺寸图请使用"Dimension image"字段，配光曲线请使用"Beam angle image"字段，不要在轮播图中重复上传。Ordering image 为订购信息示意图。Cert image 为产品认证标识图，留空则使用通用默认认证图。'
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
            'fields': ('model_number', 'ordering_info'),
            'description': 'Model Number 为该产品的型号标识（如 FL1M-80W-30K-S）。下方表格共 9 列，每列可输入多行（换行分隔），大量数据可在产品间复用，只需修改对应列的值即可。留空则整列不显示。'
        }),
        ('Legacy specs (read-only, will be migrated to Specs above)', {
            'fields': (('power', 'efficacy'), ('output', 'beam_angle', 'protection')),
            'classes': ('collapse',),
        }),
    )

    class Media:
        css = {'all': ('admin/css/admin_overrides.css',)}
        js = ('admin/js/auto_translate.js',)

    def _sync_product_images(self, obj):
        slug = obj.slug
        media_root = settings.MEDIA_ROOT

        standard_fields = ['image', 'banner_image', 'dimension_image', 'beam_angle_image']
        seed_paths = {}

        for field_name in standard_fields:
            field = getattr(obj, field_name, None)
            if field and getattr(field, 'name', ''):
                src = os.path.join(media_root, str(field))
                if os.path.exists(src):
                    filename = _clean_hashed_filename(str(field))
                    static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products', slug)
                    os.makedirs(static_dir, exist_ok=True)
                    dst = os.path.join(static_dir, filename)
                    shutil.copy2(src, dst)
                    seed_paths[field_name] = f'images/products/{slug}/{filename}'

        ordering_field = getattr(obj, 'ordering_image', None)
        if ordering_field and getattr(ordering_field, 'name', ''):
            src = os.path.join(media_root, str(ordering_field))
            if os.path.exists(src):
                filename = _clean_hashed_filename(str(ordering_field))
                static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products', 'ordering')
                os.makedirs(static_dir, exist_ok=True)
                dst = os.path.join(static_dir, filename)
                shutil.copy2(src, dst)
                seed_paths['ordering_image'] = f'images/products/ordering/{filename}'

        # Cert image — synced to per-product slug dir for Vercel persistence
        cert_field = getattr(obj, 'cert_image', None)
        if cert_field and getattr(cert_field, 'name', ''):
            src = os.path.join(media_root, str(cert_field))
            if os.path.exists(src):
                filename = _clean_hashed_filename(str(cert_field))
                static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products', slug)
                os.makedirs(static_dir, exist_ok=True)
                dst = os.path.join(static_dir, filename)
                shutil.copy2(src, dst)
                seed_paths['cert_image'] = f'images/products/{slug}/{filename}'

        gallery_paths = []
        gallery_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products', slug)
        for img in obj.images.all():
            if img.image and getattr(img.image, 'name', ''):
                src = os.path.join(media_root, str(img.image))
                if os.path.exists(src):
                    os.makedirs(gallery_dir, exist_ok=True)
                    filename = _clean_hashed_filename(str(img.image))
                    dst = os.path.join(gallery_dir, filename)
                    shutil.copy2(src, dst)
                    gallery_paths.append(f'images/products/{slug}/{filename}')

        seed_path = os.path.join(settings.BASE_DIR, 'seed_data.json')
        seed_py_path = os.path.join(settings.BASE_DIR, 'pages', 'seed_data.py')

        try:
            with open(seed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for p in data.get('products', []):
                if p.get('slug') == slug:
                    for fn, path in seed_paths.items():
                        p[fn] = path
                    p['gallery'] = gallery_paths
                    break
            with open(seed_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')
        except Exception:
            pass

        try:
            with open(seed_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            idx = content.find(f'"slug": "{slug}"')
            if idx >= 0:
                for fn, path in seed_paths.items():
                    pattern = re.compile(f'"{fn}":\\s*"([^"]*)"')
                    match = pattern.search(content[idx:])
                    if match:
                        m_start = match.start() + idx
                        val_start = content.find('"', m_start) + 1
                        val_end = content.find('"', val_start)
                        content = content[:val_start] + path + content[val_end:]
                gal_match = re.search(r'"gallery":\s*\[[^\]]*\]', content[idx:])
                if gal_match:
                    g_start = gal_match.start() + idx
                    g_end = gal_match.end()
                    content = content[:g_start] + json.dumps(gallery_paths) + content[g_end:]
                with open(seed_py_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        except Exception:
            pass

        try:
            subprocess.run(
                [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
                cwd=settings.BASE_DIR,
                capture_output=True,
                timeout=120,
            )
        except Exception:
            pass

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._sync_product_images(obj)