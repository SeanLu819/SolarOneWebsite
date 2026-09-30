"""Guards for the contact form durability fix (J1).

Two concerns are locked here:

1. ``solarone.settings._resolve_databases`` — the pure function that decides
   which DB backend is used. On Vercel a persistent ``DATABASE_URL``
   (postgres/mysql) MUST override the ephemeral ``/tmp`` SQLite; that is the
   whole "Neon/Supabase ready" half of J1 (a config-only switch). If the
   function regresses and re-hardcodes ``/tmp`` on Vercel, contact submissions
   go back to being lost on every redeploy.

2. ``pages.views.views_contact.contact`` — the delivery honesty contract: a
   submission must only be reported as successfully delivered when it is
   actually durably stored (email delivered OR persistent DB). If BOTH the
   email channel and the DB are non-durable (runtime /tmp + no notify), the
   visitor must see an honest error, never a false success (incident 2026-09-13).

   Note on DB writes: the view ALWAYS ``ContactMessage.objects.create(...)``
   before deciding the message. On the ephemeral /tmp SQLite that write happens
   but is lost on redeploy — so the guard here checks the *reported* outcome
   (success flag / honest-error text), not whether the row survived, because
   survival depends on the DB backend under test (real /tmp in prod, real
   test DB here).
"""
import os

from django.test import TestCase, Client
from django.test.utils import override_settings
from django.core.cache import cache
from unittest.mock import patch

from solarone.settings import _resolve_databases
from pages.models import ContactMessage


class DatabaseResolutionTests(TestCase):
    """``_resolve_databases`` must route Vercel to a persistent DB when given one."""

    def test_vercel_with_postgres_uses_persistent_db(self):
        dbs = _resolve_databases(True, 'postgres://user:pass@ep-neon.tech/db')
        engine = dbs['default']['ENGINE']
        self.assertTrue(
            engine.endswith('postgresql') or engine.endswith('psycopg'),
            f'expected a postgres engine, got {engine}',
        )
        self.assertNotEqual(dbs['default']['NAME'], '/tmp/db.sqlite3')

    def test_vercel_with_mysql_uses_persistent_db(self):
        dbs = _resolve_databases(True, 'mysql://user:pass@db.tech/contact')
        self.assertIn('mysql', dbs['default']['ENGINE'])

    def test_vercel_empty_url_stays_ephemeral(self):
        dbs = _resolve_databases(True, '')
        self.assertEqual(dbs['default']['NAME'], '/tmp/db.sqlite3')

    def test_vercel_tmp_url_stays_ephemeral(self):
        dbs = _resolve_databases(True, 'sqlite:////tmp/db.sqlite3')
        self.assertEqual(dbs['default']['NAME'], '/tmp/db.sqlite3')

    def test_local_empty_url_uses_local_sqlite(self):
        dbs = _resolve_databases(False, '')
        self.assertEqual(dbs['default']['ENGINE'], 'django.db.backends.sqlite3')
        self.assertEqual(dbs['default'].get('OPTIONS', {}).get('timeout'), 2)

    def test_local_postgres_url_parsed(self):
        dbs = _resolve_databases(False, 'postgres://u:p@h/db')
        self.assertTrue(dbs['default']['ENGINE'].endswith('postgresql'))


