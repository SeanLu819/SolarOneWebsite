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
import hashlib
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


_STATIC_IMAGE_HASH_INDEX = None
_IMAGE_EXTS = ('.webp', '.jpg', '.jpeg', '.png', '.gif', '.avif')


def _file_md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def reset_static_image_hash_index():
    """Drop the process cache — call after any external change to static/images."""
    global _STATIC_IMAGE_HASH_INDEX
    _STATIC_IMAGE_HASH_INDEX = None


def _static_image_hash_index():
    """``md5 -> [static-relative paths]`` for every image under static/images/.

    Built once per process（318 张 / 36 MB，几十毫秒）。`_source/` 原图目录跳过。

    🔴 只认真源 `static/` —— 与 `views.utils._list_static_dir` 同一条铁律：
    绝不并入 `staticfiles/`（collectstatic 的陈旧快照）。
    """
    global _STATIC_IMAGE_HASH_INDEX
    if _STATIC_IMAGE_HASH_INDEX is not None:
        return _STATIC_IMAGE_HASH_INDEX
    index = {}
    root = os.path.join(settings.BASE_DIR, 'static', 'images')
    static_root = os.path.join(settings.BASE_DIR, 'static')
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != '_source']
        for fn in filenames:
            if not fn.lower().endswith(_IMAGE_EXTS):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, static_root).replace('\\', '/')
            index.setdefault(_file_md5(full), []).append(rel)
    _STATIC_IMAGE_HASH_INDEX = index
    return index


def _static_copy_deduped(src, dst_dir, filename):
    """Copy ``src`` to ``dst_dir/filename`` **unless byte-identical content
    already lives somewhere under static/images/** — then reuse that path.

    Returns ``(seed_relative_path, reused_existing)``.

    🔴 背景（v1.9.9 实测）：旧实现无条件 `shutil.copy2` 到 per-slug 目录，
    于是同一张图被 18 个产品各传一次 = 18 份字节相同的副本（认证徽标最夸张，
    19 份 / 782 KB）。人工删副本没用 —— 后台下次上传立刻反弹。
    这里在**写入前**按内容哈希查表：命中就只记路径不写盘。
    """
    static_root = os.path.join(settings.BASE_DIR, 'static')
    rel_dir = os.path.relpath(dst_dir, static_root).replace('\\', '/')
    want = f'{rel_dir}/{filename}'

    digest = _file_md5(src)
    index = _static_image_hash_index()
    hits = index.get(digest) or []

    if want in hits:
        return want, True          # 目标位置已有同一份内容
    if hits:
        # 复用既有副本：优先同名（URL 更可预期），其次字典序保证结果稳定
        same_name = [p for p in hits if os.path.basename(p) == filename]
        return sorted(same_name or hits)[0], True

    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, filename))
    index.setdefault(digest, []).append(want)
    return want, False


