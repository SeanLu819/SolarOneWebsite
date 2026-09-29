---
doc_id: seo-growth-plan
title: SolarOne 增长方案 — 测速 / 关键词 / 内容 / 数据闭环（含测试方案与里程碑）
version: 1.0.0
status: approved（B0/B1 已完成；B3 进行中：per-page SEO 字段 + 品类词映射 + title/description 公式 + 唯一化守卫已落地；P2 图片外置已出方案并暂缓）
last_updated: 2026-09-28
owner: Sean Lu
related:
  - path: docs/seo-optimization-handbook.md
    role: 上一版基线手册 v1.2.0（M1 重复内容 301 / M2 GA4 通道已完成，本方案从 M3 接续）
  - path: docs/ai-search-growth-audit.md
    role: AI 搜索增长审计（GEO，对应本方案 G 大类）
  - path: docs/image-seo-naming-spec.md
    role: 图片 SEO 命名规范（对应 C6）
  - path: llm.txt
    role: 对外内容摘要，内容变更须同步（G2）
---

# SolarOne 增长方案 v1.0

> **定位**：站点已成型（技术地基达标），本方案解决「**没有关键词资产 + 没有效果数据**」两个瓶颈，
> 并把速度、内容、国际化、转化、运维、合规一并纳入。**先分大类 → 大类下细分 → 按紧急/收益/风险/工作量排序 → 分批上线 → 每层配测试。**
> **执行原则**：每批独立 commit、Preview 验证后再进 Production、可回滚；所有代码改动配守卫测试。

---

## 0. 已确认的决策（用户 2026-09-28 拍板）

| 项 | 决定 | 影响 |
|---|---|---|
| 分析工具状态 | 用户不确定 → **已线上实测确认：GA4 与 GSC 均未配置**（详见 §1） | D1 成为第一优先 |
| 关键词数据源 | **GSC + 免费工具**（Keyword Planner / Bing Webmaster） | 不采购付费 API；volume/KD 一律工具导出校准，**方案内不编造数字** |
| 图片多尺寸变体 | **后置，需人工配合**（部分原图分辨率不足，降档需人工判断） | A6 从关键路径移出，排到 B8；性能先靠 CSS/字体/懒加载拿收益 |
| 五语翻译范围 | **全 24 个产品页** | E1 工作量放大到 L，排到 B5（英文定稿后） |

---

## 1. 线上基线实测（2026-09-28，`https://www.solaronelighting.com`）

| 指标 | 实测值 | 判定 | 目标 |
|---|---|---|---|
| 首页状态码 / HTML 体积 | 200 / **40.2 KB** | 正常（内联 critical CSS + 动态字体块占大头） | — |
| TTFB（3 次） | **0.69 / 0.73 / 0.70 s** | 🟡 偏高（serverless 动态渲染，HTML 无边缘缓存） | < 0.5 s |
| `base.css` 传输（br/gzip） | **19.6 KB**（源 71 KB） | 🟡 可接受但仍**渲染阻塞** | 异步化 |
| `fonts.css` 传输 | **1.56 KB**（源 17 KB，52 个 woff2 声明） | 🟡 声明多 → 字体文件按需拉取，需子集化 | 精简至 ≤3 字重/2 子集 |
| 首图 `hero-main-1.webp` | **76.7 KB** | ✅ 合理 | — |
| sitemap `<loc>` 条目 | **53** | ✅ 含 `<image:image>` | 与可索引页保持一致（F4） |
| GA4 `G-XXXXXXX` | **`G-81MQ1C1L5H` 已生效**（sales@ 业务账号；原个人账号 `G-X2GDWKEQIL` 已删除） | ✅ 线上已验证唯一 ID | 保持 |
| `google-site-verification` | **未配置 meta** | ⬜ GSC 已通过 GA4 自动验证，meta 作为备份可选 | 可选补 HTML 标记 |
| 转化事件 `gtag('event')` | **0 个**（源码仅 `base.html:43` 定义 gtag） | 🔴 无法衡量任何 ROI | ≥4 个事件 |
| 308 归一（apex → www） | ✅ 0.58 s | 保持 | — |

> 注：首页 HTML 里的 `googletagmanager.com` 只是 `base.html:14` 的**无条件 preconnect**，
> 不代表 GA4 已生效 —— 判定依据是**没有 `G-` 开头的 ID**。

---

## 2. 工作大类总览

