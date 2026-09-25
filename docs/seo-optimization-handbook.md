---
doc_id: seo-optimization-handbook
title: SolarOne 官网 SEO 优化手册
version: 1.2.0
status: active (M1+M2 已完成)
last_updated: 2026-09-19
owner: Sean Lu
related:
  - path: ../xwechat_files/.../seo-audit-solaronelighting.html
    role: 上一版审计基准（2026-09-16，72/100）
  - path: docs/i18n_翻译工作指引.md
    role: 翻译范围与术语规则（P0 落地的依据）
  - path: docs/优化建议清单.md
    role: 总体优化 backlog（含 N-32~N-43 部署/性能/i18n 项）
---

# SolarOne 官网 SEO 优化手册

> **用途**：把 2026-09-16 审计（72/100）的结论与当前代码状态（v1.6.2）重新核对，形成一份可执行的优化清单。先出本手册，**确认后再按手册逐项实施**。
> **当前阻塞**：全面翻译已暂停（英文文案未定稿）。P0（多语言标题/描述本地化）必须等英文定稿 + 母语校对后才能落地，详见 §2-P0。

## 0. 审计基准（2026-09-16）

| 维度 | 评分 |
|---|---|
| 技术 SEO | 92 |
| 页面 SEO（On-page） | 68 |
| 国际化 i18n SEO | 35 |
| 内容质量/深度 | 63 |
| 性能 / CWV | 82 |
| 结构化数据 | 90 |
| 内链 / 站点架构 | 78 |
| **综合** | **72** |

**审计核心结论**：技术地基扎实（HTTPS+HSTS、HTTP/2、压缩、规范化 308 链、完整 sitemap、正确 hreflang、100% alt、WebP、结构化数据齐全）；**最大短板是"本地化"**——6 种语言版本的 `<title>`/`<meta description>` 全是英文硬编码，只有 H1 被翻译。

## 1. 现状核对（逐项对照审计，已重新实测代码）

| 审计项 | 审计结论 | 当前代码状态（2026-09-19 实测） | 状态 |
|---|---|---|---|
| 多语言标题/描述本地化（P0） | 6 语言全英文硬编码 | 6 个静态模板的 `<title>`/`<meta description>` **已接翻译通道**（`base.html:11-12` 走 `config.meta_title`/`meta_description`，经 N-43 的 `_t()` + `{% blocktrans %}`）；但**译文尚未导入**（翻译暂停）。产品页标题公式仍为 `name_t — SolarOne LED Lighting`（`product_detail.html:6`） | 🟡 通道已建 / 译文待导入 |
| 产品页标题缺品类词（P1） | 仅"型号+品牌" | 确认 `product_detail.html:6`：`{{ product.name_t }} — SolarOne LED Lighting` | ❌ 未改 |
| m-series 重复内容（P1） | 两 URL 各带独立 canonical | 确认：`pages/urls.py:11-12` 两条路由；`views_products.py:237-239` `product_series` 委托 `product_detail`；`views_other.py:88,95` sitemap 收录两条；`templates/product_series.html` 从未渲染（死代码） | ❌ 未改 |
| 缺失网站分析（P1） | 无 GA4/Plausible/Umami | 确认：全仓库 grep 无 `gtag`/`G-`/`analytics`(除隐私文案)/`plausible`/`umami`/`google-site-verification` | ❌ 未改 |
| 内页缺 srcset（P2） | 仅首页有 | 确认：首页 hero 有 `<picture>`+`srcset`；产品/项目页图片无 | ❌ 未改（待拍板多尺寸变体） |
| 无 apple-touch-icon/manifest/preload（P2） | 仅 favicon | 确认 `base.html:26` 仅 `favicon.webp`；无 manifest；已内联 ~2KB critical CSS（`base.html:40-79`），但 `base.css` 仍 `<link>` 阻塞（`base.html:80`） | ❌ 未改 |
| 技术强项（✓） | HTTPS/HSTS/HTTP2/压缩/308/canonical/hreflang/alt/结构化数据/404 | 全部保持，且自审计后新增：CSP 基础版、字体自托管、critical CSS 内联、N-43 翻译通道 | ✅ 保持+增强 |
| 结构化数据（✓） | WebSite+Organization / Product+BreadcrumbList | 实测更全：`base.html:539` Organization+ContactPoint；`home.html:129` WebSite+SearchAction；`products.html:100` ItemList；`product_detail.html:927` Product+PropertyValue；`breadcrumb_jsonld.html` BreadcrumbList；`project_detail.html:447` Article；`projects.html:116` ItemList | ✅ 保持 |

## 2. 问题清单（按优先级重排）

