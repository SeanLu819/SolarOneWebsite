from django.db import models


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('MODULAR', 'Modular'),
        ('FLOODLIGHT', 'Floodlight'),
        ('HIGH_BAY', 'High Bay'),
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
    image = models.ImageField(upload_to='products/', blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Project(models.Model):
    title = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    results = models.TextField(blank=True)
    image = models.ImageField(upload_to='projects/', blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


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
    hero_title = models.CharField(max_length=500, default="Precision LED systems for every arena.")
    hero_subtitle = models.TextField(default="Professional sports lighting solutions trusted in over 50 countries. From community fields to broadcast-ready stadiums, engineered for performance, built to outlast.")
    hero_background = models.ImageField(upload_to='site/', blank=True, help_text="Hero background image")

    # Stats
    stat_projects = models.CharField(max_length=100, default="500+")
    stat_projects_label = models.CharField(max_length=100, default="Projects")
    stat_countries = models.CharField(max_length=100, default="50+")
    stat_countries_label = models.CharField(max_length=100, default="Countries")
    stat_energy = models.CharField(max_length=100, default="60%")
    stat_energy_label = models.CharField(max_length=100, default="Energy Save")
    stat_support = models.CharField(max_length=100, default="24/7")
    stat_support_label = models.CharField(max_length=100, default="Support")

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

    # Projects Section
    projects_title = models.CharField(max_length=500, default="Featured Projects")
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
