# 网站测速与优化整体方案（v1.10.0 基线）

日期：2026-10-04 · 数据来源：线上实测（本机 → `https://www.solaronelighting.com`）
方案状态：**未实施**，等确认后再动代码。本文件只记录「测了什么 + 为什么 + 改哪里 + 改完能到多少」。

---

## 1. 基线（亲手量的数，不是估的）

复测命令（已固化为脚本）：

```bash
E:/Python/python3/python.exe scripts/e2e/perf_probe.py --repeats 3
```

单位毫秒（3 次中位数）：

| URL | dns | tcp | tls | **ttfb** | total | 传输 |
|---|---|---|---|---|---|---|
| `/` | 18 | 105 | 232 | **566** | 569 | 12.9 KB |
| `/products/` | 18 | 110 | 232 | **571** | 575 | 15.3 KB |
| `/projects/` | 11 | 104 | 223 | **614** | 762 | 19.1 KB |
| `/projects/football/` | 20 | 118 | 249 | **624** | 627 | 15.6 KB |
| `/projects/tennis/` | 17 | 108 | 229 | **569** | 785 | 16.0 KB |
| `/products/mseries-gs/` | 19 | 108 | 246 | **585** | 805 | 20.2 KB |
| `/news/` | 25 | 125 | 253 | **592** | 803 | 14.1 KB |

## 2. 链路分解：时间花在哪

把 TTFB 拆开（本机在中国，访问 Vercel 新加坡边缘）：

```
dns     ~18 ms     机房 DNS（CNAME → Vercel）
tcp    ~110 ms     跨境 TCP 握手（RTT 往返）
tls    ~235 ms     跨境 TLS 1.3 握手
───────────────────────────────
握手小计  ~360 ms   ← 网络固有成本，改不动
源站渲染  ~210 ms   ← 这一层是我们可以动的
───────────────────────────────
TTFB     ~570 ms
下载     ~10-200 ms（几乎可忽略，HTML 只有 13-20 KB）
```

**结论：一半是跨境网络，一半是源站渲染。** 所以"把首页做到 200ms TTFB"在中国网络下物理上做不到；能做是把**源站那 210ms 干掉**。

## 3. 响应头实证（curl -D - 抓的）

| 项 | 实测值 | 判读 |
|---|---|---|
| `Cache-Control` (HTML) | `public, max-age=0, must-revalidate` | 🔴 **每次都回源**，边缘不存 |
| `X-Vercel-Cache` | `MISS`（`age: 0`，实测 6 次全是） | 🔴 印证上一条 |
| `x-vercel-id` | `sin1::iad1::…` | 🔴 边缘在新加坡，**函数在美国东** → 跨洋回源 |
| `Content-Encoding` | `br` / `gzip`（协商成功） | ✅ 已启用 |
| `Cache-Control` (`/static/*`) | `max-age=31536000, immutable` | ✅ 静态资源一年缓存 |
| `font-display` | `swap`（`static/css/fonts.css:37`） | ✅ 不会 FOIT 卡 LCP |
| 首页 `<img>` | 3 个（logo + 2 张 `loading="lazy"`） | ✅ 首屏无大图，无 LCP 图片负担 |
| `<script>` | 11 个（10 内联 + 1 GTM `async`） | ✅ 本机 JS 体积≈0，无第三方阻塞 |
| 安全头 | HSTS preload / CSP / COOP / X-Frame DENY | ✅ 齐全，别乱动 |

## 4. 已经做对的（别改，改了反而慢）

1. Brotli/gzip 自动压缩（Vercel 层）
2. 静态资源 immutable 一年缓存（`vercel.json` headers 段）
3. 字体 `font-display: swap` + 按需字形加载
4. 首屏图全部 `loading="lazy"`，只有 logo 立即加载 → 首页 LCP 落在文本上，天然最快
5. GTM 外链脚本已带 `async`
6. 全站 JS 几乎为零（模板内联），没有大框架

## 5. 瓶颈归因（按收益排序）

