# 产品页 & 详情页长尾关键词优化方案

> 日期：2026-10-06 · 版本基线：本地 v1.10.18（线上 v1.10.15）· 范围：24 个产品页 × 6 语种 = 144 URL
> 方法：线上 `curl` 实证（`https://www.solaronelighting.com` + www + `-L`）+ 本地 seed/DB 双向核对 + 模板源码定位。
> **所有数字均为实测值，未做任何估算。** 搜索量/KD 只引用 `docs/keyword-inventory.csv` 已校准的 6 个词，其余需 GSC 校准后再填。

---

## 0. 结论先行

**收益最大的不是图片文件名。** 按 ROI 排序：

| 排名 | 动作 | 影响的词类 | 收益 | 风险 |
|---|---|---|---|---|
| **P0-1** | 修 `rt220ub` 的 `model_number`（现为 `FL1M-80W`） | 数据正确性 + 消除与 fl1m 撞词 | 高 | 无 |
| **P0-2** | 补 8 个产品的 `power` 字段 | 所有含 W 的长尾修饰词 | 中高 | 无 |
| **P1-1** | 24 页 H1 从纯型号 → 品类词+型号+功率 | 全部产品词 | **最高** | 低 |
| **P1-2** | 4 个 span 小节标签升级为 H2（5 个语义小节） | 结构化长尾覆盖 | **最高** | 低 |
| **P1-3** | 24 页写差异化描述（当前平均 11 词） | 全部产品词 | **最高** | 低（需文案） |
| **P1-4** | FAQ 按品类分化（当前 24 页字节级相同） | 长尾问句 | 高 | 低 |
| **P2-1** | `SLUG_KEYWORD_OVERRIDE` 落地（机制已建、全空） | 每页主词 | 高 | 低 |
| **P2-2** | 非英语 title 不再落枚举常量（**100 个 URL**） | 5 语种全部 | 高 | 中 |
| **P2-3** | desc 尾部模板句去重 + 断词修复 | CTR | 中 | 低 |
| **P3** | 图片文件名 + alt 重写（**134 张**） | 图片搜索（弱信号） | 低中 | 中高（4 处同步） |
| **P4** | 恢复 `led sports lighting` 落地页 + 6 个品类独立 URL | 品类词（当前 0 落地页） | 高 | 中 |

**一句话**：现在 24 个产品页的**实质量化是「94.3% 的正文 = 6 条全站共享 FAQ + 11 词产品描述」**。
Google 看到的是 24 个近乎重复的 doorway 页面。文件名是弱信号，正文与语义层级才是主战场。

---

## 1. 实证：当前产品页的真实构成

### 1.1 fl6m 页面解剖（`/products/fl6m/`）

| 区块 | 词数 | 占比 | 是否与本页产品相关 |
|---|---|---|---|
| 全页正文（去 nav/footer） | 3947 | 100% | — |
| **6 条共享 FAQ** | **3721** | **94.3%** | ❌ 与 fl6m 无关 |
| energy table | 93 | 2.4% | ✅ |
| ordering table | 79 | 2.0% | ✅ |
| `detail-desc` 产品描述 | **11** | 0.3% | ✅ |

**5 页抽样的产品描述词数**：

| slug | desc 词数 | 文本 |
|---|---|---|
| `rt410-series` | 22 | Olympic-grade, HDTV-ready sports lighting…（唯一像样的一个） |
| `vsp-xxxxw-9m-yp` | 17 | Vision Strobe Protection system for broadcast venues… |
| `fl6m` | 11 | FL6M modular floodlight configuration — part of the M Series family. |
| `rt220ub` | 10 | Building Security ,Packing lots, residential area… |
| **`rt590fl-s`** | **1** | **`RT590FL-S`**（零内容） |

### 1.2 FAQ 跨页字节级相同

5 个产品页的 6 条 FAQ 文本 hash **完全一致**（`-2711728995917784323`）。
问的是 flicker / DIALux / efficacy / IP66 / HID 节能 / modular — 24 个页面问同一批问题，
其中 8 个是投光、4 个是路灯、2 个是配件。Google 判为 boilerplate。

### 1.3 H1 与标题层级

```
H1 × 1  = "FL6M"                        ← 纯型号，零关键词
H2 × 1  = "Product FAQ"
H3 × 1  = "Request a Sample"
```

