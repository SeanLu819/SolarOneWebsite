"""Context processors: project-wide template context additions."""
from django.conf import settings


def canonical_origin(request):
    """Expose the fixed canonical origin (#17) to all templates.

    Templates must build canonical/SEO URLs from this instead of
    request.get_host() so preview/spoofed hosts can't poison SEO URLs.
    """
    return {'canonical_origin': settings.CANONICAL_ORIGIN}
