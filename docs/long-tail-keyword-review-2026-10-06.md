# 长尾关键词方案 · 复核结论与执行决策

> 日期：2026-10-06 · 增补 `docs/long-tail-keyword-plan-2026-10-06.md`（原文档 = 审计发现，本文 = 复核结论 + 方案对比）
> 触发：用户对原文档 §7 的三个未决问题作出答复 —— ① M series 配光曲线相同，借用 beam angle 没问题；② 复核；③ 细说方案和结果。
> 全部结论线上 curl + DB/seed 双向核对，无估算。

---

## 摘要：复核后发现的 3 个新 P0（比原文档更严重）

| # | 发现 | 严重度 | 原文档未收录原因 |
|---|---|---|---|
| **N0-1** | **`AREA_SITE` / `FLOODLIGHT` 等内部枚举在页面上肉眼可见** | 🔴 P0 | 上一轮只扫 `<title>`，没查可见 DOM |
| **N0-2** | **3 个产品功率字段自相矛盾**（fl9m 630 vs 720、fl12m 1000 vs 960） | 🔴 P0 | 上一轮只查 `power` 是否为空，没做跨字段交叉 |
| **N0-3** | **rt220ub 自己的光束角图是 120°，但它只卖 100°** | 🔴 P0 | 上一轮只查「是否跨 slug」，没查「图与售卖选项是否对应」 |

原文档 §1 的 3 个发现（94.3% 共享 FAQ、rt220ub 型号录错、100 个非英语 URL 落枚举）**全部复核成立**，见 §4。

---

## 一、问题① 复核：跨 slug 借图的正确性判定

### 1.1 判定方法（比「是否跨 slug」更严）

原文档用「引用路径所在目录 ≠ 产品 slug」判定借图，这个判据**太粗**——它把「同光学平台合法共用」和「真的借错了」混在一起。
本次改用**三重证据交叉**：

| 判据 | 数据源 | 意义 |
|---|---|---|
| ① 光束角选项是否一致 | `ordering_info[4]` | 同光学平台 ⇒ 选项集合必然相同 |
| ② 物理尺寸/重量/EPA 是否一致 | `energy_data` 的 `L"×W"×H"` / `Approximate Weight` / `EPA` | 同平台 ⇒ 三者必然一致 |
| ③ 图上渲染的角度标签 | 直接读图（WebP 解码后目视） | 图上标签 = 图代表的真实角度 |

### 1.2 M 系列：✅ 复核通过（用户判断正确，且证据支持）

| 产品 | 借用图 | ① 光束选项 | ② 尺寸 | ② 重量 | 结论 |
|---|---|---|---|---|---|
| `fl1m` `fl4m` `fl6m` `fl9m` `fl12m` `fl16m` `fl9m-rgbw` | `fl12m/beamangle-12183050.webp` | 全部 `12/18/30/50` ✅ | **各不同**（218×235×137 → 738×738×343） | 2.3 → 42.5kg | ✅ 用户确认配光曲线相同，**合法** |

**读图实证**：`fl12m/beamangle-12183050.webp` = 2000×400，4 联图，标签 `12° / 18° / 30° / 50°`，
cd 值分别 ~4500 / 5000 / 3000 / 1200。角度标签与 7 个产品的 `ordering_info[4]` **完全对应**。

⚠️ 一点补充（不影响结论）：图中 cd 数值（12° 峰 ~4500 cd）对应的是 **FL12M 1000W** 的量级。
若 7 页共用同一张图，则 80W 的 fl1m 页面显示的峰值 cd 也是 4500 —— **数量级对不上 80W 灯具**。
配光**曲线形状**相同（用户判断）✅，但**绝对光强值**不同。
⇒ 建议：图 alt 或图注写明「optical distribution pattern (shape reference)」，或为 fl1m 单独出图。
**这是文案级修补，不需要新拍图。**

### 1.3 VSP ×2：⚠️ 需业务单独确认（用户未涵盖）

| 产品 | 光束选项 | 尺寸 | 图 | 判定 |
|---|---|---|---|---|
| `vsp-xxxxw-9m-yp` | `12/18/30/50` ✅ 同 M 系列 | **400×355×600mm（塔式）** | 借 `fl12m/` | ⚠️ 光束选项相同，**物理形态完全不同** |
| `vsp-xxxxw-12m-yp` | `12/18/30/50` ✅ 同 M 系列 | **400×355×1000mm（塔式）** | 借 `fl12m/` | ⚠️ 同上 |

FL 系列是**矩阵式**（553×368×343 horizontally），VSP 是**竖向塔式**（400×355×1000）。
同为 12 模组，光束选项可以相同，但**配光曲线形状未必相同**（矩阵 vs 竖排的出光角分布通常有差异）。
⇒ **需确认**：VSP 的 9M/12M 是否与 FL9M/FL12M 用同一套光学模组且排列方式相同？
若塔式排列 ⇒ 应补 VSP 自己的配光图。

### 1.4 其余 5 处跨 slug 借图：❌ 复核为真错

| 借用方 | 借的图 | ① 光束选项对比 | ② 尺寸/重量对比 | ③ 图上标签 | 判定 |
|---|---|---|---|---|---|
| `rt410-series` ← `rt410-rgbw`（尺寸图） | `rt410-3d-view.webp` | rt410-series `30/50/100/80×40/110×60`<br>rt410-rgbw `12/18/30/50` **不一致** | **418×400×172mm = 418×400×172mm 完全相同**<br>13.5kg = 13.5kg 完全相同 | — | ✅ 尺寸图**合法**（同物理平台）<br>但 EPA 1.4 vs 0.26 矛盾 |
| `rt410-series` ← `rt410-rgbw`（光束图） | `beamangle183050100.webp` | 同上**不一致** | 同上 | `18/30/50/80-40/100-60/100` | ❌ 图上有 **18°**（页面不卖）、页面卖 **110×60**（图上是 100-60） |
| `rt590fl-s` ← `rt390fl` | `beamangle-3050120.webp` | 都是 `120/30` ✅ | 589×301×248mm/12.8kg vs 369×294×336mm/8.5kg **不同** | `30/50/120` | ⚠️ 选项一致但**平台不同**；图上多一个 50° |
| `rt500hb` ← `rt400hb` | `rt400hb-beamangle-254590.webp` | 都是 `25/45/90` ✅ | 500×500×457mm/16kg vs 395×395×401mm/8kg **不同** | `25/45/90` | ⚠️ 同上 |
| `rt820sl-t` ← `rt600sl-t` | `rt600sl-beamangle70-140.webp` | 都是 `70×140` ✅ | 821×350×100mm/18.3kg vs 596×350×100mm/12.5kg<br>**截面 350×100 相同，长度不同** | `70/140` | ⚠️ 可能是同截面不同长度（待确认） |
| `rt420fs-s` ← `rt220ub` | `beamangle-120d-1.webp` | rt420fs-s `120`<br>rt220ub `100` **不一致** | 420×390×125mm/8kg vs 257×207×128mm/2.3kg **不同** | `120°` | ❌ **图属于 rt420fs-s（卖 120°），rt220ub 才是错的一方**（见 N0-3） |
| `mseries-gs` ← `fl9m-rgbw` | `fl9m-gs-3d-view-540p.webp` | 无光束数据 | 「gs」= glare shield，是 **FL9M 的遮光罩** | — | ⚠️ M series 遮光罩 ≠ FL9M 遮光罩 |
| `glare-shield-for-rt410` ← `accessory` | `rt410-glare-shield-01.webp` | — | 同一款 RT410 遮光罩，从聚合页借用 | — | ✅ **合法**（`accessory` 是分类聚合页） |
| `fl9m-rgbw` / `rt410-rgbw` ← `rgb-rgbw` | `...certification-ip66-ik08.webp` | — | 认证徽标，全系列通用 | — | ✅ **合法** |

### 1.5 结论：14 处借图分类

