# DeepSeek 分享链接证据存档 — GEO round 0（2026-10-24）

- **来源**：https://chat.deepseek.com/share/8poyw8gocjhn24vm0k
- **提取路径**：分享页为客户端渲染（初始 HTML 仅 9KB app shell，且沙箱直连返回
  HTTP 429 Request Blocked）。数据端点从 CDN JS chunk 扒出：
  `GET https://chat.deepseek.com/api/v0/share/content?share_id={id}`
  （需浏览器 UA + Referer，走 Clash 代理），返回 175KB JSON。
- **数据结构**：24 条消息 = 12 个人类查询 + 12 条回复，按 `inserted_at` 排序还原。
  每条回复含 SEARCH fragment（`queries` 子查询 + `results` 检索页全列表）与
  RESPONSE fragment（正文，`[citation:N]` 标记但分享导出不带 URL）。
- **model_version**：分享 API 的 `model` 字段全部为空，**未记录**——需在原会话问
  "what model are you using" 补（同 ChatGPT 分享页的限制）。
- **重复提问**：用户将 C1（best LED stadium light manufacturers）与 L2（LED
  Stadionbeleuchtung Hersteller）各跑了两轮，两轮结果一致（均零提及），CSV 记录
  每对的最后一轮。

## 总体检索统计（12 轮）

- 检索页总计 **178 页**，**solaronelighting.com 出现 0 次**。
- 品牌查询的检索源全部是 2016-2017 年的第三方页面：体博会参展档案
  （cn.sportshow.com.cn 2016/2017）、alighting B2B 旧 listing、
  北京政府采购网（2017）、百度百科、天眼查，以及一个美国市议会 PDF。
- B1 轮 AI 自发猜测本站域名为 `site:solar-one.com.cn`（体博会档案里 2016 年
  留下的旧域），该域与 2017 年档案里的 `solai-one.com.cn` **均已 502 失效**
  （2026-10-24 实测）。现行站 solaronelighting.com 从未进入任何一轮检索结果。

## 逐格判定

### B1 — SolarOne stadium lights（mentioned=y / rank 空 / pos / cited_own=n / spec_ok=n）

答案正确锁定 **Beijing SolarOne（北京信能阳光新能源科技有限公司）**——体博会
2016（品牌 solarone，展位 07A606）/2017（信能阳光 Solarone）参展档案佐证——
并正确消歧美国 SolarOne Solutions（离网太阳能路灯）。但所有细节均来自
2016-17 年第三方页面，与当前 seed 全部对不上：

| B1 答案声明 | seed 核对 |
| --- | --- |
| 工人体育馆篮球场 48×180W 换 400W 金卤，200 lux / 0.65 / 节能 60% | ❌ MISS |
| 对外经贸大学篮球馆 100/200W 换 400W，750 lux / 0.83 / 71% / +150% | ❌ MISS |
| 大连郁顿空气膜篮球馆 58×400W，500+ lux / 0.76 | ❌ MISS |
| 法国 HD 转播篮球馆 RT200-9M，地面 3000 lux / 垂直 1800 lux | ⚠️ 项目真、数字假：seed 法国项目是 Roanne Halle André Vacheresse（篮球馆，Halle 是 Chorale Roanne Basket 主场），实际用灯 **Vision Smart FL9M-720W**，结果 ">2000 lux"；seed 无 RT200-9M 型号 |
| RT590ST：80W~140W / 100 lm/W / 2700K~7000K / IP65 / 50000h | ❌ 来自 alighting 旧 B2B listing（标题即 "solar one 大功率LED强光投射灯80W-140W"，该页现已 404）；seed 无 RT590ST 型号（现行 RT 家族：RT410 260W/RT590FL-S 160W/RT390FL 80W/RT400HB 130W/RT500HB 280W/RT220UB 40W/RT420FS-S 100W/RT410-RGBW 200W/RT600SL-T 120W/RT820SL-T 240W），且现行防护等级为 IP66 非 IP65 |

判定 spec_ok=n：身份对、细节全部来自过期第三方（可能是公司早期真实项目，
但已不在当前站点——属于"我们自己的旧内容"，性质是陈旧而非纯幻觉）。

### B2 — SolarOne LED sports lighting manufacturer（mentioned=y / rank 空 / **neg** / cited_own=n / spec_ok=n）

🔴 **全轮最严重发现——信用风险指控**。答案以 "⚠️ Important Risk Alert" 开头：
公司 "has been listed as a **dishonest debtor**, having new **tax arrears**
announcements, and being subject to **consumption restriction orders**"，
来源百度百科 + 天眼查（企业征信记录），并建议买家合作前经天眼查/企查查核实。

