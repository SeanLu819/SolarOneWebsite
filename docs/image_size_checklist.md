# 产品轮播图尺寸对照清单

> 生成时间：2026-10-07
> 判定依据：轮播渲染框恒定 **760 x 427.5 CSS px**
> （`templates/product_detail.html:689-693`，`max-width:760px` + `aspect-ratio:16/9`；媒体查询只改 `min-height`，不改宽度）
> 目标尺寸：**1520 x 855** = 760 x 2，@2x 屏 1:1 像素，1520/855 = 1.7778 = 16:9

**处理原则**

1. 缩放到宽 1520，**双向居中**贴入 1520x855 画布，四周留透明（或纯白底）。
2. **绝对不要直接拉伸** —— 960x800 硬拉成 1520x855 会把灯具压扁约 34%。
3. 比例已达标（16:9）的图，只需放大重采样；比例不达标的需补边。

---

## 汇总

| 类别 | 张数 | 需处理 |
|---|---|---|
| 轮播主图 (gallery) | 81 | **34** |
| 详情主图 (image 兜底) | 1 | 1 |
| 非轮播配图 (banner/3D/配光/证书) | 72 | 0 |

> 路径说明：seed 数据里部分图用 `products/gallery/x.webp`，部分用 `products/<slug>/x.webp`，
> 两种约定并存但磁盘实际统一在 `static/images/products/<slug>/`。改图时**按下面的文件名在磁盘上找**即可。

---

## 一、必改：轮播主图尺寸不符（34 张）

### 现状 960 x 800 —— 19 张

涉及产品：`fl12m`、`fl16m`、`fl4m`、`fl6m`、`fl9m`

> ⚠️ **比例不是 16:9**（当前 1.2000，目标 1.7778）。放入 16:9 框会上下留白，需缩放后居中补边。

| 磁盘文件 | 现状 | 目标 |
|---|---|---|
| `fl12m/fl12m-01.webp` | 960x800 (70KB) | 1520x855 |
| `fl12m/fl12m-02.webp` | 960x800 (52KB) | 1520x855 |
| `fl12m/fl12m-03.webp` | 960x800 (27KB) | 1520x855 |
| `fl12m/fl12m-04.webp` | 960x800 (51KB) | 1520x855 |
| `fl16m/fl16m-01.webp` | 960x800 (87KB) | 1520x855 |
| `fl16m/fl16m-02.webp` | 960x800 (31KB) | 1520x855 |
| `fl16m/fl16m-03.webp` | 960x800 (18KB) | 1520x855 |
| `fl16m/fl16m-04.webp` | 960x800 (61KB) | 1520x855 |
| `fl4m/fl4m-01.webp` | 960x800 (52KB) | 1520x855 |
| `fl4m/fl4m-02.webp` | 960x800 (41KB) | 1520x855 |
| `fl4m/fl4m-03.webp` | 960x800 (28KB) | 1520x855 |
| `fl4m/fl4m-04.webp` | 960x800 (28KB) | 1520x855 |
| `fl6m/fl6m-01.webp` | 960x800 (48KB) | 1520x855 |
| `fl6m/fl6m-02.webp` | 960x800 (42KB) | 1520x855 |
| `fl6m/fl6m-03.webp` | 960x800 (31KB) | 1520x855 |
| `fl6m/fl6m-04.webp` | 960x800 (36KB) | 1520x855 |
| `fl9m/fl9m-02.webp` | 960x800 (43KB) | 1520x855 |
| `fl9m/fl9m-03.webp` | 960x800 (41KB) | 1520x855 |
| `fl9m/fl9m-04.webp` | 960x800 (55KB) | 1520x855 |

### 现状 1280 x 720 —— 13 张

涉及产品：`accessory`、`glare-shield-for-rt410`、`mseries-gs`、`rt420fs-s`、`rt590fl-s`、`rt600sl-t`

> 比例已是 16:9，只是宽度不足 1520 —— **最简单的一批，只需放大重采样**，不涉及裁切或补边。

