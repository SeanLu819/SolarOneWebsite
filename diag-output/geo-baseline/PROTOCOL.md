# GEO 可见度基线测量规程

## 为什么必须测

A1/A2/A3 改的都是站内。AI 的回答要等它重新抓取才会变，周期 2–8 周；不测基线，
后面所有动作都无法归因——你不知道分数动了一下是哪个动作的功劳。

**分数只在本项目内部跨轮次可比，不要和别家公司的数字比。**

## 测三个维度

| 维度 | 方式 | 频率 |
| --- | --- | --- |
| AI 回答可见度 | 8 平台 × 核心查询，手工记录 | round 0 现在；之后每季度 |
| 索引存在性 | 4 条 site/品牌查询式，看独立站是否出现 | 每季度 |
| 第三方内容准确性 | 目录站资料页的规格是否与站内一致 | 每季度 |

前两维的工具和数据都在本目录，第三维的实测见 `index-presence-2026-10-23.md`。

## 一轮怎么跑

```bash
# 生成待测表（已有 rounds/round-0-2026-10-23.csv 就不必再生成）
python geo_round.py init --round 0

# 填完后出报告
python geo_round.py report
```

一轮 = 8 平台 × 11 条核心查询 = **88 格**。扩展查询只跑前 3 平台：注意 `init --extended`
会把全部 21 条 × 8 平台都生成（168 行），所以 round 0 的 CSV 是 init 生成 88 行核心后，
由 `insert_extended_football_rows.py` 补进 C6/X3 两条的 top-3 行（共 94 行）。
extended 6 行也填了的话，报告覆盖率会 >100%——正常，多出的是赠品格子。

规则：

1. **每个平台开一个全新会话**，不要沿用上次的上下文。
2. 把 `query_text` **原样贴入**。不要在非品牌查询里加品牌名，不要写"请列出供应商"——
   那是诱导，测出来的是你想要的答案，不是 AI 真实会说的。
3. 答完**立刻记录**，不要攒一批一起补。
4. `model_version` 一定填。AI 平台改版很频繁，不记版本就无法解释跨轮次跳变。

## 每一列怎么填

| 列 | 填法 |
| --- | --- |
| `mentioned` | 回答里出现 SolarOne / 北京信能阳光 / solaronelighting.com 任一，即 `y` |
| `rank` | 品牌**首次**出现的位置，1–10；进了回答但没进前 10 留空 |
| `sentiment` | `pos` / `neu` / `neg`，看语气不看是否提及 |
| `cited_own` | 回答是否给出 solaronelighting.com 的链接 |
| `spec_ok` | 引用的数字是否与站内一致**且归属正确**；答的是另一家公司填 `na` |
| `competitors_seen` | 分号分隔。**这一列决定声量份额，别空着** |
| `model_version` | 平台当时用的模型/版本 |
| `notes` | 任何异常：品牌混淆、答非所问、拒绝回答 |

## 四个判定陷阱

1. **品牌混淆是常态**：SolarOne Solutions（美国，离网太阳能路灯）会抢先出现在品牌查询里。
   `mentioned=y` 但 `spec_ok=n` 完全正常——这正是要抓的东西，不要手软改成 `y`。
2. **数字在、品牌不在**：S1（源深 2200 lux）很可能 AI 报得出数字却不提我们。
   这仍然记 `mentioned=n`，在 notes 里写"有数字无品牌"。
3. **非英语查询**：DeepSeek / Meta AI 可能用中文答英文问。判定 `mentioned` 时中英文品牌名都算。
4. **随机性**：同一查询两次结果可能不同。B1/X1/S1 这三类关键查询跑 2 次，取较差值。

## 出报告

```bash
python geo_round.py report            # 全部轮次，环比默认对最早一轮
python geo_round.py report --ref 0    # 指定参照轮次
```

产出 `report-latest.md`：总体指标、分平台、分查询意图、分查询、环比。

**覆盖率不到 100% 时，报告里的比率只代表已测的那部分**，不能当全量结论——
脚本会在报告开头列出数据问题，先修那些再读指标。

## 索引存在性（每季度手工跑一次）

4 条查询式，记录 `solaronelighting.com` 是否出现在结果里：

1. `site:solaronelighting.com`
2. `"solaronelighting.com"`
3. `"SolarOne" "Yuanshen Sports Centre" stadium lighting 2200 lux`
4. `SolarOne LED sports lighting manufacturer stadium`

任一条出现本站页面就是进展。首次实测结果见 `index-presence-2026-10-23.md`。

## 分享链接提取路径（2026-10-23 起可用）

测完一个平台后，点「分享」生成链接，可按 `chatgpt-share-evidence-2026-10-23.md`
同款格式提取，免去手工转录：

1. 走代理拉分享页（沙箱直连 chatgpt.com 被 SSL 拦）：
   `curl -x http://127.0.0.1:7897 -L -A "<browser UA>" <share_url> -o share.html`
2. `extract_share_turns.py` 按消息时间戳还原轮次顺序（flight 数据是**逆序**序列化的，
   必须用时间戳排序，不能信文档位置）
3. `dump_block.py <n>` 读第 n 个答案块全文；`check_citations.py` 统计每轮本站引用
4. 已知限制：分享页**不暴露模型版本**（`model_version` 仍需从原会话问）；阿拉伯语
   答案正文可能不在页面里（查询乱码态到达时）；flight 数据格式 `[idx],"text"` 的索引是
   池序不是会话序
