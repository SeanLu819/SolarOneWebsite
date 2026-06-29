# Solarone 体育照明网站 · 架构蓝图

> 基于对 Musco、Cooper Lighting Ephesus、ONOR、SCL、Signify 等国际体育照明领军网站的深度拆解分析，为 Solarone 重新梳理完整的网站架构与设计规范。

---

## 一、竞品分析总结

### 1.1 竞品概览

| 竞品 | 定位 | 核心特色 |
|------|------|----------|
| **Musco** (www.musco.com) | 全球最大体育照明系统商 | 深色主题+金色强调、案例驱动、奥运会合作伙伴背书 |
| **Cooper Ephesus** (cooperlighting.com/ephesus) | Cooper旗下专业体育照明品牌 | 场景化产品映射、白皮书/Playbook资源库、AI助手 |
| **ONOR** (onorled.com) | 中高端LED体育泛光灯制造商 | 产品线丰富、解决方案按运动细分、外贸出口导向 |
| **SCL** (stadiumlight.com) | LED体育照明系统集成商 | 深色主题+金色CTA、智能控制系统独立产品线 |
| **Signify** (signify.com) | 全球照明领导者 | 极简现代、白色背景、多市场覆盖 |

### 1.2 行业共性模式

**内容组织 — "双轨制"结构（100%采用）**
- **按运动/场景类型**：Football, Tennis, Baseball, Basketball, Soccer, Hockey 等
- **按产品/技术类型**：LED灯具系列、控制系统、供电配置等

**案例驱动的内容策略（100%采用）**
- 每家网站都将项目案例作为核心内容
- Musco：项目轮播+客户证言
- Ephesus：详尽案例研究页（含PDF白皮书），按专业/大学/公立分级
- 案例 = 最强销售工具

**技术资源深度提供（80%采用）**
- 产品数据表下载（IES文件、Datasheet、尺寸图）
- 照明设计工具（在线计算器或独立App）
- 安装指南、白皮书、FAQ

### 1.3 Musco 架构拆解（最接近目标的参考）

```
顶部公告横幅（LA28奥运合作伙伴）
├── 导航栏（固定）：Solutions | Projects | About | Careers | Control-Link | 语言切换
├── 全屏 Hero — 体育场夜景 + "You Always Know When It's Musco"
├── 设施解决方案卡片（Sports / Transportation / Entertainment / Videoboards）
├── 品牌价值区 — "Projects Made Simple" + 关键数据（10,000+ / 1,900+ / 24/7/365）
├── 品牌故事区 — 视频播放
├── 合作伙伴Logo墙（FIFA, MLB, NCAA 等16个）
├── Featured Projects 轮播（含客户证言）
├── Featured Articles（新闻动态）
├── 底部CTA — "Let's Make It Happen, Together"
└── Footer — 联系方式、社交媒体、服务支持、快速链接
```

### 1.4 Ephesus 架构拆解（功能最全面）

```
顶部CTA — Request More Information | Where to Buy
├── Explore Ephesus Solutions（按场馆分类）
│   ├── Stadiums / Arenas / Track & Ball Fields / Diamonds / Courts
│   ├── Parks & Rec / Gymnasiums / Fieldhouses / Natatoriums
│   └── Parking / Convention Centers / Amphitheaters
│   （每个场馆类型下直接映射推荐产品）
├── 产品展示（按供电配置分两大类）
│   ├── Integral Power（LumaSport 8/16, LumaVision, ArenaVision）
│   └── Remote Power（LumaSport 8/12/16 Remote Power System）
├── 资源/教育区
│   ├── Playbooks（安装指南）
│   ├── Bright Papers（白皮书/行业洞察）
│   ├── Case Studies（按Professional/Collegiate/Municipal分类）
│   └── FAQs
├── Light ARchitect App推广
└── 联系CTA
```

---

## 二、分阶段上线规划

### 2.1 阶段总览

| 阶段 | 内容 | 上线目标 |
|------|------|----------|
| **Phase 1（当前）** | 单页静态站：产品 + 项目案例 + 公司介绍 + 联系 + 社媒 | 展示产品与项目，建立品牌信任 |
| **Phase 2** | 多页面：独立产品页、案例详情页、About 页 | 深度内容，SEO优化 |
| **Phase 3** | Resources 资源中心（技术文档/白皮书/FAQ）+ 设计工具 | 技术深度，专业买家转化 |
| **Phase 4** | WordPress 集成 + 多语言 + 客户门户（按 lamp_overseas_site_manual.md） | 全球化运营 |

