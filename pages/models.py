from django.db import models
from django.db.models import JSONField
import json
import os
import shutil
import re
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.conf import settings


def project_pdf_upload_path(instance, filename):
    return f'projects/pdfs/{instance.slug}/{filename}'


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('AREA_SITE', 'Area and Site'),
        ('SPORTS_LIGHTING', 'Sports Lighting System'),
        ('FLOODLIGHT', 'Flood Lighting'),
        ('HIGHBAY_LOWBAY', 'Highbay & Low Bay'),
        ('ROADWAY', 'Roadway'),
        ('ACCESSORY', 'Accessory'),
        ('MODULAR', 'Modular'),
        ('OTHER', 'Other'),
    ]

    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    power = models.CharField(max_length=100, blank=True)
    efficacy = models.CharField(max_length=100, blank=True)
    protection = models.CharField(max_length=50, blank=True)
    output = models.CharField(max_length=100, blank=True)
    beam_angle = models.CharField(max_length=100, blank=True)
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        help_text='产品卡片/详情主图。建议 1280×720 像素（16:9，最小 640×360）。'
    )
    banner_image = models.ImageField(
        upload_to='products/banners/',
        blank=True,
        help_text='产品页顶部 banner。建议 1920×442 像素（最小 1200×280）。'
    )
    dimension_image = models.ImageField(
        upload_to='products/dimensions/',
        blank=True,
        help_text='产品尺寸图。建议 1920×800 像素（2.4:1 长条形，最小 960×400），会在详情页规格下方单独展示。'
    )
    beam_angle_image = models.ImageField(
        upload_to='products/beam_angles/',
        blank=True,
        help_text='配光曲线/光束角示意图。建议 1920×540 像素（约 3.56:1 长条形，最小 960×270），会在尺寸图上方展示。'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        verbose_name='父级系列',
        help_text='用于子系列（如 FL1M 属于 M Series）。'
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # JSON translations: {"fr": {"name": "...", "description": "...", "category": "..."}, "es": {...}, ...}
    translations = JSONField(default=dict, blank=True)
    # Flexible specs: list of up to 6 {"label": "...", "value": "..."} dicts.
    # Kept as JSON so admins can enter arbitrary labels/values and render 2 per row.
    specs = JSONField(
        default=list,
        blank=True,
        verbose_name='Product Specs',
        help_text='产品参数，最多 6 组。格式：[{"label": "Power", "value": "80W"}, ...]。页面默认 2 个一排，共 3 排。'
    )
    # Energy & Performance Data: list of {"label": "...", "value": "..."} dicts.
    # Rendered as the ENERGY AND PERFORMANCE DATA table on product detail page.
    energy_data = JSONField(
        default=[
            {"label": "Series Name", "value": "FL1M-80W"},
            {"label": "Lumen Output", "value": ">10,400lm"},
            {"label": "System Wattage", "value": "80W"},
            {"label": "CRI", "value": "70-95"},
            {"label": "Color temperature", "value": "3000K-3500K、4000K-4500k、5500K-5700K"},
            {"label": "Input Voltage (High Voltage)", "value": "347-480VAC"},
            {"label": "Input Voltage (Low Voltage)", "value": "110-277VAC"},
            {"label": "L70 Hours", "value": ">100,000 at 25°C"},
            {"label": "Operating Temperature Range", "value": "-40°C to 55°C"},
            {"label": "Surge (Common Mode / Differential Mode)", "value": "10kV"},
            {"label": "IP Rating", "value": "IP66"},
            {"label": "Effective Projected Area (EPA) at 90°", "value": "0.26 (sq. ft.)"},
            {"label": "L\" X W\" X H\"", "value": "217*234*136mm"},
            {"label": "Approximate Weight", "value": "2.3 kgs( 5.2 lbs)"},
            {"label": "Material", "value": "Aluminum / Glass"},
            {"label": "LED brand", "value": "Bridgelux"},
            {"label": "LED Driver", "value": "Inventronics Or Equal"},
        ],
        blank=True,
        verbose_name='Energy & Performance Data',
        help_text='产品能效参数表，用于详情页 ENERGY AND PERFORMANCE DATA 表格。'
                  '格式：[{"label": "Series Name", "value": "FL4M-320W"}, ...]。'
                  'label 为参数名称，value 为参数值。不填或留空数组则不显示该行。'
    )
    # Ordering Information table
    model_number = models.CharField(
        max_length=200,
        blank=True,
        default="FL1M-80W",
        verbose_name='Model Number',
        help_text='产品型号标识，示例：FL1M-80W-30K-S。新建产品时会自动填充默认值，可按需修改。'
    )
    ordering_info = JSONField(
        default=list,
        blank=True,
        verbose_name='Ordering Information',
        help_text='订购信息表格，9 列，每列支持多行（换行分隔）。'
                  '新建产品时自动填充通用默认值，大部分列（如 CCT、电压、颜色、控制方式、支架等）可直接复用，'
                  '只需修改 Series Name 和 Power 即可快速完成。'
    )
    ordering_image = models.ImageField(
        upload_to='products/ordering/',
        blank=True,
        verbose_name='Ordering Information Image',
        help_text='订购信息示意图，展示在 ORDERING INFORMATION 表格上方。建议 1920×600 像素。'
    )

    class Meta:
        ordering = ['order', 'pk']

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} › {self.name}"
        return self.name

    def t(self, field_name, lang='en'):
        """Get translated value for a field, falling back to the default English value."""
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')


