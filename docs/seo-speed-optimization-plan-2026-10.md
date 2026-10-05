# SEO / GEO / 速度 优化实施手册（v1.10.16 起）

> 生成日期：2026-10-06　基线站点版本：**v1.10.15**（`d51234e`，已 push 上线）
> 所有「现状」数据均为**线上 curl 实测**（`https://www.solaronelighting.com`，带 www）或代码实证，非推测。
> 本文档是**操作手册**，每Task 含：证据 → 改动点（文件:行号）→ 步骤 → 验收 → 回滚。

---

## 0. 基线实测（决策依据）

### 0.1 速度基线 — HTML 层已优化到位，瓶颈全在图片

| 指标 | 实测值 | 结论 |
|---|---|---|
| HTML TTFB | 0.45–0.66 s | 可接受（Vercel 边缘） |
| HTML 传输量 | 原始 44–80 KB → **Brotli 后 13.7–20.1 KB**（约 3.2×） | ✅ 无优化空间 |
| 边缘缓存 | `X-Vercel-Cache: HIT`，Age 21/25/29 稳定 | ✅ |
| Brotli / HTTP/2 | 均已启用 | ✅ |
| CSS | 2 个文件，Brotli 后 **19.8 KB + 2.2 KB = 21.9 KB**，且**已有 `<link rel=preload as=style>`** | ✅ **不是瓶颈**（修正：此前按未压缩 86.7 KB 误判） |
| 外域脚本 | 仅 1 个（Google gtag，`async`，已有 `preconnect`） | ✅ |
| 字体 | 43 个 woff2 / 1.0 MB，已按 `unicode-range` 子集化 | ✅ 良好 |
| **静态图片总量** | **295 文件 / 34.7 MB**（`static/images/`） | ⚠️ **真瓶颈** |
| 列表页卡片图 | **84–127 KB / 张** | ⚠️ |
| `srcset` 覆盖 | 全站 39 个 `<img>`，**仅首页 hero 有** | ⚠️ 移动端也下载 1280w 原图 |
| LCP 图 preload | hero 有 `fetchpriority="high"`，但**无 `<link rel=preload as=image>`** | ⚠️ |
| products 双 banner | `products-bar-dark` 87,420 B + `products-bar-light` 92,402 B，**两张全下载**（CSS 主题显隐，md5 不同） | ⚠️ 白扔 ~90 KB |

**结论：HTML / CSS / 字体 / 缓存 / 脚本 五条线均已到位，剩余速度收益 100% 在图片。**

### 0.2 SEO 技术层 — 已正确、无需动的部分

canonical 自引用 ✅｜hreflang 六语双向 + x-default ✅｜RTL `dir="rtl"` ✅｜各页 H1 恰好 1 个（实测 / /contact/ /products/ /projects/ /about/ /products/m-series/ 全为 1）✅｜OG 七项齐全 ✅｜404 真 404 ✅｜无 noindex ✅｜生产无 N+1（走 seed）✅

### 0.3 确认的缺口（按优先级）

| ID | 缺口 | 影响面 | 优先级 |
|---|---|---|---|
| A1 | sitemap `lastmod` 全站 = `2018-10-20` | 59/59 条 URL | **P0** |
| A2 | 项目页 JSON-LD `image` 是相对路径 | 22 项目 × 6 语种 = **132 页** | **P0** |
| A3 | IndexNow 完全缺失（全库 0 命中） | Bing/Yandex 引流 | **P0** |
| B1 | AI crawler 只放行 6 个 | 缺 ~10 个主流 | P1 |
| B2 | 产品↔项目↔新闻 三座孤岛无交叉内链 | 全站权重传递 | P1 |
| B3 | Article 缺 `datePublished`/`author` | 132 页 | P1 |
| B4 | products 双 banner 两张全下载 | 每访客 ~90 KB | P1 |
| C1 | 图片无 `srcset`（295 张） | 全站移动端流量 | P1（大工程） |
| D1 | news 标题超长 1 条 | 1 篇 | P2 |
| D2 | RSS 无全文 | 1 个 feed | P2 |
| D3 | 无 `llms-full.txt` | GEO | P2 |
| D4 | Breadcrumb 缺 7 页 | 7 页 | P2 |
| D5 | HTML `Cache-Control` 为 `max-age=0, must-revalidate` | 全站 | P2 |

---

## 批次 A — P0 三项（本次执行）

### A1 · sitemap `lastmod` 修复

