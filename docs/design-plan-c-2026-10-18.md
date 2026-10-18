# 配色落地方案清单 —— 方案C（钴蓝 + 浮光棕 + 碳灰）

- 日期：2026-10-18
- 状态：**已执行：步骤1（令牌）、步骤2（hero 渐变）、步骤3（文字 logo nav+footer）。待执行：步骤4（图片）、步骤5（守卫已加，随步骤1/2落）、步骤6（build/线上实证）** —— 钴蓝 #1068C9 + 暖碳灰 #1F1E1C + 暖棕三档 + footer 暖色分隔线已落地并通过守卫
- 决策依据：
  - 商标青 `#00CFF4`（H189°，不可改）仅作 favicon，页面品牌色由文字 logo 决定
  - 用户拍板走 **方案C**：UI 主蓝 = 钴蓝 `#1068C9`；文字 logo = 选项 C `#1068C9`（去 3D 倒角）
  - 绿茵场项目封面不改内容、只统外框；深底产品图随碳灰卡顺其自然（已定）
- 配套审计：`docs/design-audit-color-2026-10-17.md`

---

## 目标色板（方案C）

| 角色 | 色值 | 说明 |
|---|---|---|
| 主蓝（唯一真源） | `#1068C9` (16,104,201) | 改 `--accent-brand` 默认；admin `SiteConfig.accent_color` 仍可覆盖 |
| 浅色主题 accent | `#1068C9`（显式）或 `color-mix(#1068C9,#000 18%)`≈`#0E56A8` | 白底 5.4–5.5:1，达标 |
| hover / 渐变尾 | `#4A93D9`（≈主蓝 +15~20% 白） | |
| soft（选中底） | `rgba(16,104,201,0.08)` | |
| 暖棕·主 | `#B89076` (184,144,118) | 点缀、分隔线、次级 CTA、暖光 motif |
| 暖棕·深（浅底文字） | `#9A7256` | |
| 暖棕·浅（暗底辉光） | `#D8B89E` | |
| 深色 surface | `#1F1E1C`（暖碳灰） | 取代 `#080D1F`，并暖化中性色 |
| Logo 注册商标青 | `#00CFF4` | **仅 favicon，不动** |

---

## 步骤 1 — CSS 令牌（`static/css/base.css`）

### 1.1 `:root` 块
- `--accent-brand: #0088FF` → **`#1068C9`**
- `--bg: #080D1F` → **`#1F1E1C`**
- `--bg-soft: #111827` → **`#262420`**（暖化）
- `--bg-raised: #1A2035` → **`#2E2B26`**（暖化）
- `--ink-soft: #D9D9E3` → **`#E4DFD7`**（暖化）
- `--ink-mute: #8A8A95` → **`#9C958B`**（暖化）
- `--ink-subtle: #5A5A65` → **`#6E675E`**（暖化）
- `--accent-hover: #269DFF` → **`#3E8FD8`**（≈主蓝+15%白，仅老浏览器字面）
- `--accent-soft: rgba(0,136,255,0.10)` → **`rgba(16,104,201,0.10)`**
- `--accent-glow: rgba(0,136,255,0.22)` → **`rgba(16,104,201,0.22)`**
- `--accent-deep: #0066BF` → **`#0E56A8`**（仅老浏览器字面；现代浏览器由 color-mix 派生）
- `--line: rgba(255,255,255,0.07)` → **`rgba(237,233,227,0.08)`**（暖化）
- `--line-strong: rgba(255,255,255,0.14)` → **`rgba(237,233,227,0.15)`**（暖化）
- 新增暖棕三档（静态字面，admin 不注入）：
  ```
  --accent-warm:       #B89076;
  --accent-warm-deep:  #9A7256;
  --accent-warm-soft:  #D8B89E;
  ```

### 1.2 `[data-theme="light"]` 块
- `--accent: #006AC7` → **`#1068C9`**（或 `color-mix(var(--accent-brand), #000 18%)`）
- `--accent-soft` / `--accent-glow` 同步改 `rgba(16,104,201,…)`
- 保留 `@supports color-mix` 派生（hover/deep/soft/glow 自动跟随新品牌，无需再写）

### 1.3 老浏览器字面兜底
- 第 17/18/19/20 行等 `#0088FF`/`#269DFF`/`#0066BF`/`rgba(0,136,255,…)` 字面 → 同步改为 `#1068C9` 家族
- 模板中 `rgba(0, 136, 255, 0.06)`（sidebar 浅色激活底，`base.css` 约 1940/2009）→ 改为 `rgba(16,104,201,0.06)`（其后的 color-mix 行已覆盖现代浏览器，仅保老浏览器一致）

> ⚠️ 铁律：admin 只注入 `--accent-brand`，其余蓝全部由它经 color-mix 派生；**禁止新增写死蓝色字面量**（暖棕三档属刻意新增，须登记守卫）。

---

