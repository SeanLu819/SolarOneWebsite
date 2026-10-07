"""Mutation probes for pages/tests_carousel_thumb_srcset.py (run manually).

Applies a deliberate regression to a template, runs the guard suite, and
restores the original bytes in a finally block. A probe is only meaningful if
the suite goes RED; if it stays green the guard is vacuous.

Run:  python scripts/probe_carousel_thumb_srcset.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable

# (label, template, old bytes, new bytes)
PROBES = [
    ('P1 drop thumbnail srcset (the original bug)',
     'templates/product_detail.html',
     b'<img src="{{ img.src }}" srcset="{{ img.src|srcset }}" sizes="(max-width:768px) 24vw, 190px" alt="{{ img.alt }}"',
     b'<img src="{{ img.src }}" alt="{{ img.alt }}"'),

    ('P2 thumbnail sizes back to the slide value (1200px)',
     'templates/product_detail.html',
     b'srcset="{{ img.src|srcset }}" sizes="(max-width:768px) 24vw, 190px" alt="{{ img.alt }}"',
     b'srcset="{{ img.src|srcset }}" sizes="(max-width:768px) 100vw, (max-width:1200px) 90vw, 1200px" alt="{{ img.alt }}"'),

    ('P3 slide sizes back to 1200px for a 760px box',
     'templates/product_detail.html',
     b'srcset="{{ img.src|srcset }}" sizes="(max-width:768px) 92vw, 760px"',
     b'srcset="{{ img.src|srcset }}" sizes="(max-width:768px) 100vw, (max-width:1200px) 90vw, 1200px"'),

    ('P4 project carousel capped at 760px (full-width box)',
     'templates/project_detail.html',
     b'.ps-carousel {\n    position: relative;\n    width: 100%;',
     b'.ps-carousel {\n    position: relative;\n    max-width: 760px;\n    width: 100%;'),
]


def run_suite():
    proc = subprocess.run(
        [PY, 'manage.py', 'test', 'pages.tests_carousel_thumb_srcset', '-v', '0'],
        cwd=ROOT, capture_output=True, text=True)
    out = (proc.stdout or '') + (proc.stderr or '')
    return proc.returncode != 0, out


def main():
    baseline_rc, _ = run_suite()
    if baseline_rc != 0:
        print('BASELINE NOT GREEN — fix the suite before probing')
        return 1
    print('baseline: GREEN\n')

    ok = True
    for label, rel, old, new in PROBES:
        path = os.path.join(ROOT, rel)
        original = open(path, 'rb').read()
        n = original.count(old)
        if n != 1:
            print('PROBE BROKEN  %-48s anchor found %d times' % (label, n))
            ok = False
            continue
        try:
            open(path, 'wb').write(original.replace(old, new, 1))
            rc, out = run_suite()
            if rc == 0:
                print('PROBE FAILED (guard stayed green)  %s' % label)
                ok = False
            else:
                red = [ln for ln in out.splitlines()
                       if ln.startswith('FAIL:') or ln.startswith('ERROR:')]
                print('OK  %-48s -> %s' % (label, '; '.join(red) or 'RED'))
        finally:
            open(path, 'wb').write(original)
            assert open(path, 'rb').read() == original, 'restore failed: ' + rel

    print('\nresult:', 'ALL PROBES TURNED THE SUITE RED' if ok else 'PROBLEM')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