class NewsArticle(models.Model):
    title = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    summary = models.TextField(blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to='news/', blank=True)
    published_at = models.DateTimeField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='产品'
    )
    image = models.ImageField(
        upload_to='products/gallery/',
        help_text='轮播图。建议 1280×720 像素（16:9，最小 640×360）。'
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='Alt 文本')
    order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = '产品轮播图'
        verbose_name_plural = '产品轮播图'

    def __str__(self):
        return f"{self.product.name} — {self.alt_text or self.image.name}"


class Project(models.Model):
    VENUE_TYPE_CHOICES = [
        ('OUTDOOR', 'Outdoor'),
        ('INDOOR', 'Indoor'),
        ('INFRASTRUCTURE', 'Infrastructure'),
    ]

    SPORT_TYPE_CHOICES = [
        ('FOOTBALL_FIELD', 'Football Field'),
        ('SOCCER_FIELD', 'Soccer Field'),
        ('BASEBALL_FIELD', 'Baseball Field'),
        ('TENNIS_COURTS', 'Tennis Courts'),
        ('SKI_AREA', 'Ski Area'),
        ('BASKETBALL', 'Basketball'),
        ('VELODROME', 'Velodrome'),
        ('TENNIS', 'Tennis'),
        ('TRACK_FIELD', 'Track and Field'),
        ('MULTI_SPORT', 'Multi-Sport Arena'),
        ('AIRPORT', 'Airport'),
        ('SEAPORT', 'Seaport'),
        ('ICE_ARENA', 'Ice Arena'),
        ('OTHER', 'Other'),
    ]

    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPE_CHOICES, default='OUTDOOR')
    sport_type = models.CharField(max_length=50, choices=SPORT_TYPE_CHOICES, default='OTHER')
    description = models.TextField()
    results = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='projects/',
        blank=True,
        help_text='Reference card cover image. Recommended 1280×720 px (16:9, min 640×360).'
    )
    pdf_file = models.FileField(
        upload_to=project_pdf_upload_path,
        blank=True,
        help_text='Optional PDF document for download (e.g. project case study, specification sheet).'
    )
    pdf_static = models.CharField(
        max_length=255,
        blank=True,
        help_text='Static PDF path relative to /static/ (e.g. "files/project-case-study.pdf"). Used as persistent fallback on Vercel where uploaded files are ephemeral.'
    )
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    # JSON translations: {"fr": {"title": "...", "description": "...", "location": "...", "results": "..."}, ...}
    translations = JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'

    def __str__(self):
        return self.title

    def t(self, field_name, lang='en'):
        """Get translated value for a field, falling back to the default English value."""
        if lang == 'en' or not self.translations:
            return getattr(self, field_name, '')
        lang_data = self.translations.get(lang, {})
        val = lang_data.get(field_name, '')
        return val if val else getattr(self, field_name, '')


