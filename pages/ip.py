"""Client IP resolution (B4 / v1.6.x).

A single shared implementation of X-Forwarded-For handling so the contact
rate-limit and the visitor-tracking middleware no longer each hand-roll the
split. Returns a tuple ``(ip, is_routable)`` where ``ip`` is the resolved
address (``None`` when neither header is present) — call sites only consume
``ip``.

Behaviour is identical to the previous inline parsing: take the first hop of
``HTTP_X_FORWARDED_FOR`` (comma-separated; the left-most entry is the original
client), otherwise fall back to ``REMOTE_ADDR``.

NOTE: the v1.6.x B4 spec asked to route these call sites through Django's
built-in ``django.utils.http.get_client_ip``. That symbol does **not** exist
in the installed Django 6.0.7 (verified — ``dir(django.utils.http)`` and a
full-package grep for ``def get_client_ip`` / ``HTTP_X_FORWARDED_FOR`` both
come back empty), so importing it would raise ``ImportError`` and take the
whole app down. This module is the consolidation point instead; it is a
behaviour-equivalent stand-in, so swapping to Django's built-in later (if a
Django release adds it) is a one-line import change in the two call sites.
"""


def get_client_ip(request):
    """Return ``(ip, is_routable)`` for *request*.

    ``ip`` is the client address resolved from X-Forwarded-For (first hop) or
    ``REMOTE_ADDR``. ``is_routable`` is ``None`` here (unused by call sites);
    kept for signature parity with the documented Django helper.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip, None