| 类别 | 数量 | 处理 |
|---|---|---|
| ✅ 合法（用户确认 + 证据支持） | 9（M 系列 7 + 认证 1 + 遮光罩 1） | 保留 |
| ✅ 合法（证据支持） | 1（rt410-series 尺寸图） | 保留 |
| ⚠️ 待业务确认 | 5（VSP×2、rt590fl-s、rt500hb、mseries-gs） | 问业务，不动 |
| ❌ 确认错误 | 2（rt410-series 光束图、rt420fs-s↔rt220ub 归属） | P0-3 处理 |

---

## 二、问题③ 细说：6 个 FL\* 是否合并为 1 页 + 变体

### 2.1 先看数据：这 6 页到底有多少独有内容

| slug | energy 行 | specs | ordering 列 | gallery | **独有值** |
|---|---|---|---|---|---|
| `fl1m` | 17 | 6 | 9 | 4 | 80W / 10,400lm / EPA 0.26 / 218×235×137 / 2.3kg |
| `fl4m` | 17 | 6 | 9 | 4 | 320W / 41,600lm / EPA 1.05 / 368×368×343 / 11.0kg |
| `fl6m` | 17 | 6 | 9 | 4 | 480W / 62,400lm / EPA 1.58 / 553×368×343 / 16.8kg |
| `fl9m` | 17 | 6 | 9 | 4 | 720W / 93,600lm / EPA 2.37 / 553×553×343 / 26.0kg |
| `fl12m` | 17 | 6 | 9 | 4 | 960W / 124,800lm / EPA 3.16 / 553×738×343 / 33.0kg |
| `fl16m` | 17 | 6 | 9 | 4 | 1280W / 166,400lm / EPA 4.16 / 738×738×343 / 42.5kg |

**17 行 energy_data 的行标签 6 页完全相同**（Series Name / Lumen Output / System Wattage / CRI / CCT /
输入电压 ×2 / L70 / 工作温度 / 浪涌 / IP / EPA / 尺寸 / 重量 / 材质 / LED 品牌 / 驱动），
**只有数值不同**。ordering 9 列中 **col2/4/5/7/8 完全相同**，col0（型号）/col1（功率）/col3（电压）/col6（控制）不同。

⇒ 结构上 6 页是**同一张表换 6 组数值**。这是「薄」的结构，不是「重复」的结构。

### 2.2 反对合并的最强论据：**采购方是按功率选型的**

| slug | 功率 | 真实可装场景（按 EPA + 流明推） |
|---|---|---|
| `fl1m` | 80W / 10,400lm / 2.3kg | 80W 投光**装不了体育场**。真实定位：小型场地、园区、建筑立面、替换 250W HID |
| `fl4m` | 320W / 41,600lm | 网球场、社区场地、训练场 |
| `fl6m` | 480W / 62,400lm | 中小学校球场、训练基地 |
| `fl9m` | 720W / 93,600lm | 俱乐部级球场、网球中心 |
| `fl12m` | 960W / 124,800lm | 市级赛场 |
| `fl16m` | 1280W / 166,400lm | 大型球场、broadcast 级 |

6 款覆盖的场景跨度从「替换 250W HID」到「大型 broadcast 球场」，**中间没有重叠**。
合并成 1 页 = 采购方要在一个页面里滚动一张 6 行对比表才能找到自己能用的那款。
**这是把 B2B 选型路径改窄了，不是改宽了。**

### 2.3 三方案对比

| 维度 | A：保持 6 页 + 差异化文案 | B：合并 1 页 + 变体 tab | **C（推荐）：hub + 6 页重新定位** |
|---|---|---|---|
| URL 变动 | 无 | 6 个 URL → 301 到 hub | **无** |
| 泛词竞争 | ❌ 6 页都打 `LED Area & Site Lighting` 内耗 | ✅ 泛词只 1 页 | ✅ hub 打泛词，6 页打功率长尾 |
| 功率长尾 | ✅ 每页一个 | ❌ 同页无法同时排 480W 和 1280W | ✅ 每页一个 |
| 选型路径 | ✅ 6 个入口 | ❌ 1 个页面内查表 | ✅ 6 个入口 + hub 横向对比 |
| 301 风险 | 无 | 🔴 现有排名信号转移，hub 未必接得住 | 无 |
| 现有链接 | 不变 | 需在 `redirects.py` 登记 6 条 | 不变 |
| 工作量 | 6 × 100 词文案 | 模板改造 + 301 + 对比表组件 | 6 × 100 词文案 + 2 个模板 + title 公式 |
| **净收益** | 中 | **低（负）** | **高** |

### 2.4 方案 C 详解

**C-1 hub 改造** —— `/products/m-series/`（已是 `page_layout='overview'`，模板 `product_overview.html`）

当前状态：H1 `M Series` + 1 段描述 + 规格条 + FAQ，**233 词**，内链只有 sidebar。
改造为真正的 Tier-1 hub：

| 新增区块 | 内容 | 目标词 |
|---|---|---|
| Applications 分区 | 体育场 / 网球场 / 机场 / 道路 / 高杆 5 个场景 | `modular LED stadium flood light` |
| **6 款对比表** | 功率 / 流明 / EPA / 尺寸 / 重量 / 光束角，每行链到对应子页 | `480W LED flood light` 等 |
| 选型指引 | 「80W 替换 250W HID / 320W 网球场 / 1280W 大型球场」 | `how to choose stadium lights` |
| Related Projects | 复用 `related_projects`（`views_products.py:346` 已注入，B 批次已写） | 内链 + 项目页反链 |

**C-2 子页 title 重新定位** —— 这是方案 C 的核心

现状 6 页 title 全部以 `LED Area & Site Lighting` 开头 ⇒ **6 页争同一个泛词**。

改法：把泛词从子页 title 移除，只在 hub 保留。子页 title 改为「型号 + 功率 + 具体品类」：

| slug | 现状 | 方案 C |
|---|---|---|
| `fl6m` | `LED Area & Site Lighting FL6M-480W-30K-S \| SolarOne` | `FL6M 480W Modular LED Flood Light \| SolarOne` |
| `fl12m` | `LED Area & Site Lighting FL12M-1000W-YYK-H-30 \| SolarOne` | `FL12M 960W Modular LED Flood Light \| SolarOne` |
| `fl16m` | `LED Area & Site Lighting FL16M-1280W-30K-H \| SolarOne` | `FL16M 1280W Modular LED Stadium Light \| SolarOne` |
| `fl1m` | `LED Area & Site Lighting FL1M-80W-30K-S \| SolarOne` | `FL1M 80W LED Area Flood Light \| SolarOne` |

⇒ 6 页主词互不相同，不再内耗；泛词交给 hub。

实现落点：`pages/utils.py:144` 的 `SLUG_KEYWORD_OVERRIDE`（**机制已建、全空**）
+ 新增 `SLUG_TITLE_MAXWATT` 之类的产品决策常量，或直接在 `translations.en.seo_title` 里写显式覆盖
（`get_seo_override()` 已支持，`pages/utils.py:190`）。

### 2.5 预期结果（判据，不是预测数字）

**明确不做流量预测**（无 GSC 基线数据，编数字违反 `seo-growth-plan.md:32` 的约定）。改为给出**可验证判据**：

| 判据 | 现状（实测基线） | 目标 | 验证方法 |
|---|---|---|---|
| FL 子页之间 title 首词是否重复 | **6/6 全部 `LED Area & Site Lighting`** | ≤ 1/6 | 改后跑 `build_seo_title` 全表比对 |
| 单页有效正文占比 | **5.7%**（94.3% 是共享 FAQ） | ≥ 60% | 线上 curl 抽 3 页计数 |
| 每页独有描述词数 | **11 词** | ≥ 80 词 | 从 `_load_seed()` 派生断言（铁律 7） |
| 非英语 title 含枚举常量 | **100 个 URL** | **0** | 六语种全表扫描 |
| 可见 DOM 里的枚举常量 | **24 页 hero label** | **0** | curl 抓 `series-hero-label` |
| 功率跨字段矛盾数 | **3** | **0** | 交叉核对脚本 |

---

## 三、问题② 复核：8 个非英语品类词

### 3.1 好消息：`i18n.py:_SIDEBAR_I18N` 已有现成译法，零新增翻译量

原文档说「需母语复核 40 条新词」。复核后发现**不用新造 40 条** —— 站内已有 6 个品类的成熟译法，
只是 `CATEGORY_KEYWORD`（`pages/utils.py:130`）目前**只有英文**：

