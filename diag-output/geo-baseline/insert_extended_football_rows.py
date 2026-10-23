#!/usr/bin/env python3
"""Insert the two extended football queries (C6, X3) into round-0 CSV.

`geo_round.py init --extended` would generate every query on every platform
(21 x 8 = 168 rows), but PROTOCOL.md says extended queries only need the
top-3 platforms. So the core CSV comes from init (8 platforms x 11 core
queries = 88 rows) and this script adds the six extended rows by hand, in
the same per-platform, query-id-sorted order init uses.

Idempotent: skips (platform, query_id) pairs already present.
"""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV = HERE / 'rounds' / 'round-0-2026-10-23.csv'

TOP3 = ['ChatGPT', 'Gemini', 'Perplexity']
EXT = [
    ('C6', 'football field lighting manufacturer China', 'en', 'category'),
    ('X3', 'Musco vs SolarOne football field lighting', 'en', 'comparison'),
]


def main():
    with CSV.open(encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.reader(fh))
    header, data = rows[0], rows[1:]

    existing = {(r[1], r[2]) for r in data}
    platforms = []
    for r in data:
        if not platforms or platforms[-1] != r[1]:
            platforms.append(r[1])

    out = [header]
    added = 0
    for platform in platforms:
        block = [r for r in data if r[1] == platform]
        if platform in TOP3:
            for qid, text, lang, intent in EXT:
                if (platform, qid) in existing:
                    continue
                block.append(['0', platform, qid, text, lang, intent,
                              '', '', '', '', '', '', '', ''])
                added += 1
        block.sort(key=lambda r: r[2])
        out.extend(block)

    with CSV.open('w', encoding='utf-8', newline='') as fh:
        csv.writer(fh).writerows(out)

    # --- verify ---
    with CSV.open(encoding='utf-8-sig', newline='') as fh:
        check = list(csv.DictReader(fh))
    assert len(check) == 94, len(check)
    assert len({(r['platform'], r['query_id']) for r in check}) == 94, 'dupes'
    assert not any((r.get('mentioned') or '').strip() for r in check), \
        'measurement data present -- refusing to leave it half-written'
    print('round-0 CSV OK: %d data rows (88 core + 6 extended), '
          '%d added this run' % (len(check), added))


if __name__ == '__main__':
    main()