**证据**
- 线上：`curl https://www.solaronelighting.com/sitemap.xml` → 59 条 URL 的 `<lastmod>` **全部 = `2018-10-20`**。
- 本地：`http://127.0.0.1:8000/sitemap.xml` → `2026-10-05`（正确）。
- 代码逻辑**没错**：`pages/views/views_other.py:226-232` 读 `seed_data.json` 的 `os.path.getmtime()`。
- **根因**：Vercel serverless 下文件 mtime 不可靠（检出/缓存层改写），且 `build.sh` **无任何构建时间戳注入**。
- 后果：Google 认为全站内容 8 年未更新，直接影响抓取频率与「新鲜度」评估。

**改动点**
1. `build.sh` — 在 `python -m pages.seed_sync --json` 之后新增一步，生成 `pages/build_meta.py`
2. `.gitignore` — 新增 `pages/build_meta.py`（与 `pages/seed_data.py` 同为构建产物）
3. `pages/views/views_other.py:225-232` — 优先读构建时间戳，回落 mtime

**步骤**
```bash
# build.sh（插在 "Regenerating seed_data.py" 段之后）
BUILD_DATE="$(date -u +%Y-%m-%d)"
echo "=== [build.sh] Stamping build date: ${BUILD_DATE} ==="
printf "SITE_LAST_MODIFIED = '%s'\n" "$BUILD_DATE" > pages/build_meta.py
```

```python
# pages/views/views_other.py 替换 try 块
_lastmod = ''
try:
    from pages.build_meta import SITE_LAST_MODIFIED
    if SITE_LAST_MODIFIED:
        _lastmod = SITE_LAST_MODIFIED
except Exception:
    pass
if not _lastmod:
    try:
        _lastmod = datetime.fromtimestamp(os.path.getmtime(
            os.path.join(str(settings.BASE_DIR), 'seed_data.json')
        )).date().isoformat()
    except Exception:
        _lastmod = ''
```

**验收**
- 本地无 `pages/build_meta.py` 时回落 mtime（不报错）
- 线上 `/sitemap.xml` 的 `lastmod` = 部署当天日期，且**全站一致**（稳定，不随每次请求变化）

**风险 / 回滚**：只读新增，无数据改动。回滚 = 删 `build_meta.py` + 还原 try 块。

---

### A2 · 项目页 JSON-LD `image` 改绝对 URL

**证据**（线上实测，正则须允许 `nonce` 属性）
```
项目页 /projects/football-field-led-retrofit/
  @type = Article
  image = "/static/images/projects/.../bmhs-football-field-02.webp"   << 相对路径
产品页 /products/m-series/
  @type = Product
  image = "https://www.solaronelighting.com/static/..."               << 正确
```
⇒ Google 判定图片 URL 无效 → 富媒体结果与 AI 配图引用全部丢失，**只有项目页中招**。

**改动点**
- `templates/project_detail.html:515`

```diff
- "image": "{{ project.image_url|default:'' }}",
+ "image": "{{ canonical_origin }}{{ project.image_url|default:'' }}",
```
（对照：`templates/product_detail.html:984` 已是 `"{{ canonical_origin }}{{ product.banner_image_url }}"`）

**验收**：线上 22 个项目页的 JSON-LD `image` 均以 `https://` 开头（六语种各抽查）。

**风险 / 回滚**：1 行。注意 `{{ }}` 拼接不产生双斜杠（`image_url` 以 `/static/` 开头，`canonical_origin` 无尾斜杠）。

---

### A3 · IndexNow（Bing / Yandex 主动推送）

**证据**：`grep -riE "indexnow|bing|yandex"` 全库 **0 命中**。Bing 只能被动等爬虫 → 新内容收录慢。

**改动点（3 处新建 + 1 处路由）**
1. `pages/views/views_other.py` — 新增 `indexnow_key` 视图，返回 `text/plain`
2. `pages/urls.py` — 注册 `/<key>.txt`（**必须在通配路由之前**）
3. `solarone/settings.py` — `INDEXNOW_KEY`（从 env 读，内置默认值）
4. `scripts/indexnow_ping.py` — 发布后批量推送脚本（手工执行）

**约束**
- key 必须是 **8–128 位十六进制**（`[a-f0-9]`）。实施时生成 32 位并**写进文档与 settings 默认值**，key 文件内容与 URL 名必须一致。
- 端点：`POST https://api.indexnow.org/indexnow`，body `{"host","key","urlList"}`

**验收**
- `https://www.solaronelighting.com/<key>.txt` → 200、`text/plain`、内容 = key
- 推送脚本 dry-run 输出待推 URL 数（应 = 59 × 语种数，或至少 59 条 en 路由）

