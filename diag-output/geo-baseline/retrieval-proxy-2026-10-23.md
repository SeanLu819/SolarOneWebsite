# 检索层实测：10 条核心查询（2026-10-23 19:40）

**这是什么**：把 round 0 的 10 条核心查询过一遍网页搜索引擎，看**检索层**能不能拿到本站页面。
**这不是 AI 回答测量**——`rounds/round-0-*.csv` 记的是 AI 回答，两回事，不要混填。
**为什么先测这层**：ChatGPT 检索 / Copilot / Perplexity 的回答质量直接继承搜索引擎索引。
检索层是零，AI 层不可能有第一方来源可引。这层测完，你手工问 88 格（+6 格扩展）时心里有底。

**检索源**：本机搜索工具（引擎未标注，**不是 Bing**，Bing 侧仍需 Bing WMT 才能看）。

---

## 总结论：10/10 零本站命中

| # | 查询 | 意图 | 本站页面 | 品牌是否出现 |
| --- | --- | --- | --- | --- |
| B1 | SolarOne stadium lights | brand | **0** | 出现，但是别人的 + 错的 |
| B2 | SolarOne LED sports lighting manufacturer | brand | **0** | 出现，但是错的 |
| C1 | best LED stadium light manufacturers | category | **0** | **完全不出现** |
| C2 | LED sports field lighting supplier China | category | **0** | **完全不出现** |
| C3 | LED high mast flood light manufacturer | category | **0** | **完全不出现** |
| L1 | مورد إضاءة ملاعب رياضية LED | local/ar | **0** | **完全不出现** |
| L2 | LED Stadionbeleuchtung Hersteller | local/de | **0** | **完全不出现** |
| L3 | fournisseur éclairage LED stade sportif | local/fr | **0** | **完全不出现** |
| S1 | stadium lighting 2200 lux AFC … 2018 | spec | **0** | 数字在，品牌不在 |
| X1 | Musco vs SolarOne stadium lighting | comparison | **0** | **完全不出现** |

---

## 三条比"零命中"更值钱的发现

### ① 品牌查询能搜到我们，但每条都是错的（B1/B2）

B1 前 5 条里 3 条是本品牌相关内容，全部来自第三方：

| 来源 | 原文写的 | 站内现在说的 |
| --- | --- | --- |
| CIFTIS 服贸会 productId=26946 | 「灯具**8年质保**，8年内保证灯具光衰不超过5%」「德国技术团队」 | 5+ 年 |
| Made-in-China | 「more **800,000PCS** … more than **160PCS** countries」 | 500+ 项目 / 50+ 国 |
| alighting.cn 产品页 | 「防护等级 **IP65** 使用寿命 **>50000h**」 | 全线 IP66 / L70 100,000 h |

**并且 B1 第 5 条是 `solarone.net`（SolarOne Solutions，美国离网太阳能路灯公司）**——
正是 `Not to be confused with` 段和 `disambiguatingDescription` 要拦的那个混淆源。
消歧目前只存在于站内，检索层完全看不到。

### ② 非英语查询返回的是中文页（L1/L2/L3）

德语法语查询的前 5 条结果里，中文页面占多数（hxbdxled、b2b.baidu.com、b2b168.org、
gdzkzt），阿语查询前 5 条**没有一条是阿语内容**。

这一条要分开看：本地语言内容层薄不只是我们的事（整个品类都这样），
但它意味着 `/de/` `/fr/` `/ar/` 页面即使被收录，也要和一堆中文页抢同一个查询。
**A1 让 FAQ 变本地语言是必要条件，但不是充分条件。**

### ③ 我们不在任何对比集里（X1）

X1 返回 5 条，全是 Musco 项目页 + 各类"全球十大体育照明厂商"榜单
（customizelighting、ceramiclite、zcleds、hylele）。榜单常客是
Musco / Signify / Cooper-Ephesus / Cree / Acuity / LSI / Schréder。

**没有一条榜单提到 SolarOne。** AI 被问"Musco vs SolarOne"时，
要么说无法比较，要么拿第三方目录里的错误规格来比——这就是 X1 spec_ok 报错的机制。

---

## 对 round 0 的预期校准

基于以上，手工问 AI 时**大概率**会看到：

- B1：mentioned=y 但 spec_ok=n（混淆或错规格），cited_own=n
- B2：同上，但中文品牌名"信能阳光"可能被提到
- C1/C2/C3：mentioned=n，competitors_seen 会有 Musco/Signify 等一串
- L1/L2/L3：mentioned=n，且可能用英文答非所问
- S1：mentioned=n + notes"有数字无品牌"
- X1：mentioned=n 或 AI 拒绝比较

**如果实测比这个好，说明 IndexNow 那 354 条已经开始起作用了**——
那本身就是有价值的信号，值得单独记一笔。

---

## 复测规则

同一批查询式每季度重跑一次，间隔 ≥ 14 天。任一条出现 `solaronelighting.com`
即为进展。历史记录见本目录 `index-presence-2026-10-23.md`。
