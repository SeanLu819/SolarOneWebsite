# Grok round 0 证据存档（2026-10-24）

数据来源：用户分享链接
<https://grok.com/share/bGVnYWN5LWNvcHk_849802a6-ce0e-4f0f-baa4-5e468a2799d9>
经 `https://grok.com/rest/app-chat/share_links_data/{shareId}` API 提取
（沙箱直连被拦，走 Clash 代理 `http://127.0.0.1:7897`）。22 条 response =
11 个人类查询 + 11 条 grok-3 回复，按 createTime 排序还原。
11 格全部实测，时间跨度 2026-10-24 12:38–13:27 UTC。

**模型版本：全部 11 轮均为 `grok-3`**（response.model 字段直读，分享页不暴露
但 API 数据带）。

## ⚠️ 方法说明

1. Grok 分享页是 Next.js 客户端渲染，初始 HTML 不含对话内容；数据从
   `rest/app-chat/share_links_data` 端点拉取（该路径从 CDN JS chunk 里扒出）
2. 内联引用是 `<grok:render card_type="citation_card">` 卡片，citation_id
   在 B1/B2/C1 三轮能映射到 webSearchResults  URL，其余轮正文无内联引用
   （Grok 大部分轮次直接给答案不出链接——11 轮里只有 3 轮有内联引用）
3. L1 阿拉伯语查询**以乱码态到达 Grok**（与 ChatGPT L1 同一遭遇：查询被
   GBK→UTF-8 双重编码），Grok 自行还原了查询并用阿拉伯语作答，
   webResults=0（纯模型知识，未检索）

## 逐格判定

### B1 — SolarOne stadium lights（core en，提及，spec_ok=n）——品牌撞车惨败

答案主体是**美国 SolarOne Solutions**：2004 年马萨诸塞成立、SO-Bright 技术、
2019 年被法国 Fonroche 收购、约 2020 年 rebrand 为 Fonroche Lighting
America，主推离网太阳能 LED 区域照明。只在结尾有一个注脚：

> **Note:** There is a separate Chinese company (Beijing Solarone Energy
> Technology) that produces LED sports field/high-mast lights (grid-powered
> options), but this is distinct from the U.S. SolarOne/Fonroche lineage.

- mentioned=y（品牌名出现，注脚也提到我们且描述准确）；rank 留空
  （答案主体是美国公司，我们在结尾注脚，不在任何名单里）；sentiment=neu
- spec_ok=**n** —— 答的是另一家（操作手册 B1 坑位明文：品牌撞车时
  mentioned=y 但 spec_ok=n）；6 条内联引用全部指向美国方域名
  （devex / altenergymag / edisonreport / fonrochesolarlighting 等），
  本轮 87 条检索结果里 solaronelighting.com 零命中
- cited_own=n
- **这是三平台 B1 最差结果**：ChatGPT 和 Perplexity 的 B1 都正确提及我们，
  Grok 把整个答案给了美国同名公司

### B2 — SolarOne LED sports lighting manufacturer（core en，提及，排 1，spec_ok=y）——三平台第一个全对品牌答案

答案正确锁定 solaronelighting.com。逐项对 seed 核对：

| Grok 声明 | 站内证据 |
| --- | --- |
| active since 2007 | llm.txt ✓ |
| 500+ projects / 50+ countries / 5+ year warranties / 50%+ savings | llm.txt ✓ |
| M Series ~80 W（1 模组）→ 1280 W+（16+ 模组），~130 lm/W | seed `80~1280W+` ✓ / "16 Module" ✓ / 130lm/W ✓ |
| VSP up to ~4200 W，Vision Strobe Protection | seed VSP 4200W ✓ / "Vision Strobe Protection-System" ✓ |
| 光学 12°/18°/30°/50° | seed 型号代码表 "12=12° 18=18° 30=30° 50=50°" ✓ |
| UL listing + DLC qualification | 站内认证体系 ✓（UL/DLC 在 10 个产品 slug 上声明） |
| Olympic facilities（fencing, swimming, tennis）项目 | seed 击剑馆/英东游泳馆/两个网球项目 ✓ |
| 主动消歧美国 SolarOne Solutions（2004/Fonroche） | llm.txt 消歧段 ✓ |

- mentioned=y；rank=1；sentiment=pos；spec_ok=**y**（全部声明有据）；
  cited_own=**y**（正文给出 `[solaronelighting.com](https://www.solaronelighting.com/)` 链接）