| 编号 | 大类 | 目标 | 现状 | 来源 |
|---|---|---|---|---|
| **A** | 网站速度测试与优化 | 移动端 LCP<2.5s / CLS<0.1 / INP<200ms | TTFB 0.7s、CSS 阻塞、字体 1.3MB | 用户指定 |
| **B** | 关键词研究与 On-page SEO | 24 页一页一词，消灭内耗 | title 纯型号、description 雷同 | 用户指定 |
| **C** | 内容优化 | 唯一化 + 参数化 + EEAT | 2 个产品描述 9 字符、specs 大量空 | 用户指定 |
| **D** | 数据分析与转化追踪 | 有数据、能归因 | GA4/GSC 未配、0 事件 | **补充** |
| **E** | 国际化 SEO（五语 + RTL） | 各语言独立排名 | 24 产品仅 5 个有译文 | **补充** |
| **F** | 技术 SEO 与索引健康 | 抓取/索引/规范化无漏 | 地基好，需审计闭环 | **补充** |
| **G** | GEO / AI 可见性 | AI 答案引擎引用 | llm.txt/RSS/JSON-LD 已建，缺维护机制 | **补充** |
| **H** | 转化路径与 UX | 流量 → 询盘转化 | 表单/CTA 未埋点、未优化 | **补充** |
| **I** | 权威与外链 | 域名权重 | 从未盘点 | **补充** |
| **J** | 运维与可靠性 | 线索不丢、站点可用 | 🔴 表单存 /tmp DB 会随部署清空 | **补充** |
| **K** | 合规与无障碍 | 无法律风险、可访问 | 🔴 页脚隐私/条款是 `<span>` 非链接 | **补充** |

---

## 3. 优先级评分定义

| 维度 | 取值 | 含义 |
|---|---|---|
| **紧急 E** | H / M / L | 是否阻塞后续工作或正在持续损失 |
| **收益 R** | H / M / L | 对「展现 → 点击 → 询盘」的直接贡献 |
| **风险 S** | L / M / H | 回归风险、线上事故风险（H = 需 Preview 充分验证） |
| **工作量 W** | S(<0.5d) / M(0.5–2d) / L(>2d) | 含测试 |

**排序规则**：先做 `S=L 且 R=H 且 W=S/M` 的**快赢**；`E=H` 项无条件提前；`S=H` 项必须 Preview 验证。

---

## 4. 细分任务清单

### A — 网站速度测试与优化

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| A1 | CWV 基线测量脚本 `scripts/perf_baseline.py`（PSI API，6 类页 × mobile/desktop → JSON） | 新增 | H | H | L | M | PSI key | B0 | 输出 `docs/perf_baseline_2026-09-28.json` |
| A2 | `base.css` 异步化：`preload`+`onload` swap，`<noscript>` 回退 | `base.html:104` | M | H | M | S | A4 | B2 | 无 FOUC；LCP 不退化 |
| A3 | 关键 CSS 扩面（首屏 nav/hero/footer 已在 `base.html:63-103`，补首屏卡片） | `base.html:63-103` | M | M | M | M | — | B2 | 快照对比无样式缺失 |
| A4 | 字体子集化：保留 latin/latin-ext 400/500/600，CJK 交给系统字体（`--ff-body` 已含 PingFang/雅黑） | `static/css/fonts.css`（17KB / 52 woff2）、`static/fonts` 1.3MB | M | M | L | M | — | B2 | 字体传输 < 400KB |
| A5 | hero slide 2..n 改 `loading="lazy"`（首图保留 `fetchpriority=high`） | `home.html:36` | L | M | L | S | — | B2 | 首屏请求数下降 |
| A6 | 内页 `srcset` 三档变体（640/1024/1600 WebP） | 产品/项目页 | L | H | L | **L** | 人工制图 | **B8** | 移动端 LCP 降 1s+ |
| A7 | 产品页 banner 加 `<link rel="preload" as="image">` | `product_detail.html:67` 已有 fetchpriority | L | M | L | S | — | B2 | LCP 改善 |
| A8 | TTFB / HTML 缓存策略调研（边缘缓存 or `Cache-Control: s-maxage`） | 实测 0.70s | M | M | M | M | — | B2 | 方案文档 + 试验 |
| A9 | 第三方脚本治理 | GA4 已 async + preconnect ✅ | L | L | L | S | — | — | 保持 |
| A10 | lazy YouTube 嵌入（若 C9 采纳） | 交叉项 | L | M | L | S | C9 | B7 | 无首屏阻塞 |

