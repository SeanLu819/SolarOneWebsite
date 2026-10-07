"""Mutation probes for the project image sync guards (v1.10.25).

Iron law 3: a new guard is worthless until a mutation makes it go red. Each
probe breaks one piece of the sync implementation, runs the guard module, and
expects a non-zero exit. The original bytes are restored in a ``finally`` block
— never via ``git checkout``.

Anchors are written as LF and converted, so a stray ``/r/n`` typo cannot slip
in (that exact typo cost a debugging round while writing these probes).
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
GUARD = 'pages.tests_project_image_sync'


def C(s):
    """LF anchor -> CRLF bytes (models.py is pure CRLF)."""
    return s.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')


PROBES = [
    {
        # admin pass: without the fallback the hashed DB path finds no media
        'name': 'the admin pass loses the clean-name fallback',
        'file': 'pages/admin/project.py',  # measured: pure LF
        'old': b'            src = _find_project_media_source(media_root, fname)\n'
               b'            if src:\n'
               b'                dst_name = _clean_hashed_filename(src)\n'
               b'                return src, f\'images/projects/{slug}/{dst_name}\', dst_name\n',
        'new': b'            src = None\n'
               b'            if src:\n'
               b'                dst_name = _clean_hashed_filename(src)\n'
               b'                return src, f\'images/projects/{slug}/{dst_name}\', dst_name\n',
    },
    {
        'name': 'the admin pass stops writing canonical paths back',
        'file': 'pages/admin/project.py',
        'old': b'        for holder, field, rel in writebacks:\n'
               b'            setattr(holder, field, rel)\n'
               b'            holder.save(update_fields=[field])\n',
        'new': b'        for holder, field, rel in writebacks:\n'
               b'            pass\n',
    },
    {
        'name': 'the admin prune guard is removed',
        'file': 'pages/admin/project.py',
        'old': b'        _preserved = {\'old-hid-lighting.webp\', \'new-led-lighting.webp\'}\n'
               b'        if current_dest_names:\n',
        'new': b'        _preserved = {\'old-hid-lighting.webp\', \'new-led-lighting.webp\'}\n'
               b'        if True:\n',
    },
    {
        # signal pass: same fallback, different module
        'name': 'the signal pass loses the clean-name fallback',
        'file': 'pages/models.py',  # measured: pure CRLF
        'old': C(b'        src = _find_project_media_source(media_root, fname)\n'
                 b'        if src:\n'
                 b'            dst_name = _clean_hashed_filename(src)\n'),
        'new': C(b'        src = None\n'
                 b'        if src:\n'
                 b'            dst_name = _clean_hashed_filename(src)\n'),
    },
    {
        'name': 'the signal prune guard is removed',
        'file': 'pages/models.py',
        'old': C(b'    # still references (the v1.10.25 Bohemia Manor data loss).\n'
                 b'    if current_dest_names:\n'),
        'new': C(b'    # still references (the v1.10.25 Bohemia Manor data loss).\n'
                 b'    if True:\n'),
    },
]


def run_guard():
    return subprocess.run([PY, 'manage.py', 'test', GUARD, '-v', '0'],
                          cwd=ROOT, capture_output=True, text=True)


def main():
    failures = 0
    for probe in PROBES:
        path = os.path.join(ROOT, probe['file'])
        with open(path, 'rb') as fh:
            original = fh.read()
        try:
            n = original.count(probe['old'])
            if n != 1:
                print('PROBE SKIPPED (anchor found %d times): %s'
                      % (n, probe['name']))
                failures += 1
                continue
            with open(path, 'wb') as fh:
                fh.write(original.replace(probe['old'], probe['new'], 1))
            res = run_guard()
            if res.returncode == 0:
                failures += 1
                print('PROBE BROKEN (guard stayed green): %s' % probe['name'])
            else:
                print('PROBE OK (guard went red): %s' % probe['name'])
        finally:
            with open(path, 'wb') as fh:
                fh.write(original)
            with open(path, 'rb') as fh:
                assert fh.read() == original, 'restore failed: ' + probe['file']
    print()
    print('%d/%d probes behaved as expected' % (len(PROBES) - failures, len(PROBES)))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