**风险 / 回滚**：新增只读路由，不影响既有页面。⚠️ `urls.py` 顺序：`i18n_patterns` 下加在 `sitemap.xml` 附近，确认不与 slug 冲突（key 是 32 位 hex，不会撞）。

---

## 批次 B — P1（A 完成后）

| ID | 任务 | 改动点 | 备注 |
|---|---|---|---|
| B1 | AI crawler 放行补齐 | `templates/robots.txt`（现 6 个：GPTBot / OAI-SearchBot / ClaudeBot / PerplexityBot / Google-Extended / Applebot-Extended） | 补：meta-externalagent、CCBot、Bytespider、Amazonbot、Claude-User、ChatGPT-User、DuckAssistBot、YouBot、Omgilibot、Diffbot |
| B2 | 打破三座内容孤岛 | 项目详情 → 相关产品卡；产品详情 → 应用案例卡；新闻 → 产品/项目 | 需**双路径同改**（`models.py` property ↔ `views/utils.py` 的 `_DictProject`/`_DictProduct`） |
| B3 | Article 补 `datePublished`/`dateModified`/`author` | `templates/project_detail.html:509-526` | 项目 seed 无日期字段 ⇒ 需用构建日期或加字段；先确认数据可得性 |
| B4 | products 双 banner 按需加载 | `templates/products.html:66-67` | 按主题只输出一张（服务端判断），或 `html.js` 门控 + `data-src` |

## 批次 C — 图片 `srcset`（大工程，需先定规格）

- 现状：295 张 / 34.7 MB，卡片图 84–127 KB，无 `srcset`
- 建议规格：**640w + 1280w** 两档（现有多为 1280×720，只需生成 640w 一档，约 +295 个文件）
- 需你确认：① 是否接受新增 ~295 个静态文件；② 是否只做**卡片图**（收益最大）还是全站
- 涉及：批量脚本 + `cards.py` + 列表/详情模板 + N-31 断点守卫复查

## 批次 D — P2（收尾）

D1 news 标题超长 1 条（`SolarOne FL6M-480W Light Up Tianjin Binhai International`，len=64，渲染 80 > 60）｜D2 RSS 全文｜D3 `llms-full.txt`｜D4 Breadcrumb 补 home/about/contact/news 列表/集合页｜D5 HTML 浏览器缓存（`vercel.json` headers 加 HTML 规则，**注意别写 `source:"/(.*)"`**）

---

## 执行铁律（每批次都必须遵守）

1. **改版本号先于跑测试**（否则 `tests_release_metadata` 假失败）。本批次完成后 bump → **v1.10.16**（`VERSION` / `solarone/settings.py:APP_VERSION` / `llm.txt` 三处）
2. **新守卫必须做变异探针**：改实现 → 确认变红 → 还原 → `git diff --stat` 零残留。探针包 `try/finally` + 先备份原始 bytes，**还原绝不 `git checkout`**
3. **双路径同改**：`pages/models.py` property ↔ `pages/views/utils.py` 的 `_DictProject`/`_DictProduct`（生产走 seed 那条）
4. **测试一律 `run_in_background=true`**（前台跑 >2 min 会被沙箱 SIGTERM）；**跑测试前先停 runserver**
5. **只跑相关分组**（全量 >20 min）。本批次相关：`tests_release_metadata`、`tests_static_assets`、`tests_meta_description_budget`、`tests_redirects`、`JsonLdValidityTests`
6. **提交**：`git add` 逐文件显式列（禁 `-A`、禁 `git rm` 批量）；message 落临时文件后 `commit -F`；**push 由你执行**
7. **每次提交前 `git status --short` 逐文件核对**（admin 保存会回写 `static/` 与 `seed_data.json`）
8. 线上验证：`curl -sL` + **必须带 www**（无 www 是 308）

---

## 验收命令（你在 PowerShell 里跑；我自己在 bash 里跑完给结论）

```powershell
# A1  sitemap 日期
(curl -sL "https://www.solaronelighting.com/sitemap.xml").Content -match '<lastmod>'

# A2  项目页 JSON-LD 图片
Invoke-WebRequest -Uri "https://www.solaronelighting.com/projects/football-field-led-retrofit/" -UseBasicParsing | Select-String -Pattern '"image"'

# A3  IndexNow key 文件
Invoke-WebRequest -Uri "https://www.solaronelighting.com/<key>.txt" -UseBasicParsing | Select-Object StatusCode, Content
```
> ⚠️ 你的终端里 `curl` 是 `Invoke-WebRequest` 的别名（无 `-sL`）、无 `grep`、无 `/tmp`。上面给了兼容写法。
