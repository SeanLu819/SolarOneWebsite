from django.shortcuts import render
from django.contrib import messages
from django.templatetags.static import static
from pages.models import Product, Project, ContactMessage, SiteConfig


def home(request):
    products = Product.objects.all()
    projects = Project.objects.all()
    site_config = SiteConfig.objects.first()
    if not site_config:
        site_config = SiteConfig.objects.create()

    # Pre-compute static URLs for all ImageField references so they work
    # on Vercel (ephemeral filesystem) where MEDIA files are unavailable.
    for p in products:
        if p.image:
            p.image_url = static(p.image.name)
        else:
            p.image_url = ''

    for proj in projects:
        if proj.image:
            proj.image_url = static(proj.image.name)
        else:
            proj.image_url = ''

    if site_config.hero_background:
        site_config.hero_bg_url = static(site_config.hero_background.name)
    else:
        site_config.hero_bg_url = static('images/hero-main.fw.png')

    if site_config.logo:
        site_config.logo_url = static(site_config.logo.name)
    else:
        site_config.logo_url = static('images/logo.png')

    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message', '')
        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                message=message
            )
            messages.success(request, 'Your message has been sent successfully!')

    context = {
        'products': products,
        'projects': projects,
        'config': site_config,
    }
    return render(request, 'home.html', context)
