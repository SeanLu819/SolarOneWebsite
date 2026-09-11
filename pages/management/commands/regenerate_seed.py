"""Regenerate pages/seed_data.py from seed_data.json (local-dev helper).

On Vercel this happens automatically in build.sh (``python -m pages.seed_sync
--json``). For a fresh local clone, or after editing seed_data.json by hand,
run this to rebuild the embedded Python module that Django imports at runtime.

Usage:
    python manage.py regenerate_seed
"""
from django.core.management.base import BaseCommand

from pages.seed_sync import sync_seed_from_json


class Command(BaseCommand):
    help = 'Regenerate pages/seed_data.py from the committed seed_data.json'

    def handle(self, *args, **options):
        ok = sync_seed_from_json()
        if ok:
            self.stdout.write(
                self.style.SUCCESS(
                    'pages/seed_data.py regenerated from seed_data.json '
                    '(seed_data.json left untouched — it is the source of truth)'
                )
            )
        else:
            self.stderr.write('Failed to regenerate seed_data.py (see errors above)')
            raise SystemExit(1)