### P0 — 多语言标题/描述本地化（最高优先，阻塞于英文文案）
- **证据**：`base.html:11-12`（`<title>`/`<meta description>` 用 `config.meta_title`/`meta_description`）；`pages/views/common.py` 已让这两个字段经 `_t()`（`i18n_overrides.json` 提供译文）；6 模板包 `{% blocktrans %}`；`docs/i18n_p0_draft.csv` 14 条 MT 草稿待校对。
- **影响**：343 个语言 URL 的本地化投入几乎白费；各语言市场无自然排名；易被判定低质量重复。
- **修复**：
  1. **阶段 A（静态模板，阻塞）**：英文文案定稿 → 母语校对 `docs/i18n_p0_draft.csv` → `python scripts/import_i18n_csv.py docs/i18n_p0_draft.csv` → 6 模板标题/描述五语落地。
  2. **阶段 B（产品/项目页，随全站翻译）**：标题公式改为"型号 + 品类词 + 卖点"（`product_detail.html:6`），品类词用 `category_t`（经 `enrich.py` 三级 fallback）；描述用已翻译的 `description_t`。
- **工作量**：中。**依赖**：英文文案定稿 + 母语校对。

### P1a — 产品页标题缺品类关键词
- **证据**：`product_detail.html:6`。
- **修复**：并入 P0 阶段 B；或先用静态 slug→品类映射（如 `m-series→LED Flood Light`、`rt410-series→Stadium Floodlight`）补标题词。
- **工作量**：低-中。**依赖**：P0 阶段 B 或品类映射表。

### P1b — `/products/series/<slug>/` 与 `/products/<slug>/` 重复内容
- **证据**：`pages/urls.py:11-12`；`views_products.py:237-239`（`product_series` → `product_detail`）；`views_other.py:88,95`（sitemap 两条）；`templates/product_series.html`（从未渲染，死代码）。
- **影响**：分散排名信号、浪费爬虫预算。
- **修复（推荐 301 方案）**：
  1. 保留规范 URL `/products/<slug>/`；
  2. 把 `/products/series/<slug>/` 用重定向视图 **301** 到 `/products/<slug>/`（在 `pages/urls.py` 加 redirect，或在 `views_products.py` 让 `product_series` 直接 `return redirect(...)`）；
  3. 从 sitemap 移除 series 条目（`views_other.py:95`）；
  4. 删除从未渲染的 `templates/product_series.html` 死代码（删除前确认无渲染引用——实际无）。
  - 备选：统一 canonical 指向 `/products/<slug>/`，但不如 301 彻底。
- **工作量**：低。**注意**：先确认无外链指向 `series/` 路径；若有则必须 301 而非 404。

### P1c — 全站缺失网站分析
- **证据**：grep 确认无 `gtag`/`G-`/`plausible`/`umami`/`google-site-verification`。
- **影响**：SEO 动作无数据支撑，等于"盲飞"。
- **修复**：部署 **GA4** + 关联 **Google Search Console**（含各语言国际定向报告）。GA4 脚本用现有 CSP nonce：
  ```html
  <script nonce="{{ request.csp_nonce }}" async src="https://www.googletagmanager.com/gtag/js?id=G-XXXX"></script>
  <script nonce="{{ request.csp_nonce }}">window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-XXXX');</script>
  ```
  保留 GSC 验证（DNS TXT 或 meta 标签）。**隐私权衡**：引入 Google 第三方脚本会打破此前"无第三方请求"的隐私定位——若坚持隐私优先，改用 **Plausible / Umami 自托管**。
- **工作量**：低。**需用户拍板**：GA4（标准）vs Plausible/Umami（隐私优先）。

### P2a — 内页（产品/项目）缺响应式图片 srcset
- **证据**：首页 hero 有 `<picture>`+`srcset`；产品/项目页图片无。
- **影响**：移动端 LCP 偏慢。
- **修复**：复用首页 `picture+srcset` 模式；为移动端提供 ≤1280w 轻量变体。
- **状态**：待用户拍板生成多尺寸变体（CLS/lazy 已做，v1.5.9）。

### P2b — 无 apple-touch-icon / Web App Manifest / CSS 预加载
- **证据**：`base.html:26` 仅 `favicon.webp`；无 manifest；`base.css` 仍 `<link>` 阻塞（`base.html:80`），虽有 ~2KB critical CSS 内联兜底。
- **修复**：补充 `apple-touch-icon`（多种尺寸）；加 `manifest.json` + `<link rel="manifest">`；把 `base.css` 改为 `preload`+`onload` 异步加载（critical CSS 已兜底，安全）。
- **工作量**：低。

## 3. 已确认无需处理 / 已完成（强项，保持）

- ✅ 全站 HTTPS + HSTS 预加载 + HTTP/2
- ✅ 规范化 308 链 → `https://www`
- ✅ sitemap 完整（49 英文 URL，7 语言 hreflang 含 x-default 自引用）
- ✅ 49 页全部 200；无缺 title/description/H1/canonical；100% alt；全 WebP
- ✅ 结构化数据全面（WebSite/Organization/Product/ItemList/BreadcrumbList/Article）
- ✅ 安全头（X-Frame-Options DENY、X-Content-Type-Options nosniff）
- ✅ 404 正确返回 404
- 🆕 自审计后新增：CSP 基础版、字体自托管（无第三方）、critical CSS 内联、N-43 多语言标题/描述翻译通道