| `CATEGORY_KEYWORD` 键 | `_SIDEBAR_I18N` 已有译法（站内正在用） |
|---|---|
| `AREA_SITE` | `Area and Site` → fr `Zone et Site` · es `Área y Sitio` · de `Bereich und Standort` · ru `Территория и площадка` · ar `المنطقة والموقع` |
| `SPORTS_LIGHTING` | `Sports Lighting System` → fr `Système d'Éclairage Sportif` · es `Sistema de Iluminación Deportiva` · de `Sportbeleuchtungssystem` · ru `Система спортивного освещения` · ar `نظام إضاءة رياضية` |
| `FLOODLIGHT` | `Flood Lighting` → fr `Projecteurs` · es `Proyectores` · de `Flutlicht` · ru `Прожекторное освещение` · ar `إضاءة فيضانية` |
| `HIGHBAY_LOWBAY` | `Highbay & Low Bay` → fr `Haute & Basse Baie` · es `Alta & Baja Bahía` · de `Highbay & Lowbay` · ru `Высокий и низкий пролёт` · ar `إضاءة عالية ومنخفضة` |
| `ROADWAY` | `Roadway` → fr `Éclairage Routier` · es `Alumbrado Vial` · de `Straßenbeleuchtung` · ru `Дорожное освещение` · ar `إنارة الطرق` |
| `ACCESSORY` | `Accessory` → fr `Accessoire` · es `Accesorio` · de `Zubehör` · ru `Аксессуар` · ar `ملحق` |

**6 个键全部有现成译法**（`MODULAR` / `OTHER` 两个键无产品使用，可暂不处理）。

### 3.2 候选词表（**待母语复核**，勿直接上线）

规则：在站内既有译法上加 `LED` 前缀 + 品类修饰词，保持与英文 `CATEGORY_KEYWORD` 的词序一致。

| 键 | en | fr | es | de | ru | ar |
|---|---|---|---|---|---|---|
| `AREA_SITE` | LED Area & Site Lighting | Éclairage LED de zone et de site | Iluminación LED de áreas y exteriores | LED-Beleuchtung für Außenflächen | Светодиодное освещение территорий | إضاءة LED للمناطق الخارجية |
| `SPORTS_LIGHTING` | LED Stadium Light | Projecteur LED pour stade | Proyector LED para estadio | LED-Stadionfluter | LED-прожектор для стадиона | كشاف LED للملاعب |
| `FLOODLIGHT` | LED Flood Lights | Projecteurs LED | Proyectores LED | LED-Flutlicht | LED-прожекторы | كشافات LED |
| `HIGHBAY_LOWBAY` | High Bay & Low Bay LED Lights | Luminaires LED haute et basse baie | Luminarias LED de alta y baja bahía | LED-High-Bay- und Low-Bay-Leuchten | LED-светильники High Bay и Low Bay | مصابيح LED عالية ومنخفضة |
| `ROADWAY` | LED Roadway & Street Lights | Éclairage routier LED | Alumbrado vial LED | LED-Straßenbeleuchtung | Дорожное освещение LED | إنارة الطرق LED |
| `ACCESSORY` | LED Lighting Accessories | Accessoires d'éclairage LED | Accesorios de iluminación LED | LED-Beleuchtungszubehör | Аксессуары для светодиодного освещения | ملحقات إضاءة LED |

**复核要点（给母语/译审的 3 个问题）**：
1. 法国/西语市场 LED 灯具常用「projecteur / proyector」还是「luminaire / luminaria」？站内既有译法用前者 ⇒ 保持一致但需确认是否符合当地采购习惯。
2. 德语 `Highbay` 站内**故意不译**（保留英文）—— 这是既有决策，需确认是否也适用于 SEO title。
3. 俄语 `Прожекторное освещение`（照明类别名词）vs `прожектор`（单数灯具）—— SEO title 应用哪个？

### 3.3 落地形态（关键设计决策）

`CATEGORY_KEYWORD` 的值会被用于**英文 title 主词**（搜索量已校准的英文词）。
非英语不应复用同一张表——

```python
# pages/utils.py —— 建议形态（🔴 需用户批准后实施）
CATEGORY_KEYWORD = { ... }              # 英文，保持不变（有校准数据）
CATEGORY_KEYWORD_I18N = {               # 新增：非英语，值为 None 表示"回落英文词"
    'AREA_SITE': {'fr': '...', 'es': '...', 'de': '...', 'ru': '...', 'ar': '...'},
    ...
}
```

**回落策略**（铁律：绝不回落枚举串）：
```
显式译文  →  英文 CATEGORY_KEYWORD  →  空串（不写品类词，只留型号）
```
🔴 **绝不能回落 `product.category`**（那是枚举串 `AREA_SITE`）—— 这正是当前 100 个 URL 的病根。

---

## 四、原文档 3 个主要发现的复核结果

| 原文档发现 | 复核方法 | 结论 |
|---|---|---|
| 94.3% 正文 = 6 条共享 FAQ | 重新按 `<div class="detail-faq">` 精确切片 + 5 页 hash 比对 | ✅ **成立**。FAQ hash 仍全等（`-2711728995917784323`） |
| `rt220ub.model_number = 'FL1M-80W'` | DB + seed + `pages/models.py:178` 三处查 | ✅ **成立，且找到根因**（见下） |
| 100 个非英语 URL 落枚举常量 | 六语种 × 24 slug 全表生成 title | ✅ **成立，100/100** |

### 4.1 `rt220ub` 型号错误的**根因**（比原文档更深一层）

`pages/models.py:175-181`：

```python
model_number = models.CharField(
    max_length=200, blank=True,
    default="FL1M-80W",              # ← 病根
    help_text='产品型号标识，示例：FL1M-80W-30K-S。新建产品时会自动填充默认值，可按需修改。',
)
```

新建产品时 `model_number` **自动填 `FL1M-80W`**。后台创建 `rt220ub` 时没改这个默认值 ⇒ 静默带上别人的型号。

⇒ **这是系统性问题，不是孤立录入错误。** 佐证：全库 24 个产品中，
5 个 `model_number` 为空（`mseries-gs` / `m-series` / `rgb-rgbw` / `accessory` / `glare-shield-for-rt410`），
只有 `rt220ub` 恰好等于这个默认值。

**修复必须两处**：
1. `rt220ub.model_number` → `RT220UB-40W`（数据修正）
2. `models.py` 的 `default=""` 去掉（机制修正，防复发）
   ⚠️ 改 `default` 会产生迁移，且可能影响后台新建表单的 `initial` 值 ⇒ 需确认无其他依赖。

### 4.2 型号前缀一致性扫描（新）

| slug | name | model_number | 判定 |
|---|---|---|---|
| `rt410-series` | RT410 Series | `RT410FL-260W-XXK-S` | ✅ 合理（RT410FL 是产品线真名，sidebar 也是 `RT410FL-S`） |
| `rt420fs-s` | RT420FS-S | `RT420FS-S100W` | ✅ 合理 |
| `rt220ub` | RT220UB | `FL1M-80W` | ❌ 唯一真错 |

---

## 五、N0-1 新发现：`AREA_SITE` 在页面上肉眼可见 🔴

原文档只扫 `<title>`，漏了可见 DOM。线上实测：

```html
<!-- templates/product_detail.html:72 / product_overview.html:76 -->
<span class="series-hero-label">{{ banner_label }}</span>
```
```python
# pages/views/views_products.py:333
context['banner_label'] = product.category_t   # ← category_t = translate(self,'category') = 枚举串
```

六语种实测（`/fr|de|ar/products/fl6m/`）：

| 位置 | 值 |
|---|---|
| `<title>` | `AREA_SITE FL6M-480W-30K-S \| SolarOne` |
| `series-hero-label`（**页面可见**） | `AREA_SITE` |
| H1 | `FL6M` |
| `detail-desc` | 英文原文（`FL6M modular floodlight configuration — part of the M Series family.`） |

⇒ **访客在页面上肉眼看到 `AREA_SITE` 这个数据库枚举码**，在 hero 图左上角，`product_detail.html:341` 有专门 CSS 样式（说明设计上是要显示的分类标签）。

