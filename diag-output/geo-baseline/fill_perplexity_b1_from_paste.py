"""Fill Perplexity round-0 cell B1 from the user-pasted thread (2026-10-24).

Source: user paste of the Perplexity Computer thread
(https://www.perplexity.ai/computer/tasks/d5a72574-...). Only the
(platform=Perplexity, query_id=B1) row is touched; every other row must
stay byte-identical (snapshot assert). Idempotent: re-running with
identical data is a no-op; differing data is refused unless --force.

Claim provenance: every factual claim cross-checked against seed_data.json
and llm.txt by verify_b1_claims.py -- company stats all FOUND on-site;
"Sweden"/"Canada" project references NOT on-site (fabricated) ->
spec_ok=n, same binary standard as B2 (Karlstad/Paris hallucination).
"""

import csv
import sys

sys.path.insert(0, '.')
import geo_round  # noqa: E402

CSV_PATH = 'rounds/round-0-2026-10-23.csv'

MV = 'Perplexity Computer (agent task), model not shown'

FILL = {
    'B1': {
        'mentioned': 'y',
        'rank': '1',
        'sentiment': 'pos',
        'cited_own': '',
        'spec_ok': 'n',
        'competitors_seen': '',
        'model_version': MV,
        'notes': '答案把我们拆成两个实体："SolarOne Lighting"（2007/500+ 项目/50+ 国家/five continents/50%+ 节能/5+ 保修，逐字取自站内 projects_subtitle 与 llm.txt）与 "Beijing Solarone Energy Technology"（称作 a related company with the same name）——实为同一家公司（品牌名 vs 注册名），AI 实体拆分是新 GEO 风险；项目引用大部分真实但名称压缩错位："Beijing Olympic stadium (fencing and swimming)" 实为武汉 CISM 击剑馆+北京英东游泳馆+北京奥林匹克体育中心体育馆的错拼，"China National Tennis Center" 对应国家奥林匹克体育中心网球馆/北京国际网球中心；幻觉：projects in Sweden, France, and Canada——法国真（Andre Vacheresse/Narbonne），瑞典、加拿大在 seed 22 项目+llm.txt 零命中；主动消歧 SolarOne Solutions（Needham MA，2019 被 Fonroche 收购）与 llm.txt 消歧段一致；引用链接未随粘贴提供，cited_own 待补',
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
    assert len(targets) == 1, 'expected 1 Perplexity target row, got %d' % len(targets)
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

    # every row outside the target must be byte-identical in values
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
