# SolarOne 全站体检报告

**日期：** 2026-10-06  
**范围：** SEO / GEO / 性能 / 技术健康度  
**模式：** 只读审查，未改代码  
**线上地址：** https://www.solaronelighting.com

---

## 一、线上实测性能数据（浏览器 Performance API）

| 页面 | TTFB | DOMContentLoaded | Load | 传输体积 | 资源数 | HTML 解码 |
|------|------|-------------------|------|----------|--------|-----------|
| 首页 `/` | 97ms | 1074ms | 2812ms | 134 KB | 12 | 43 KB |
| 产品详情 `/products/m-series/` | 96ms | 930ms | 1372ms | 106 KB | 11 | 67 KB |
| 项目列表 `/projects/` | 95ms | 577ms | 1002ms | 36 KB | 11 | 78 KB |

**首页最重资源 Top 5：**

| 资源 | 传输大小 | 耗时 |
|------|----------|------|
| hero-main-2-portrait.webp | 119 KB | 1712ms |
| hero-main-1-portrait.webp | 73 KB | 659ms |
| base.css | 20 KB | 229ms |
| inter-latin-500.woff2 | 47 KB | 508ms |
| logo.webp | 23 KB | 160ms |

**静态资产盘点：**

| 类别 | 数量 | 总大小 |
|------|------|--------|
| base.css | 1 | 70.1 KB（未压缩） |
| fonts.css | 1 | 14.6 KB |
| 静态图片 | 295 | 34.7 MB |
| 最大单图 | — | 466 KB（ccsc-baseball-1080p-03.webp） |

**性能总评：** TTFB 优秀（<100ms），边缘缓存命中率高。首页 Load 偏慢（2.8s），主要被两张 hero portrait 图拖慢。CSS 70KB 未压缩是最大可优化项（gzip 后约 12-18 KB，但构建管线未做 minify）。

---

## 二、SEO 审查结果

### 已做得好的（无需改动）

| 项目 | 状态 | 说明 |
|------|------|------|
| Title 标签 | ✅ | 每页动态生成，产品/项目/新闻均有独立 SEO title |
| Meta Description | ✅ | 每页动态生成，产品有 `seo_description_t` |
| Canonical URL | ✅ | 固定 `canonical_origin`，防止 preview 域名泄漏 |
| Hreflang | ✅ | 6 语种 + x-default，通过自定义模板标签实现 |
| Sitemap | ✅ | 动态生成，含图片 sitemap + 多语言 alternate |
| Open Graph | ✅ | 5 项核心 OG 标签齐全，og:image 有 fallback |
| JSON-LD 结构化数据 | ✅ | Organization / Product / FAQPage / BreadcrumbList / WebSite / ItemList / NewsArticle / Article 全覆盖 |
| URL 结构 | ✅ | 纯 slug，无数字 ID，i18n 前缀合理 |
| 图片 alt | ✅ | 所有 `<img>` 均有描述性 alt |
| 图片懒加载 | ✅ | LCP 图 `fetchpriority="high"`，下方图 `loading="lazy"` |
| 响应式图片 | ✅ | `<picture>` + `srcset` + `sizes`，含 portrait 裁切 |
| Robots.txt | ✅ | 明确 Allow AI 爬虫（GPTBot/ClaudeBot 等） |
| 安全头 | ✅ | HSTS / CSP / X-Frame-Options / Referrer-Policy 全配 |
| 404/500 错误页 | ✅ | 自定义模板，独立于 base.html，零 DB 依赖 |
| 移动端适配 | ✅ | viewport / 响应式断点 / 触摸目标 44px / RTL 移动支持 |

### 需改进的（按优先级排序）

#### 🔴 高优先级

| # | 问题 | 严重度 | 影响 |
|---|------|--------|------|
| S1 | **产品翻译缺失** — 多个产品（FL1M、Glare Guard、RGB/RGBW、Accessory 等）翻译对象为空 `{}`，非英语语种回退英文 | HIGH | hreflang 价值被稀释；Google 视为跨语种重复内容；AI 爬虫判定薄内容 |
| S2 | **无对比/选购指南内容** — 全站无 "M Series vs RT410"、"LED 球场灯选购" 等决策辅助内容 | HIGH | AI 搜索引擎（Perplexity/ChatGPT Search）偏好此类内容 |
| S3 | **无教程/规范类内容** — 缺少 "如何确定球场照度"、"Lux 标准" 等教育内容 | HIGH | AI 引擎在生成回答时引用此类内容 |

#### 🟡 中优先级

