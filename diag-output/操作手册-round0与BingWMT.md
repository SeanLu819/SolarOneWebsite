# 操作手册：round 0 基线测量 + Bing Webmaster Tools

2026-10-23 | 对应清单文档 A 类剩余项与 C1

两件事都是手工活。这份手册的目标是让你**照着点就行**，不用回去翻协议。

---

## Part 0. 先看这个，能省你一半心理准备

我已经把原 10 条核心查询过了一遍检索层（网页搜索；C5/C6/X3 是后来补的，没走这层），结论：

> **10/10 零本站命中。** 没有一条查询返回 `solaronelighting.com` 的任何页面。

而且比"零命中"更具体的三件事：

| 发现 | 后果 |
| --- | --- |
| 品牌查询能搜到我们，但内容全在第三方且**规格是错的**（8 年质保 / 800,000PCS / IP65） | AI 引用我们时会引用错数字 |
| 德/法/阿语查询返回的多是**中文页** | `/de/` `/fr/` `/ar/` 页面要跟中文页抢同一个查询 |
| **没有任何"十大厂商"榜单提到 SolarOne** | 被问"Musco vs SolarOne"时 AI 很可能说无法比较 |

完整记录：`geo-baseline/retrieval-proxy-2026-10-23.md`

**所以你手工问 AI 时，大概率大面积看到 `mentioned=n`。这不是你测错了，这就是基线。**
反过来，如果哪一条明显好于预期，说明 IndexNow 推的 354 条开始见效了——那是要单独记一笔的好消息。

---

## Part ①. round 0 基线（88 格核心 + 6 格扩展）

### 1.1 准备（10 分钟）

一次性打开 8 个平台，**每个都开一个全新会话**（不要沿用旧上下文）：

| # | 平台 | 地址 | 检索底座 |
| --- | --- | --- | --- |
| 1 | ChatGPT | chatgpt.com | Bing |
| 2 | Copilot | copilot.microsoft.com | Bing |
| 3 | Perplexity | perplexity.ai | 自有 + Google |
| 4 | Gemini | gemini.google.com | Google |
| 5 | Claude | claude.ai | 训练数据为主 |
| 6 | Grok | grok.com | X + 网页 |
| 7 | Meta AI | meta.ai | Bing |
| 8 | DeepSeek | chat.deepseek.com | 自有 |

**排序建议**：先跑 1–2（ChatGPT / Copilot，都是 Bing 底座），再跑 3–8。
因为 N5 已经确认 Bing 侧零存在，1–2 最可能零命中——先啃最硬的，后面越跑越有信心。

> 登录状态会影响结果（登录后的 ChatGPT 能看到更多）。**记下你是登录还是匿名**，
> 写进 `notes`，否则下一轮没法复现。

### 1.2 粘贴单

`geo-baseline/paste-sheet-round0.txt` 已经按 CSV 行序排好 11 条，**原样粘贴，一个字都别改**。

```
cd diag-output/geo-baseline && cat paste-sheet-round0.txt
```

每条查询下面那行小字是判定提示，**不要粘进对话框**。特别是 C1 那条
"best LED stadium light manufacturers"——手贱加上"比如 SolarOne 怎么样"，
这格就废了，测出来的是你想要的答案，不是 AI 真实会说的。

### 1.3 逐格填法