### B — 关键词研究与 On-page SEO（核心）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| B1 | 建关键词总表 `docs/keyword-inventory.csv`（词/语言/意图/层级/目标URL/展现/点击/校准日期） | 新增 | H | H | L | M | D2 | B3 | 表建立并周度回填 |
| B2 | **新增 per-page SEO 字段** `Product.seo_title/seo_description`（Project 同）+ 接入 `translations` 第三套机制 | `models.py:481-482`（现仅 SiteConfig 全局字段） | **H** | **H** | M | M | — | B3 | 迁移 + seed 同步 + 守卫 |
| B3 | `CATEGORY_KEYWORD` Python 常量映射 + slug 级覆盖表（**禁模板拼**；品类词走 translations，`{% trans %}` 只吃字面量） | 新增于 `pages/views/views_products.py` | H | H | L | M | B2 | B3 | 单元测试覆盖 24 slug |
| B4 | title 公式：`{品类词} {型号} — {关键参数} \| SolarOne` | `product_detail.html:6`、`product_overview.html:6`、`project_detail.html:6` | H | H | L | M | B2/B3 | B3 | 24 页 title 含品类词 |
| B5 | description 公式 + **唯一化**（50–160 字符，24 页互不相同） | 同上 + `seed_data.json` | H | H | L | M | B2 | B3/B4 | 唯一性守卫通过 |
| B6 | 关键词内耗审计（FL1M–FL16M 六页描述逐字雷同 → 按功率/场景差异化） | `seed_data.json` | M | H | L | M | B5 | B4 | 六页描述互异 |
| B7 | H1/H2 结构审计（每页唯一 H1，含品类词） | 全模板 | M | M | L | S | — | B1 | 审计报告 |
| B8 | **各语言本地化词表**（禁止直译：fr `projecteur LED stade / éclairage sportif`；de `LED Stadionbeleuchtung / Flutlicht`；es `iluminación LED para estadios / proyectores deportivos`；ru `светодиодное освещение стадионов`；ar `إضاءة ملاعب LED`） | — | H | H | L | M | B1 | B5 | 5 语种词表 |
| B9 | slug 评估 | `fl1m` 等无品类词 | L | M | **H**（改 URL 丢索引） | L | — | 决策 | **建议不改 URL**，靠 title 补词 |
| B10 | 内链锚文本用品类词（产品 ↔ 项目 ↔ 资源三角） | 全站 | M | M | L | M | C4 | B4 | 内链覆盖率提升 |

### C — 内容优化

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| C1 | 24 产品描述重写（150–250 字符唯一；**`rt590fl-s`/`rt390fl` 仅 9 字符，紧急**） | `seed_data.json` | **H** | H | L | M | — | B4 | 最短 ≥150 字符 |
| C2 | `specs` / `energy_data` 补齐（功率/光效/光通量/光束角/防护/认证）→ 自动喂 `additionalProperty` JSON-LD | `pages/utils.py: JSONLD_PROPERTY_FIELDS` | M | H | L | M | — | B4 | 每产品 ≥5 项参数 |
| C3 | 项目页实测数据结构化为可抓取表格（lux / 均匀度 / 场馆类型 / 国家） | `llm.txt:36-54` 已有 10 条素材 | M | H | L | M | — | B4 | 22 项含数据表 |
| C4 | 资源中心首批 4 篇（stadium lux 指南 / HID 改造测算 / DIALux 设计服务 / 防眩光方案）覆盖 L3 词 | News 现仅 1 篇 | M | H | L | L | B1 | B4 | 上线 + 内链 |
| C5 | News 月度更新节奏 + RSS 已建（`news/feed.xml` 已 200） | — | L | M | L | S | C4 | 持续 | 每月 ≥1 篇 |
| C6 | 图片 alt / 命名审计（按 `docs/image-seo-naming-spec.md`） | `static/images`、`media/` | L | M | L | M | — | B4 | 审计 + 修复清单 |
| C7 | FAQ 内容扩展（现 6 条常量；按品类/场景扩，🔴 **禁插值用户输入**，`|safe` 无转义） | `views_products.py: PRODUCT_FAQ` | L | M | M | M | — | B7 | 守卫断言无 `</script>` |
| C8 | EEAT 信任信号：认证展示（`cert_image` 字段已有）、48h photometric 承诺、案例数 | 全站 | M | M | L | M | — | B4 | 首页 + 产品页可见 |
| C9 | 项目视频 lazy 嵌入（YouTube，提升停留时长） | 交叉 A10 | L | M | M | M | — | B7 | LCP 不退化 |

### D — 数据分析与转化追踪（补充大类，第一优先）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| D1 | Vercel 配 `GA4_MEASUREMENT_ID` + `GSC_VERIFICATION_CODE` | `settings.py:86-89`；**实测未配** | **H** | **H** | L | S | 用户操作 | B0 | 线上出现 `G-` 与 verification meta |
| D2 | GSC 验证 + 提交 sitemap（53 条）+ 国际定向检查（6 语） | — | H | H | L | S | D1 | B0 | GSC 收录开始 |
| D3 | **4 个转化事件**：`generate_lead`（表单成功）/ `contact_click`（WA·mailto·tel）/ `pdf_download` / `quote_view`；**gtag 未定义时安全降级** | `views_contact.py:93/116/128` 成功分支；`base.html:43` | **H** | **H** | L | M | D1 | B0 | GA4 实时报告可见 |
| D4 | GA4 **Consent Mode v2** 与现有 cookie banner 联动（GDPR；欧盟流量否则数据缺失） | `base.html:520-564` | M | M | M | M | D1 | B0 | 未同意前不写 cookie |
| D5 | KPI 看板定义：询盘数 / 来源落地页 / 国家 / 词 | — | M | H | L | S | D3 | B0 | 看板可用 |
| D6 | 周度 GSC 关键词导出 → 回填 `keyword-inventory.csv` | — | M | H | L | S | B1 | 持续 | 每周一次 |

