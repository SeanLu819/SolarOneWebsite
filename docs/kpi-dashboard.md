---
doc_id: kpi-dashboard
title: SolarOne 转化与流量 KPI 看板定义（B0 / D5）
version: 1.0.0
last_updated: 2026-09-28
owner: Sean Lu
related:
  - path: docs/seo-growth-plan.md
    role: 总方案（B0 批次含 D5）
---

# KPI 看板定义（B0 / D5）

> 目的：在 GA4 + GSC 生效之前先定好「看什么、怎么拆」，避免埋点上线后返工。
> 全部指标来自 **D3 的 4 个转化事件 + GA4/GSC 原生报告**，无需自定义维度。

## 1. 北极星指标（North Star）

**询盘数（generate_lead 事件数）** —— 一切 SEO/速度的终极出口。
SEO 把「展现 → 点击 → 落地页」做起来，转化层把「落地页 → 询盘」做起来，
二者相加才是真实 ROI。

## 2. 转化漏斗（4 个事件）

| 事件名 | 触发时机 | 业务含义 | GA4 报告位置 |
|---|---|---|---|
| `generate_lead` | 联系表单**真实**提交成功（非 honeypot 机器人丢弃路径） | 已交付的询盘（核心） | 事件 / 转化 |
| `contact_click` | 点击 mailto / tel / WhatsApp 链接（参数 `method`） | 主动联系意图（次级线索） | 事件（按 `method` 细分） |
| `pdf_download` | 点击任意 `.pdf` 链接（参数 `file_name`） | 项目案例/规格下载兴趣 | 事件（按 `file_name` 细分） |
| `quote_view` | 产品页「Request a Sample」询价区进入视口（曝光，触发一次） | 产品页询价意向强度 | 事件 |

> ⚠️ **安全降级**：以上事件仅在 `GA4_MEASUREMENT_ID` 配置后才会真正上报；
> 未配置时 `gaTrack()` 为 no-op，不会抛错、不发任何第三方请求。
> 因此**看板在变量配好之前为空属正常**。

## 3. 流量获取维度（GSC + GA4）

| 维度 | 来源 | 用途 |
|---|---|---|
| 有展现词数 / Top-10 词数 / CTR | GSC「效果」报告 | 关键词资产增长（B3 后对比） |
| 国家/地区 | GA4 用户维度 | 定位高价值市场（欧美/中东为主） |
| 落地页 | GA4 着陆页报告 | 哪类页带来询盘（产品 vs 项目 vs 资源） |
| 设备（移动/桌面） | GA4 技术维度 | 移动端优先验证（B2 CWV 回归） |
| 渠道（organic / direct / referral） | GA4 默认渠道分组 | 自然搜索占比提升 = SEO 有效 |

## 4. 速度门禁（L3，详见 `scripts/perf_baseline.py`）

| 指标 | 门禁 | 频率 |
|---|---|---|
| LCP（移动） | < 2.5s，且每批不劣化 >10% | 每次部署 / 每月 |
| CLS | < 0.1 | 同上 |
| INP | < 200ms | 同上 |
| TTFB | 监控趋势（基线 ~0.7s） | 同上 |

## 5. 看板搭建步骤（GA4 生效后）

1. **GA4**：管理 → 事件 → 确认 4 个事件出现在「事件」列表（实时报告可即时验证）。
2. **探索/报表**：用「事件名称」+「着陆页」+「国家」做自由组合，保存为「询盘来源」报表。
3. **GSC**：效果 → 查询，每周导出有展现词 → 回填 `docs/keyword-inventory.csv`（B1/B6）。
4. **告警**：`generate_lead` 连续 7 天为 0 → 检查表单/邮件通知（J4）。

## 6. 当前状态（2026-09-28）

- ✅ 4 个事件代码已落地（D3）+ 守卫测试（`pages/tests_analytics.py`）。
- ⏳ GA4 / GSC 环境变量待配（D1）→ 看板为空直到配置完成。
- ⏳ `perf_baseline_<date>.json` 首次真实采集需 `PSI_API_KEY`（A1）。
