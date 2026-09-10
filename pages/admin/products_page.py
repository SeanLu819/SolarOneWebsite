"""ProductsPageCardAdmin + custom view + URL routing.

This module owns everything related to the public ``/products/`` page's
card grid (separate from ``ProductAdmin``, which manages the actual product
records). The cards live in the ``ProductsPageCard`` model.

Three responsibilities:
  1. ``ProductsPageCardAdmin``: standard ModelAdmin for editing individual
     cards. Includes a bulk action ``resync_card_images_to_static`` that
     force-re-syncs *all* card images from media/ → static/.
  2. ``products_page_view``: a card-grid admin view that lets editors see
     all cards at once and jump to each card's edit page.
  3. URL routing: ``admin.site.get_urls`` is monkey-patched to inject
     ``/admin/products-page/`` ahead of the default admin URLs.

Previously lived in ``pages/admin.py`` (1246 lines). Extracted in v1.5.0.
"""
import json
import os
import shutil
import subprocess
import sys

from django import forms
from django.conf import settings
from django.contrib import admin
from django.urls import path as url_path
from django.utils.html import mark_safe

from .mixins import CacheClearMixin
from pages.models import ProductsPageCard, SiteConfig, _clean_hashed_filename


PRODUCTS_PAGE_WHITELIST = [
    'm-series',
    'rt410-series',
    'vsp-xxxxw-9m-yp',
    'rt590fl-s',
    'rt400hb',
    'rt600sl-t',
]