### 🔴 根因 1：HTML 零缓存 —— 每次请求都从美国东源站渲染

`Cache-Control: max-age=0, must-revalidate` + `X-Vercel-Cache: MISS` 意味着**每一个访客每一次刷新都要跨洋跑一趟**。首页、列表页、详情页全中招。

收益：改成边缘缓存后，命中请求 TTFB ≈ 握手 360ms + 边缘处理 ~20ms ≈ **380ms**，砍掉约 200ms（≈35%）。

### 🔴 根因 2：函数区域被跨洋调度

`x-vercel-id: sin1::iad1` = 边缘在新加坡、函数在 `iad1`（美东）。新加坡访客的请求要走一趟新加坡→美国东。

收益：固定函数区域后，亚太访客边缘与函数同区，单程跨境变本地，可再省 **80–150ms**。

### 🟡 根因 3：源站渲染 210ms（占比最小）

Python serverless 冷/热启动 + Django 渲染 + seed 读取。生产零 DB（`pages/admin/visitor.py:5` 明确写着访客统计只 non-Vercel 写库，所以生产没有写库开销 —— 这点已经做对了）。

收益空间最小，且动了容易影响功能。

## 6. 方案（分层，标了预期收益与风险）

### P0 — 本周做，收益最大

| # | 动作 | 改哪里 | 预期 | 风险 | 验证 |
|---|---|---|---|---|---|
| P0-1 | HTML 加边缘缓存：**不带 query 的 GET 响应**加 `Cache-Control: public, s-maxage=300, stale-while-revalidate=86400` | 新增一个尾部中间件给 `HttpResponse` 打头（**必须排除带 query 的 URL** —— `/projects/?sport=X` 这类筛选 URL 一旦被缓存会把不同筛选串味） | TTFB 570 → **~380ms** | seed 更新后最长 5 分钟才生效（可接受）；部署新版本时 Vercel 自动失效旧缓存 | `curl -sI` 看 `X-Vercel-Cache: HIT` / `age>0` |
| P0-2 | 固定函数区域 | Vercel → Project Settings → **Functions → Region** → 固定 `iad1`（iadr1）或 `sin1`（看主市场；现有项目以欧美为主，建议 iad1） | 亚太访客再省 **80–150ms** | 改区域会短暂重建函数 | 连测 3 次看 `x-vercel-id` 是否只剩一个区域前缀 |

### P1 — 两周内，锦上添花

| # | 动作 | 改哪里 | 预期 |
|---|---|---|---|
| P1-1 | 给 GTM 加 `<link rel="preconnect">` | `templates/base.html` head 区 | 省掉 GTM 的一次 DNS+TLS，~50–100ms 的第三方开销 |
| P1-2 | 探针接 CI：`scripts/e2e/perf_probe.py` 加进 `.github/workflows/ci.yml`（可设 `--ttfb-budget 800`） | ci.yml | 以后每次 push 都有速度读数，回归可见 |
| P1-3 | 首页/落地页模板检查有无重复遍历（seed 已在模块级缓存，预计无需改） | `pages/views/*.py` | 可能再省 20–50ms 源站时间 |

### P2 — 长期观察

- P2-1：若 P0-1 因 CSP/SEO 团队要求不能用，退而求其次在 **Cloudflare 加 Cache Rule 缓存 HTML 5 分钟**（注意别和 Vercel 边缘缓存叠两层）。
- P2-2：Core Web Vitals 用 **field data** 看（GSC → 核心网页指标），实验室数据（Lighthouse）在这个跨境场景会误导。
- P2-3：图片优化已由你拍板「不降分辨率」，因此本方案**不动任何图片**。

## 7. 验收命令

```bash
# 当前基线（应全绿，exit 0）
E:/Python/python3/python.exe scripts/e2e/perf_probe.py --repeats 3

# 收紧预算：超过 400ms 就失败（等 P0 做完才定这个阈值）
E:/Python/python3/python.exe scripts/e2e/perf_probe.py --repeats 5 --ttfb-budget 450 --total-budget 900

# 边缘缓存是否命中
curl -sI --noproxy '*' https://www.solaronelighting.com/ | grep -iE "x-vercel-cache|age|cache-control"

# 函数区域是否只剩一个
for i in 1 2 3; do curl -sI --noproxy '*' https://www.solaronelighting.com/ | grep -i x-vercel-id; done
```