被 Google 当作小节标题的字段全部是 `<span>`，不是 heading：

- `Beam Angle Type:` → `<span class="detail-beam-angle-label">`（`templates/product_detail.html:150`）
- `Dimensions:` → `<span>`（`:154`）
- `ENERGY AND PERFORMANCE DATA:` → `<span>`（`:166`）
- `ORDERING INFORMATION:` → `<span>`（`:184`）

⇒ **「photometric / beam angle / ordering guide / certifications」这四类长尾，页面有数据但没有语义标记。**

- 无可见面包屑（只有 JSON-LD `BreadcrumbList`）⇒ 爬虫与用户都看不到层级。
- 无 related products 模块。`product_detail.html:1001` 只有 `related_projects`，
  且实测 fl6m 页内 `related` 出现 0 次 ⇒ **该产品无任何相关内链**。
- 内链只有 sidebar（每页 24 个分类链接），无上下文内链。

### 1.4 6 个 FL\* 子系列描述雷同（doorway 特征）

```
fl1m  "FL1M modular floodlight configuration — part of the M Series family."
fl4m  "FL4M modular floodlight configuration — part of the M Series family."
fl6m  "FL6M modular floodlight configuration — part of the M Series family."
…（fl9m / fl12m / fl16m 同构）
```
只替换了型号数字。6 个 URL 争同一批词，页间无差异化。

---

## 2. 实证：Title / Meta Description 缺陷

### 2.1 P0 — `rt220ub` 型号数据错误，且与 fl1m 撞词

`pages_product` 与 `seed_data.json` **双向一致**（不是同步漂移，是录入错误）：

| 字段 | DB/seed 现值 | 正确值来源 |
|---|---|---|
| `slug` | `rt220ub` | — |
| `name` | `RT220UB` | — |
| **`model_number`** | **`FL1M-80W`** ❌ | `energy_data[0].value = "RT220UB"`；`ordering_info[1] = "40W"` |

线上实测：
```
/products/rt220ub/  <title>LED Flood Lights FL1M-80W | SolarOne</title>       ← 用的是别人的型号
/products/fl1m/      <title>LED Area & Site Lighting FL1M-80W-30K-S | SolarOne</title>
```
后果：① 型号与 `ordering_info`（FloodLight 40W）、`energy_data`（RT220UB, 40W, 5200lm）自相矛盾；
② 两个页面主词撞 `FL1M-80W`；③ 用户点进来看到「RT220UB」H1 配「FL1M-80W」型号，转化直接崩。
`Model Number:` 行同样渲染 `FL1M-80W`（`product_detail.html:186`）。

### 2.2 P0 — 8 个产品缺 `power` 字段

`power` 为空 ⇒ `build_seo_title`（`pages/utils.py:419-420`）与 `build_seo_description`（`:439-440`）
都无法追加 `— {power}` 与 `delivers {power}`，丢掉全部功率长尾修饰：

| slug | model_number 里的 W | `power` 字段 | title 是否含 W |
|---|---|---|---|
| `fl1m` | FL1M-**80W**-30K-S | 空 | 靠型号 ✅ |
| `rt390fl` | RT390FL-**80W** | 空 | 靠型号 ✅ |
| `rt400hb` | RT400HB-**130W** | 空 | 靠型号 ✅ |
| `rt500hb` | RT500HB-**280W** | 空 | 靠型号 ✅ |
| `rt590fl-s` | RT590FL-**160W** | 空 | 靠型号 ✅ |
| `rt420fs-s` | RT420FS-S**100W** | 空 | 靠型号 ✅ |
| `rt220ub` | FL1M-80W ❌ | 空 | ❌ |
| `rt600sl-t` / `rt820sl-t` | RT600SL-T（无 W） | 空 | ❌ |

前 6 个只是没进 `power` 字段（型号里已含），真正缺 W 的是 **rt220ub / rt600sl-t / rt820sl-t**，
且 desc 少了 `delivers 40W of high-efficiency LED output` 这类长尾句式。

### 2.3 P1 — 非英语 100 个 URL 的 title 落原始枚举常量

根因：`_seo_keyword()`（`pages/utils.py:223`）非英语走
`localized = obj.t('category', lang) if hasattr(obj,'t') else kw`。
`translate()`（`pages/utils.py:51-54`）在缺译时**回落英文原值**，而 `product.category` 存的是枚举串：

