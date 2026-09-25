# 图片文件名 SEO 规范（产品图 / 项目图 / 站点图）

SolarOne 官网 · 摄影/图片资产命名与落地指引
适用范围：`static/images/**`（含 `products/`、`projects/`、`products_page/`、根级站点图）

---

## 0. 先校准预期：文件名的权重到底有多高

在动手改 185 个文件之前，必须先明确三件事，否则会做大量无用功。

| 信号 | 权重 | 本站现状 |
|---|---|---|
| `alt` 文本 | **高**（图片搜索 + 无障碍） | 由 `product.name_t` / `project.title_t` 推导，**与文件名无关** |
| 图片所在页面正文的上下文 | **高** | 已达标（产品/项目详情页图文相关） |
| 结构化数据 | 中高 | 产品页已有 `Product` JSON-LD |
| 图片 sitemap（`<image:image>`） | 中高 | **完全没有** |
| **文件名 / URL 文本** | **弱** | 纯型号 + 序号，信息量低 |
| 文件扩展名、目录名 | 弱 | 已达规范（全 `.webp`、小写目录） |

**结论：文件名是弱信号。** 它几乎不影响普通网页搜索排名，主要在 **Google 图片搜索**里作为辅助文本。因此：

> 不要为「SEO」把 185 张图全部改名。优先做 alt 与图片 sitemap，文件名的收益只在少数「门面图」上值得投入。

---

## 1. 决定性事实：文件名在"上传那一刻"就被固化

这不是一个可以事后随意改的字段。实际链路：

```
admin 上传 → media/products/gallery/<name>_<django-hash>.webp
           ↓  post_save 信号 sync_product_on_save()
             pages/models.py:747-794
           ↓  只去掉 Django 的 hash 后缀，文件名其余部分原样保留
           ↓
static/images/products/<slug>/<name>.webp   ← 文件名 = 你上传时的原始文件名
```

推论：

1. **想控制文件名，必须在「上传之前」把本地文件改好名。** 上传后再改，要手工同步 media、static、DB、seed 四处。
2. 生产环境（`IS_VERCEL`）零 DB 访问，图片路径**硬编码**在 `pages/seed_data.py` → 构建时生成 `seed_data.json`。**改文件名不同步改 `seed_data.py` 就会线上 404。**
3. 目录结构 `static/images/products/<slug>/` 与 `static/images/projects/<slug>/` 已经很好，**不要动目录名**（目录名来自 slug，与 URL 路由绑定）。

---

## 2. 绝对不可改名的文件（代码硬编码）

以下文件名被代码直接引用，改名会断链，且需要同时改 3 处代码：

| 文件 | 引用位置 |
|---|---|
| `old-hid-lighting.webp` | `pages/models.py:572`（`_COMPARE_IMAGE_SLUGS`）<br>`pages/admin/project.py:113`（`_preserved`）<br>`templates/project_detail.html:129` |
| `new-led-lighting.webp` | 同上三处（`templates/project_detail.html:133`） |

位于 `static/images/projects/football-field-led-retrofit/`。**建议保持不变。**

---

## 3. 命名规范

### 3.1 公式

```
solarone-<产品型号或场馆>-<品类词或运动>-<视角/场景>-<两位序号>.webp
```

示例：

```
solarone-fl1m-led-flood-light-front-01.webp
solarone-bcia-airport-apron-led-lighting-night.webp
solarone-chunan-velodrome-track-lighting-02.webp
```

### 3.2 硬性规则

| 规则 | 说明 |
|---|---|
| 全小写 | `VSP9M-01.webp` → `vsp9m-01.webp` |
| 只用连字符 `-` | **不用下划线**。Google 把 `_` 当连接符不切词，`glare_shield_of_rt410` 会被当成 1 个词 |
| 不用空格、不用中文 | 空格变 `%20`；非 ASCII 在部分 CDN/日志里乱码 |
| 仅 `a-z 0-9 -` | 纯 ASCII |
| 词数 3–6，总长 ≤ 60 字符 | URL 越短越好；序号统一两位补零 `-01` |
| 品类词优先于型号 | `led-flood-light` 比 `fl1m` 有搜索价值 |
| 品牌词只出现一次 | `solarone-...` 开头，不要重复两次 |
| 扩展名小写统一 `.webp` | 已有 2 个 `.png` 需统一 |
| 禁止：分辨率、`img`、`dsc`、无意义序号 | `1080p`/`720p` 不是有效关键词，纯占词位 |

### 3.3 词表（请统一使用，避免同义词漂移）

