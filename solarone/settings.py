"""
Django settings for solarone project.
"""

from pathlib import Path
import os
import secrets
from django.core.exceptions import ImproperlyConfigured

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ---- Local development .env loader (optional) ----
# Read a gitignored .env file from the project root so local development can
# keep a stable SECRET_KEY (sessions/CSRF survive restarts). Real environment
# variables always win. Minimal parser on purpose — no interpolation/expansion —
# so a missing .env never affects Vercel/production deployments.
def _load_local_env(path):
    for _line in path.read_text(encoding='utf-8').splitlines():
        _line = _line.strip()
        if not _line or _line.startswith('#') or '=' not in _line:
            continue
        _key, _value = _line.split('=', 1)
        _key = _key.strip()
        _value = _value.strip()
        # Strip surrounding single/double quotes, e.g. SECRET_KEY="abc"
        if len(_value) >= 2 and _value[0] == _value[-1] and _value[0] in ('"', "'"):
            _value = _value[1:-1]
        if _key and _key not in os.environ:
            os.environ[_key] = _value

_ENV_FILE = BASE_DIR / '.env'
if _ENV_FILE.exists():
    _load_local_env(_ENV_FILE)
del _load_local_env, _ENV_FILE

# Detect Vercel environment
IS_VERCEL = os.environ.get('VERCEL', '') == '1'

# Build time: VERCEL is set but VERCEL_URL is not yet available
# Runtime: both VERCEL and VERCEL_URL are set
# NOTE: IS_RUNTIME is unreliable on Vercel because VERCEL_URL timing varies.
# index.py pre-sets DATABASE_URL=sqlite:///tmp/db.sqlite3 when VERCEL=1,
# so we detect runtime by DATABASE_URL being set AND containing /tmp/
IS_RUNTIME = IS_VERCEL and '/tmp/' in os.environ.get('DATABASE_URL', '')

# SECURITY WARNING: keep the secret key used in production secret!
# On Vercel (production), SECRET_KEY MUST be set as an environment variable.
# If missing, we raise ImproperlyConfigured — no insecure fallback.
# In local dev (non-Vercel), a random key is generated each startup so
# the app never crashes, but sessions/CSRF will not persist across restarts.
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    if IS_VERCEL:
        raise ImproperlyConfigured(
            'SECRET_KEY environment variable is required on Vercel. '
            'Set it in the Vercel project settings.'
        )
    # Local development: generate a random key for this process
    SECRET_KEY = secrets.token_urlsafe(50)
    import logging
    logging.getLogger('solarone').warning(
        'SECRET_KEY not set in environment — generated a random key for '
        'local development. Sessions/CSRF will not persist across '
        'restarts. Set SECRET_KEY=... in your .env for stable local dev.'
    )

# SECURITY WARNING: don't run with debug turned on in production!
# DEBUG defaults to False everywhere (including local dev) — developers must
# explicitly set DEBUG=true in their environment to enable debug mode.
# On Vercel, DEBUG is force-disabled regardless of env var.
DEBUG = not IS_VERCEL and os.environ.get('DEBUG', 'False').lower() == 'true'


# Fixed origin for canonical/SEO URLs (#17): canonical link, hreflang,
# og:url, JSON-LD, sitemap.xml and robots.txt must NOT depend on the
# request Host — otherwise any *.vercel.app preview URL (or a spoofed
# Host header accepted via the ALLOWED_HOSTS wildcard) could become the
# canonical URL, an SEO/cache-poisoning vector.
CANONICAL_ORIGIN = os.environ.get(
    'CANONICAL_ORIGIN', 'https://www.solaronelighting.com'
).rstrip('/')

# ============ WEB ANALYTICS (M2 / SEO P1c) ============
# GA4 Measurement ID (e.g. 'G-XXXXXXXXXX'). Empty = analytics disabled (no
# third-party request is made). Set via env (Vercel: GA4_MEASUREMENT_ID).
GA4_MEASUREMENT_ID = os.environ.get('GA4_MEASUREMENT_ID', '')
# Google Search Console verification meta tag content (from GSC). Empty = omit.
GSC_VERIFICATION_CODE = os.environ.get('GSC_VERIFICATION_CODE', '')