### E — 国际化 SEO（补充）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| E1 | **24 产品页五语 title/desc 全量翻译**（用户已定） | seed `translations`（现仅 5 个产品有） | H | H | L | **L** | B5 英文定稿 | B5 | 24×5 无空串回退 |
| E2 | 五语本地化词表落地（与 B8 同一份） | — | H | H | L | M | B8 | B5 | 各语言 title 含本地词 |
| E3 | hreflang 自引用 + x-default 复核 | `templatetags/seo_tags.py:27-49` ✅ | L | M | L | S | — | 保持 | 守卫已覆盖 |
| E4 | 🔴 **RTL 隔离专项**（未覆盖：规格表数值、面包屑、导航下拉、footer 联络信息） | `base.css` 已有 `[dir="rtl"] bdi` | M | M | M | M | — | B5 | RTL 截图验收 |
| E5 | GSC 国际定向报告：各语言索引状态 | — | M | M | L | S | D2 | B5 | 报告 + 修复 |

### F — 技术 SEO 与索引健康（补充）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| F1 | canonical 全站审计（多语种 / trailing slash / 查询参数） | `base.html:21` | M | M | L | M | — | B1 | 审计报告 |
| F2 | 重复内容审计（`/products/series/` 已 301 ✅；FL 系列同质；筛选参数 `?category=`） | 手册 M1；`news.html` chips 用 `?category=` | M | M | L | M | — | B1 | 参数页 canonical/unique |
| F3 | 404 / 软 404 审计（未知 product slug 已真 404 ✅；复核 project/news） | `ProductPageLayoutSplitTests` | M | M | L | S | — | B1 | 全部真 404 |
| F4 | sitemap 一致性（53 条 ↔ 实际可索引页；`image:image` 全覆盖） | `views_other.py:94` 起 | M | M | L | M | — | B1 | 条数一致 |
| F5 | robots / AI 抓取复核（已上线 ✅：`/robots.txt` AI 块、`/llm.txt`、`/llms.txt`、`/news/feed.xml`） | — | L | M | L | S | — | 保持 | 季度复核 |
| F6 | 抓取预算：GSC 抓取统计 + Googlebot 频次监控 | — | L | M | L | S | D2 | B1 | 月度检查 |
| F7 | CSP 与 GA4 共存验证（上线后控制台无 CSP 报错） | `settings.py` CSP | M | M | L | S | D1 | B0 | 控制台 0 报错 |
| F8 | PDF / media 索引策略（项目页 `pdf_url` 是否进 sitemap） | seed `pdf_url` | L | M | L | S | — | B1 | 决策 + 落地 |

### G — GEO / AI 可见性（补充）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| G1 | JSON-LD 扩展：`Service`（DIALux 设计）、`FAQPage` 已 ✅、`Product` 参数随 C2 自动增强 | `views_products.py` | M | M | L | M | C2 | B7 | Rich Results Test 通过 |
| G2 | `llm.txt` 维护机制（🔴 文件头仍写 v1.8.1，实际 1.8.3；内容变更须同步） | `llm.txt:5` | M | M | L | S | — | B3 | 版本号同步 |
| G3 | AI 引用监测：每月用 GPT/Perplexity 问 10 个目标问题，记录是否被引用 | — | M | M | L | S | — | 持续 | 监测表 |
| G4 | JSON-LD 守卫保持（`JsonLdValidityTests` 10 用例） | `pages/tests.py` | H | H | L | S | — | 每次提交 | 全绿 |

### H — 转化路径与 UX（补充）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| H1 | 询盘表单摩擦优化（字段数、移动端键盘、错误提示） | `templates/contact.html` | M | M | L | M | — | B6 | 提交成功率提升 |
| H2 | CTA 一致性（产品页 → 询价 / WhatsApp） | 全站 | M | M | L | M | — | B6 | 每页 ≥1 CTA |
| H3 | WhatsApp / tel / mailto 点击追踪 | `base.html:230-232` | M | H | L | S | D3 | B0 | 事件可见 |
| H4 | 项目页 PDF 下载入口与转化 | seed `pdf_url` | L | M | L | S | — | B6 | 下载可追踪 |
| H5 | 移动端导航（1025 阈值已改 ✅） | — | L | L | L | S | — | 保持 | — |

### I — 权威与外链（补充）

| ID | 任务 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|
| I1 外链现状盘点（GSC 链接报告 / 免费工具） | M | M | L | S | D2 | B7 | 基线清单 |
| I2 行业目录与协会（照明/体育场馆协会、IES 类） | L | M | L | M | I1 | B7 | ≥5 条质量外链 |
| I3 项目业主 / 合作方反向链接请求（22 个项目方） | L | H | L | M | I1 | B7 | ≥3 条 |
| I4 `sameAs` 一致性（Organization 已含 FB/YT/IG/TikTok/LinkedIn ✅） | L | L | L | S | — | 保持 | — |
| I5 案例投稿 / 新闻稿 | L | M | L | M | C4 | B7 | ≥2 篇 |

