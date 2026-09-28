import datetime as _dt
import hashlib
import os
import secrets
import zoneinfo
import user_agents
from django.conf import settings
from django.utils import timezone
from pages.ip import get_client_ip as django_get_client_ip
from .models import Visitor, DailyStats


def _site_day_bounds_utc(day):
    """Return (start, end) UTC datetimes covering ``day`` in the site timezone.

    SQLite evaluates ``__date`` in UTC, so comparing it against a
    site-local date gives the wrong answer for part of every day. Building the
    range explicitly keeps "today" defined by ``settings.TIME_ZONE`` while the
    comparison itself stays in UTC.
    """
    try:
        tz = zoneinfo.ZoneInfo(getattr(settings, 'TIME_ZONE', 'UTC') or 'UTC')
    except Exception:  # unknown/empty timezone → fall back to UTC semantics
        tz = _dt.timezone.utc
    start = _dt.datetime.combine(day, _dt.time.min, tzinfo=tz)
    end = start + _dt.timedelta(days=1)
    return start.astimezone(_dt.timezone.utc), end.astimezone(_dt.timezone.utc)


def _hash_ip(ip):
    """Return a deterministic salted hash of an IP address (#16/GDPR).

    Unique-visit counting only needs equality, never the IP itself, so we
    store a SECRET_KEY-peppered SHA-256 hash instead of the plaintext IP.
    """
    pepper = settings.SECRET_KEY.encode('utf-8')
    return hashlib.sha256(pepper + ip.encode('utf-8', 'replace')).hexdigest()


class VisitorTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Preview/test mode: skip DB write entirely (set by scripts/dev_preview.py
        # and the test suite). Lets the site serve read-only when the dev box can't
        # commit to sqlite — without touching real analytics in production.
        if os.environ.get('DJANGO_DISABLE_VISITOR_TRACKING'):
            return response

        # Skip admin, static, media requests
        if request.path.startswith('/admin/') or request.path.startswith('/static/') or request.path.startswith('/media/'):
            return response
        
        # Only track GET requests
        if request.method != 'GET':
            return response
        
        try:
            raw_ip = self.get_client_ip(request)
            # Store only a salted hash — never the plaintext IP (#16/GDPR)
            ip = _hash_ip(raw_ip)
            ua_string = request.META.get('HTTP_USER_AGENT', '')
            
            # Parse user agent
            ua = user_agents.parse(ua_string)
            browser_family = ua.browser.family if ua.browser.family else 'Unknown'
            browser_version = ua.browser.version_string if ua.browser.version_string else ''
            os_family = ua.os.family if ua.os.family else 'Unknown'
            
            # Determine device type
            if ua.is_mobile:
                device = 'Mobile'
            elif ua.is_tablet:
                device = 'Tablet'
            else:
                device = 'Desktop'
            
            # Check if unique visit (first from this IP today).
            #
            # v1.8.2: `visited_at__date=today` silently used UTC on SQLite while
            # `today` came from the site timezone (Asia/Shanghai). For the
            # 00:00–08:00 CST window the two dates differ, so *every* visit was
            # counted as unique — daily unique stats were inflated overnight.
            # Compare an explicit UTC range built from the site-local day
            # boundaries instead: same business meaning, no backend-dependent
            # `__date` timezone behaviour.
            today = timezone.localdate()
            day_start, day_end = _site_day_bounds_utc(today)
            is_unique = not Visitor.objects.filter(
                ip_address=ip,
                visited_at__gte=day_start,
                visited_at__lt=day_end,
            ).exists()
            
            Visitor.objects.create(
                ip_address=ip,
                path=request.path,
                referrer=request.META.get('HTTP_REFERER', ''),
                user_agent=ua_string[:500],
                browser=browser_family,
                browser_version=browser_version,
                os=os_family,
                device=device,
                session_key=request.session.session_key or '',
                is_unique=is_unique,
            )
            
            # Update daily stats (use F() to avoid race conditions)
            from django.db.models import F
            daily_stats, _ = DailyStats.objects.get_or_create(date=today)
            DailyStats.objects.filter(pk=daily_stats.pk).update(
                total_visits=F('total_visits') + 1,
                unique_visits=F('unique_visits') + (1 if is_unique else 0),
            )
            
        except Exception:
            pass  # Never let tracking break the site

        return response

    def get_client_ip(self, request):
        ip, _ = django_get_client_ip(request)
        return ip


class ContentSecurityPolicyMiddleware:
    """Emit a per-request Content-Security-Policy header (v1.5.9, E1; nonce v1.6.2).

    A cryptographic nonce is generated for every request and injected into both
    the CSP header (``script-src 'nonce-<n>'``) and the templates via
    ``request.csp_nonce`` (exposed through the ``request`` context processor as
    ``{{ request.csp_nonce }}``). Inline ``<script>``/``<style>`` blocks carry the
    matching nonce attribute; inline event-handler attributes (onclick=, onerror=)
    cannot be nonced and were refactored to addEventListener in base.html, which
    lets us drop ``'unsafe-inline'`` from script-src and close the main XSS vector.
    style-src keeps ``'unsafe-inline'`` because of ubiquitous inline ``style=``
    attributes.

    The policy template is read from ``settings.CONTENT_SECURITY_POLICY`` and the
    literal ``__NONCE__`` placeholder is replaced with the request nonce. The
    header is only set when absent, so an upstream middleware / view can override.

    Django's admin relies on inline scripts / event handlers (``'unsafe-inline'``)
    and is exempted with a permissive policy so the strict nonce CSP does not
    break the admin UI.
    """

    # Permissive policy for Django admin, which cannot use our per-request nonce.
    _ADMIN_POLICY = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self' 'unsafe-inline'; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'self'"
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self._policy = getattr(settings, 'CONTENT_SECURITY_POLICY', '')

    def __call__(self, request):
        nonce = secrets.token_urlsafe(16)
        request.csp_nonce = nonce
        response = self.get_response(request)
        if 'Content-Security-Policy' in response:
            return response
        if request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = self._ADMIN_POLICY
        elif self._policy:
            response['Content-Security-Policy'] = self._policy.replace('__NONCE__', nonce)
        return response
