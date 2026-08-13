from django.urls import path
from pages import views

urlpatterns = [
    path('__diag__/', views.diagnostic, name='diagnostic'),
    path('', views.home, name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('news/', views.news, name='news'),
    path('products/', views.products, name='products'),
    path('products/series/<slug:slug>/', views.product_series, name='product_series'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('projects/', views.projects, name='projects'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]