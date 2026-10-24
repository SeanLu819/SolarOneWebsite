"""Fill DeepSeek round-0 cells from the share link (2026-10-24).

Source: https://chat.deepseek.com/share/8poyw8gocjhn24vm0k
fetched via https://chat.deepseek.com/api/v0/share/content?share_id=... through
the Clash proxy (sandbox direct connection gets HTTP 429; browser UA required
even via proxy). 24 messages = 12 human queries + 12 replies, sorted by
inserted_at. C1 and L2 were each run twice by the user; the latest answer of
each pair is recorded (both runs: no mention).

Only the (platform=DeepSeek) rows are touched; every other row must stay
value-identical (snapshot assert). Idempotent: identical re-run is a no-op;
differing data is refused unless --force.

Claim provenance: verified against seed_data.json + llm.txt (see
verify_ds_claims.py in .tmp_deepseek/). Headline facts:
- solaronelighting.com appears in ZERO of ~150 retrieved web pages across all
  12 turns (full retrieval lists available in the share payload).
- B1 identity correct (Beijing SolarOne, sportshow 2016/2017 exhibitor
  profiles) but all project/spec details trace to 2016-17 third-party pages
  (alighting B2B listing, sportshow, gov procurement) and MISS current seed:
  Workers' Stadium / UIBE / Dalian Yudon / France RT200-9M 3000-1800 lux /
  RT590ST 80-140W-100lm/W-IP65-2700-7000K. The France project is real (Roanne
  Halle Andre Vacheresse, basketball) but actual product is Vision Smart
  FL9M-720W with >2000 lux. No RT590ST/RT200-9M in the current line; current
  ingress rating is IP66.
- B2 leads with a credit-risk alert ("dishonest debtor / tax arrears /
  consumption restriction", sourced from Baidu Baike + Tianyancha). THREE
  distinct 信能阳光 entities appear in Tianyancha results; which one holds
  the risk records must be confirmed by the user. Three project claims are
  real (Royal Fighters -> Olympic Sports Center Gymnasium; speed skating ->
  National Snow and Ice Research Center; fencing -> 7th CISM Military World
  Games venue); "drafting national lighting standards" is not on-site.
- X1 is a one-sided negative comparison; "primarily basketball courts"
  contradicts the 22-project seed mix (football/tennis/baseball/ski/
  velodrome/karting/roadway/airport all present); "no FIFA certs" is true
  (site claims UL/DLC/GS/CE/IP66 only).
"""

import csv
import sys

sys.path.insert(0, '.')
import geo_round  # noqa: E402

CSV_PATH = 'rounds/round-0-2026-10-23.csv'

