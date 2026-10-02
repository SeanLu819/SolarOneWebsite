"""Guards for release metadata that lives outside the database.

`VERSION` (repo root), `settings.APP_VERSION` (admin header) and the version
string quoted in `llm.txt` previously drifted apart after a bump, so this
module pins all three together and keeps the AI-facing summary in sync with the
landing pages shipped in v1.9.0.
"""
import os

from django.conf import settings
from django.test import TestCase

REPO_ROOT = settings.BASE_DIR
SPORT_LANDING_PAGES = (
    '/products/sports-lighting/',
    '/products/football-stadium-lights/',
    '/products/tennis-court-lighting/',
)


def _read(*parts):
    with open(os.path.join(REPO_ROOT, *parts), encoding='utf-8') as handle:
        return handle.read()


class ReleaseMetadataConsistencyTests(TestCase):
    """The three version strings must never diverge again."""

    def test_version_file_matches_app_version(self):
        # The VERSION file carries a leading "v" while APP_VERSION does not
        # (admin headers add their own "v"), so normalise before comparing.
        self.assertEqual(_read('VERSION').strip().lstrip('vV'), settings.APP_VERSION)

    def test_app_version_follows_semver(self):
        self.assertRegex(settings.APP_VERSION, r'^\d+\.\d+\.\d+$')

    def test_llm_txt_declares_the_same_version(self):
        self.assertIn(f'Site version v{settings.APP_VERSION}', _read('llm.txt'))

    def test_llm_txt_lists_the_sport_landing_pages(self):
        text = _read('llm.txt')
        for path in SPORT_LANDING_PAGES:
            self.assertIn(path, text)
