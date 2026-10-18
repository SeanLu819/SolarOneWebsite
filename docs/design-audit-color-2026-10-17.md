# 设计语言与配色审计报告（SolarOne 外贸站）

- 日期：2026-10-17
- 状态：**方案探讨，全部未落地**（未改任何代码、未换任何图片）
- 目标：全站配色统一，奠定「高级感」基础；为后续 方案C（单一蓝 + 浮光棕 + 碳灰）落地留档
- 范围：CSS 令牌（`static/css/base.css`）、模板引用的 banner/hero、产品封面（23）、项目封面（22）、news 封面（7）

---

## 1. 现状诊断：全站实际在用的「4 个蓝」

| 位置 | 实际色值 | 来源（文件:行） | 色相 | 说明 |
|---|---|---|---|---|
| Logo 位图 | `#0068A8` (0,104,168) | `static/images/logo.webp`（实测像素） | 203° 偏灰 | 品牌资产，最暗最灰的一档 |
| 侧栏标题/激活项、竖条 | `#006AC7` (0,106,199) | 全走 `var(--accent)`：`base.css:1826 / 1858 / 1935 / 2004` | 208° | 浅色主题派生色 |
| 首页 View Products 按钮 | `#006AC7` | `base.css:937` `background: var(--accent)` | 208° | 与侧栏同源 |
| 首页大数字 500+/50% | 渐变 `#006AC7→#4CACFF→#00B2FF` | `base.css:1001-1002`（`.unit` 另在 `:1014`） | 208°→190° 偏青 | 混了 `#00D4FF` 青色，视觉上更亮更青 |
| 深色主题（**默认**）accent | `#0088FF` (0,136,255) | `base.css:15` + `base.html:5`（默认 `data-theme="dark"`） | 208° | 站点默认走这档 |

**关键结论**
- 「比 #0088FF 暗」是因为：站点默认深色主题才用 #0088FF；截图是**浅色主题**，其 `--accent` 被派生为 `color-mix(#0088FF, #000 22%)` = **#006AC7**（`base.css:113`，白底可读性派生，**刻意且正确**，不要改回）。
- 实测对比度：#0088FF 白底 ≈ **3.5:1（AA 正文 FAIL）**；#006AC7 白底 ≈ **5.4:1（PASS）**。
- 真正造成「不统一」的是两点：① 首页数字渐变混入青色端点（190°，偏青）；② Logo 位图第三档（203°，偏灰）。

---

## 2. 大图色貌审计（像素级色温分析）

方法：逐张缩放采样，过滤近黑/近白后取饱和像素的环形平均色相，按暖(15–70°)/绿(80–160°)/青绿(160–200°)/蓝(200–260°)/紫(>260°) 归类。

### 2.1 产品封面（23）
- **白底棚拍（≈16 张，白 58–83%，中性）**：`rt410-sports-light`、`fl1m~fl16m` 全系、`rt390`、`rt590`、`rt600sl`、`rt820sl` 等 → **干净中性，完美契合任何配色，保留**。本体带微弱暖橙/琥珀反光（43–57°），与浮光棕天然协调。
- **深底产品（黑 70–80%）**：`rt400hb`、`rt220ub`、`hb500-04`、`rgbw-9m-w` → 在碳灰卡片里自然融合（见 §4 决策）。
- **⚠️ 明显违和**：`rgbw-rt410-red.webp`（色相 5°，红色封面）→ 与蓝+棕方向冲突，列入替换清单。
- RGBW 系列（`rgbw-mseries`、`rgbw-9m-w`、`rgbw-rt410-*`）本质多彩光演示，暖橙/琥珀调与浮光棕协调，保留；仅红色那张替换。

