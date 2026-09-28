# AI 搜索 / 搜索引擎 / 引流审计（2026-09-28）

审计对象：SolarOne 外贸站（Django + Vercel，6 语种）
审计方式：实测渲染（`django.test.Client`）+ 逐模板静态检查 + seed 数据核对
基线：24 产品 / 22 项目 / **1 篇新闻** / 6 语种 URL（英文无前缀）

优先级：**P0 = 现在就在漏流量（含真 bug）**，P1 = 一个月内，P2 = 有余力。

---

## P0 — 必修（含 3 个已确认真 bug）

### P0-1 🔴 Organization JSON-LD 全站非法（实测 8/8 页报错）

- 根因：`templates/base.html:582-586`，`sameAs` 数组每条都写死尾逗号：
  ```
  {% if config.social_facebook %}"…",{% endif %}
  {% if config.social_instagram %}"…",{% endif %}
  {% if config.social_youtube %}"…",{% endif %}
  {% if config.social_linkedin %}"…"{% endif %}   ← seed 里为空
  ```
  `social_linkedin` 在 `seed_data.json` 中为空串 → 数组以 `,` 结尾 → JSON 尾逗号 → 解析失败。
- 实测：`/`、`/products/`、`/projects/`、`/news/`、`/about/`、`/contact/`、`/products/fl6m/` 全部
  `Expecting value: line 21 column 3`。
- 影响：全站唯一承载品牌身份的 schema **100% 失效**——Google 知识面板、AI 品牌实体识别、
  `sameAs` 社交实体关联全部拿不到。这是当前投入产出比最高的一个修复。
- 修法：模板改用 `{% for %}...{% if not forloop.last %},{% endif %}`，数据源改为
  SiteConfig 的 `social_same_as`（Python 侧拼 list，空值自然过滤），并在尾部补 LinkedIn 真实 URL。
- **✅ 已于 v1.8.2 修复**：`SiteConfig.social_same_as`（`pages/models.py`）在 Python 侧过滤空值，
  模板只做 join；LinkedIn 保持留空（不编造 URL），靠过滤而非补占位符解决。
  守卫测试 `pages.tests.JsonLdValidityTests` 覆盖 11 个路径 × 多语种。

### P0-2 🔴 Organization.logo 是相对路径

- 根因：`templates/base.html:573` 输出 `{{ config.logo_url }}` = `/static/images/logo.webp`。
- 影响：schema.org 要求绝对 URL → logo 判无效 → Organization 富媒体不合格。
- 修法：`"logo": "{{ canonical_origin }}{{ config.logo_url }}"`。
- **✅ 已于 v1.8.2 修复**：输出 `https://www.solaronelighting.com/static/images/logo.webp`。

### P0-3 🟠 Organization 缺「实体三要素」

`base.html:569-588` 只有 name/url/logo/description/contactPoint/sameAs。缺：

| 缺字段 | 为什么关键 |
|---|---|
| `address` (PostalAddress) | 「Beijing, China」只在 `contact_address` 文本里，机器读不到 → 地域实体关联丢失 |
| `foundingDate: 2007` | 「since 2007」是全站核心信任状，AI 无法引用 |
| `areaServed` | 50+ 国家的业务覆盖无法表达 |
| `knowsAbout` | 体育照明专长（llm.txt 的核心卖点）无法进入知识图谱 |

- **✅ 已于 v1.8.2 修复**：四项全部补齐，取值来自 `SiteConfig` 既有字段
  （`contact_address` 拆分为 locality/country；`foundingDate` = `FOUNDING_YEAR` = 2007；
  `areaServed` = `{"@type":"Place","name":"Worldwide"}`；`knowsAbout` = `KNOWS_ABOUT` 关键词）。
  有意**省略 `streetAddress`**：`contact_address` 只有 "Beijing, China"，无门牌号可填，不编造。

### P0-4 🟠 WebSite SearchAction 指向不存在的搜索页

- 根因：`templates/home.html:137` target = `/en/products/?q={search_term_string}`。
  ① 英文**无 `/en/` 前缀**；② 全站没有搜索视图（`pages/urls.py` 无 search 路由，`?q=` 无处理）。
- 影响：Google Search Console 报「网站链接搜索框无效」，且是无效结构化数据。
- 修法：二选一 —— (a) 删掉 `potentialAction`（10 秒，零风险）；(b) 真做站内搜索（顺带提升站内发现）。
- **✅ 已于 v1.8.2 修复 —— 采用 (a)**：整个 `potentialAction` 块已删除，保留 `@type`/`name`/`url`。
  守卫测试 `test_home_website_block_has_no_search_action` 锁住契约：将来若要重加
  SearchAction，必须先真的做搜索路由与视图，否则测试会红。

