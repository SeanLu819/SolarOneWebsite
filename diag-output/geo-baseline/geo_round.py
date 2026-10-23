#!/usr/bin/env python3
"""SolarOne GEO visibility baseline — round tooling.

Two subcommands:

  init     Create a new measurement round as a pre-filled CSV (one row per
           platform x query, measurement columns left blank).
  report   Read every rounds/round-*.csv, validate it, and write a markdown
           report with per-platform / per-cluster metrics, an AIVO-style
           composite and the delta against a reference round.

Stdlib only. No network. Everything the script knows about the query set
comes from queries.json sitting next to it.
"""

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROUNDS = HERE / 'rounds'
QUERIES_FILE = HERE / 'queries.json'
REPORT_FILE = HERE / 'report-latest.md'

# The eight platforms the 2026-10 diagnosis covers. index_family matters:
# retrieval-based platforms inherit a search index, so a Bing-family failure
# and a Google-family failure have different root causes.
PLATFORMS = [
    ('ChatGPT',    'bing'),
    ('Gemini',     'google'),
    ('Copilot',    'bing'),
    ('Perplexity', 'bing'),
    ('Claude',     'own'),
    ('Grok',       'own'),
    ('Meta AI',    'google'),
    ('DeepSeek',   'own'),
]

FIELDS = ['round', 'platform', 'query_id', 'query_text', 'lang', 'intent',
          'mentioned', 'rank', 'sentiment', 'cited_own', 'spec_ok',
          'competitors_seen', 'model_version', 'notes']

YES = {'y', 'yes', '1', 'true', 't'}
NO = {'n', 'no', '0', 'false', 'f'}
# "Not applicable" — e.g. spec_ok on a query where the AI answered about a
# different company. Same effect as blank for the maths: the cell is left out
# of the rate rather than counted as a failure.
NOT_MEASURED = {'', 'na', 'n/a', '-'}
SENTIMENT = {'pos': 'pos', 'positive': 'pos',
             'neu': 'neu', 'neutral': 'neu',
             'neg': 'neg', 'negative': 'neg'}

# AIVO weights — visibility dominates because a brand nobody mentions has no
# other dimension to score.
W_VISIBILITY, W_INFRA, W_COMPETITIVE, W_SENTIMENT = 0.40, 0.20, 0.25, 0.15

GRADES = ((90, '优秀'), (75, '良好'), (60, '一般'), (0, '较差'))


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def load_queries():
    data = json.loads(QUERIES_FILE.read_text(encoding='utf-8'))
    return {q['id']: q for q in data['queries']}


def grade(score):
    for threshold, label in GRADES:
        if score >= threshold:
            return label
    return '较差'


def norm_yesno(value, field, row_no, problems):
    v = (value or '').strip().lower()
    if v in NOT_MEASURED:
        return None
    if v in YES:
        return True
    if v in NO:
        return False
    problems.append('行 %s：%s=%r 无法识别（应为 y/n，留空或 na 表示不适用）'
                    % (row_no, field, value))
    return None


def norm_sentiment(value, row_no, problems):
    v = (value or '').strip().lower()
    if v == '':
        return None
    if v in SENTIMENT:
        return SENTIMENT[v]
    problems.append('行 %s：sentiment=%r 无法识别（应为 pos/neu/neg）'
                    % (row_no, value))
    return None


def norm_rank(value, row_no, problems):
    v = (value or '').strip()
    if v in NOT_MEASURED:
        return None
    try:
        n = int(v)
    except ValueError:
        problems.append('行 %s：rank=%r 不是整数' % (row_no, value))
        return None
    if not 1 <= n <= 10:
        problems.append('行 %s：rank=%d 超出 1-10（未进前 10 请留空）'
                        % (row_no, n))
        return None
    return n


# --------------------------------------------------------------------------- #
# init
# --------------------------------------------------------------------------- #