| 磁盘文件 | 现状 | 目标 |
|---|---|---|
| `accessory/mseries-glare-shield-720p-02.webp` | 1280x720 (35KB) | 1520x855 |
| `accessory/rt410-glare-shield-01.webp` | 1280x720 (41KB) | 1520x855 |
| `glare-shield-for-rt410/rt410-glare-shield-02.webp` | 1280x720 (22KB) | 1520x855 |
| `glare-shield-for-rt410/rt410-glare-shield-03.webp` | 1280x720 (24KB) | 1520x855 |
| `glare-shield-for-rt410/rt410-glare-shield-04.webp` | 1280x720 (28KB) | 1520x855 |
| `mseries-gs/mseries-glare-shield-720p-01.webp` | 1280x720 (54KB) | 1520x855 |
| `mseries-gs/mseries-glare-shield-720p-03.webp` | 1280x720 (27KB) | 1520x855 |
| `rt420fs-s/rt420fl-01.webp` | 1280x720 (64KB) | 1520x855 |
| `rt420fs-s/rt420fl-02.webp` | 1280x720 (74KB) | 1520x855 |
| `rt420fs-s/rt420fl-03.webp` | 1280x720 (78KB) | 1520x855 |
| `rt420fs-s/rt420fl-05.webp` | 1280x720 (74KB) | 1520x855 |
| `rt590fl-s/rt590fl-s-01.webp` | 1280x720 (147KB) | 1520x855 |
| `rt600sl-t/RT600SL-T.webp` | 1280x720 (233KB) | 1520x855 |

### 现状 720 x 600 —— 1 张

涉及产品：`fl9m`

> ⚠️ **比例不是 16:9**（当前 1.2000，目标 1.7778）。放入 16:9 框会上下留白，需缩放后居中补边。

| 磁盘文件 | 现状 | 目标 |
|---|---|---|
| `fl9m/fl9m-01.webp` | 720x600 (41KB) | 1520x855 |

### 现状 1520 x 854 —— 1 张

涉及产品：`rt410-rgbw`

> 比例已是 16:9，只是宽度不足 1520 —— **最简单的一批，只需放大重采样**，不涉及裁切或补边。

| 磁盘文件 | 现状 | 目标 |
|---|---|---|
| `rt410-rgbw/rgbw-rt410-red.webp` | 1520x854 (170KB) | 1520x855 |

---

## 二、可选：详情主图兜底（1 张）

`image` 字段的兜底主图，**仅当该产品没有 gallery 时才显示**。比例偏宽，塞进 16:9 框会左右留白。影响小，可不改。

| 磁盘文件 | 现状 | 比例 |
|---|---|---|
| `rt410-series/floodlight.webp` | 956x517 (40KB) | 1.8491 |

---

## 三、不用改：非轮播配图（72 张）

走 `object-fit: contain` 居中显示（banner 条图、3D 视图、配光图、证书图等），尺寸不影响布局。

| 尺寸 | 张数 | 用途示例 |
|---|---|---|
| 1920x442 | 23 | `accessory/accessory-banner-02.webp` |
| 1920x540 | 15 | `fl12m/fl12m-3d-view.webp` |
| 1520x855 | 11 | `fl1m/fl1m80w-floodlight-855p-01.webp` |
| 960x800 | 4 | `fl1m/fl1m-01.webp` |
| 1920x400 | 4 | `rt400hb/rt400hb-beamangle-254590.webp` |
| 1921x442 | 3 | `fl12m/fl12m-bar-1.webp` |
| 640x128 | 2 | `m-series/certifications-ul-dlc-gs-ce-ip66.webp` |
| 2000x400 | 1 | `fl12m/beamangle-12183050.webp` |
| 1920x600 | 1 | `fl16m/fl16m-3d-view.webp` |
| 1920x650 | 1 | `fl16m/fl16m-ngs-3d-view-650p.webp` |
| 2048x576 | 1 | `fl4m/fl4m-3d-view.webp` |
| 1280x720 | 1 | `m-series/m-series-floodlight-02.webp` |
| 1200x616 | 1 | `m-series/rt200-m.webp` |
| 1920x517 | 1 | `m-series/sample-number.webp` |
| 1920x384 | 1 | `rt390fl/beamangle-3050120.webp` |
| 2213x540 | 1 | `rt500hb/rt500hb-3d-view.webp` |
| 1920x612 | 1 | `rt820sl-t/rt820-3d-view.webp` |

---

## 四、已合格（47 张，无需处理）

已是 1520x855 或 1520x856。`856` 与 `855` 差 1 像素、比例差 0.1%，`object-fit:contain` 下肉眼无差异，**不用改**。

涉及产品（13 个）：`fl9m-rgbw`、`rgb-rgbw`、`rt220ub`、`rt390fl`、`rt400hb`、`rt410-rgbw`、`rt410-series`、`rt500hb`、`rt590fl-s`、`rt600sl-t`、`rt820sl-t`、`vsp-xxxxw-12m-yp`、`vsp-xxxxw-9m-yp`
