# SEO + GEO 全站审计报告

- **审计日期**：2026-10-07
- **站点版本**：v1.10.23（取自线上 `llm.txt`）
- **域**：`www.solaronelighting.com`（无 www 308 → www）
- **语言**：en（无前缀）/ fr / es / de / ru / ar（RTL）
- **方法**：直接抓取**线上已部署产物**（最准），交叉核对仓库静态配置。所有结论附实测 URL/值。

---

## 结论先行（一句话）

技术 SEO 与 GEO 的**地基很强**（hreflang 全覆盖、JSON-LD 体系完整、llm.txt 丰富、AI crawler 全放行、IndexNow 已接线、图片 srcset 优化）。审计列出的 4 项可修缺口已在 v1.10.24 全部落地（301 / og:image / 落地页 FAQ / `@id`+author），另有 2 项经核查判定**不该做**（`llms.txt` 归一、`SearchAction`）。剩余为**手动配置**（Cloudflare AI Crawl Control、Vercel env）与**内容债务**。

---

## A. 技术 SEO

### A1. 语言路由 & hreflang —— ✅ 强
- 路由：`/`(en) `/fr/` `/es/` `/de/` `/ru/` `/ar/`，ar 页 `<html lang="ar" dir="rtl">` 实测正确。
- 每个页面 `<head>` 输出 **7 条 `alternate hreflang`**（6 语 + `x-default`），且 `x-default`→en（无前缀）。
- 自引用正确：en 页 `hreflang="en"`→`/` 且 `x-default`→`/`；fr 页 `hreflang="fr"`→`/fr/`。
- sitemap 内每个 `<url>` 同样携带 7 条 `alternate`（实测 420 条 / 60 URL = 7.0/URL），HTML 与 sitemap 一致。
- **无冲突、无缺失、无回退歧义。**

### A2. Canonical —— ✅ 强
- 首页 `canonical`= `https://www.solaronelighting.com/`
- 产品页 `canonical`= `https://www.solaronelighting.com/products/rt820sl-t/`
- 各语言页**自 canonical 正确**（fr→`/fr/`，互不指向对方）。无 canonical 错误。

### A3. Title / Meta Description —— ✅ 强（标题）/ ⚠️ 描述翻译欠账
- 长度均合理（45–60 字符），无超长/截断。示例：
  - en 首页：`SolarOne — LED Stadium Lighting Solutions Since 2007`
  - 产品：`LED Roadway & Street Lights RT820SL-T — 240W | SolarOne`
  - 落地页：`LED Stadium Lighting — SolarOne Sports Floodlights`
- 多语标题**已本地化**：fr/es/de/ru/ar 标题均翻译（ar 为阿语）。
- ⚠️ **meta description 非英回退**：实测 es 产品页标题西语化，但 `description` 仍是英文
  （`"The RT820SL-T is the higher-output roadway luminaire..."`）。属已知内容欠账（P1：描述+新闻标题待译）。影响：该语种页在 SERP 摘要质量偏低，但不触发重复内容惩罚（hreflang 仍有效）。

### A4. Sitemap —— ✅ 干净 / ✅ lastmod 已按真实数据处理（v1.10.24 `2d3e158`）
- 60 个 canonical URL；含 image 扩展（**251 个 `image:image`**，产品/项目/集合页图均有）。
- 覆盖：首页、/products/、/projects/、24 产品、22 项目、3 新闻、/stadium-lighting/。
- **无过期条目**：已删落地页未出现在 sitemap；hreflang 每 URL 7 条（420/60 = 7.0）。
- ✅ **lastmod 已修**：原"全站同值 = 构建戳"（读作"60 个页面每次部署都变了"，Google 会逐步折扣
  不可信的 lastmod）。先量数据发现：
  | 类型 | 数量 | 真实时间字段 |
  |---|---|---|
  | 新闻 | 3 | ✅ 有 `published_at`（8/31、9/13、9/28） |
  | 产品 | 24 | ❌ seed 里**零时间字段** |
  | 项目 | 22 | ❌ seed 里**零时间字段** |
  | 静态/集合 | 11 | ❌ 无 |

  `lastmod` 在 sitemap schema 里是**可选**的，57/60 拿不到真值时**不输出比输出假日期更诚实**。
  新政策：**只在有真实日期时输出** ⇒ 3 个新闻页带真值，其余 57 个不输出。
  curl 实证：60 个 `<url>` 完整、XML 合法、恰好 3 个 `<lastmod>`、hreflang 仍 7.0/URL、251 张图未丢。