**这是转化问题，不只是 SEO 问题。** 24 个产品页 × 6 语种 = 144 处。

修法（一行）：`views_products.py:333` 改用已存在且已翻译的 `product.category_display`
（`enrich.py:150-151` 走 `_PRODUCT_CARD_LABELS` / `_PRODUCT_CAT_TO_SIDEBAR_LABEL` + `_t()`，有 6 语种译法）。

---

## 六、N0-2 新发现：3 个产品功率字段自相矛盾 🔴

原文档只查 `power` 是否为空，**没做跨字段交叉**。本次交叉核对
（`specs.Power` / `power` / `energy_data.System Wattage` / `ordering_info[1]` / `model_number` 五个来源）：

| slug | 冲突值 | 各来源实况 | 线上表现 |
|---|---|---|---|
| **`fl9m`** | **630W vs 720W** | `specs.Power=720W` · `power=630W` · `energy=720W` · `ordering=720W` · `model=FL9M-720W-XXK-S` | title: `LED Area & Site Lighting FL9M-720W-XXK-S — 630W \| SolarOne`<br>desc: `delivers 630W ...`<br>页面 spec 条: **720W** ⚠️ 自相矛盾 |
| **`fl12m`** | **1000W vs 960W** | `specs.Power=1000W` · `power=1000W` · `energy=960W` · `ordering=960W` · `model=FL12M-1000W-YYK-H-30` | title: `...FL12M-1000W-YYK-H-30`<br>页面 spec 条: **1000W**<br>ENERGY 表: **960W** ⚠️ 自相矛盾 |
| **`rt220ub`** | 40W vs 80W | `specs` 空 · `power` 空 · `energy=40W` · `ordering=40W` · `model=FL1M-80W` ❌ | 见 §4.1 |

**判定**：`power` / `specs.Power` 是**孤立的错值**，四源交叉中 `energy_data` + `ordering_info` 一致占多数 ⇒ 以它们为准。
- `fl9m.power`：`630W` → **`720W`**
- `fl12m.power` / `fl12m.specs[Power]`：`1000W` → **`960W`**
  ⚠️ 但 `fl12m.model_number = 'FL12M-1000W-YYK-H-30'` 仍含 1000 ⇒ **需业务确认额定功率到底是 960 还是 1000**（可能是「模块 80W × 12 = 960W」vs「标称 1000W」的口径差）

**影响面**：`power` 进 `build_seo_title`（`pages/utils.py:419-420`）和 `build_seo_description`（`:439-440`）
⇒ 错值直接进 title 和 meta description，6 语种全中。

---

## 七、N0-3 新发现：rt220ub 自己的光束角图是错的 🔴

`rt220ub` 的 `beam_angle_image` = `own` 目录下的 `beamangle-120d-1.webp`（文件名自带 `120d`）。
**读图实证**：该图为 2000×400，标签 `120°`，cd 峰值 ~300。

但 `rt220ub.ordering_info[4]` = **`100=100°`** ⇒ **这个产品只卖 100° 配光，页面却放 120° 的配光图**。

而 `rt420fs-s.ordering_info[4]` = **`120=120°`** ⇒ **它才应该是这张图的真正归属**，
但它现在跨 slug 借用了 `rt220ub/` 目录下的这张图。

⇒ **根因是文件放错了目录**，不是「借图」。正确修法：
1. 把 `beamangle-120d-1.webp` 移到 `static/images/products/rt420fs-s/`
2. `rt420fs-s.beam_angle_image` 改为 own 路径
3. `rt220ub` **需要自己的 100° 配光图**（业务提供）⇒ 在此之前 `rt220ub.beam_angle_image` 置空 + 模板条件隐藏

⚠️ 模板 `product_detail.html:150-152` 已有 `{% if %}` 守卫（实测 `<img>` 只在有值时渲染），置空是安全的。

---

## 八、修正后的执行顺序

| 批次 | 内容 | 是否需业务输入 | 风险 |
|---|---|---|---|
| **P0-A** | `views_products.py:333` `banner_label` → `category_display`（消除 144 处可见枚举） | 否 | 低 |
| **P0-B** | `rt220ub.model_number` → `RT220UB-40W`；`models.py:178` 去掉 `default` | 否（机制变更需确认） | 低 |
| **P0-C** | `fl9m.power` → `720W` | 否 | 低 |
| **P0-D** | `rt410-series` 光束图：换用自己的图或调整 `ordering_info[4]` 与图对齐 | ⚠️ 需确认 110×60 vs 100-60 | 中 |
| **P0-E** | `beamangle-120d-1.webp` 归位到 `rt420fs-s/`；`rt220ub` 光束图置空 | ⚠️ 需 100° 新图 | 中（改路径） |
| **P1-A** | 24 页写 80–150 词差异化描述（6 个 FL\* 逐款按功率/场景差异化） | 需文案 | 低 |
| **P1-B** | 4 个 `<span>` → `<h2>`；H1 加品类词+功率 | 否 | 低 |
| **P1-C** | FAQ 按品类分 4 套（消除 24 页雷同） | 需文案 | 低 |
| **P2-A** | `SLUG_KEYWORD_OVERRIDE` 落地：FL\* 6 款按 §2.4 方案 C 重定 title | 否 | 低 |
| **P2-B** | `CATEGORY_KEYWORD_I18N` 6 语种（消除 100 个 URL 枚举） | ⚠️ **需母语复核 §3.2** | 低 |
| **P2-C** | `mseries-gs` title 压 ≤60；desc 尾句去模板 + 修断词 | 否 | 低 |
| **P3** | 补 10 个集合页 image sitemap；alt 重写 | 否 | 低 |
| **P4** | hub 改造（`product_overview.html` 加对比表/选型指引/Applications）；恢复 `/sports-lighting/` | ⚠️ 需批准 | 中 |

### 仍需业务确认的 3 项（不阻塞 P0-A/B/C）
1. `fl12m` 额定功率：960W 还是 1000W？
2. VSP 9M/12M 是否与 FL9M/FL12M 同光学模组（同排列）？若否则需补图。
3. `rt590fl-s`←`rt390fl`、`rt500hb`←`rt400hb`、`rt820sl-t`←`rt600sl-t`、`mseries-gs`←`fl9m-rgbw` 这 4 处借图是否成立（选项一致但平台尺寸不同）。

---

## 九、业务确认结论（2026-10-06，用户答复）与 P0 批次实施结果

### 9.1 三项业务确认（已落地）

| 确认项 | 答复 | 处理 |
|---|---|---|
| `fl12m` 额定功率 | **1000W** | `energy_data.System Wattage` 与 `ordering_info[1]` 的 `960W` 全部改为 `1000W`（`power`/`specs`/`model_number` 本就是 1000W）⇒ 五源一致 |
| VSP 9M/12M 与 FL9M/FL12M 光学关系 | **硬件相同，区别只是安装方案** | 借图**合法**，无需补图。已在守卫 docstring 记录该结论（`BeamAngleImageIntegrityTests`），并**删掉**我原先「禁止跨 slug 借图」的过严规则 |
| `rt590fl-s`←`rt390fl` / `rt500hb`←`rt400hb` / `rt820sl-t`←`rt600sl-t` / `mseries-gs`←`fl9m-rgbw` | **成立** | 同上，保留借图。守卫改为只锁「文件必须在盘」+「单角度图的角度必须在售卖选项内」 |

🔴 **我第一轮的规则写错了**：把「跨 slug 借图」一律判为错误。用户确认后改为按光学平台判定，
守卫规则相应放宽 —— 这也符合铁律精神：守卫的期望值必须是**产品决策**，不是我的猜测。

### 9.2 已实施（v1.10.19，未提交）

