"""生成 i18n 待译清单（engine-agnostic）。

输出 docs/i18n_待译清单.md，含：
  A. gettext 目录缺失串（= KNOWN_UNTRANSLATED 冻结的那批，含 Cookie 同意条）
  B. SiteConfig 单语文案字段（含 meta_title/meta_description —— 五语页面标题全英文的根因）
  C. Product 缺译（seed_data.json）
  D. Project 缺译
  E. 模板里硬编码的 title/meta/og 字面量
"""
import ast
import gettext as _gettext
import json
import os
import re
import sys
from pathlib import Path

import django

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # 脚本在 scripts/ 下，需把项目根加进 import path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'solarone.settings')
django.setup()

LANGS = ['fr', 'es', 'de', 'ru', 'ar']
out = []


def w(s=''):
    out.append(s)


# ---------- A. gettext 缺失串 ----------
# 直接 import 测试模块里的 frozenset（正则解析会被串内引号带偏）
import pages.tests as _pt  # noqa: E402

known = None
for _name in dir(_pt):
    obj = getattr(_pt, _name)
    if isinstance(obj, type) and hasattr(obj, 'KNOWN_UNTRANSLATED'):
        known = sorted(obj.KNOWN_UNTRANSLATED)
        break
if known is None:
    raise SystemExit('未找到 KNOWN_UNTRANSLATED')
w('## A. gettext 目录缺失串（当前在五语下静默回退英文）')
w()
w(f'共 **{len(known)}** 条。这些串在模板/代码里存在，但 `locale/*/django.po` **根本没有对应 msgid**')
w('（`django.po` 生成于 2026-07-22，其后新增的串从未提取）。')
w()
w('| # | 英文原文 | 出现位置 |')
w('|---|---|---|')

tpl_files = sorted((ROOT / 'templates').rglob('*.html'))
py_files = [p for p in sorted((ROOT / 'pages').rglob('*.py'))
            if not p.name.startswith('test') and p.name != 'seed_data.py']


def rel(p):
    return p.relative_to(ROOT).as_posix()


def line_of(txt, pos):
    return txt[:pos].count('\n') + 1


# Python 侧：用 ast 精确匹配 —— 会自动合并隐式相邻字符串拼接
# （如 _('A ' 'B')），这是朴素子串搜索漏掉 views_contact.py:124 的原因。
py_idx = {}
for p in py_files:
    try:
        tree = ast.parse(p.read_text(encoding='utf-8'))
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            py_idx.setdefault(node.value, f'`{rel(p)}:{node.lineno}`')

# 模板侧：原样 → 空白归一化 → templatize() 确认（blocktrans 占位符）
from django.utils.translation.template import templatize as _templatize  # noqa: E402


def locate(s):
    hits = []
    if s in py_idx:
        hits.append(py_idx[s])
    for p in tpl_files:
        txt = p.read_text(encoding='utf-8')
        if s in txt:
            hits.append(f'`{rel(p)}:{line_of(txt, txt.index(s))}`')
            continue
        flat = re.sub(r'\s+', ' ', txt)
        if re.sub(r'\s+', ' ', s) in flat:
            head = s.split()[0]
            if head in txt:
                hits.append(f'`{rel(p)}:{line_of(txt, txt.index(head))}`†')
            continue
        try:
            if s in _templatize(txt, str(p)):
                hits.append(f'`{rel(p)}`†')
        except Exception:
            pass
    return hits[:2]


for idx, s in enumerate(known, 1):
    hits = locate(s)
    cells = ' '.join(hits) if hits else '_未在源码中定位到_'
    w(f'| {idx} | `{s}` | {cells} |')
w()
w('† = 模板里是多行写法或 `{{{{ }}}}` 占位符，行号为启发式定位（首个词所在行）。')
w()

# ---------- B. SiteConfig 单语文案 ----------
from pages.models import SiteConfig  # noqa: E402
from pages.views.i18n import _SIDEBAR_I18N  # noqa: E402

seed = json.loads((ROOT / 'seed_data.json').read_text(encoding='utf-8'))
sc = seed.get('siteconfig', {})
ROUTED = {'hero_title', 'hero_subtitle', 'products_title', 'products_subtitle',
          'projects_title', 'projects_subtitle'}
STRUCT = re.compile(r'^(font_|color|theme|primary|accent|.*_url$|.*_path$|logo|'
                    r'og_image|hero_background|.*_size$|.*_weight$|.*_enabled$|id$|'
                    r'social_|brand_name|.*_email$|.*_phone$|.*_address$)')

w('## B. SiteConfig 单语文案字段（DB/seed 里只有一份英文，没有多语版本）')
w()
w('这些字段直接渲染到页面上，**没有** `translations` 结构，也没有经过 `_t()`。')
w('加粗的 `meta_title` / `meta_description` 是「五语页面 `<title>` 与 meta 全英文」的根因')
w('（`base.html:11/12/15/16/23/24/546` 全部取这两个值）。')
w()
w('| 字段 | 当前英文值 | 是否经 `_t()` | 已有 `_SIDEBAR_I18N` 条目 |')
w('|---|---|---|---|')
_b_total = _b_routed = _b_trans = 0
for k, v in sc.items():
    if not isinstance(v, str) or not v.strip():
        continue
    if STRUCT.match(k):
        continue
    _b_total += 1
    routed = k in ROUTED
    _b_routed += 1 if routed else 0
    has = bool(v in _SIDEBAR_I18N and all(
        (_SIDEBAR_I18N[v] or {}).get(l, '').strip() for l in LANGS))
    _b_trans += 1 if has else 0
    star = '**' if k in ('meta_title', 'meta_description') else ''
    w(f'| {star}`{k}`{star} | {v[:64].replace("|", "/")} | '
      f'{"✅" if routed else "❌"} | {"✅" if has else "❌"} |')