def cmd_init(args):
    queries = load_queries()
    ROUNDS.mkdir(exist_ok=True)
    stamp = args.date or date.today().isoformat()
    out = ROUNDS / ('round-%d-%s.csv' % (args.round, stamp))
    if out.exists() and not args.force:
        print('已存在：%s（加 --force 覆盖）' % out)
        return 1

    selected = [q for q in queries.values()
                if args.extended or q.get('core')]
    selected.sort(key=lambda q: q['id'])

    with out.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        for platform, _family in PLATFORMS:
            for q in selected:
                writer.writerow({
                    'round': args.round,
                    'platform': platform,
                    'query_id': q['id'],
                    'query_text': q['text'],
                    'lang': q['lang'],
                    'intent': q['intent'],
                })

    total = len(PLATFORMS) * len(selected)
    print('已生成 %s' % out)
    print('  %d 个平台 x %d 条查询 = %d 行待测' % (len(PLATFORMS), len(selected), total))
    print('  把每一行的 query_text 原样贴进对应平台，然后填 mentioned / rank / '
          'sentiment / cited_own / spec_ok / competitors_seen / model_version')
    return 0


# --------------------------------------------------------------------------- #
# report
# --------------------------------------------------------------------------- #

def read_rounds(queries):
    """Return (rows, problems). rows are dicts with normalised fields."""
    rows, problems = [], []
    files = sorted(ROUNDS.glob('round-*.csv'))
    if not files:
        return rows, ['rounds/ 下没有任何 round-*.csv，先跑 init']

    valid_platforms = {p for p, _ in PLATFORMS}
    seen = set()

    for path in files:
        # utf-8-sig: Excel writes a BOM, and without this the first column
        # name becomes '\ufeffround' and every round label reads as empty.
        with path.open(encoding='utf-8-sig', newline='') as fh:
            for offset, raw in enumerate(csv.DictReader(fh), start=2):
                row_no = '%s:%d' % (path.name, offset)
                platform = (raw.get('platform') or '').strip()
                qid = (raw.get('query_id') or '').strip()
                round_label = (raw.get('round') or '').strip()
                if not round_label:
                    problems.append('%s：round 列为空（表头是否被 BOM 污染？）'
                                    % row_no)
                    continue
                if platform not in valid_platforms:
                    problems.append('%s：platform=%r 不在 8 平台清单里'
                                    % (row_no, platform))
                    continue
                if qid not in queries:
                    problems.append('%s：query_id=%r 不在 queries.json 里'
                                    % (row_no, qid))
                    continue
                key = (raw.get('round'), platform, qid)
                if key in seen:
                    problems.append('%s：round/platform/query 重复' % row_no)
                seen.add(key)

                mentioned = norm_yesno(raw.get('mentioned'), 'mentioned',
                                       row_no, problems)
                if mentioned is None:
                    continue          # not measured — excluded from every rate

                rows.append({
                    'round': round_label,
                    'platform': platform,
                    'query_id': qid,
                    'intent': queries[qid]['intent'],
                    'lang': queries[qid]['lang'],
                    'mentioned': mentioned,
                    'rank': norm_rank(raw.get('rank'), row_no, problems),
                    'sentiment': norm_sentiment(raw.get('sentiment'), row_no,
                                                problems),
                    'cited_own': norm_yesno(raw.get('cited_own'), 'cited_own',
                                            row_no, problems),
                    'spec_ok': norm_yesno(raw.get('spec_ok'), 'spec_ok',
                                          row_no, problems),
                    'competitors': [c.strip() for c in
                                    re.split(r'[;,]\s*',
                                             (raw.get('competitors_seen')
                                              or '').strip())
                                    if c.strip()],
                    'model_version': (raw.get('model_version') or '').strip(),
                })
    return rows, problems


