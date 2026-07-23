from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

# Use prefix_default_language=False so only non-default languages get a prefix
# Default language (en) uses unprefixed URLs: /products/
# Other languages use prefixed URLs: /fr/products/, /es/products/, etc.
urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