### 2.2 Phase 1 核心定位

**首要目的**：向欧美客户展示产品能力和项目实绩，建立信任
**核心功能**：
- 产品展示 — 让客户快速了解产品线和核心参数
- 项目案例 — 用真实项目证明实力（国际案例优先）
- 公司介绍 — 品牌故事、资质认证、发展历程
- 联系方式 — 邮箱、电话、WhatsApp、在线表单
- 社交媒体 — Facebook、YouTube 等欧美主流平台链接

**不做（留给后续阶段）**：
- 解决方案/场馆分类导航（Phase 2）
- 资源中心/白皮书下载（Phase 3）
- 多语言切换（Phase 4）
- 在线报价系统（Phase 4）

---

## 三、Phase 1 网站架构

### 3.1 信息架构图（Phase 1 简化版）

```
首页 (Homepage) — 单页滚动
│
├── 1. Products（产品中心）— 前期 3 大系列
│   ├── M 系列 — 模块化灯具（6M / 9M / 12M 等）
│   ├── RT410 系列 — LED 泛光灯
│   ├── HB 系列 — 工矿灯
│   └── 更多系列（后续阶段添加）
│
├── 2. Projects（项目案例）
│   ├── 精选项目轮播/展示
│   │   ├── 项目实景图
│   │   ├── 项目名称 + 地点
│   │   └── 客户证言（引用 + 姓名 + 职位）
│   └── 按运动类型标签筛选（可选）
│
├── 3. About（公司介绍）
│   ├── 品牌故事 / 公司简介
│   ├── 关键数据（项目数、覆盖国家、节能率等）
│   ├── 合作伙伴 & 认证
│   └── 发展历程（可选，轻量展示）
│
├── 4. Contact（联系方式）
│   ├── 联系信息（邮箱、电话、地址）
│   ├── WhatsApp 快捷联系
│   └── 在线咨询表单（Name/Email/Phone/Message）
│
└── 5. Social Media（社交媒体）
    ├── Facebook
    ├── Instagram
    ├── YouTube
    └── TikTok
```

### 3.2 Phase 1 导航结构

**桌面端（>1024px）— 水平导航（精简 3+1 结构）**

```
[Logo: Solarone]   Products   Projects   About   [Contact Us ▸]   [🔍]
```

导航项只有 3 个（产品/项目/关于），加 1 个 CTA 按钮（联系我们）。
简洁明了，用户无需下拉菜单即可直达目标区域。

**平板端（768-1024px）— 水平导航不变**

```
[Logo]   Products   Projects   About   [Contact Us ▸]
```

与桌面端结构一致，仅间距微调。

**手机端（<768px）— 汉堡菜单 + 侧滑面板**

```
[Logo]                              [Contact Us ▸] [☰]
```

- 侧滑面板展示：Products / Projects / About / Contact（4项）
- 社媒链接放在 Footer（所有端均可见）

### 3.3 Phase 1 首页内容布局

