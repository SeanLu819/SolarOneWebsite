# SolarOne 外贸站 — SEO / GEO 优化状态与待办（v1.9.6）

> 最后更新：2026-10-03 · 所有结论均来自本地脚本实测 + 线上 `curl` 实测，非主观判断。
> 代码状态：v1.9.1–v1.9.5 **已 push 并部署上线**（`origin/main = c6157fa`）；v1.9.6 为本地新提交，未 push。
> ⚠️ **GitHub 默认分支仍是 `master`**（2026-10-03 `git ls-remote --symref` 实测），见 A1。

---

## 0. 一句话结论

**代码层面的 SEO 硬伤基本修完，卡点已从"代码"转移到"发布动作 + 内容源清洗"。**
v1.9.6 补掉了最后一处已知的 description 预算缺口（全站 58 URL 扫出 5 条站点级超标）。
未完成项里，多数只能在你本机/控制台完成。

---

## 1. 已完成

| # | 项 | 提交 | 实测 |
|---|---|---|---|
| 1 | Tier-1 hub `/products/sports-lighting/` + 三落地页 | `d378695` | 线上已生效 |
| 2 | 项目 → 落地页 `sport_type` 内链块 | `d378695` | 22/22 项目带出链 |
| 3 | Vercel 两阶段清理 workflow | `d378695` | 需手动触发（见 A2） |
| 4 | A 组 5 项 JSON-LD P0 修复 + 10 守卫 | `d378695` | 912 块 0 失败 |
| 5 | B 组 llm.txt / robots AI UA / 产品 FAQ / RSS | `d378695` | 见 §3 已验证 |
| 6 | 三落地页五语本地化 | `c24d186` | 6/6 locale 命中 |
| 7 | 项目 `<title>` 注入品类词，**22/22 ≤60 字符** | `dbb2886` | 关键词与 `| SolarOne` 永不被切 |
| 8 | 项目 meta description 压缩，**22/22 ≤160 字符、0 个 `【`** | `e6478d6` | 改前 599–1215 字符 |
| 9 | 正文/列表卡/JSON-LD 的 `【】` 清洗 | `f92ad74` | 22/22 段落结构不变 |
| 10 | 修 2 个常年 error 的 admin 测试，**首次全绿** | `c702975` | 431 → 0/0 |
| 11 | 301 redirect 机制（`pages/redirects.py`） | `c6157fa` | 452 tests / 0/0 |
| 12 | **站点级 meta description 压到 ≤160**（v1.9.6） | 待 push | 线上实测超标 5 条 → 现 148–157 |

全量回归：**462 tests / 0 failures / 0 errors**。

### v1.9.6 细节：站点级 description（2026-10-03 线上全站扫描发现）

线上 58 个 sitemap URL 全扫，5 条超标：`/` 180、`/products/` 187、`/about/` 179、
`/products/football-stadium-lights/` 171、`/products/tennis-court-lighting/` 187。
改成 148–157 字符，砍的全是填充词（`at every level of play` / `field-proven reliability` /
`worldwide` / `solutions`），商业词一个没丢。

- 🔴 **测长度必须先 `html.unescape`**：Django 把 `'` 渲染成 `&#x27;`，raw HTML 每个撇号多 5 字符。
  第一遍扫项目页时 5 条"超标"是**误报**（161–164 → 解码后都 ≤160）。
- 五语 msgid 全部重键、`msgstr` 原样保留；用「改动前后 dump 全部 `.mo` 条目比对」证明零漂移。
- **非英语故意不压到 160**：Google 按渲染宽度截断，ru/ar 每字符承载信息量远大于拉丁字母，
  190 字符的俄语比 160 字符的英语占的版面还小。ar 现已自然落在 126–143。
  如果你仍想压 fr/es/de（164–209），需要授权重写译文——这是独立决策，不夹带。


---

## 2. ✅ P0 — 正文渲染带中文方括号的原文（v1.9.3 已修）

**证据**（test client 渲染 `/projects/perryville-high-school/`）：

