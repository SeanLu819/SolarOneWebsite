# SolarOne 图片手动处理清单

> 生成时间：2026-10-03 19:40 · 数据来源：`.workbuddy/preview/image_audit.json`
> 本清单**只读**，未改动任何图片。按顺序处理，每项处理完可勾选。

## ⚠️ 动手前必读（4 条会直接打挂线上）

1. **不要改文件名**。图片路径写死在 `seed_data.json` / `pages/seed_data.py` 的 `images` 数组里，
   改名 = 线上 404。想换图就保持文件名覆盖。
2. **不要删 `<slug>` 目录里的图**。产品/项目画廊是**目录枚举**渲染的
   （`pages/views/utils.py:325-339` 的 `_list_static_dir`），文本里搜不到也照样显示 ——
   删了 = 那个产品页少一张图，属于**视觉变更**，不是清垃圾。
3. **不要动这 4 个写死的文件名**：`old-hid-lighting.webp`、`new-led-lighting.webp`
   （`templates/project_detail.html` 硬编码）、`m-series/certifications-ul-dlc-gs-ce-ip66.webp`、
   `rgb-rgbw/rgbw-interface-0-10v-dali-dmx-certification-ip66-ik08.webp`
   （`pages/views/enrich.py:21` 的 `DEFAULT_CERT_IMAGE` 兜底用）。
4. **透明通道图不能简单对比度压缩**。判据不是「B/px > 0.30」（照片类天然高），
   而是「重压后是否真变小」。用 `scripts/optimize_images.py --dry-run` 先验算，它有
   PSNR ≥40dB 门禁 + alpha 合成白底（否则透明区算出虚假低值）。

---

## 第 1 优先：唯一的 >1 MB 离群图（1 张，省 ~1.3 MB）

这张比全站第 2 名大 3.3 倍、同相册其它图只有 0.1–0.3 MB → **当时漏压了**。

| 勾 | 当前 | 尺寸 | 绝对路径 | 动作 |
|---|---|---|---|---|
| [ ] | **1.54 MB** | 1217x675 | `E:\Python\PROJECT\website\static\images\projects\beijing-international-tennis-center\bitc-tennis-03.webp` | 重导出不改尺寸，PSNR≥40dB |

---

## 第 2 优先：比例错配（渲染时被裁，**必须重导出而非压缩**）

渲染框是 16:9，源图不是 → 白白传了像素还被裁掉。

| 勾 | 当前 | 尺寸 | 比例 → 裁切 | 绝对路径 | 动作 |
|---|---|---|---|---|---|
| [ ] | 330 KB | 1920x442 | 4.34:1 → 裁 59% | `E:\Python\PROJECT\website\static\images\products\accessory\glare-shield-rt410-bar-03.webp` | 重导出 16:9 |
| [ ] | 330 KB | 1920x442 | 4.34:1 → 裁 59% | `E:\Python\PROJECT\website\static\images\products\glare-shield-for-rt410\glare-shield-rt410-bar-03.webp` | 重导出 16:9 |
| [ ] | 244 KB | 1920x600 | 3.20:1 → 裁 44% | `E:\Python\PROJECT\website\static\images\products\fl16m\fl16m-3d-view.webp` | 重导出 16:9 |
| [ ] | 226 KB | 1920x442 | 4.34:1 → 裁 59% | `E:\Python\PROJECT\website\static\images\products\fl1m\fl1m-bar-1.webp` | 重导出 16:9 |
| [ ] | 213 KB | 1920x442 | 4.34:1 → 裁 59% | `E:\Python\PROJECT\website\static\images\products\fl9m\fl9m-bar-1.webp` | 重导出 16:9 |
| [ ] | 203 KB | 1920x442 | 4.34:1 → 裁 59% | `E:\Python\PROJECT\website\static\images\products\rt400hb\rt400hb-barnner-02.webp` | 重导出 16:9 |

> ⚠️ 其中 2 张 `glare-shield-rt410-bar-03.webp` **md5 完全相同**（重复副本），
> 且两张都在**活目录**（`products/accessory/`、`products/glare-shield-for-rt410/`）里会被渲染。
> 只压不裁的话，两个页面显示的是同一张 4.34:1 的图。

---

## 第 3 优先：像素过量 >1872px 宽（47 张 / 10.07 MB）

渲染框最宽 **1248 px**。这些图宽 1920，多出的 35% 像素纯浪费。
**批量降到 1280 宽**即可，预计这部分 10.07 MB → 4.53 MB。

按相册归并（每个相册基本都是 5 张 1920×1080 一起处理最省事）：