```
┌────────────────────────────────────────────────────────────────┐
│  [固定导航栏]                                                   │
│  Logo | Products | Projects | About | [Contact Us ▸]          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  Section 1: HERO — 全屏（100vh）                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  大幅体育场夜景背景 / 深色渐变 + 光效动画                   │  │
│  │  主标题: 品牌标语                                         │  │
│  │  副标题: 价值主张（如 Precision LED Lighting Systems）       │  │
│  │  [View Products ▸]  [Contact Us ▸]                        │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Section 2: 产品展示 — "Our Products"                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐               │
│  │  产品白底图  │ │  产品白底图  │ │  产品白底图  │               │
│  │  M Series   │ │  RT410      │ │  HB Series  │               │
│  │  核心参数    │ │  核心参数    │ │  核心参数    │               │
│  │  核心卖点    │ │  核心卖点    │ │  核心卖点    │               │
│  │  [Details→] │ │  [Details→] │ │  [Details→] │               │
│  └────────────┘ └────────────┘ └────────────┘               │
│                                                                │
│  Section 3: 项目案例 — "Featured Projects"                    │
│  ┌──────────────────┐ ┌──────────────────┐                   │
│  │  项目实景照片     │ │  项目实景照片     │                   │
│  │  项目名称 + 地点  │ │  项目名称 + 地点  │                   │
│  │  项目简介         │ │  项目简介         │                   │
│  │  客户证言         │ │  客户证言         │                   │
│  │  " — Name, Title │ │  " — Name, Title │                   │
│  └──────────────────┘ └──────────────────┘                   │
│  （可扩展为 3-4 个项目卡片）                                     │
│                                                                │
│  Section 4: 品牌价值 — "Why Solarone"                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  品牌故事简介                                             │  │
│  │                                                          │  │
│  │   500+          50+           60%          24/7           │  │
│  │   Projects      Countries     Energy Save   Support      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Section 5: 合作伙伴/认证 — "Trusted Worldwide"                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  认证Logo / 合作伙伴Logo 墙（横向排列或滚动）               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Section 6: 联系我们 — "Get in Touch"                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ┌──────────────┐  ┌──────────────────────┐            │  │
│  │  │  联系信息      │  │  在线咨询表单          │            │  │
│  │  │  ✉ Email     │  │  Name  ________________│            │  │
│  │  │  ☎ Phone     │  │  Email ________________│            │  │
│  │  │  ▲ WhatsApp  │  │  Phone ________________│            │  │
│  │  │  ▣ Address   │  │  Message _____________│            │  │
│  │  │              │  │  [Submit ▸]           │            │  │
│  │  └──────────────┘  └──────────────────────┘            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                │
│  Footer                                                       │
│  ┌────────────┬────────────┬────────────┬────────────┐       │
│  │  Solarone   │ Quick Links│ Social      │ Contact    │       │
│  │  品牌描述    │ Products  │ ▶ Facebook  │ ✉ Email   │       │
│  │             │ Projects  │ ▶ YouTube   │ ☎ Phone   │       │
│  │             │ About     │ ▶ LinkedIn  │ ▲ WhatsApp│       │
│  │             │           │ ▶ Instagram │ ▣ Address  │       │
│  └────────────┴────────────┴────────────┴────────────┘       │
│  © 2025 Solarone Lighting. All rights reserved.               │
│  [Privacy Policy] [Terms of Service]                         │
└────────────────────────────────────────────────────────────────┘
```

### 3.4 各端布局策略（Phase 1）

| 组件 | PC (≥1024px) | 平板 (768-1023px) | 手机 (<768px) |
|------|-------------|-------------------|---------------|
| 导航 | 水平 3+1 导航 | 水平 3+1 导航 | 汉堡菜单 + 侧滑面板 |
| Hero | 全屏 + 双CTA按钮 | 80vh + 双CTA | 70vh + 堆叠CTA |
| 产品网格 | 3列 | 2列 | 1列堆叠 |
| 项目展示 | 2列卡片 | 2列 / 1列 | 1列堆叠 |
| 统计数字 | 4列横排 | 2x2网格 | 2x2网格 |
| Logo墙 | 横向排列 | 横向滚动 | 横向滚动 |
| 联系区 | 左信息+右表单（双列） | 左信息+右表单（双列） | 信息在上、表单在下（堆叠） |
| Footer | 4列 | 2x2网格 | 单列折叠 |
| 社媒图标 | Footer独立列 | Footer合并列 | Footer底部横排 |

---

## 四、设计风格规范

### 4.1 整体风格定位

| 属性 | 定义 |
|------|------|
| **风格名称** | Industrial Dark Tech（工业深色科技风） |
| **风格关键词** | 专业、精准、科技感、可信赖 |
| **视觉参考** | 深色基调 + 蓝色科技强调 + 体育场馆实景摄影 |
| **情感目标** | 传达"可信赖的全球体育照明技术专家"形象 |

### 4.2 配色方案

**主色板（Dark Theme）**

| Token | 色值 | 用途 |
|-------|------|------|
| `--bg` | `#08080B` | 主背景（近黑色） |
| `--bg-soft` | `#0F0F14` | 次级背景、卡片底色 |
| `--bg-raised` | `#141820` | 悬浮面板、弹窗底色 |
| `--ink` | `#FFFFFF` | 主文字、标题 |
| `--ink-soft` | `#D9D9E3` | 正文文字 |
| `--ink-mute` | `#8A8A95` | 次要说明文字 |
| `--ink-subtle` | `#5A5A65` | 占位文字、禁用状态 |

