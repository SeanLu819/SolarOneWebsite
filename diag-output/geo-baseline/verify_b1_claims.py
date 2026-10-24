"""Verify Perplexity B1 ("SolarOne stadium lights") claims against seed + llm.txt.

Paste source: user paste of the Perplexity Computer thread, 2026-10-24.
Every factual claim in the answer is checked against the two on-site
authoritative sources (seed_data.json / llm.txt). Prints a verdict table
used to justify the spec_ok cell in rounds/round-0-2026-10-23.csv.
"""

import json
import re
import sys

SEED = 'seed_data.json'
LLM = 'llm.txt'


def main():
    with open(SEED, encoding='utf-8') as fh:
        seed = json.load(fh)
    with open(LLM, encoding='utf-8') as fh:
        llm = fh.read()

    projects = seed['projects']
    print('seed project count: %d' % len(projects))

    # country-level rollup of project locations
    locs = {}
    for p in projects:
        loc = (p.get('location') or '(none)').strip()
        locs.setdefault(loc, []).append(p.get('title') or p.get('slug'))
    print('\n-- project locations --')
    for loc in sorted(locs):
        print('  %-28s %s' % (loc, '; '.join(locs[loc])))

    # whole seed serialized (includes projects_subtitle etc., not just the
    # projects array -- "five continents" lives in seed['projects_subtitle'])
    blob = json.dumps(seed, ensure_ascii=False)
    low = blob.lower()
    llm_low = llm.lower()

    def seed_has(term):
        return term.lower() in low

    def llm_has(term):
        return term.lower() in llm_low

    checks = [
        # (claim, on-site evidence, verdict-when-true)
        ('company founded 2007', llm_has('2007'), None),
        ('500+ projects', bool(re.search(r'500\s*\+', llm)), None),
        ('50+ countries', bool(re.search(r'50\s*\+\s*(countr|market)', llm)), None),
        ('five continents', llm_has('five continents') or llm_has('5 continents') or seed_has('five continents'), None),
        ('50%+ energy savings', bool(re.search(r'50\s*%', llm)) or bool(re.search(r'50\s*%\s*(energy|saving)', blob, re.I)), None),
        ('5+ year warranty', bool(re.search(r'5\s*\+\s*(year|yr)', llm, re.I)), None),
        ('"precision optics" wording', llm_has('precision optic') or seed_has('precision optic'), None),
        ('"modular" wording', seed_has('modular'), None),
        ('"Olympic training centers"', llm_has('olympic training') or seed_has('olympic training'), None),
        ('"community football pitches"', llm_has('community football') or seed_has('community football'), None),
        ('fencing venue project', seed_has('fencing'), None),
        ('natatorium / swimming project', seed_has('natatorium') or seed_has('swimming'), None),
        ('tennis project', seed_has('tennis'), None),
        ('olympic project (gymnasium)', seed_has('olympic'), None),
        ('France project', seed_has('france') or llm_has('france'), None),
        ('Sweden project', seed_has('sweden') or llm_has('sweden'), None),
        ('Canada project', seed_has('canada') or llm_has('canada'), None),
        ('"SolarOne Solutions" / Fonroche disambiguation', llm_has('solarone solutions') or llm_has('fonroche'), None),
    ]

    print('\n-- claim-by-claim --')
    bad = []
    for name, ok, _ in checks:
        print('  %-46s %s' % (name, 'FOUND on-site' if ok else 'NOT on-site'))
        if not ok:
            bad.append(name)
    print('\nclaims with NO on-site evidence: %s' % (bad or 'none'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