```html
<div class="detail-desc"><p>【Customer Profile】<br>Perryville High School is a prominent public…
```

**落点两处**：

- `templates/project_detail.html:106` — `{{ project.description_t|nl2para }}`（正文，用户可见）
- `templates/projects.html:75` — `{{ project.description_t }}`（列表页 22 张卡片，每卡 600–1200 字符）

**为什么 v1.9.2 还没解决**：上一轮只改了 `seo_description()`（meta/og 通道），正文走的是 `description_t`，**两条通道没打通**。

**v1.9.3 修法**：`pages/utils.py` 加 `scrub_project_markers()`（**只删标记、不动换行**；`\r`→`\n` 会静默把单换行变成分段、重排整篇正文），`pages/templatetags/text_filters.py` 加 `descrub` 过滤器——**一处定义同时覆盖 DB 与 seed 两条路径**（过滤器作用于渲染值，从根上避免"双路径各写一遍"的经典漂移），`SafeString` 身份保留使转义仍归 `nl2para`。模板 4 处接入（详情正文、列表卡、两处 JSON-LD）。

**实测 22/22**：段落数与改动前完全一致（3→3），长度差恒等于标记文本本身，`【` 全站归零；`<br>` 减少只发生在标记处（原本 `【Customer Profile】` 单独断行）。

---

## 3. 已验证 OK —— 不要重复做（纠正之前的两处误判）

| 检查项 | 之前的判断 | 实测 | 结论 |
|---|---|---|---|
| sitemap 收录 | 疑缺项目页 | 58 条 `<loc>`：products 28 / **projects 23** / news 2 / 各单页 | ✅ 完整 |
| hreflang | 只有 1 处，疑残缺 | `{% hreflang_links %}` 实际输出 **7 标签**（en/fr/es/de/ru/ar + x-default） | ✅ 完整 |
| llm.txt 双入口 | — | `build.sh` 有 `public/llms.txt`；robots.txt 6 个 AI UA | ✅ |
| 产品 title / desc | — | 24/24 ≤60 字符；描述均为人工文案 ≥150 | ✅ |
| 项目 title / desc | — | 22/22 ≤60 / ≤160，0 个 `【`（仅 meta 通道） | ✅ 本地已改，待上线 |

---

## 4. 未完成清单

### A 类 — 只能你本机 / 控制台做（代码侧无解）