### J — 运维与可靠性（补充，🔴 含致命项）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| **J1** | 🔴 **联系表单持久化**：现写 /tmp DB，**重部署即清空** → 迁 Neon/Supabase Postgres（或确保邮件通知 100% 送达） | `api/index.py` `_ensure_runtime_schema()` | **H** | **H** | M | L | — | B6 | 部署后历史线索仍可查 |
| J2 | 部署后线上冒烟自动化（关键 URL × 状态码 × 关键串） | 新增 `scripts/e2e/smoke_online.py` | M | M | L | M | — | B1 | 每次部署跑 |
| J3 | 可用性监控（UptimeRobot 免费） | — | M | M | L | S | — | B6 | 告警生效 |
| J4 | 邮件送达复核（`CONTACT_NOTIFY_EMAIL` + 应用专用密码） | 手册 §7 | H | H | L | S | — | B0 | 实测收信 |

### K — 合规与无障碍（补充）

| ID | 任务 | 证据 / 位置 | E | R | S | W | 依赖 | 批次 | 验收 |
|---|---|---|---|---|---|---|---|---|---|
| K1 | Cookie 同意与 GA4 联动（同 D4） | `base.html:520-564` | M | M | M | M | D1 | B0 | 合规 |
| K2 | 🔴 **页脚隐私政策 / 服务条款是 `<span>` 不是链接**（无真实页面） | `base.html:240-241` | M | M | L | M | — | B6 | 两个真实页面 |
| K3 | a11y 复核（焦点可见、对比度、alt 100% ✅、ARIA） | — | L | M | L | M | — | B6 | 无新增违规 |
| K4 | GDPR / 目标市场合规文案（Cookie、隐私文本不机翻） | 既有铁律 | M | M | L | M | E1 | B5 | 各语言合规 |

---

## 5. 快赢清单（第 1 周内可上线，收益/风险比最高）

| 序 | 动作 | 批次 | 理由 |
|---|---|---|---|
| 1 | 配 GA4 + GSC 环境变量（D1） | B0 | 否则一切优化无数据 |
| 2 | 4 个转化事件（D3） | B0 | 埋点即 KPI 起点 |
| 3 | CWV 基线脚本（A1） | B0 | 无基线无法证明优化有效 |
| 4 | `rt590fl-s` / `rt390fl` 9 字符描述补齐（C1） | 提前 | 两页近乎空 meta |
| 5 | `llm.txt` 版本号同步（G2） | B3 | 5 分钟 |
| 6 | hero slide 2..n lazy（A5） | B2 | 1 行改动 |
| 7 | 页脚隐私/条款链接（K2） | B6 | 合规缺口 |

---

## 6. 批次执行计划

| 批次 | 周次（自 2026-09-28） | 内容 | 预估 | 上线前必测 | 回滚 |
|---|---|---|---|---|---|
| **B0** | W1（9/28–10/4） | D1(用户配变量) · D2 · D3 · D5 · A1 · F7 · J4 · H3 | 1.5d | 单测 + 线上 `G-`/meta 验证 + 控制台 0 报错 | revert commit |
| **B1** | W1–W2 | F1 · F2 · F3 · F4 · F8 · B7 · J2 | 2d | 冒烟脚本全绿 | revert |
| **B2** | W2（10/5–10/11） | A2 · A3 · A4 · A5 · A7 · A8 | 2d | **PSI 回归对比 A1 基线** + 视觉快照 | revert（FOUC 风险需在 Preview 看） |
| **B3** | W3（10/12–10/18） | B1 · **B2（新增字段）** · B3 · B4 · B5 · G2 | 2.5d | 新增 `tests_seo_keywords.py` 全绿 + seed 往返一致 | revert + 迁移回滚 |
| **B4** | W3–W4 | C1 · C2 · C3 · C6 · C8 · B6 · B10 | 3d | 内容唯一性守卫 + JSON-LD 守卫 | revert |
| **B5** | W5–W6（10/26–11/8） | **E1（24×5 翻译）** · E2/B8 · E4 · E5 · K4 | 5d | 五语无空串回退 + RTL 截图 | revert |
| **B6** | W5–W6 并行 | H1 · H2 · H4 · **J1（表单持久化）** · J3 · K2 · K3 | 3d | 表单实测端到端 + 重部署后数据仍在 | revert |
| **B7** | W7+ | G1 · G3 · C7 · C9 · I1–I5 | 持续 | Rich Results Test + 性能不退化 | revert |
| **B8** | 随时插入 | **A6 图片三档变体（需人工制图配合）** | 待定 | 人工验收 | revert |

---

## 7. 测试方案（四层）

### L1 — 单元测试（每次提交必跑）
`E:/Python/python3/python.exe manage.py test`（当前基线 **292 tests / 0 failures / 2 errors**，errors 为 `ProductAdminSidebarTreeTests` 缺 `lookup_opts`，与本次无关）。

新增守卫套件（命名约定）：

