# Perplexity round 0 证据存档（2026-10-24）

数据来源：用户粘贴的 Perplexity Computer 任务线程全文
（https://www.perplexity.ai/computer/tasks/d5a72574-47c4-48bd-9a6b-fd78b5e14f77?view=thread）。
免费额度用尽，线程共产出 10 格（B1/B2/C1/C2/C3/C5/C6/L1/L2/L3，其中 B1/C3/C5 于
2026-10-24 补帖入库）；X1/X3 用户确认无法进行（永久留空，按协议从分母剔除），仅剩 S1 待补。

## ⚠️ 方法偏差（必读）

协议要求的是「在 Perplexity 搜索框逐条原样贴入查询」。本轮实际用的是
**Perplexity Computer（agentic 任务模式）**：它自己规划多步检索、自己追问细化、
输出为结构化表格。与逐条问答的差异：

1. 检索策略不同（多步深度搜索 vs 单轮检索），跨平台可比性有折扣
2. 它会引用自己前几步的发现（阿语轮开头即"استكمالًا لبحثنا السابق"）
3. 免费额度限制导致只跑了 10/13 格，不是随机抽样

结论：本文件数据代表「Perplexity 检索层对我们的可见度」，可作 round 1 对比基准，
但与 ChatGPT 格的横向对比只能说明趋势，不能当精确差值。

## 逐格判定

### B1 — SolarOne stadium lights（core en，提及，排 1，spec_ok=n）

答案是一段消歧式介绍，把 "SolarOne" 拆成多个实体，其中与体育场照明相关的两个：

1. **"SolarOne Lighting (LED sports lighting)"**——2007 年起、500+ 项目、50+ 国家、
   five continents、50%+ 节能、5+ 保修；"compact modular luminaires and
   stadium-grade high-bay systems, featuring precision optics and modular
   architecture"
2. **"Beijing Solarone Energy Technology"**——被称作 "a related company with
   the same name"，项目引用归在它名下：Beijing Olympic stadium (fencing
   and swimming)、China National Tennis Center、projects in Sweden, France,
   and Canada

另消歧 SolarOne Solutions（Needham, MA，2019 年被法国 Fonroche 收购，
"not a stadium-lighting brand"）和一批消费级 "Solar One" 零售商。

- mentioned=y；rank=1（品牌查询，我们是被答主体，与 B2 先例一致）；sentiment=pos
- spec_ok=**n** —— 用 verify_b1_claims.py 对 seed_data.json + llm.txt 逐项核对：
  - **公司级数据全部真实**：2007 / 500+ 项目 / 50+ 国家 / five continents /
    50%+ 节能 / 5+ 保修 / precision optics / modular / Olympic training
    centers / community football pitches 全部站内有据，其中 "five
    continents…Olympic training centers…community football pitches" 与
    seed `projects_subtitle` 近乎逐字吻合
  - **项目引用大部分真实但名称压缩错位**："Beijing Olympic stadium
    (fencing and swimming)" 实为武汉 CISM 击剑馆 + 北京英东游泳馆 + 北京
    奥林匹克体育中心体育馆三个项目的错拼；"China National Tennis Center"
    对应国家奥林匹克体育中心网球馆 / 北京国际网球中心
  - **幻觉两项**："projects in Sweden, France, and Canada"——法国真
    （Andre Vacheresse / Narbonne 两个项目），**瑞典、加拿大在 seed 22 个
    项目 + llm.txt 全文零命中**（seed 项目只分布在北京×9 / 法国×2 / 美国×8
    / 杭州 / 上海 / 武汉）
- **新 GEO 风险：品牌实体拆分**。AI 把品牌名（SolarOne Lighting）和注册名
  （Beijing Solarone Energy Technology）当成两家 "related" 公司，站内内容
  被劈成两半——公司 stats 归给 phantom "SolarOne Lighting"，项目引用归给
  注册名。买家搜品牌名拿到的是一个 fragmented 画像。这与 B2 的幻觉是不同
  物种：事实都是我们的，但身份被拆了。
- competitors_seen 留空（SolarOne Solutions/零售商是同名撞车实体，不是
  品类竞品，与 B2 及 ChatGPT B1/B2 先例一致）
- cited_own 留空：粘贴未附引用链接

### B2 — SolarOne LED sports lighting manufacturer（core en，提及，排 1，spec_ok=n）

Perplexity 给出整段品牌介绍：Beijing Solarone Energy Technology Co., Ltd.，2007 年成立，
顺义区，50+ 国家 500+ 项目；产品线表格（RT410 260W/130lm/W/32,500+lm、VSP 至 4200W、
RT180FS–RT420FS、High Bay 130W、M Series 80–1,280W+）；项目清单；认证与条款。
**主动消歧**："this is a different company from SolarOne Solutions Inc. of Needham,
Massachusetts — the US solar street-light maker acquired by France's Fonroche in 2019."