| # | 事项 | 卡点 | 动作 |
|---|---|---|---|
| ~~A1~~ | ~~push~~ | ✅ **已完成** 2026-10-03，`origin/main = c6157fa`，本地 ahead 0 | 6 个提交全部上线 |
| A2 | **默认分支 master → main** | 2026-10-03 `git ls-remote --symref` 实测 HEAD 仍指 `refs/heads/master`（`ef45310`）。**scheduled workflow 只在默认分支生效** | GitHub → Settings → Branches → Default branch → `main` |
| A3 | Vercel 配邮件环境变量 | `settings.py:445-458` 已就绪，但 `CONTACT_NOTIFY_EMAIL` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` 只有 env 有值时才生效 | 未配 → 联系表单仍落 /tmp DB，重部署即丢 |
| A4 | Cloudflare 放行 AI 爬虫 | CF 新域默认拦截 AI crawler（robots.txt 已写好 6 UA，代码无解） | CF console → AI Crawl Control / Bot 管理手动放行 |
| A5 | 跑一次 vercel-cleanup + 看存储 | 存储约 8.94/10GB，聚合有延迟 | 直接访问 `/actions/workflows/vercel-cleanup.yml` → Run workflow → 选 main |
| A6 | GSC 申请索引 | 三个新落地页可能没被快速收录 | `/products/sports-lighting/`、`/football-stadium-lights/`、`/tennis-court-lighting/` 手动 Request Indexing |
| A7 | Semrush 复测 | 新标题/落地页需时间发酵 | 2–4 周后 |

### B 类 — 需要改代码（未开工）

| # | 事项 | 现状 / 影响 | 建议 |
|---|---|---|---|
| ~~B1~~ | ~~正文 `【】` 残留~~ | ✅ **v1.9.3 已修** | 见 §2 |
| ~~S1~~ | ~~2 个预存 error~~ | ✅ **v1.9.4 已修**，回归首次全绿 | 根因在测试：用 `__new__` 构造 `ChangeList`，漏了 `__init__` 才设置的 `lookup_opts`，而 Django `_get_deterministic_ordering()` 会读它 → 还没跑到被测逻辑就 AttributeError。改成一个 `_make_change_list()` helper 补齐字段；变异探针验证过（侧栏注入改 `False` 后测试确实变红） |
| B2 | 「500+ projects / 50+ countries」自证矛盾 | `projects.html:6,8` 硬编码 500+，站内可验证 23 条案例 | 改可自证说法（如「精选案例覆盖 50+ 国家」），或补案例页。`home.html` 的 50+ 属营销话术，可保留 |
| ~~S2~~ | ~~301 redirect 机制缺失~~ | ✅ **v1.9.5 已建** | 新增 `pages/redirects.py`（单一真源，纯 stdlib，不放 seed/DB）：项目/产品 slug 表 + 整条路由退役表。只在 slug 解析失败时才查表，所以登记 redirect 不会遮蔽现存活页；目标走 `reverse()`，语言前缀保留。守卫 21 例 + 两条变异探针 |
| ~~B4~~ | ~~未知产品 slug 软 404~~ | ✅ **早已是真 404**（2026-10-02 实测 `/products/definitely-not-a-slug/` → 404） | `views_products.py:397` 现为 `raise Http404`，`test_unknown_slug_returns_real_404` 锁住。**此前文档描述过时，已更正**——无需再做 |
| B3 | B 组：5 个纯人名词 slug 改关键词 | ✅ **前置已解除**（redirect 表现在可用） | 仍建议暂缓：商业意图词贡献≈0，却要付 301 登记（现在只需在 `pages/redirects.py` 加一行）+ mv 5 个 `static/images/projects/<slug>/` 目录 + 改 `project_detail.html:126` 硬编码分支 |
| B5 | `red-1-karting-beijing` 描述 183 字符 | 22 条项目里唯一 thin | 扩写到 ≥400 字符（配图 + 客户背景 + 交付清单）**——需要你提供事实内容，AI 不能编造客户背景** |
| B8 | fr/es/de 译文 description 164–209 字符 | 英文已达标，非英语超的是**字符数**不是版面宽度 | **待你决策**：若要压需重写 5 语译文（AI 可执行，但术语与营销措辞需你过目）。ru/ar 不建议动（每字符信息量高） |

### 2026-10-03 下午复审计（58 URL 全扫 + 六语抽样）新发现

**先说已排除的虚警**（测量 bug，非站点问题）：`content="([^"\']*)"` 里的单引号会把
`Explore SolarOne's range...` 截断成 `Explore SolarOne`（16 字符），一度误报「3 条超短 desc」。
真实分布是 **107–160 字符，无超短无超长**（v1.9.6 已上线生效）。

| # | 优先级 | 问题 | 证据 |
|---|---|---|---|
| ~~C1~~ | ~~产品页非英语 description 没有 clamp~~ | ✅ **v1.9.8 已修** | 新增 `pages.utils.fit_description`（句界优先），`Product.seo_description` + `_DictProduct.seo_description` 双路径同步（另加 `tests_seo_keywords.py` 测试镜像）。实测 24 产品 × 6 语 = 144 条全部 ≤160、英语零变化。**守卫本身是探针逼出来的**：第一版只测 seed 路径，从 `models.py` 删掉 clamp 依然全绿（测试环境渲染走 seed 镜像），补了 DB 路径 + 双路径一致性两条才锁住 |
| ~~C2~~ | ~~title 超 60：news 80 / products 64~~ | ✅ **v1.9.8 已修** | products 改 `templates/products.html:5,7`（**title 与 og_title 必须成对改**，否则 i18n 覆盖守卫立刻报"缺 gettext 条目"）；news 是**数据不是文案** → 改 `seed_data.json` + `pages/seed_data.py` 两处真源。现 57 / 54 字符 |
| C3 | P2 | **594/596 张图无 width/height**（CLS 风险） | 全站 596 个 `<img>` 只有 2 个有显式尺寸；`fetchpriority="high"` 仅 26 个 |
| C4 | P2 | 593/596 张图无 srcset | 三档方案待议（v1.9.x 起已挂账） |
| C5 | P2 | 项目页非英语 desc 全回退英文 | `/projects/perryville-high-school/` 五语 desc 均 156 字符（项目 `translations` 无 `en` 键 → 恒走公式，见 C1 的对照） |