| 勾 | 相册目录 | 张数 | 体积 |
|---|---|---|---|
| [ ] | `images\projects\beijing-liu-li-bridge` | 5 | 1.65 MB |
| [ ] | `images\projects\perryville-high-school` | 5 | 1.47 MB |
| [ ] | `images\projects\red-1-karting-beijing` | 5 | 1.24 MB |
| [ ] | `images\projects\garrison-forest-school` | 5 | 1.19 MB |
| [ ] | `images\projects\national-olympic-sports-center-beijing-tennis-cour` | 5 | 0.91 MB |
| [ ] | `images\projects\north-creek-community-center` | 3 | 0.84 MB |
| [ ] | `images\projects\baseball-field-led-retrofit` | 4 | 0.78 MB |
| [ ] | `images\projects\beijing-capital-international-airport` | 5 | 0.77 MB |
| [ ] | `images\projects\pickle-n-par-club` | 5 | 0.62 MB |
| [ ] | `images\projects\mcintosh-county-academy` | 5 | 0.61 MB |

---

## 第 4 优先：其余超大图 >200KB（49 张 / 14.81 MB）

> 这一档是「全站 318 张 / 37.71 MB」里的大头。`200–300 KB` 那 31 张优先级最低，可以最后处理。

### 4a. 300–500 KB（17 张 / 6.14 MB）

