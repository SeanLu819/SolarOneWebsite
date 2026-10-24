"""Fill Perplexity round-0 cells C3/C5 from the user-pasted thread (2026-10-24).

Source: user paste of the Perplexity Computer thread
(https://www.perplexity.ai/computer/tasks/d5a72574-...). Only the
(platform=Perplexity, query_id in {C3,C5}) rows are touched; every other
row must stay byte-identical (snapshot assert). Idempotent: re-running with
identical data is a no-op; differing data is refused unless --force.

Claim provenance: C3's exclusion rationale ("SolarOne don't show a dedicated
high-mast product line on their sites") was checked against seed_data.json
with `grep -i 'mast' seed_data.json` -- the site DOES carry a high-mast line
(FL6M 480W "built for high-mast and large-area sites such as airports",
FL16M 1280W "the largest high-mast sites", FL12M 1000W "hohen Masten") plus
a Tianjin Binhai Airport high-mast retrofit news article
(slug low-cct-high-cri-high-mast-led-retrofit). The claim is a false
negative caused by retrieval failure -> spec_ok=n (mirror image of the
B1/B2 hallucinations).
"""

import csv
import sys

sys.path.insert(0, '.')
import geo_round  # noqa: E402

CSV_PATH = 'rounds/round-0-2026-10-23.csv'

MV = 'Perplexity Computer (agent task), model not shown'

FILL = {
    'C3': {
        'mentioned': 'y',
        'rank': '',
        'sentiment': 'neu',
        'cited_own': '',
        'spec_ok': 'n',
        'competitors_seen': 'AGC Lighting;MECREE;Hishine;CHZ Lighting',
        'model_version': MV,
        'notes': '三家中国高杆厂商表格（AGC HiMast 300/600/900W IP66/IK08、MECREE 100–5,000W 160lm/W、Hishine Hi-Robot+Hi-Titan 300–1,500W）；SolarOne 被点名但以 "don\'t show a dedicated high-mast product line on their sites" 明确踢出名单——该判断为假否定：seed 有整条 FL-M 高杆线（FL6M 480W "built for high-mast and large-area sites such as airports"、FL16M 1280W "the largest high-mast sites"、FL12M 1000W 德语描述 hohen Masten）+ 天津滨海机场高杆改造新闻案例（slug low-cct-high-cri-high-mast-led-retrofit）；这是检索失败（AI 没抓到站内已有内容而对买家宣称我们没有高杆产品线），与 B1/B2 幻觉互为镜像；mentioned=y 但不在名单，rank 留空；spec_ok=n；引用链接未随粘贴提供',
    },
    'C5': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'CHZ Lighting;MECREE;Hishine',
        'model_version': MV,
        'notes': '同查询 ChatGPT 排 1/5，Perplexity 零提及；三家均带供应商自报项目案例（MECREE：德国足球场 48×AFL 105×68m/25m 安装、玻利维亚 80×R580；Hishine：葡萄牙 480W、马来西亚 320W）；CHZ 附照明仿真支持；开头 "Continuing our China sourcing" 承接前序短名单（我们不在其中）；Computer agent 任务模式',
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
    assert len(targets) == 2, 'expected 2 Perplexity target rows, got %d' % len(targets)
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

    # every row outside the targets must be byte-identical in values
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
