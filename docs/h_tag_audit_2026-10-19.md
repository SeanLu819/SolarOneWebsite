# 全站 H 标签分级审计（2026-10-19，v1.10.32 线上实测）

> 数据来源：线上真实渲染页 curl 抓取（英文版，H 结构与语言无关）。
> 覆盖 14 个页面类型；`/product-overview/` 返回 404（见问题 6）。

## 一、总览

| # | 页面 | URL | H 标题数 | H1 唯一 | 跳级 | 结论 |
|---|------|-----|---------|--------|------|------|
| 1 | 首页 | `/` | 3 | ✓ | 无 | ✅ 良好 |
| 2 | 产品列表 | `/products/` | 7 | ✓ | **H1→H3** | ⚠️ 跳级 |
| 3 | 产品详情 | `/products/fl1m/` | 7 | ✓ | 无 | ✅ 良好（问题 4 已于 v1.10.34 修复） |
| 4 | 项目列表 | `/projects/` | 11 | ✓ | **H1→H3** | ⚠️ 跳级 + H1 文案 |
| 5 | 项目详情 | `/projects/football/` | 13 | ✓ | 无 | ✅ 良好 |
| 6 | 新闻列表 | `/news/` | 4 | ✓ | **H1→H3** | ⚠️ 跳级 |
| 7 | 新闻详情 | `/news/global-led-lighting-market-2034/` | 4 | ✓ | 无 | ✅ 良好 |
| 8 | 落地页 stadium-lighting | `/stadium-lighting/` | 17 | ✓ | 无 | ✅ 教科书级 |
| 9 | 落地页 football-stadium-lights | `/football-stadium-lights/` | 13 | ✓ | 无 | ✅ 教科书级 |
| 10 | 落地页 tennis-court-lighting | `/tennis-court-lighting/` | 13 | ✓ | 无 | ✅ 教科书级 |
| 11 | 关于我们 | `/about/` | 20 | ✓ | 无 | ✅ 良好（末尾混入隐私区块，见问题 5） |
| 12 | 联系我们 | `/contact/` | 6 | ✓ | **H1→H3** | ⚠️ 公司名用了 H3（问题 3 已于 v1.10.34 修复） |
| 13 | 隐私政策 | `/privacy/` | 8 | ✓ | 无 | ✅ 良好 |
| 14 | 服务条款 | `/terms/` | 8 | ✓ | 无 | ✅ 良好 |

**全站没有多 H1 问题**（每页恰好 1 个 H1）；H5/H6 全站未使用（层级浅，无碍）。

## 二、问题清单（按优先级）

### 问题 1（P1）：三个列表页 H1→H3 跳级 —— **待用户决策（A/B 方案）**

列表页的卡片/条目标题直接用了 H3，而它们的父级分组没有 H2，形成 H1→H3 断层：

- `/products/`：H1 "Our Products" → H3 ×6（M Series、RT410 Series、VSP series、FLOOD LIGHTING、HIGHBAY、Street Lighting）
- `/projects/`：H1 "Trusted Worldwide" → H3 ×10（项目名）
- `/news/`：H1 "Latest Updates" → H3 ×3（文章标题）

**对照**：三个落地页（stadium/football/tennis）之所以结构完美，正是因为它们有 H2 分组
（"Stadium Floodlights" → H3 系列；"Delivered Venue Projects" → H3 项目）。

**修复方向（二选一，供决策）**：
- 方案 A（贴近落地页模式）：在 H3 卡片区前补一个 H2 分组标题（如 "Product Series" / "Featured Projects" / "Latest Articles"）。
- 方案 B（语义升级）：列表页条目标题 H3 → H2（每个系列/项目本身即页面二级主题）。

### 问题 2（P1）：`/projects/` 的 H1 文案不具关键词且与 About 重复 —— **待用户定文案**

- `/projects/` H1 = "Trusted Worldwide"
- `/about/` H1 = "Trusted worldwide for a reason."

两个不同意图的页面共用近似 H1，且项目列表页 H1 不含任何关键词（"projects"/"lighting"）。
建议 `/projects/` H1 改为含关键词的文案（如 "Lighting Projects" / "Our Lighting Projects"）——具体文案你定。

### 问题 3（P2）：`/contact/` 公司名用了 H3 —— ✅ **已修复（v1.10.34）**

结构：H1 "Contact Us" → **H3** 公司名 → H2 "Agents & Distributors" → H3 ×3 代理。
公司名是 H1 下的直接子级，应为 H2（或降为非标题文本）。

修复：H3 → H2；inline style 由 `margin-bottom: 24px` 改为 `margin: 1em 0 24px`
（旧 H3 靠 UA 默认 `margin-block-start: 1em`，H2 的 UA 默认是 0.83em，显式写
1em 保持像素级一致）。守卫 `tests_heading_semantics.py::ContactHeadingSemanticsTests`。

### 问题 4（P3）：产品详情页 "Request a Sample" 用 H3 —— ✅ **已修复（v1.10.34）**

`/products/fl1m/`：… → H2 "ORDERING INFORMATION:" → H3 "Request a Sample" → H2 "Product FAQ"。
"Request a Sample" 是表单/CTA 而非文档章节，用标题标签语义不当（可保留视觉样式、去掉 h3 标签，或改 p/strong）。影响小，可选。

修复：`<h3 class="detail-request-sample-title">` → `<p class="detail-request-sample-title">`
（样式全在 class 上，视觉零变化）。守卫 `tests_heading_semantics.py::ProductDetailHeadingSemanticsTests`。

