"""Fill Perplexity round-0 cells from the user-pasted Computer-task thread.

Source: user paste of https://www.perplexity.ai/computer/tasks/d5a72574-...
(view=thread). The thread covers 4 of the 13 Perplexity cells; the free
quota ran out before the rest. Per platform quota discipline:

  * only rows (platform=Perplexity, query_id in {C6,L1,L2,L3}) are touched
  * every other row must stay byte-identical (snapshot assert)
  * idempotent: re-running with identical data is a no-op; differing data
    is refused unless --force
  * rank/sentiment/cited_own/spec_ok stay EMPTY where not measured --
    never guess (protocol: empty = not applicable, excluded from metrics)

Data provenance: specs verified against seed_data.json (RT410 260W /
130lm/W; VSP up to 4200W; M up to 1280W+).
"""

import csv
import sys

sys.path.insert(0, '.')
import geo_round  # noqa: E402

CSV_PATH = 'rounds/round-0-2026-10-23.csv'

MV = 'Perplexity Computer (agent task), model not shown'

FILL = {
    'C6': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'CHZ Lighting;MECREE;Hishine',
        'model_version': MV,
        'notes': 'Computer agent 任务（非逐条问答）；三家中国厂商均带项目案例，未含 SolarOne',
    },
    'L1': {
        'mentioned': 'y',
        'rank': '4',
        'sentiment': 'neu',
        'cited_own': '',
        'spec_ok': 'y',
        'competitors_seen': 'CHZ Lighting;MECREE;Hishine',
        'model_version': MV,
        'notes': '规格与站内全一致（RT410 130lm/W）；排第 4/4；引用链接未随粘贴提供，cited_own 待补',
    },
    'L2': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'Musco;Signify;Ephesus;Schreder;CHZ Lighting;MECREE;Hishine',
        'model_version': MV,
        'notes': '国际四强主导；"中国厂商"补充句仅提 CHZ/MECREE/Hishine',
    },
    'L3': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'Musco;Signify;Ephesus;Schreder;CHZ Lighting;MECREE;Hishine',
        'model_version': MV,
        'notes': '同 L2：国际四强主导；中国厂商补充句无 SolarOne',
    },
    'B2': {
        'mentioned': 'y',
        'rank': '1',
        'sentiment': 'pos',
        'cited_own': '',
        'spec_ok': 'n',
        'competitors_seen': '',
        'model_version': MV,
        'notes': '专段正面介绍+主动消歧美国 SolarOne Solutions；2007/500+项目/50+国家/产品规格/顺义地址全对；但项目清单含站内不存在的 Karlstad Sweden 与 Paris tennis，认证清单含站内不声明的 ISO9001/RoHS/TUV；引用链接未随粘贴提供',
    },
    'C1': {
        'mentioned': 'y',
        'rank': '5',
        'sentiment': 'neu',
        'cited_own': '',
        'spec_ok': 'na',
        'competitors_seen': 'Musco;Signify;Ephesus;Schreder',
        'model_version': MV,
        'notes': '四强名单后附注段提及：承认产品线但明言"国际场馆验证记录不如四强"；无引用规格数字（主体为别家，spec_ok=na）',
    },
    'C2': {
        'mentioned': 'y',
        'rank': '5',
        'sentiment': 'neu',
        'cited_own': '',
        'spec_ok': 'y',
        'competitors_seen': 'CHZ Lighting;AGC Lighting;MECREE;Hishine',
        'model_version': MV,
        'notes': '五家表格第 5；措辞"four verified + SolarOne from earlier"置于 verified 名单外；RT410 260W/VSP 4200W/M 1280W+ 与站内一致',
    },
}

MEASURED_COLS = ('mentioned', 'rank', 'sentiment', 'cited_own', 'spec_ok',
                 'competitors_seen', 'model_version', 'notes')


def main():
    force = '--force' in sys.argv
    with open(CSV_PATH, encoding='utf-8-sig', newline='') as fh:
        rows = list(csv.DictReader(fh))
    snapshot = [dict(r) for r in rows]

    targets = [r for r in rows
               if r['platform'] == 'Perplexity' and r['query_id'] in FILL]
    assert len(targets) == 7, 'expected 7 Perplexity target rows, got %d' % len(targets)
    by_id = {r['query_id']: r for r in targets}

    changed = 0
    for qid, data in FILL.items():
        row = by_id[qid]
        existing = {c: (row.get(c) or '').strip() for c in MEASURED_COLS}
        incoming = {c: (v or '').strip() for c, v in data.items()}
        if any(existing.values()):
            if existing == incoming:
                print('%s: already filled identically, skip' % qid)
                continue
            if not force:
                print('%s: ALREADY HAS DATA and it differs -- refusing. '
                      'Re-run with --force to overwrite.' % qid)
                return 1
            print('%s: overwriting existing data (--force)' % qid)
        row.update(data)
        changed += 1
        print('%s: filled mentioned=%r rank=%r sentiment=%r spec_ok=%r'
              % (qid, data['mentioned'], data['rank'], data['sentiment'],
                 data['spec_ok']))

    # every row outside the 4 targets must be byte-identical in values
    for before, after in zip(snapshot, rows):
        key = (before['platform'], before['query_id'])
        if key[0] == 'Perplexity' and key[1] in FILL:
            continue
        assert before == after, ('untouched row mutated: %s' % (key,))

    if not changed:
        print('nothing to do')
        return 0

    with open(CSV_PATH, 'w', encoding='utf-8', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=geo_round.FIELDS)
        w.writeheader()
        w.writerows(rows)
    print('wrote %d cell(s); all other rows untouched' % changed)
    return 0


if __name__ == '__main__':
    sys.exit(main())