class ProductAdminForm(forms.ModelForm):
    """Custom form that renders specs, energy_data, and ordering_info via custom widgets."""

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'specs': SpecsWidget,
            'energy_data': EnergyDataWidget,
            'ordering_info': OrderingInfoWidget,
            'description': forms.Textarea(attrs={'rows': 2, 'style': 'width:100%;max-width:900px;box-sizing:border-box;max-height:5.5em;'}),
            'translations': TranslationsWidget(attrs={'rows': '2'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 封面下拉只列出本产品已上传的轮播图，避免跨产品误选。
        instance = kwargs.get('instance')
        if instance and instance.pk:
            self.fields['cover_image'].queryset = ProductImage.objects.filter(
                product=instance).order_by('order', 'pk')
        else:
            self.fields['cover_image'].queryset = ProductImage.objects.none()


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
            'fields': ('image', 'cover_image', 'banner_image', 'ordering_image', 'cert_image'),
            'description': '「封面图（从轮播图选择）」可直接复用下方 Product images 中的某一张当卡片/详情主图，<b>不额外占空间</b>；选中后上方「主图」可留空。两张都填时以封面选择为准。Ordering image 为订购信息示意图（两种模板都显示）。Cert image 为产品认证标识图（UL / DLC / GS / CE / IP66 标识条）。留空则自动使用这张通用标识图——所有产品共用同一份，请勿逐个产品重复上传。'
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
        css = {'all': ('admin/css/admin_overrides_v2.css',)}
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
                    # 内容相同就直接复用既有文件（见 _static_copy_deduped 的说明）
                    seed_paths[field_name], _reused = _static_copy_deduped(
                        src, static_dir, filename)

        ordering_field = getattr(obj, 'ordering_image', None)
        if ordering_field and getattr(ordering_field, 'name', ''):
            src = os.path.join(media_root, str(ordering_field))
            if os.path.exists(src):
                filename = _clean_hashed_filename(str(ordering_field))
                static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products', 'ordering')
                seed_paths['ordering_image'], _reused = _static_copy_deduped(
                    src, static_dir, filename)

        # Cert image — synced to per-product slug dir for Vercel persistence
        cert_field = getattr(obj, 'cert_image', None)
        if cert_field and getattr(cert_field, 'name', ''):
            src = os.path.join(media_root, str(cert_field))
            if os.path.exists(src):
                filename = _clean_hashed_filename(str(cert_field))
                static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products', slug)
                seed_paths['cert_image'], _reused = _static_copy_deduped(
                    src, static_dir, filename)

        # Gallery images are synced in ``save_related`` — the inline rows do not
        # exist yet at this point (iron rule 25: save_model precedes save_formset).

        try:
            subprocess.run(
                [sys.executable, 'manage.py', 'collectstatic', '--noinput'],
                cwd=settings.BASE_DIR,
                capture_output=True,
                timeout=120,
            )
        except Exception:
            pass

        # 🔴 v1.10.24 — 把解析出的 static 相对路径写回 DB。
        # 背景（本函数修复的根因）：ImageField 的 ``upload_to`` 决定了上传落点
        # （``products/`` / ``products/gallery/``），Django 会把那个相对路径
        # **自动存进 DB**；而本函数复制到的真源目录是
        # ``static/images/products/<slug>/``。两者结构不同 ⇒ DB 里的路径永远
        # 指向磁盘上不存在的目录，前台 srcset 全 404（缩略图走原图 src 侥幸能显示，
        # 主图裂图）。此前本函数算出的 ``seed_paths`` / ``gallery_paths`` 只存进
        # 局部变量就丢弃，从不回写 ⇒ 每传一次图就复现一次。
        #
        # 现在写回 ``images/products/<slug>/<file>``（与 seed_data.json 约定一致）。
        for field_name, rel in seed_paths.items():
            if getattr(obj, field_name, None) and rel:
                setattr(obj, field_name, rel)
        if seed_paths:
            obj.save(update_fields=list(seed_paths.keys()))
        reset_static_image_hash_index()

    def save_related(self, request, form, formsets, change):
        """Gallery images only exist after ``save_formset`` ran.

        🔴 Iron rule 25: ``save_model`` fires BEFORE ``save_formset``, so syncing
        the inline gallery there would export the *previous* image set. That is
        why this hook exists — the inline rows are guaranteed saved at this point.
        """
        super().save_related(request, form, formsets, change)
        obj = form.instance
        gallery_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products', obj.slug)
        media_root = settings.MEDIA_ROOT
        touched = False
        for img in obj.images.all():
            if not (img.image and getattr(img.image, 'name', '')):
                continue
            src = os.path.join(media_root, str(img.image))
            if not os.path.exists(src):
                continue
            filename = _clean_hashed_filename(str(img.image))
            rel, _reused = _static_copy_deduped(src, gallery_dir, filename)
            if rel and img.image.name != rel:
                img.image = rel
                img.save(update_fields=['image'])
                touched = True
        if touched:
            reset_static_image_hash_index()
            self._sync_seed_files(request)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        self._sync_product_images(obj)