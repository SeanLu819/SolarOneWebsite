"""Django system checks — surface production misconfiguration early.

The contact form on Vercel stores submissions in the ephemeral /tmp SQLite DB
(lost on every redeploy) unless DATABASE_URL points at a persistent DB. The only
durable delivery channel is email, gated by CONTACT_NOTIFY_EMAIL + SMTP. If
neither is configured, submissions are silently lost (incident 2026-09-13).
"""
import os

from django.conf import settings
from django.core.checks import Warning, register


@register()
def check_contact_persistence(app_configs, **kwargs):
    errors = []
    if not getattr(settings, 'IS_VERCEL', False):
        return errors
    notify = getattr(settings, 'CONTACT_NOTIFY_EMAIL', '')
    smtp_user = getattr(settings, 'EMAIL_HOST_USER', '')
    smtp_pass = getattr(settings, 'EMAIL_HOST_PASSWORD', '')
    db_url = os.environ.get('DATABASE_URL', '')
    # On Vercel the runtime defaults to the ephemeral /tmp SQLite (injected by
    # api/index.py). At BUILD time DATABASE_URL is empty (the /tmp default is only
    # set at runtime), so an empty URL on Vercel is the SAME risk as /tmp/: no
    # persistent DB is configured. Treat both as the ephemeral scenario so the
    # warning also fires during `manage.py check` at build (build.sh runs it and
    # refuses to ship if pages.W001 is present). A real postgres/mysql
    # DATABASE_URL => not risky => no warning.
    risky = (not db_url) or ('/tmp/' in db_url)
    if not risky:
        return errors
    # Ephemeral/empty DB => email is the ONLY durable channel. Both the recipient
    # and working SMTP credentials are required; a half-config (notify set but no
    # SMTP creds) silently discards mail via the locmem backend and still loses
    # the lead, so flag it explicitly.
    db_desc = 'is unset' if not db_url else 'points at the ephemeral /tmp SQLite (lost on redeploy)'
    if not notify:
        errors.append(
            Warning(
                'Contact form has no durable delivery on Vercel: DATABASE_URL ' + db_desc + ' and '
                'CONTACT_NOTIFY_EMAIL is empty, so submissions are silently lost. '
                'Set CONTACT_NOTIFY_EMAIL + SMTP credentials, or point DATABASE_URL at a '
                'persistent DB (Neon/Supabase).',
                id='pages.W001',
            )
        )
    elif not (smtp_user and smtp_pass):
        errors.append(
            Warning(
                'Contact form email is enabled (CONTACT_NOTIFY_EMAIL set) but SMTP credentials '
                '(EMAIL_HOST_USER / EMAIL_HOST_PASSWORD) are missing, so notifications are '
                'silently discarded (locmem backend) and submissions are lost on redeploy. '
                'Set EMAIL_HOST_USER + EMAIL_HOST_PASSWORD (and EMAIL_HOST / EMAIL_PORT / '
                'EMAIL_USE_TLS as needed).',
                id='pages.W001',
            )
        )
    return errors