### 2.2 项目封面（22，实景照）
- **绿色调主导（8 张，78–94°）**：`bmhs-football`、`shys-soccer`、`ccsc-baseball`、`msu-tennis`、`nanshan-ski`、`phs-football`、`garrison-forest-lacrosse`、`pap-pickleball` → 草坪绿是摄影现实，**不改内容**，仅用于非首屏卡片。
- **冷蓝调（7 张，197–254°）**：`choecm-basketball`、`Narbonne-basketball`、`27factory`、`bycicle-chunan`、`whzyxy`、`ydyyg`、`bnoc` → 与品牌蓝同源，**最契合，优先用于醒目位**。
- **暖橙调（6 张，22–33°）**：`bcia-airport`、`bitc-tennis`、`llq-roadway`、`red1-karting`、`mc-football`、`ncc-tennis` → 暖光实景，**与浮光棕 #B89076 呼应，方案C 加分项**。

### 2.3 模板 hero / banner
- `hero-main-2` 青绿(184°)、`hero-main-3` 琥珀(67°)、`hero-main-1` 暖橙(43°) → hero 带明显色偏，与「单一蓝」方向不符，列入替换/重拍。
- `about-main` 青绿略偏 → 去青。
- `home-project` 蓝(205°)、`home-products` 中性白、landing 页继承 home hero → 保留/对齐。
- `products-bar-dark/light` 微弱琥珀调 → 与新暖棕天然协调，保留。

### 2.4 news 封面（7）
- `asiaworld-expo-2026` 白底中性、`tianjin-binhai` 青绿 → 基本契合，青绿那张若用于 og 图可去青。

---

## 3. 已确认的设计决策（本次拍板）

1. **绿茵场项目封面**：接受「内容不改动、只统一外框」。绿草坪不重拍、不改色；统一的是卡片/边框/标签/分隔线的镀铬。
2. **深底产品图**：随碳灰卡片「顺其自然」。不补拍浅底版；落地碳灰 surface 后深底产品图自然融合，浅色主题下不再黑块突兀。
3. **浮光棕 #B89076** 作为暖点缀方向确认合理（冷蓝主色 + 暖棕点缀 = 静奢冷暖对比，且语义契合照明品牌）。
4. **深色背景转碳灰**：方向确认（#080D1F → 暖炭灰，建议略压深到 #1F1E1C 以保层次），落地时须连同中性色一起暖化。

---

## 4. 方案C 目标配色（提案，未执行）

| 角色 | 色值 | 说明 |
|---|---|---|
| 主蓝（唯一真源） | `#1068C9` (16,104,201) | 建议作为 `--accent-brand` 默认；admin `SiteConfig.accent_color` 仍可覆盖（当前默认 #0088FF） |
| 浅色主题 accent | `color-mix(#1068C9, #000 18%)` ≈ `#0E56A8` | 白底对比达标，与深主题只差明度不差色相 |
| hover / 渐变尾 | `#4A93D9` | 主蓝 +15~20% 白 |
| soft（选中底色） | `#D8E6F5` | 浅底选中/高亮 |
| 暖棕·主 | `#B89076` (184,144,118) | 点缀、标签分隔线、暖光 motif |
| 暖棕·深（浅底文字） | `#9A7256` | |
| 暖棕·浅（暗底辉光） | `#D8B89E` | |
| 深色 surface | `#1F1E1C` → `#1F1E1C`（暖炭灰） | 取代 #080D1F，并暖化 `--ink-soft/--ink-mute/--line` |
| Logo | `#0068A8`（暂保留） | 后续评估换单色 SVG 以完全对齐（可选，非必须） |

**统一原则**：照片是「内容」不是「配色」；镀铬（边框/标签/分隔线/按钮）= 单一蓝派生；暖棕只做点缀，正好接住暖光实景照与产品本体暖反射。

---

## 5. 待替换 / 重拍文件清单

> P0 = 与品牌色直接冲突，优先处理；P1 = 首屏 hero/banner 色偏，建议去色；保留 = 不改。