| 勾 | 当前 | 尺寸 | 比例 | 绝对路径 |
|---|---|---|---|---|
| [ ] | 466 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\baseball-field-led-retrofit\ccsc-baseball-1080p-03.webp` |
| [ ] | 441 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\beijing-liu-li-bridge\llq-roadway-1080p-01.webp` |
| [ ] | 434 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\red-1-karting-beijing\red1-karting-1080p-04.webp` |
| [ ] | 434 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\north-creek-community-center\ncc-tennis-02.webp` |
| [ ] | 410 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\perryville-high-school\phs-football-05.webp` |
| [ ] | 396 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\beijing-liu-li-bridge\llq-roadway-1080p-03.webp` |
| [ ] | 395 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\red-1-karting-beijing\red1-karting-1080p-03.webp` |
| [ ] | 394 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\beijing-liu-li-bridge\llq-roadway-1080p-02.webp` |
| [ ] | 360 KB | 1520x856 | 16:9 OK | `E:\Python\PROJECT\website\static\images\products\vsp-xxxxw-9m-yp\VSP9M-04.webp` |
| [ ] | 337 KB | 1280x720 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\chunan-velodrome\bycicle-chunan03.webp` |
| [ ] | 330 KB | 1920x442 | 4.3:1 → 16:9 框裁掉 59% | `E:\Python\PROJECT\website\static\images\products\accessory\glare-shield-rt410-bar-03.webp` |
| [ ] | 330 KB | 1920x442 | 4.3:1 → 16:9 框裁掉 59% | `E:\Python\PROJECT\website\static\images\products\glare-shield-for-rt410\glare-shield-rt410-bar-03.webp` |
| [ ] | 327 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\perryville-high-school\phs-football-01.webp` |
| [ ] | 314 KB | 1280x720 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\national-snow-and-ice-research-center\27factory-02.webp` |
| [ ] | 310 KB | 1280x720 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\olympic-sports-center-gymnasium-beijing\oscg-01.webp` |
| [ ] | 304 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\garrison-forest-school\Garrison_Forest-1.webp` |
| [ ] | 300 KB | 1920x1080 | 16:9 OK | `E:\Python\PROJECT\website\static\images\projects\garrison-forest-school\Garrison_Forest-2.webp` |

### 4b. 200–300 KB（31 张 / 7.13 MB）

```
images/projects/beijing-liu-li-bridge/llq-roadway-1080p-04.webp   292 KB  1920x1080
images/projects/perryville-high-school/phs-football-02.webp   292 KB  1920x1080
images/projects/garrison-forest-school/Garrison_Forest-4.webp   291 KB  1920x1080
images/projects/beijing-capital-international-airport/bcia-airport-04.webp   287 KB  1920x1080
images/projects/north-creek-community-center/ncc-tennis-01.webp   282 KB  1920x1080
images/projects/olympic-sports-center-gymnasium-beijing/oscg-05.webp   266 KB  1280x720
images/products/rt590fl-s/rt590fl-s-03.webp            258 KB  1520x856
images/hero-main-2.webp                                246 KB  1920x1078
images/products/fl16m/fl16m-3d-view.webp               244 KB  1920x600
images/projects/perryville-high-school/phs-football-04.webp   239 KB  1920x1080
images/projects/beijing-capital-international-airport/bcia-airport-02.webp   238 KB  1920x1080
images/projects/perryville-high-school/phs-football-03.webp   236 KB  1920x1080
images/projects/olympic-sports-center-gymnasium-beijing/oscg-02.webp   235 KB  1280x720
images/projects/yingdong-natatorium/ydyyg-swim-01.webp   234 KB  1280x720
images/products/rt600sl-t/RT600SL-T.webp               233 KB  1280x720
images/projects/narbonne-arena/Narbonne-basketball-04.webp   230 KB  1280x720
images/projects/chunan-velodrome/bycicle-chunan02.webp   230 KB  1280x720
images/products/fl1m/fl1m-bar-1.webp                   226 KB  1920x442
images/projects/football-field-led-retrofit/bmhs-football-field-03.webp   225 KB  1280x720
images/hero-main-3.webp                                221 KB  1920x1078
images/projects/olympic-sports-center-gymnasium-beijing/oscg-03.webp   215 KB  1280x720
images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-03.webp   215 KB  1920x1080
images/products/fl9m/fl9m-bar-1.webp                   213 KB  1920x442
images/pwa-icon-512.png                                211 KB  512x512
images/projects/chunan-velodrome/bycicle-chunan01.webp   210 KB  1280x720
images/projects/national-olympic-sports-center-beijing-tennis-cour/bnoc-tennis-1080p-02.webp   209 KB  1920x1080
images/projects/football-field-led-retrofit/bmhs-football-field-02.webp   208 KB  1280x720
images/projects/mcintosh-county-academy/mc-football-04.webp   207 KB  1920x1080
images/projects/olympic-sports-center-gymnasium-beijing/oscg-04.webp   206 KB  1280x720
images/products/rt400hb/rt400hb-barnner-02.webp        203 KB  1920x442
images/projects/national-snow-and-ice-research-center/27factory-01.webp   201 KB  1280x720
```

---

## 参考：目标规格

| 用途 | 渲染框 | 建议导出 |
|---|---|---|
| 项目列表卡 / 详情大图 | 1248×560 ~ 1200×675 | **1280×720（16:9）** |
| 产品画廊 | 1248 宽（contain 4:3） | 1280 宽，原比例 |
| 首页 hero | 1920 视口 | 保持 1920，但压 q 值 |
| 横条图（1920×442） | 16:9 框 | 1280×295 或重出 16:9 |

> ⚠️ 降尺寸会改 md5 → 若某张图在**重复副本组**里，降完可能与同组另一张不再相同，
> 反而制造新重复。`fl9m-3d-view` 系 4 份、`beamangle-12183050.webp` 9 份属于这组，
> 建议**整组一起改到同一规格**，别只改其中一份。

---

## 别处理的（已确认安全 / 有意保留）

| 文件 | 原因 |
|---|---|
| `images/news/low-cct-…/_source/W0….jpg`（3 张 / 0.42 MB） | 虽在磁盘上但已 gitignore，是重导出用的**原图来源**，必须留 |
| `images/products/ordering/sample-number.webp` | 唯一确认的死图（与被引用的 `m-series/sample-number.webp` md5 相同）—— 但**删不删都行，只省 60 KB** |
| 19 张 `certifications-…ip66.webp`（工作区已 D 删除） | 已验证全站零引用（seed 只有 `m-series` + `rgb-rgbw` 两条），删了**不 404、无视觉变化**，去重收益保留。你 push 时会随 commit 一起进仓库 |
| `scripts/audit_images.py` 报的「未引用 31 张 / 2.94 MB」 | ❌ **假阳性**，其中 27 张在模板里（`hero-main-*`/`logo`/`favicon`/`optics-*`/`agent-*`），**别删** |

---

## 处理完的回归检查

```bash
# 1. 全量测试（约 2 分半，前台跑会被 SIGTERM → 必须后台跑）
E:/Python/python3/python.exe manage.py test pages

# 2. 重跑图片审计，看体积与重复数是否下降
E:/Python/python3/python.exe scripts/audit_images.py

# 3. 线上抽查改过的项目页（注意必须带 www，裸域 308）
curl -sI -L https://www.solaronelighting.com/static/images/projects/beijing-international-tennis-center/bitc-tennis-03.webp
```

跑测试前**不要**改 `VERSION` / `solarone/settings.py:485 APP_VERSION` / `llm.txt` 的版本号，
否则启动时 settings 读旧值会让 `tests_release_metadata` 报假失败。

图片文件名/数量变动后，`pages/tests_cert_images.py` 与 sitemap 图片守卫
（`test_every_sitemap_image_loc_resolves_to_a_real_file`）会一起验证引用完整性 ——
这两个是专门锁图片引用的，别跳过。
