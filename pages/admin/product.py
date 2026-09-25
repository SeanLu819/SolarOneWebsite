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
import os
import shutil
import subprocess
import sys

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.views.main import ChangeList
from django.db.models import Case, IntegerField, Value, When
from django.utils.html import mark_safe

from .mixins import CacheClearMixin, admin_image_preview
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


def _sidebar_rank_map():
    """slug -> (rank, breadcrumb labels) mirroring the PUBLIC products sidebar.

    The single source of truth is ``pages.views.i18n._get_products_sidebar('en')``,
    so the admin changelist shows the same category → series → subseries grouping,
    order and parent/child relationships the front-end sidebar renders. Cached at
    module level (sidebar data is static); a sidebar failure must never break the
    admin, so any exception yields an empty map (everything falls back to plain
    ``order``-based ordering).
    """
    global _SIDEBAR_RANK_MAP_CACHE
    if _SIDEBAR_RANK_MAP_CACHE is not None:
        return _SIDEBAR_RANK_MAP_CACHE
    result = {}
    try:
        from pages.views.i18n import _get_products_sidebar
        sidebar = _get_products_sidebar('en')
        rank = 0
        for cat in sidebar:
            for s in cat.get('series', []):
                result[s['slug']] = (rank, [cat.get('label', ''), s.get('label', '')])
                rank += 1
                for sub in s.get('subseries', []):
                    result[sub['slug']] = (
                        rank, [cat.get('label', ''), s.get('label', ''), sub.get('label', '')])
                    rank += 1
    except Exception:
        result = {}
    _SIDEBAR_RANK_MAP_CACHE = result
    return result


_SIDEBAR_RANK_MAP_CACHE = None


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'order')



class SidebarOrderedChangeList(ChangeList):
    """ChangeList that sorts rows in public-sidebar traversal order.

    The ordering must live here — NOT in ``ProductAdmin.get_ordering()`` —
    because that method is also consumed by related-field list filters
    (``RelatedFieldListFilter.field_choices`` → ``field.get_choices(ordering=...)``)
    whose own queryset has no ``_sidebar_rank`` annotation (FieldError).

    This override hooks ``ChangeList.get_ordering(request, queryset)`` — the
    Django ≥4 hook that runs inside ``ChangeList.get_queryset`` *after* the
    annotated ``root_queryset`` (from ``ProductAdmin.get_queryset``) has been
    filtered, so ``_sidebar_rank`` always exists here.

    Explicit column sorting (``?o=...``) still wins over the sidebar default.
    """

    def get_ordering(self, request, queryset):
        ordering = super().get_ordering(request, queryset)
        # Explicit column sort (?o=...) → respect the user's choice.
        if self.params.get('o'):
            return ordering
        # Sidebar order only when the annotation actually exists on THIS
        # queryset (it always does here — root_queryset comes annotated from
        # ProductAdmin.get_queryset — but stay defensive).
        if '_sidebar_rank' in getattr(queryset.query, 'annotations', {}):
            ordering = ['_sidebar_rank'] + [
                f for f in ordering if f not in ('_sidebar_rank', 'pk', '-pk')
            ] + ['pk']
        return ordering

