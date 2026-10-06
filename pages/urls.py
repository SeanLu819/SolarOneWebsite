from django.urls import path
from django.views.generic import RedirectView
from django.conf import settings
from pages import views
from pages.redirects import legacy_path_entries

# S2: retired routes 301 to their replacement. These come FIRST on purpose —
# a catch-all like `products/<slug:slug>/` would otherwise match the legacy
# path and the redirect would never run. Empty table today: adding an entry to
# LEGACY_PATH_REDIRECTS is all it takes to register one.
_legacy_redirects = [
    path(route, RedirectView.as_view(pattern_name=name, permanent=True))
    for route, name in legacy_path_entries()
]

urlpatterns = _legacy_redirects + [
    path('', views.home, name='home'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    # IndexNow key file (Bing/Yandex). The route name is derived from the key so
    # rotating the key auto-rotates the URL; no slug route can shadow it because
    # it sits at the site root with a .txt suffix.
    path(settings.INDEXNOW_KEY_FILE, views.indexnow_key, name='indexnow_key'),
    path('news/', views.news, name='news'),
    path('news/feed.xml', views.news_feed, name='news_feed'),
    path('news/<slug:slug>/', views.news_detail, name='news_detail'),
    path('products/', views.products, name='products'),
    # v1.10.23 (P4-A): the generic stadium-lighting term. Registered before
    # ``products/<slug:slug>/``? Not strictly necessary — the path has
    # no ``products/`` prefix — but it MUST sit before nothing and
    # AFTER ``products/series/...``. Kept next to the product routes so the
    # reason it exists is visible to whoever next reorders this list.
    path('stadium-lighting/', views.stadium_lighting, name='stadium_lighting'),
    path('products/series/<slug:slug>/', views.product_series, name='product_series'),
    path('products/<slug:slug>/', views.product_detail, name='product_detail'),
    path('projects/', views.projects, name='projects'),
    # Static collection pages MUST precede `projects/<slug:slug>/` — the slug
    # converter matches "football" too, so placing them after it would hand
    # /projects/football/ to project_detail() and 404.
    path('projects/football/', views.projects_football, name='projects_football'),
    path('projects/tennis/', views.projects_tennis, name='projects_tennis'),
    path('projects/<slug:slug>/', views.project_detail, name='project_detail'),
    path('about/', views.about, name='about'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),
    path('contact/', views.contact, name='contact'),
]

# Diagnostic endpoint is ONLY available when DEBUG=True (never in production).
# It is also staff-only via @staff_member_required on the view itself.
if settings.DEBUG:
    urlpatterns.insert(0, path('__diag__/', views.diagnostic, name='diagnostic'))