class ProjectImage(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Reference'
    )
    image = models.ImageField(
        upload_to='projects/gallery/',
        help_text='Reference detail carousel image. Recommended 1280×720 px (16:9, min 640×360).'
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='Alt text')
    order = models.IntegerField(default=0, verbose_name='Order')

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Project image'
        verbose_name_plural = 'Project images'

    def __str__(self):
        return f"{self.project.title} — {self.alt_text or self.image.name}"


class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject or 'No Subject'}"


class SiteConfig(models.Model):
    """Singleton model for all site-wide editable content"""
    # Hero Section
    hero_title = models.CharField(max_length=500, default="The Next Generation Lighting Systems For Every Area")
    hero_subtitle = models.TextField(default="Professional SolarOne sports lighting solutions trusted in over 50 countries. From community fields to broadcast-ready stadiums, engineered for performance, built to outlast.")
    hero_background = models.ImageField(upload_to='site/', blank=True, help_text="Hero background image")

    # Stats
    stat_projects = models.CharField(max_length=100, default="500+")
    stat_projects_label = models.CharField(max_length=100, default="Projects")
    stat_countries = models.CharField(max_length=100, default="50+")
    stat_countries_label = models.CharField(max_length=100, default="Countries")
    stat_energy = models.CharField(max_length=100, default="50%+")
    stat_energy_label = models.CharField(max_length=100, default="Energy Save")
    stat_support = models.CharField(max_length=100, default="5+")
    stat_support_label = models.CharField(max_length=100, default="warranty")

    # About Section
    about_title = models.CharField(max_length=500, default="Trusted worldwide for a reason.")
    about_text_1 = models.TextField(default="Since 2007, SolarOne Vision has focused on the design and manufacture of high power LED Sports lighting systems, LED Roadway infrastructure lighting systems, and LED industrial lighting systems. We bring first-hand knowledge and experience for new and retrofit projects — from small projects requiring a few lights to professional high-level facilities, we've got you covered.")
    about_text_2 = models.TextField(default="SolarOne's mission is to deliver innovative outdoor and indoor lighting solutions for recreational, high school, college, and semi-professional sports venues, airports, seaports, and other industrial facilities. We protect the environment, reduce energy consumption, deliver satisfying and inspiring lighting experiences, and add value to people's vision of life.")
    about_stat_years = models.CharField(max_length=100, default="18+")
    about_stat_years_label = models.CharField(max_length=100, default="Years Experience")
    about_stat_projects = models.CharField(max_length=100, default="500+")
    about_stat_projects_label = models.CharField(max_length=100, default="Projects Delivered")
    about_stat_countries = models.CharField(max_length=100, default="50+")
    about_stat_countries_label = models.CharField(max_length=100, default="Countries Served")
    about_stat_clients = models.CharField(max_length=100, default="1000+")
    about_stat_clients_label = models.CharField(max_length=100, default="Happy Clients")

    # Products Section
    products_title = models.CharField(max_length=500, default="Our Products")
    products_subtitle = models.TextField(default="From compact modular luminaires to stadium-grade high bay systems. Precision optics, modular architecture, and field-proven reliability across every product line.")

    # References Section
    projects_title = models.CharField(max_length=500, default="Featured References")
    projects_subtitle = models.TextField(default="Real installations across five continents. From Olympic training centers to community football pitches, our luminaires deliver reliable performance under the toughest conditions.")

    # Contact Section
    contact_title = models.CharField(max_length=500, default="Get in Touch")
    contact_subtitle = models.TextField(default="Have a project in mind? Send us the details and our engineering team will respond with a full photometric proposal within 48 hours.")
    contact_email = models.EmailField(default="sales@solarone.com")
    contact_phone_1 = models.CharField(max_length=200, default="+8613910887405")
    contact_phone_2 = models.CharField(max_length=200, default="+8613910887405")
    contact_whatsapp = models.CharField(max_length=200, default="+86 13910887405")
    contact_address = models.CharField(max_length=500, default="Beijing, China")

    # Social Media
    social_facebook = models.URLField(blank=True, default="https://facebook.com")
    social_instagram = models.URLField(blank=True, default="https://instagram.com")
    social_youtube = models.URLField(blank=True, default="https://youtube.com")
    social_tiktok = models.URLField(blank=True, default="https://tiktok.com")
    social_linkedin = models.URLField(blank=True, default="")

    # Footer
    footer_description = models.TextField(default="Professional LED lighting systems for sports, industrial, and infrastructure applications. Engineered in Beijing since 2007, trusted in 50+ countries worldwide.")

    # Brand / Logo
    brand_name = models.CharField(max_length=200, default="SolarOne")
    logo = models.ImageField(upload_to='site/', blank=True, help_text="Brand logo")

    # Meta
    meta_title = models.CharField(max_length=200, default="SolarOne — Precision LED Lighting Systems")
    meta_description = models.TextField(default="Professional LED sports lighting, high bay, and modular luminaire solutions. Engineered in Beijing since 2007, trusted in 50+ countries worldwide.")

    # SEO / Open Graph
    og_image = models.ImageField(upload_to='site/', blank=True, help_text="Social sharing preview image")

    # Typography
    font_family_body = models.CharField(
        max_length=200, 
        default="'Inter', 'Helvetica Neue', Arial, sans-serif",
        verbose_name="Body Font Family",
        help_text="CSS font-family value, e.g. 'Inter', sans-serif"
    )
    font_family_heading = models.CharField(
        max_length=200,
        default="'Inter', 'Helvetica Neue', Arial, sans-serif",
        verbose_name="Heading Font Family",
        help_text="CSS font-family value for headings"
    )
    font_size_base = models.CharField(
        max_length=10,
        default="16px",
        verbose_name="Base Font Size",
        help_text="Root font size, e.g. 16px, 18px"
    )
    font_size_nav = models.CharField(
        max_length=10,
        default="17px",
        verbose_name="Navigation Font Size",
        help_text="Nav link font size, e.g. 15px, 17px, 18px"
    )
    font_size_hero_title = models.CharField(
        max_length=10,
        default="3.5rem",
        verbose_name="Hero Title Font Size",
        help_text="Hero heading size, e.g. 3.5rem, 4rem"
    )
    font_size_hero_subtitle = models.CharField(
        max_length=10,
        default="1.15rem",
        verbose_name="Hero Subtitle Font Size",
        help_text="Hero subtitle size, e.g. 1.15rem, 1.25rem"
    )
    font_size_section_title = models.CharField(
        max_length=10,
        default="2.25rem",
        verbose_name="Section Title Font Size",
        help_text="Section headings size, e.g. 2.25rem, 2.5rem"
    )
    font_size_body = models.CharField(
        max_length=10,
        default="1.05rem",
        verbose_name="Body Text Font Size",
        help_text="Paragraph text size, e.g. 1.05rem, 1.1rem"
    )
    font_size_card_title = models.CharField(
        max_length=10,
        default="1.25rem",
        verbose_name="Card Title Font Size",
        help_text="Product/Project card title size"
    )
    font_size_card_desc = models.CharField(
        max_length=10,
        default="0.95rem",
        verbose_name="Card Description Font Size",
        help_text="Product/Project card description size"
    )
    accent_color = models.CharField(
        max_length=20,
        default="#0088FF",
        verbose_name="Accent Color",
        help_text="Primary accent color, e.g. #0088FF, #FF6B00"
    )

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Site Configuration"

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteConfig.objects.exists():
            raise ValueError("Only one SiteConfig instance is allowed. Edit the existing one instead.")
        super().save(*args, **kwargs)