class ContactDeliveryHonestyTests(TestCase):
    """The view must never claim success when the lead is actually lost.

    ``cache.clear()`` in setUp resets the in-process LocMem rate limiter so the
    per-(ip, session) cap (default 3) does not bleed across tests in the same
    process and deny a legitimate submission.
    """

    def setUp(self):
        cache.clear()

    def _post(self, data, **settings_override):
        with override_settings(**settings_override):
            client = Client()
            return client.post('/contact/', data, HTTP_HOST='localhost')

    def _valid_data(self, **extra):
        base = {
            'name': 'Jane Buyer',
            'email': 'jane@example.com',
            'phone': '+86 13800000000',
            'message': 'Please quote 20 sets of FL6M for a stadium project.',
        }
        base.update(extra)
        return base

    def test_runtime_without_email_shows_honest_error(self):
        """Vercel ephemeral DB + no notify => lead not durably delivered => honest error."""
        before = ContactMessage.objects.count()
        resp = self._post(
            self._valid_data(),
            IS_RUNTIME=True,
            IS_VERCEL=True,
            CONTACT_NOTIFY_EMAIL='',
        )
        # No false success flag.
        self.assertFalse(resp.context.get('contact_submitted_success', False))
        # Honest error text must be shown to the visitor.
        self.assertContains(resp, 'could not deliver', status_code=200)
        # The view always writes the row first; on /tmp that write is ephemeral.
        self.assertEqual(ContactMessage.objects.count(), before + 1)

    def test_local_without_email_saves_and_succeeds(self):
        """Local/dev: DB persists => success is honest even without email."""
        before = ContactMessage.objects.count()
        resp = self._post(
            self._valid_data(),
            IS_RUNTIME=False,
            IS_VERCEL=False,
            CONTACT_NOTIFY_EMAIL='',
        )
        self.assertTrue(resp.context.get('contact_submitted_success', False))
        self.assertEqual(ContactMessage.objects.count(), before + 1)

    def test_email_delivered_marks_success(self):
        """Email channel works (locmem backend, no network) => success."""
        before = ContactMessage.objects.count()
        resp = self._post(
            self._valid_data(),
            IS_RUNTIME=True,
            IS_VERCEL=True,
            CONTACT_NOTIFY_EMAIL='sales@solaronelighting.com',
            EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        )
        self.assertTrue(resp.context.get('contact_submitted_success', False))
        self.assertEqual(ContactMessage.objects.count(), before + 1)

    def test_email_send_failure_on_runtime_is_honest(self):
        """Runtime /tmp + email configured but SMTP fails => honest error, no false success."""
        before = ContactMessage.objects.count()
        with patch('django.core.mail.send_mail', side_effect=Exception('smtp down')):
            resp = self._post(
                self._valid_data(),
                IS_RUNTIME=True,
                IS_VERCEL=True,
                CONTACT_NOTIFY_EMAIL='sales@solaronelighting.com',
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
            )
        self.assertContains(resp, 'could not deliver', status_code=200)
        self.assertFalse(resp.context.get('contact_submitted_success', False))
        self.assertEqual(ContactMessage.objects.count(), before + 1)

    def test_email_send_failure_on_persistent_db_still_succeeds(self):
        """Persistent DB (non-runtime) + email fails => lead saved => success is honest."""
        before = ContactMessage.objects.count()
        with patch('django.core.mail.send_mail', side_effect=Exception('smtp down')):
            resp = self._post(
                self._valid_data(),
                IS_RUNTIME=False,
                IS_VERCEL=True,  # pretend Vercel but with a persistent DB
                CONTACT_NOTIFY_EMAIL='sales@solaronelighting.com',
                EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
            )
        self.assertTrue(resp.context.get('contact_submitted_success', False))
        self.assertEqual(ContactMessage.objects.count(), before + 1)

    def test_honeypot_silently_drops(self):
        """A filled honeypot field must drop the submission (not saved) but pretend success."""
        before = ContactMessage.objects.count()
        resp = self._post(
            self._valid_data(company_website='http://spam.example'),
            IS_RUNTIME=False,
            IS_VERCEL=False,
            CONTACT_NOTIFY_EMAIL='',
        )
        self.assertEqual(resp.status_code, 200)
        # The honeypot branch returns early — nothing is persisted.
        self.assertEqual(ContactMessage.objects.count(), before)


class ContactDurabilitySystemCheckTests(TestCase):
    """pages.W001 must fire on Vercel whenever there is no durable channel.

    The check reads DATABASE_URL from os.environ (not settings), so the env var
    is manipulated directly here rather than via override_settings.
    """

    def _run_with_env(self, db_url, notify='', smtp_user='', smtp_pass=''):
        saved = {
            'DATABASE_URL': os.environ.get('DATABASE_URL'),
            'CONTACT_NOTIFY_EMAIL': os.environ.get('CONTACT_NOTIFY_EMAIL'),
            'EMAIL_HOST_USER': os.environ.get('EMAIL_HOST_USER'),
            'EMAIL_HOST_PASSWORD': os.environ.get('EMAIL_HOST_PASSWORD'),
        }
        if db_url is None:
            os.environ.pop('DATABASE_URL', None)
        else:
            os.environ['DATABASE_URL'] = db_url
        os.environ['CONTACT_NOTIFY_EMAIL'] = notify
        os.environ['EMAIL_HOST_USER'] = smtp_user
        os.environ['EMAIL_HOST_PASSWORD'] = smtp_pass
        # Re-resolve settings-derived flags the check reads.
        with override_settings(
            IS_VERCEL=True,
            CONTACT_NOTIFY_EMAIL=notify,
            EMAIL_HOST_USER=smtp_user,
            EMAIL_HOST_PASSWORD=smtp_pass,
        ):
            from pages.checks import check_contact_persistence
            errors = check_contact_persistence(None)
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        return errors

    def test_vercel_ephemeral_db_without_email_warns(self):
        errors = self._run_with_env(db_url='', notify='', smtp_user='', smtp_pass='')
        self.assertIn('pages.W001', [e.id for e in errors])

    def test_vercel_notify_but_no_smtp_warns(self):
        errors = self._run_with_env(
            db_url='', notify='sales@solaronelighting.com', smtp_user='', smtp_pass=''
        )
        self.assertIn('pages.W001', [e.id for e in errors])

    def test_vercel_persistent_db_no_warning(self):
        errors = self._run_with_env(db_url='postgres://u:p@db/contact')
        self.assertFalse(any(e.id == 'pages.W001' for e in errors))
