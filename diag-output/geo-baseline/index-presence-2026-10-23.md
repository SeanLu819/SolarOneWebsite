# 独立站索引存在性与第三方内容实测

- 日期：2026-10-23
- 方式：4 条查询式检索 + 逐条阅读返回结果（非站内自检）
- 意义：检索类 AI（ChatGPT 检索 / Copilot / Perplexity 走 Bing，Gemini / Meta AI 走 Google）
  的答案来自搜索引擎索引。**索引里没有我们，这些 AI 就只能引第三方。**

## 一、4 条查询式的结果

| # | 查询式 | solaronelighting.com 出现 |
| --- | --- | --- |
| 1 | `site:solaronelighting.com` | **否**（返回 5 条，0 条本站） |
| 2 | `"solaronelighting.com"` | **否**（返回 5 条，0 条本站） |
| 3 | `"SolarOne" "Yuanshen Sports Centre" stadium lighting 2200 lux` | **否**（返回 5 条，0 条本站） |
| 4 | `SolarOne LED sports lighting manufacturer stadium` | **否**（返回 5 条，0 条本站） |

**4/4 全部为零。** 独立站在该引擎没有任何可检索痕迹。

## 二、品牌的检索足迹 100% 在第三方，且内容已过期或冲突

| 来源 | 语言 | 实测内容 | 与站内的冲突 |
| --- | --- | --- | --- |
| Made-in-China（en + nl 两个镜像） | en / nl | "800,000PCS 产品、160 国客户" | 现站口径为 500+ 项目 / 50+ 国 |
| CIFTIS 服贸会 | zh | "8 年质保，8 年内保证光衰不超过 5%" | 现站为 5+ 年质保 |
| GlobalSources | en | "IP67 rating"；"Meeting CE, RoHS, TuV and UL Standards" | 现站全线 **IP66**；UL/DLC 仅部分型号（铁律 50） |
| ListCompany + 357th.com（抓取镜像） | en | 旧地址昌平 + 旧域名 `solar-one.com.cn` / `xnsolar.com` | 公司已迁顺义；现域名为 solaronelighting.com |
| 天眼查 | zh | 品牌名「信能阳光」 | 与英文名 SolarOne 脱节，中英文检索无法互达 |

这些页面是 AI 引用我们时**最可能拿到的事实源**。X1（Musco vs SolarOne）这类对比查询里
AI 报错规格，根因就在这里，不在站内。

## 三、旗舰项目的数字已进 AI 知识库，但品牌缺席

Grokipedia 的 `Yuanshen Sports Centre Stadium` 条目完整记载：

> 320 盏高性能 LED 泛光灯，平均 2200 lux，均匀度 U0 0.8，显色指数 Ra>80，
> 符合 AFC Stadium Lighting Guidelines 2018

这组数字与 `llm.txt` 里我们发布的口径完全一致——但**全文未出现 SolarOne**。

这是 GEO 最典型的一类缺口：**实测数据已经进入 AI 可见内容，却没有品牌归属**。
修法不是改数据，而是让「项目 + 品牌」在更多可索引处共同出现。

## 四、品牌混淆在检索层已经成立

4 条查询式里，返回的"SolarOne"实体是：

- **SolarOne Solutions**（美国，离网太阳能路灯，Fonroche Lighting 旗下，域名 solarone.net）
- **Solar One**（美国纽约，可再生能源非营利组织）
- **信能阳光**（中文工商注册品牌名）

`llm.txt` / `llm.ar.txt` 的 `Not to be confused with` 段与
`templates/base.html` 的 `disambiguatingDescription` 方向正确，但目前**只存在于站内**，
尚未进入上面任何一个第三方页面。

## 五、下一步（按性价比排序）

1. **更新 Made-in-China 与 GlobalSources 两个资料页**的规格和口径——我们完全可控，
   直接消除 IP67 / 8 年质保 / 160 国这三处会被 AI 引用的错误事实。
2. **C7 round 0 基线**（本目录 `rounds/round-0-2026-10-23.csv`）。
3. **C2 行业媒体外联**——唯一能同时解决第二、三、四条的动作，但周期 1–3 个月。

## 复测方式

每季度重跑第一节的 4 条查询式，把结果追加到本文件。任一条出现本站页面即为进展。
注意：更换搜索引擎或更换地区设置会改变结果，复测时要用同一引擎同一地区。

---

## 2026-10-23 12:45 推送后复测（第一次）

**部署已验证上线**（commit `dec46fa`，v1.10.36）：

| 项 | 推送前 | 推送后 | 判定 |
| --- | --- | --- | --- |
| `/llm.txt` | 6463 B | **13999 B** | ✅ 与本地逐字节一致 |
| `/llm.ar.txt` | **404** | **21808 B** | ✅ 首次上线，与本地逐字节一致 |
| `/robots.txt` LLM-Txt 声明 | 1 行 | **2 行**（en + ar） | ✅ |
| `/fr/products/fl1m/` FAQ 首问 | What is the luminous efficacy… | **Quelle est l'efficacité lumineuse…** | ✅ A1 生效 |
| `/ar/products/fl1m/` FAQ 首问 | 英文原文 | **ما هي الكفاءة الضوئية…** | ✅ A1 生效 |
| `/ru/products/fl1m/` FAQ 首问 | 英文原文 | **Какова световая отдача…** | ✅ A1 生效 |
| 首页 Organization JSON-LD | 无 disambiguatingDescription | **已含**（含三个同名实体声明） | ✅ |

**IndexNow**：`scripts/indexnow_ping.py --live` → **HTTP 200**，354 条 URL（59 × 6 语种）
已提交。密钥文件线上 200 可达。

**索引存在性复测**：`site:solaronelighting.com` 与 `"solaronelighting.com"`
两条查询式**仍返回 0 条本站页面**——符合预期，IndexNow 推送仅数分钟，
搜索引擎索引更新以天/周计。下次复测建议间隔 ≥ 14 天。

附带观察：`"solaronelighting.com"` 查询的第 2 条结果是 `solarone.net`
（Fonroche 旗下同名品牌 SolarOne Solutions）——正是 `Not to be confused with`
段与 `disambiguatingDescription` 要拦截的混淆源，目前该消歧只存在于站内。