# #4 (v1.6.1): tighten ALLOWED_HOSTS — drop the bare `.vercel.app` wildcard that
# let ANY *.vercel.app host (incl. attacker-controlled) be accepted, an SEO/canonical
# poisoning vector (see CANONICAL_ORIGIN below). Keep the known preview host +
# production custom domains + localhost. Random branch-preview *.vercel.app URLs must
# set ALLOWED_HOSTS env (Vercel "Preview" scope) if they must be served.
ALLOWED_HOSTS = os.environ.get(
    'ALLOWED_HOSTS',
    'www.solaronelighting.com,solaronelighting.com,solar-one-website.vercel.app,localhost,127.0.0.1'
).split(',')

# Trusted origins for CSRF protection (Django 4+ requires full origin URLs).
# Without this, POST forms (contact, admin) from the custom domains would
# fail with 403 once ALLOWED_HOSTS is fixed.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get(
        'CSRF_TRUSTED_ORIGINS',
        'https://solar-one-website.vercel.app,'
        'https://www.solaronelighting.com,'
        'https://solaronelighting.com'
    ).split(',') if o.strip()
]

# ============ SECURITY: HTTPS, HSTS & secure cookies ============
# Vercel terminates TLS at its edge and proxies to the app over HTTP.
# Without SECURE_PROXY_SSL_HEADER, request.is_secure() returns False,
# which breaks secure-cookie logic and CSRF origin checks (#22).
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if IS_VERCEL:
    # Production: force HTTPS and enable HSTS (1 year, preload-ready) (#5).
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # Cookies are HTTPS-only in production (#6). Local dev stays False so
    # plain-http 127.0.0.1 logins/POSTs keep working.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    # Local dev runs on http://127.0.0.1 — no redirect/HSTS there, and
    # Secure cookies would break plain-http logins/POSTs.
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

SECURE_CONTENT_TYPE_NOSNIFF = True
# Django 6 renamed this from REFERRER_POLICY.
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
# NOTE: CSRF_COOKIE_HTTPONLY is intentionally left at its default (False):
# static/admin/js/auto_translate.js reads the csrftoken cookie to send the
# X-CSRFToken header; marking it HttpOnly would break admin auto-translate.

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages.apps.PagesConfig',
    # 'django_cleanup',  # Uncomment after installing: pip install django-cleanup
]

# On Vercel, use cookie-based sessions (no DB writes)
if IS_VERCEL:
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

# ============ CONTENT SECURITY POLICY (E1, v1.5.9) ============
# Baseline CSP response header. Initially permissive (unsafe-inline) because
# templates still contain inline <script>/<style> and inline event handlers;
# this is defense-in-depth without breaking the site. Tighten (nonces / hashes)
# later once inline code is migrated out. The header is emitted by
# pages.middleware.ContentSecurityPolicyMiddleware, inserted right after
# SecurityMiddleware below.
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "img-src 'self' data: https://www.google-analytics.com https://*.google-analytics.com; "
    "style-src 'self' 'unsafe-inline'; "
    "script-src 'self' 'nonce-__NONCE__' https://www.googletagmanager.com; "
    "font-src 'self'; "
    "connect-src 'self' https://www.google-analytics.com https://*.google-analytics.com https://analytics.google.com; "
    "frame-ancestors 'none'; "
    "base-uri 'self'"
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'pages.middleware.ContentSecurityPolicyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if not IS_VERCEL:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    MIDDLEWARE.append('pages.middleware.VisitorTrackingMiddleware')
else:
    # v1.10.3: edge caching for HTML. Must sit LAST so it sees the final
    # response (after sessions/CSRF had their chance to add Set-Cookie) and
    # can veto caching. It is a no-op unless EDGE_CACHE_ENABLED (below).
    MIDDLEWARE.append('pages.edge_cache.EdgeCacheHeaderMiddleware')

ROOT_URLCONF = 'solarone.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'pages.context_processors.canonical_origin',
            ],
            'debug': DEBUG,  # Match DEBUG setting instead of hardcoded True
        },
    },
]

WSGI_APPLICATION = 'solarone.wsgi.application'