### A5. robots.txt —— ✅ 强
- `Allow: /`；`Disallow: /admin/`。
- **AI crawler 全放行**（batch B2+B1）：GPTBot、OAI-SearchBot、ClaudeBot、PerplexityBot、Google-Extended、Applebot-Extended、meta-externalagent、CCBot、Bytespider、Amazonbot、Claude-User、ChatGPT-User、DuckAssistBot、YouBot、Omgilibot、Diffbot——共 16 个。
- 含 `Sitemap:` 指令、非标准 `LLM-Txt:`、`Feed:` 提示。
- ⚠️ **Cloudflare 边缘 AI Crawl Control 仍需手动开启**（P1，robots 只是礼貌信号，真实拦截在边缘）。需到 Cloudflare 控制台 Security → Bots → AI Crawl Control 放行，否则上述 robots 放行无效。

### A6. 结构化数据 JSON-LD —— ✅ 强（v1.10.24 已补 @id / author）
站点全页输出 JSON-LD（在 `<body>`，非 head），实测类型：
| 页面 | @type |
|---|---|
| 首页(en/fr) | WebSite, Organization |
| 产品详情 | Product, FAQPage(含 Question/Answer), BreadcrumbList, Brand, Organization |
| 落地页 | BreadcrumbList, **FAQPage（v1.10.24 新增）**, Organization |
| 新闻详情 | NewsArticle（**author 已补**）, BreadcrumbList, Organization |

亮点：**产品页有 FAQPage**，对 GEO（AI 直接抽取问答）极有利；全站 Organization + BreadcrumbList 齐全。

**v1.10.24 已修（原缺口）**：
- ~~所有 JSON-LD 缺 `@id`~~ → 全站实体均有锚点：`#organization` / `#website` /
  每个页面自己的 `#product` `#article` `#itemlist` `#breadcrumb` `#faq`。
  `WebSite.publisher`、`NewsArticle.author/publisher`、`Product.brand`、
  项目 `Article.publisher` 改为**引用同一 `@id`** 而非内联副本 ⇒ 知识图谱能识别为同一实体。
- ~~NewsArticle 缺 `author`~~ → 已补，与 `publisher` 指向同一 Organization。
- ~~落地页无 FAQPage~~ → `/stadium-lighting/` 已有 6 组页面级问答 + FAQPage（见 A8）。
- 🔴 **刻意不加 `WebSite.potentialAction` / `SearchAction`**：站点**没有搜索**（无路由、无模板、无表单）。
  SearchAction 是 SEO 检查清单里常见的复制项，此处会指向不存在的端点。已加守卫断言它永不出现。

### A7. 已删除的 3 个根级关键词落地页 —— ✅ 已修（v1.10.23 提交 `aa2a515`）
- 实测：`/sports-lighting/`、`/football-stadium-lights/`、`/tennis-court-lighting/` 原本 **HTTP 404**（无重定向）。
- **已登记 301**（`pages/redirects.py`），按用户指定的映射：

| 旧 URL | 301 → | 说明 |
|---|---|---|
| `/sports-lighting/` | `/stadium-lighting/` | 合并后的关键词 hub |
| `/football-stadium-lights/` | `/projects/football/` | foot field + soccer field 项目合集 |
| `/tennis-court-lighting/` | `/projects/tennis/` | outdoor + indoor tennis 项目合集 |

- 语言前缀自动保留（`i18n_patterns` + `LocaleMiddleware`，实测 `/fr/sports-lighting/` → `/fr/stadium-lighting/`）。
- curl 实测 + 守卫 31/31绿。

