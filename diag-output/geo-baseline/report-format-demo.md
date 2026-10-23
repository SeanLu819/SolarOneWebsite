> 格式示例：本文件由 example-round.csv 的演示数据生成，数字不是真实测量结果。
> 真实基线以你填好的 rounds/round-0-*.csv 跑出来的 report-latest.md 为准。

# SolarOne GEO 可见度基线报告

- 生成时间：2026-10-23
- 数据轮次：bad, demo, demo2
- 查询集：18 条（核心 10 条 / 扩展 8 条）
- 单轮满覆盖 = 8 平台 x 10 核心查询 = 80 格

## ⚠️ 数据问题（先修这些再信指标）

- round-bad.csv:2：platform='Bard' 不在 8 平台清单里
- round-bad.csv:4：round/platform/query 重复

## 总体（demo2）

| 指标 | 值 |
| --- | --- |
| 已测格子 | 80 / 80（覆盖 100%） | 
| 品牌被提及 | 23 / 80 = **29%** | 
| 平均排名 | 4.39 | 
| 引用本站域名 | 61% | 
| 引用数据准确 | 87% | 
| 正面/中立/负面 | 9 / 14 / 0 | 
| 声量份额（对竞品） | 37% | 
| **AIVO 综合分** | **50.4 / 100（较差）** | 

AIVO = 可见度 40% + 基建 20% + 竞争优势 25% + 舆情 15%。本批：V 40.0 / I 73.8 / C 37.1 / S 69.6。

## 分平台

| 平台 | 索引族 | 已测 | 提及率 | 平均排名 | 引用本站 | 数据准确 | 声量份额 | AIVO |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ChatGPT | bing | 10 | 50% | 4.40 | 60% | 100% | 62% | 62.5 |
| Gemini | google | 10 | 20% | 4.50 | 50% | 100% | 25% | 45.9 |
| Copilot | bing | 10 | 40% | 3.00 | 100% | 75% | 50% | 62.0 |
| Perplexity | bing | 10 | 50% | 4.20 | 100% | 80% | 62% | 67.8 |
| Claude | own | 10 | 10% | 5.00 | 0% | — | 14% | 21.1 |
| Grok | own | 10 | 20% | 5.50 | 0% | — | 25% | 26.0 |
| Meta AI | google | 10 | 10% | 5.00 | 0% | — | 14% | 21.1 |
| DeepSeek | own | 10 | 30% | 5.33 | 33% | 100% | 38% | 50.4 |

## 分查询意图

| 意图 | 已测 | 提及率 | 平均排名 | 引用本站 | 声量份额 | AIVO |
| --- | --- | --- | --- | --- | --- | --- |
| brand | 16 | 88% | 3.71 | 50% | 100% | 85.0 |
| category | 24 | 25% | 6.67 | 83% | 25% | 45.5 |
| spec | 8 | 0% | — | — | — | 0.0 |
| comparison | 8 | 38% | 3.00 | 67% | 38% | 47.0 |
| local | 24 | 0% | — | — | 0% | 0.0 |

## 分查询

| 查询 | 意图 | 语言 | 已测 | 提及 | 最好排名 | 引用本站 |
| --- | --- | --- | --- | --- | --- | --- |
| B1 SolarOne stadium lights | brand | en | 8 | 6/8 | 2 | 2 |
| B2 SolarOne LED sports lighting manufactu | brand | en | 8 | 8/8 | 1 | 5 |
| C1 best LED stadium light manufacturers | category | en | 8 | 2/8 | 6 | 2 |
| C2 LED sports field lighting supplier Chi | category | en | 8 | 4/8 | 4 | 3 |
| C3 LED high mast flood light manufacturer | category | en | 8 | 0/8 | — | 0 |
| L1 مورد إضاءة ملاعب رياضية LED | local | ar | 8 | 0/8 | — | 0 |
| L2 LED Stadionbeleuchtung Hersteller | local | de | 8 | 0/8 | — | 0 |
| L3 fournisseur éclairage LED stade sporti | local | fr | 8 | 0/8 | — | 0 |
| S1 stadium lighting 2200 lux AFC Stadium  | spec | en | 8 | 0/8 | — | 0 |
| X1 Musco vs SolarOne stadium lighting | comparison | en | 8 | 3/8 | 2 | 2 |

## 环比（bad → demo2）

| 指标 | bad | demo2 | 变化 |
| --- | --- | --- | --- |
| 提及率 | 100% | 29% | -0.71 |
| 平均排名 | 4.00 | 4.39 | +0.39 |
| 引用本站 | 100% | 61% | -0.39 |
| 数据准确 | 100% | 87% | -0.13 |
| 声量份额 | 100% | 37% | -0.63 |
| AIVO | 88.9 | 50.4 | -38.46 |

## 读数提醒

- 覆盖率不足 100%% 时，上面的比率只代表「已测的那部分」，不能当全量结论。
- AI 回答有随机性：同一查询两次结果可能不同，关键查询请跑 2 次取较差值。
- AIVO 只在本项目内部跨轮次可比；不要和别家公司的分数比。