w()

w(f'共 **{_b_total}** 个文案字段，其中 **{_b_routed}** 个经 `_t()`、**{_b_trans}** 个已有完整五语条目；'
  f'剩余 **{_b_total - _b_trans}** 个在五语下全是英文。')
w()

# ---------- C/D. 产品与项目缺译 ----------
w('## C. Product 缺译（`seed_data.json`）')
w()
prods = seed.get('products', [])
rows = []
for p in prods:
    t = p.get('translations') or {}
    miss = [l for l in LANGS if not (t.get(l) or {}).get('name', '').strip()]
    if miss:
        rows.append((p.get('slug', ''), p.get('name', '')[:40], miss))
w(f'共 **{len(rows)} / {len(prods)}** 个产品在部分或全部语种下无译文'
  f'（其中 {sum(1 for r in rows if len(r[2]) == 5)} 个**五语全缺**）。')
w()
w('| slug | 英文名 | 缺哪些语言 |')
w('|---|---|---|')
for slug, name, miss in rows:
    w(f'| `{slug}` | {name.replace("|", "/")} | {", ".join(miss)} |')
w()

w('## D. Project 缺译（`seed_data.json`）')
w()
projs = seed.get('projects', [])
prow = []
for p in projs:
    t = p.get('translations') or {}
    miss = [l for l in LANGS if not (t.get(l) or {}).get('title', '').strip()]
    if miss:
        prow.append((p.get('slug', ''), p.get('title', '')[:40], miss))
w(f'共 **{len(prow)} / {len(projs)}** 个项目缺部分语种译文。')
w()
w('| slug | 英文标题 | 缺哪些语言 |')
w('|---|---|---|')
for slug, title, miss in prow:
    w(f'| `{slug}` | {title.replace("|", "/")} | {", ".join(miss)} |')
w()

# ---------- E. 模板硬编码 title/meta ----------
w('## E. 模板里硬编码的 title / meta 字面量（未经任何翻译机制）')
w()
w('| 模板 | 行 | 内容 |')
w('|---|---|---|')
pat = re.compile(r'{%\s*block\s+(title|meta_description|og_title|og_description)\s*%}\s*([^{][^%]{0,80})')
cnt = 0
for p in tpl_files:
    txt = p.read_text(encoding='utf-8')
    for mm in pat.finditer(txt):
        val = mm.group(2).strip()
        if not val or val.startswith('{{'):
            continue
        ln = txt[:mm.start()].count('\n') + 1
        w(f'| `{p.relative_to(ROOT).as_posix()}` | {ln} | `{val[:76]}` |')
        cnt += 1
w()
w(f'共 {cnt} 处。' if cnt else '（无）')

dest = ROOT / 'docs' / 'i18n_待译清单.md'
body = '\n'.join(out) + '\n'
front = f"""---
doc_id: i18n-translation-inventory
title: 多语种待译清单（六语站 i18n 欠账盘点）
version: 1.0.0
status: in_progress
last_updated: 2026-09-17
owner: Sean Lu
related:
  - path: docs/优化建议清单.md
    role: 生产无状态化（seed_data.json 为内容真源）决策出处
generated_by: scripts/gen_i18n_inventory.py（可重跑刷新）
---

# 多语种待译清单

本文件由脚本生成，用于把站点上**尚未翻译的英文内容**一次性盘清，交给翻译统一处理。

重跑方式（在项目根目录）：

```bash
E:/Python/python3/python.exe scripts/gen_i18n_inventory.py
```

站点两套翻译机制（详见 `PONYTAIL_AUDIT.md` §10）：
① gettext 目录 `locale/<lang>/LC_MESSAGES/django.mo`（服务 `{{% trans %}}` 与 `_()`）；
② `pages/views/i18n.py` 的 `_SIDEBAR_I18N` 字典 + `_t()`（服务侧栏/规格/SiteConfig 文案，
**查不到即静默回退英文**）。

## ⚠️ 译文落地链路（重要）

生产内容是**无状态**的：`seed_data.json` 是**内容真源**，线上的 DB 只是 `/tmp` 临时库、
每次重新部署即丢。因此：

| 内容 | 译文应写到哪里 | 落地方式 |
|---|---|---|
| A 段 gettext 串 | `locale/<lang>/LC_MESSAGES/django.po` | 需**提取**（本机无 gettext，缺 xgettext）+ 翻译 + **编译 `.mo`**（可用已安装的 `polib`） |
| B 段 SiteConfig 单语字段 | 经 `_t()` 则该写 `_SIDEBAR_I18N` | 改代码 + 加字典条目 |
| C/D 段 产品/项目 | `seed_data.json` 的 `translations.<lang>` | 改 `seed_data.json` → `manage.py regenerate_seed` → 提交推送 |

**注意**：后台 admin 的「自动翻译」按钮写的是**本地 DB**，而 DB 不是生产内容源；
`seed_sync.sync_seed_from_db()`（能把 DB 导出成 `seed_data.json`）全仓库**没有任何调用点**，
docstring 里说的 "called from Django admin hooks" 的 hook **并不存在**。
所以走 admin 翻译后必须**手工**执行 `python pages/seed_sync.py`（无参数 = DB 模式）导出并提交，
否则译文永远到不了线上。

---

"""
dest.write_text(front + body, encoding='utf-8')
print(f'written: {dest}')
print(f'A={len(known)} B=siteconfig C={len(rows)}/{len(prods)} D={len(prow)}/{len(projs)} E={cnt}')