class Visitor(models.Model):
    ip_address = models.GenericIPAddressField(verbose_name="IP Address")
    path = models.CharField(max_length=500, blank=True, default="/")
    referrer = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)
    browser = models.CharField(max_length=100, blank=True)
    browser_version = models.CharField(max_length=50, blank=True)
    os = models.CharField(max_length=100, blank=True)
    device = models.CharField(max_length=50, blank=True, default="Unknown")
    country = models.CharField(max_length=100, blank=True, default="Unknown")
    city = models.CharField(max_length=100, blank=True, default="Unknown")
    session_key = models.CharField(max_length=100, blank=True)
    is_unique = models.BooleanField(default=True, help_text="First visit from this IP today")
    visited_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-visited_at']
        verbose_name = "Visitor"
        verbose_name_plural = "Visitor Records"

    def __str__(self):
        return f"{self.ip_address} - {self.visited_at.strftime('%Y-%m-%d %H:%M')}"


class DailyStats(models.Model):
    date = models.DateField(unique=True, db_index=True)
    total_visits = models.IntegerField(default=0)
    unique_visits = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date']
        verbose_name = "Daily Stat"
        verbose_name_plural = "Daily Statistics"

    def __str__(self):
        return str(self.date)


def _sync_project_media_to_static(project):
    """Copy project cover + all gallery images from media/ to static/images/projects/<slug>/.

    Also PRUNES stale files from the static directory: any image in
    static/images/projects/<slug>/ that is no longer referenced by the
    current DB state is deleted. This prevents the carousel from growing
    indefinitely when images are replaced or deleted in the admin.

    Returns (cover_rel_path, gallery_rel_paths) relative to static/.
    """
    if not project or not getattr(project, 'slug', None):
        return '', []
    slug = project.slug
    media_root = str(settings.MEDIA_ROOT)
    static_dir = os.path.join(str(settings.BASE_DIR), 'static', 'images', 'projects', slug)
    os.makedirs(static_dir, exist_ok=True)

    def _dest_name(src_path):
        """Stable destination filename: strip Django hash suffix so repeated
        uploads of the same file don't produce divergent static paths."""
        base = os.path.basename(src_path)
        stem, ext = os.path.splitext(base)
        parts = stem.rsplit('_', 1)
        if len(parts) == 2 and len(parts[1]) > 0 and any(c.isdigit() for c in parts[1]):
            return f'{parts[0]}{ext}'
        return base

    # ---- Collect current destination filenames from DB ----
    current_dest_names = set()

    cover_rel = ''
    if getattr(project, 'image', None) and project.image.name:
        src_cover = os.path.join(media_root, str(project.image.name))
        if os.path.exists(src_cover):
            dst_name = _dest_name(src_cover)
            current_dest_names.add(dst_name)
            dst_cover = os.path.join(static_dir, dst_name)
            try:
                shutil.copy2(src_cover, dst_cover)
            except Exception:
                pass
            cover_rel = f'images/projects/{slug}/{dst_name}'

    gallery_paths = []
    try:
        images_qs = project.images.all()
    except Exception:
        images_qs = []
    for img in images_qs:
        fname = getattr(img.image, 'name', None)
        if not fname:
            continue
        src = os.path.join(media_root, str(fname))
        if not os.path.exists(src):
            continue
        dst_name = _dest_name(src)
        current_dest_names.add(dst_name)
        dst = os.path.join(static_dir, dst_name)
        try:
            shutil.copy2(src, dst)
        except Exception:
            pass
        rel = f'images/projects/{slug}/{dst_name}'
        if rel not in gallery_paths:
            gallery_paths.append(rel)

    # ---- Prune stale files from static directory ----
    try:
        for entry in os.listdir(static_dir):
            entry_lower = entry.lower()
            if not entry_lower.endswith(('.webp', '.jpg', '.jpeg', '.png', '.gif')):
                continue
            if entry not in current_dest_names:
                stale_path = os.path.join(static_dir, entry)
                try:
                    os.remove(stale_path)
                except Exception:
                    pass
    except Exception:
        pass

    return cover_rel, gallery_paths