```python
# pages/views/utils.py::_DictProduct.__init__ — 无 category 翻译时
'AREA_SITE' | 'SPORTS_LIGHTING' | 'FLOODLIGHT' | 'HIGHBAY_LOWBAY' | 'ROADWAY' | 'ACCESSORY'
```

线上实测（每语种抽 6 个 slug）：

| slug | en | fr | de | ru | ar |
|---|---|---|---|---|---|
| `fl6m` | LED Area & Site Lighting FL6M-480W-30K-S | **AREA_SITE** FL6M-480W-30K-S | **AREA_SITE** … | **AREA_SITE** … | **AREA_SITE** … |
| `rt590fl-s` | LED Flood Lights RT590FL-160W | **FLOODLIGHT** … | **FLOODLIGHT** … | **FLOODLIGHT** … | **FLOODLIGHT** … |
| `rt820sl-t` | LED Roadway & Street Lights RT820SL-T | **ROADWAY** … | **ROADWAY** … | **ROADWAY** … | **ROADWAY** … |
| `mseries-gs` | LED Lighting Accessories Glare Shield… | **ACCESSORY** … | **ACCESSORY** … | **ACCESSORY** … | **ACCESSORY** … |

**24 产品中只有 4 个有 `category` 翻译**（`m-series` / `rt410-series` / `rgb-rgbw` / `vsp-*` 两款）
⇒ **20 × 5 = 100 个 URL 的 title 首个词是 `AREA_SITE` 之类的内部枚举**。

而这 4 个有翻译的也**语义错位**：`fr/rt410-series` → `Projecteur`（法语「投光灯」），
不是 `CATEGORY_KEYWORD['AREA_SITE'] = 'LED Area & Site Lighting'` 的法语对应
（应为 `éclairage d'aire et de site` 等）。⇒ 非英语页面实际存在**两套互不兼容的命名**。

### 2.4 P1 — 非英语 meta description 直接落英文原文

```
/fr/products/fl6m/   desc = "FL6M modular floodlight configuration — part of the M Series family."  (英文)
/ru/products/rt590fl-s/  desc = "RT590FL-S"   (1 个词)
```
`_DictProduct.seo_description()`（`pages/views/utils.py`）非英语走 `fit_description(self.t('description', lang))`，
`t()` 缺译回落英文 ⇒ hreflang 声明 `fr` 但正文/desc 全英文，语种信号自相矛盾。

### 2.5 P1 — 英文 desc 尾部模板句 + 断词

**全部 24 条**都以同一句结尾：
`for professional sports, industrial and commercial lighting projects.`

且 6 条在 160 字符处硬切在词中：
```
fl4m  D160  …for professional sports, industrial and commercial lighting pro...
m-series D160 …for professional sports, industrial and commercial lighting proje...
```
- 重复：24 页同尾 ⇒ boilerplate 信号。
- 断词：最后 ~20 字符是半截单词，信息量为 0。
- 语义错：`rt220ub`（保安/堆场/广告牌）、`rt600sl-t`（路灯）页面写 "professional sports"。

### 2.6 P2 — title 长度与 token 浪费

| slug | title | 长度 | 问题 |
|---|---|---|---|
| `mseries-gs` | LED Lighting Accessories Glare Shield for M series \| SolarOne | **61** | 超 SERP 预算，尾部被截 |
| `m-series` | … M Series — **80~1280W+** \| SolarOne | 56 | 型号位是营销话术，非搜索词 |
| `rt220ub` | … **FL1M-80W** \| SolarOne | 36 | 撞词 + 错误 |

---

## 3. 实证：图片（文件名 / alt / 配图正确性）

### 3.1 P1 — 跨 slug 借用配图导致「图与页不符」

`seed_data.json` 的 `beam_angle_image` / `dimension_image` 字段指向**别的产品的目录**：

