# Round 0 收官登记（2026-10-24）

## 最终状态

**44 格 / 4 平台 / 3 索引族中的 2 族，总体 AIVO 62.5（一般）**。round 0 测量
到此为止——剩余 4 平台从当前测量环境（中国大陆网络）均不可达，详见下文。

| 平台 | 索引族 | 已测 | AIVO | 数据 |
| --- | --- | --- | --- | --- |
| ChatGPT | bing | 13 | 90.1（优秀） | chatgpt-share-evidence-2026-10-23.md |
| Perplexity | bing | 10/13 | 57.6（较差） | perplexity-computer-evidence-2026-10-24.md |
| Grok | own | 11 | 46.9（较差） | grok-share-evidence-2026-10-24.md |
| DeepSeek | own | 10 | 25.3（较差） | deepseek-share-evidence-2026-10-24.md |

CSV 数据（rounds/round-0-2026-10-23.csv）与 report-latest.md 不再变动，
作为 round 1 复测的对比基准冻结。

## 未测 4 平台：测量环境不可达（非内容问题）

| 平台 | 索引族 | 障碍 | 证据 |
| --- | --- | --- | --- |
| Copilot | bing | 国内网络 HTTP 502（页面本身打不开）；10-23 另发现需微软账号登录 | 2026-10-24 用户截图 |
| Meta AI | bing | Meta 服务大陆被墙，需代理 + Meta 账号 | 2026-10-24 用户确认 |
| Gemini | google | 地区封锁，需代理 | 2026-10-23 实测 |
| Claude | own | 无法登录 | 2026-10-24 用户确认 |

**为什么这个缺口可以接受**：

1. **Copilot / Meta AI 与已测的 ChatGPT / Perplexity 同属 bing 族**——同一
   检索索引的第三、四个样本，信息增量低（且 bing 族内部差异已被 ChatGPT 92%
   vs Perplexity 60% 证明取决于各平台检索源覆盖，不取决于索引本身）。
2. **Gemini 是唯一 Google 族样本，但推迟测量方法学上更干净**：站点在
   Google 的收录尚未起步（GSC 未验证、Google 族覆盖为 0），此刻测 Gemini
   大概率只能测到"模型知识 + 空索引"，与 Grok 的模式重复。等 round 1 做完
   GSC 与收录修复再补测，才能把"Google 索引修复是否生效"变成可观测信号。
3. 已测 4 平台覆盖了买家决策最重要的两条路径：ChatGPT（海外 B2B 调研主力，
   bing 检索）+ 模型知识路径（Grok B2 证明只要模型有事实，输出质量最高）。

**补测入口保留**：换网络环境（代理/海外）后随时可补，直接填同一份 CSV 对应
行，报告按新覆盖重算。若海外同事愿意协测，分享链接即可由 AI 侧提取。

## Round 0 产出的行动项清单（按优先级）

1. 🔴 **失信被执行人处置**（用户侧，法律/财务）：公开渠道已证实记录挂在主实体
   （entity-verification-xinneng-2026-10-24.md）。履行义务→名单移除→百科
   更新，是 S 维度（舆情健康度）唯一的根治路径；百科是 AI 传播载体。
2. 🔴 **Bing WMT 验证 + IndexNow 状态检查**（用户侧 10 分钟）：bing 族已测
   2/4 平台、是唯一稳定检索到本站的索引族，验证 WMT 是检索覆盖的第一杠杆。
3. 🟡 **llm.txt 实体消歧**（AI 侧可立即做）：品牌名=注册名=信用代码
   91110116663729775X 的同一实体声明；三家信能阳光实体关系与网站运营主体
   写清楚；FL-M 高杆线写显式（Perplexity C3 假否定观测点）。
4. 🟡 **旧域名 301 恢复**（用户侧确认域名状态）：solar-one.com.cn /
   solai-one.com.cn 已 502 失效，若能续费应 301 到现行站。
5. 🟢 **Google GSC + 收录**（用户侧）：round 1 后段，Gemini 补测的前置。
6. 🟢 **B1 旧第三方内容**：alighting listing / 体博会档案的过期规格与旧地址，
   考虑向第三方更新资料。

## Round 1 复测观测点

- **C3**（LED high mast flood light manufacturer）：Perplexity 假否定是否修复
  ——索引覆盖的第一验收点
- **B1/B2**（品牌查询）：实体拆分（Perplexity/Grok 两平台复现）是否收敛为
  单一实体画像
- **DeepSeek 检索层**：178 页零出现 solaronelighting.com 是否改善
- **同查询集、同判定口径**，AIVO 逐项对比