| # | 问题 | 严重度 | 影响 |
|---|------|--------|------|
| S4 | **无 `<meta name="robots">`** — 无法对筛选页（`?venue=&sport=`）设 noindex | MEDIUM | 筛选 URL 产生重复内容爬取 |
| S5 | **面包屑只有 JSON-LD，无可视导航** — 用户和搜索引擎看不到面包屑路径 | MEDIUM | 丢失内链信号和用户导航便利 |
| S6 | **联系页有 2 个 H1** — "Request a Sample" 和 "Contact Us" 都是 `<h1>` | MEDIUM | 违反单 H1 最佳实践 |
| S7 | **Sitemap 缺 `<changefreq>`** | MEDIUM | 虽 Google 已弱化此字段，但仍是协议标准 |
| S8 | **Product Schema 缺 `offers`** — 无价格/可用性信息 | MEDIUM | 限制富摘要资格 |
| S9 | **OG locale:alternate 缺失** — 未声明其他 5 个语种的 OG 替代 | MEDIUM | 社交爬虫信号不完整 |
| S10 | **robots.txt 未屏蔽查询参数 URL** — `?page=`、`?venue=` 等可被爬取 | MEDIUM | 爬取预算浪费 |
| S11 | **Privacy/Terms 的 meta description 未翻译** | MEDIUM | 非英语搜索引擎显示英文描述 |

#### 🟢 低优先级

| # | 问题 | 严重度 | 影响 |
|---|------|--------|------|
| S12 | **Favicon 仅 WebP 格式** — Safari 不支持 WebP favicon | LOW | Safari 用户无图标 |
| S13 | **项目详情页无 H2/H3** — 只有 H1 + `<span>` 排版 | LOW | 内容结构信号弱 |
| S14 | **产品详情页无"相关产品"推荐** | LOW | 丢失内链机会 |
| S15 | **llm.txt 未在 robots.txt 中声明** | LOW | AI 爬虫发现性降低 |

---

## 三、GEO（生成式引擎优化）审查

### 优势

- **llm.txt 质量高**（113 行）：覆盖公司身份、产品差异化、实测数据、完整产品目录、场地类型、站点结构、URL 模式、301 重定向、meta 规范、关键词着陆页
- **FAQ 内容**：产品详情/概览页有可见的 FAQ 区（`<details>/<summary>`）+ FAQPage JSON-LD
- **关键词着陆页**：`/projects/football/`、`/projects/tennis/` 按场地类型分
- **产品描述技术性强**：具体到型号参数、替代功率、安装高度

### 缺口

| # | 缺口 | 影响 |
|---|------|------|
| G1 | **产品翻译空白的产品** 在 fr/es/de/ru/ar 版本中回退英文，AI 爬虫访问本地化 URL 时得到英文内容 | 高 |
| G2 | **无 llm-full.txt** — 部分 AI 爬虫寻找扩展版 | 低 |
| G3 | **无对比/选购/教程内容** — AI 引擎生成回答时缺乏可引用的深度内容 | 高 |
| G4 | **无客户评价/案例研究结构化内容** — 缺少 `Review`/`AggregateRating` 数据 | 中 |

---

## 四、性能优化审查

### 已做得好的

| 项目 | 说明 |
|------|------|
| 边缘缓存 | `s-maxage=300, stale-while-revalidate=86400`，HTML 边缘缓存 5 分钟 |
| 静态文件 | 内容哈希命名 + `Cache-Control: immutable, max-age=31536000` |
| 关键 CSS 内联 | ~2KB above-the-fold CSS 内联在 `<head>` |
| 资源提示 | `preconnect` Google 域名 + `preload` fonts.css/base.css |
| 字体 | 自托管 woff2 + `font-display: swap` + `unicode-range` 子集化（GDPR 友好） |
| Hero 图延迟加载 | 第 2/3 张 hero 图用 `data-src` 模式，初始 payload 减少 ~470KB |
| WebP 普及率 | 98% 静态图已转 WebP |
| GA4 | `async` 加载，无 MEASUREMENT_ID 时不发请求 |

### 可优化项

| # | 优化项 | 当前 | 预期收益 | 难度 |
|---|--------|------|----------|------|
| P1 | **CSS 压缩** — build.sh 中加 minify 步骤 | 70 KB 未压缩 | -18~28 KB/页（25-40%） | 低 |
| P2 | **图片尺寸上限** — 构建时 resize 到 max 1920px | 最大 466 KB/张 | 防止大图直达 CDN | 低 |
| P3 | **列表查询缺 select_related/prefetch_related** | 产品/项目列表无优化 | 消除 N+1（非 Vercel 环境） | 低 |
| P4 | **模板片段缓存** | 无 fragment cache | 减少热实例计算 | 中 |
| P5 | **HTML 压缩** — 构建时 minify | 无 | -5~10% HTML 体积 | 低 |
| P6 | **字体自托管** — fonts.css 当前已自托管，但 render-blocking | 2 个 render-blocking CSS | 可考虑 `media="print" onload` 技术 | 中 |

---

## 五、技术健康度

### 架构亮点