| 优先级 | 文件（真实路径） | 当前问题 | 建议替代方向 |
|---|---|---|---|
| **P0** | `static/images/products/rt410-rgbw/rgbw-rt410-red.webp` | 红色封面（色相 5°），与蓝+棕冲突 | 换中性白光/产品本体封面；红色仅留 RGBW 详情页 gallery 作「色彩选项」 |
| **P1** | `static/images/hero-main-1.webp`（含 `-portrait`/`-1280` 变体） | hero 暖橙色偏(43°) | 重拍/去色到中性冷暗或蓝调场景 |
| **P1** | `static/images/hero-main-2.webp`（含变体） | hero 青绿色偏(184°) | 同上，转中性冷暗/蓝调 |
| **P1** | `static/images/hero-main-3.webp`（含变体） | hero 琥珀色偏(67°) | 同上 |
| **P1** | `static/images/about-main.webp` | 青绿略偏 | 去青，转中性或蓝调 |
| P2 | `static/images/home-project.webp` | 蓝(205°) 已契合 | 保留，仅核对与其它蓝同源 |
| — | `static/images/products-bar-dark.webp` / `-light.webp` | 微弱琥珀，与暖棕协调 | **保留** |
| 避免用于首屏 | 8 张绿茵场项目封面（§2.2 绿群组） | 草坪绿与蓝+棕冲突 | **内容不改**；首页/分类 banner 位改用冷蓝/暖橙 13 张 |

> 绿茵场 8 张清单：`bmhs-football-02`、`shys-soccer-02`、`ccsc-baseball-720p-01`、`msu-tennis-court-720p-01`、`nanshan-ski-resort-720p-01`、`phs-football-02`、`garrison-forest-Lacrosse-1080p`、`pap-pickleball-courts-1080p-01`（路径前缀 `static/images/projects/<slug>/`）。
> 优先用于首屏的冷蓝/暖橙 13 张：`choecm-basketball-02`、`Narbonne-basketball-04`、`27factory-skating-arena`、`bycicle-chunan01`、`whzyxy-fencing-04`、`ydyyg-swimming-pool`、`bnoc-tennis`、`bcia-airport-01`、`bitc-tennis-court`、`llq-roadway-1080p-01`、`red1-karting-1080p-01`、`mc-football-04`、`ncc-tennis-03`。

---

## 6. 建议保留不改的文件（汇总）

- 全部白底棚拍产品封面（≈16 张）
- 深底产品图 `rt400hb` / `rt220ub` / `hb500-04` / `rgbw-9m-w`（碳灰卡顺其自然）
- 暖橙调项目封面 6 张（呼应浮光棕）
- 冷蓝调项目封面 7 张（呼应品牌蓝）
- `products-bar-dark/light`、`home-products`、`home-project`、landing 页 hero

---

## 7. 后续落地步骤（提案，未执行 —— 待拍板后另开任务）

1. **主蓝统一**：`--accent-brand` 默认改 `#1068C9`；浅色主题 `--accent` 改 `color-mix(var(--accent-brand), #000 18%)`；保留 admin 注入链路（不破坏「单一色源」铁律）。
2. **收敛渐变**：`.hero-stat-num` / `.unit` 去掉 `#00D4FF` 端点，改同相微渐变（accent → accent+20~30% 白）。
3. **碳灰背景**：`--bg` #080D1F → #1F1E1C，并暖化 `--ink-soft/--ink-mute/--line/--bg-raised`。
4. **暖棕 token**：新增 `--accent-warm` / `-deep` / `-soft` 三档，用于标签分隔线、次级 CTA、hover、图片 scrim。
5. **图片替换**：按 §5 清单替换 P0/P1（需用户提供新图或重拍）。
6. **守卫**：加/修 CSS 断言（禁止写死蓝字面量、禁止渐变出现青色端点、深色 surface 为暖炭灰），保持变异探针非空转。

---

## 8. 风险提醒

- 浅色主题 #006AC7 的「暗」是**优点**（白底 AA），落地时不要为了「统一」把它改回 #0088FF。
- 浮光棕在 #1F1E1C 上正文对比约 4.8:1，仅过 AA 普通文本线 → **只用于大字号/点缀/非正文**，不要排正文。
- 改 `--accent-brand` 默认会经 `color-mix` 自动派生 hover/deep/soft；若新增暖棕 token，须在 `:root` 与 `[data-theme="light"]` 两处同补并配守卫。
- 绿茵场/深底图**不改内容**，统一靠镀铬；若未来要批量加蓝调 scrim，单独提案，不在此文档执行范围内。
