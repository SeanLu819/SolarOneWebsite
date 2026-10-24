# Perplexity round 0 证据存档（2026-10-24）

数据来源：用户粘贴的 Perplexity Computer 任务线程全文
（https://www.perplexity.ai/computer/tasks/d5a72574-47c4-48bd-9a6b-fd78b5e14f77?view=thread）。
免费额度用尽，仅完成 4 轮（C6/L1/L2/L3），其余 9 格留空不计入。

## ⚠️ 方法偏差（必读）

协议要求的是「在 Perplexity 搜索框逐条原样贴入查询」。本轮实际用的是
**Perplexity Computer（agentic 任务模式）**：它自己规划多步检索、自己追问细化、
输出为结构化表格。与逐条问答的差异：

1. 检索策略不同（多步深度搜索 vs 单轮检索），跨平台可比性有折扣
2. 它会引用自己前几步的发现（阿语轮开头即"استكمالًا لبحثنا السابق"）
3. 免费额度限制导致只跑了 4/13 格，不是随机抽样

结论：本文件数据代表「Perplexity 检索层对我们的可见度」，可作 round 1 对比基准，
但与 ChatGPT 格的横向对比只能说明趋势，不能当精确差值。

## 逐格判定

### C6 — football field lighting manufacturer China（extended，未提及）

Perplexity 答案给出三家中国厂商表格：CHZ Lighting（FL21A 足球泛光 + 场馆仿真）、
MECREE（AFL/R580 系列，供应商自报德国体育场 + 玻利维亚球场案例）、Hishine
（Hi-Shoot，葡萄牙 + 马来西亚项目）。**无 SolarOne。**

- mentioned=n；competitors_seen=`CHZ Lighting;MECREE;Hishine`
- 三家全部带「供应商自报项目案例」——这是它们占据答案的核心素材
- notes：Computer agent 任务模式

### L1 — مورد إضاءة ملاعب رياضية LED（core ar，提及，排 4/4）

答案续接前序搜索，列出四家：CHZ / MECREE / Hishine / **SolarOne（北京）**。
SolarOne 描述：RT410 系列（260W，130 lm/W）、VSP 系列（至 4200W，电视转播）、
M 系列（至 1280W）。

- mentioned=y；rank=4；sentiment=neu（名单罗列无推荐语气，排最后）
- spec_ok=**y**：与 seed_data.json 逐项核对全对——
  RT410 `Power=260W / Efficacy=130lm/W`；VSP-4200W `System Wattage=4200W`；
  M Series `80~1280W+`
- cited_own=**留空**：粘贴文本未附引用链接，不猜（协议：空=不适用）
- 意义：**规格全部取自站内 spec 表的 130lm/W**，而 ChatGPT 同查询自己算成 125
  ——再次坐实站内「130 vs 32500/260=125」的自相矛盾

### L2 — LED Stadionbeleuchtung Hersteller（core de，未提及）

主名单为国际四强：Musco（Control-Link）、Signify/Philips（ArenaVision + Interact
Sports）、Ephesus（LumaSport + AirMesh）、Schréder（OMNIBLAST，FIFA Quality Pro）。
追问句"Falls Sie weiterhin Hersteller aus China suchen"仅补 CHZ/MECREE/Hishine，
**无 SolarOne**。

- mentioned=n；competitors_seen=`Musco;Signify;Ephesus;Schreder;CHZ Lighting;MECREE;Hishine`

### L3 — fournisseur éclairage LED stade sportif（core fr，未提及）

结构与 L2 完全相同：国际四强主导 + 中国三强补充，**无 SolarOne**。

- mentioned=n；competitors_seen 同 L2

## 与 ChatGPT 的交叉对比（本轮最大发现）

| 查询 | ChatGPT（bing 族） | Perplexity（bing 族） |
| --- | --- | --- |
| C6 football field lighting mfr China | 提及，3/3 | **未提及** |
| L1 阿语 | 提及（正文乱码缺失） | 提及，4/4，规格全对 |
| L2 德语 | 提及，3/3 | **未提及** |
| L3 法语 | 提及，3/3 | **未提及** |

同族索引（都挂 bing）差异却极大 → Perplexity Computer 的检索源与 Bing 网页索引
重叠度低。Perplexity 答案的厂商素材几乎全部带「项目案例」（德国体育场、葡萄牙、
马来西亚、玻利维亚）——外域电商/目录页的案例内容在它的检索里权重远高于独立站。

**行动含义（round 1 后再动手，现在记着）**：

1. 根因仍是索引存在性：`site:solaronelighting.com` 零结果（10-23 实测），
   IndexNow/Bing WMT 覆盖 bing 直系，Perplexity 的源要等它自己抓
2. MIC / GlobalSources 资料页更新（进行中）可能是对 Perplexity 最直接的杠杆——
   CHZ/MECREE/Hishine 正是靠在那些渠道的案例内容占据它的答案
3. 我们的 /projects/ 实测照度数据是比"供应商自报案例"更硬的素材，问题是
   Perplexity 的检索还抓不到——这又回到收录问题，不是内容问题

## Perplexity 平台成绩（4 格）

| 指标 | 值 |
| --- | --- |
| 提及率 | 1/4 = 25% |
| 平均排名 | 4.00 |
| 数据准确 | 100%（1 格可判定） |
| 声量份额 | 25% |
| AIVO | 49.1（较差） |
