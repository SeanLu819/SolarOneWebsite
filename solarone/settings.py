"""
Django settings for solarone project.
"""

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Detect Vercel environment
IS_VERCEL = os.environ.get('VERCEL', '') == '1'

# Build time: VERCEL is set but VERCEL_URL is not yet available
# Runtime: both VERCEL and VERCEL_URL are set
# NOTE: IS_RUNTIME is unreliable on Vercel because VERCEL_URL timing varies.
# index.py pre-sets DATABASE_URL=sqlite:///tmp/db.sqlite3 when VERCEL=1,
# so we detect runtime by DATABASE_URL being set AND containing /tmp/
IS_RUNTIME = IS_VERCEL and '/tmp/' in os.environ.get('DATABASE_URL', '')

# SECURITY WARNING: keep the secret key used in production secret!
# In production (Vercel), SECRET_KEY should be set as an environment variable.
# We use .get() with a fallback so the app never crashes on missing env var;
# if SECRET_KEY is not configured on Vercel, a warning is logged and the
# insecure fallback is used (still functional, but sessions/CSRF are weak).
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production-x9k2m')
if IS_VERCEL and SECRET_KEY.startswith('django-insecure-'):
    import logging
    logging.getLogger('solarone').warning(
        'SECRET_KEY env var not set on Vercel — using insecure fallback. '
        'Configure SECRET_KEY in Vercel project settings immediately.'
    )

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = not IS_VERCEL and os.environ.get('DEBUG', 'True').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '.vercel.app,localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pages',
    # 'django_cleanup',  # Uncomment after installing: pip install django-cleanup
]

# On Vercel, use cookie-based sessions (no DB writes)
if IS_VERCEL:
    SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Visitor tracking middleware only in local dev (not on Vercel)
if not IS_VERCEL:
    MIDDLEWARE.append('pages.middleware.VisitorTrackingMiddleware')

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
            ],
            'debug': DEBUG,  # Match DEBUG setting instead of hardcoded True
        },
    },
]

WSGI_APPLICATION = 'solarone.wsgi.application'

# Database — support DATABASE_URL for cloud databases (e.g., Neon, Supabase)
# On Vercel: index.py sets DATABASE_URL=sqlite:////tmp/db.sqlite3 before settings loads.
# IS_RUNTIME now checks for /tmp/ in DATABASE_URL (set by index.py).
# We use direct SQLite config on Vercel to avoid dj_database_url parsing issues.
if IS_VERCEL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',
        }
    }
else:
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL:
        try:
            import dj_database_url
            DATABASES = {'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)}
        except ImportError:
            DATABASES = {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': BASE_DIR / 'db.sqlite3',
                }
            }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

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
STATIC_ROOT = '/tmp/staticfiles' if IS_RUNTIME else BASE_DIR / 'staticfiles'

# Media files (User uploads).
# On Vercel we keep media under the static tree so WhiteNoise can serve the
# generated images/PDFs from the deployed app. For local development, serve
# media at `/media/` to avoid MEDIA_URL being within STATIC_URL (which
# prevents `runserver` from serving files).
if IS_VERCEL:
    MEDIA_URL = '/static/media/'
    MEDIA_ROOT = BASE_DIR / 'static' / 'media'
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# ============ WHITENOISE (Static File Compression & Caching) ============
# Enable gzip/brotli compression and aggressive caching for static assets
WHITENOISE_USE_FINDERS = True
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_MAX_AGE = 31536000  # 1 year cache for versioned static files
# Allow Whitenoise to compress files even without a manifest
WHITENOISE_ALLOW_ALL_ORIGINS = True
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

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
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.smtp.EmailBackend' if os.environ.get('EMAIL_HOST_USER')
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
APP_VERSION = '1.2.1'