| 页面 | 引用的图 | 实际在哪个产品目录 | 问题 |
|---|---|---|---|
| `fl1m` `fl4m` `fl6m` `fl9m` `fl12m` `fl16m` `fl9m-rgbw` | `beamangle-12183050.webp` | **`fl12m/`** | 6 页共用 fl12m 的光束角图 |
| `vsp-xxxxw-9m-yp` / `-12m-yp` | `beamangle-12183050.webp` | **`fl12m/`** | 体育场灯用错光束角图 |
| `rt590fl-s` | `beamangle-3050120.webp` | **`rt390fl/`** | 160W 用 80W 的角度图 |
| `rt390fl` | `beamangle-3050120.webp` | `rt390fl/` | ✅ |
| `rt500hb` | `rt400hb-beamangle-254590.webp` | **`rt400hb/`** | 280W 用 130W 的角度图 |
| `rt820sl-t` | `rt600sl-beamangle70-140.webp` | **`rt600sl-t/`** | 820W 用 600W 的角度图 |
| `rt420fs-s` | `beamangle-120d-1.webp` | **`rt220ub/`** | 100W 用 40W 的角度图 |
| `rt410-series` | `rt410-3d-view.webp` | **`rt410-rgbw/`** | 尺寸图错 |

**这是正确性问题，不只是 SEO** —— 页面把错误的配光曲线给到潜在客户。
Google Images 对「图文不符」直接降权，且这是跳出率信号。

### 3.2 P2 — 文件名问题分布（134 个产品图）

| 问题 | 数量 | 样例 |
|---|---|---|
| 纯序号结尾、无语义 | **80** | `fl6m-01.webp` … `fl6m-04.webp` |
| 含大写字母 | 7 | `VSP9M-01.webp`、`RT600SL-T.webp`、`RT600SL-dimension-1.webp` |
| 含下划线 | 1 | `Glare_shield_of_RT410.webp` |
| 分辨率后缀 | 10 | `fl6m-ngs-3d-view-540p.webp`、`rgbw-rt410-855p-01.webp` |
| **拼写错误** | **3** | `tr590-3d-view.webp`（应 `rt590`）、`rt400hb-barnner-02.webp`、`rt500hb-barnner-01.webp`（应 `banner`） |
| 前缀与 slug 不符 | 4 | `rt500hb/hb500-02.webp`、`rt390fl/rt390-*.webp`、`rt420fs-s/rt420fl-*.webp` |

`docs/image-seo-naming-spec.md` 自己的结论是「文件名是**弱信号**，只影响图片搜索」——
本次审计同意该判断：**134 张改名不应进第一批**（要同步 media/static/DB/seed 四处，§1 铁律）。

### 3.3 P2 — alt 文本零长尾

`enrich.py:128-140` 的 `_gallery_alt()` 输出：
```
FL6M — Area and Site — view 1
RT220UB — Flood Lighting — view 1
```
- `Area and Site` 来自 `_PRODUCT_CAT_TO_SIDEBAR_LABEL`（**侧栏导航名**，不是搜索词）。
- `view 1/2/3/4` 零信息。
- 没有：型号全称、功率、光束角、认证。

对比可用素材（都已在页面上，只是没写进 alt）：`480W` / `18~50°` / `IP66` / `10kV` /
`3000~5700K` / `70~95 CRI` / `Bridgesun` / `Inventronics`。

DB 侧有 `ProductImage.alt_text` 字段（`enrich.py:180` 优先用），**⇒ 支持后台逐张覆盖，无需改代码路径**。

### 3.4 P3 — 10 个 URL 无 image sitemap

`sitemap.xml` 59 个 URL 中 10 个缺 `image:image`：
`/`、`/products/`、`/projects/`、`/projects/football/`、`/projects/tennis/`、`/news/`、`/about/`、`/privacy/`、`/terms/`、`/contact/`
⇒ 集合页的卡片图不进图片索引。产品/项目/新闻页 49 个都有（实测 416 个 `image:image`）。

---

## 4. 实证：URL 架构缺口（品类词 0 落地页）

`CATEGORY_KEYWORD`（`pages/utils.py:130-139`）定义了 8 个品类词，
`docs/keyword-inventory.csv` 把它们全部指向 **`/products/`**（单一 URL）：

```csv
LED Area & Site Lighting,en,commercial,category,/products/,
LED Stadium Lights,     en,commercial,category,/products/,
LED Flood Lights,       en,commercial,category,/products/,
High Bay & Low Bay LED Lights, en,commercial,category,/products/,
LED Roadway & Street Lights,  en,commercial,category,/products/,
```

实测 `/products/?category=FLOODLIGHT`：
```
canonical = https://www.solaronelighting.com/products/     ← 指回列表页
<title>   = "LED Lighting Products — SolarOne Professional Lighting"   ← 未变
H1        = "Our Products"
```
⇒ **筛选态不可索引，6 个品类词没有自己的落地页**，只能靠 24 个产品页的 title 竞争。