def _rewrite_seed_project(slug, cover_rel, gallery_paths):
    """Rewrite seed_data.json + pages/seed_data.py with current project image/gallery.

    Gallery is REPLACED (not merged) with the current DB state — the database
    is the source of truth. Old images removed from the admin are also removed
    from seed to prevent accumulation of stale files in the carousel.
    """
    seed_path = os.path.join(str(settings.BASE_DIR), 'seed_data.json')
    seed_py_path = os.path.join(str(settings.BASE_DIR), 'pages', 'seed_data.py')

    changed = False
    try:
        with open(seed_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for p in data.get('projects', []):
            if p.get('slug') == slug:
                if cover_rel and p.get('image') != cover_rel:
                    p['image'] = cover_rel
                    changed = True
                gal = list(p.get('gallery', []) or [])
                new_gal = list(gallery_paths)
                if new_gal != gal:
                    p['gallery'] = new_gal
                    changed = True
                break
        if changed:
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
            new_content = content
            if cover_rel:
                img_match = re.search(r'"image":\s*"([^"]*)"', new_content[idx:])
                if img_match:
                    i_start = img_match.start() + idx
                    val_start = new_content.find('"', i_start) + 1
                    val_end = new_content.find('"', val_start)
                    if new_content[val_start:val_end] != cover_rel:
                        new_content = new_content[:val_start] + cover_rel + new_content[val_end:]
            gal_match = re.search(r'"gallery":\s*\[[^\]]*\]', new_content[idx:])
            if gal_match:
                g_start = gal_match.start() + idx
                g_end = gal_match.end()
                existing = gal_match.group(0)
                new_block = '"gallery": ' + json.dumps(gallery_paths)
                if new_block != existing:
                    new_content = new_content[:g_start] + new_block + new_content[g_end:]
            if new_content != content:
                with open(seed_py_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
    except Exception:
        pass


@receiver(post_save, sender=Project)
def sync_project_on_save(sender, instance, **kwargs):
    cover_rel, gallery_rel = _sync_project_media_to_static(instance)
    _rewrite_seed_project(instance.slug, cover_rel, gallery_rel)


@receiver(post_save, sender=ProjectImage)
def sync_project_image_on_save(sender, instance, **kwargs):
    project = getattr(instance, 'project', None)
    if not project:
        return
    cover_rel, gallery_rel = _sync_project_media_to_static(project)
    _rewrite_seed_project(project.slug, cover_rel, gallery_rel)


@receiver(post_delete, sender=ProjectImage)
def sync_project_image_on_delete(sender, instance, **kwargs):
    project = getattr(instance, 'project', None)
    if not project:
        return
    cover_rel, gallery_rel = _sync_project_media_to_static(project)
    _rewrite_seed_project(project.slug, cover_rel, gallery_rel)


# Legacy helper retained for external callers.
def _update_seed_project(project):
    cover_rel, gallery_rel = _sync_project_media_to_static(project)
    _rewrite_seed_project(getattr(project, 'slug', ''), cover_rel, gallery_rel)


@receiver(post_save, sender=Product)
def sync_product_on_save(sender, instance, **kwargs):
    if not getattr(instance, 'slug', None):
        return
    slug = instance.slug
    media_root = str(settings.MEDIA_ROOT)
    static_dir = os.path.join(str(settings.BASE_DIR), 'static', 'images', 'products', slug)
    os.makedirs(static_dir, exist_ok=True)

    def _copy_to(field_attr):
        field = getattr(instance, field_attr, None)
        fname = getattr(field, 'name', None)
        if not fname:
            return None
        src = os.path.join(media_root, str(fname))
        if not os.path.exists(src):
            return None
        dst = os.path.join(static_dir, os.path.basename(fname))
        try:
            shutil.copy2(src, dst)
        except Exception:
            pass
        return f'images/products/{slug}/{os.path.basename(fname)}'

    for attr in ('image', 'banner_image', 'dimension_image', 'beam_angle_image'):
        _copy_to(attr)

    try:
        for pimg in instance.images.all():
            fname = getattr(pimg.image, 'name', None)
            if not fname:
                continue
            src = os.path.join(media_root, str(fname))
            if not os.path.exists(src):
                continue
            dst = os.path.join(static_dir, os.path.basename(fname))
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass
    except Exception:
        pass


@receiver(post_save, sender=ProductImage)
def sync_product_image_on_save(sender, instance, **kwargs):
    product = getattr(instance, 'product', None)
    if product:
        sync_product_on_save(type(product), product)