### P0-5 🟡 Product JSON-LD 的 url 用 request host

- 根因：`templates/product_detail.html:900`、`product_overview.html:502` 用
  `{{ request.build_absolute_uri }}`；`project_detail.html:456` 用 `canonical_origin` —— 两处不一致。
- 影响：本地/preview 部署 schema 里出现 `http://localhost/...` 或 `*.vercel.app`，canonical 冲突。
- 修法：统一为 `{{ canonical_origin }}{% url 'product_detail' product.slug %}`。
- **✅ 已于 v1.8.2 修复**：两个 Product 模板统一用 canonical 写法；同时补上了 `news_detail.html`
  NewsArticle 缺失的 `url`（同一 canonical 写法）。

### P0-6 🟠 JSON-LD 字符串未转义 / `additionalProperty` 仍是模板拼数组（QA 二轮发现）

同源于 P0-1 的「模板拼 JSON」模式，v1.8.2 一并修掉：

| # | 位置 | 问题 | 状态 |
|---|---|---|---|
| a | `products.html:106,108-109`、`projects.html:122,124-125` | `name`/`headline` 未 `escapejs`：产品名含 `\` → `Invalid \escape` 整块非法；含 `"` → 被 HTML autoescape 转成 `&quot;` 造成值污染 | ✅ 已修（全部补 `\|escapejs`） |
| b | `home.html:135` | WebSite `name` 未 escapejs，与 `base.html:571` 不一致 | ✅ 已修 |
| c | `product_detail.html`、`product_overview.html` 的 `additionalProperty` | 仍是模板拼数组，靠末尾固定的 `Category` 兜底才没尾逗号 | ✅ 已修：改为 `Product.jsonld_properties`（`pages/utils.jsonld_property_pairs`，Python 侧过滤空值），DB 模型与 seed `_DictProduct` 两条路径均已实现 |
| d | 顺手补齐的同款漏网点 | `base.html` 的 `contactPoint.email`/`phone`（`contact_phone_1` 是可自由填写的 CharField）；`project_detail.html` 的 `publisher.name` | ✅ 已修（当前取值转义后字节不变，纯粹加固） |

已知**接受不修**的残留（非缺陷，记录以免后人重复排查）：各 JSON-LD 里的 URL/路径片段
（`logo_url`、`image_url`、`banner_image_url`、`request.path`、`section_url`、`leaf_url`、
`{% url %}` 产物、`sameAs` 成员）保持原样不套 `escapejs` —— slug 受 `[\w-]+` 约束、
路径经 `static()` 归一化，无法注入 `\` 或 `"`；且 `escapejs` 会把 `=` 转成 `\u003D`，
白白牺牲可读性却换不到安全性。`breadcrumb_jsonld.html` 的 `leaf_name` 由**调用方**负责
转义（4 个调用点均已带 `|escapejs`，见该 include 头部注释）。

---

## P1 — AI 搜索（GEO）专项

| # | 项 | 现状 | 动作 | 性价比 |
|---|---|---|---|---|
| G1 | **Cloudflare AI Crawl Control** | DNS 走 Cloudflare；2025-07 起 CF 对新域名**默认拦截 AI 爬虫** | 去 CF dashboard → Bots / AI Crawl Control，确认 GPTBot、OAI-SearchBot、PerplexityBot、ClaudeBot、Google-Extended 为 Allow | 🔴 **最高**——不查的话前面所有 GEO 工作可能全废 |
| G2 | `/llms.txt` 别名 | 只有 `/llm.txt`；主流约定名是 `llms.txt`，部分 AI 爬虫只认这个 | `build.sh` 5.5 步同时 `cp llm.txt public/llms.txt` | 零成本 |
| G3 | **FAQPage schema** | 全站 0 个 | 产品页加 4–6 条 FAQ（MOQ / 交期 / 质保 / DIALux 方案 / 认证 / 无频闪）+ FAQPage JSON-LD | 🔴 高——AI 问答引擎最偏好的结构化类型 |
| G4 | 每页 `inLanguage` | 无 | 所有 JSON-LD 补 `"inLanguage": "{{ LANGUAGE_CODE }}"` | 低 |
| G5 | `og:locale:alternate` | 只有 `og:locale` | 补 5 个语种的 alternate | 低 |
| G6 | NewsArticle 字段 | 缺 `dateModified` / `author` / `articleSection` / `url`；`publisher` 无 logo | 补齐（`news_detail.html:16-26`） | 低 |
| G7 | 项目页语义 | 用 `Article` | 补 `about`（场地类型）/ `mentions`（国家）/ `datePublished` | 中 |
| G8 | 显式放行 AI 爬虫 | robots.txt 只写 `User-agent: *` | 显式列 GPTBot / ClaudeBot / PerplexityBot / Google-Extended 并 Allow | 低（但防 CF 层误判） |