- **零 DB 生产模式**：内容来自 `seed_data.json`，构建期生成 `seed_data.py`，Vercel 不碰数据库
- **三套翻译机制清晰分离**：gettext / `_SIDEBAR_I18N` / `translations` JSONField
- **CSP 每页 nonce**：`ContentSecurityPolicyMiddleware` 生成加密 nonce
- **GDPR 友好访客追踪**：IP 经 SHA-256 + SECRET_KEY 加盐哈希，不存明文
- **测试覆盖**：~258 个测试方法，含图片路径守卫、RTL 隔离守卫、静态资源守卫

### 风险点

| # | 风险 | 严重度 | 说明 |
|---|------|--------|------|
| T1 | **vercel.json 无安全头兜底** | MEDIUM | 安全头完全依赖 Django middleware；若函数超时/边缘出错，无安全头 |
| T2 | **无 skip navigation 链接** | MEDIUM | WCAG 2.4.1 Level A 要求；屏幕阅读器用户需遍历整个导航 |
| T3 | **LocMemCache 在 Vercel 冷启动无效** | LOW | 每次冷启动缓存为空，但边缘缓存吸收了大部分负载 |
| T4 | **多图片缺 width/height HTML 属性** | LOW | 依赖 CSS `aspect-ratio`，旧浏览器可能 CLS |
| T5 | **`style-src 'unsafe-inline'`** | LOW | CSP 的 XSS 防护被削弱（但当前模板大量 inline style 是必要的） |

---

## 六、本地测速可行性

### 已完成

- ✅ 线上 Performance API 实测（TTFB / DOMContentLoaded / Load / 资源传输大小）
- ✅ 静态资产体积盘点

### 可进一步做但需要配置

| 工具 | 需要什么 | 说明 |
|------|----------|------|
| PageSpeed Insights API | `PSI_API_KEY` 环境变量 | 项目已有 `scripts/perf_baseline.py`，配置 key 即可跑 6 页 × 2 策略的 CWV 基线 |
| Lighthouse CLI | `npm install -g lighthouse` | 可跑完整本地审计（Performance / Accessibility / Best Practices / SEO 四维度评分） |
| 本地 dev server 对比 | `python scripts/dev_preview.py` | 可对比本地 vs CDN 的 TTFB 差异 |

### 建议

如果要做完整的本地 Lighthouse 审计，需要安装 Node.js 的 `lighthouse` 包。如果只需要 CWV 基线追踪，配置 `PSI_API_KEY` 跑现有脚本即可。

---

## 七、优先行动清单（Top 10）

| 序号 | 行动 | 类别 | 预期收益 | 工作量 |
|------|------|------|----------|--------|
| 1 | 补全 seed_data.json 中空白产品翻译（至少 fr/es/de） | SEO/GEO | 消除跨语种重复内容信号，提升 hreflang 价值 | 中 |
| 2 | build.sh 加 CSS 压缩步骤 | 性能 | 每页减少 18-28 KB 传输 | 低 |
| 3 | 创建 3-5 篇对比/选购指南内容页 | GEO | AI 搜索引擎引用率提升 | 高（内容创作） |
| 4 | 添加 `<meta name="robots">` 支持 + robots.txt 屏蔽查询参数 URL | SEO | 减少重复内容爬取 | 低 |
| 5 | 添加可视面包屑导航（不只是 JSON-LD） | SEO/UX | 内链信号 + 用户导航 | 低 |
| 6 | 修复联系页双 H1 | SEO | 符合单 H1 规范 | 低 |
| 7 | vercel.json 加安全头兜底 | 安全 | 防御纵深 | 低 |
| 8 | 添加 skip navigation 链接 | 可访问性 | WCAG Level A 合规 | 低 |
| 9 | robots.txt 加 `Allow: /llm.txt` | GEO | AI 爬虫发现性 | 低 |
| 10 | 构建时图片 resize 上限（max 1920px, quality 82） | 性能 | 防止超大图直达 CDN | 低 |

---

## 八、总体评分

| 维度 | 评分 | 说明 |
|------|------|------|
| SEO 基础 | **9/10** | meta/sitemap/hreflang/structured data 全面且正确；缺口在内容层面（翻译缺失、缺决策辅助内容） |
| GEO 就绪度 | **7/10** | llm.txt 优秀 + FAQ 内容好；但缺对比/教程类深度内容 |
| 性能 | **8/10** | TTFB 优秀、边缘缓存好、图片优化到位；CSS 未压缩是最大可优化项 |
| 可访问性 | **7/10** | ARIA 做得好；缺 skip link、部分图片缺尺寸属性 |
| 安全 | **9/10** | HSTS/CSP/安全头齐全；vercel.json 缺兜底 |
| 技术架构 | **9/10** | 零 DB 模式 + 内容哈希 + 测试覆盖，工程素养高 |

**综合：8.2/10** — 技术底子扎实，主要提升空间在内容层（翻译补全 + 深度内容创作）和构建优化（CSS 压缩）。