- mentioned=y；rank=1；sentiment=pos（专段正面介绍）
- spec_ok=**n** —— 与 seed/llm.txt 逐项核对后，**公司级数字和产品规格全对**
  （2007、500+ projects、50+ countries、RT410/VSP/M 全部规格、5+ warranty、50%+
  energy saving、顺义区新地址均在 llm.txt/contact.html 有据），**但两处站内不存在**：
  1. 项目清单里的 "Karlstad, Sweden football court" 和 "Paris tennis court"——
     seed 22 个项目 + llm.txt 全文零命中（站内法国项目是 Roanne 的 Halle André
     Vacheresse 体育馆，无巴黎、无网球场、无瑞典项目）
  2. 认证清单 "ISO9001, CE, RoHS, TUV, and UL testing"——ISO9001/RoHS/TUV 三项
     站内从未声明（站内认证体系是 UL/DLC/GS/CE/IP66）
- **这是本轮最重要的 GEO 风险发现**：AI 在品牌查询里会主动"补全"站内从没说过的话。
  认证是敏感领域——它替我们声明的三项认证一旦被买家追问，我们无法兑现。
  Perplexity 自己给这句加了 hedge（"are stated to pass"），但它确实说出口了。
- competitors_seen 留空（答案主体是我们，末句 "compare against Musco or Signify"
  是追问建议不是名单，与 ChatGPT B1/B2 行先例一致）

### C1 — best LED stadium light manufacturers（core en，提及，排 5）

主名单国际四强：Musco（Control-Link、LA28 官方指定）、Signify/Philips（ArenaVision
Gen 3.5 FIBA 认证）、Ephesus（LumaSport+AirMesh）、Schréder（OMNIBLAST FIFA
Quality Pro）。关于我们的表述在四强之后的附注段：

> On SolarOne, which you asked about earlier — it's a Chinese manufacturer with
> modular floodlight lines and a broadcast-focused VSP series, but the brands
> above have deeper verified track records at major international venues.

- mentioned=y；rank=5；sentiment=neu（承认产品线存在，但明言"国际场馆验证记录
  不如四强"——客观相对劣势陈述，与 ChatGPT X1/X3 先例判定标准一致）
- spec_ok=na（答案主体是别家，未引用我们的规格数字）
- competitors_seen=`Musco;Signify;Ephesus;Schreder`

### C2 — LED sports field lighting supplier China（core en，提及，排 5）

五家供应商表格：CHZ Lighting（2013）、AGC Lighting（37,350 m² 深圳厂+越南厂）、
MECREE、Hishine、**SolarOne**。开头措辞值得注意：
"Here are four verified China-based suppliers with dedicated sports field lighting
lines, **plus SolarOne from earlier**"——前四家属"verified"，我们被放在 verified
名单之外（承接前文的定位）。

- mentioned=y；rank=5；sentiment=neu
- spec_ok=**y**：RT410 (260 W)、VSP broadcast series (4,200 W)、M-series modular
  up to 1,280 W+、Beijing (Shunyi District) 全部与站内一致
- competitors_seen=`CHZ Lighting;AGC Lighting;MECREE;Hishine`
- 注意 AGC Lighting 是 ChatGPT 侧没出现过的新竞品

### C3 — LED high mast flood light manufacturer（core en，提及但被踢出名单，spec_ok=n）

三家中国高杆厂商表格：AGC Lighting（HiMast 300/600/900 W，IP66/IK08，独立旋转模组）、
MECREE（100–5,000 W，160 lm/W，IP66）、Hishine（Hi-Robot 模组 + Hi-Titan 300–1,500 W）。
关于我们的只有一句剔除说明：

> CHZ Lighting and SolarOne from the earlier sports-lighting shortlist
> don't show a dedicated high-mast product line on their sites, so I left
> them off this list.

- mentioned=y（被点名）；rank 留空（不在名单内）；sentiment=neu（客观陈述语气）
- spec_ok=**n** —— **这句是假否定，且是本轮最有业务杀伤力的发现**。
  `grep -i 'mast' seed_data.json` 证明站内明明有整条高杆线：
  - FL6M 480 W："built for **high-mast** and large-area sites such as
    airports and interchange lighting"（SEO 描述："for high-mast yards,
    aprons and airports"）
  - FL16M 1280 W："built for the most demanding **high-mast** and stadium
    applications"（SEO 描述："for the largest high-mast sites"）
  - FL12M 1000 W：德语描述 "an hohen **Masten**"（高杆）
  - 外加新闻案例 `low-cct-high-cri-high-mast-led-retrofit`：FL6M 高杆族替换
    天津滨海国际机场机坪旧金卤灯
  AI 对买家说"这家没有高杆产品线"——而 FL6M 480W 正好落在它列的竞品功率带
  （300–1,500W）里，连应用场景（机场机坪）都和 MECREE 列出的完全重合。
  **这是检索失败的直接证据**：不是内容缺失，是 Perplexity 检索没抓到站内
  已有内容（与 `site:solaronelighting.com` 零结果同根）。与 B1/B2 的幻觉
  互为镜像——那边是"没检索到就编"，这边是"没检索到就说没有"。
