from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve
from pages.admin import admin_translate

urlpatterns = i18n_patterns(
    path('admin/translate/', admin_translate, name='admin_translate'),
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    prefix_default_language=False,
)

# Always serve media via Django if WhiteNoise/direct static misses.
# On Vercel this path will rarely be hit (WhiteNoise handles it), but it
# guarantees local consistency whether DEBUG is True or False.
import os
_media_roots = [str(settings.MEDIA_ROOT)]
_shadow = os.path.join(str(settings.BASE_DIR), 'static', 'media')
if _shadow not in _media_roots:
    _media_roots.append(_shadow)
for _mr in _media_roots:
    if os.path.isdir(_mr):
        urlpatterns += [
            re_path(r'^media/(?P<path>.*)$', serve, {'document_root': _mr}),
        ]
        break

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)