def scope_metrics(rows, expected_cells=None):
    """Compute the metric block for one set of measured rows."""
    out = {'measured': len(rows)}
    if expected_cells:
        out['expected'] = expected_cells
        out['coverage'] = (len(rows) / expected_cells) if expected_cells else 0.0
    if not rows:
        return out

    mentions = [r for r in rows if r['mentioned']]
    out['mentions'] = len(mentions)
    out['mention_rate'] = len(mentions) / len(rows)

    ranked = [r for r in mentions if r['rank'] is not None]
    out['ranked'] = len(ranked)
    out['mean_rank'] = (sum(r['rank'] for r in ranked) / len(ranked)
                        if ranked else None)
    # 1st place scores 1.0, 10th scores 0.1, unranked mention scores 0.
    out['rank_score'] = (sum((11 - r['rank']) / 10 for r in ranked)
                         / len(mentions)) if mentions else 0.0

    cited = [r for r in mentions if r['cited_own'] is not None]
    out['citation_rate'] = (sum(1 for r in cited if r['cited_own']) / len(cited)
                            if cited else None)

    spec = [r for r in mentions if r['spec_ok'] is not None]
    out['spec_rate'] = (sum(1 for r in spec if r['spec_ok']) / len(spec)
                        if spec else None)

    sent = [r for r in mentions if r['sentiment'] is not None]
    out['sentiment_n'] = len(sent)
    for key in ('pos', 'neu', 'neg'):
        out[key] = sum(1 for r in sent if r['sentiment'] == key)
    out['sentiment_score'] = ((out['pos'] + 0.5 * out['neu']) / len(sent)
                              if sent else None)

    # Share of voice: of the answers that named us OR any competitor, how
    # many named us.
    contested = [r for r in rows if r['mentioned'] or r['competitors']]
    out['contested'] = len(contested)
    out['sov'] = (len(mentions) / len(contested)) if contested else None

    visibility = 100 * (0.7 * out['mention_rate'] + 0.3 * out['rank_score'])
    infra_parts = [v for v in (out['citation_rate'], out['spec_rate'])
                   if v is not None]
    infra = 100 * (sum(infra_parts) / len(infra_parts)) if infra_parts else 0.0
    competitive = 100 * out['sov'] if out['sov'] is not None else 0.0
    sentiment = (100 * out['sentiment_score']
                 if out['sentiment_score'] is not None else 0.0)
    out['aivo'] = (W_VISIBILITY * visibility + W_INFRA * infra
                   + W_COMPETITIVE * competitive + W_SENTIMENT * sentiment)
    out['aivo_parts'] = {'V': visibility, 'I': infra,
                         'C': competitive, 'S': sentiment}
    return out


def pct(value):
    return '—' if value is None else '%.0f%%' % (100 * value)


def num(value, fmt='%.2f'):
    return '—' if value is None else fmt % value