| 文件 | 测试类 | 覆盖 |
|---|---|---|
| `pages/tests_seo_keywords.py` | `ProductSeoTitleKeywordTests` | 24 页 title 必含品类词 + 参数 |
| | `MetaDescriptionUniquenessTests` | 24 页 description 互异、长度 50–160 |
| | `SeoFieldFallbackTests` | `seo_title` 为空回退 name，**绝不空串** |
| | `CategoryKeywordMappingTests` | `CATEGORY_KEYWORD` 覆盖全部 category + slug 覆盖表 |
| `pages/tests_analytics.py` | `ConversionEventTests` | 4 事件渲染；未配 GA4 时不渲染；gtag 未定义安全降级 |
| `pages/tests.py`（既有） | `JsonLdValidityTests`(10) · `NewsChipsAndCopyTests` · `ProductImagePathResolutionTests` · `RtlBidiIsolationTests` | 保持全绿 |

> 打页面记得带 `HTTP_HOST='localhost'`（ALLOWED_HOSTS 不含 testserver）；admin Client 需 `setup_test_environment()`。

### L2 — 线上冒烟（每次部署后）
`scripts/e2e/smoke_online.py`（新增）断言：
1. `/`、`/products/`、`/products/<slug>/`、`/projects/<slug>/`、`/news/`、`/contact/` 全 200；
2. 每页 `<title>` 含品类词（B3 后生效）；
3. canonical 自引用 + hreflang 6 语 + x-default；
4. JSON-LD 块 JSON 可解析（≥1 块/页）；
5. GA4 `G-` ID 与 `google-site-verification` 存在（D1 后）；
6. `/robots.txt` 含 AI 块、`/llm.txt`、`/llms.txt`、`/news/feed.xml`、`/sitemap.xml` 全 200。

### L3 — 性能回归（B2 前后 + 每月）
`scripts/perf_baseline.py`：
- 输入：6 类代表页 × {mobile, desktop}；
- 数据源：**PageSpeed Insights API**（免费 key；若不愿申请，退化为手动 Lighthouse 导出 JSON）；
- 输出：`docs/perf_baseline_<date>.json`；
- **门禁**：LCP 不劣化 > 10%、CLS < 0.1、INP < 200ms，否则阻断上线。

### L4 — 人工 / 平台验收
- PSI 手动抽查（每批 1 次）；
- GA4 实时报告验证 `generate_lead` 事件；
- GSC：收录数、国际定向、查询词；
- RTL：阿语页面截图（B5 后）；
- Visual：Preview 环境人眼看 FOUC（B2 必做）。

---

## 8. 里程碑与时间表（接续既有手册 M1/M2）

| 里程碑 | 内容 | 对应批次 | 目标日期 | 出口指标 |
|---|---|---|---|---|
| **M3** | 数据基建与转化追踪 | B0 | 2026-10-04 | GA4/GSC 生效、4 事件可见、CWV 基线存档 |
| **M4** | 索引健康与技术审计 | B1 | 2026-10-11 | 审计报告 + 冒烟脚本上线 |
| **M5** | 核心网页指标优化 | B2 | 2026-10-11 | 移动 LCP < 2.5s |
| **M6** | 关键词资产落地（英文） | B3 | 2026-10-18 | 24 页 title 含品类词、描述唯一 |
| **M7** | 内容深度与 EEAT | B4 | 2026-10-25 | 24 产品描述 ≥150 字符、参数 ≥5 项、资源中心 4 篇 |
| **M8** | 五语全覆盖 | B5 | 2026-11-08 | 24×5 无空串、RTL 隔离验收 |
| **M9** | 转化与可靠性 | B6 | 2026-11-08 | 表单持久化、隐私/条款页面上线 |
| **M10** | 权威与 GEO | B7 | 2026-11-15 起持续 | 外链基线 + AI 引用监测表 |
| **M11** | 图片变体（人工配合） | B8 | 待定 | 移动端 LCP 再降 1s |

---

## 9. KPI 与监控节奏

| 频率 | 动作 | 指标 |
|---|---|---|
| 每次部署 | L1 单测 + L2 冒烟 | 0 failures |
| 每周 | GSC 查询词导出 → 回填 `keyword-inventory.csv` | 有展现词数、Top-10 词数、CTR |
| 每周 | GA4 看板 | `generate_lead` 数、来源页、国家 |
| 每月 | PSI 全量回归 | LCP / CLS / INP |
| 每月 | AI 引用监测（G3）+ 外链盘点 | 被引用次数、外链数 |
| 每季度 | 索引健康复核（F1–F6） | 收录率、抓取错误 |

---

## 10. 风险登记与回滚

