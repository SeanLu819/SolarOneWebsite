"""ProjectAdmin: project/case-study admin with PDF + image sync.

Responsibilities:
  - Custom form (ProjectAdminForm): wider translations textarea, smaller
    results textarea, TranslationsWidget for 5-language coverage.
  - Inline ``ProjectImage`` gallery.
  - ``_sync_project_images()``: copies media/ → static/images/projects/{slug}/,
    strips hash suffixes, prunes stale files (preserves template-hardcoded
    comparison shots like ``old-hid-lighting.webp``).
  - ``save_model()`` regenerates seed_data.json + seed_data.py via
    ``_sync_seed_files()`` (reads latest DB values) after PDF/image copy, so
    the committed seed stays correct for Vercel without hand-written patches.
  - ``save_model()`` also handles uploaded PDF → static/files/ for local dev.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
import os
import shutil

from django import forms
from django.conf import settings
from django.contrib import admin

from .mixins import CacheClearMixin
from .widgets import TranslationsWidget
from pages.models import Project, ProjectImage, _clean_hashed_filename


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
            'description': forms.Textarea(attrs={'rows': 8, 'style': 'width:100%;max-width:900px;box-sizing:border-box;'}),
            'results': forms.Textarea(attrs={'rows': 3, 'style': 'width:100%;max-width:900px;box-sizing:border-box;'}),
            'translations': TranslationsWidget(attrs={'rows': 10}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 封面下拉只列出本项目已上传的轮播图，避免跨项目误选。
        instance = kwargs.get('instance')
        if instance and instance.pk:
            self.fields['cover_image'].queryset = ProjectImage.objects.filter(
                project=instance).order_by('order', 'pk')
        else:
            self.fields['cover_image'].queryset = ProjectImage.objects.none()


@admin.register(Project)
class ProjectAdmin(CacheClearMixin, admin.ModelAdmin):
    form = ProjectAdminForm
    change_form_template = "admin/pages/project/change_form.html"
    list_display = ('title', 'venue_type', 'sport_type', 'location', 'order')
    list_filter = ('venue_type', 'sport_type')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['order']
    search_fields = ['title', 'location', 'description']
    inlines = [ProjectImageInline]
    # Plain multi-select is painful with ~24 products; the horizontal widget
    # shows the picked luminaires at a glance. The M2M order is not preserved,
    # so the page renders them in Product.Meta order.
    filter_horizontal = ('related_products',)
    fieldsets = (
        (None, {
            'fields': (('title', 'slug'), ('venue_type', 'sport_type'), 'location', 'order')
        }),
        ('Related Products', {
            'fields': ('related_products',),
            'description': '手工选择本项目实际使用的灯具。可多选；<b>不选则不显示</b>页面底部的 "Related Products" 区块（不再自动匹配）。',
        }),
        ('Images', {
            'fields': ('image', 'cover_image'),
            'description': '「封面图（从轮播图选择）」可直接复用下方 Project images 中的某一张当卡片/详情主图，<b>不额外占空间</b>；选中后上方「主图」可留空。两张都填时以封面选择为准；主图也空时详情页/列表页自动取第一张轮播图。轮播图片请在下方 "Project images" 区域添加。'
        }),
        ('Content', {
            # Put description and results each on their own row so they stack vertically
            'fields': ('description', 'results', 'translations')
        }),
        ('PDF Document', {
            'fields': ('pdf_static', 'pdf_file'),
            'description': '推荐使用 pdf_static 字段（输入路径如 "files/project-name.pdf"），文件请手动放入 static/files/ 目录。pdf_file 仅供本地开发预览使用，上传后 Vercel 无法访问。',
            'classes': ('collapse',),
        }),
    )


    def _sync_project_images(self, obj):
        slug = obj.slug
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'projects', slug)
        os.makedirs(static_dir, exist_ok=True)
        media_root = settings.MEDIA_ROOT

        # Collect destination filenames for stale-file pruning
        current_dest_names = set()

        cover_rel = ''
        if obj.image:
            src_cover = os.path.join(media_root, str(obj.image))
            if os.path.exists(src_cover):
                dst_name = _clean_hashed_filename(src_cover)
                current_dest_names.add(dst_name)
                dst_cover = os.path.join(static_dir, dst_name)
                shutil.copy2(src_cover, dst_cover)
                cover_rel = f'images/projects/{slug}/{dst_name}'

        gallery_paths = []
        for img in obj.images.all():
            src = os.path.join(media_root, str(img.image))
            if not os.path.exists(src):
                continue
            dst_name = _clean_hashed_filename(src)
            current_dest_names.add(dst_name)
            dst = os.path.join(static_dir, dst_name)
            shutil.copy2(src, dst)
            rel = f'images/projects/{slug}/{dst_name}'
            if rel not in gallery_paths:
                gallery_paths.append(rel)

        # Prune stale files no longer referenced by DB
        # Template-hardcoded special images (e.g. before/after comparison shots)
        # are preserved — they are not managed through ProjectImage records.
        _preserved = {'old-hid-lighting.webp', 'new-led-lighting.webp'}
        try:
            for entry in os.listdir(static_dir):
                if not entry.lower().endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                    continue
                if entry.lower() in _preserved:
                    continue
                if entry not in current_dest_names:
                    try:
                        os.remove(os.path.join(static_dir, entry))
                    except OSError:
                        pass
        except OSError:
            pass


    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Handle PDF file copy to static directory
        if obj.pdf_file:
            src = obj.pdf_file.path
            dst_dir = os.path.join(settings.BASE_DIR, 'static', 'files')
            os.makedirs(dst_dir, exist_ok=True)
            safe_name = obj.slug.replace('-', '_')
            _, ext = os.path.splitext(os.path.basename(src))
            dst_name = f'{safe_name}{ext}'
            dst = os.path.join(dst_dir, dst_name)
            if os.path.exists(src):
                shutil.copy2(src, dst)
                obj.pdf_static = f'files/{dst_name}'
                Project.objects.filter(pk=obj.pk).update(pdf_static=obj.pdf_static)
        self._sync_project_images(obj)
        # Regenerate seed_data.json + seed_data.py now that pdf_static / image
        # paths are final (replaces the hand-written pdf_url patch that used to
        # live in _update_seed_pdf_url). _sync_seed_files reads the latest DB
        # values so the committed seed stays correct for Vercel.
        # ``request`` must be forwarded so a failed export surfaces as an admin
        # warning instead of a silent logger.error (see CacheClearMixin).
        self._sync_seed_files(request)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model == ProjectImage:
            self._sync_project_images(form.instance)

    class Media:
        css = {'all': ('admin/css/admin_overrides_v2.css',)}
        js = ('admin/js/auto_translate.js',)