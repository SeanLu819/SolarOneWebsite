"""Edge cache policy for HTML responses (v1.10.3).

Why this exists
---------------
Measured on production 2026-10-04: every HTML response comes back
``Cache-Control: public, max-age=0, must-revalidate`` with ``Age: 0`` and
``X-Vercel-Cache: MISS`` — i.e. **every page view executes Django**, even for
a returning visitor who just loaded the same page seconds ago. That is the
default Vercel gives a Serverless Function response.

Why it cannot be done in ``vercel.json``
----------------------------------------
The only place that can set headers for the HTML is vercel.json, but two
documented facts rule that out (Vercel docs, fetched 2026-10-04):

* ``source`` "matches each incoming pathname (**excluding querystring**)",
  so a rule cannot tell ``/news/`` from ``/news/?category=Case+Studies``.
  Those two are genuinely different documents — verified by md5: they differ.
* ``missing`` requires one concrete ``key`` and has no wildcard, so
  "has no query string at all" is not expressible in a headers block.

A catch-all rule would therefore cache the *filtered* news page under
``/news/`` and hand it to every visitor. Hence the policy lives here, where the
real ``request.META['QUERY_STRING']`` is available.

Why ``Vercel-CDN-Cache-Control`` and not ``Cache-Control``
--------------------------------------------------------
Setting ``Cache-Control: s-maxage=…`` also makes the *browser* keep the page
for ``max-age`` seconds, which delays the effect of a deploy and risks
content-flash. ``Vercel-CDN-Cache-Control`` is consumed by Vercel's proxy and
never forwarded to the client, so the browser keeps revalidating (content is
never stale for the visitor) while the edge stops re-running Django.

Safety rules encoded below
--------------------------
* Only GET/HEAD — a POST must never be replayed from cache.
* Only 200 responses; 404/500/301/302 stay uncached (caching a 302 would
  freeze a redirect target, e.g. the apex->www301, into the edge forever).
* Paths carrying per-user state are excluded: ``/admin/`` (session-bound),
  ``/contact/`` (renders a CSRF token — replaying it to another visitor makes
  their POST fail with 403) and ``/__diag__/`` (debug output).
* ``/news/feed.xml`` is excluded by exact match, not prefix — it startswith
  the cacheable ``/news/`` yet must stay fresh for RSS subscribers.
* Any query string at all is treated as uncacheable, since query-driven views
  (``/news/?category=``) render different HTML per value.
* Any response carrying ``Set-Cookie`` is excluded (a session start is
  per-visitor by definition).
* Language is part of the URL (``i18n_patterns``), so ``/de/`` and ``/en``
  are distinct cache entries. Verified on production: ``Accept-Language`` does
  NOT change the response (``/`` returns ``<html lang="en">`` for fr/de/ar
  requests alike), so caching cannot mix languages up.

Verification note
-----------------
``IS_VERCEL`` is read from the ``VERCEL`` env var while settings are imported,
and Django freezes the middleware chain at that moment — ``override_settings``
in-process cannot install a middleware the non-Vercel branch skipped. That is
not theoretical: the first implementation run had all 15 direct-call tests
green while real requests carried no header at all.
``tests_edge_cache.EdgeCacheOnVercelSubprocessTests`` therefore re-imports the
settings module in a child process with ``VERCEL=1`` and asserts on live
responses.
"""

from django.conf import settings

#: Only HTML we know is identical for every visitor. Keep this a strict
#: allowlist: a path added here becomes publicly cacheable at the edge.
CACHEABLE_HTML_PREFIXES = (
    '/',
    '/news/',
    '/products/',
    '/projects/',
    '/projects/football/',
    '/projects/tennis/',
    '/about/',
    '/privacy/',
    '/terms/',
)

#: Never cacheable, regardless of method. ``/contact/`` renders a CSRF token
#: bound to the visitor's cookie; serving a cached copy hands somebody else's
#: token to the next visitor and their form POST fails with 403.
UNCACHEABLE_PREFIXES = (
    '/admin/',
    '/contact/',
    '/__diag__/',
)

#: Never cacheable, matched exactly.
#:
#: These live *underneath* a cacheable prefix, so a ``startswith`` list cannot
#: express them: ``/news/feed.xml`` startswith ``/news/`` and would otherwise
#: be cached, holding a new article back from every RSS subscriber for up to
#: ``EDGE_S_MAXAGE`` seconds. The subprocess guard caught this — the first
#: implementation had it wrong. Freshness is the entire point of a feed.
#:
#: ``/sitemap.xml`` and ``/robots.txt`` are cacheable on purpose: search
#: engines re-fetch them on their own schedule and nothing user-facing depends
#: on them being real-time.
UNCACHEABLE_EXACT = (
    '/news/feed.xml',
)

#: Edge freshness window (seconds). Short enough that a copy edit shows up
#: within minutes, long enough that a normal browsing burst is served from the
#: edge instead of re-running Django.
EDGE_S_MAXAGE = 300

#: Serve stale while revalidating in the background. Vercel's proxy consumes
#: this directive, so it never reaches the browser — it only smooths the
#: revalidation, and a new deployment replaces the cached copy.
EDGE_SWR = 86400

CDN_CACHE_CONTROL = (
    f'public, s-maxage={EDGE_S_MAXAGE}, stale-while-revalidate={EDGE_SWR}'
)


class EdgeCacheHeaderMiddleware:
    """Attach ``Vercel-CDN-Cache-Control`` to cacheable HTML responses.

    Disabled unless ``settings.EDGE_CACHE_ENABLED`` is True; the setting is
    wired to ``IS_VERCEL`` in settings.py so local dev and tests keep seeing
    plain, uncached responses (a cached local response would hide code changes
    during ``runserver``).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _is_cacheable(request, response):
        if request.method not in ('GET', 'HEAD'):
            return False
        if response.status_code != 200:
            return False
        # A query string means the view is allowed to render per-value HTML
        # (/news/?category=…). Without this the edge would serve one
        # category's filtered page to everyone.
        if request.META.get('QUERY_STRING'):
            return False
        path = request.path
        if path in UNCACHEABLE_EXACT:
            return False
        if path.startswith(UNCACHEABLE_PREFIXES):
            return False
        if response.get('Set-Cookie'):
            # A response that starts a session must stay per-visitor.
            return False
        # /static/ is served from public/ and already carries a one-year
        # immutable rule in vercel.json; matching it here would replace that.
        if path.startswith('/static/') or path.startswith('/media/'):
            return False
        return path.startswith(CACHEABLE_HTML_PREFIXES)

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(settings, 'EDGE_CACHE_ENABLED', False):
            return response
        if self._is_cacheable(request, response):
            response['Vercel-CDN-Cache-Control'] = CDN_CACHE_CONTROL
        return response