### 2026-10-03 晚 — 图片问题全面扫描（用户要求先扫描后推送）

**总量**：磁盘 **318 张 / 37.71 MB**（webp 315、非 webp 3、不可读 0）；HEAD 跟踪 337 →
工作区已删 19（= 磁盘 321，其中 3 张是 gitignore 的 `news/*/_source/*.jpg`）。

| 分类 | 判定 | 结论 |
|---|---|---|
| 重复副本（md5 全同） | **21 组 / 2.02 MB** | 最大组 `fl9m-3d-view` 系 4 份 0.52 MB；`beamangle-12183050.webp` 9 份 0.31 MB。都落在活的枚举画廊目录里 → **删副本 = 从那个画廊里少一张图（视觉变化）**，不是纯白捡 |
| `scripts/audit_images.py` 报「未引用 31 张 / 2.94 MB」 | ❌ **几乎全是假阳性** | 扫描器只查 seed 数组，`hero-main-*` / `logo` / `favicon` / `apple-touch-icon` / `optics-*` / `agent-*` 其实都在模板里 |
| **真·死图** | ✅ **只有 4 张 / 0.42 MB** | 3 张 `images/news/low-cct-…/_source/W0…jpg`（本就 gitignore，是重导出原图，应保留）+ 1 张 `images/products/ordering/sample-number.webp`（与被引用的 `m-series/sample-number.webp` md5 相同） |
| 页面级 `<img>` 属性 | 596 个 | **594 无 width/height**（CLS）、**593 无 srcset**、0 缺 alt、26 `fetchpriority="high"` |
| 工作区已删的 19 张认证图（17× `certifications-…ip66.webp` + 2× `rgbw-interface-…ip66-ik08.webp`） | ✅ **删得安全** | 全站只有 2 条认证图完整路径在 `seed_data.json`（`m-series` + `rgb-rgbw`），另有一处 `pages/views/enrich.py:21 DEFAULT_CERT_IMAGE`；模板里零硬编码。删除只让它们不再渲染，**不产生 404、无视觉回归** |

**判定口径（漏一维就翻车）**：产品/项目画廊是**目录枚举**渲染的
（`_list_static_dir('images/products/<slug>')`，`pages/views/utils.py:325-339`），
文本里搜不到 ≠ 死图。只做文本 grep 时死图清单 17 个 / 1.89 MB，补上枚举维度后只剩 4 个 / 0.42 MB。

**未动、待决策**：① C3/C4 属性缺口；② 21 组重复副本是否允许「同图多画廊」；
③ 真死图的清理由你确认（`ordering/sample-number.webp` 单删即可）。

### 「异常大」图片清单（>200 KB 口径，跟 `scripts/gen_image_issue_report.py` 一致）

**49 张 / 14.81 MB，占全站（37.71 MB）的 39%。**

