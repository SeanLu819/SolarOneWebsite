from django.urls import path
from pages import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('products/series/<slug:slug>/', views.product_series, name='product_series'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('projects/', views.projects, name='projects'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
]