**品类词**

`led-flood-light` · `led-high-bay` · `led-street-light` · `led-sports-lighting` · `led-stadium-light` · `led-area-light` · `led-linear-light` · `led-wall-washer` · `led-track-light`

**视角 / 场景词**

| 词 | 用途 |
|---|---|
| `front` | 产品正面主图 |
| `angle` | 45° 斜视 |
| `detail` | 局部特写 |
| `close-up` | 微距（芯片、透镜、反射器）|
| `3d-view` | 3D 渲染/尺寸图 |
| `dimension` | 三视图尺寸 |
| `beam-angle` | 配光曲线/光束角 |
| `installed` | 现场安装实景 |
| `night` | 夜间照明效果 |
| `before` / `after` | 改造前后对比（**仅新图使用，存量对比图不可改名**）|
| `banner` | 横幅/宽幅装饰图 |

**序号**：`-01` `-02` …（同组图必须补零，避免 `-1` 与 `-10` 排序错乱）

---

## 4. 现状诊断（基于真实文件扫描）

### 4.1 已达标

- 目录名规范：`products/<slug>/`、`projects/<slug>/`，slug 与 URL 路由一致。
- 扩展名统一 `.webp`（185 个 webp + 2 个 png，png 待统一）。
- 产品目录大量使用小写连字符：`fl12m/fl12m-01.webp`、`rt590fl-s/rt590fl-s-02.webp`。
- 项目目录使用**场馆缩写 + 运动类型**：`bcia-airport-01.webp`、`bitc-tennis-01.webp`、`whzyxy-fencing-01.webp` —— 方向正确。

### 4.2 问题清单

| 严重度 | 问题 | 实例 | 影响 |
|---|---|---|---|
| 高 | **拼写错误** | `bycicle-chunan01.webp` … `05`（应为 `bicycle`）| 错误关键词 + 观感 |
| 高 | 大写字母（20 个文件）| `VSP9M-01.webp`、`Baseball.webp`、`CCSC-Baseball-01.webp`、`RT600SL-T.webp`、`RT600SL-dimension-1.webp` | 大小写混用；Linux/CDN 路径**大小写敏感**，易 404 |
| 中 | 下划线 | `Glare_shield_of_RT410.webp` | 不切词，整串变 1 个词 |
| 中 | 分辨率噪声 | `ccsc-baseball-1080p-02.webp`、`llq-roadway-1080p-01.webp` | 无效关键词占位 |
| 中 | 纯型号 + 序号、零描述 | `fl12m-01.webp`、`hb500-02.webp`、`rt820-01.webp`（占绝大多数）| 图片搜索无可用文本 |
| 低 | 无意义名 | `sample-number.webp`、`m-series-05.webp` | 零信息 |
| 低 | 品牌词全站缺失 | 所有文件 | 丢掉品牌词 |

### 4.3 前后对比（按图片类型）

| 类型 | 现在 | 建议 |
|---|---|---|
| 产品主图 | `fl1m/fl1m-01.webp` | `solarone-fl1m-led-flood-light-front-01.webp` |
| 产品 3D/尺寸 | `fl1m/fl1m-3d-view.webp` | `solarone-fl1m-led-flood-light-dimensions-3d.webp` |
| 产品光束角 | `fl1m/beamangle-12183050.webp` | `solarone-fl1m-beam-angle-12-18-30-50-degrees.webp` |
| 产品横幅 | `m-series/m-series-bar-1.webp` | `solarone-m-series-led-high-bay-banner.webp` |
| 产品画廊 | `m-series/m-series-01.webp` | `solarone-m-series-led-high-bay-installed-night-01.webp` |
| 项目封面 | `bcia-airport-01.webp` | `solarone-beijing-capital-airport-apron-led-lighting.webp` |
| 项目画廊 | `ccsc-baseball-1080p-02.webp` | `solarone-ccsc-baseball-stadium-led-floodlight-night-02.webp` |
| 场馆-骑行 | `bycicle-chunan01.webp` | `solarone-chunan-velodrome-track-lighting-01.webp` |
| 分类页图 | `products_page/VSP9M-01.webp` | `solarone-led-street-lighting-series.webp` |
| 首页 hero | `hero-main-1.webp` | `solarone-led-stadium-lighting-night-01.webp` |
| 页脚/装饰 | `home-products.webp` | `solarone-led-luminaire-product-lineup.webp` |
| 对比图 | `old-hid-lighting.webp` | **不改名**（代码硬编码） |