## 步骤 2 — 收敛 hero 渐变（去掉青色端点）

`static/css/base.css`：
- `.hero-stat-num`：`linear-gradient(135deg, var(--accent) 0%, #4D9BFF 50%, #00D4FF 100%)`
  → `linear-gradient(135deg, var(--accent) 0%, color-mix(in srgb, var(--accent), #fff 30%) 100%)`
  （删掉 `#00D4FF` 第三停，改为同相微渐变）
- `.hero-stat-num .unit`：`linear-gradient(135deg, #4D9BFF 0%, #00D4FF 100%)`
  → `linear-gradient(135deg, color-mix(in srgb, var(--accent), #fff 30%) 0%, var(--accent) 100%)`
- `.hero-title .line.accent` 用 `#4D9BFF`（=主蓝+30%白）保留，无需动

---

## 步骤 3 — 文字 logo（选项 C）

- **重制 `static/images/logo.webp`**：颜色 `#0068A8` → **`#1068C9`**，并**去掉 3D 倒角/高光/投影**，改扁平单色；保留字体字怀与 `®`
- 备选（更优）：把 `<img id="brandLogo">` 换成 CSS 文本 `SolarOne®`，`color: var(--accent)`，自动跟随主题与 admin 注入；免去图片重色
- 深色主题下该图（或文本）显示 `#1068C9`，在碳灰 `#1F1E1C` 上可见，无需第二张图
- ✅ **执行扩展（2026-10-18）**：footer 的 `.footer-brand-name` 同样改为 `<span class="brand-wordmark">SolarOne®</span>`（`color: var(--accent)`），导航与页脚字标统一；`.footer-brand-name` 颜色 `var(--ink)`→`var(--accent)`，浅色主题覆盖 `#FFFFFF`→`var(--accent)`（footer 在浅色主题亦为深底，accent 可见）

---

## 步骤 4 — 图片替换（沿用审计 §5，商标青不动）

| 优先级 | 文件 | 动作 |
|---|---|---|
| P0 | `static/images/products/rt410-rgbw/rgbw-rt410-red.webp` | 换中性白光封面；红色留 RGBW 详情页 gallery |
| P1 | `static/images/hero-main-1/2/3.webp`（含 `-portrait`/`-1280` 变体） | 去色偏 → 中性冷暗/蓝调 |
| P1 | `static/images/about-main.webp` | 去青绿 |
| 保留 | 绿茵场 8 张 / 深底产品图 / 白底棚拍 / 暖橙·冷蓝实景照 | 不改内容 |

---

## 步骤 5 — 守卫（pages/tests 或 CSS 断言）

- [ ] 断言 `base.css` 中 `.hero-stat-num` / `.unit` 背景**不再含** `#00D4FF`（青色端点已删）
- [ ] 断言深色 `--bg` 解析为 `#1F1E1C`（暖碳灰），非 `#080D1F`
- [ ] 断言除刻意老浏览器兜底外，无 `#0088FF`/`#006AC7` 残留蓝字面量
- [ ] 断言 `--accent-warm` / `--accent-warm-deep` / `--accent-warm-soft` 三档已定义且至少 1 处被引用
- [ ] （可选）图片测试：重制后 `logo.webp` 主色 ≈ `#1068C9`±容差；`rgbw-rt410-red` 不再作为产品封面
- 守卫须配**变异探针**（改实现→变红→还原→`git diff --stat` 零残留），非空转

---

## 步骤 6 — 执行顺序与验证

1. 步骤 1（令牌）→ 2（渐变）→ 3（logo）→ 4（图片）→ 5（守卫）
2. `E:/Python/python3/python.exe manage.py check`
3. `build.sh`（fail-closed，确认 collectstatic/manifest/静态索引通过）
4. `scripts/dev_preview.py` 本地预览，肉眼核对浅/深双主题
5. 线上实证：`curl -L https://www.solaronelighting.com/...`（带 www，避免 308）核对渲染与对比度
6. 对比度复核：正文蓝 `#1068C9`/`#0E56A8` 白底 ≥4.5:1（实测 5.4–5.5:1）；`#B89076` 仅大字号/点缀（碳灰上 4.8:1，禁排正文）
7. commit（用户手动 push；本地提交按项目铁律显式 `git add` 逐文件 + 临时 message 文件）

---

## 风险

- 浅色主题 `#1068C9` 5.4:1 达标；若改用 `#0E56A8` 同样达标，二选一保持一致
- 浮光棕在碳灰上 4.8:1 → **只用于大字号/点缀/非正文**
- 改 `--accent-brand` 默认后，hover/deep/soft/glow 自动派生（好）；务必同步更新老浏览器字面兜底，否则旧浏览器下色差
- favicon 商标青（H189）与 UI 钴蓝（H208）存在 19° 色差 —— **方案C 已知取舍，已在决策中接受**
- 暖棕三档为新写死字面（非 admin 注入），须登记守卫防回归
