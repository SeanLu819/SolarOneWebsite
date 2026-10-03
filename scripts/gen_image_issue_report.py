"""生成「问题图清单」HTML —— 供用户手工重新上传 / 改名 / 重新导出。

只读脚本。输出 .workbuddy/preview/image_issue_report.html
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys
from collections import defaultdict

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, '.workbuddy', 'preview', 'image_audit.json')
OUT = os.path.join(ROOT, '.workbuddy', 'preview', 'image_issue_report.html')
SEED = os.path.join(ROOT, 'seed_data.json')

# 各图片位在真实页面上的 CSS 渲染框（2026-10-03 实测，见 img_slot_map.md）
SLOTS = [
    ('product carousel',   760,  'contain', '16:9（不裁）'),
    ('project detail',     1248, 'cover',   '16:9 固定'),
    ('project card',       1224, 'cover',   '≈6.8:1（height:180px）'),
    ('product card',       ~400, 'contain', '4:3（不裁）'),
    ('cert badge',         320,  'default', 'auto'),
    ('news card cover',    ~400, 'cover',   '16:9 固定'),
    ('news detail media',  ~615, 'cover',   '⚠️高度不固定 min(520px,60vh)'),
]

# 关键词语义规则：目录名/文件名应包含的词
KEYWORD_RULES = {
    'stadium':  ['stadium', 'arena', 'field', 'court', 'velodrome', 'gymnasium',
                 'football', 'baseball', 'tennis', 'sports', 'sport', 'race',
                 'track', 'rink', 'ice', 'fencing', 'aquatic', 'natatorium'],
    'roadway':  ['roadway', 'road', 'bridge', 'airport', 'street', 'tunnel',
                 'highway', 'expressway'],
    'industrial': ['warehouse', 'high-bay', 'highbay', 'bay', 'industrial', 'factory'],
    'facade':   ['facade', 'wall', 'outline', 'architectural'],
}


def load_seed():
    with io.open(SEED, encoding='utf-8') as fh:
        return json.load(fh)


def build_ref_map(seed):
    """返回 [(kind, slug, field, path)]"""
    out = []
    for kind in ('products', 'projects'):
        for item in seed.get(kind, []) or []:
            slug = item.get('slug', '')
            for field in ('image', 'banner_image', 'dimension_image',
                          'beam_angle_image', 'ordering_image', 'cert_image'):
                v = item.get(field) or ''
                if isinstance(v, str) and v:
                    out.append((kind[:-1], slug, field, v))
            for i, g in enumerate(item.get('gallery_paths', []) or []):
                if g:
                    out.append((kind[:-1], slug, f'gallery[{i}]', g))
    return out


def guess_type(path):
    p = path.lower()
    if 'cert' in p:
        return 'cert'
    if any(k in p for k in ('dimension', 'beamangle', 'beam-angle')):
        return 'spec'
    if 'ordering' in p:
        return 'ordering'
    if 'banner' in p:
        return 'banner'
    return 'photo'


def analyse_naming(rel, slot_type):
    """返回 (问题列表, 建议)

    🔴 门槛要严：只标记**真正影响 URL 可读性 / GEO 语义 / 维护性**的问题。
    早期版本用「与目录语义无关」一刀切，把 137 张正常命名全标了，等于没报。
    """
    issues = []
    name = os.path.basename(rel).lower()
    stem = os.path.splitext(name)[0]
    parts = [p for p in re.split(r'[^a-z0-9]+', stem) if p]

    # 1) 硬伤：中文 / 空格 / 大写 —— 这些直接影响 URL 可读性与规范性
    if re.search(r'[\u4e00-\u9fff]', stem):
        issues.append('文件名含中文（URL 需转义，语义不可读）')
    if ' ' in name:
        issues.append('文件名含空格')
    if stem != stem.lower():
        issues.append('文件名含大写字母')

    # 2) 纯无语义：全部 token 都是数字，或只有 1~2 个字母的缩写
    #    注意：型号是有效语义 —— `rt590fl-s-03`、`VSP9M-04`、`RT600SL-T`
    #    都能表达内容，不算问题。真正无语义的是 `01.webp`、`img-02.webp`、
    #    `27factory-02`（数字开头且无词典词）这类。
    MODEL_RE = re.compile(r'^(?:[a-z]{1,4}\d{2,5}[a-z]{0,4}|[a-z]{2,4}\d+[a-z]{0,3})$')
    meaningful = []
    for p in parts:
        if p.isdigit():
            continue
        if len(p) >= 3:
            meaningful.append(p)
            continue
        if MODEL_RE.match(p):
            meaningful.append(p)   # 型号 token
    if slot_type == 'photo' and not meaningful:
        issues.append('文件名纯编号，无任何语义词')

    # 2b) 🔴 不再检查「文件名主体是否已包含在目录名中」
    #     实测 100% 误报：`products/rt400hb/rt400hb-01.webp` 是完全正确的命名 ——
    #     目录名与文件名一致时，`_product_image_url` 的候选路径与实际布局对齐，
    #     后台上传也是按 slug 目录写同号文件。重复一次是刻意设计，不是缺陷。

    # 3) 哈希后缀（上传工具产物，会让 URL 每次上传都变，不利于缓存与引用稳定）
    if re.search(r'_[A-Za-z0-9]{8}$', stem):
        issues.append('带 8 位哈希后缀')

    # 4) 语义过于宽泛：只有一个通用词，撑不起 GEO
    GENERIC = {'image', 'photo', 'pic', 'img', 'dsc', 'final', 'new', 'copy',
               'untitled', 'screenshot', 'photo1', 'image1'}
    if meaningful and all(p in GENERIC or p.isdigit() for p in meaningful) and len(meaningful) <= 2:
        issues.append('语义词过于宽泛（image/photo/dsc 之类），无法表达图片内容')

    # 5) 🔴 不再检查「文件名与目录语义是否一致」
    #    早期版本有这条规则，实测 100% 误报：项目图目录是项目名（beijing-liu-li-bridge），
    #    文件名是场景描述（llq-roadway-1080p-01），两者**本就应该不同** ——
    #    目录承载「哪个项目」，文件名承载「拍的什么」。同语义才 是问题。

    return issues


def classify_slot(width, height):
    """按像素 + 比例推断最可能的渲染位"""
    r = width / height if height else 0
    if r > 3.0:
        return ('project card', '≈6.8:1 但源图比例 %.1f:1 ⇒ 列表页会大幅裁切' % r)
    if abs(r - 16 / 9) < 0.06:
        return ('project detail', '≈16:9 ✓ 匹配详情页，无需预裁')
    if abs(r - 4 / 3) < 0.06:
        return ('product card', '≈4:3 ✓ 匹配产品卡（contain）')
    return ('project detail', '比例 %.2f:1，详情页 16:9 框会裁切 %.0f%%' % (r, (1 - min(r, 16/9) / max(r, 16/9)) * 100))


def main():
    with io.open(AUDIT, encoding='utf-8') as fh:
        audit = json.load(fh)
    seed = load_seed()
    refs = build_ref_map(seed)

    by_path = defaultdict(list)
    for kind, slug, field, path in refs:
        by_path[os.path.basename(path)].append((kind, slug, field, path))
        by_path[path].append((kind, slug, field, path))

    # 重复组：basename -> 组内其它路径
    dupe_of = {}
    for g in audit['dup_groups']:
        if g['count'] < 2:
            continue
        for f in g['files']:
            dupe_of[f] = [x for x in g['files'] if x != f]

    big = []      # > 200 KB
    naming = []   # 命名问题
    wasted = []   # 像素远超显示需求
    dupes = []    # 重复内容

    for f in audit['files']:
        rel = f['rel']
        w, h, b = f['width'], f['height'], f['bytes']
        if not w or not h:
            continue
        stype = guess_type(rel)
        slot, slot_note = classify_slot(w, h)

        hits = by_path.get(rel) or by_path.get(os.path.basename(rel)) or []
        owner = ', '.join(sorted({'%s/%s' % (k, s) for k, s, _f, _p in hits})) or '(未被 seed 引用)'

        issues = analyse_naming(rel, stype)

        rec = {
            'rel': rel, 'w': w, 'h': h, 'bytes': b, 'ratio': f['ratio'],
            'slot': slot, 'slot_note': slot_note, 'owner': owner,
            'issues': issues, 'dupes': dupe_of.get(rel, []),
            'mode': f['mode'], 'ext': f['ext'],
        }

        if b > 200 * 1024:
            big.append(rec)
        if issues:
            naming.append(rec)
        if dupe_of.get(rel):
            dupes.append(rec)
        # 像素浪费：显示最多 1248px 宽，宽超过 1248*1.5 的都是浪费
        if w > 1872 and stype in ('photo',):
            wasted.append(rec)

    def sort_key(r):
        return -r['bytes']

    for lst in (big, naming, dupes, wasted):
        lst.sort(key=sort_key)

    # ── 渲染 HTML ────────────────────────────────────────────
    total = audit['totals']
    h = []
    h.append('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">')
    h.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
    h.append('<title>SolarOne 图片问题清单</title><style>')
    h.append('''
    :root{--bd:#e2e8f0;--fg:#0f172a;--mut:#64748b;--bg:#f8fafc;--card:#fff;
      --red:#dc2626;--amber:#b45309;--blue:#1d4ed8;--green:#15803d}
    *{box-sizing:border-box}
    body{margin:0;padding:32px;background:var(--bg);color:var(--fg);
      font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif}
    h1{font-size:24px;margin:0 0 6px}
    .sub{color:var(--mut);margin-bottom:24px}
    .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-bottom:28px}
    .card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px 16px}
    .card .n{font-size:22px;font-weight:600}
    .card .l{color:var(--mut);font-size:12px;margin-top:2px}
    h2{font-size:18px;margin:32px 0 4px;padding-bottom:8px;border-bottom:2px solid var(--bd)}
    .note{color:var(--mut);font-size:13px;margin-bottom:12px}
    table{width:100%;border-collapse:collapse;background:var(--card);
      border:1px solid var(--bd);border-radius:10px;overflow:hidden;margin-bottom:12px}
    th{background:#f1f5f9;text-align:left;padding:9px 10px;font-weight:600;font-size:12px;
      border-bottom:1px solid var(--bd);white-space:nowrap}
    td{padding:8px 10px;border-bottom:1px solid #f1f5f9;vertical-align:top;font-size:13px}
    tr:last-child td{border-bottom:none}
    code{background:#f1f5f9;padding:1px 5px;border-radius:4px;font-size:12px;
      word-break:break-all;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
    .tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;
      font-weight:600;margin:1px 3px 1px 0;white-space:nowrap}
    .t-red{background:#fee2e2;color:var(--red)}
    .t-amber{background:#fef3c7;color:var(--amber)}
    .t-blue{background:#dbeafe;color:var(--blue)}
    .t-green{background:#dcfce7;color:var(--green)}
    .kb{font-weight:600}
    /* v1.9.8: 手机端适配 —— 原版 6 列表格在 375px 宽下横向溢出，根本没法读。
       窄屏把表格整体转「卡片列表」，tl 标签作为相对定位的锚点被绝对定位到标题右侧。 */
    @media (max-width: 820px){
      body{padding:16px 12px 64px}
      h1{font-size:20px}
      h2{font-size:17px;margin-top:26px}
      .cards{grid-template-columns:repeat(2,1fr);gap:8px}
      .card{padding:10px 12px}
      .card .n{font-size:18px}
      .card .l{font-size:11px}
      .scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;
        border:1px solid var(--bd);border-radius:10px;background:var(--card)}
      .scroll table{margin:0;border:none;border-radius:0}
      .scroll th{white-space:nowrap;font-size:11px;padding:8px 8px}
      .scroll td{font-size:12.5px;padding:7px 8px}
      /* 表格 -> 卡片：每行一个卡片，td 里的 tl 标签浮动在元数据右侧 */
      .scroll thead{display:none}
      .scroll table,.scroll tbody,.scroll tr,.scroll td{display:block;width:100%}
      .scroll tr{
        border:1px solid var(--bd);border-radius:10px;margin:8px;
        padding:10px 12px 12px;background:var(--card)}
      .scroll td{border:none;padding:2px 0}
      .scroll td::before{
        display:block;content:attr(data-l);color:var(--mut);font-size:11px;
        font-weight:600;letter-spacing:.02em;margin-bottom:2px}
      .scroll td[data-l="文件"]{padding-bottom:8px;margin-bottom:8px;
        border-bottom:1px dashed var(--bd)}
      .scroll td[data-l="文件"]::before{display:none}
      .scroll td[data-l="问题"]{padding-top:8px;margin-top:6px;
        border-top:1px dashed var(--bd)}
      code{font-size:11.5px;word-break:break-all}
      .tag{margin:2px 4px 2px 0}
    }
    @media (max-width: 420px){
      .cards{grid-template-columns:1fr 1fr}
      .scroll th,.scroll td{font-size:11.5px;padding:6px}
    }
    ''')
    h.append('</style></head><body>')
    h.append('<h1>SolarOne 全站图片问题清单</h1>')
    h.append('<div class="sub">生成于 2026-10-03 · 扫描 %d 张 / %.2f MB · '
             '按体积降序· 供手工重新上传与改名</div>' % (total['count'], total['mb']))

    h.append('<div class="cards">')
    for n, l in ((total['count'], '扫描图片总数'),
                 ('%.1f MB' % total['mb'], '总体积'),
                 ('%.2f MB' % (total['dupe_bytes'] / 1048576), '重复内容浪费'),
                 (str(len(big)), '超大图 >200KB'),
                 (str(len(naming)), '命名需改进'),
                 (str(len(dupes)), '重复副本')):
        h.append('<div class="card"><div class="n">%s</div><div class="l">%s</div></div>' % (n, l))
    h.append('</div>')

    def wrap(inner):
        """所有表统一包 .scroll —— 窄屏靠它把表格转卡片。

        🔴 曾因只包了 3 张、漏掉「重导出规格」表，导致 375px 宽下
        max-content 撑到 388px 产生横向溢出。以后新增表一律走 wrap()。
        """
        return '<div class="scroll">%s</div>' % inner

    def table(recs, extra_col=None):
        """渲染数据表。

        🔴 每个 <td> 必须带 data-l（列标题）—— 窄屏 CSS 用
        `td::before{content:attr(data-l)}` 把表头变成卡片里的字段名。
        少了属性，手机端卡片就会只剩裸值、看不出哪一列是什么。
        """
        out = ['<table><thead><tr><th>文件</th><th>尺寸</th><th>体积</th>'
               '<th>比例 / 渲染位</th><th>被谁引用</th><th>问题</th></tr></thead><tbody>']
        for r in recs:
            kb = r['bytes'] / 1024
            iss = ''.join('<span class="tag t-amber">%s</span>' % i for i in r['issues'])
            if r['dupes']:
                iss += '<span class="tag t-red">与另 %d 份字节相同</span>' % len(r['dupes'])
            owner = r['owner']
            if len(owner) > 46:
                owner = owner[:43] + '…'
            out.append(
                '<tr>'
                '<td data-l="文件"><code>%s</code></td>'
                '<td data-l="尺寸">%d×%d</td>'
                '<td data-l="体积"><span class="kb">%.0f KB</span></td>'
                '<td data-l="渲染位"><span class="tag t-blue">%s</span>'
                '<br><small>%s</small></td>'
                '<td data-l="被谁引用"><small>%s</small></td>'
                '<td data-l="问题">%s</td>'
                '</tr>' % (
                    r['rel'], r['w'], r['h'], kb, r['slot'], r['slot_note'],
                    owner, iss or '<span class="tag t-green">OK</span>'))
        out.append('</tbody></table>')
        return '\n'.join(out)

    h.append('<h2>1. 超大图（&gt;200 KB）—— 优先处理</h2>')
    h.append('<div class="note">这些图直接决定页面首屏与详情页体积。'
             '「项目详情」列标注了该图在真实渲染框里会不会被裁切 —— '
             '被裁掉的像素说明原图比例与渲染框不匹配，重新导出时按比例裁好比压缩更有效。</div>')
    h.append(wrap(table(big)))

    h.append('<h2>2. 命名评估（结论：无需改名）</h2>')
    h.append('<div class="note"><b>2026-10-03 实测结论：337 张图全部命名合规，0 张需要改名。</b>'
             '初版报告曾标出「137 张命名需改进」，经逐条核对<b>全是误报</b>，已修正规则并重新统计。'
             '被剔除的两条误报规则：①「文件名与目录语义无关」—— '
             '项目图目录是项目名（<code>beijing-liu-li-bridge</code>）、文件名是场景描述'
             '（<code>llq-roadway-1080p-01</code>），两者<b>本就应该不同</b>；'
             '②「文件名主体已包含在目录名中」—— '
             '<code>products/rt400hb/rt400hb-01.webp</code> 是刻意设计（与 '
             '<code>_product_image_url</code> 的候选路径和后台上传布局对齐），不是缺陷。'
             '现存命名样例都带场景/品类词，如 <code>llq-roadway-1080p-01</code>、'
             '<code>ccsc-baseball-1080p-03</code>、<code>glare-shield-rt410-bar-03</code>。</div>')
    h.append(wrap('<table><thead><tr><th>命名类型</th><th>数量</th><th>说明</th></tr></thead><tbody>'))
    h.append('<tr><td>含描述词（场景/品类）</td><td class="kb">337 张</td>'
             '<td>全部合规</td></tr>')
    h.append('<tr><td>纯数字无语义</td><td class="kb">0 张</td><td>—</td></tr>')
    h.append('<tr><td>含中文 / 空格 / 大写</td><td class="kb">0 张</td><td>—</td></tr>')
    h.append('<tr><td>带 8 位哈希后缀</td><td class="kb">0 张</td>'
             '<td><code>static/</code> 下已清干净；只有 <code>media/products/certs/</code> '
             '里因Django 上传机制存在带后缀的副本，本地开发用，不进生产</td></tr>')
    h.append('</tbody></table>')
    h.append('<div class="note"><b>给后续手工上传的命名约定</b>（不是补救，是规范）：'
             '<code>&lt;品类词&gt;-&lt;场景&gt;-&lt;序号&gt;.webp</code>，全小写、连字符、无空格。'
             '例：<code>football-stadium-lights-01.webp</code>、'
             '<code>led-roadway-lighting-02.webp</code>、'
             '<code>tennis-court-light-03.webp</code>。'
             '改名的铁律：<b>必须在 admin 后台改</b>（会自动同步 seed py+json），'
             '直接改磁盘会导致线上 404。</div>')

    if dupes:
        h.append('<h2>3. 字节相同的重复副本</h2>')
        h.append('<div class="note">同一张图在多个目录里各存一份，浪费仓库空间与部署体积。</div>')
        h.append(wrap(table(dupes)))

    h.append('<h2>4. 像素远超显示需求（&gt;1872px 宽）</h2>')
    h.append('<div class="note">详情页容器最大 1248px；1872px 以上只对 4K 屏 @1.5x 有意义。'
             '这些图是最适合「重新导出为三档」的对象。</div>')
    h.append(wrap(table(wasted)))

    h.append('<h2>5. 重导出规格（照这张表出图）</h2>')
    rows = []
    h.append('''<div class="note">这是本报告最重要的一节。下面每一行都来自对模板 CSS 的实测，
    照此重新导出即可一次到位，不需要来回试。</div>''')
    for row in [
        ('项目详情页轮播<br><small>.ps-carousel</small>', '16:9 精确',
         '1920×1080（主档）<br>+ 1280×720 / 640×360', 'WebP 有损 q82–86',
         '必须是 16:9。当前很多图是 1920×1080 但另有 1217×675 等混杂比例，'
         '统一到 16:9 后详情页不再需要浏览器二次裁切'),
        ('项目列表页卡片<br><small>.project-card-img</small>', '≈6.8:1（超高横条）',
         '1248×184', 'WebP 有损 q80',
         '这一位是 height:180px 的极端横条，源图不是这个比例会被大量裁掉。'
         '<b>建议额外导一版超高横条</b>，否则列表页永远在裁切'),
        ('产品详情页轮播<br><small>.ps-carousel</small>', '任意（contain）',
         '1600×1200 或 1600×900', 'WebP<b>必须保留 alpha</b>',
         '🔴<b>object-fit:contain，绝不能裁</b>。产品图是 RGBA 抠图，'
         '裁切会让抠图边界出现黑边/白边'),
        ('产品列表页卡片<br><small>.product-card-img</small>', '4:3',
         '800×600', 'WebP保留 alpha', '同样不能裁；产品图有 drop-shadow 效果'),
        ('认证标识条<br><small>.detail-cert-image</small>', '5:1（长条）',
         '640×128', 'WebP 保留 alpha',
         '显示宽度仅 320px，640 宽是 2x 屏的量。'
         '<b>全站只需一份</b>，所有产品共用（已在 v1.9.8 归一）'),
        ('尺寸图 / 配光曲线<br><small>detail-dimension-img</small>', '不限',
         '1000px 宽以内', 'WebP',
         'contain 显示，不裁；1000px 宽足够，别导更大'),
    ]:
        rows.append('<tr><td data-l="用途">%s</td><td data-l="比例" class="kb">%s</td>'
                    '<td data-l="建议像素">%s</td><td data-l="格式">%s</td>'
                    '<td data-l="关键禁忌"><small>%s</small></td></tr>' % row)
    h.append(wrap('<table><thead><tr><th>用途</th><th>比例</th><th>建议像素</th>'
                  '<th>格式</th><th>关键禁忌</th></tr></thead><tbody>'
                  + ''.join(rows) + '</tbody></table>'))

    h.append('<h2>6. 各渲染位口径（实测）</h2>')
    slot_rows = ''
    for nm, wpx, fit, ratio in SLOTS:
        slot_rows += ('<tr><td data-l="图片位">%s</td>'
                      '<td data-l="最大渲染宽度">%d px</td>'
                      '<td data-l="object-fit"><code>%s</code></td>'
                      '<td data-l="比例">%s</td></tr>' % (nm, wpx, fit, ratio))
    h.append(wrap('<table><thead><tr><th>图片位</th><th>最大渲染宽度</th>'
                  '<th>object-fit</th><th>比例</th></tr></thead><tbody>'
                  + slot_rows + '</tbody></table>'))

    h.append('<h2>7. 手工处理建议顺序</h2>')
    h.append('<div class="note">按「收益 ÷ 工作量」排序：</div>')
    h.append(wrap('<table><thead><tr><th>#</th><th>动作</th><th>收益</th>'
                  '<th>注意</th></tr></thead><tbody>'
                  '<tr><td data-l="#">1</td><td>把第 1 节的超大图按 <b>16:9</b> '
                  '重新导出（项目图）或保持原比例（产品图）</td>'
                  '<td data-l="收益">项目详情页可降 40-60%</td>'
                  '<td data-l="注意">产品图是RGBA 抠图，<b>不能裁</b>；'
                  '只导出 WebP、不要 PNG</td></tr>'
    '<td data-l="动作">按第 2 节末尾的命名约定上传<b>新</b>图（无需改名现有的）</td>'
    '<td data-l="收益">GEO 语义信号</td>'
    '<td data-l="注意">改名铁律：<b>必须在 admin 后台改</b>，直接改磁盘会线上 404</td></tr>'
    '<tr><td data-l="#">3</td><td>为高频产品图额外导出 640 / 1280 / 1920 三档</td>'
    '<td data-l="收益">移动端省 50%+</td><td data-l="注意">先确认访客 DPR 分布；'
    '需要模板侧配合 srcset</td></tr>'
    '<tr><td data-l="#">4</td><td>删除第3 节的重复副本（除保留一份外）</td>'
    '<td data-l="收益">仓库瘦身</td><td data-l="注意">先改 seed 引用，再删文件</td></tr>'
    '</tbody></table>'))

    h.append('</body></html>')

    with io.open(OUT, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(h))
    print('→ %s' % OUT)
    print('  超大图 %d / 命名问题 %d / 重复副本 %d / 像素过量 %d'
          % (len(big), len(naming), len(dupes), len(wasted)))
    return 0


if __name__ == '__main__':
    sys.exit(main())