**强调色（Branding）— 蓝色主调**

| Token | 色值 | 用途 |
|-------|------|------|
| `--accent` | `#0077ED` | 主强调色 — CTA按钮、链接、关键数字 |
| `--accent-hover` | `#0090FF` | CTA按钮悬停态 |
| `--accent-soft` | `rgba(0, 119, 237, 0.10)` | 标签背景、选中态底色 |
| `--accent-glow` | `rgba(0, 119, 237, 0.22)` | 光晕效果、焦点状态 |
| `--accent-deep` | `#005BB5` | 深蓝色，用于渐变底色、hover加强 |

**辅助色（扩展场景）**

| Token | 色值 | 用途 |
|-------|------|------|
| `--success` | `#22C55E` | 成功状态、节能数据 |
| `--info` | `#38BDF8` | 信息提示、技术参数 |
| `--warning` | `#F59E0B` | 警告、太阳能产品系列（可选区分） |
| `--border` | `rgba(255,255,255,0.07)` | 分割线、卡片边框 |
| `--border-strong` | `rgba(255,255,255,0.14)` | 强调边框、CTA描边 |

**配色说明**
- 蓝色 `#0077ED` 作为品牌强调色，传递科技感、专业性、可靠性
- 与现有 `index.html` 保持一致，减少重构成本
- 深色背景 + 蓝色强调 = 行业内独特的"科技工业风"定位，区别于 Musco 的金色路线

### 4.3 字体规范

| 用途 | 字体 | 字重 | 备注 |
|------|------|------|------|
| **标题/H1-H3** | Space Grotesk | 600/700 | Google Fonts，科技感几何无衬线 |
| **正文** | Inter | 400/500 | Google Fonts，清晰可读 |
| **标签/导航** | Inter | 500 | 大写字母，字母间距 0.05em |
| **数据/数字** | IBM Plex Mono | 500 | 用于大数字统计、技术参数 |
| **备选** | system-ui, sans-serif | — | 字体加载失败时回退 |

**字体层级**

| 层级 | 大小(PC) | 行高 | 字重 |
|------|----------|------|------|
| H1 | 56px (clamp: 40-64px) | 1.1 | 700 |
| H2 | 40px (clamp: 32-48px) | 1.2 | 600 |
| H3 | 28px (clamp: 24-32px) | 1.3 | 600 |
| Body | 16px (clamp: 15-18px) | 1.6 | 400 |
| Small | 14px | 1.5 | 400 |
| Nav Label | 12px | — | 500 |

> 使用 `clamp()` 实现流式字体大小，无需断点切换。

### 4.4 间距系统

基于 8px 网格：

| Token | 值 | 用途 |
|-------|------|------|
| `--sp-1` | 8px | 组件内间距 |
| `--sp-2` | 16px | 元素间距、卡片内边距 |
| `--sp-3` | 24px | 组件间距 |
| `--sp-4` | 48px | 区块间距 |
| `--sp-5` | 96px | 大区块间距 |
| `--sp-6` | 160px | 首屏上下留白 |

### 4.5 响应式断点

采用 Mobile-First 策略：

| 断点名称 | 值 | 设备适配 |
|----------|------|----------|
| `--bp-xs` | 375px | 小屏手机 |
| `--bp-sm` | 640px | 大屏手机 |
| `--bp-md` | 768px | 平板竖屏 |
| `--bp-lg` | 1024px | 平板横屏 / 小笔记本 |
| `--bp-xl` | 1280px | 桌面端（标准） |
| `--bp-2xl` | 1536px | 大桌面 / 外接显示器 |

### 4.6 图片与视觉规范

| 类型 | 规格 | 要求 |
|------|------|------|
| Hero背景 | 1920x1080, WebP格式 | 体育场馆夜景实景摄影 |
| 产品白底图 | 800x800+, PNG/WebP | 纯白背景，产品居中 |
| 项目案例图 | 1200x800+, WebP | 真实安装场景照片 |
| Logo墙图标 | SVG优先，PNG备选 | 单色白色或原色 |
| 图标 | SVG, 24x24 | 线性图标(linear icons) |
| 社媒图标 | SVG, 24x24 | 品牌官方图标（Facebook/YouTube/LinkedIn等） |