---

## 5. 落地成本与分层执行

改名不是纯文件操作，每改一个文件名需同步：

1. `media/products/...` 或 `media/projects/...` 下的源文件
2. `static/images/...` 下的产物文件
3. `pages/seed_data.py` 中的路径字符串（生产环境唯一真源）
4. 重建 `seed_data.json`
5. DB 中 `ImageField` 记录（本地/admin 模式）

**成本约 5 分钟/张。** 因此分三层执行：

### Tier A — 零改名，收益最高（建议先做）

- **补齐图片 sitemap**：`pages/views/views_other.py` 的 sitemap 目前**没有** `<image:image>` 扩展。这是 Google 图片索引的正式通道，收益远大于文件名。需加 `xmlns:image` 命名空间与每 URL 的 `<image:image><image:loc>`。
- **改善 alt 文案**：生产环境画廊 alt 现在由 `pages/views/enrich.py` 生成，形如 `f"{product.name_t} — view {i+1}"`（见 `enrich.py:155`、`210`、`239`），其中 **"view 2" 对图片搜索零信息**。模型层已有 `alt_text` 字段（`ProductImage.alt_text` `models.py:212`、`ProjectImage.alt_text` `models.py:303`），但无状态生产模式下未被读取。打通它（或让 `seed_data.py` 支持 `alts` 数组）是比改名大得多的收益。

### Tier B — 只改「门面图」（约 55–60 张）

这些是真正会被图片搜索抓取、且出现在分享卡片里的图：

| 组 | 数量 |
|---|---|
| `static/images/products_page/` 分类图 | 6 |
| 根级 hero + 首页装饰图 | 6 |
| 各产品 `image` / `banner_image`（约 17 个产品 × 2）| ~34 |
| 项目封面图（`projects/*/` 首图）| 23 |

合计约 60 张，覆盖绝大多数图片搜索曝光。**其余 125 张画廊图不改。**

### Tier C — 存量画廊图（125 张）

收益/成本比低。**不要批量改**，只让**新上传**遵循新规范即可。

---

## 6. 风险提示

- **改名 = 断链**。已被 Google 索引的旧 URL 会 404。静态文件经 Whitenoise / Vercel 边缘提供，**无法按单文件做 301** —— 只能整目录重定向，代价更大。因此：**只改尚未索引的图，或接受旧图权重丢失。**
- **大小写敏感**：`VSP9M-01.webp` 在 Windows 本地能访问，部署到 Linux 构建环境后大小写不匹配会 404。这类文件即使不改名，也建议统一为小写以消除隐患。
- **`?v={% now "U" %}` 缓存穿透**：`templates/project_detail.html:127,131` 用时间戳做 `?v=`，改文件名后依然需要清缓存，注意回归验证方式（做 HTML 对比时先归一化 `?v=\d+`）。

---

## 7. 新图上传检查清单

上传前逐项确认：

- [ ] 文件名符合公式 `solarone-<产品/场馆>-<品类词>-<视角>-<序号>.webp`
- [ ] 全小写，只有 `a-z 0-9 -`
- [ ] 无下划线、无空格、无中文、无分辨率、无 `img/dsc`
- [ ] 词数 3–6，长度 ≤ 60 字符
- [ ] 品牌词 `solarone` 只出现一次
- [ ] 目录正确：产品图 `.webp` 会落到 `static/images/products/<slug>/`（由 slug 决定，无需手工建目录）
- [ ] 品类词/视角词取自本规范第 3.3 节词表
- [ ] 上传后在 admin 的 `alt_text` 字段填写**描述性** alt（不要写 "view 2"）
- [ ] 若为产品主图或横幅，确认已同步写入 `pages/seed_data.py` 对应字段

---

## 8. 附：批量改名脚本的注意事项

如确需批量重命名，务必：

1. **先备份** `static/images/` 与 `media/` 两个目录。
2. 用 `git mv` 而非 `rm` + 新建，保留文件历史。
3. 改名后**必须**同步 `pages/seed_data.py`，然后重建 `seed_data.json`（走 `sync_seed_data`）。
4. 跑完整测试：`E:/Python/python3/python.exe manage.py test pages --keepdb`。
5. **不要触碰**第 2 节列出的 2 个硬编码文件名。
6. Windows 下 `Path.write_text()` 会写 `\r\n`，若脚本读写文本需用 `read_bytes`/`write_bytes`。

---

*本规范基于 2026-09-22 对仓库的实际扫描（185 个 webp、23 个项目目录）编写。*
