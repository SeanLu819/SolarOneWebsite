"""Mutation probes for LlmTxtEntityIdentityAndHighMastTests.

Each probe mutates a shipped file, runs the ONE guard that is supposed to
catch it, asserts the guard went red, then restores the original bytes in a
`finally` block. Restoration is byte-level on purpose: `git checkout` would
also revert unrelated work (iron rule 3).

A probe that stays green means the guard is decorative, not that the code is
wrong. Prints RED / RESTORED per probe and exits non-zero on any surprise.
"""
import os
import subprocess
import sys

PYTHON = 'E:/Python/python3/python.exe'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = 'pages.tests_release_metadata.LlmTxtEntityIdentityAndHighMastTests.'

PROBES = (
    # (file, old bytes, new bytes, guard that must fail)
    ('llm.txt', b'are ONE entity', b'are one entity',
     TARGET + 'test_who_section_declares_one_entity'),
    ('llm.txt', b'FL6M (480W)', b'FL6M (500W)',
     TARGET + 'test_high_mast_wattages_match_seed'),
    ('llm.ar.txt', b'91110116663729775X', b'91110116663739775X',
     TARGET + 'test_arabic_variant_mirrors_the_identity_claim'),
    ('templates/base.html', b'company are one entity', b'company are an entity',
     TARGET + 'test_jsonld_declares_the_single_entity'),
)

failures = []


def run(guard):
    result = subprocess.run(
        [PYTHON, 'manage.py', 'test', guard, '-v', '0'],
        cwd=REPO, capture_output=True, text=True)
    return result.returncode


for name, old, new, guard in PROBES:
    path = os.path.join(REPO, name)
    with open(path, 'rb') as handle:
        original = handle.read()

    if original.count(old) != 1:
        failures.append('%s: anchor %r found %d times'
                        % (name, old.decode('utf-8', 'replace'),
                           original.count(old)))
        continue

    try:
        with open(path, 'wb') as handle:
            handle.write(original.replace(old, new, 1))
        mutated = run(guard)
        if mutated == 0:
            failures.append('%s: guard stayed GREEN after mutation (%s)'
                            % (name, guard.rsplit('.', 1)[-1]))
            print('GREEN (BAD)  %-22s %s' % (name, guard.rsplit('.', 1)[-1]))
        else:
            print('RED (ok)     %-22s %s' % (name, guard.rsplit('.', 1)[-1]))
    finally:
        with open(path, 'wb') as handle:
            handle.write(original)

    restored = run(guard)
    if restored != 0:
        failures.append('%s: guard still RED after restore (%s)'
                        % (name, guard.rsplit('.', 1)[-1]))
        print('STILL RED    %-22s %s' % (name, guard.rsplit('.', 1)[-1]))
    else:
        print('RESTORED     %-22s %s' % (name, guard.rsplit('.', 1)[-1]))

print()
if failures:
    print('PROBE FAILURES:')
    for item in failures:
        print('  -', item)
    sys.exit(1)
print('All %d probes behaved: RED under mutation, GREEN after restore.'
      % len(PROBES))