**图片处理原则**
- Hero 使用 `picture` + `srcset` 响应式图片
- 非首屏图片使用 `loading="lazy"` 懒加载
- 优先使用 WebP 格式
- 大图使用 CSS `object-fit: cover` 裁切

### 4.7 动效规范

| 类型 | 实现 | 时长 | 使用场景 |
|------|------|------|----------|
| 滚动渐入 | IntersectionObserver + CSS transform/opacity | 600ms ease-out | 所有区块首次进入视口 |
| 数字计数器 | JS requestAnimationFrame | 2s ease-out | Stats 统计数字 |
| 卡片悬停 | CSS transform: translateY(-8px) + box-shadow | 300ms | 产品卡片、项目卡片 |
| 按钮悬停 | CSS 背景色渐变 + 轻微放大 | 200ms | 所有按钮 |
| 链接下划线 | CSS ::after 伪元素 | 200ms | 文字链接 |
| Hero光效 | CSS 渐变动画 | 8s infinite | Hero 背景 |

**动效原则**
- 所有动画仅使用 `transform` 和 `opacity`（GPU加速属性）
- 尊重 `prefers-reduced-motion` 系统设置
- Mobile 端减少动画复杂度，降低性能消耗

### 4.8 组件规范速查

**按钮**

| 类型 | 样式 | 用途 |
|------|------|------|
| Primary | 蓝色填充 `#0077ED` + 白色文字 | 主CTA（Contact Us等） |
| Secondary | 透明 + 蓝色边框 + 蓝色文字 | 次CTA（View Products等） |
| Ghost | 透明 + 白色边框 + 白色文字 | 辅助操作 |
| Text | 无边框 + 蓝色文字 + 右箭头 | 链接型CTA |

**卡片**

| 类型 | 样式 |
|------|------|
| Product Card | 产品图 + 名称 + 核心参数 + 核心卖点 + 悬停CTA |
| Project Card | 项目实景图 + 名称地点 + 项目简介 + 客户证言 |

**社交媒体链接**

| 平台 | 优先级 | 位置 |
|------|--------|------|
| **Facebook** | P0（必须有） | Footer + 可选：Contact区 |
| **Instagram** | P0（必须有） | Footer |
| **YouTube** | P0（必须有） | Footer |
| **TikTok** | P0（必须有） | Footer |

社媒链接统一使用品牌官方 SVG 图标，深色主题下白色图标，悬停变为蓝色（`#0077ED`）。
Footer 社媒区设计为图标横排，间距 `--sp-2`(16px)，图标尺寸 20x20 或 24x24。

**联系表单**

| 字段 | 类型 | 必填 |
|------|------|------|
| Name | text | Yes |
| Email | email | Yes |
| Phone | tel | No |
| Project Type / Message | textarea | Yes |

Submit 按钮使用 Primary 样式（蓝色填充）。表单下方可选显示 WhatsApp 快捷联系按钮。

---

## 五、竞品设计风格对比

### 5.1 视觉风格矩阵

| 品牌 | 主背景 | 强调色 | 字体风格 | 布局特点 |
|------|--------|--------|----------|----------|
| Musco | 深色 #0A0A0A | 金色 #F5A623 | 现代无衬线 | 全宽分段式 |
| Ephesus | 白色 #FFFFFF | 蓝色(Cooper品牌) | 企业级无衬线 | 左侧栏+内容区 |
| ONOR | 白色+深蓝导航 | 黄色/橙色 | 传统B2B无衬线 | 信息密集多列 |
| SCL | 深蓝/深色 | 金色CTA | 现代无衬线 | 长页面滚动 |
| Signify | 白色极简 | Philips蓝 | 极简无衬线 | 大量留白 |

### 5.2 Solarone 风格定位

**深色 + 蓝色科技风**，在行业中形成差异化：

| 对比维度 | Musco 路线 | Solarone 路线 |
|----------|-----------|--------------|
| 背景 | 深色 | 深色（一致） |
| 强调色 | 金色（温暖、高端） | 蓝色（科技、精准） |
| 品牌信号 | 值得信赖的领导者 | 技术驱动的创新者 |
| 差异化优势 | 与 Musco 视觉雷同风险 | 蓝色科技感在深色背景下更醒目，传递 LED + 智能控制的技术属性 |