| 尺寸 | 张数 | 体积 | 处理建议 |
|---|---|---|---|
| 1920×1080 | 22 | 6.92 MB | 列表卡渲染框最宽 1248 px → 降到 1280×720，省约 55% |
| 1280×720 | 15 | 3.57 MB | 已接近上限，只需重压（q 值），不必改尺寸 |
| **1920×442（4.34:1 横条）** | 5 | 1.27 MB | 比例与 16:9 框不符 → **渲染时裁掉 59%**，应重导出为正经 16:9 或缩到 1280×295 |
| 1520×856 | 2 | 0.60 MB | VSP9M 系列（v1.9.7 已压一轮，VSP9M-04 仍 360 KB，是全场最重的产品图） |
| 1920×1078 | 2 | 0.46 MB | hero 位，降 1280 宽即可 |
| **1217×675** | 1 | **1.54 MB** | ⚠️ **明显异常值** —— 比第 2 名（466 KB）大 3.3 倍，同一相册其它图仅 0.1–0.3 MB，等于漏压了一张，重导出收益最大 |
| 1920×600（3.20:1） | 1 | 0.24 MB | `fl16m-3d-view`，同样被 16:9 框裁切 |
| 512×512 | 1 | 0.21 MB | `pwa-icon-512.png`（PWA 图标，不算问题） |

**像素远超显示需求**（>1872 px 宽，渲染框最宽 1248 px）：**47 张 / 10.07 MB**，集中在 10 个项目相册整组（liu-li-bridge、perryville、red-1-karting、garrison-forest、national-olympic-tennis、north-creek、baseball-field、beijing-capital、pickle-n-par、mcintosh），每组 5 张全是 1920×1080。

**优先级**：`bitc-tennis-03.webp`（1.54 MB）→ 1920 系列 22 张统一降 1280×720 → 5 张 1920×442 横条重导出（顺带修 59% 裁切）→ 47 张像素过量批量降规格（预计 10 MB → 4 MB 以内）。

**已确认 OK、别重复做**：canonical 58/58 ✓、hreflang **7 标签 58/58** ✓、OG + Twitter 全覆盖 ✓、
无重复 title ✓、h1 全有且 ≤60 ✓、img `alt` 全有 ✓、JSON-LD 17 类 ✓、desc 全 107–160 ✓。
| B6 | RTL 零隔离 | `/ar/` 卡片拉丁标题双向重排（2026-09 已截图坐实） | `bdi` / `unicode-bidi` 专项，全站性 |
| B7 | 生产联系表单持久化 | 存 /tmp DB，重部署清空 | 中期迁 Neon / Supabase |

---

## 5. 建议执行顺序

1. ~~**先 A2**（默认分支切 main）~~ → **已做**：2026-10-03 已 push + 部署上线。
2. ⚠️ **A2 仍待补做**：默认分支实测仍是 `master`，A5 的 cron 在切到 `main` 之前不会触发。
3. push v1.9.6（站点级 description）。
4. 代码侧可继续开工的：**C1**（唯一"逻辑不对称"的真 bug，影响 5 语 × 24 产品）→ 然后 C2；
   B2 属纯文案 + 5 语 `.po`，可并行；B3/B5/B8 待决策或需你提供内容。

---

## 6. 回归验证清单（上线后）

```bash
# 本地（注意：线上必须带 www，裸域 308 跳 www）
python manage.py test          # 期望 462+ / 0 failures / 0 errors

# 线上
curl -sL https://www.solaronelighting.com/projects/perryville-high-school/ | grep -o "<title>[^<]*"
curl -sL https://www.solaronelighting.com/sitemap.xml | grep -c "<loc>"
curl -sL https://www.solaronelighting.com/ | grep -o 'hreflang="[a-z-]*"'
curl -sL https://www.solaronelighting.com/llms.txt | head -1

# v1.9.6 上线验收：站点级 description 长度（v1.9.6 前超标 5 条）
curl -sL https://www.solaronelighting.com/            | grep -o 'name="description" content="[^"]*"'
curl -sL https://www.solaronelighting.com/products/   | grep -o 'name="description" content="[^"]*"'
curl -sL https://www.solaronelighting.com/about/      | grep -o 'name="description" content="[^"]*"'
# 期望：149 / 155 / 157（v1.9.6 前是 180 / 187 / 179）
```