FILL = {
    'B1': {
        'mentioned': 'y',
        'rank': '',
        'sentiment': 'pos',
        'cited_own': 'n',
        'spec_ok': 'n',
        'competitors_seen': '',
        'model_version': '',
        'notes': '身份判定正确：锁定 Beijing SolarOne（北京信能阳光新能源科技有限公司，sportshow 2016/2017 参展档案佐证）并正确消歧美国 SolarOne Solutions；但全部细节来自 2016-17 年第三方页面而非本站：①工人体育馆篮球场 48×180W/200lux/0.65/60%节能 ②对外经贸大学篮球馆 100/200W/750lux/0.83/71% ③大连郁顿空气膜篮球馆 58×400W/500lux/0.76 ④法国 HD 转播篮球馆 RT200-9M 3000lux/1800lux——四个项目在 seed 22 个项目中全部 MISS；法国项目真实存在（Roanne Halle André Vacheresse 篮球馆）但实际用灯 Vision Smart FL9M-720W、结果 >2000 lux；RT590ST 规格（80-140W/100lm/W/2700-7000K/IP65/50000h）来自 alighting 旧 B2B  listing，seed 无 RT590ST/RT200-9M 型号且现行防护等级为 IP66；AI 自猜域名 site:solar-one.com.cn（2016 旧域）落空；solaronelighting.com 不在本轮 10 条检索结果中',
    },
    'B2': {
        'mentioned': 'y',
        'rank': '',
        'sentiment': 'neg',
        'cited_own': 'n',
        'spec_ok': 'n',
        'competitors_seen': '',
        'model_version': '',
        'notes': '🔴 全轮最严重发现——信用风险指控：答案以 Important Risk Alert 开头，称公司 listed as a dishonest debtor / tax arrears / consumption restriction orders（来源 Baidu Baike + Tianyancha，建议天眼查核实）。检索结果中存在三家「信能阳光」注册实体（新能源科技/节能科技/绿色照明器材科技），失信记录归属哪家必须由用户确认（llm.txt 注册名 Beijing Solarone Energy Technology Co., Ltd.）；三个项目引用真实（CBA 北京控股主场→seed 奥体馆、2022 冬奥速滑→国家冰雪运动研究中心、国家奥体击剑馆→七届军运会击剑馆）；「参与起草国家体育场馆照明标准」站内无此声明；solaronelighting.com 不在 12 条检索结果中',
    },
    'C1': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': 'Musco;Signify;Cree;Acuity;SITECO;Ephesus;Hubbell;Zumtobel;Eaton',
        'model_version': '',
        'notes': '两轮（用户重复提问）均零提及；名单来自 2026 市场报告（gminsights/168report/qyresearch）：国际五强 Musco/Signify/Cree/Acuity/Eaton + SITECO/Ephesus/Hubbell/Zumtobel；solaronelighting.com 不在 25 条检索结果中；同查询 ChatGPT 排 1/5',
    },
    'C3': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': 'Philips (Signify);OSRAM;CREE;WOSEN;iShineLux;UNIKE',
        'model_version': '',
        'notes': '零提及（连点名剔除都没有——与 Perplexity C3 的假否定互为镜像）：名单 Philips/OSRAM/CREE + 中国 WOSEN/iShineLux/UNIKE（200-1500W 170lm/W IP66）；FL-M 高杆线（FL6M 480W high-mast/airports、FL16M 1280W largest high-mast sites、天津滨海机场高杆改造新闻）在 DeepSeek 检索层完全不可见；solaronelighting.com 不在 12 条检索结果中',
    },
    'C5': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;Thorn;Schreder',
        'model_version': '',
        'notes': '零提及；答案以 FIFA 认证为硬筛选门槛（Signify/Musco FIFA Preferred Provider + Thorn Altis/Schréder OMNIBLAST FIFA Quality Pro）；我们无 FIFA 认证且站内不声称（体系 UL/DLC/GS/CE/IP66）；同查询 ChatGPT 排 1/5；solaronelighting.com 不在 13 条检索结果中',
    },
    'L1': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;MECREE;LEDLUCKY',
        'model_version': '',
        'notes': '查询以 GBK→UTF-8 乱码到达（同 ChatGPT L1 遭遇），DeepSeek 仍输出完整阿拉伯语答案可判定；值得注意：其自发子查询含 "SolarOne 北京信能阳光 体育场馆照明" 且检索结果摸到 sportshow/tianyancha/alighting 三页我们的档案，但答案层仍零提及（列 Signify/Musco/MECREE/LEDLUCKY）——检索层摸到过、答案层没写；solaronelighting.com 不在 29 条检索结果中',
    },
    'L2': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': 'Lumosa;Signify;Musco;LEDLUCKY;Lamp Shining;UNIKE;Huaxia Beidouxing;ROKEE',
        'model_version': '',
        'notes': '两轮（用户重复提问）均零提及；Lumosa（德国，60,000 盏/UEFA Level B 项目）+ FIFA 双雄 + 中国 LEDLUCKY/Lamp Shining/UNIKE/华夏北斗星/ROKEE；solaronelighting.com 不在 26 条检索结果中；同查询 Perplexity 亦未提及，仅 ChatGPT 提及 3/3',
    },
    'L3': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': 'Signify;Schreder;LEDLUCKY',
        'model_version': '',
        'notes': '零提及；FIFA 双雄（Signify 指定供应商/Schréder OMNIBLAST FIFA Quality Pro）+ 中国 LEDLUCKY（ArenaSharp E 480-2200W/VariFlood GEN II）；solaronelighting.com 不在 14 条检索结果中',
    },
    'S1': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': '',
        'model_version': '',
        'notes': '纯 AFC 标准解读并纠正查询前提：2200 lux 不对应任何 AFC 等级（Cat1 水平 2400/垂直 1200、Cat2 2000/1100、Cat3 1800/1000，2200 落在 Cat2 与 Cat1 之间），附韩国仁川联 2500+ lux 升级案例；零品牌提及（同 ChatGPT S1）；solaronelighting.com 不在 24 条检索结果中',
    },
    'X1': {
        'mentioned': 'y',
        'rank': '2',
        'sentiment': 'neg',
        'cited_own': 'n',
        'spec_ok': 'n',
        'competitors_seen': 'Musco',
        'model_version': '',
        'notes': '对比答案但单方面碾压：开篇 "not a comparison between peers"，Musco 优先（FIFA Preferred Provider/2026 世界杯 12/16 场馆/25 年保修）；我们被描述为 domestic Chinese manufacturer with project experience primarily in basketball courts and training facilities + 重复 B2 失信被执行人/欠税/限制消费令指控 + "highly questionable partner"；「primarily basketball」与 seed 22 项目矛盾（football/tennis/baseball/ski/velodrome/karting/roadway/airport 均在列）；「无 FIFA Quality Pro/Preferred Provider」属实（站内不声称）；「法国篮球馆 HD 转播」部分属实（Roanne 确是篮球馆，但型号 FL9M-720W 非 RT200-9M）；solaronelighting.com 不在 13 条检索结果中；同查询 ChatGPT 排 2/2 且 spec_ok=y——DeepSeek 是唯一给出负面对比结论的平台',
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
               if r['platform'] == 'DeepSeek' and r['query_id'] in FILL]
    assert len(targets) == 10, 'expected 10 DeepSeek target rows, got %d' % len(targets)
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
        print('%s: filled mentioned=%r rank=%r sentiment=%r cited_own=%r spec_ok=%r'
              % (qid, data['mentioned'], data['rank'], data['sentiment'],
                 data['cited_own'], data['spec_ok']))

    # every row outside the targets must be identical in values
    for before, after in zip(snapshot, rows):
        key = (before['platform'], before['query_id'])
        if key[0] == 'DeepSeek' and key[1] in FILL:
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