## 4. 实施路线图（里程碑）

| 里程碑 | 内容 | 阻塞 | 工作量 |
|---|---|---|---|
| **M0** | 英文文案定稿 + P0 译文母语校对 + 导入 | 用户定稿 | 中 |
| **M1** | ✅ **P1b 重复内容修复**（301 + sitemap + 删死代码） | 无 | 低（已完成 ✅） |
| **M2** | ✅ **P1c 分析工具部署**（GA4 + GSC，用户拍板 GA4） | 用户拍板（已定 GA4） | 低（已完成 ✅） |
| **M3** | **P0 阶段 A + P1a 标题关键词**（随 M0 译文导入） | M0 | 中 |
| **M4** | **P2a 内页 srcset + P2b PWA/CSS 异步** | 用户拍板多尺寸变体（P2a） | 中 |

> 建议先做 **M1 + M2**（不依赖翻译，低风险高收益），M0 定稿后做 M3，最后 M4。

## 5. 验证方法

- **上线前**：`python manage.py test`（L1，146 用例）；L2 Playwright 渲染快照（标题/描述/og/canonical/hreflang 五语对照）。
- **上线后**：Google Search Console 国际定向报告；PageSpeed Insights / Lighthouse 实测 **LCP / CLS / INP** 三项核心指标；GA4 实时验证埋点生效。
- **重复内容修复验证**：`curl -I https://www.solaronelighting.com/products/series/m-series/` 应返回 **301 → /products/m-series/**；sitemap 中不再含 `series/` 条目。

## 6. 备注

- **联系表单邮件验证**正在进行（Cloudflare Email Routing 验证邮件待确认），与 SEO 无关，但建议并行完成 Vercel 邮件环境变量配置（见对话）。
- **翻译暂停**：英文文案定稿前不导入任何译文，避免返工。
- 本手册是执行依据；每完成一个里程碑在 `docs/seo-optimization-handbook.md` 顶部版本号 +1 并追加变更行。

## 7. 变更记录

### v1.1.0 (2026-09-19) — M1 完成
- **P1b 重复内容修复（已完成）**：
  - `pages/views/views_products.py`：`product_series()` 改为对 `product_detail` 的 **301 永久重定向**（`redirect(..., permanent=True)`，因在 `i18n_patterns` 内，语言前缀自动保留）。
  - `pages/views/views_other.py`：sitemap 移除 `product_series` 条目（产品已由 `product_detail` 覆盖）。
  - `templates/product_detail.html`、`templates/products.html`：侧栏子系列链接由 `product_series` 改为 `product_detail`。
  - 删除从未被任何视图渲染的死模板 `templates/product_series.html`，并清理其 3 处测试引用（`tests.py` 移除 `test_product_series_hero_is_lcp`、改 `test_detail_grid_collapses_at_1024` 仅校验 `product_detail`；`scripts/e2e/run_checks.py` 移除 `ps_html` 改校验 `pd_html`）+ 更新 `carousel_js.html` 注释。
  - 新增回归测试 `ProductSeriesRedirectTests`：验证 `/products/series/fl1m/` → 301 `/products/fl1m/`，且 `/fr/products/series/fl1m/` → 301 `/fr/products/fl1m/`（语言前缀保留）。
  - 验证：`manage.py test pages` 全量 **147 测试 OK**。
- **待定**：M2 需用户拍板分析工具（GA4 标准 vs Plausible/Umami 隐私优先）；M0/M3 阻塞于英文文案定稿；M4 待拍板多尺寸图片变体。

### v1.2.0 (2026-09-19) — M2 完成
- **P1c 分析工具部署（GA4，用户拍板）**：
  - `settings.py`：`GA4_MEASUREMENT_ID` / `GSC_VERIFICATION_CODE` 取自 env（空 = 不加载第三方）；CSP `script-src` 加 `https://www.googletagmanager.com`，`connect-src`/`img-src` 加 `https://www.google-analytics.com` 与 `https://*.google-analytics.com`，`connect-src` 另加 `https://analytics.google.com`。
  - `pages/views/common.py`：`get_common_context()` 注入 `ga4_id` / `gsc_code`。
  - `templates/base.html`：`<head>` 注入 GA4 异步 snippet（CSP nonce）+ GSC 验证 meta（仅当 code 设置）。
  - 新增 `AnalyticsRenderingTests`：未设置不渲染、设置后渲染带 nonce 的 snippet、GSC meta 渲染。
  - 验证：`manage.py test pages` 全量 **150 测试 OK**。
  - **上线动作**：Vercel 设 `GA4_MEASUREMENT_ID=G-XXXX` 与（可选）`GSC_VERIFICATION_CODE`，重新部署生效。隐私权衡：引入 Google 第三方脚本，打破此前「无第三方请求」定位。
- **剩余**：M0/M3 阻塞英文文案定稿（翻译暂停）；M4 待拍板多尺寸图片变体（P2a）与 PWA/manifest（P2b）。
