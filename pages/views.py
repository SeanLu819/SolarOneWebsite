from django.shortcuts import render
from django.contrib import messages
from django.templatetags.static import static
from pages.models import Product, Project, SiteConfig, ContactMessage


def get_common_context():
    """Get context shared across all pages"""
    site_config = SiteConfig.objects.first()
    if not site_config:
        site_config = SiteConfig.objects.create()

    # Pre-compute static URLs for hero bg and logo
    if site_config.hero_background:
        site_config.hero_bg_url = static(site_config.hero_background.name)
    else:
        site_config.hero_bg_url = static('images/hero-main.fw.png')

    if site_config.logo:
        site_config.logo_url = static(site_config.logo.name)
    else:
        site_config.logo_url = static('images/logo.png')

    return {'config': site_config}


def home(request):
    return render(request, 'home.html', get_common_context())


def contact(request):
    context = get_common_context()

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

    return render(request, 'contact.html', context)


def products(request):
    context = get_common_context()
    products_list = Product.objects.all()
    for p in products_list:
        if p.image:
            p.image_url = static(p.image.name)
        else:
            p.image_url = ''
    context['products'] = products_list
    return render(request, 'products.html', context)


def projects(request):
    context = get_common_context()
    projects_list = Project.objects.all()
    for proj in projects_list:
        if proj.image:
            proj.image_url = static(proj.image.name)
        else:
            proj.image_url = ''
    context['projects'] = projects_list
    return render(request, 'projects.html', context)


def about(request):
    context = get_common_context()
    return render(request, 'about.html', context)