@admin.register(Product)
class ProductAdmin(CacheClearMixin, admin.ModelAdmin):
    form = ProductAdminForm
    list_display = ('image_preview', 'name', 'sidebar_tree', 'category', 'parent',
                    'page_layout', 'order', 'is_active')
    list_filter = ('category', 'parent', 'page_layout')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order']
    search_fields = ['name', 'category', 'description']
    inlines = [ProductImageInline]
    list_per_page = 25
    ordering = ('order', 'pk')
    change_list_template = 'admin/pages/product/change_list.html'

    def image_preview(self, obj):
        field = getattr(obj, 'image', None)
        src = ''
        if field and getattr(field, 'name', ''):
            from pages.seed_sync import _resolve_static_path
            path = _resolve_static_path(field.name, obj.slug, 'products', field_name='image')
            src = f'/static/{path}'
        return admin_image_preview(src, placeholder=mark_safe(
            '<span style="color:#999;">(no image)</span>'))
    image_preview.short_description = 'Card Image'

    def is_active(self, obj):
        wl = {'m-series','rt410-series','vsp-xxxxw-9m-yp','rt590fl-s','rt400hb','rt600sl-t'}
        if obj.parent is None and obj.slug in wl:
            return mark_safe('<span style="color:#28a745;font-weight:bold;">PAGE</span>')
        return mark_safe('<span style="color:#999;">detail</span>')
    is_active.short_description = 'Products Page'

    def sidebar_tree(self, obj):
        """Breadcrumb mirroring the public sidebar: Category ▸ Series ▸ Model."""
        entry = _sidebar_rank_map().get(obj.slug)
        if not entry:
            return mark_safe('<span style="color:#999;">— outside sidebar</span>')
        _, crumbs = entry
        parts = []
        for i, crumb in enumerate(crumbs):
            if i == 0:
                parts.append(f'<span style="color:#666;">{crumb}</span>')
            elif i == len(crumbs) - 1:
                parts.append(f'<strong>{crumb}</strong>')
            else:
                parts.append(crumb)
        return mark_safe(' ▸ '.join(parts))
    sidebar_tree.short_description = 'Sidebar Position'

    def get_queryset(self, request):
        """Annotate the sidebar traversal rank (see SidebarOrderedChangeList).

        NOTE: no ordering is applied here. Django's ``ModelAdmin.get_queryset``
        and the related-field list filters both call ``get_ordering()`` inside
        their own querysets — an annotation-based ordering there raises
        FieldError (``_sidebar_rank`` only exists on the changelist queryset).
        The actual ordering lives in ``SidebarOrderedChangeList.order_queryset``.
        """
        qs = super().get_queryset(request)
        rank_map = _sidebar_rank_map()
        if not rank_map:
            return qs
        fallback_rank = max(rank for rank, _ in rank_map.values()) + 1
        whens = [When(slug=slug, then=Value(rank)) for slug, (rank, _) in rank_map.items()]
        return qs.annotate(_sidebar_rank=Case(*whens, default=Value(fallback_rank),
                                              output_field=IntegerField()))

    def get_changelist(self, request, **kwargs):
        return SidebarOrderedChangeList

    fieldsets = (
        (None, {
            'fields': (('name', 'slug'), 'category', 'parent', 'page_layout', 'order'),
            'description': 'Page template：系列首页 = 只展示 banner / 主图轮播 / 文字说明'
                           '（无光束角、尺寸图、参数表），用做大系列落地页；'
                           '产品详细页 = 展示全部技术参数。默认「产品详细页」。'
                           '选择「系列首页」后，仅详细页使用的表单区块（尺寸/光束角图、Energy 表等）会自动隐藏，数据保留不会删除。'
        }),
        ('Content', {
            # Put translations on its own row so it can span full width
            'fields': ('description', 'translations')
        }),
        ('Images', {
            # ordering_image / cert_image are ALSO used by the overview template
            # (free-form copy slot + certification badges), so they live here.
            'fields': ('image', 'banner_image', 'ordering_image', 'cert_image'),
            'description': '上传图片时请参考字段下方的尺寸提示。Ordering image 为订购信息示意图（两种模板都显示）。Cert image 为产品认证标识图，留空则使用通用默认认证图。'
        }),
        ('Detail-page images (仅在「产品详细页」显示)', {
            'classes': ('detail-only',),
            'fields': ('dimension_image', 'beam_angle_image'),
            'description': '尺寸图请使用"Dimension image"字段，配光曲线请使用"Beam angle image"字段，不要在轮播图中重复上传。这两个图只在产品详细页（product_detail）渲染，系列首页不显示。'
        }),
        ('Specs (flexible — up to 6, 4 columns × 3 rows)', {
            'fields': ('specs',),
            'description': '每个参数包含 label（名称）和 value（数值）。最多 6 组，每行 2 组（4 列），共 3 行，与前台显示一致。'
        }),
        ('Energy & Performance Data (17 standard parameters — 仅「产品详细页」)', {
            'classes': ('detail-only',),
            'fields': ('energy_data',),
            'description': '详情页 ENERGY AND PERFORMANCE DATA 表格的 17 个标准参数。填写 value（值）即可，留空的行不会显示。选为「系列首页」时本区块自动隐藏，数据保留、不会删除。'
        }),
        ('Ordering Information (订购信息 — 两种模板)', {
            'fields': ('model_number', 'ordering_info'),
            'description': 'Model Number 为该产品的型号标识（如 FL1M-80W-30K-S），也用于页面的 JSON-LD。下方表格共 9 列，每列可输入多行（换行分隔）。产品详细页按 9 列表格渲染；系列首页则把每列内容平铺为文字行，与 Ordering image 一起构成图文区块。留空则整列不显示。'
        }),
        ('Legacy specs (read-only — 仅「产品详细页」)', {
            'fields': (('power', 'efficacy'), ('output', 'beam_angle', 'protection')),
            'classes': ('collapse', 'detail-only'),
        }),
    )

    class Media:
        css = {'all': ('admin/css/admin_overrides.css',)}
        js = ('admin/js/auto_translate.js', 'admin/js/page_layout_toggle.js')

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