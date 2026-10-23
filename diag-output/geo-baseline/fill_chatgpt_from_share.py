"""Fill the 13 ChatGPT cells of round 0 from the shared ChatGPT conversation.

Source: share link https://chatgpt.com/share/6adb738e-fe10-83e8-8e18-66ffabab93a6
(title "SolarOne Stadium Lights Overview"), extracted verbatim from the share
page flight data. Every value below is read from the actual answer text, not
inferred — except L1 rank/sentiment/spec_ok, which stay blank because the
Arabic answer body is not present in the share page (the Arabic query itself
arrived at ChatGPT mojibake'd).

Safety: asserts every non-ChatGPT row and every untouched ChatGPT row is
byte-identical to the pre-edit snapshot.
"""
import csv
import sys

sys.path.insert(0, '.')
import geo_round

CSV = 'rounds/round-0-2026-10-23.csv'

# query_id -> (mentioned, rank, sentiment, cited_own, spec_ok, competitors, notes)
DATA = {
    'B1': ('y', '', 'pos', 'y', 'y', '',
           'RT410 260W/32,500+lm 正确；功效写 125 而站内标 130lm/W（站内自身 32500/260=125 本就打架）；'
           'VSP 广播抗闪烁正确；引用 /products/'),
    'B2': ('y', '', 'pos', 'y', 'y', '',
           '2007/北京/50+国家/四大产品线全对；附独立核实免责声明；搜索结果混入同名太阳能公司（品牌撞车）'),
    'C1': ('y', '5', 'pos', 'y', 'y', 'Signify;Musco;Ephesus;Sportsbeams;HISHINE;SENSE',
           '中国工厂直采名单第 1（全场第 5/7）；RT410+VSP 型号正确；明示非排名'),
    'C2': ('y', '1', 'pos', 'y', 'y', 'HISHINE;SOGA',
           '三家首选第 1；引用 6 个 URL 含 /ar/ /es/ /fr/ /ru/ 语言首页'),
    'C3': ('y', '2', 'neu', 'y', 'y', 'HISHINE',
           'HISHINE 为主推荐；SolarOne 为次选对比（涉运动/体育场场景时）'),
    'C5': ('y', '1', 'pos', 'y', 'y', 'HISHINE;ZGSM;SCL;RC Lighting',
           '5 家短名单第 1；末尾追问球场类型（用户续答一轮，该轮不计入基线）'),
    'C6': ('y', '3', 'pos', 'y', 'y', 'SCL;HISHINE',
           '3 家推荐第 3；定位 international supply'),
    'L1': ('y', '', '', 'y', '', 'SCL;HISHINE',
           '阿拉伯语答案正文不在分享页（查询以乱码态到达 ChatGPT）；实体/图片区含 SolarOne；'
           '排名/口径待用户从原会话补填'),
    'L2': ('y', '3', 'neu', 'y', 'y', 'SCL;HISHINE',
           '3 家第 3；最终推荐 SCL+HISHINE；引用 /de/'),
    'L3': ('y', '3', 'neu', 'y', 'y', 'SCL;HISHINE',
           '3 家第 3；最终推荐 SCL+HISHINE'),
    'S1': ('n', '', '', 'n', '', '',
           '纯 AFC 标准解读，零品牌提及（连泛指供应商都未出现）'),
    'X1': ('y', '2', 'neu', 'y', 'y', 'Musco',
           '并排对比 Musco 优先；SolarOne 定位中国直供候选；引用 /products/'),
    'X3': ('y', '2', 'neu', 'y', 'y', 'Musco',
           '引用 12 个 URL 含 /about/ 与各语言页；邮箱+WhatsApp 与站内一致'),
}

with open(CSV, encoding='utf-8-sig', newline='') as fh:
    rows = list(csv.DictReader(fh))
snapshot = [dict(r) for r in rows]

filled = 0
for r in rows:
    if r['platform'] != 'ChatGPT':
        continue
    qid = r['query_id']
    assert qid in DATA, 'unexpected ChatGPT query row: %s' % qid
    m, rank, sent, cite, spec, comps, notes = DATA[qid]
    # refuse to overwrite existing measurements (idempotency + no-clobber)
    for col in ('mentioned', 'rank', 'sentiment', 'cited_own', 'spec_ok',
                'competitors_seen', 'model_version', 'notes'):
        assert not (r.get(col) or '').strip(), (
            'row %s/%s already has %s=%r — refusing to overwrite'
            % (r['platform'], qid, col, r[col]))
    r['mentioned'] = m
    r['rank'] = rank
    r['sentiment'] = sent
    r['cited_own'] = cite
    r['spec_ok'] = spec
    r['competitors_seen'] = comps
    r['notes'] = notes
    filled += 1

assert filled == 13, filled
for a, b in zip(snapshot, rows):
    if a['platform'] != 'ChatGPT':
        assert a == b, ('non-ChatGPT row changed', a, b)

with open(CSV, 'w', encoding='utf-8', newline='') as fh:
    w = csv.DictWriter(fh, fieldnames=geo_round.FIELDS)
    w.writeheader()
    w.writerows(rows)
print('filled %d ChatGPT cells; %d other rows untouched' % (filled, len(rows) - filled))