# Database — support DATABASE_URL for cloud databases (e.g., Neon, Supabase).
# On Vercel the runtime defaults to sqlite:////tmp/... (ephemeral) — api/index.py
# injects that fallback ONLY when DATABASE_URL is absent, so a persistent
# DATABASE_URL (postgres:// / mysql://) set on Vercel OVERRIDES the ephemeral
# default with no further code changes. build.sh already runs `migrate` when
# DATABASE_URL is present and not /tmp/ (build.sh:98), so the contact form
# (and any real DB model) survives redeploys once DATABASE_URL points at Neon/
# Supabase. This is the J1 "持久化" fix: a config-only switch.
_LOCAL_SQLITE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # 2026-09-26 故障：本地 dev 下 runserver / 测试进程 / 预览自动刷新并发
        # 访问同一个 db.sqlite3，VisitorTrackingMiddleware 的 INSERT 在默认
        # busy 等待里一卡 30-56s（期间读锁也被压制），页面请求整体 30-56s，
        # admin 写路径直接 "database is locked" → 500。给 2s 短超时：中间件
        # 本来就 except-pass 吞掉写失败（页面照常渲染），admin 则快速报错
        # 而不是挂着。Vercel /tmp 分支是单进程无并发，无需设置。
        'OPTIONS': {'timeout': 2},
    }
}

# Ephemeral Vercel runtime SQLite (lost on every deploy / instance recycle).
_EPHEMERAL_SQLITE = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }
}

# Extracted as a pure function so it is unit-testable without booting Django
# (tests_contact.py imports it directly). See J1 changelog (seo-growth-plan.md).
def _resolve_databases(is_vercel, db_url):
    """Return the DATABASES dict for the given runtime context.

    - Local dev (is_vercel False) honours a real DATABASE_URL if set, else the
      shared local SQLite (2s busy-timeout to survive concurrent dev access).
    - Vercel honours a persistent DATABASE_URL (postgres/mysql) if supplied; the
      api/index.py /tmp fallback only kicks in when DATABASE_URL is absent, so a
      Neon/Supabase connection string is a drop-in — no further code changes.
    - Anything else (absent or sqlite:////tmp/...) uses the ephemeral /tmp SQLite,
      which is the documented J1 risk: submissions there are lost on redeploy.
    """
    if not is_vercel:
        if db_url:
            try:
                import dj_database_url
                return {'default': dj_database_url.parse(db_url, conn_max_age=600)}
            except ImportError:
                return _LOCAL_SQLITE
        return _LOCAL_SQLITE
    # Vercel: persistent external DB wins; otherwise ephemeral /tmp.
    _persistent = bool(db_url) and 'sqlite:////tmp' not in db_url and db_url.startswith(
        ('postgres', 'postgresql', 'postgres+', 'mysql', 'mysql+')
    )
    if _persistent:
        try:
            import dj_database_url
            return {'default': dj_database_url.parse(db_url, conn_max_age=600)}
        except ImportError:
            # dj_database_url missing on Vercel => never crash the build; fall
            # back to ephemeral (the pre-existing behaviour) rather than the
            # persistent DB, because we cannot parse the URL safely.
            return _EPHEMERAL_SQLITE
    return _EPHEMERAL_SQLITE


if IS_VERCEL:
    DATABASES = _resolve_databases(True, os.environ.get('DATABASE_URL', ''))
else:
    DATABASES = _resolve_databases(False, os.environ.get('DATABASE_URL', ''))

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
    ('es', 'Español'),
    ('de', 'Deutsch'),
    ('ru', 'Русский'),
    ('ar', 'العربية'),
]

LOCALE_PATHS = [BASE_DIR / 'locale']

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
# STATIC_ROOT must be consistent for both build-time collectstatic and runtime.
# Locally we keep the conventional ./staticfiles (git-ignored). On the Vercel
# build, build.sh sets VERCEL_STATIC_ROOT=public/static so collectstatic writes
# the hashed assets DIRECTLY into the CDN root (public/static) — this skips the
# redundant ~140 MB `cp -R staticfiles public/static` that otherwise doubled the
# build's static-processing cost (2026-09-28 build-speed fix).
_VERCEL_STATIC_ROOT = os.environ.get('VERCEL_STATIC_ROOT')
STATIC_ROOT = BASE_DIR / (_VERCEL_STATIC_ROOT or 'staticfiles')

# WhiteNoise 6.x emits a "No directory at: <STATIC_ROOT>" UserWarning at
# middleware-init time when STATIC_ROOT does not exist. build.sh creates
# staticfiles/ during Vercel builds and the directory is gitignored, so on a
# fresh local clone it is absent — create it to keep local startup clean.
if not IS_VERCEL:
    STATIC_ROOT.mkdir(parents=True, exist_ok=True)