打开 `rounds/round-0-2026-10-23.csv`（**只读查看可以，切勿保存**——2026-10-24
实测 Excel/WPS 另存会把 UTF-8 中文批量替换成 `?`、每行多出幻影列、引号双倍转义，
已造成一次事故并从 git 提交版恢复；要录入请粘贴文本给 AI 填），94 行已经预填好
`platform` / `query_id` / `query_text` / `lang` / `intent`，你只填后面 7 列。
**ChatGPT 平台 13 格已由分享链接提取填入**（见 `chatgpt-share-evidence-2026-10-23.md`）；
**Perplexity 10 格已完成**（B1/B2/C1/C2/C3/C5/C6/L1/L2/L3，Computer agent 任务模式，
B1/C3/C5 于 2026-10-24 补帖；X1/X3 用户确认无法进行、S1 原对话已删除且额度耗尽
无法重跑（2026-10-24 确认），三格永久留空，该平台定格 10/13 收官，见
`perplexity-computer-evidence-2026-10-24.md`）；**Grok 11 格已由分享链接提取填入**
（model=grok-3，见 `grok-share-evidence-2026-10-24.md`）；**DeepSeek 10 格已由分享链接
提取填入**（B1/B2/C1/C3/C5/L1/L2/L3/S1/X1，C1/L2 用户各跑两轮结果一致；model_version
分享 API 不暴露需回原会话补，见 `deepseek-share-evidence-2026-10-24.md`——其中
**B2/X1 出现"失信被执行人"指控——公开渠道初筛已证实挂在主实体本身**
（信用代码 91110116663729775X，英文名与 llm.txt 注册名一致，非同名张冠李戴，
见 `entity-verification-xinneng-2026-10-24.md`；用户侧待办：天眼查/zxgk 核实
案号明细与履行状态）。其余平台仍留空待测；
剩下的平台也可以照样分享链接我来提取：

| 列 | 填什么 |
| --- | --- |
| `mentioned` | 回答里出现 **SolarOne / 信能阳光 / solaronelighting.com** 任一 → `y`，否则 `n` |
| `rank` | 品牌**首次**出现的位置，1–10；提到了但不在前 10 → 留空 |
| `sentiment` | `pos` / `neu` / `neg`，看语气，不看是否提及 |
| `cited_own` | 回答给没给 solaronelighting.com 链接 → `y` / `n` |
| `spec_ok` | 引用的数字**和站内一致且归属正确** → `y`；不一致 / 归错公司 / 答的是另一家 → `n` 或 `na` |
| `competitors_seen` | 分号分隔，如 `Musco;Signify;Cooper`。**这列决定声量份额，别空着** |
| `model_version` | 当时用的模型版本，如 `GPT-5` / `Claude 4.5`。**必填** |
| `notes` | 任何异常：品牌混淆、答非所问、拒绝回答、用中文答英文问 |

**答完一格立刻记，不要攒一批一起补。** AI 回答不缓存，回头你只记得大意，
`rank` 和 `competitors_seen` 这种精确列会全丢。

### 1.4 四个坑（都会让数据失真）

1. **品牌混淆是常态。** SolarOne Solutions（美国，离网太阳能路灯）会抢先出现在 B1 里。
   `mentioned=y` 但 `spec_ok=n` **完全正常**，这正是要抓的东西，别手软改成 `y`。
2. **数字在、品牌不在。** S1 那条 AI 很可能报得出 2200 lux 却不提我们。
   仍记 `mentioned=n`，`notes` 写"有数字无品牌"。
3. **非英语查询可能用中文答。** 判定 `mentioned` 时中英文品牌名都算，
   但在 `notes` 里写清楚它用什么语言答的。
4. **随机性。** 同一查询两次结果可能不同。B1 / S1 / X1 这三类跑完再跑一次，**取较差值**。

### 1.5 出报告

```bash
cd diag-output/geo-baseline
python geo_round.py report
```

产出 `report-latest.md`：总体指标、分平台、分查询意图、分查询、环比，含 AIVO 综合分。

**如果报告开头列出"数据问题"，先修再读指标**——覆盖率不到 100% 时，
比率只代表已测的那部分，不能当全量结论。

> ⚠️ Excel 存 CSV 会带 BOM，会让首列名变 `\ufeffround`、轮次标签读成空。
> 脚本已经按 `utf-8-sig` 读取并会在 round 列为空时报错，但**存盘时尽量选
> "CSV UTF-8（逗号分隔）"而不是"CSV（逗号分隔）"**。

### 1.6 时间预算

| 阶段 | 时长 |
| --- | --- |
| 准备 + 开 8 个会话 | 10 min |
| 每平台 11 问（问 + 判定 + 记录） | 10–15 min |
| 8 个平台 | **80–120 min** |
| B1/S1/X1 复跑一次 | +15 min |
| C6/X3 扩展 6 行（仅 ChatGPT/Gemini/Perplexity） | +5 min |
| 出报告 + 核对 | 10 min |
| **合计** | **约 2.5–3 小时** |