| 风险 | 触发点 | 影响 | 缓解 | 回滚 |
|---|---|---|---|---|
| CSS 异步化 FOUC | A2/A3 | 首帧无样式 | critical CSS 兜底 + `<noscript>`；**Preview 目视验收** | revert commit + push |
| 字体子集化截断字形 | A4 | 部分字符（如 °、μ）变豆腐块 | 保留 latin-ext + 逐页目视；重点查 `°C`、`μ`、箭头 | revert |
| 翻译空串污染线上 | E1 | 页面空白标题 | 第三套机制铁律：缺译回退英文，守卫断言非空 | revert + seed 回退 |
| seed 覆盖事故 | B2/B4/C1 | 生产文案被静默回写 | 🔴 **改文案 DB + JSON 同改再 `--json`；改 DB 用 `.update()`** | git revert + 重新同步 |
| 表单线索丢失 | J1 | SEO 带来的线索随部署清空 | 迁 Neon/Supabase | 保留邮件副本兜底 |
| GA4 与 CSP 冲突 | D1 | 脚本被拦 | `script-src` 已含 GTM；上线后查控制台 | 移除变量即关闭（代码已条件渲染） |
| 改 URL 丢索引 | B9 | 排名归零 | **决定不改 slug**，靠 title 补词 | — |
| 测试卡死 | 全批 | 长跑 test 与 runserver 抢 sqlite 锁 | 已设 `timeout: 2`；**不要并行跑** | — |

---

## 11. 需要你提供的物料 / 操作

| # | 物料 | 用于 | 紧急 |
|---|---|---|---|
| 1 | Vercel 配 `GA4_MEASUREMENT_ID`、`GSC_VERIFICATION_CODE` | D1 | **H** |
| 2 | GSC 域名验证 + sitemap 提交（或授权我用 meta 验证） | D2 | **H** |
| 3 | PSI API key（免费，Google Cloud 启用；不愿则退手动 Lighthouse） | A1 | M |
| 4 | 五语母语校对（24 产品页 title/desc） | E1 | H（B5 前） |
| 5 | 图片原图分辨率清单（判断哪些够降档） | A6/B8 | L |
| 6 | 认证证书文件（CE/ENEC/UL 等） | C8 | M |
| 7 | 项目业主/合作方联系（外链请求） | I3 | L |

---

## 12. 变更记录

### v1.0.0 (2026-09-28) — 初版
- 线上实测建立基线（TTFB 0.70s、base.css 19.6KB br、sitemap 53 条、**GA4/GSC 未配置、0 转化事件**）。
- 划分 A–K 共 11 个大类（用户指定 A/B/C + 补充 D–K 共 8 类）。
- 用户拍板：关键词源 = GSC + 免费工具；图片变体后置需人工；五语覆盖全 24 产品页。
- 制定批次 B0–B8、里程碑 M3–M11、四层测试方案、风险登记表。
- **状态：待批准** → 批准后从 **B0** 开工。

### v1.0.1 (2026-09-28) — B0 代码落地
- **D3 / H3 转化事件**：`base.html` 注入 `gaTrack()` 安全降级封装 + 全局 click 处理器
  （`contact_click`=mailto/tel/wa.me、`pdf_download`=`.pdf`）+ 产品页 `quote_view`
  IntersectionObserver 曝光（挂在 `product_detail.html` 的 `data-ga-event="quote_view"`）。
  `contact.html` 在表单**真实成功**时渲染 `generate_lead`（`contact_submitted_success`
  上下文标志，honeypot 机器人丢弃路径不触发）。全部事件仅在 `GA4_MEASUREMENT_ID`
  配置后真正上报，未配置时 no-op。
- **A1 CWV 基线脚本**：新增 `scripts/perf_baseline.py`（PSI API，6 类页 × mobile/desktop →
  `docs/perf_baseline_2026-09-28.json`；无 key 时写 skeleton + 手填说明）。
- **L1 守卫**：新增 `pages/tests_analytics.py`（7 用例：4 事件接线 + gtag 安全降级 +
  GA4/GSC 按需渲染 + 产品页 quote_view 钩子 + generate_lead 成功触发）。
- **L2 冒烟脚本**：新增 `scripts/e2e/smoke_online.py`（路由 200 / canonical / hreflang /
  JSON-LD / GA4·GSC / robots·llm·feed·sitemap）。
- **D5 KPI 看板定义**：新增 `docs/kpi-dashboard.md`（北极星=generate_lead，4 事件漏斗，维度拆解）。
- **测试结果**：全量 299 tests / 0 failures / 2 errors（2 errors 为已知 `ProductAdminSidebarTreeTests`
  遗留，与 B0 无关）。
- **待用户操作（D1/D2/J4）**：Vercel 配 `GA4_MEASUREMENT_ID` + `GSC_VERIFICATION_CODE`、
  GSC 验证并交 sitemap、复核 `CONTACT_NOTIFY_EMAIL` 邮件送达。配好即生效，不配则完全不加载第三方。
- **D4（GA4 Consent Mode v2）**：B0 行未纳入，作为 GDPR 加固项顺延到后续批次；当前页面浏览
  `gtag('config')` 在加载即上报，欧盟流量合规需补 Consent Mode，已登记为已知 follow-up。

---

## 变更记录

### v1.0.1 (2026-09-28, B0 闭环)
- B0 数据分析/转化基座完成：GA4 商务账号 `G-81MQ1C1L5H` 上线、GSC 商务账号验证 + sitemap 提交 53 页、4 个转化事件守卫、CWV 基线脚本、线上冒烟脚本、KPI 看板。