# Media files (User uploads).
# CRITICAL: Vercel's serverless filesystem is ephemeral — files written at
# runtime disappear after the request. Therefore:
#   1. Locally: use /media/ + BASE_DIR/media (normal Django behavior)
#   2. Vercel:  use the SAME /media/ URL namespace so DB-stored paths work
#      unchanged, but MEDIA_ROOT also points into the static tree so files
#      committed there (or copied by the post-save signal during a local
#      admin session before git push) get served by WhiteNoise on Vercel.
# Admin uploads made ON Vercel will NOT persist — admins must work locally
# then commit the copied static/images/projects/* files + updated seed JSON.
MEDIA_URL = '/media/'
if IS_VERCEL:
    MEDIA_ROOT = BASE_DIR / 'static' / 'media'
else:
    MEDIA_ROOT = BASE_DIR / 'media'

# ============ WHITENOISE (Static File Compression & Caching) ============
# On Vercel, WhiteNoiseMiddleware is removed from MIDDLEWARE (index.py
# handles static files via a WSGI-level wrapper). So WhiteNoise only runs
# in the index.py wrapper, where it reads files directly from disk.
# WHITENOISE_USE_FINDERS controls the Django-middleware integration —
# irrelevant on Vercel but we set it False for clarity.
WHITENOISE_USE_FINDERS = not IS_VERCEL
WHITENOISE_MANIFEST_STRICT = False
# Local dev only: WhiteNoise without autorefresh serves the file snapshot
# taken AT PROCESS START (its `self.files` dict). Admin image uploads write
# into static/ (and collectstatic into staticfiles/) while the server keeps
# running -> those new files 404 until a restart: the admin changelist icon
# goes missing and freshly uploaded product images break on the frontend.
# autorefresh=True re-resolves via finders/directory scan per request.
# Vercel stays False: files are collected once at build time, the wrapper
# process only lives for the request anyway.
WHITENOISE_AUTOREFRESH = not IS_VERCEL
# N-30: a 1-year max-age is only safe for content-HASHED filenames, which exist
# solely on Vercel (BundledManifestStaticFilesStorage -> css/base.<hash>.css).
# Locally the URL is un-versioned (/static/css/base.css), so a 1-year max-age
# made the dev browser pin the OLD stylesheet for a year after every edit —
# the "I changed the CSS but my phone still shows the old layout" trap.
# 0 => "max-age=0, public" => the browser revalidates on every request.
# 🔴 On Vercel this value is DEAD CONFIG — see the CORRECTION note in the
# STATIC STORAGE block below. Production caching is set by vercel.json headers.
WHITENOISE_MAX_AGE = 31536000 if IS_VERCEL else 0
# ============ EDGE CACHE (HTML) ============
# 🔴 v1.10.3: production serves EVERY HTML response as
# `max-age=0, must-revalidate` with `X-Vercel-Cache: MISS` (measured
# 2026-10-04), i.e. every page view re-runs Django even for a returning
# visitor. `pages.edge_cache.EdgeCacheHeaderMiddleware` attaches
# `Vercel-CDN-Cache-Control` (edge-only: the browser keeps revalidating, so a
# deploy shows up immediately and content never goes stale for a visitor).
#
# 🔴 This CANNOT live in vercel.json. Vercel's `headers.source` "matches each
# incoming pathname (excluding querystring)" and `missing` needs a concrete key
# with no wildcard — so a rule cannot distinguish `/news/` from
# `/news/?category=…`, which are different documents (verified by md5). A
# catch-all would serve one category's filtered page to everyone.
#
# Kept off locally: a cached local response would hide code changes during
# runserver, and the sqlite-backed VisitorTrackingMiddleware writes per GET.
EDGE_CACHE_ENABLED = IS_VERCEL
# Do NOT send Access-Control-Allow-Origin:* for static assets (#7) —
# no legitimate third-party site needs to fetch this site's static files.
WHITENOISE_ALLOW_ALL_ORIGINS = False
WHITENOISE_EXTRA_PREFIXES = [
    ('/media/', str(BASE_DIR / 'static' / 'media')),
]
# ============ STATIC STORAGE (content hashing -> immutable CDN cache) ============
# P0 speed win: on production, serve CSS/JS/images from a content-hashed filename
# so Vercel's edge CDN can return `Cache-Control: immutable, max-age=31536000`
# for repeat visitors, replacing `max-age=0, must-revalidate` on un-hashed files.
#
# 🔴 CORRECTION (v1.9.7, verified live 2026-10-03): the two settings above DO NOT
# produce that header in production, and the old comment here claimed they did.
# Two independent reasons:
#   1. On Vercel, WhiteNoiseMiddleware is REMOVED from MIDDLEWARE (see the
#      IS_VERCEL block above) — the api/index.py WSGI wrapper handles statics.
#   2. More decisively, build.sh mirrors collectstatic output into public/static/,
#      which Vercel serves straight from its edge CDN. Nothing in the Django
#      process ever touches those bytes, so WHITENOISE_MAX_AGE is dead config.
# Live probe that found it: `/static/css/base.<hash>.css` (already content-hashed,
# so `immutable` would be safe) still returned `max-age=0, must-revalidate`.
# The fix is the `headers` block in vercel.json — that is the only place that can
# set response headers for files served out of public/. Do not "fix" this by
# raising WHITENOISE_MAX_AGE; it changes nothing on Vercel.
#
# CRITICAL (Django 6.0): the legacy `STATICFILES_STORAGE` setting was REMOVED and
# is SILENTLY IGNORED — setting it has no effect at all. The storage MUST be
# configured via the `STORAGES` dict under the "staticfiles" key. (Root-caused
# here: with only STATICFILES_STORAGE set, collectstatic emitted un-hashed files.)
#
# Local/dev keeps the PLAIN storage on purpose: the dev server serves static via
# WhiteNoise finders (WHITENOISE_USE_FINDERS=True) straight from ./static, where
# files are NOT hash-renamed. If we hashed locally, {% static %} would emit
# hashed URLs that finders cannot resolve -> 404 on every asset. Hashing only
# matters where collectstatic actually runs (the Vercel build).
#
# v1.5.5: production uses pages.storage.BundledManifestStaticFilesStorage, which
# reads the hash map from the build-time generated pages/static_index_data.py
# instead of the on-disk staticfiles/staticfiles.json. That JSON cannot be relied
# on: staticfiles/ is excluded from the function bundle to stay under Vercel's
# 225 MB limit, and a MISSING manifest makes every {% static %} raise
# ("The file 'css/base.css' could not be found") -> HTTP 500 on every page.
# The subclass also degrades to un-hashed URLs instead of raising.
if IS_VERCEL:
    _STATIC_BACKEND = 'pages.storage.BundledManifestStaticFilesStorage'