**与现有设计的关系**
- 保留现有 `index.html` 的蓝色强调色 `#0077ED`（无需修改）
- 保留 Space Grotesk 作为标题字体（科技感契合蓝色主题）
- 保留 Inter + IBM Plex Mono 组合
- 主要变更：从简单单页 → 标准化 6 区块布局（Hero / Products / Projects / Brand Value / Certifications / Contact）

---

## 六、技术实现建议

### 6.1 当前阶段：Phase 1 单页静态站

沿用现有技术栈：
- HTML5 单文件
- CSS3 内联样式 + CSS 变量
- Vanilla JS（最小依赖）
- 目标：首屏加载 < 1.5s

### 6.2 响应式实现要点

```css
/* Mobile First */
.container { padding: 0 16px; }          /* 手机 16px 边距 */
@media (min-width: 768px)  { .container { padding: 0 32px; } }  /* 平板 */
@media (min-width: 1280px) { .container { max-width: 1280px; margin: 0 auto; } }  /* 桌面 */

/* 导航响应式 */
.nav-links    { display: none; }            /* 手机隐藏 */
@media (min-width: 768px) { .nav-links { display: flex; } }  /* 平板以上显示 */
.hamburger    { display: block; }           /* 手机显示 */
@media (min-width: 768px) { .hamburger { display: none; } }  /* 平板以上隐藏 */

/* 产品网格响应式 */
.grid-products { grid-template-columns: 1fr; }                    /* 手机 1列 */
@media (min-width: 768px)  { .grid-products { grid-template-columns: repeat(2, 1fr); } }  /* 平板 2列 */
@media (min-width: 1280px) { .grid-products { grid-template-columns: repeat(3, 1fr); } }  /* 桌面 3列 */

/* 联系区响应式 */
.contact-grid { grid-template-columns: 1fr; }          /* 手机堆叠 */
@media (min-width: 768px) { .contact-grid { grid-template-columns: 1fr 1fr; } }  /* 平板以上双列 */
```

---

## 七、与现有项目的关系

### 7.1 现有文件处理

| 文件 | 作用 | 处理建议 |
|------|------|----------|
| `index.html` | 当前单页站点 | **重构**：按 Phase 1 架构重写，保留蓝色主题 |
| `index.backup.html` | 备份 | 保留不动 |
| `docs/spec-single-page.md` | 原始架构文档 | 由本文档取代 |
| `docs/lamp_overseas_site_manual.md` | WordPress部署手册 | 保留，Phase 4 参考 |
| `images/processed/` | 产品图片（RT200-M, RT400-HB, SolarOne等） | 保留，新页面直接引用 |

### 7.2 Phase 1 核心变更（相对现有 index.html）

1. **架构**：从简单混合布局 → 标准化 6 区块布局（Hero / Products / Projects / Brand Value / Certifications / Contact）
2. **内容增加**：项目案例区、品牌数据统计区、认证Logo墙、完整联系表单、社媒链接
3. **导航简化**：从多导航项 + Mono字体 → 3+1 精简导航（Products / Projects / About + Contact CTA）
4. **响应式完善**：全面的 PC/平板/手机三端适配
5. **保留不变**：蓝色强调色 `#0077ED`、深色背景、Space Grotesk + Inter + IBM Plex Mono 字体组合

---

## 八、总结

本文档基于对 5 个国际体育照明领军网站的深度拆解，结合 Solarone 的实际业务需求，确立了分阶段上线的网站架构：

**Phase 1（当前阶段）核心：**
1. **三大内容板块** — Products + Projects + About（展示为主，建立信任）
2. **联系方式 + 社媒** — 邮箱/电话/WhatsApp + Facebook/YouTube（欧美客户习惯）
3. **蓝色科技风** — 深色背景 + 蓝色强调色 `#0077ED`，区别于 Musco 金色路线
4. **三端响应式** — Mobile First，PC 水平导航、平板简化、手机汉堡菜单
5. **单页静态站** — HTML + CSS + Vanilla JS，快速上线

**后续阶段预留：**
- Phase 2：独立产品页、案例详情页、多页面路由
- Phase 3：资源中心（技术文档/白皮书/设计工具）
- Phase 4：WordPress 多语言站点 + 客户门户

**下一步**：基于此架构蓝图，开始重构 `index.html` 首页。
