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
    db_url = os.environ.get('DATABASE_URL', '')
    ephemeral = '/tmp/' in db_url
    if ephemeral and not notify:
        errors.append(
            Warning(
                'Contact form has no durable delivery on Vercel: DATABASE_URL points at the '
                'ephemeral /tmp SQLite (lost on redeploy) and CONTACT_NOTIFY_EMAIL is empty, '
                'so submissions are silently lost. Set CONTACT_NOTIFY_EMAIL + SMTP credentials, '
                'or point DATABASE_URL at a persistent DB (Neon/Supabase).',
                id='pages.W001',
            )
        )
    return errors
