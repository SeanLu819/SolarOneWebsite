"""Fill all 11 Grok round-0 cells from the share link (2026-10-24).

Source: https://grok.com/share/bGVnYWN5LWNvcHk_849802a6-ce0e-4f0f-baa4-5e468a2799d9
fetched via https://grok.com/rest/app-chat/share_links_data/{id} through the
Clash proxy (sandbox direct connection is blocked). 22 responses = 11 human
queries + 11 grok-3 replies, sorted by createTime. Only the
(platform=Grok) rows are touched; every other row must stay byte-identical
(snapshot assert). Idempotent: identical re-run is a no-op; differing data
is refused unless --force.

Claim provenance: specs verified against seed_data.json (2007 / 500+ / 50+ /
80~1280W+ / 130lm/W / VSP 4200W / beam options 12-18-30-50 in model-code
legend / Vision Strobe Protection / UL+DLC / Olympic projects). The B1
answer is about the US namesake SolarOne Solutions (Fonroche) -> spec_ok=n
per the manual's B1 collision precedent.
"""

import csv
import sys

sys.path.insert(0, '.')
import geo_round  # noqa: E402

CSV_PATH = 'rounds/round-0-2026-10-23.csv'

MV = 'grok-3'

FILL = {
    'B1': {
        'mentioned': 'y',
        'rank': '',
        'sentiment': 'neu',
        'cited_own': 'n',
        'spec_ok': 'n',
        'competitors_seen': '',
        'model_version': MV,
        'notes': '答案主体是美国 SolarOne Solutions（2004 马萨诸塞，2019 被 Fonroche 收购后 rebrand Fonroche Lighting America，离网太阳能路灯）；我们（Beijing Solarone Energy Technology）仅在结尾注脚被提及一次且描述准确（LED sports field/high-mast lights, grid-powered），但无规格无链接；6 条内联引用全部指向美国方域名（devex/altenergymag/edisonreport/fonrochesolarlighting 等）；品牌撞车惨败——同查询 ChatGPT/Perplexity 均提及我们',
    },
    'B2': {
        'mentioned': 'y',
        'rank': '1',
        'sentiment': 'pos',
        'cited_own': 'y',
        'spec_ok': 'y',
        'competitors_seen': '',
        'model_version': MV,
        'notes': '答案正确锁定 solaronelighting.com：2007/500+ 项目/50+ 国家/5+ 保修/50%+ 节能/M 系列 80W→1280W+（16 模组）/130lm/W/VSP 4200W+Vision Strobe Protection/光学 12-18-30-50°/UL+DLC/奥运项目（击剑游泳网球）全部与 seed 核对一致；主动消歧美国 SolarOne Solutions 准确；正文给出 solaronelighting.com 链接；但仍有实体拆分："A related Chinese manufacturer is Beijing Solarone Energy Technology... The solaronelighting.com brand appears closely aligned"——把品牌名和注册名当两家（同 Perplexity B1）',
    },
    'C1': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': 'n',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;Cree;Acuity;Eaton;Zumtobel;Thorn;Hubbell;GE Current;Schreder;GS Light;Lepower;LEDYi;Romanso',
        'model_version': MV,
        'notes': '全球五强表（Signify/Musco/Cree/Acuity/Eaton）+ 中国段仅 GS Light/Lepower/LEDYi/Romanso，无 SolarOne；3 条内联引用无本站；本站域名不在本轮 35 条检索结果中',
    },
    'C2': {
        'mentioned': 'y',
        'rank': '',
        'sentiment': 'neu',
        'cited_own': '',
        'spec_ok': 'na',
        'competitors_seen': 'Huadian;Mecree;GS Light;LEDYi;Romanso;ONOR;Hishine;Benwei;RC Lighting;Lepower;AOK LED;ZGSM;Topsports;SOGA;Leyond',
        'model_version': MV,
        'notes': '十家中国供应商表格（Huadian/Mecree/GS Light/LEDYi/Romanso/ONOR/Hishine/Benwei/RC 等）+ 末尾补一段 "Earlier in related searches, Beijing Solarone Energy Technology (and the solaronelighting.com brand) also appears as a supplier of high-power LED sports field and stadium floodlights with project references including Olympic-related venues"——提及但不在表内、无规格数字、注明来自前序检索；同查询 ChatGPT 排 1/5',
    },
    'C3': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;Acuity;Eaton;Cree;Hubbell;Hishine;ZGSM;RC Lighting;ONOR;LEDYi;Golon;CHZ Lighting;Haichang Optotech;LEDRhythm;Mecree;Huadian;GS Light;Romanso;Benwei',
        'model_version': MV,
        'notes': '全球品牌+中国高杆名单（Hishine/ZGSM/RC/ONOR/LEDYi/Golon/CHZ/Haichang/LEDRhythm/Mecree 等），无 SolarOne；"discussed previously" 说明同会话上下文仍在，我们仍未进名单——与 Perplexity C3 的假否定不同，Grok 是直接遗漏',
    },
    'C5': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;Eaton;Acuity;Huadian;GS Light;Benwei;Mecree;Hishine;RC Lighting;ZGSM;ONOR;LEDYi;Romanso;Luxsun;CHZ Lighting',
        'model_version': MV,
        'notes': '全球四家+中国七家表格（Huadian/GS Light/Benwei/Mecree/Hishine/RC/ZGSM/ONOR/LEDYi/Romanso/Luxsun/CHZ），无 SolarOne；同查询 ChatGPT 排 1/5',
    },
    'L1': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;Huadian;GS Light;Mecree;Hishine;Benwei;RC Lighting;ZGSM;ONOR;LEDYi;Romanso',
        'model_version': MV,
        'notes': '阿拉伯语查询以乱码态到达（同 ChatGPT L1 遭遇），Grok 自行还原查询并用阿拉伯语作答；webResults=0 纯模型知识；全球两家+中国七家表无 SolarOne；三家平台三种结果（ChatGPT 提及/Perplexity 排 4/4/Grok 未提及）',
    },
    'L2': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;Eaton;Acuity;Huadian;GS Light;Mecree;Hishine;Benwei;RC Lighting;ZGSM;ONOR;LEDYi;Romanso',
        'model_version': MV,
        'notes': '德语答案：全球 premium（Signify/Musco/Eaton/Acuity）+中国七家表，无 SolarOne；webResults=0 纯模型知识；同 ChatGPT L2（提及 3/3）、Perplexity L2（未提及）',
    },
    'L3': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': 'Signify;Musco;Eaton;Acuity;Huadian;GS Light;Mecree;Hishine;Benwei;RC Lighting;ZGSM;ONOR;LEDYi;Romanso',
        'model_version': MV,
        'notes': '同 L2 结构（全球 premium+中国七家表），无 SolarOne；webResults=0 纯模型知识；同 ChatGPT L3（提及 3/3）、Perplexity L3（未提及）',
    },
    'S1': {
        'mentioned': 'n',
        'rank': '',
        'sentiment': '',
        'cited_own': '',
        'spec_ok': '',
        'competitors_seen': '',
        'model_version': MV,
        'notes': '纯 AFC 标准解读并纠正查询前提（"no exact requirement of 2,200 lux"，Cat1>2400/Cat2>2000/Cat3>1800），零品牌提及（同 ChatGPT S1）；webResults=30 但正文无内联引用',
    },
    'X1': {
        'mentioned': 'y',
        'rank': '2',
        'sentiment': 'neu',
        'cited_own': '',
        'spec_ok': 'y',
        'competitors_seen': 'Musco',
        'model_version': MV,
        'notes': '并排对比 Musco 优先（同 ChatGPT X1/X3 模式，rank=2）；关于我们的表述全部与站内一致（2007/500+/50+/M 1280W+/130lm/W/5+ 保修/无 FIFA Preferred Provider 状态——站内确实未声明）；本站域名出现在本轮检索结果（首页/projects/football//projects/tennis//ru/ 四页）但正文未给链接；定位我们为社区/训练/中高端性价比之选',
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
               if r['platform'] == 'Grok' and r['query_id'] in FILL]
    assert len(targets) == 11, 'expected 11 Grok target rows, got %d' % len(targets)
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

    # every row outside the targets must be byte-identical in values
    for before, after in zip(snapshot, rows):
        key = (before['platform'], before['query_id'])
        if key[0] == 'Grok' and key[1] in FILL:
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