## 8. 明确不做（避免花冤枉钱）

| 项 | 理由 |
|---|---|
| 图片降分辨率 | 你已明确否决（17 张 >300 KB 维持原样） |
| 换框架 / 上 Next.js | 当前 JS 体积≈0，换框架只会增加体积 |
| SPA 化 / 客户端渲染 | 对 SEO 有害，且现在首屏 LCP 是文本、本来最快 |
| 上 CDN 付费套餐 | Vercel 边缘已是 CDN，`public/static/` 走边缘直供 |
| 内联所有 CSS/JS | 单文件 base.css 已 88 KB 磁盘（br 后 ~13 KB），收益 <20ms |

## 8b. 怎么测「欧美客户的真实速度」（重要）

Section 1-3 的数字是**从开发机（中国）访问新加坡边缘**测的，它对欧美客户**没有参考价值** ——
握手成本完全不同，源站渲染才是共同项。要拿欧美数据，照下面三选一。

### A. 在海外机器上跑已有探针（最准，30 秒）

`scripts/e2e/perf_probe.py` 是纯 curl，不需要任何第三方服务。在**美国或欧洲的电脑 / VPS** 上：

```bash
git pull
python scripts/e2e/perf_probe.py --repeats 5
```

输出就是当地真实 TTFB（含 dns/tcp/tls 分解，能直接看出 RTT 成本）。
放 VPS 上比家用宽带准（不受咖啡厅 Wi-Fi 干扰）。

### B. 浏览器 devtools 一眼看边缘落点（10 秒，零工具）

打开站点 → F12 → Network → 刷新 → 点第一个 document 请求 → Response Headers：

```
x-vercel-id: cdg1::iad1::2026-10-04T01:40:42Z
              └──┘  └──┘
             边缘  函数执行区域
```

- `iad1::iad1` → 边缘与函数同区（美国东最好情形）
- `cdg1::iad1` → 边缘在法国、**函数跑在美国东**（欧洲访客跨大西洋回源）
- `sin1::iad1` → 边缘在新加坡、函数在美东（亚太访客横穿太平洋）

这是**零成本的定位方法**，让海外同事截个图就能告诉你落点。

### C. 真实用户聚合（长期）

- **Vercel → Analytics → Function Invocations / Duration**：p50/p75 函数执行时长（= 源站渲染，与地理位置无关）。
- **GSC → 核心网页指标 → 完整报告**：按国家/设备的真实用户 LCP、INP、CLS（28 天窗口）。

### 推算参考（未实测，只作量级参考）

共同项 = 源站渲染 ~210ms（全球一致，从上面「570ms − 360ms 握手」推得）。
加上各区到本地边缘的 RTT：

| 访客 | 边缘 | 额外 RTT | 推算 TTFB |
|---|---|---|---|
| 美国东海岸 | `iad1` | ~15–40 ms | ~230–250 ms |
| 美国西海岸 | `iad1`/`sfo1` | ~30–60 ms | ~240–270 ms |
| 英国 | `lhr1` → 函数 `iad1` | ~80–110 ms | ~290–320 ms |
| 德国/法国 | `cdg1`/`fra1` → `iad1` | ~85–120 ms | ~295–330 ms |
| 中国（对照） | `sin1` → `iad1` | ~330–360 ms | ~560–590 ms（实测） |

> 这些是**量级估算，不是实测**。做优化决策前的基准请用方法 A 或 B 取真数。

## 9. 复测节奏

- 每次改动后：`perf_probe.py` 跑一次，把表贴回来对比。
- 每月：GSC → 核心网页指标 看移动端 LCP/INP/CLS 的 field data（真实用户，比实验室准）。
- 2–4 周后：Semrush 复测关键词（收录 ≠ 排名）。