比预估的 2–3 小时略快，因为粘贴单已经把判定提示写在旁边了。

### 1.7 平台缺口处理（10-23 实测缺口 + 10-24 补测顺序决定）

**不用改任何文件**：CSV 里未测平台的行全部留空，`report` 会自动把未测行
从分母剔除（`mentioned` 留空 = 不适用，不进任何比率，也不报错）。
2026-10-23 已用模拟数据验证：6 平台实测 70 格 / 88 = coverage 80%，
报告总体指标与分平台表全部正常，未测平台显示「0 已测」。

**缺口的影响比想象小，但有一个结构性缺口**：已测 4 平台（ChatGPT /
Perplexity / Grok / DeepSeek）覆盖 Bing 族 2 个、自有族 2 个，**Google 族
为 0**。（2026-10-24 更正：本节原文把 Meta AI 记作 Google 族有误——Meta AI
的网页检索由 Bing 提供，实为 Bing 族；Gemini 才是唯一 Google 族样本。）
Copilot 与 ChatGPT / Perplexity 同族、冗余度最高；但 Google 收录本来就要
等 GSC，round 0 缺 Google 族可接受，补测成本也只是一次代理。

**实际工作量**：70 格（6 平台 × 11 核心 = 66，加 ChatGPT / Perplexity
各多 C6 / X3 = 4），约 2–2.5 小时。

**补测顺序（2026-10-24 定，按障碍从低到高）**：

1. **Copilot**：10-23"打不开"的真因是**需登录微软账号**（不是地区封锁），
   国内直连无需代理。与 Part ② Bing WMT 同一个账号，一举两得。bing 族
   第三样本。
2. **Gemini**：地区封锁，换代理即可访问；`model_version` 列注明地区和
   版本（如 `flash-us`），保证 round 1 可复现。Google 族唯一样本。
3. **Meta AI**：10-24 确认国内不可用（Meta 服务被墙），需代理 + Meta
   账号，摩擦最高排最后；搞不定就记「本轮不可达」，不硬刚。
4. **Claude**：无法登录，记「平台不可达」。

补测时直接填同一份 CSV 的对应行——已测行不用动，报告按新覆盖重算。

---

## Part ②. Bing Webmaster Tools（10 分钟）

**为什么值得做**：ChatGPT 检索 / Copilot / Meta AI 三个都继承 Bing 索引。
我们在 Bing 目前是零存在——这不是内容问题，是压根没在 Bing 那里登记过。
IndexNow 已经推了 354 条 URL，但 WMT 不验证的话，你看不到收录进展，
也没法主动提交。

### 2.1 打开并添加站点

1. 浏览器开 **https://www.bing.com/webmasters**
2. 用 Microsoft 账号登录（没有就注册一个，或用 Google / Facebook 账号授权）
3. 添加站点，填 **`https://www.solaronelighting.com`**（带 https，不带末尾斜杠）

### 2.2 验证所有权 —— 推荐走 DNS，1 分钟搞定

Bing 会给三个选项：

| 方式 | 要不要改代码/部署 | 推荐度 |
| --- | --- | --- |
| **CNAME（DNS 记录）** | **不用** | ✅ **选这个** |
| XML 文件上传 | 要改代码 + 部署 | 备用 |
| meta 标签 | 要改代码 + 部署 | 备用 |

**走 CNAME 的步骤**：

1. Bing 会显示一条记录，形如「主机记录 `xxxx` → 目标 `verify.bing.com`」
   （具体值以屏幕上显示的为准，每人不同）
2. 打开 Cloudflare → 选 `solaronelighting.com` → DNS → 添加记录
3. 类型选 **CNAME**，名称填 Bing 给的主机记录，目标填 `verify.bing.com`，
   代理状态（小橙云）**关掉**，设为"仅 DNS"
4. 保存，回 Bing 点验证