---

## P1 — 内容与引流

| # | 项 | 现状 | 动作 |
|---|---|---|---|
| C1 | 🔴 **内容量**：news 仅 1 篇 | 1 篇（2026-09-25） | 外贸 B2B 长尾靠持续产出；建议每月 2–4 篇，主题见下 |
| C2 | 无 RSS / Atom feed | `pages/urls.py` 无 feed 路由 | 加 `/news/feed.xml`（约 15 行视图 + 1 条 url），AI 聚合器与新闻源入口 |
| C3 | 无「照度标准对照表」页 | 无 | 足球/网球/篮球/冰球各级别 lux 要求对照表 —— 长尾词密度最高、AI 最爱引用的内容形态 |
| C4 | 无视频 | 无 VideoObject | 球场实拍视频（YouTube 已有频道）+ 站内 VideoObject schema |
| C5 | sitemap 静态页无 `lastmod` | `views_other.py:191` 只给产品/项目传 lastmod | 首页/关于/联系等固定页也补（用 seed mtime） |
| C6 | GA4 未配置 | `GA4_MEASUREMENT_ID` env 为空 → 全站不渲染 gtag | Vercel 配 env。**没有数据就无法迭代引流** |
| C7 | GSC 未验证 | `GSC_VERIFICATION_CODE` 为空 | 配 env + 提交 sitemap，是 P0-4 报错的观察入口 |
| C8 | 图片 CLS | 全站 `<img>` 均无 `width`/`height`（首页 6、产品 9、项目 11） | 补尺寸属性；`VSP9M-02.webp` 860KB 需压缩 |
| C9 | alt 缺失 | 首页 hero 3 图、news 列表 1 图无 alt | 补描述性 alt（Google 图片流量入口） |
| C10 | 站外实体 | `social_linkedin` 为空 | 补 LinkedIn 公司页 URL（同时修 P0-1 的实体关联） |

**建议内容主题**（体育照明长尾）：
- `LED sports lighting lux requirements by sport`（对照表）
- `FIFA / UEFA / IAAF lighting class explained`
- `Flicker-free lighting for super slow-motion broadcast`
- `High mast retrofit: ROI and payback calculation`
- `DIALux photometric study: what you receive in 48 hours`
- `Glare control (GR / UGR) for stadium lighting`

---

## P2 — 锦上添花

- `speakable` schema（新闻页）
- `Service` schema（体育照明设计 + 配光方案服务）
- `Product.offers`（B2B 可给 `priceSpecification` 区间，换取 Product 富媒体）
- 404 页加「热门产品 + 返回首页」（降低跳出）
- Bing Places / Google Business Profile 建档
- 行业目录外链：照明展会、体育场馆协会、B2B 平台

---

## 已具备的强项（保持，勿动）

- canonical 全站固定 `CANONICAL_ORIGIN`（不依赖 request host）
- hreflang 6 语种 + `x-default`（HTML 与 sitemap `xhtml:link` 双向一致）
- sitemap 含 Google **image sitemap** 扩展（`<image:image>` + title/caption）
- JSON-LD：Organization / WebSite / BreadcrumbList / Product / ItemList / NewsArticle / Article
- OG + twitter card 完整，OG 为唯一真源（不重复造 twitter:title）
- 全站 WebP、首屏关键 CSS 内联、preconnect/preload
- `/llm.txt` 已通过 `build.sh` 上线 + robots.txt 声明

---

## 验证方法

```bash
# JSON-LD 合法性（P0-1 回归用）
python - <<'PY'
import os,django,json,re
os.environ.setdefault('DJANGO_SETTINGS_MODULE','solarone.settings'); django.setup()
from django.test import Client
c=Client()
for p in ['/','/products/','/projects/','/news/','/about/','/contact/','/products/fl6m/']:
    h=c.get(p,HTTP_HOST='localhost').content.decode()
    for b in re.findall(r'type="application/ld\+json"[^>]*>(.*?)</script>',h,re.S):
        try: json.loads(b)
        except Exception as e: print('❌',p,e)
PY
```
