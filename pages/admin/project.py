"""ProjectAdmin: project/case-study admin with PDF + image sync.

Responsibilities:
  - Custom form (ProjectAdminForm): wider translations textarea, smaller
    results textarea, TranslationsWidget for 5-language coverage.
  - Inline ``ProjectImage`` gallery.
  - ``_sync_project_images()``: copies media/ → static/images/projects/{slug}/,
    strips hash suffixes, prunes stale files (preserves template-hardcoded
    comparison shots like ``old-hid-lighting.webp``).
  - ``_update_seed_pdf_url()``: rewrites pdf_url in both seed_data.json and
    seed_data.py when PDF static path changes.
  - ``save_model()`` also handles uploaded PDF → static/files/ for local dev.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
import json
import os
import re
import shutil

from django import forms
from django.conf import settings
from django.contrib import admin

from .mixins import CacheClearMixin
from .widgets import TranslationsWidget
from pages.models import Project, ProjectImage


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
    fieldsets = (
        (None, {
            'fields': (('title', 'slug'), ('venue_type', 'sport_type'), 'location', 'order')
        }),
        ('Images', {
            'fields': ('image',),
            'description': '主图。轮播图片请在下方 "Project images" 区域添加。'
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

    def _update_seed_pdf_url(self, slug, pdf_static):
        seed_path = os.path.join(settings.BASE_DIR, 'seed_data.json')
        seed_py_path = os.path.join(settings.BASE_DIR, 'pages', 'seed_data.py')
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
            try:
                import importlib
                from pages import seed_data as sd_mod
                importlib.reload(sd_mod)
                sd_data = sd_mod.SEED_DATA
                for p in sd_data.get('projects', []):
                    if p.get('slug') == slug:
                        p['pdf_url'] = pdf_static
                        break
                with open(seed_py_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                pattern = re.compile(
                    r'("pdf_url":\s*")[^"]*(")',
                    re.DOTALL
                )
                idx = content.find(f'"slug": "{slug}"')
                if idx >= 0:
                    next_idx = content.find('"pdf_url"', idx)
                    if next_idx >= 0:
                        start = content.find('"', next_idx) + 1
                        end = content.find('"', start)
                        content = content[:start] + pdf_static + content[end:]
                        with open(seed_py_path, 'w', encoding='utf-8') as f:
                            f.write(content)
            except Exception:
                pass
        except Exception:
            pass

    def _sync_project_images(self, obj):
        slug = obj.slug
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'projects', slug)
        os.makedirs(static_dir, exist_ok=True)
        media_root = settings.MEDIA_ROOT

        def _dest_name(src_path):
            """Strip Django's 7-char hash suffix so repeated uploads produce stable filenames."""
            base = os.path.basename(src_path)
            stem, ext = os.path.splitext(base)
            m = re.search(r'_([a-zA-Z0-9]{7})$', stem)
            if m:
                return f'{stem[:m.start()]}{ext}'
            return base

        # Collect destination filenames for stale-file pruning
        current_dest_names = set()

        cover_rel = ''
        if obj.image:
            src_cover = os.path.join(media_root, str(obj.image))
            if os.path.exists(src_cover):
                dst_name = _dest_name(src_cover)
                current_dest_names.add(dst_name)
                dst_cover = os.path.join(static_dir, dst_name)
                shutil.copy2(src_cover, dst_cover)
                cover_rel = f'images/projects/{slug}/{dst_name}'

        gallery_paths = []
        for img in obj.images.all():
            src = os.path.join(media_root, str(img.image))
            if not os.path.exists(src):
                continue
            dst_name = _dest_name(src)
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

        seed_path = os.path.join(settings.BASE_DIR, 'seed_data.json')
        seed_py_path = os.path.join(settings.BASE_DIR, 'pages', 'seed_data.py')

        # Update seed_data.json
        try:
            with open(seed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            found = False
            for p in data.get('projects', []):
                if p.get('slug') == slug:
                    if cover_rel:
                        p['image'] = cover_rel
                    p['gallery'] = gallery_paths
                    found = True
                    break
            if not found:
                # Add new project to seed_data.json
                new_proj = {
                    'pk': obj.pk,
                    'title': obj.title,
                    'location': obj.location,
                    'slug': slug,
                    'venue_type': obj.venue_type,
                    'sport_type': obj.sport_type,
                    'description': obj.description,
                    'results': obj.results,
                    'image': cover_rel,
                    'order': obj.order,
                    'pdf_url': obj.pdf_static if obj.pdf_static else '',
                    'gallery': gallery_paths,
                    'translations': obj.translations if obj.translations else {},
                }
                data['projects'].append(new_proj)
            with open(seed_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')
        except Exception:
            pass

        # Update seed_data.py
        try:
            with open(seed_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            idx = content.find(f'"slug": "{slug}"')
            if idx >= 0:
                img_match = re.search(r'"image":\s*"([^"]*)"', content[idx:])
                if img_match:
                    i_start = img_match.start() + idx
                    val_start = content.find('"', i_start) + 1
                    val_end = content.find('"', val_start)
                    if cover_rel:
                        content = content[:val_start] + cover_rel + content[val_end:]
                gal_match = re.search(r'"gallery":\s*\[[^\]]*\]', content[idx:])
                if gal_match:
                    g_start = gal_match.start() + idx
                    g_end = gal_match.end()
                    content = content[:g_start] + json.dumps(gallery_paths) + content[g_end:]
                with open(seed_py_path, 'w', encoding='utf-8') as f:
                    f.write(content)
        except Exception:
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
        if obj.pdf_static:
            self._update_seed_pdf_url(obj.slug, obj.pdf_static)
        self._sync_project_images(obj)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model == ProjectImage:
            self._sync_project_images(form.instance)

    class Media:
        css = {'all': ('admin/css/admin_overrides.css',)}
        js = ('admin/js/auto_translate.js',)