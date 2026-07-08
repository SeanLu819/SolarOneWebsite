from django.shortcuts import render
from django.contrib import messages
from pages.models import Product, Project, ContactMessage, SiteConfig


def home(request):
    products = Product.objects.all()
    projects = Project.objects.all()
    site_config = SiteConfig.objects.first()
    if not site_config:
        site_config = SiteConfig.objects.create()

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