**必须由用户确认的事项**：本轮检索结果里天眼查出现了**三家**带"信能阳光"的
注册实体——北京信能阳光**新能源科技**有限公司（/company/11158553）、
北京信能阳光**节能科技**有限公司（/company/5503137664）、北京信能阳光
**绿色照明器材科技**有限公司（/company/35223161）。失信记录归属哪一家、
是否确为本公司（llm.txt 注册名 Beijing Solarone Energy Technology Co., Ltd.），
只有业务方能核实。若记录属于同名实体，这是 AI 张冠李戴；若确属本公司，
这是需要在 round 1 前严肃应对的舆情危机——B2 与 X1 两轮都在重复它。

三个项目引用倒是真实的（均与 seed 对上）：CBA 北京控股男篮主场 → seed
`olympic-sports-center-gymnasium-beijing`；2022 冬奥速滑 → seed
`national-snow-and-ice-research-center`（400m 速滑馆 2000 lx）；国家奥体
击剑馆 → seed `fencing-venue-of-the-7th-cism-military-world-games`。
但"参与起草国家体育场馆照明标准"站内无此声明。spec_ok=n。

### C1 — best LED stadium light manufacturers（mentioned=n，两轮一致）

两轮均零提及。名单来自 2026 市场报告（gminsights / 168report / qyresearch）：
Musco（FIFA Quality Pro + 首选供应商）、Signify（2025 份额 12%+）、Cree
（1900K 低蓝光）、Acuity（M3 Innovation/MAKO 模块化）、另提 SITECO /
Ephesus(Eaton) / Hubbell / Zumtobel。同查询 ChatGPT 排 1/5。

### C3 — LED high mast flood light manufacturer（mentioned=n）

零提及——**连点名剔除都没有**，与 Perplexity C3 的假否定
（"don't show a dedicated high-mast product line"）互为镜像：一个编造我们没有，
一个根本不知道我们。名单：Philips / OSRAM / CREE + 中国 WOSEN / iShineLux /
UNIKE（200-1500W，170 lm/W，IP66）。FL-M 高杆线（FL6M 480W high-mast、
FL16M 1280W、天津滨海机场高杆改造新闻）在 DeepSeek 检索层完全不可见。

### C5 — football stadium LED lighting supplier（mentioned=n）

零提及。答案以 **FIFA 认证为硬筛选门槛**：Signify / Musco（FIFA Preferred
Provider）+ Thorn Altis / Schréder OMNIBLAST（FIFA Quality Pro）。我们无 FIFA
认证且站内不声称（体系为 UL/DLC/GS/CE/IP66）——在此筛选逻辑下结构性出局。
同查询 ChatGPT 排 1/5。

### L1 — مورد إضاءة ملاعب رياضية LED（mentioned=n）

查询以 GBK→UTF-8 乱码到达（同 ChatGPT L1 遭遇），DeepSeek 仍输出完整阿拉伯语
答案，可判定。**最值得注意的一轮**：AI 的自发子查询里出现了
`"SolarOne" 北京信能阳光 体育场馆照明`，且 29 页检索结果确实摸到了我们的三页
档案（sportshow / tianyancha / alighting）——**检索层摸到过、答案层没写**。
答案列 FIFA 双雄 + 中国 MECREE（AFL 250-2400W，160-180 lm/W）/ LEDLUCKY。

### L2 — LED Stadionbeleuchtung Hersteller（mentioned=n，两轮一致）

两轮均零提及。Lumosa（德国，60,000 盏，UEFA Level B 项目）+ Signify/Musco +
中国 LEDLUCKY / Lamp Shining / UNIKE / 华夏北斗星（周明集团）/ ROKEE。同查询
Perplexity 亦未提及，仅 ChatGPT 提及 3/3。

### L3 — fournisseur éclairage LED stade sportif（mentioned=n）

零提及。Signify（FIFA 指定供应商）+ Schréder（OMNIBLAST FIFA Quality Pro）+
中国 LEDLUCKY（ArenaSharp E 480-2200W / VariFlood GEN II）。

### S1 — stadium lighting 2200 lux AFC（mentioned=n）

纯 AFC 标准解读并**纠正查询前提**：2200 lux 不对应任何 AFC 等级（Cat1 水平
2400/垂直 1200，Cat2 2000/1100，Cat3 1800/1000；2200 落在 Cat2 与 Cat1 之间），
附韩国仁川联升级 2500+ lux 案例。零品牌提及（同 ChatGPT S1）。

### X1 — Musco vs SolarOne stadium lighting（mentioned=y / rank=2 / **neg** / cited_own=n / spec_ok=n）

开篇定调 "**not a comparison between peers**"：Musco 优先（FIFA 首选供应商、
2026 世界杯 12/16 场馆、25 年保修）；我们被描述为 "domestic Chinese
manufacturer with project experience **primarily in basketball courts and
training facilities**"，重复 B2 的失信/欠税/限消指控，结论 "**highly
questionable partner**"。

