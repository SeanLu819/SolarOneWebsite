"""
Sync database data to seed_data.py and seed_data.json.
Called automatically when saving Product or Project in Django admin.
"""
import json
import os
from pathlib import Path
from django.conf import settings


def _clean_image_path(path):
    """Clean image path: remove hash suffix, ensure correct format."""
    if not path:
        return ''
    # Remove Django upload hash suffix like _yPJsGNE
    if '_' in path:
        base, ext = os.path.splitext(path)
        if '_' in base:
            base = base.rsplit('_', 1)[0]
            path = f'{base}{ext}'
    # Ensure path starts with 'images/' for static files
    if path.startswith('products/'):
        path = f'images/{path}'
    elif path.startswith('processed/'):
        path = f'images/{path}'
    return path


def _build_product_data(product):
    """Build product dict from Product model instance."""
    # Clean image paths
    image = _clean_image_path(product.image.name if product.image else '')
    banner_image = _clean_image_path(product.banner_image.name if product.banner_image else '')
    dimension_image = _clean_image_path(product.dimension_image.name if product.dimension_image else '')
    beam_angle_image = _clean_image_path(product.beam_angle_image.name if product.beam_angle_image else '')
    
    # Build gallery paths
    gallery = []
    for img in product.images.all().order_by('order'):
        gallery.append(_clean_image_path(img.image.name if img.image else ''))
    
    # Build specs
    specs = product.specs if isinstance(product.specs, list) else []
    
    # Build energy_data
    energy_data = product.energy_data if isinstance(product.energy_data, list) else []
    
    # Build translations
    translations = product.translations if isinstance(product.translations, dict) else {}
    
    return {
        'pk': product.pk,
        'name': product.name,
        'slug': product.slug,
        'category': product.category,
        'description': product.description,
        'power': product.power,
        'efficacy': product.efficacy,
        'output': product.output,
        'beam_angle': product.beam_angle,
        'protection': product.protection,
        'image': image,
        'banner_image': banner_image,
        'dimension_image': dimension_image,
        'beam_angle_image': beam_angle_image,
        'order': product.order,
        'parent_slug': product.parent.slug if product.parent else '',
        'translations': translations,
        'gallery': gallery,
        'specs': specs,
        'energy_data': energy_data,
    }


def _build_project_data(project):
    """Build project dict from Project model instance."""
    # Clean image path
    image = _clean_image_path(project.image.name if project.image else '')
    
    # Build gallery paths
    gallery = []
    for img in project.images.all().order_by('order'):
        gallery.append(_clean_image_path(img.image.name if img.image else ''))
    
    # Build translations
    translations = project.translations if isinstance(project.translations, dict) else {}
    
    # Build PDF URL
    pdf_url = ''
    if project.pdf_file:
        pdf_url = project.pdf_file.name
    elif project.pdf_static:
        pdf_url = project.pdf_static
    
    return {
        'pk': project.pk,
        'title': project.title,
        'location': project.location,
        'slug': project.slug,
        'venue_type': project.venue_type,
        'sport_type': project.sport_type,
        'description': project.description,
        'results': project.results,
        'image': image,
        'order': project.order,
        'translations': translations,
        'gallery': gallery,
        'pdf_url': pdf_url,
    }


def _build_siteconfig_data(siteconfig):
    """Build siteconfig dict from SiteConfig model instance."""
    return {
        'brand_name': siteconfig.brand_name,
        'logo': _clean_image_path(siteconfig.logo.name if siteconfig.logo else ''),
        'meta_title': siteconfig.meta_title,
        'meta_description': siteconfig.meta_description,
        'og_image': _clean_image_path(siteconfig.og_image.name if siteconfig.og_image else ''),
        'hero_title': siteconfig.hero_title,
        'hero_subtitle': siteconfig.hero_subtitle,
        'hero_background': _clean_image_path(siteconfig.hero_background.name if siteconfig.hero_background else ''),
        'stat_projects': siteconfig.stat_projects,
        'stat_projects_label': siteconfig.stat_projects_label,
        'stat_countries': siteconfig.stat_countries,
        'stat_countries_label': siteconfig.stat_countries_label,
        'stat_energy': siteconfig.stat_energy,
        'stat_energy_label': siteconfig.stat_energy_label,
        'stat_support': siteconfig.stat_support,
        'stat_support_label': siteconfig.stat_support_label,
        'products_title': siteconfig.products_title,
        'products_subtitle': siteconfig.products_subtitle,
        'projects_title': siteconfig.projects_title,
        'projects_subtitle': siteconfig.projects_subtitle,
        'about_title': siteconfig.about_title,
        'about_text_1': siteconfig.about_text_1,
        'about_text_2': siteconfig.about_text_2,
        'about_stat_years': siteconfig.about_stat_years,
        'about_stat_years_label': siteconfig.about_stat_years_label,
        'about_stat_projects': siteconfig.about_stat_projects,
        'about_stat_projects_label': siteconfig.about_stat_projects_label,
        'about_stat_countries': siteconfig.about_stat_countries,
        'about_stat_countries_label': siteconfig.about_stat_countries_label,
        'about_stat_clients': siteconfig.about_stat_clients,
        'about_stat_clients_label': siteconfig.about_stat_clients_label,
        'contact_title': siteconfig.contact_title,
        'contact_subtitle': siteconfig.contact_subtitle,
        'contact_email': siteconfig.contact_email,
        'contact_phone_1': siteconfig.contact_phone_1,
        'contact_phone_2': siteconfig.contact_phone_2,
        'contact_whatsapp': siteconfig.contact_whatsapp,
        'contact_address': siteconfig.contact_address,
        'social_facebook': siteconfig.social_facebook,
        'social_instagram': siteconfig.social_instagram,
        'social_youtube': siteconfig.social_youtube,
        'social_tiktok': siteconfig.social_tiktok,
        'social_linkedin': siteconfig.social_linkedin,
        'footer_description': siteconfig.footer_description,
    }


def sync_seed_data():
    """
    Sync all data from database to seed_data.py and seed_data.json.
    Returns True on success, False on failure.
    """
    try:
        from pages.models import Product, Project, SiteConfig
        
        # Build products list
        products = []
        for product in Product.objects.all().order_by('order'):
            products.append(_build_product_data(product))
        
        # Build projects list
        projects = []
        for project in Project.objects.all().order_by('order'):
            projects.append(_build_project_data(project))
        
        # Build siteconfig
        siteconfig = {}
        try:
            sc = SiteConfig.objects.first()
            if sc:
                siteconfig = _build_siteconfig_data(sc)
        except Exception:
            pass
        
        # Build seed data dict
        seed_data = {
            'products': products,
            'projects': projects,
            'siteconfig': siteconfig,
        }
        
        # Write to seed_data.json
        json_path = os.path.join(settings.BASE_DIR, 'seed_data.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(seed_data, f, ensure_ascii=False, indent=2)
        
        # Write to seed_data.py
        py_path = os.path.join(settings.BASE_DIR, 'pages', 'seed_data.py')
        with open(py_path, 'w', encoding='utf-8') as f:
            f.write('"""Seed data embedded as Python module for Vercel compatibility.\n')
            f.write('\n')
            f.write('On Vercel, non-Python files (like seed_data.json) are not automatically included\n')
            f.write('in the serverless function bundle. Embedding the data here ensures it is always\n')
            f.write('available via a normal Python import.\n')
            f.write('"""\n\n')
            f.write('SEED_DATA = ')
            f.write(json.dumps(seed_data, ensure_ascii=False, indent=2))
            f.write('\n')
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Failed to sync seed data: {e}', exc_info=True)
        return False