| 项 | 内容 | 验证 |
|---|---|---|
| **P0-A** | `views_products.py:333` `banner_label`：`category_t` → `category_display` | **144/144 页可见枚举归零**，6 语种标签实测：`Area and Site`/`Zone et Site`/`Área y Sitio`/`Bereich und Standort`/`Территория и площадка`/`المنطقة والموقع` |
| **P0-B** | `rt220ub.model_number`：`FL1M-80W` → `RT220UB-40W`；`models.py` 删 `default="FL1M-80W"`（迁移 `0032`）；help_text 改为警示文案 | 线上 title 从 `LED Flood Lights FL1M-80W` → `LED Flood Lights RT220UB-40W` |
| **P0-C** | `fl9m.power` `630W`→`720W`；`fl12m` 960W→1000W；**13 个空 `power` 从 `energy_data` 回填** | **title 含瓦数 120/144**（缺的 24 = 4 个无瓦特产品 × 6 语种，符合预期） |
| **P0-E** | `beamangle-120d-1.webp` 移到 `rt420fs-s/`；`rt420fs-s` 改指 own 路径；`rt220ub` 光束图置空 | 本地渲染：`rt420fs-s` 出图 `rt420fs-s/beamangle-120d-1.webp`；`rt220ub` 无图（模板 `{% if %}` 守卫生效） |

**新增** `pages/tests_product_data_integrity.py`（14 条）+ `pages/migrations/0032_alter_product_model_number.py`。
`seed_data.json` diff 收敛在 **19 行**（无副作用），CRLF 保持。
变体目录已同步重生成（`rt420fs-s` +3，旧 `rt220ub` 孤儿变体已删）。

### 9.3 守卫与探针

- **14 条守卫全绿**。
- **7 个变异探针全过**（MUTATED 红 → RESTORED 绿 → `git diff --stat` 字节零残留，不用 `git checkout`）：
  P1 还原 `banner_label` 枚举 / P2 还原 `default="FL1M-80W"` / P3 rt220ub 型号改回 FL1M-80W /
  P4 fl9m 瓦数改回 630W / P5 rt820sl-t power 清空 / P6 rt220ub 重新指向 120° 图 / P7 fl6m 图路径不存在。
- 🔴 **我第一版守卫自己写错 2 处**（`test_beam_angle_image_lives_in_the_products_own_directory`
  禁止合法借图、`test_beam_angle_degrees_match_the_ordering_table` 用 `beamangle-(\d+)` 把
  `12183050` 当成单个角度）。业务确认后已改：借图放行 + 只对 `beamangle-(\d+)d` 单角度命名做校验。

### 9.4 回归归因（关键：用 `git worktree` 在 HEAD 上独立复现）

`tests_product_seo_description_budget` + `tests_seo_keywords` 跑出 **28 failures**。
用 `git worktree add .workbuddy/tmp/head-check HEAD --detach` 在 HEAD 上跑同一批：

| 项 | HEAD | 当前工作区 |
|---|---|---|
| failures 数 | **28** | **28** |
| 失败项清单 | **逐条相同** | 同左 |
| `test_english_product_pages_are_unchanged` 断言值 | `164 not less than or equal to 160` | **逐字相同** |
| `test_all_product_titles_fit_serp_display` 断言值 | `61 … mseries-gs` | **逐字相同** |

⇒ **28 failures 全部是既存基线，本次改动零回归。**
其中 24 条是 `test_model_and_seed_paths_agree`（`Product(...)` 只传 4 个字段、不传 `power`，
而 `_DictProduct` 读 `power` ⇒ 公式必然分叉），属**守卫自身的历史缺陷**，
需单独修（把 `power`/`model_number` 传进 `Product(...)`）—— 已记入待办。
worktree 已 `git worktree remove` 清理。

核心回归：`tests_release_metadata` + `tests_product_data_integrity` + `tests_static_assets`
+ `tests_cert_images` + `tests_image_srcset` = **72 tests OK**（1 skipped = 本地无
`static_index_data.py`，既有）。

### 9.5 剩余待办

| 优先级 | 项 | 阻塞 |
|---|---|---|
| P1 | 24 页差异化描述（当前 11 词，6 个 FL\* 逐款按功率/场景差异化） | 需文案 |
| P1 | 4 个 `<span>` → `<h2>`；H1 加品类词+功率 | 否 |
| P1 | FAQ 按品类分 4 套（消除 24 页雷同） | 需文案 |
| P2 | `SLUG_KEYWORD_OVERRIDE` 落地（FL\* 6 款重定 title，方案 C） | 否 |
| P2 | `CATEGORY_KEYWORD_I18N` 6 语种（消除 100 个 title 枚举） | ⚠️ 母语复核 |
| P2 | `mseries-gs` title 压 ≤60（**既存失败**）；desc 尾句去模板 + 修断词（**既存失败** 164>160） | 否 |
| P2 | 修 `test_model_and_seed_paths_agree` 守卫缺陷（`Product(...)` 漏传 `power`/`model_number`）⇒ 可一次消掉 24 条既存失败 | 否 |
| P2 | 修 news title 80>60（**既存失败**，已知欠账） | 需文案 |
| P3 | 补 10 个集合页 image sitemap；alt 重写 | 否 |
| P4 | hub 改造（`product_overview.html` 加对比表/选型指引）；恢复 `/sports-lighting/` | ⚠️ 需批准 |
| — | `rt220ub` 100° 配光图待业务提供 | ⚠️ 需素材 |
| — | M 系列共用一张 cd 图：fl1m 80W 页显示 4500cd 量级不对 ⇒ alt 加 "optical distribution pattern" | 否 |

---

## 十、P1 批次实施结果（v1.10.20）

三项全部落地，144 页渲染实证通过。

### 10.1 P1-A：24 页差异化描述

| 指标 | 之前 | 之后 |
|---|---|---|
| 描述词数 | 1–34（`rt590fl-s` = 1 词 `RT590FL-S`；6 个 FL\* = 11 词同构） | **107–132，均值 121** |
| 唯一描述数 | 24 页里 6 个 FL\* 只差型号数字 | **24/24 全不同**（bigram Jaccard 最高 0.12，阈值 0.80） |

🔴 **文案取材纪律**：每个数字都来自该产品自己的 `energy_data` / `ordering_info`
（流明、EPA、尺寸、重量、光束角、调光方式、支架）。**零编造**，且**未添加任何
业务数据**（MOQ / 交期 / 保修）—— 仓库里没有这些数字。
段落用 `

`（模板走 `|nl2para`）。

### 10.2 P1-B：标题语义层级

| 指标 | 之前 | 之后 |
|---|---|---|
| H1 | 纯型号 `FL6M` | `FL6M 480W`（24 页中 20 页带功率，4 个无瓦特产品不带） |
| H2 数量 | **1**（只有 Product FAQ） | **5**（叶型号）/ 1–3（hub 与无瓦特页，符合模板设计） |
| 小节标签 | 4 个 `<span>` | 4 个 `<h2>` + CSS 重置（`margin:0; font-weight:normal`） |
| 模板内 `{{ product.category_t }}` | 2 处（兜底 hero） | **0** |

**为什么 H1 只加功率不加品类词**：品类词目前只有英文版（`CATEGORY_KEYWORD`），
非英语回落枚举串 —— 注入 H1 会把英文词放到 `/fr/` 页上。
留待 P2-B 的 `CATEGORY_KEYWORD_I18N` 落地后再加。

**H2 只在 `product_detail.html` 断言**：`product_overview.html` 的头部注释明说
「Deliberately has NO technical blocks」⇒ 守卫加了**反向断言**
（overview 模板**不得**出现这四个 class），否则两页会重复同一套 H2 小节、
互相竞争同一批词。

### 10.3 P1-C：FAQ 按品类分 4 套

| 指标 | 之前 | 之后 |
|---|---|---|
| 唯一 FAQ 组合 | **1**（24 页字节级相同） | **4**（sports 2 / flood+area 15 / highbay+roadway 4 / accessory 3） |
| sports 问题泄漏 | 24/24 页都有 | **仅 2 页**（`vsp-*`） |

结构：`_SHARED_FAQ`（3 条通用：效率/L70、IP66/10kV/温度、DIALux）
+ 按品类追加 3 条。ACCESSORY 用 `_SHARED_FAQ_BY_KEY[完整问句]` 精确摘 1 条
（配件不适用 DIALux 与 HID 节能问题，但买家会问宿主灯具的效率），
**用完整问句作 key 而非索引**，这样重排 `_SHARED_FAQ` 不会静默改变配件页内容。