### A8. Social / og:image —— ✅ 已修（v1.10.24 提交 `eb3ed0b`）
- 原状：产品页/ar 页/项目页有 `og:image`；**首页(en/fr) 与 `/stadium-lighting/` 完全没有**
  （`base.html` 只在 `SiteConfig.og_image` 有值时输出，而该字段生产为空 ⇒ 页面声明
  `twitter:card=summary_large_image` 却没有图 ⇒ Facebook/WhatsApp/Telegram/Slack 只显示纯文字）。
- **已修**：新增 `static/images/og-default.webp`（1200×630 = 1.91:1 品牌卡，由
  `scripts/make_og_default.py` 从现有 hero 图 + logo 生成），`base.html` 的
  `og_image` / `twitter_image` 两个 block 各加 `{% else %}` 兜底指向它。
- 刻意**入库而非 build 期生成**：v1.10.18 的图片变体热修已证明 build 期生成器可能静默产出 0 个文件，
  而 404 的 og:image 比"仅通用"更糟。后台 `SiteConfig.og_image` 真分支保留，管理员仍可覆盖。
- 守卫 `pages/tests_seo_og_image.py` 5/5 绿 + 5/5 变异探针。

### A9. 落地页内容深度 —— ✅ 已修（v1.10.24 提交 `1c7443f`）
- `/stadium-lighting/` 原本是「2 个产品 + 表格 + 9 个项目」的薄结构页，缺 GEO 最看重的问答块。
- **已补页面级 FAQ**（6 组，`views_stadium.STADIUM_FAQ`）：要几个灯杆、能否用于 televised /
  超慢动作回放、配光角度、效率与防护、供电与调光、光度报告。
- 所有数字均可溯源到 `seed_data.json` 的 `energy_data` / `ordering_info`；守卫做**双向对拍**
  （seed→期望、期望→FAQ 文案），反向对拍当场抓出草稿里一处无据的"1000 W HID"对比并已删除。
- 可见折叠区（`<details>`，无 JS 可用）与 FAQPage JSON-LD **同源**，守卫断言两者文案不可漂移。

---

## B. GEO（生成式引擎优化）

### B1. llm.txt —— ✅ 强
- `https://www.solaronelighting.com/llm.txt`（规范名）与 `llms.txt`（带 s）均 200 且**内容完全一致**（md5 相同）。
- 内容质量高：品牌、产品矩阵、实测项目数据（含 lux/均匀度/赛事合规）、联系方式、明确 "SolarOne 不翻译" 规则。这是 GEO 的优质机器可读入口。
- ℹ️ **审计初稿建议把 `llms.txt` 301 到 `llm.txt`，此建议撤回**：查 `build.sh:225-227`，
  这份复制是 **B1 批次的刻意设计** —— "Some AI crawlers only recognise /llms.txt"。
  强行归一会让只认复数形式的 crawler 拿不到内容，与 GEO 目标相反。**两个入口都要保留。**

### B2. AI crawler 放行 —— ✅ 配置强 / ⚠️ 边缘未配
- robots.txt 已全放行（见 A5）。
- ⚠️ **Cloudflare 边缘 AI Crawl Control 未确认开启**（P1，手动）。这是 GEO 能否被 AI 引擎实际抓取的决定性一环。

### B3. IndexNow —— ✅ 已实现（待验证 key）
- 仓库已接线：`pages/urls.py`、`pages/views/...`、`scripts/indexnow_ping.py`、`pages/tests_indexnow.py`、`INDEXNOW_KEY` 配置链路存在（batch A）。
- **待验证**：Vercel 环境变量 `INDEXNOW_KEY` 是否已配置且发布时真实 ping（建议查 Vercel 控制台 env + 抓一次发布后的网络请求确认）。

### B4. 内容可提取性（给 LLM 吃） —— ✅ 强
- 语义化 HTML、清晰 h1/h2、产品页 FAQ 区块、丰富 `llm.txt`、图片 alt 与图站地图 caption 齐全。
- 落地页正文已占满宽度（本轮打磨）、图片已收敛，首屏信息密度高——利于 AI 摘要与用户速读。

---

## C. 内容 / 关键词债务（已知，本次核实仍成立）