def render_report(all_rows, problems, queries, ref_round):
    rounds = sorted({r['round'] for r in all_rows},
                    key=lambda s: (len(s), s))
    core_ids = [q['id'] for q in queries.values() if q.get('core')]
    expected_core = len(PLATFORMS) * len(core_ids)

    lines = []
    add = lines.append
    add('# SolarOne GEO 可见度基线报告')
    add('')
    add('- 生成时间：%s' % date.today().isoformat())
    add('- 数据轮次：%s' % (', '.join(rounds) if rounds else '无'))
    add('- 查询集：%d 条（核心 %d 条 / 扩展 %d 条）'
        % (len(queries), len(core_ids), len(queries) - len(core_ids)))
    add('- 单轮满覆盖 = 8 平台 x %d 核心查询 = %d 格' % (len(core_ids),
                                                    expected_core))
    add('')

    if problems:
        add('## ⚠️ 数据问题（先修这些再信指标）')
        add('')
        for p in problems:
            add('- %s' % p)
        add('')

    latest = rounds[-1] if rounds else None
    latest_rows = [r for r in all_rows if r['round'] == latest]

    add('## 总体（%s）' % latest)
    add('')
    m = scope_metrics(latest_rows, expected_core)
    add('| 指标 | 值 |')
    add('| --- | --- |')
    add('| 已测格子 | %d / %d（覆盖 %s） | '
        % (m['measured'], expected_core, pct(m.get('coverage'))))
    add('| 品牌被提及 | %d / %d = **%s** | '
        % (m['mentions'], m['measured'], pct(m['mention_rate'])))
    add('| 平均排名 | %s | ' % num(m['mean_rank']))
    add('| 引用本站域名 | %s | ' % pct(m['citation_rate']))
    add('| 引用数据准确 | %s | ' % pct(m['spec_rate']))
    add('| 正面/中立/负面 | %d / %d / %d | ' % (m['pos'], m['neu'], m['neg']))
    add('| 声量份额（对竞品） | %s | ' % pct(m['sov']))
    add('| **AIVO 综合分** | **%.1f / 100（%s）** | '
        % (m['aivo'], grade(m['aivo'])))
    add('')
    add('AIVO = 可见度 40%% + 基建 20%% + 竞争优势 25%% + 舆情 15%%。'
        '本批：V %.1f / I %.1f / C %.1f / S %.1f。'
        % (m['aivo_parts']['V'], m['aivo_parts']['I'],
           m['aivo_parts']['C'], m['aivo_parts']['S']))
    add('')

    # ---- per platform ----
    add('## 分平台')
    add('')
    add('| 平台 | 索引族 | 已测 | 提及率 | 平均排名 | 引用本站 | 数据准确 | 声量份额 | AIVO |')
    add('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    families = dict(PLATFORMS)
    for platform, _f in PLATFORMS:
        rows = [r for r in latest_rows if r['platform'] == platform]
        if not rows:
            add('| %s | %s | 0 | — | — | — | — | — | — | '
                % (platform, families[platform]))
            continue
        pm = scope_metrics(rows)
        add('| %s | %s | %d | %s | %s | %s | %s | %s | %.1f |'
            % (platform, families[platform], pm['measured'],
               pct(pm['mention_rate']), num(pm['mean_rank']),
               pct(pm['citation_rate']), pct(pm['spec_rate']),
               pct(pm['sov']), pm['aivo']))
    add('')

    # ---- per intent ----
    add('## 分查询意图')
    add('')
    add('| 意图 | 已测 | 提及率 | 平均排名 | 引用本站 | 声量份额 | AIVO |')
    add('| --- | --- | --- | --- | --- | --- | --- |')
    for intent in ('brand', 'category', 'spec', 'comparison', 'local'):
        rows = [r for r in latest_rows if r['intent'] == intent]
        if not rows:
            continue
        im = scope_metrics(rows)
        add('| %s | %d | %s | %s | %s | %s | %.1f |'
            % (intent, im['measured'], pct(im['mention_rate']),
               num(im['mean_rank']), pct(im['citation_rate']),
               pct(im['sov']), im['aivo']))
    add('')

    # ---- per query ----
    add('## 分查询')
    add('')
    add('| 查询 | 意图 | 语言 | 已测 | 提及 | 最好排名 | 引用本站 |')
    add('| --- | --- | --- | --- | --- | --- | --- |')
    for qid in sorted(queries):
        rows = [r for r in latest_rows if r['query_id'] == qid]
        if not rows:
            continue
        hits = [r for r in rows if r['mentioned']]
        ranks = [r['rank'] for r in hits if r['rank'] is not None]
        cited = [r for r in hits if r['cited_own'] is True]
        add('| %s %s | %s | %s | %d | %d/%d | %s | %d |'
            % (qid, queries[qid]['text'][:38], queries[qid]['intent'],
               queries[qid]['lang'], len(rows), len(hits), len(rows),
               min(ranks) if ranks else '—', len(cited)))
    add('')

    # ---- delta ----
    ref = ref_round or (rounds[0] if len(rounds) > 1 else None)
    if ref and ref != latest:
        ref_rows = [r for r in all_rows if r['round'] == ref]
        rm = scope_metrics(ref_rows)
        add('## 环比（%s → %s）' % (ref, latest))
        add('')
        add('| 指标 | %s | %s | 变化 |' % (ref, latest))
        add('| --- | --- | --- | --- |')
        for label, key, fmt in (('提及率', 'mention_rate', pct),
                                ('平均排名', 'mean_rank', num),
                                ('引用本站', 'citation_rate', pct),
                                ('数据准确', 'spec_rate', pct),
                                ('声量份额', 'sov', pct),
                                ('AIVO', 'aivo', lambda v: '%.1f' % v)):
            a, b = rm.get(key), m.get(key)
            if a is None or b is None:
                delta = '—'
            else:
                delta = '%+.2f' % (b - a)
            add('| %s | %s | %s | %s |'
                % (label, fmt(a) if a is not None else '—',
                   fmt(b) if b is not None else '—', delta))
        add('')
    elif len(rounds) > 1:
        add('## 环比')
        add('')
        add('参照轮次未指定；用 `--ref <round>` 指定，或删除多余轮次。')
        add('')

    add('## 读数提醒')
    add('')
    add('- 覆盖率不足 100%% 时，上面的比率只代表「已测的那部分」，不能当全量结论。')
    add('- AI 回答有随机性：同一查询两次结果可能不同，关键查询请跑 2 次取较差值。')
    add('- AIVO 只在本项目内部跨轮次可比；不要和别家公司的分数比。')
    add('')
    return '\n'.join(lines)


def cmd_report(args):
    queries = load_queries()
    rows, problems = read_rounds(queries)
    if not rows:
        print('没有可用的已测数据。')
        for p in problems:
            print('  - %s' % p)
        return 1
    text = render_report(rows, problems, queries, args.ref)
    REPORT_FILE.write_text(text, encoding='utf-8')
    print('报告已写入 %s' % REPORT_FILE)
    print('')

    rounds = sorted({r['round'] for r in rows}, key=lambda s: (len(s), s))
    latest = rounds[-1]
    latest_rows = [r for r in rows if r['round'] == latest]
    core_ids = [q['id'] for q in queries.values() if q.get('core')]
    m = scope_metrics(latest_rows, len(PLATFORMS) * len(core_ids))
    print('轮次 %s：已测 %d 格（核心满覆盖 %d）' %
          (latest, m['measured'], len(PLATFORMS) * len(core_ids)))
    print('  提及率 %s | 平均排名 %s | 引用本站 %s | 数据准确 %s | 声量 %s'
          % (pct(m['mention_rate']), num(m['mean_rank']),
             pct(m['citation_rate']), pct(m['spec_rate']), pct(m['sov'])))
    print('  AIVO %.1f / 100（%s）  V %.1f / I %.1f / C %.1f / S %.1f'
          % (m['aivo'], grade(m['aivo']), m['aivo_parts']['V'],
             m['aivo_parts']['I'], m['aivo_parts']['C'],
             m['aivo_parts']['S']))
    if problems:
        print('  ⚠️ %d 条数据问题，见报告开头' % len(problems))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                    formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)

    p_init = sub.add_parser('init', help='生成新一轮待测 CSV')
    p_init.add_argument('--round', type=int, required=True)
    p_init.add_argument('--date', help='YYYY-MM-DD，默认今天')
    p_init.add_argument('--extended', action='store_true',
                        help='连扩展查询一起生成（默认只生成核心查询）')
    p_init.add_argument('--force', action='store_true', help='覆盖已存在文件')
    p_init.set_defaults(func=cmd_init)

    p_rep = sub.add_parser('report', help='汇总所有轮次并生成报告')
    p_rep.add_argument('--ref', help='环比参照轮次，默认最早一轮')
    p_rep.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
