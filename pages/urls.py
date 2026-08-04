from django.urls import path
from pages import views

urlpatterns = [
    path('', views.home, name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('news/', views.news, name='news'),
    path('products/', views.products, name='products'),
    path('products/series/<slug:slug>/', views.product_series, name='product_series'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('references/', views.projects, name='references'),
    path('references/<slug:slug>/', views.project_detail, name='reference_detail'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