### 10.4 守卫与探针

新增 `pages/tests_product_content_p1.py`（**20 条**）+ 12 个变异探针全过。

🔴 **探针抓出两个「我自己的假守卫」**（铁律 4/4b 的又一次实例）：

1. **改 `seed_data.json` 对守卫完全无感** —— 因为 `_load_seed()` 优先
   `from pages.seed_data import SEED_DATA`（铁律 2 已记载，但写守卫时没联想到）。
   ⇒ 新增 `test_build_artifact_matches_the_json`：产物与 JSON 必须逐字段一致。
   探针拆成 A1a（只改 JSON ⇒ sync 守卫必须红）与 A1b（两者都改 ⇒ 深度守卫必须红）。
2. **「词集合相同」判据太弱** —— 把 fl1m 描述原样复制给 fl4m 后守卫仍绿，
   因为 fl4m 原文里顺带提了 `FL1M`（"more output than the single-module FL1M"）
   ⇒ 词集差一个 token。**doorway 页是「近乎相同」不是「完全相同」**。
   ⇒ 改为 **word-bigram Jaccard ≥ 0.80 判同源**（实测真实 fl1m↔fl4m = 0.120）。
   阈值写成 `SIMILARITY_LIMIT` 常量，探针 A2 把它**升到 400** 验证可证伪
   （降阈值本就该绿，升阈值才是有效变异）。

🔴 探针脚本自身也踩了 3 个坑并修掉：P1-B2 锚点在模板里出现 **2 次**
（banner hero + 兜底 hero）必须全删；P1-A3 的 splice 切片跨过了整个 JSON 块
导致「变异」实际没生效；探针跑 `seed_sync --json` 会改 gitignore 的
`pages/seed_data.py`，`git diff --stat` **看不到** ⇒ 必须显式备份/恢复产物，
否则前一个探针的残留会污染后一个的 baseline（这个坑让我连续两轮误判）。

### 10.5 同步重写的既有守卫

`pages/tests_qa_bgroup.py`（14 条）的 FAQ 断言锁的是「旧共享文本」：
`PATHS` 只有 2 条、`EXPECTED_FACTS` 含 `flicker`、硬编码
`'VSP high-frequency'` 与 `'Are SolarOne stadium lights flicker-free for broadcast?'`。
分化后这些断言**必然失败**（fl6m 是 AREA_SITE，不再有 flicker 问题）⇒
按铁律「反转既有契约必须同步重写」：
- `PATHS` 扩到 **5 条（每品类一页）** + 新增 `PATH_CATEGORY` 映射
- `EXPECTED_FACTS` 拆成 `SHARED_FACTS` / `ACCESSORY_SHARED_FACTS` / `CATEGORY_FACTS`
- 新增**反向断言**：sports 专属问题**不得**出现在其余四页
- 可见性探针改为**从常量派生**（遍历该页应有的 6 条），不再硬编码某一句
- `</script` 扫描从单个 `PRODUCT_FAQ` 扩到 `PRODUCT_FAQ_BY_CATEGORY` 全 6 套

### 10.6 回归

核心 11 个模块 = **141 tests OK**（1 skipped = 本地无 `static_index_data.py`，既有）。
`manage.py check` 0 问题。`seed_data.json` CRLF 保持，diff 收敛在 43 行（24 条描述）。

---

## 十一、P2 批次实施结果（v1.10.21）

四项全部落地，144 页渲染实证：0 枚举、0 超长、0 重复。

### 11.1 P2-A：`SLUG_KEYWORD_OVERRIDE` 落地（机制 2026-09 建成，值首次填）

| slug | 之前 | 之后 | 理由 |
|---|---|---|---|
| `fl4m`–`fl16m`（5 款） | LED Area & Site Lighting | **Modular LED Flood Light** | 仓库自己的文案称其为 "FL M-series floodlight family"；`docs/keyword-inventory.csv` 实测 `led stadium lights` 1000/mo KD6 是本站性价比最好的词 |
| `fl9m-rgbw` | LED Area & Site Lighting | **Modular LED Flood Light RGBW** | 同上 + 颜色版本 |
| `rt410-series` | LED Area & Site Lighting | **LED Stadium Light** | 仓库描述是 "Olympic-grade, HDTV-ready sports lighting"，归在 AREA_SITE **本身就是分类错误** |
| `fl1m` | LED Area & Site Lighting | *保持不变* | 80W / 2.3kg / EPA 0.26 sq ft —— 是面积/场地改造尺寸，不是体育场 |

**效果**：11 页同首词 → **7 组，最大组 4 页**（改造前最大组 11 页）。

### 11.2 P2-B：非英语品类词回落链

| 指标 | 之前 | 之后 |
|---|---|---|
| 非英语 title 含枚举 | **100 / 120** | **0** |
| 144 页 title 唯一数 | 144（含枚举） | **144，无重复** |
| title 超 60 字符 | 1 | **0** |

**关键决策：复用站内既有译法，不新造词。**
`CATEGORY_KEYWORD_I18N` 的 6×5 = 30 条全部取自 `i18n.py:_SIDEBAR_I18N`
（侧栏与集合卡已在用的译法）⇒ title / 侧栏 / 卡片三处措辞统一，
且**上线不需要新的翻译审校**。母语复核后的 SEO 词组候选仍留在 §3.2 待用。

回落链写死在代码注释里：`显式译文 → 英文词 → 空串`，
🔴 **`product.category` 在任何一环都不参与**（那正是病根）。

### 11.3 P2-C：title 裁剪 + desc 尾句按品类

| 指标 | 之前 | 之后 |
|---|---|---|
| title 超 60 | 1（`mseries-gs` 61） | **0** |
| desc 断词 | 6 条以 `lighting pro...` 结尾 | **0**（改词边界裁剪） |
| desc 尾句 | 24 页同一句，且路灯页写 "professional sports" | **6 个品类 6 种尾句**，措辞全部取自仓库既有文案 |
| desc 超 160 | 0 | **0** |

title 裁剪**只让 identifier 让位**（复用项目页已有的 `_fit_project_title` 词边界策略）——
关键词与品牌是页面竞价的部分，完整名称仍在 H1 / og:title / breadcrumb JSON-LD 里。

### 11.4 P2-D：顺带修掉 24 条既存失败

`tests_product_seo_description_budget.py` 的 `Product(...)` 只传 4 个字段
（`slug`/`name`/`description`/`translations`），而公式读 6 个
（+`category`/`power`/`model_number`）⇒ **该守卫在报自己的缺口，不是报镜像漂移**。
补齐后 `test_model_and_seed_paths_agree` 24 条一次消掉。

同一文件另一处：desc 长度**在 HTML 反转义前测量** ⇒ 含 `&` 的描述被多算 4 字符
（实测 `raw 164 / unescaped 160`）⇒ 改为先 `html.unescape` 再量。

**既存失败 10 → 5**（用 `git worktree` 在 HEAD 上独立复现对比，见 §9.4 同法）。

### 11.5 守卫与探针

新增 `pages/tests_seo_p2.py`（**18 条**）+ **8 个变异探针全过**
（A1 清空 override / A2 override 退化成品类词 / B1 回落枚举 / B2 删 locale 词条 /
C1 去 title 裁剪 / C2 恢复硬切 / C3 恢复通用尾句 / C4 两品类共用尾句）。

🔴 **探针又抓出一个我自己写的假守卫**：P2-C 的新尾句让
**所有 24 条描述都短于 160 字符（最长 159）** ⇒ 裁剪分支**一次都不触发**
⇒ 「desc 不许断词」的守卫遍历真实数据时什么都没发现，
**把硬切改回去它照样绿**。⇒ 改为用一个**故意超预算的合成产品**驱动裁剪分支
（真实数据遍历保留为第二道较弱检查）。

探针脚本自身又踩两次：① 锚点里写死西里尔/阿拉伯字节导致 B2 锚点从未匹配
（探针静默退化成 no-op 假通过）⇒ 改为**按 key 名定位**；
② 清空 override 表时 `d[j+1:]` 留下 `}` 变成 `{}}` 语法错误，
让探针「看起来通过」。

### 11.6 同步重写的既有守卫