同时：`/products/sports-lighting/`（承载 `led sports lighting` 390/mo KD15）已 **301 到 `/products/`**（v1.10.0 决策），
`/sports-lighting/` 现在 **404**。⇒ 唯一有量级记录的 sports 品类词当前**无落地页**。

已存在的品类页只有 `/projects/football/`、`/projects/tennis/`（项目侧，不是产品侧）。

---

## 5. 落地方案

### 阶段 P0 — 数据正确性（无风险，先做）

| # | 改动 | 文件 / 位置 | 同步要求 |
|---|---|---|---|
| P0-1 | `rt220ub.model_number`: `FL1M-80W` → `RT220UB-40W` | `pages_product` + `seed_data.json` | DB 用 `.update()`（不触发 post_save）→ 显式 `python -m pages.seed_sync --json` |
| P0-2 | 补 `power`：`rt220ub=40W`、`rt600sl-t`/`rt820sl-t` 按 `ordering_info` 填 | 同上 | 同上 |
| P0-3 | 修 3 个拼错文件名 + 消除 8 处跨 slug 借图 | `static/images/products/**` + seed 图片字段 | **需先确认真实光束角/尺寸图**（见 §5.1） |

⚠️ **P0-3 前置**：跨 slug 借图有可能是「同一款光学平台共用一张角度图」的设计决策，
而不是录错。**动手前需业务确认**每个系列的角度/尺寸图是否真的不同。
若确实不同 ⇒ 补新图；若相同 ⇒ 改文件名成中性名（如 `beam-angle-m-series.png`）并在 alt 写清系列。

### 阶段 P1 — 内容与语义（主战场，收益最高）

| # | 改动 | 位置 | 验收 |
|---|---|---|---|
| P1-1 | H1 → `{{品类词}} {{型号}} {{功率}}`（保留原型号在 `<bdi>`）；如 `LED Modular Flood Light FL6M 480W` | `product_detail.html:73,79` / `product_overview.html` | 每页 H1 恰好 1 个且含品类词+型号 |
| P1-2 | 4 个 `<span>` 小节标签 → `<h2>`：Applications / Technical Specifications / Photometric Data / Ordering Guide / Certifications | `product_detail.html:150,154,166,184` | 渲染后 H2 = 5 |
| P1-3 | 24 页各写 **80–150 词**差异化描述（当前 11 词），必含：应用场景 / 功率+流明+效率 / 光束角 / CCT / IP66+10kV / 模块化 / 认证。6 个 FL\* 逐款差异化 | seed `description` + `translations[lang]['description']` | desc 词数 ≥ 80 |
| P1-4 | FAQ 按品类分 4 套（sports / flood / highbay+roadway / accessory），每套 5–6 条与该品类相关 | `views_products.py:40-86` `PRODUCT_FAQ` | 24 页 FAQ hash 不再全等；4 套文本存在 |
| P1-5 | 加可见面包屑 + Related Products（同系列兄弟页） | `product_detail.html` | 每页 ≥1 面包屑 + ≥3 相关产品内链 |
| P1-6 | 修 6 条 160 字符断词 desc + 6 个 FL\* 雷同描述 | `pages/utils.py:443-445` | desc 无 `...pro...` 断词 |

### 阶段 P2 — Title / Description 公式

| # | 改动 | 位置 |
|---|---|---|
| P2-1 | 填 `SLUG_KEYWORD_OVERRIDE`：sports 类（`vsp-*`×2、`rt410-series`、`m-series`）→ `LED Stadium Light` / `Modular LED Stadium Light`；flood 类 4 款 → `LED Flood Light`；highbay 2 款 → `LED High Bay Light`；roadway 2 款 → `LED Street Light` | `pages/utils.py:144` |
| P2-2 | `CATEGORY_KEYWORD` 扩为 6 语种映射（8 品类 × 5 语 = 40 条），非英语**不得回落枚举串**；若无译文则回落英文词（`en` 词也比 `AREA_SITE` 强） | `pages/utils.py:130` + `_seo_keyword()` |
| P2-3 | desc 尾部模板句按品类替换（flood → `for yards, parking lots and facades`；roadway → `for streets and highways`…） | `build_seo_description` |
| P2-4 | `mseries-gs` title 压到 ≤ 60（参考 `_fit_project_title` 的词边界裁剪法） | `pages/utils.py` |
| P2-5 | 修 `fr/rt410-series` = `Projecteur` 的语义错位（与 `CATEGORY_KEYWORD` 法语词统一） | seed `translations.fr.category` |