### v1.0.2 (2026-09-28, B1 第一批)
- **F1（footer 假链接修复）**：`templates/base.html` 的 `隐私政策 / 服务条款` 从死 `<span>` 改为真实 `<a href="{% url 'privacy' %}">` / `terms`；新增 `templates/privacy.html` + `templates/terms.html`（英文法律正文，多语种法律翻译留作 B5/C 专项）+ `views_other.privacy/terms` + `urls.py` 路由 + sitemap 静态页（priority 0.4）。
- **F2（PWA / 图标）**：新增 `static/manifest.json`（name/display/theme_color #0088FF/icons）；由 `static/images/favicon.webp`(100×100) 用 Pillow 放大生成 `apple-touch-icon.png`(180) / `pwa-icon-192.png` / `pwa-icon-512.png`；`base.html` head 新增 `rel="manifest"` 与 `rel="apple-touch-icon"`。
- **守卫**：新增 `pages/tests_pages_b1.py`（6 用例，全过）；`scripts/e2e/smoke_online.py` 扩展 privacy/terms 路由 + manifest/apple-touch-icon 资源检查 + manifest JSON 合法性校验；`scripts/e2e/visual_review.py` DEFAULT_PATHS 增加 `/privacy/`、`/terms/`。
- **测试**：全量 305/0 failures/2 errors（2 errors 为已知 ProductAdminSidebarTreeTests 遗留）。修复两处坑：① 测试文件顶层重复 `setup_test_environment()` 会 RuntimeError（与 tests_analytics.py 同坑）；② 模板多行 `{# #}` 注释触发 `test_no_multiline_hash_comment_in_templates`（改单行注释）。
- **待部署后验证**：新页面/资源需 Vercel 重新部署才上线，跑 `python scripts/e2e/smoke_online.py` 复核。
- **未做（本轮外）**：① GSC 索引覆盖率审计需等 GSC 数据（2–3 天后）再查 F3/F4 类重复内容/404；② CI 部署后自动冒烟（J2）为 follow-up；③ 法律页多语种翻译（B5/C）。

### v1.0.3 (2026-09-29, B3 第一批 — per-page SEO)
- **B2（per-page SEO 字段）**：`seo_title`/`seo_description` 不新增 DB 列，改存入既有 `translations` JSON（按语种），复用第三套 i18n 机制、免迁移、免 seed_sync 改 schema。**铁律**：方法名 `seo_title`/`seo_description` 与 `translations` 的 key 同名，会撞 `translate()` 的 `getattr(obj, field)` 回退（en 时返回方法本身→真值→永远不落公式）；新增 `pages/utils.py: get_seo_override()` 直接读 `translations` 字典避开碰撞。
- **B3（品类词映射）**：`pages/utils.py: CATEGORY_KEYWORD`（8 类→SEO 短语）+ `SLUG_KEYWORD_OVERRIDE`（空，机制预留）；`pages/utils.py: _seo_keyword()` 解析。
- **B4（title 公式）**：`build_seo_title()` = `{品类词} {型号} — {关键参数} | SolarOne`；`model_number` 已含功率时不重复追加。
- **B5（description 公式 + 唯一化）**：`build_seo_description()` 英文公式，嵌入唯一标识（型号/名称）保证 24 页互异、50–160 字符；非英文回退翻译 `description`（不退化成英文公式）。
- **接入点**：`pages/views/enrich.py` 在 `_enrich_product`/`_enrich_project` 挂 `seo_title_t`/`seo_description_t`；模板 `product_detail`/`product_overview`/`project_detail` 改用这两个属性（保留 Not Found 分支）。
- **B1（词库）**：新增 `docs/keyword-inventory.csv`（32 行：8 品类 + 24 产品 slug，量级/KD 留空待 GSC 校准）。
- **G2（llm.txt 版本）**：经核实 `VERSION` 文件与 `llm.txt` 均为 v1.8.1，**已自洽**，无需改（记忆里"实际 1.8.3"与文件不符，以文件为准，待用户确认是否 bump）。
- **守卫**：新增 `pages/tests_seo_keywords.py`（11 用例：品类词覆盖、title 含品类词、非英文 localized keyword、description 唯一+长度、显式覆盖优先、非英文回退翻译、模板渲染端到端）；`scripts/e2e/smoke_online.py` 增加产品页 title 含品类词+`| SolarOne` 校验。
- **测试**：全量 319/0 failures/3 errors（3 errors 为已知 `SidebarOrderedChangeList` 缺 `lookup_opts` 后台遗留，与 B3 无关）；`tests_seo_keywords` 11 全绿。
- **影响面**：仅改产品/项目详情页的 title/description 生成；列表页（products/projects/home 等）仍是 `{% blocktrans %}` 硬编码，不受影响。B4/C1 后续可把显式 `seo_description` 译文写进 seed 提升文案质量。
- **待部署验证**：Vercel 重部署后跑 `python scripts/e2e/smoke_online.py` 复核产品页 `<title>` 含品类词。
