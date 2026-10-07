"""Mutation probes for the manual "Related Products" guards (v1.10.25).

Iron law 3: a new guard is worthless until a mutation makes it go red. Each
probe breaks one piece of the implementation, runs the guard module, and expects
a non-zero exit. The original bytes are restored in a ``finally`` block — never
via ``git checkout``.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
GUARD = 'pages.tests_project_related_products_manual'

PROBES = [
    {
        'name': 'an automatic fallback creeps back in when nothing is picked',
        'file': 'pages/views/related_links.py',
        'old': b'    if not slugs:\n        return []\n',
        'new': b'    if not slugs:\n        slugs = [p.slug for p in get_all_products(lang)[:3]]\n',
    },
    {
        'name': 'the manual picks are ignored and the whole catalogue is used',
        'file': 'pages/views/related_links.py',
        'old': b'    return [by_slug[s] for s in slugs if s in by_slug]\n',
        'new': b'    return get_all_products(lang)[:3]\n',
    },
    {
        'name': 'the seed exporter renames the key',
        'file': 'pages/seed_sync.py',
        'old': b"        'related_product_slugs': related_slugs,\r\n",
        'new': b"        'related_products': related_slugs,\r\n",
    },
    {
        'name': 'the admin stops offering the picker',
        'file': 'pages/admin/project.py',
        'old': b"            'fields': ('related_products',),\n",
        'new': b"            'fields': ('order',),\n",
    },
    {
        'name': 'the seed mirror drops the exported slugs',
        'file': 'pages/views/utils.py',
        'old': b"        self.related_product_slugs = item.get('related_product_slugs', []) or []\r\n",
        'new': b'',
    },
    {
        # The change form renders fieldsets through a name whitelist, so a
        # fieldset can exist in ProjectAdmin and still never reach the page.
        'name': 'the change form whitelist drops the new fieldset',
        'file': 'templates/admin/pages/project/change_form.html',
        'old': b" or fieldset.name == 'Related Products'",
        'new': b'',
    },
    {
        # Iron law 32: the guard must check the condition itself, not a
        # substring that a fallback branch would still satisfy.
        'name': 'the template gate grows a fallback so the section always shows',
        'file': 'templates/project_detail.html',
        # templates/project_detail.html is LF (measured, not assumed).
        'old': b'{% if related_products %}\n',
        'new': b'{% if related_products or True %}\n',
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