@admin.register(ProductsPageCard)
class ProductsPageCardAdmin(CacheClearMixin, admin.ModelAdmin):
    list_display = ('image_preview', 'title', 'slug', 'link_url', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle', 'slug', 'link_url')
    ordering = ('order', 'pk')
    actions = ['resync_card_images_to_static']
    fieldsets = (
        (None, {
            'fields': (('title', 'slug'), 'subtitle', 'image', ('link_url', 'order', 'is_active'))
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj=obj, **kwargs)
        if 'subtitle' in form.base_fields:
            form.base_fields['subtitle'].widget = forms.Textarea(attrs={
                'rows': 4,
                'style': 'width:100%;min-height:80px;',
            })
        return form

    def _sync_ppc_image(self, obj=None):
        """Copy current PPC image(s) from media/ → static/images/products_page/
        with Django upload hashes stripped, and reflect into seed_data.json.

        Runs for all cards (all PPC images share one static dir), and also
        writes cleaned paths into seed_data['productspagecards'].
        """
        from pages.cards import ProductsPageCard as PPC
        media_root = settings.MEDIA_ROOT
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'products_page')
        os.makedirs(static_dir, exist_ok=True)

        cards = list(PPC.objects.all().order_by('pk'))
        current_names = set()
        card_paths = {}

        for card in cards:
            field = getattr(card, 'image', None)
            fname = getattr(field, 'name', None)
            if not fname:
                card_paths[card.pk] = ''
                continue
            src = os.path.join(media_root, str(fname))
            if not os.path.exists(src):
                card_paths[card.pk] = ''
                continue
            clean_name = _clean_hashed_filename(fname)
            current_names.add(clean_name)
            dst = os.path.join(static_dir, clean_name)
            try:
                if not os.path.exists(dst) or \
                   os.path.getmtime(src) > os.path.getmtime(dst) or \
                   os.path.getsize(src) != os.path.getsize(dst):
                    shutil.copy2(src, dst)
            except Exception:
                pass
            card_paths[card.pk] = f'images/products_page/{clean_name}'

        # Prune stale
        try:
            for entry in os.listdir(static_dir):
                entry_lower = entry.lower()
                if not entry_lower.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif', '.svg')):
                    continue
                if entry not in current_names:
                    try:
                        os.remove(os.path.join(static_dir, entry))
                    except Exception:
                        pass
        except Exception:
            pass

        # Persist to seed_data.json (use cleaned, flat relative paths)
        seed_path = os.path.join(settings.BASE_DIR, 'seed_data.json')
        try:
            with open(seed_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ppc_entries = data.setdefault('productspagecards', [])
            existing_by_slug = {}
            for i, e in enumerate(ppc_entries):
                s = (e.get('slug') or '').strip() or \
                    (e.get('link_url') or '').strip('/').split('/')[-1]
                if s:
                    existing_by_slug[s] = i
            for card in cards:
                s = (card.slug or '').strip()
                if not s:
                    continue
                cleaned = card_paths.get(card.pk, '')
                entry = {
                    'is_active': bool(card.is_active),
                    'order': card.order,
                    'title': card.title or '',
                    'subtitle': card.subtitle or '',
                    'slug': s,
                    'link_url': card.link_url or '',
                    'image': cleaned,
                }
                if s in existing_by_slug:
                    ppc_entries[existing_by_slug[s]] = entry
                else:
                    ppc_entries.append(entry)
                    existing_by_slug[s] = len(ppc_entries) - 1
            with open(seed_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write('\n')
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
        try:
            self._sync_ppc_image(obj)
        except Exception:
            pass

    def resync_card_images_to_static(self, request, queryset):
        """Admin action: force re-sync *all* ProductsPageCard images from
        media/ → static/images/products_page/ with hash suffixes stripped."""
        try:
            self._sync_ppc_image()
            from django.contrib import messages
            self.message_user(request, 'Products page card images re-synced (media → static, hashes stripped).', messages.SUCCESS)
        except Exception as e:
            from django.contrib import messages
            self.message_user(request, f'Failed to re-sync card images: {e}', messages.ERROR)
    resync_card_images_to_static.short_description = 'Re-sync card images (media → static, strip hashes)'

    def image_preview(self, obj):
        if obj.image and getattr(obj.image, 'name', ''):
            return mark_safe(
                f'<img src="{obj.image.url}" style="width:60px;height:45px;object-fit:contain;'
                f'border:1px solid #ddd;border-radius:4px;background:#f9f9f9;" />'
            )
        return '(no image)'
    image_preview.short_description = 'Image'


def products_page_view(request):
    """Custom admin view: manage the Products listing page cards.

    Shows all ProductsPageCard entries as a card grid so the admin can
    independently edit images, text, and link URLs for each card on the
    public Products page.
    """
    from django.shortcuts import render

    cards_data = []
    for card in ProductsPageCard.objects.all():
        img_url = ''
        if card.image and getattr(card.image, 'name', ''):
            img_url = card.image.url
        cards_data.append({
            'id': card.pk,
            'title': card.title,
            'subtitle': card.subtitle or '',
            'image_url': img_url,
            'slug': card.slug or '',
            'link_url': card.link_url,
            'order': card.order,
            'is_active': card.is_active,
            'edit_url': f'/admin/pages/productspagecard/{card.pk}/change/',
        })

    try:
        site_config = SiteConfig.objects.first()
        page_title = site_config.products_title if site_config else ''
        page_subtitle = site_config.products_subtitle if site_config else ''
    except Exception:
        page_title = ''
        page_subtitle = ''

    context = {
        'title': 'Products Page — Card Management',
        'cards': cards_data,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
        'site_config_edit_url': '/admin/pages/siteconfig/',
        'products_page_url': '/products/',
        'add_card_url': '/admin/pages/productspagecard/add/',
        'site_header': admin.site.site_header,
        'site_title': admin.site.site_title,
    }

    return render(request, 'admin/pages/products_page.html', context)


original_get_urls = admin.site.get_urls


def get_urls_with_products_page():
    urls = original_get_urls()
    custom_urls = [
        url_path(
            'products-page/',
            admin.site.admin_view(products_page_view),
            name='products_page',
        ),
    ]
    return custom_urls + urls


admin.site.get_urls = get_urls_with_products_page