> 关掉代理是因为 Bing 要直接读到这条记录，走了 Cloudflare 代理有时会被挡。
> 如果 Bing 给的是 TXT 记录而不是 CNAME，同样关掉代理。

**如果你不想动 DNS**：告诉我，我用 `gsc_code` 那套现成模式加一个
`BING_VERIFICATION` 环境变量走 meta 标签，改一行模板 + 一处 settings，
你只要在 Vercel 加个环境变量。但要多一次部署，不如 DNS 快。

### 2.3 提交 sitemap

验证通过后，左侧菜单找 **Sitemap**（或"站点地图"）：

1. 输入 `sitemap.xml`（或完整地址 `https://www.solaronelighting.com/sitemap.xml`）
2. 提交

线上已确认 `sitemap.xml` 可访问（59 × 6 语种 = 354 条 URL）。

### 2.4 确认 IndexNow

左侧找 **IndexNow** 一栏。我们的密钥文件已经线上可达，这一步只是让 Bing 知道：

- 密钥文件：`https://www.solaronelighting.com/b662d773724397c2d6eb02109bac5e48.txt`
- 内容就是密钥本身：`b662d773724397c2d6eb02109bac5e48`
- 已实测线上 **200 可达**

如果 Bing 的 IndexNow 页面提示"未检测到密钥"，点一下重新检测即可——
密钥文件不需要注册，IndexNow 是靠爬这个文件自我验证的。

### 2.5 手动提交重点 URL

左侧 **URL 检查**（URL Inspection），逐条输入并点"提交编入索引"：

```
https://www.solaronelighting.com/
https://www.solaronelighting.com/stadium-lighting/
https://www.solaronelighting.com/projects/football/
https://www.solaronelighting.com/projects/tennis/
https://www.solaronelighting.com/products/vsp-xxxxw-9m-yp/
https://www.solaronelighting.com/projects/yuanshen-sports-centre-stadium/
https://www.solaronelighting.com/llm.txt
```

**⚠️ 不要提交这三个地址**——它们是 301，提交了也是浪费时间：

| 旧地址 | 实际 301 到 |
| --- | --- |
| `/sports-lighting/` | `/stadium-lighting/` |
| `/football-stadium-lights/` | `/projects/football/` |
| `/tennis-court-lighting/` | `/projects/tennis/` |

这不是故障，是 v1.10.0（提交 `a0ba31e`）的**有意整合**：原先那三个页面是为关键词硬造的、
没有真实内容支撑，所以 301 到承载同一意图的诚实页面。上面 7 条里第 2/3/4 条就是整合后的
真身，均已实测 200 且有实质内容（H1 分别是 "LED Stadium Lighting" / "Football Field
Lighting" / "Tennis Court Lighting"）。

前 5 条是流量入口，最后两条是这次新增的资产（项目页带 2200 lux 实测数据，
`llm.txt` 是给 AI 的机读摘要）。Bing 对手动提交有配额，别一次刷全站 354 条。

---

## 做完之后的节奏

| 时间 | 做什么 |
| --- | --- |
| 今天 | Part ①（2–2.5 h）+ Part ②（10 min） |
| 2–4 周后 | round 1 复测，和 round 0 对比——那个差值才有归因意义 |
| ≥14 天后 | 复跑 4 条索引查询式（`index-presence-2026-10-23.md`），看 354 条有没有被收录 |

**round 1 之前不要改站内内容**，否则差值归因不干净。实在要改，记下改动日期。

---

## 附：本次会话已交付的文件

| 文件 | 用途 |
| --- | --- |
| `geo-baseline/paste-sheet-round0.txt` | 11 条查询粘贴单，带判定提示 |
| `geo-baseline/retrieval-proxy-2026-10-23.md` | 检索层 10/10 零命中的完整证据 |
| `geo-baseline/rounds/round-0-2026-10-23.csv` | 94 格待测表（88 核心 + 6 扩展，已预填） |
| `geo-baseline/PROTOCOL.md` | 完整规程（本手册的详细版） |
| `geo-baseline/geo_round.py` | 出报告脚本 |