- **但实体拆分仍在**："A related Chinese manufacturer is **Beijing Solarone
  Energy Technology Co., Ltd.** (est. ~2007, Beijing) ... The solaronelighting.com
  brand **appears closely aligned** with this manufacturer's sports-lighting
  focus."——又一次把品牌名和注册名当成两家（Perplexity B1 同款），只是这次
  用了 hedge 措辞。两个平台复现，这不是偶然了。

### C1 — best LED stadium light manufacturers（core en，未提及）

全球五强表：Signify #1、Musco #2、Cree #3、Acuity #4、Eaton #5；另有
Zumtobel/Thorn、Hubbell、GE Current、Schréder；中国段只列 GS Light、
Lepower、LEDYi、Romanso。**无 SolarOne。** 3 条内联引用无本站，本站域名
不在本轮 35 条检索结果中。

### C2 — LED sports field lighting supplier China（core en，提及，表外补段）

十家中国供应商表格（Huadian / Mecree / GS Light / LEDYi / Romanso / ONOR /
Hishine / Benwei / RC 等），**我们不在表内**，但末尾补了一段：

> Earlier in related searches, **Beijing Solarone Energy Technology** (and the
> solaronelighting.com brand) also appears as a supplier of high-power LED
> sports field and stadium floodlights with project references including
> Olympic-related venues.

- mentioned=y；rank 留空（表外提及）；sentiment=neu；spec_ok=na（提及但
  无规格数字，归属正确——奥运项目引用真实）；cited_own 留空（正文无引用）
- 注意措辞 "Earlier in related searches"——这个提及来自**同会话前序轮次
  （B2）的检索**，不是本轮检索（本轮 35 条结果无本站域名）
- 同查询 ChatGPT 排 1/5、Perplexity 排 5/5，Grok 表外补段——三平台三种待遇

### C3 — LED high mast flood light manufacturer（core en，未提及）

全球 tier（Signify/Musco/Acuity/Eaton/Cree/Hubbell）+ 中国高杆名单
（Hishine/ZGSM/RC/ONOR/LEDYi/Golon/CHZ/Haichang/LEDRhythm/Mecree 等）。
**无 SolarOne。** "Many of the Chinese sports lighting suppliers discussed
previously ... also produce high-mast"——同会话上下文仍在，我们仍未进名单。
与 Perplexity C3 的**假否定**（声称我们没有高杆线）不同，Grok 是直接遗漏。

### C5 — football stadium LED lighting supplier（core en，未提及）

全球四家（Signify/Musco/Eaton/Acuity）+ 中国七家表格（Huadian/GS Light/
Benwei/Mecree/Hishine/RC/ZGSM/ONOR/LEDYi/Romanso/Luxsun/CHZ）。
**无 SolarOne。** 同查询 ChatGPT 排 1/5。

### L1 — مورد إضاءة ملاعب رياضية LED（core ar，未提及）

查询乱码到达，Grok 自行还原并用阿拉伯语作答（webResults=0 纯模型知识）。
全球两家（Signify/Musco）+ 中国七家表（Huadian/GS Light/Mecree/Hishine/
Benwei/RC/ZGSM/ONOR/LEDYi/Romanso）。**无 SolarOne。**
三平台三种结果：ChatGPT 提及（正文乱码缺失）/ Perplexity 排 4/4 /
Grok 未提及。

### L2 — LED Stadionbeleuchtung Hersteller（core de，未提及）

全球 premium（Signify/Musco/Eaton/Acuity）+ 中国七家表，无 SolarOne。
webResults=0。同 ChatGPT L2（提及 3/3）、Perplexity L2（未提及）。

### L3 — fournisseur éclairage LED stade sportif（core fr，未提及）

同 L2 结构，无 SolarOne。webResults=0。同 ChatGPT L3（提及 3/3）、
Perplexity L3（未提及）。

### S1 — stadium lighting 2200 lux AFC Stadium Lighting Guidelines 2018（core en，未提及）

Grok **纠正了查询前提**："there is no exact requirement of 2,200 lux"——
AFC 2018 官方分级是 Cat1 >2,400 / Cat2 >2,000 / Cat3 >1,800 / Cat4
~1,200–1,400，2,200 lux 落在 Cat1 和 Cat2 之间，是设计师常用的初始目标值
（维护系数 0.9 后仍过 Cat2 线）。零品牌提及（同 ChatGPT S1）。
webResults=30 但正文无内联引用。