| 项 | 现状 | 级别 |
|---|---|---|
| 非英 meta description 未译（es 实测英文回退） | 标题已译、描述回退英文 | P1 |
| `projects.html` 硬编码 500+/50+ | 来自历史审计，待母语复核 | P1 |
| `red-1-karting-beijing` 描述仅 183 字符（薄） | 内容欠账 | P2 |
| 新闻标题/描述待母语复核（fr/es/de/ru/ar） | 已知欠账 | P1/P2 |

---

## D. 优先级行动清单（v1.10.24 更新）

| 优先级 | 动作 | 状态 |
|---|---|---|
| 🔴 HIGH | 3 个已删根级落地页登记 301 | ✅ 已修 `aa2a515`（映射见 A7） |
| 🟠 MED | 全站补默认 `og:image` | ✅ 已修 `eb3ed0b`（见 A8） |
| 🟠 MED | 落地页补 FAQ 区块 + FAQPage JSON-LD | ✅ 已修 `1c7443f`（见 A9） |
| 🟡 LOW–MED | `@id` 实体锚点 + NewsArticle `author` | ✅ 已修 `b11fa2b`（见 A6） |
| ⚪ **撤回** | ~~`llms.txt` 301 到 `llm.txt`~~ | ❌ **不该做**：`build.sh` 刻意保留双入口，见 B1 |
| ❌ **不加** | ~~`WebSite.SearchAction`~~ | 站点无搜索功能，声明即虚假，已加守卫阻止 |
| 🟡 LOW | sitemap `lastmod` 真实化 | ✅ 已修 `2d3e158`：量数据后发现 57/60 无真值可给，改为**只在有真实日期时输出**（见 A4） |
| ⚪ 手动 | Cloudflare 控制台开启 AI Crawl Control 放行（P1） | ⏳ robots 仅为礼貌信号，需边缘配置 |
| ⚪ 手动 | 确认 Vercel `INDEXNOW_KEY` 已配且发布时真 ping | ⏳ 仓库已接线，env 待核 |
| ⚪ 内容 | 推进 P1/P2 翻译与内容债务（见 C） | ⏳ 非英 meta description 回退英文等 |

### 已交付提交
| 提交 | 内容 |
|---|---|
| `aa2a515` | 3 个根级落地页 301 |
| `eb3ed0b` | 全站 `og:image` 兜底卡 |
| `1c7443f` | 落地页页面级 FAQ + FAQPage |
| `b11fa2b` | JSON-LD `@id` 锚点 + NewsArticle author |
| `2d3e158` | sitemap `lastmod` 只在有真实日期时输出 |

新增守卫：`tests_seo_og_image.py`(5) / `tests_seo_stadium_faq.py`(8) / `tests_seo_entity_ids.py`(10) /
重写 `tests_sitemap_lastmod.py`(14)，全部经变异探针验证非空转。相关分组回归 **112/112 绿**。

---

## 附录：实测证据
- 首页 en 200，hreflang×7，canonical=`/`，无 og:image（仅注释提及）。
- 产品页 `/products/rt820sl-t/` 200：canonical 正确，og:image 有，JSON-LD = Product+FAQPage+BreadcrumbList+Organization。
- es 产品页标题 `Alumbrado Vial RT820SL-T — 240W | SolarOne`，description 仍为英文。
- ar 产品页 `<html lang="ar" dir="rtl">`，标题阿语，og:image 有。
- 新闻 `/news/global-led-lighting-market-2034/` 200：NewsArticle JSON-LD（datePublished✅, author❌）。
- `/sports-lighting/`、`/football-stadium-lights/`、`/tennis-court-lighting/` → 404；`/products/sports-lighting/` → 301 `/products/`。
- sitemap：60 canonical URL，420 hreflang，含 image 扩展，lastmod=2026-10-07。
- robots.txt：16 个 AI crawler `Allow: /`，含 Sitemap/LLM-Txt/Feed 指令。
- llm.txt / llms.txt 均 200，md5 相同（`727ad4fafe7b52e7a1d814f61c292e18`）。
