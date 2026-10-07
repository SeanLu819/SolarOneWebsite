"""Guards for the project image sync (admin + post_save signal), v1.10.25.

The v1.10.25 Bohemia Manor data loss: the DB stored hashed upload paths
(``projects/gallery/x_abc1234.webp``) while the files on disk kept the clean
names, so both sync passes found no media, and the prune pass then deleted
every good static file the seed still referenced — the exported gallery went
empty and the page lost all its images. Three behaviours must hold:

1. a hashed DB path resolves through the clean-name fallback;
2. a DB path that already IS a canonical static path is kept (and its file
   protected from pruning) even though no media file exists;
3. the prune pass never runs when nothing resolved — an empty result set
   means "media missing", not "gallery empty".
"""
import os
import shutil
import tempfile

from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from pages.models import (
    Project,
    ProjectImage,
    _find_project_media_source,
    _static_project_file_exists,
    _sync_project_media_to_static,
)


def _admin_instance():
    return admin.site._registry[Project]


class ProjectImageSyncTests(TestCase):
    def setUp(self):
        tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        self.tmp = tmp
        self.slug = 'sync-probe-project'
        self.static_dir = os.path.join(
            tmp, 'static', 'images', 'projects', self.slug)
        self.media_dir = os.path.join(tmp, 'media')
        os.makedirs(self.static_dir)
        os.makedirs(os.path.join(self.media_dir, 'projects', 'gallery'))
        self.patcher = override_settings(BASE_DIR=tmp, MEDIA_ROOT=self.media_dir)
        self.patcher.enable()
        self.addCleanup(self.patcher.disable)

        self.project = Project.objects.create(
            slug=self.slug, title='T', location='L',
            venue_type='OUTDOOR', sport_type='FOOTBALL_FIELD', description='d')

    # -- helpers -------------------------------------------------------
    def _put_media(self, rel, payload=b'x'):
        path = os.path.join(self.media_dir, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as fh:
            fh.write(payload)
        return path

    def _put_static(self, name, payload=b'x'):
        path = os.path.join(self.static_dir, name)
        with open(path, 'wb') as fh:
            fh.write(payload)
        return path

    # -- 1. hashed DB path falls back to the clean media file ----------
    def test_hashed_db_path_falls_back_and_writes_back(self):
        self._put_media('projects/gallery/probe-shot_abc1234.webp', b'v1')
        img = ProjectImage.objects.create(
            project=self.project,
            image=SimpleUploadedFile('probe-shot_abc1234.webp', b'v1'),
            order=0)
        # point the DB row at the hashed upload path, like a real upload does
        ProjectImage.objects.filter(pk=img.pk).update(
            image='projects/gallery/probe-shot_abc1234.webp')
        img.refresh_from_db()

        _admin_instance()._sync_project_images(self.project)

        copied = os.path.join(self.static_dir, 'probe-shot.webp')
        self.assertTrue(os.path.isfile(copied),
                        'the clean-named media file was not copied to static')
        with open(copied, 'rb') as fh:
            self.assertEqual(fh.read(), b'v1')
        img.refresh_from_db()
        self.assertEqual(
            img.image.name,
            'images/projects/%s/probe-shot.webp' % self.slug,
            'the canonical static path was not written back to the DB')

    def test_the_media_fallback_helper_finds_clean_names(self):
        self._put_media('projects/gallery/probe-shot.webp', b'v')
        found = _find_project_media_source(
            self.media_dir, 'projects/gallery/probe-shot_zzz9999.webp')
        self.assertIsNotNone(found, 'clean-name fallback failed')
        self.assertTrue(found.replace(os.sep, '/').endswith(
            'projects/gallery/probe-shot.webp'))

    # -- 2. canonical static DB paths survive a media-less save --------
    def test_static_db_path_is_kept_and_protected_from_prune(self):
        # static file exists, media file does not: exactly the recovered state
        self._put_static('probe-shot.webp', b'keep-me')
        img = ProjectImage.objects.create(project=self.project, order=0)
        ProjectImage.objects.filter(pk=img.pk).update(
            image='images/projects/%s/probe-shot.webp' % self.slug)

        _admin_instance()._sync_project_images(self.project)

        self.assertTrue(os.path.isfile(os.path.join(self.static_dir,
                                                    'probe-shot.webp')),
                        'the static file was deleted although the DB still '
                        'references it via its canonical path')

    # -- 3. prune never fires when nothing could be resolved -----------
    def test_prune_never_empties_the_directory(self):
        # a good static file exists but the DB references something missing
        self._put_static('good-file.webp', b'keep-me')
        img = ProjectImage.objects.create(project=self.project, order=0)
        ProjectImage.objects.filter(pk=img.pk).update(
            image='projects/gallery/gone-from-media_abc1234.webp')

        _admin_instance()._sync_project_images(self.project)
        self.assertTrue(os.path.isfile(os.path.join(self.static_dir,
                                                    'good-file.webp')),
                        'prune wiped a good file although no image resolved')

        # the same contract on the signal-side pass
        _sync_project_media_to_static(self.project)
        self.assertTrue(os.path.isfile(os.path.join(self.static_dir,
                                                    'good-file.webp')),
                        'the signal-side prune wiped a good file')

    def test_signal_side_also_uses_the_fallback(self):
        self._put_media('projects/gallery/probe-shot.webp', b'v1')
        img = ProjectImage.objects.create(project=self.project, order=0)
        ProjectImage.objects.filter(pk=img.pk).update(
            image='projects/gallery/probe-shot_abc1234.webp')
        img.refresh_from_db()

        _cover, gallery = _sync_project_media_to_static(self.project)

        self.assertIn('images/projects/%s/probe-shot.webp' % self.slug,
                      gallery,
                      'the signal-side pass missed the hashed DB path')

    def test_the_static_path_predicate_rejects_media_paths(self):
        self.assertFalse(_static_project_file_exists('projects/gallery/x.webp'))
        self.assertFalse(_static_project_file_exists(''))
        # images/... paths are only accepted when the file really exists
        self.assertFalse(_static_project_file_exists(
            'images/projects/%s/nope.webp' % self.slug))
