#!/usr/bin/env python3
"""Add the football cluster to the round-0 query set (2026-10-23).

The original 18 queries measured the stadium intent seven ways (C1, C2, S1,
S3, X1, X2 + brand B1) and tennis once (C4), but football -- the buyer
question behind /projects/football/ -- not at all. Adds:

  C5  core      -- football cluster, full 8 platforms (main battlefield)
  C6  extended  -- US "field" vs "stadium" phrasing, top-3 platforms only
  X3  extended  -- Musco head-to-head on football, top-3 platforms only

Insertion is positional: C5/C6 after C4, X3 after X2, keeping the file's
id-clustered order. Idempotent: refuses to run if C5 is already there.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
QF = HERE / 'queries.json'

C5 = {
    "id": "C5",
    "text": "football stadium LED lighting supplier",
    "lang": "en",
    "intent": "category",
    "core": True,
    "target": "/projects/football/",
    "watch": ["Musco"],
    "notes": "Football cluster, added 2026-10-23: the round-0 set had stadium (7 queries) and tennis (1) but zero football. /projects/football/'s title carries the exact term 'Football Stadium Lighting' -- this measures whether an AI actually cites it."
}
C6 = {
    "id": "C6",
    "text": "football field lighting manufacturer China",
    "lang": "en",
    "intent": "category",
    "core": False,
    "target": "/projects/football/",
    "watch": [],
    "notes": "Extended. US-leaning 'field' phrasing vs C5's 'stadium' -- tests the term split on the same target."
}
X3 = {
    "id": "X3",
    "text": "Musco vs SolarOne football field lighting",
    "lang": "en",
    "intent": "comparison",
    "core": False,
    "target": "/projects/football/",
    "watch": ["Musco"],
    "notes": "Extended. Football head-to-head; X1 already covers the comparison pattern on stadium."
}


def insert_after(queries, after_id, new):
    for i, q in enumerate(queries):
        if q['id'] == after_id:
            queries[i + 1:i + 1] = new
            return
    raise SystemExit('anchor %s not found' % after_id)


def main():
    data = json.loads(QF.read_text(encoding='utf-8'))
    queries = data['queries']
    if any(q['id'] == 'C5' for q in queries):
        raise SystemExit('C5 already present -- nothing to do')

    insert_after(queries, 'C4', [C5, C6])
    insert_after(queries, 'X2', [X3])

    meta = data['meta']
    meta['version'] = '1.1'
    meta['updated'] = '2026-10-23'
    notes = meta['notes']
    for i, n in enumerate(notes):
        if n.startswith('core=true marks'):
            notes[i] = (n.replace('the 10 queries', 'the 11 queries')
                        .replace('(80 cells)', '(88 cells)'))
    notes.append(
        'Football cluster gap (2026-10-23): the original set measured stadium '
        'intent seven ways and tennis once, but football -- the buyer question '
        'behind /projects/football/ -- not at all. C5 is core (full 8 '
        'platforms); C6 tests the US "field" vs "stadium" phrasing and X3 the '
        'Musco head-to-head, both extended (top-3 platforms).')

    QF.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n',
                  encoding='utf-8')

    # --- verify by re-reading from disk ---
    data2 = json.loads(QF.read_text(encoding='utf-8'))
    qs2 = data2['queries']
    assert len(qs2) == 21, len(qs2)
    assert len({q['id'] for q in qs2}) == 21, 'duplicate ids'
    core = [q['id'] for q in qs2 if q.get('core')]
    assert len(core) == 11, core
    order = [q['id'] for q in qs2]
    assert order.index('C4') < order.index('C5') < order.index('C6') \
        < order.index('S1'), order
    assert order.index('X2') < order.index('X3') < order.index('L1'), order
    assert data2['meta']['version'] == '1.1'
    print('queries.json OK: 21 queries (11 core / 10 extended), '
          'order C4<C5<C6<S1, X2<X3<L1')


if __name__ == '__main__':
    main()