### 问题 5（P3）：About 页末尾混入隐私政策区块 —— **待用户决策**

`/about/` 末尾出现 H2 "Privacy Policy" + H3 "Cookie Usage" / "Data We Collect" / "Your Rights"。
About 页不应承载隐私详情（已有独立 `/privacy/` 页），疑为复用组件带入。内容组织问题，可选清理。

### 问题 6（P2）：~~`product_overview.html` 模板存在但无路由~~ —— **结论已修正（v1.10.34）**

初版报告称「`templates/product_overview.html` 存在，但 `pages/urls.py` 无对应路由 → 404」，据此怀疑是死模板。**该结论错误**：`views_products.product_detail` 按 `Product.page_layout` 双模板派发——

* `detail` → `product_detail.html`（全规格单品页）
* `overview` → `product_overview.html`（系列着陆页）

seed 中 3 个产品用 `overview` 布局（m-series / rgb-rgbw / accessory），页面经 `/products/<slug>/` 正常渲染（200）。教训：搜 "overview" 只查 urls.py 会漏掉动态模板名派发。**该模板在用，不可删。**

## 三、各页面完整 H 结构

### 1. 首页 `/`
```
H1  The Next Generation Lighting Systems For Every Area
H2  Our Products
H2  Trusted Worldwide
```

### 2. 产品列表 `/products/`
```
H1  Our Products
H3  M Series                    ← 跳级（H1→H3）
H3  RT410 Series
H3  VSP series
H3  FLOOD LIGHTING
H3  HIGHBAY
H3  Street Lighting
```

### 3. 产品详情 `/products/fl1m/`
```
H1  FL1M 80W
H2  Beam Angle Type:
H2  Dimensions:
H2  ENERGY AND PERFORMANCE DATA:
H2  ORDERING INFORMATION:
H3  Request a Sample            ← CTA 用了标题（问题 4）
H2  Product FAQ
```

### 4. 项目列表 `/projects/`
```
H1  Trusted Worldwide           ← 文案问题（问题 2）
H3  Bohemia Manor High School   ← 跳级（H1→H3）
H3  Yuanshen Sports Centre Stadium
H3  Carroll County Sports Complex
H3  Morgan State University Tennis Courts
H3  Nanshan Ski Village
H3  Andre Vacheresse Stadium
H3  Narbonne Arena
H3  Beijing Capital International Airport
H3  Beijing International Tennis Center
H3  National Snow and Ice Research Center
```

### 5. 项目详情 `/projects/football/`
```
H1  Football Field Lighting
H2  Football Floodlights
H3  M Series
H3  VSP series
H2  Choosing the Right Output
H2  Delivered Football Venue Projects
H3  Bohemia Manor High School
H3  Yuanshen Sports Centre Stadium
H3  Perryville High School
H3  McIntosh County Academy
H3  Garrison Forest School
H2  Football Lighting FAQ
H2  Other Lighting Categories
```

### 6. 新闻列表 `/news/`
```
H1  Latest Updates
H3  Global LED Market to Triple by 2034     ← 跳级（H1→H3）
H3  Outdoor and Tech Light Expo 2026, Hong Kong
H3  SolarOne FL6M-480W Lights Binhai Airport
```

### 7. 新闻详情 `/news/global-led-lighting-market-2034/`
```
H1  Global LED Market to Triple by 2034
H2  More news
H3  Outdoor and Tech Light Expo 2026, Hong Kong
H3  SolarOne FL6M-480W Lights Binhai Airport
```

### 8-10. 落地页（三个同构，以 stadium-lighting 为例）
```
H1  LED Stadium Lighting
H2  Stadium Floodlights
H3  M Series
H3  VSP series
H2  Choosing the Right Output
H2  Delivered Venue Projects
H3  Bohemia Manor High School
H3  …（项目名 ×7）
H2  Stadium Lighting FAQ
H2  Other Lighting Categories
```

### 11. 关于我们 `/about/`
```
H1  Trusted worldwide for a reason.
H2  Technical Advantages
H3  Clearest Visual Comfort
H3  Powerful and Efficient
H2  CPG-Optics System
H3  COB Light Engine
H3  Proprietary Reflector
H3  Glass Fresnel Lens
H2  Lighting Projects Made Simple
H3  Consultation
H3  Custom Fabrication
H3  Manufacture
H3  Installation
H3  Maintenance
H3  Financing Solutions
H2  Privacy Policy               ← 混入区块（问题 5）
H3  Cookie Usage
H3  Data We Collect
H3  Your Rights
H2  Ready to Light Up Your Project?
```

### 12. 联系我们 `/contact/`
```
H1  Contact Us
H3  BEIJING SOLARONE ENERGY TECHNOLOGY CO., LTD   ← 应为 H2（问题 3）
H2  Agents & Distributors
H3  USA Agent
H3  Germany Agent
H3  France Agent
```

### 13. 隐私政策 `/privacy/`
```
H1  Privacy Policy
H2  1. Data controller
H2  2. What we collect
H2  3. How we use your data
H2  4. Cookies
H2  5. Your rights
H2  6. International transfers
H2  7. Contact
```

### 14. 服务条款 `/terms/`
```
H1  Terms of Service
H2  1. Acceptance of terms
H2  2. Intellectual property
H2  3. Product information
H2  4. Quotations and orders
H2  5. Limitation of liability
H2  6. Governing law
H2  7. Contact
```