| X1 声明 | seed 核对 |
| --- | --- |
| primarily basketball courts and training facilities | ❌ 与 22 项目矛盾：football-field-led-retrofit / 奥体足球场 / 棒球场 / 网球×2 / 滑雪村 / 自行车馆 / 卡丁车 / 市政道路 / 首都机场 / 4 所美国学校均在列 |
| 无 FIFA Quality Pro / Preferred Provider | ✅ 属实（站内不声称，体系 UL/DLC/GS/CE/IP66） |
| 最高光是法国篮球馆 HD 转播、非足球场 | ⚠️ 半对：Roanne 确是篮球馆，但项目是多功能馆（篮球+网球联合会杯），且 AI 在 B1 给的型号/数字全错 |
| 失信被执行人/欠税/限制消费令 | ⚠️ 同 B2，来源百度百科/天眼查，**待用户核实**（三家信能阳光实体） |

同查询 ChatGPT 排 2/2 且 spec_ok=y——DeepSeek 是唯一给出负面对比结论的平台。

## 四平台交叉对比

| 查询 | ChatGPT | Perplexity | Grok | DeepSeek |
| --- | --- | --- | --- | --- |
| B1 品牌 | 提及，规格对（RT410 125 vs 130 站内打架） | 提及 1/1，实体拆分+瑞典加拿大幻觉 | 撞车惨败（美国 Fonroche 拿走答案） | 提及，身份对但细节全来自 2016-17 旧页 |
| B2 品牌专段 | 提及，全对 | 提及 1/1，Karlstad/Paris 幻觉+虚构认证 | 提及 1/1，**全对**（唯一 cited_own=y） | 提及但**信用风险警报**（待核实） |
| C1 全球最佳 | 提及 1/5 | 提及 5/5 附注 | 提及（表格外附注） | 零提及 |
| C3 高杆 | — | 提及但假否定（FL-M 不可见） | 零提及 | 零提及 |
| C5 足球场供应商 | 提及 1/5 | 零提及 | 零提及 | 零提及 |
| L1 阿拉伯语 | 提及（正文乱码缺失） | 提及 4/4 | 零提及 | 零提及（但检索层摸到过档案） |
| L2 德语 | 提及 3/3 | 零提及 | 零提及 | 零提及 |
| L3 法语 | 提及 3/3 | 零提及 | 零提及 | 零提及 |
| S1 AFC 标准 | 零提及 | 未跑 | 零提及 | 零提及 |
| X1 对比 | 提及 2/2，spec 全对 | 无法进行 | 提及 2/2，spec 全对 | 提及 2/2，**负面碾压+信用指控** |

**跨平台规律**：三个"自有索引族"平台（Grok/DeepSeek）对本站的检索覆盖全部
为零——Grok 靠模型知识（B2 全对但 cited 只有一次），DeepSeek 靠 2016-17 旧
第三方页（细节全过期）。ChatGPT（bing）是唯一稳定检索到本站的平台。

## DeepSeek 平台成绩（10 格）

| 指标 | 值 |
| --- | --- |
| 提及率 | 3/10 = 30% |
| 平均排名 | 2.00（仅 X1 一格有排名） |
| 引用本站 | 0/3 = 0%（178 页检索零出现） |
| 数据准确 | 0/3 = 0%（B1 旧页细节 / B2 信用指控 / X1 负面论断，三项均与当前站不符或不可验证） |
| 声量份额 | 33% |
| AIVO | **25.3（较差，四平台最低）** |

四平台排序：ChatGPT 90.1（优秀）> Perplexity 57.6（较差）> Grok 46.9（较差）
> DeepSeek 25.3（较差）。

## round 1 行动项（由本轮产生）

1. 🔴 **信用记录核实（最高优先级，用户侧）**：天眼查/企查查确认失信记录归属
   哪家"信能阳光"实体。若张冠李戴 → 在 llm.txt 强化注册名+统一社会信用代码
   级消歧；若确属本公司 → 舆情处置优先级高于一切 GEO 优化。
2. **本站域名进索引**：178 页零出现说明 DeepSeek 索引根本没有本站。旧域
   solar-one.com.cn / solai-one.com.cn 已 502——若还能续费，301 到现行站；
   同时检查 Bing/Google 对 solaronelighting.com 的收录状态（BingWMT 计划）。
3. **B1 旧内容清理或更新**：alighting listing（80-140W 旧规格）已 404 但仍在
   索引；体博会档案带旧地址（东城区）。考虑向这些第三方更新资料或屏蔽。
4. **L1 悖论利用**：DeepSeek 检索层能摸到我们的中文档案（子Query 自带
   "SolarOne 北京信能阳光"）——中文世界认知存在，缺的是权威可索引的现行内容。
5. **FL-M 高杆线**继续作为 round 1 索引修复观测点（Perplexity 假否定 +
   DeepSeek 零提及双证据）。
6. **model_version 补录**：原会话问 "what model are you using"。