else:
    _STATIC_BACKEND = 'django.contrib.staticfiles.storage.StaticFilesStorage'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': _STATIC_BACKEND},
}

# ============ CACHE ============
# Local dev uses LocMem (in-process). On Vercel there's no persistent cache
# backend available without extra services, so we also fall back to LocMem
# there — rate limiting will be per-instance (best-effort), which is
# acceptable for a low-traffic contact form. Upgrade to Redis/Upstash for
# strict distributed rate limiting.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'solarone-default',
    }
}

# ============ EMAIL ============
# Email is optional: if SMTP env vars are not set, contact notifications
# silently no-op (the DB record is still saved). Set these in Vercel/local
# env to enable admin email alerts on new contact submissions.
# On Vercel, if a notify recipient is configured we force the real SMTP backend
# (never locmem) so a delivery failure is LOUD (exception -> honest error to the
# visitor) instead of silently swallowed by the in-memory backend (which would
# lose the lead without anyone noticing). pages.W001 also guards this at check time.
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend'
    if (os.environ.get('EMAIL_HOST_USER') or os.environ.get('CONTACT_NOTIFY_EMAIL'))
    else 'django.core.mail.backends.locmem.EmailBackend',
)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@solarone.com')

# Recipient for new contact-message notifications. Leave empty to disable
# email notifications entirely (DB record still saved).
CONTACT_NOTIFY_EMAIL = os.environ.get('CONTACT_NOTIFY_EMAIL', '')

# ============ CONTACT RATE LIMITING ============
# Per IP+session submission cap for the contact form. Tunable via env so
# production can tighten/loosen without a code change.
CONTACT_RATE_LIMIT = int(os.environ.get('CONTACT_RATE_LIMIT', '3'))   # max submissions
CONTACT_RATE_WINDOW = int(os.environ.get('CONTACT_RATE_WINDOW', '600'))  # window in seconds

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Application version (displayed in admin)
APP_VERSION = '1.10.6'