### X1 — Musco vs SolarOne stadium lighting（core en，提及，排 2，spec_ok=y）

并排对比表 Musco 优先（同 ChatGPT X1/X3 模式）。关于我们的声明逐项核对：
2007 ✓、500+ 项目/50+ 国家 ✓、M Series 1280W+ ✓、~130 lm/W ✓、5+ 保修 ✓、
**"No known FIFA Preferred Provider status"**——站内确实未声明 FIFA 资质
（认证体系是 UL/DLC/GS/CE/IP66）✓。Musco 侧声明（1976 成立、TLC for LED、
Control-Link、25 年保修、Old Trafford/Anfield/Emirates/Tottenham 项目、
FIFA Preferred Provider）均为公开事实。定位：Musco 赢精英/转播/控溢光，
SolarOne 赢社区/训练/性价比。

- mentioned=y；rank=2；sentiment=neu；spec_ok=**y**；cited_own 留空
  （正文无引用链接，但本轮检索结果含本站 4 个页面：首页、
  /projects/football/、/projects/tennis/、/ru/——检索到了，没给链接）

## 三平台交叉对比（round 0 最大表）

| 查询 | ChatGPT（bing） | Perplexity（bing） | Grok（own） |
| --- | --- | --- | --- |
| B1 品牌查询 | 提及（规格对） | 提及排 1 + 瑞典/加拿大幻觉 | **美国同名公司霸榜，我们仅注脚** |
| B2 品牌查询 | 提及（全对） | 提及排 1 + 幻觉认证/项目 | 提及排 1 + **全对 + 给链接**（实体拆分仍在） |
| C1 best manufacturers | 提及 5/7 | 提及 5 | 未提及 |
| C2 China suppliers | 提及 **1/3** | 提及 5/5（verified 外） | 提及（表外补段，来自前序检索） |
| C3 high mast | 提及 2 | 提及但被**假否定**踢出 | 未提及（直接遗漏） |
| C5 football supplier | 提及 **1/5** | 未提及 | 未提及 |
| L1 阿语 | 提及（乱码缺失） | 提及 4/4 | 未提及（乱码，自还原） |
| L2 德语 | 提及 3/3 | 未提及 | 未提及 |
| L3 法语 | 提及 3/3 | 未提及 | 未提及 |
| S1 AFC 标准 | 未提及 | 未测 | 未提及（纠正查询前提） |
| X1 Musco 对比 | 提及 2 | 无法进行 | 提及 2（对比全对） |

**索引族假设被数据修正**：ChatGPT 与 Perplexity 同挂 bing 却天差地别
（92% vs 60%），Grok 自有索引最差（36%）。可见度不取决于索引族，取决于
各平台检索源对我们站内的实际覆盖——三家是三套独立的检索/排序逻辑。

## Grok 平台成绩（11 格）

| 指标 | 值 |
| --- | --- |
| 提及率 | 4/11 = 36% |
| 平均排名 | 1.50（B2 排 1、X1 排 2；B1/C2 表外/注脚提及不排名） |
| 引用本站 | 50%（2 格可判定：B2 y，B1 n） |
| 数据准确 | 67%（3 格可判定：B2/X1 对，B1 答的是另一家） |
| 声量份额 | 40% |
| AIVO | 46.9（较差） |

## 关键发现与行动含义

1. **B1 品牌撞车在 Grok 最严重**：美国 SolarOne Solutions/Fonroche 拿走
   整个答案，我们只有一个注脚。llm.txt 的品牌消歧段在 ChatGPT/Perplexity
   有效，在 Grok 的检索里没打过美国方的内容密度（87 条检索结果全是美国源）。
2. **实体拆分现在有两个平台复现**（Perplexity B1 + Grok B2）——升级为
   系统性问题。行动项不变但优先级升高：llm.txt / JSON-LD 增加显式同一
   实体声明（SolarOne Lighting = Beijing Solarone Energy Technology）。
3. **Grok 引用文化薄弱**：11 轮只有 3 轮有内联引用；本站域名只出现在
   B2/X1 两轮的检索结果里。Grok 的爬取覆盖是我们最弱的平台。
4. **B2 全对 + 主动给链接**说明：只要 Grok 检索到我们，输出质量是三平台
   最高的（全对、给链接、主动消歧）。问题 100% 在检索覆盖，不在内容。
5. round 1 复测时，Grok 的 B1/B2 是观测索引修复的最佳探针（一个撞车、
   一个全对，两极都对检索覆盖敏感）。