- competitors_seen=`AGC Lighting;MECREE;Hishine;CHZ Lighting`（CHZ 同在剔除句里被点名）

### C5 — football stadium LED lighting supplier（core en，未提及）

三家 "verified" 中国供应商：CHZ Lighting（FL21A 足球泛光 + FL32/FL38 模组泛光，
附照明仿真支持）、MECREE（AFL 1000/1200W + R580 1500W；自报德国足球场 48×AFL，
105×68 m 场地 / 25 m 安装；玻利维亚 80×R580）、Hishine（Hi-Shoot；自报葡萄牙
480W、马来西亚 320W 足球场；Hi-Titan 至 1500W）。**无 SolarOne。**

- mentioned=n；competitors_seen=`CHZ Lighting;MECREE;Hishine`
- 同查询 ChatGPT 排 **1/5**（五家短名单第 1）——同族索引差异再添一例
- 开头 "Continuing our China sourcing" 说明它沿用自己的前序短名单，
  我们从头到尾没进过那个名单

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
| B1 品牌查询 | 提及（规格对，功效 125 与站内 130 打架） | 提及，排 1；公司数据全对，但瑞典/加拿大项目幻觉 + 拆成两个实体 |
| B2 品牌查询 | 提及（2007/北京/50+国家全对） | 提及，排 1，但**幻觉认证与项目** |
| C1 best manufacturers | 提及，5/7 | 提及，排 5，"记录不如四强" |
| C2 China suppliers | 提及，**1/3** | 提及，5/5，verified 名单外 |
| C3 high mast | 提及，2/n（HISHINE 为主，我们次选） | 提及但被剔除，理由是**假否定**（站内确有 FL-M 高杆线） |
| C5 football supplier | 提及，**1/5** | **未提及** |
| C6 football field mfr China | 提及，3/3 | **未提及** |
| L1 阿语 | 提及（正文乱码缺失） | 提及，4/4，规格全对 |
| L2 德语 | 提及，3/3 | **未提及** |
| L3 法语 | 提及，3/3 | **未提及** |

同族索引（都挂 bing）差异却极大 → Perplexity Computer 的检索源与 Bing 网页索引
重叠度低。Perplexity 答案的厂商素材几乎全部带「项目案例」（德国体育场、葡萄牙、
马来西亚、玻利维亚）——外域电商/目录页的案例内容在它的检索里权重远高于独立站。
同一查询在 ChatGPT 排第 1（C2）在 Perplexity 排第 5，也是这个机制的直接体现。

**行动含义（round 1 后再动手，现在记着）**：

1. 根因仍是索引存在性：`site:solaronelighting.com` 零结果（10-23 实测），
   IndexNow/Bing WMT 覆盖 bing 直系，Perplexity 的源要等它自己抓
2. MIC / GlobalSources 资料页更新（进行中）可能是对 Perplexity 最直接的杠杆——
   CHZ/MECREE/Hishine 正是靠在那些渠道的案例内容占据它的答案
3. 我们的 /projects/ 实测照度数据是比"供应商自报案例"更硬的素材，问题是
   Perplexity 的检索还抓不到——这又回到收录问题，不是内容问题
4. **幻觉风险的处置**（B2 的 ISO9001/RoHS/TUV/Karlstad/Paris，B1 的
   Sweden/Canada）：AI 替我们说的话我们无法控制，但可以在站内提供**更结构化
   的否认/澄清素材**（如 llm.txt 里已有的品牌消歧段），并监控第三方目录站——
   幻觉往往混合了站外陈旧内容。认证领域宁可 AI 少说，不可多说。
5. **实体拆分处置**（B1 新发现）：llm.txt / JSON-LD 的消歧段只区分了美国
   SolarOne Solutions，没有把「SolarOne Lighting = Beijing Solarone Energy
   Technology = 同一法人」说死。round 1 前可在 llm.txt 增加显式同一实体声明，
   观察 AI 是否收敛为单实体画像。
6. **C3 假否定的业务代价**（本轮新增）：买家搜 "LED high mast flood light
   manufacturer"，AI 主动告诉他们 SolarOne 没有高杆产品线——而 FL6M/FL16M
   正在售。收录问题的代价从"不被提及"升级为"被错误描述"。round 1 复测此
   查询是验收索引修复的第一观测点；短期可在 llm.txt 产品清单里把 FL-M 系列
   的高杆定位写得更显式（现在散在各产品描述里）。

## Perplexity 平台成绩（10 格）

| 指标 | 值 |
| --- | --- |
| 提及率 | 6/10 = 60% |
| 平均排名 | 3.20 |
| 数据准确 | 40%（5 格可判定：C2/L1 对，B1/B2 幻觉 + C3 假否定） |
| 声量份额 | 60% |
| AIVO | 57.6（较差） |