### 阶段 P3 — 图片（低 ROI，但修正确性优先）

- 补齐 10 个集合页的 `image:image`（`views_other.py:sitemap_xml`）。
- alt 模板改为：`<型号> <功率>W <品类词> — <视角/用途>（<角度> beam angle / IP66 / dimension）`；
  优先走 DB `ProductImage.alt_text` 逐张覆盖（`enrich.py:180` 已支持）。
- 文件名改名单独排期（134 张 × 4 处同步），**不与前 3 批混做**。

### 阶段 P4 — 架构（需用户批准）

1. **恢复 `/sports-lighting/`**（`led sports lighting` 390/mo KD15 是 keyword-inventory 里唯一有量的 sports 词，
   现在 404）。做成 Tier-1 hub：banner + 场景分区 + 相关产品（vsp/rt410/m-series）+ 相关项目 + 自身 FAQ。
2. **6 个品类独立 URL**：`/products/area-site/`、`/products/flood-lighting/`、`/products/high-bay/`、
   `/products/roadway/`、`/products/accessory/`、`/products/modular/`。
   必须在 `views_other.py:sitemap_xml` 登记 + `product_overview.html` 复用；否则 24 页会与品类页争词。
3. 已下线 URL 走 `pages/redirects.py` 登记 301（铁律 14）。

---

## 6. 验证与铁律

- **改前必读** `.workbuddy/memory/MEMORY.md` 铁律，尤其：
  - 铁律 2：改文案**三处同改**（DB / `seed_data.json` / `pages/seed_data.py`），且
    `seed_sync` 默认 **DB→JSON** ⇒ 只改 JSON 会被静默覆盖。
  - 铁律 1：`models.py` property ↔ `views/utils.py` 的 `_DictProduct` **双路径同改**。
  - 铁律 3：新守卫必做**变异探针**（改实现确认变红 → 还原 → `git diff --stat` 零残留，
    **不用 `git checkout`**）。
  - 铁律 4/4b：守卫期望值必须是**独立产品决策**，禁从实现常量派生。
  - 铁律 5：改版本号**先改再跑测试**（VERSION / settings.APP_VERSION / llm.txt 三处）。
  - 铁律 6：`/media/` 线上 404 ⇒ 目录枚举只认 `static/`。
  - 铁律 13：断言扫全文会被自己写的注释反噬 ⇒ 需 `_markup()` 剥注释。
  - 铁律 15：本地 `DEBUG=False` ⇒ **改模板后必须重启 runserver**。
  - 铁律 28：`utils.py` / `models.py` / `views_other.py` / `urls.py` 是 **CRLF** ⇒ 只能 Python 字节级替换。
- **验收命令**（用户侧 PowerShell）：
  ```powershell
  # P0-1 撞词是否消除
  curl.exe -s https://www.solaronelighting.com/products/rt220ub/ | Select-String '<title>'
  # P2-2 枚举常量是否清零（改完后应无输出）
  curl.exe -s https://www.solaronelighting.com/fr/products/fl6m/ | Select-String 'AREA_SITE'
  ```
- **回归**（改完只跑相关分组，全量 >20 分钟）：
  `tests_seo_*` / `tests_image_srcset` / `tests_static_assets` / `tests_release_metadata` / `tests_project_*`
- **AI/子代理结论必须 curl 交叉验证**（铁律 30）。本报告所有数字均已线上 curl 实测。

---

## 7. 未决问题（需业务/用户输入）

1. **跨 slug 借图**是设计还是录错？（阻塞 P0-3）
2. **8 个非英语品类词**是否需要母语复核？（P2-2 的 40 条词）
3. **6 个 FL\* 是否算 6 个独立可索引页**？若产品线同质，可考虑合并为 1 页 + 变体参数
   （但需评估现有 6 个 URL 的收录量后再定，不能直接合）。
4. `/products/` 列表页只展示 6 张卡片（`productspagecards`），其余 18 个产品仅靠 sidebar 触达
   ⇒ **18 个产品页的内部链接深度只有 1 层但权重低**。是否需要「全系列」区块？
