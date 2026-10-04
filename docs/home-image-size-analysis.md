# 首页图片尺寸分析（2026-10-04 实测）

结论先行：**首页每张图的分辨率对目标设备都是「刚好够 + 高分屏余量」，没有一张是纯粹过大的。**
真正的大浪费不在尺寸，而在「首屏把 3 张全屏轮播图全下载了」。

测量方式：线上抓首页 HTML → 逐张下载 → PIL 读像素与字节 → 对照 `base.css` / `home.html` 的真实显示宽度。

## 1. 逐张实测

| 图片 | 文件像素 | 体积 | 实际显示 | DPR2 需求 | 判定 |
|---|---|---|---|---|---|
| logo | 800×174 | 22.8 KB | 184×40（`base.html:97` `.nav-brand img{height:40px}`） | 368px | ✅ 对高分屏是余量，**保留** |
| hero-1（LCP，active） | 1920×1080 | 74.9 KB | 100vw×100svh（`base.css:705` inset:0 + cover） | 3840px | ✅ 分辨率合理 |
| hero-2 | 1920×1078 | **246.4 KB** | 同上 | 3840px | ✅ 分辨率合理，**但质量档偏重** |
| hero-3 | 1920×1078 | 220.6 KB | 同上 | 3840px | ✅ 同上 |
| home-products | 1200×640 | 74.2 KB | 608px（`.home-preview-card` 1fr of 1216px） | 1216px | ✅ 刚好卡住 DPR2 |
| home-project | 1200×640 | 143.8 KB | 608px | 1216px | ✅ 同上 |
| **首屏合计** | | **541.9 KB** | 只有 hero-1 是 `active` | | 🔴 |

hero 的两档 srcset 也量了：`1920w` 与 `1280w` 差 **39%–55%**（hero-1: 74.9 vs 45.6 KB）。
现有 `sizes="(min-width:1200px) 1920px, 1280px"` 意味着 **1440/1512 的笔记本也只能下 1920 档**（候选里没有中间档）。

## 2. 质量扫描（只动 quality，**不动分辨率**）

| 图 | 当前 | q88 | q80 | q72 | q64 |
|---|---|---|---|---|---|
| hero-2 | 246 KB | 273 | 227 | 193 | 176 |
| hero-3 | 221 KB | 244 | 192 | 153 | 138 |

当前质量约在 q88 附近 → **下调到 q80 可省 ~8%，q72 省 ~22%**，1920px 分辨率一点不动。

home-preview 两张按显示宽度重编码的模拟（DPR1，608px）：

| 图 | DPR1 所需 | 重编码 q80 | 省 |
|---|---|---|---|
| home-products | 608px | 23.9 KB | 74.2 → 23.9（−68%） |
| home-project | 608px | 43.4 KB | 143.8 → 43.4（−70%） |

**但这两张的 1200px 对 Retina 是刚需**（DPR2 需 1216px），所以正确做法不是缩小现有文件，而是**给高分屏外的设备多一档**（见建议 3）。

## 3. 发现与建议

### 🔴 建议 1（收益最大，且不降任何分辨率）：首屏只下载第 1 张 hero

**问题**：`home.html:43/50` 的 hero-2 / hero-3 虽然写了 `loading="lazy"`，但 `.hero-slide` 是
`position:absolute; inset:0` 的**全屏元素** —— 它们始终在视口内（只是 `opacity:0`），
所以 lazy 对它们**无效**，浏览器在首屏就把 3 张全下载了。

**实测后果**：首屏 541.9 KB，其中 **467 KB（86%）是用户眼前根本看不到的**（要等轮播切到第 2/3 帧）。
三张大图并发抢带宽，直接拖慢 LCP。

**改法**（与 `docs/三屏响应式优化方案.md:1494` 的「方案 A」一致，当时未实施）：

- hero-2 / hero-3 的 `<img>` **不写 src**，只写 `data-src`
- 轮播切到该帧时 `setAttribute('src', dataSrc)`
- 配 `.hero-slide:not(.active) { visibility: hidden; }` 防止未加载时留白
- 首图保留 `fetchpriority="high"` + 静态 `src`，保证无 JS 时首屏照常显示

**收益**：首屏 541.9 KB → **74.9 KB（−86%）**，LCP 图片独占带宽。
**代价**：改 `templates/home.html` + `templates/base.html` 的轮播 JS；首图仍是静态，无 JS 降级不受影响。

⚠️ 守卫影响：
- `pages/tests.py:430` 正则匹配 `class="hero-slide active"` 的 img 标签 → 首图仍保留，不受影响
- `scripts/e2e/run_checks.py:541` 检查 `img.hero-slide.active` → 同上
- 需要新守卫：确认 2/3 张**没有** `src` 属性（否则 lazy 白写了）

### 🟡 建议 2（可选，需你目视确认）：hero-2 / hero-3 降到 q80

分辨率 1920px 不变，只改质量参数：hero-2 246→227 KB、hero-3 221→192 KB，合计省 ~48 KB。
WebP 照片 q80 是常规可用档，但 hero 是视觉门面，**建议你自己先看一眼 q80 的观感再定**。
⚠️ 文件名带内容哈希（`hero-main-2.f07b3eace487.webp`），重编码 = 新文件名 → 要改模板 + 重新 collectstatic。

### 🟡 建议 3（稳妥、新增文件不改动现有）：两张 home-preview 加 1 档 srcset

`home-products.webp`（1200px）与 `home-project.webp`（1200px）**不动**，新增两个 608px 版本，
HTML 改成：

```html
<img src="1200w 版" srcset="608w 版 608w, 1200w 版 1200w"
     sizes="(max-width:767px) 100vw, 608px" loading="lazy">
```

**收益**：DPR1 设备省 ~68–70%（74→24 KB、144→43 KB），Retina 仍走 1200w 不受影响。
**代价**：多 2 个文件；`sizes` 要写准（当前 608px 来自 `1fr 1fr` 布局，767px 以下转单列 → 100vw）。

## 4. 明确不做（附理由）

| 项 | 理由 |
|---|---|
| 压 hero 的分辨率 | 你已明确否决「项目图不降分辨率」；且 1920px 对 100vw 全屏是刚需 |
| 压 home-preview 分辨率 | 1200px 刚好满足 DPR2，压了 Retina 直接糊 |
| 压 logo 到 400px | 800px 是品牌资产，被 JSON-LD Organization.logo（`base.html:622`）、OG、footer 共用；DPR2 也用得上。DPR1 下省的那几 KB 不值得动文件名（会牵动 config） |
| 给 hero 加 1600w 中间档 | 能省 ~15%，但要多 3 个文件 + 改模板 srcset，收益/维护比不划算；建议放 P2 |

## 5. 实施前必须知道的两件事

1. **图片文件名带内容哈希**，任何重编码都会产生新文件名；模板里是硬编码的
   （`templates/home.html:36/43/50/98/117`），不是从 seed 读的 → 改图 = 改文件 + 改模板 +
   重新 `collectstatic`，三处同步（项目铁律）。
2. **`pages/tests_static_assets.py`** 有一类守卫：模板里写死引用的静态文件必须真实存在并被哈希清单收录。
   新增 srcset 候选要确认同样能被 collectstatic 收录，否则线上回落未哈希 URL + 每请求 warning。