`tests_seo_keywords.py` 两条契约被 P2 反转，按铁律同步重写：
- `test_all_product_titles_contain_category_keyword` 断言「title 必含**该品类的**词」
  ⇒ **结构上就不允许 per-slug override 存在**。改为「必含 *override 或* 品类词」。
- `test_non_english_title_uses_localized_keyword` 断言关键词取自
  `translations[lang]['category']` ⇒ **正是 P2-B 要废除的回落链**。改为取自
  `CATEGORY_KEYWORD_I18N`，并新增 3 条：覆盖完整性、**禁止回落英文**、
  **与侧栏措辞锁死**（防日后有人换 SEO 词组时 unnoticed 地漂移）。

回归：`release_metadata + seo_p2 + seo_keywords + product_data_integrity +
product_content_p1 + qa_bgroup + project_seo_title + project_seo_description +
meta_description_budget + project_prose_scrub` = **140 tests OK**。

---

## 十二、P3 批次实施结果（v1.10.22）

三项全部落地。144 页渲染实证：**0 缺 alt / 0 枚举 / 0 无品类词 / 24 唯一组合 × 6 语种**；
sitemap **240 条 image 条目**，216 个唯一 URL **全部 curl 200，零死链**。

### 12.1 P3-A：36 条陈旧 alt 遮蔽了早已改好的公式（🔴 本批最隐蔽的缺陷）

`_gallery_alt` **早就被改过**（加入 qualifier），但站点上什么都没变 —— 因为
`enrich.py:180` 是 `img.alt_text or _gallery_alt(...)`：

```
db.sqlite3 → pages_productimage: 91 行，其中 36 行 alt_text 非空
  且 36 行全部形如 'FL6M — view 1'（_gallery_alt 的旧输出）
  ⇒ 存值优先 ⇒ 新公式在这 36 张图上从未执行过
```

这同时解释了审计发现的**双路径 alt 不一致**（铁律 1）：本地走 DB 拿到旧串，
生产走 seed 拿到新串。

**清理方式**：`re.match(r'^(.+?) — view (\d+)$')` **模式匹配后**才清，
🔴 绝不全量清空 —— 人工撰写的 alt 不可能被销毁（当前人工撰写 = 0 条，新闻图 5 条）。

| 产品 | 张数 |
|---|---|
`m-series` / `rt410-series` / `fl1m` / `fl4m` / `fl6m` / `fl9m` / `fl12m` / `fl16m` / `vsp-xxxxw-12m-yp` | 各 4 张 |

### 12.2 P3-C：alt 词组从「侧栏导航名」换成「title 在竞价的搜索词」

| 页面 | 之前 | 之后 |
|---|---|---|
`fl6m` gallery | `FL6M — Area and Site — view 1` | `FL6M — Modular LED Flood Light — view 1` |
`rt410-series` | `RT410 Series — Area and Site — view 1` | `RT410 Series — LED Stadium Light — view 1` |
`rt600sl-t` | `RT600SL-T — Roadway — view 1` | `RT600SL-T — LED Roadway & Street Lights — view 1` |
项目 `football-field-...` | `Bohemia Manor High School — United States — view 1` | `... — LED football Stadium Lights — United States — view 1` |
`/fr/` 的 fl6m | `FL6M — Zone et Site — view 1` | `FL6M — Zone et Site — view 1`（P2 的 i18n 表顺带白送） |

**6 处模板裸 alt 同步补词组**：hero 背景图 / 封面图 / 配光图 / 尺寸图 /
订购图 / 认证徽标。两个模板（`product_detail` + `product_overview`）都改 ——
只改一个会让 `overview` 页保留旧的裸 alt。

🔴 **认证徽标 alt 原来是 `{% trans 'Product Certifications' %}`**，
即**24 页字面完全相同**。改为 `{% blocktrans with name=... %}`：
`UL, DLC, GS, CE and IP66 certifications for FL6M`，
六语种实测全部正确落地（fr/de/es/ru/ar 句式本地化，UL/DLC/GS/CE/IP66 保留专名）。
旧 msgid 两个调用点都已迁移 ⇒ 未孤儿化（若只改 detail 模板，overview 仍用旧 msgid）。

### 12.3 P3-B：10 个集合页从 0 图到 240 条 image 条目

| 页面 | 之前 | 之后 |
|---|---|---|
`/` | 0 | **5**（3 张 hero + home-products + home-project） |
`/products/` | 0 | 1（products-bar-dark） |
`/projects/` | 0 | **10**（前 10 个项目封面，受 `_COLLECTION_IMAGE_CAP` 限） |
`/projects/football/` | 0 | 5 |
`/projects/tennis/` | 0 | 5 |
`/news/` | 0 | 2 |
`/about/` | 0 | 1 |
`/contact/` | 0 | 3 |
`/privacy/` `/terms/` | 0 | **0（设计如此）** |

**两条自律规则（都有守卫）**：
1. **只收该页真实渲染的图** —— hero 的 3 个 `-portrait.webp`（移动端
   `<source media>` 替代图）与浅色主题 `products-bar-light.webp`（CSS 交替态，
   不是第二张图）**均不收**。
2. **文件必须在盘** —— 用 `_first_static()`（项目唯一的存在性校验器，
   与页面服务同一份 manifest），不在盘就**丢弃该条**而不是给爬虫一个 404。

🔴 `_COLLECTION_PROJECT_SPORTS` 只声明「哪个集合页读哪个 sport 过滤器」，
**成员列表运行时从 `get_projects()` 取** —— 写死列表在项目加入 sport 组那一刻就开始腐烂。

### 12.4 🔴 探针第四次抓出我的假守卫（两次）

1. **DB 守卫读的是空测试库**：`ProductImage.objects.all()` 在 `TestCase` 里
   返回 0 行 ⇒ `test_no_stored_alt_matches_the_old_generated_shape` **恒绿**。
   手动往 `db.sqlite3` 写回陈旧 alt，测试**照样全绿**。
   ⇒ 改用 `sqlite3.connect('file:...?mode=ro')` 直读真实 DB（同
   `tests_cert_images.CertDatabasePathTests` 模式）+ **防空守卫**。
   ⚠️ 防空守卫的「被测对象」是**图片行**而非「非空 alt」—— 修复后正确状态
   就是「零非空 alt」，拿 alt 列做防空会在修复生效时反而失败。
2. **期望值从被验常量派生**（铁律 4b 第 N 次实例）：
   `test_project_collection_images_match_the_sport_filter` 遍历
   `_COLLECTION_PROJECT_SPORTS` 取期望值 —— 把 tennis 集合指向 football 的
   sport 类型时**实现与期望同时移动 ⇒ 恒绿**。
   那行 docstring 甚至写着「derived on purpose: the mapping is the product
   decision」—— **恰恰是铁律 4b 说的错误**。
   ⇒ 改为**字面量**期望表 + 新增**两集合图片不重叠**守卫（无需字面量也能抓映射错误）。

探针脚本自身又踩两个坑：
① **side-effect 型变异**：`probe()` 在 `mutate()` 之后又 `target.write(ret)`，
把 SQL 改动用原始字节覆盖掉 ⇒ A1 报「守卫没红」而守卫其实完全正确。
   ⇒ 加 `side_effect=True` 模式：跳过回写、改用文件级 `shutil.copyfile` 备份，
   残留检查用 **SHA-256**（`db.sqlite3` **不被 git 跟踪**，生产无状态，
   `git diff --stat` 看不见它的残留）。
② 锚点出现次数：`old.count == 1` 断言在实为 2 处时提前
   return 未写盘 ⇒ 报「探针没执行」。模板锚点出现多次必须**全替换**。

### 12.5 回归

16 个核心模块 = **231 tests OK**（1 skipped = 本地无 `static_index_data.py`，既有）。
`manage.py check` 0 问题。locale 6 个 `.po` 追加 + `.mo` 全部重编译。

### 12.6 剩余待办
| 优先级 | 项 | 阻塞 |
|---|---|---|
P1 | `rt220ub` 的 100° 配光图 | ⚠️ 需素材 |
P1 | `tests_seo_b4` 5 条文案欠账 / news title 80>60 | 需文案 |
P2 | 134 张图片文件名问题（80 纯序号 / 3 拼错）单独排期 | 否 |
P2 | M 系列 7 页共用一张 cd 图 ⇒ fl1m 80W 页 cd 量级不对，alt 加 "optical distribution pattern" | 否 |
P3 | hub 改造（`product_overview.html` 对比表/选型指引） | ⚠️ 需批准 |
P4 | 恢复 `/sports-lighting/` + 6 个品类独立 URL | ⚠️ 需批准 |

---

## 十三、P4 批次实施结果（v1.10.23）—— 方案从「6 个品类页」改为「1 个体育泛词页」

### 13.1 🔴 实证推翻了原方案：6 个品类里 4 个撑不起独立页

| 品类 | 产品数 | 项目数 | 判定 |
|---|---|---|---|
`SPORTS_LIGHTING` | 2 | **20** | ✅ 建页 |
`AREA_SITE` | 11 | 1 | `/products/` 已覆盖 |
`FLOODLIGHT` | 4 | 0 | ❌ thin page |
`HIGHBAY_LOWBAY` | **2** | 0 | ❌ thin page |
`ROADWAY` | **2** | 1 | ❌ thin page |
`ACCESSORY` | 3 | 0 | ❌ thin page |

为 2 个产品的品类建页 = **P1 刚消灭的那种 thin page 一次重建 4 个**。

而真正有量的是**同一个意图的四种拼法**：
`stadium lights` 2900 + `led stadium lights` 1000 + `stadium light` 720 +
`led sports lighting` 390 = **5010/mo**，v1.10.0 撤回后**无任何页面承载**。

⇒ **只建 1 个 `/stadium-lighting/`**，并把「拒绝」写进守卫：
`test_no_category_page_exists_beyond_the_one_that_earned_it` 扫 urlpatterns，
日后任何人加 `highbay_lighting` 都会红，必须重新论证。

### 13.2 新页构成

| 项 | 内容 |
|---|---|
URL | `/stadium-lighting/`（6 语种，无 `/en/` 前缀） |
数据源 | `related_links.PRODUCT_CATEGORY_TO_PROJECT_SPORTS['SPORTS_LIGHTING']` —— **与产品页「Application Cases」同一张表**，两边不可能对不上 |
产品 | 2 个 VSP 体育场泛光灯 |
场馆 | **9 个真实项目**（足球 3 / 足球场 2 / 棒球 1 / 多用途 2 / 速滑 1 / 游泳 1 / 高山滑雪 1 / 卡丁 1 中取 9） |
选型表 | 4 行 × 4 列（场地类型 / 典型灯具 / 光束分布 / 安装高度），**逐格 `{% blocktrans %}`** |
sitemap | priority 0.8，**11 条 image**（产品封面 + 场馆封面） |
内链 | `/products/`（无条件）+ `/projects/football/` `/projects/tennis/`（`{% if collection_key %}` 门控） |
实机实测 | 六语种 title 41–60 / desc 127–160 / 正文 342–588 词 / H2 ×4 / hreflang 7 |

**desc 从 209 压到 140**（初稿超预算 49 字符，SERP 里会被截断）。

**ru title 从 65 压到 41** —— 译文不是英文的机械转写，
英语版有 "Sports Floodlights" 是因为品牌已隐含，俄语需要另一种压缩；
页内 H2 仍带|stadium floodlights| 的俄语说法。

**选型表逐格翻译而非整行**：整行 `{% blocktrans %}` 会把 `<td>` 标记
塞进 msgid，译者无法使用 ⇒ 16 个可翻译字符串，不是 4 个。
型号/功率/光束角**六语种一律不译**（符合 AGENTS.md §4）。

### 13.3 🔴 顺带修掉 5 处模板注释泄漏（我自己 v1.10.20 / v1.10.22 引入）

Django 的 `{# #}` **只支持单行** —— 跨行写它根本不是注释，
模板引擎会把内容**原样输出为可见正文**（v1.5.2 已经踩过一次并修过，
`products.html` 里那次又回来了）。

| 文件 | 行 | 引入批次 | 后果 |
|---|---|---|---|
`product_overview.html` | 77 | v1.10.20（P1-B） | **每次访问 `/products/m-series/` 都显示这段说明文字** |
`product_overview.html` | 148 | v1.10.22（P3-C） | 认证徽标上方 |
`product_detail.html` | 69 / 153 | v1.10.22（P3-C） | hero 图与认证徽标上方 |
`products.html` | 68 | **v1.10.x 之前**（v1.5.2 修过一次） | `/products/` 顶部 |

全部转为 `{% comment %}`，并加守卫
`test_no_template_comment_reaches_the_output`（扫 4 个页面的**渲染输出**）。
hub 页各减 42 词（`m-series` 409→367、`rgb-rgbw` 396→354、`accessory` 414→394）。

### 13.4 P4-B 子型号选择器，**以及我前提性错误的更正**

🔴 **本项的出发点是错的**。我最初扫描得出「hub 页没链接任何子型号」，
但那次扫描 `re.sub(r'<(nav|footer|header)[^>]*>.*?</>','',b)` **把 `<nav>` 剥掉了**，
而系列筛选导航 `sidebar-nav-list` **就是 `<nav>`** ⇒ 侧栏链接被剥掉后才计数。
**侧栏一直都链接全部子型号。**

选择器仍然值得做，因为它带了侧栏没有的东西：

| | 侧栏 | 选择器 |
|---|---|---|
位置 | 折叠筛选控件内 | 正文区 |
型号名 | ✅ | ✅ |
**功率** | ❌ | ✅（`FL1M 80W` … `FL16M 1280W`） |
**该子页在竞价的关键词** | ❌ | ✅（`Modular LED Flood Light`） |

实机实测：`m-series` 6 行（FL12M 1000W / FL16M 1280W / FL1M 80W /
FL4M 320W / FL6M 480W / FL9M 720W），`rgb-rgbw` 2 行，`accessory` 2 行，
叶型号 `fl6m` 正确渲染 0 行。

🔴 **第一版守卫也是空转的**：断言 `assertIn(child_url, body)` ——
**侧栏已经满足**。变异探针把选择器整块删掉，测试照样全绿。
⇒ 改为匹配选择器**自身的 markup**（`class="series-child"`），
并加「叶型号必须渲染 0 行」的反向断言（否则守卫看不见选择器消失）。

### 13.5 守卫与探针

新增 `pages/tests_seo_p4.py`（**25 条**）+ **9 个变异探针全过**
（A1 路由注销 / A2 内链断 / A3 交接链接泄漏到总索引 / A4 场馆列表清空 /
A5 出现未论证的品类页 / A6 sitemap 丢失 / A7 sitemap 无图 /
B1 模板选择器移除 / B2 视图不供子型号）。

探针脚本自身踩了 3 个坑：
① `views_stadium.py` 是**新建文件（LF）**，而 `core.autocrlf=true` 只让
git 签出的文件在工作区是 CRLF ⇒ 锚点用 CRLF 永远不匹配；
② 变异 `VENUE_PROJECT_LIMIT = 0` 时误加了 4 空格缩进 ⇒ IndentationError，
守卫报的是语法错而非业务断言；
③ A3/A4 的期望串我连改两次都改错方向（两个 mutation 命中不同断言），
最后直接取实际输出定位。

### 13.6 回归

19 个核心模块 = **295 tests OK**（1 skipped 既有）。`manage.py check` 0 问题。
locale 6 个 `.po` 追加 44 条 + `.mo` 全量重编译。

### 13.7 剩余待办
| 优先级 | 项 | 阻塞 |
|---|---|---|
P1 | **`rt220ub` 的 100° 配光图** | ⚠️ 用户明日提供 |
P1 | `tests_seo_b4` 5 条文案欠账 / news title 80>60 | 需文案 |
P2 | 134 张图片文件名问题（80 纯序号 / 3 拼错）单独排期 | 否 |
P2 | M 系列 7 页共用一张 cd 图 ⇒ alt 加 "optical distribution pattern" | 否 |
P2 | GSC 索引 3 新页面 + 观察 `/stadium-lighting/` 收录与排名 | 上线后 |
