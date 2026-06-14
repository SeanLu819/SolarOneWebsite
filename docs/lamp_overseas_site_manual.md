# 灯具产品出海独立站 · 开发手册

> **目标市场**：北美（美国 / 加拿大）  
> **服务器**：GoDaddy Managed WordPress Ultimate  
> **核心原则**：先做最简单、最快上线的站点，后续逐步迭代

---

## 目录

1. [技术架构总览](#1-技术架构总览)
2. [域名与 DNS 配置](#2-域名与-dns-配置)
3. [服务器环境准备](#3-服务器环境准备)
4. [WordPress + WooCommerce 安装配置](#4-wordpress--woocommerce-安装配置)
5. [支付与物流配置](#5-支付与物流配置)
6. [主题与插件安装](#6-主题与插件安装)
7. [SEO 基础配置](#7-seo-基础配置)
8. [安全与性能优化](#8-安全与性能优化)
9. [产品上架规范](#9-产品上架规范)
10. [跨浏览器兼容性注意要点](#10-跨浏览器兼容性注意要点)
11. [测试验收清单](#11-测试验收清单)
12. [实施路线图](#12-实施路线图)
13. [后续迭代方向](#13-后续迭代方向)

---

## 1. 技术架构总览

### 1.1 一句话架构

```
WordPress + WooCommerce（GoDaddy 主机）
  + Cloudflare（DNS + CDN + WAF）
  + Stripe + PayPal（支付）
  + WooCommerce Shipping & Tax（物流）
  + Google Analytics 4 + Meta Pixel（数据分析）
```

### 1.2 架构拓扑图

```
用户请求（北美）
      ↓ HTTPS
Cloudflare（DNS + CDN + WAF）
      ↓ 动态请求回源
GoDaddy Managed WordPress Ultimate
      ↓
WordPress + WooCommerce（PHP 8.1 + Redis 缓存）
      ↓
MySQL（产品/订单数据）+ Redis（对象缓存）
      ↓
第三方服务：Stripe / PayPal / USPS-UPS-DHL / Klaviyo / GA4
```

### 1.3 组件职责说明

| 组件 | 职责 | 备注 |
|------|------|------|
| GoDaddy 主机 | 应用服务器、PHP 执行、数据库 | Managed WordPress 已优化 |
| Cloudflare | CDN 加速、DNS、安全防护 | 免费版即可 |
| WordPress | CMS 内容管理核心 | PHP 8.1+ |
| WooCommerce | 电商功能（产品/购物车/订单） | 插件 |
| Stripe | 信用卡 / Apple Pay / Google Pay | 北美首选 |
| PayPal Express | PayPal 支付 | 信任度高 |
| WooCommerce Shipping & Tax | 北美物流 + 税费计算 | 官方插件 |

### 1.4 为什么选这套架构

| 维度 | 评分 | 说明 |
|------|------|------|
| 上线速度 | ⭐⭐⭐⭐⭐ | GoDaddy 一键安装 WordPress，1 小时可跑通全流程 |
| 成本 | ⭐⭐⭐⭐ | ~$12/月起步，性价比高 |
| 扩展性 | ⭐⭐⭐⭐ | 日单 100+ 后可升级 VPS |
| 维护成本 | ⭐⭐⭐⭐ | Managed WP 自动更新备份，省心 |
| 北美访问速度 | ⭐⭐⭐⭐ | 配合 Cloudflare 足够快 |
| 生态插件 | ⭐⭐⭐⭐⭐ | WooCommerce 插件最多最成熟 |

---

## 2. 域名与 DNS 配置

### 2.1 域名选择建议

```
主域名：yourbrand.com（.com 北美最权威）
品牌保护：yourbrand.net / yourbrand.org（同注册）

不要用：.us / .ca 等国别域名（美国用户对 .com 信任度更高）
```

### 2.2 DNS 迁移到 Cloudflare（必须做）

**目的**：免费获得 CDN 加速 + HTTPS + WAF 防护

**步骤**：

```
1. 在 Cloudflare 注册账号（cloudflare.com）
2. 添加站点（Add a Site），输入 yourbrand.com
3. Cloudflare 自动扫描现有 DNS 记录
4. 将 Nameserver 改为 Cloudflare 提供的两个地址
   （在 GoDaddy 域名设置中修改 Nameserver）
5. 等待生效（通常 5 分钟 - 24 小时）
```

**DNS 配置检查清单**：

```
□ A 记录：yourbrand.com → GoDaddy 主机 IP
□ A 记录：www → yourbrand.com（CNAME 方式）
□ MX 记录：邮件服务商提供的记录（如有）
□ CNAME：_acme-challenge → 用于 SSL 证书验证
□ Cloudflare SSL/TLS 模式：Full（严格）
□ Cloudflare Always Use HTTPS：开启
□ Cloudflare HTTPS Rewrites：开启
```

### 2.3 域名配置注意事项

- **不要在 GoDaddy 同时开启 CDN/DNS**（和 Cloudflare 冲突）
- 主机 IP 若变化，及时更新 Cloudflare 的 A 记录
- 建议购买 2 年以上域名，避免续费涨价

---

## 3. 服务器环境准备

### 3.1 GoDaddy 主机购买与配置

**推荐配置**：

| 项目 | 配置 | 备注 |
|------|------|------|
| 产品 | Managed WordPress - Ultimate | 一键 WordPress |
| PHP 版本 | 8.1 或 8.2 | 性能最优 |
| SSD 存储 | 40GB | 产品图多可加购 |
| 流量 | 不限 | GoDaddy 宣传不限，但需合理使用 |
| 免费 SSL | ✅ | Let's Encrypt |
| 自动备份 | ✅ | 每日自动 |
| 免费域名 | ✅ | 首年 |

**数据中心选择**：

- 面向北美 → 选择 **US East（弗吉尼亚）** 或 **US West（凤凰城）**
- 在 GoDaddy 购买时注意选择数据中心位置

### 3.2 PHP 版本设置

```
登录 GoDaddy 产品页面 → cPanel / Plesk
→ MultiPHP Manager → 选择 8.1 或 8.2
→ 保存
```

**注意**：切换 PHP 版本前，确保主题和插件支持该版本（主流主题均支持 8.x）。

### 3.3 OPcache 开启检查

```
cPanel → MultiPHP INI Editor → 点击域名
→ 查找 opcache.enable → 确认 = 1
```

OPcache 可将 PHP 响应速度提升 30-50%，是必须开启的优化项。

---

## 4. WordPress + WooCommerce 安装配置

### 4.1 一键安装 WordPress

```
GoDaddy 产品页面 → Managed WordPress → 安装 WordPress
→ 选择域名 → 填写管理员邮箱/密码/站点标题
→ 安装完成，登录 wp-admin
```

### 4.2 WordPress 初始配置

**必做设置（wp-admin → 设置）**：

```
设置 → 常规：
  □ 站点标题：品牌名
  □ Tagline：简短品牌描述（利于 SEO）
  □ WordPress 地址 / 站点地址：均设为 https://yourbrand.com（带 www 或不带 www 统一）
  □ 时区：UTC-8（太平洋时间）
  □ 日期格式 / 时间格式：自定义为 M j, Y / g:i a

设置 → 固定链接：
  □ 选择：文章名（/%postname%/）
  □ 勾选："将正文中纯文本 URLs 转换为链接"
  □ 原因：利于 SEO + 用户友好 URL

设置 → 讨论：
  □ 关闭：新评论需要人工审核（减少垃圾评论干扰）
  □ 关闭：允许评论通知

设置 → 媒体：
  □ 缩略图尺寸：300×300
  □ 中等尺寸：600×600
  □ 大尺寸：1200×1200
  □ 取消勾选："将完整尺寸图片链接到文件"
```

### 4.3 安装 WooCommerce

```
WordPress 后台 → 插件 → 安装插件
→ 搜索 "WooCommerce" → 现在安装 → 启用
→ 进入 WooCommerce 设置向导
```

**WooCommerce 向导填写**：

| 步骤 | 填写内容 |
|------|---------|
| 商店位置 | 美国 / 具体州 |
| 行业 | 零售 / 灯具 / 家居 |
| 产品类型 | 实体产品（physical goods） |
| 功能 | 暂时不勾选"subscriptions"等高级功能，先跑通基础 |
| 主题 | 暂时跳过，先用默认主题安装 WooCommerce，再切换主题 |

### 4.4 WooCommerce 基础设置

```
WooCommerce → 设置 → 常规：
  □ 售卖地点：仅限美国、加拿大
  □ 货币：USD（美元）
  □ 货币选项：$1,234.56 格式
  □ 重量单位：lb（磅）
  □ 尺寸单位：in（英寸）

WooCommerce → 设置 → 产品：
  □ 产品数量：每页显示 12/16/24 个（可选）
  □ 评价：开启产品评价（社会证明，提升转化）

WooCommerce → 设置 → 账户与隐私：
  □ 允许客人结账：开启（降低弃购率）
  □ 强制创建账户：关闭（购物后可选注册）
  □ GDPR 相关：开启必要选项（隐私政策页面需先创建）
```

---

## 5. 支付与物流配置

### 5.1 Stripe 配置（优先推荐）

**注册 Stripe 账号**：
```
1. 访问 stripe.com → 注册账号
2. 完成邮箱验证 + 身份认证
3. 获取 API Keys：
   - Publishable Key（公钥，前端用）
   - Secret Key（私钥，后端用，妥善保管）
4. 开启测试模式，测试完成后再切换生产模式
```

**在 WordPress 中配置**：
```
WordPress 后台 → WooCommerce → 设置 → 支付
→ 找到 "Stripe Credit Card" → 启用
→ 输入 Publishable Key 和 Secret Key
→ 保存测试
```

**Stripe 测试流程**：

| 卡号 | 用途 | 预期结果 |
|------|------|---------|
| 4242 4242 4242 4242 | 测试成功 | 支付成功，订单创建 |
| 4000 0000 0000 0002 | 测试 Declined | 显示拒绝原因 |
| 4000 0000 0000 3220 | 3D Secure 测试 | 需要额外验证 |

### 5.2 PayPal 配置

```
WooCommerce → 设置 → 支付
→ 找到 "PayPal Checkout" → 启用
→ 填写 PayPal 邮箱地址（商家收款邮箱）
→ 保存 → 测试订单
```

**PayPal 沙箱测试**：
- 在 developer.paypal.com 注册沙箱账号
- 获取沙箱商家/买家账号
- 在 WooCommerce PayPal 设置中启用沙箱模式测试

### 5.3 物流配置

**WooCommerce Shipping & Tax**：
```
WooCommerce → 设置 →  Shipping → Shipping & Tax
→ 填写店铺地址（美国/加拿大地址）
→ 开启运费计算
→ 设置默认运费区域：美国全国 + 加拿大
```

**运费策略建议（灯具类产品）**：

| 方案 | 规则 | 适用场景 |
|------|------|---------|
| 免费配送 | 订单满 $99 免费配送 | 提升客单价 |
| 固定费率 | $9.99 统一运费 | 控制成本 |
| 按重量计算 | 实时 USPS/UPS 报价 | 最准确，但流程复杂 |

**初期建议**：选择**固定费率 $9.99** 或 **满 $99 免费**，简化运营。

---

## 6. 主题与插件安装

### 6.1 主题选择（快速上线优先）

**推荐顺序（从简单到丰富）**：

| 优先级 | 主题 | 价格 | 上手难度 | 适合灯具 |
|--------|------|------|---------|---------|
| ⭐ 首选 | **Astra** | 免费 / Pro $59 | 低 | ✅ 速度快，灯具展示清晰 |
| ⭐⭐ | **Flatsome** | $59 | 中 | ✅ 电商专用，UX Themes 出品 |
| ⭐⭐ | **Shopkeeper** | $79 | 中 | ✅ 视觉好，适合灯具 |
| ⭐⭐⭐ | **WoodMart** | $59 | 中 | ✅ 功能全，XTemos 出品 |

**初期建议**：Astra（免费版）+ Elementor（免费版），最快速度上线。

### 6.2 Astra 主题安装

```
WordPress 后台 → 外观 → 主题 → 添加
→ 搜索 "Astra" → 安装 → 启用
→ 外观 → Astra 选项 → 选择一个基础模板
```

**Astra 关键设置**：

```
全局设置 → 颜色：
  □ 主色：#D4AF37（金色，适合灯具/轻奢定位）
  □ 辅助色：#1A1A1A（深灰，文字/背景）
  □ 强调色：#E8C547

全局设置 → 排版：
  □ 字体：Google Fonts → Inter 或 Poppins
  □ 正文：16px
  □ 标题：H1 36px / H2 28px / H3 22px

页眉设置：
  □ Logo 上传（高度 60-80px，白底或透明 PNG）
  □ 购物车图标：开启
  □ 移动端菜单：汉堡菜单
```

### 6.3 必须安装的插件（精简清单）

**必须安装（按优先级）**：

| 插件 | 用途 | 优先级 |
|------|------|--------|
| WooCommerce | 电商核心 | P0 |
| WooCommerce Stripe Gateway | 信用卡支付 | P0 |
| WooCommerce PayPal Payments | PayPal 支付 | P0 |
| WooCommerce Shipping & Tax | 物流税费 | P0 |
| Yoast SEO | SEO 优化 | P0 |
| LiteSpeed Cache 或 WP Super Cache | 页面缓存 | P0 |
| Wordfence Security | 安全防护 | P0 |
| UpdraftPlus | 自动备份 | P0 |
| WebP Express | 图片格式优化 | P1 |
| Contact Form 7 | 联系表单 | P1 |
| Smush | 图片压缩优化 | P1 |

**可选安装（初期可跳过）**：

| 插件 | 用途 | 何时安装 |
|------|------|---------|
| Elementor Pro | 页面构建器 | 有定制需求时 |
| WPForms | 高级表单 | 有复杂表单需求时 |
| MonsterInsights | GA4 集成 | 有数据分析需求时 |
| Klaviyo | 邮件营销 | 有邮件自动化需求时 |
| Instagram Feed | 社媒动态 | 有社媒展示需求时 |

### 6.4 插件安装注意事项

```
⚠️ 重要原则：
1. 不要一次性安装过多插件，插件越多，性能越差
2. 每个插件安装后立即测试，确认正常工作再装下一个
3. 避免安装功能重复的插件（如同时装两个缓存插件）
4. 定期检查插件更新，保持最新版本
5. 停用的插件也要删除（影响后台加载速度）
```

---

## 7. SEO 基础配置

### 7.1 Yoast SEO 基础设置

```
SEO → 常规 → 你的信息：
  □ 组织类型：Organization
  □ 组织名称：品牌名
  □ Logo 上传

SEO → 搜索外观 → 固定链接：
  □ 清洁 permalink 结构：/%postname%/

SEO → 高级 → 工具：
  □ 编辑 .htaccess 和 robots.txt
  □ robots.txt 填写：
```

**robots.txt 参考模板**：

```
User-agent: *
Allow: /

# 屏蔽后台
User-agent: *
Disallow: /wp-admin/
Allow: /wp-admin/admin-ajax.php

# 屏蔽搜索结果
Disallow: /?s=*

# 屏蔽标签页（避免重复内容）
Disallow: /tag/

# Sitemap
Sitemap: https://yourbrand.com/sitemap_index.xml
```

### 7.2 Google Search Console 提交

```
1. 访问 search.google.com/search-console
2. 添加属性：yourbrand.com
3. 验证方式：HTML 文件 或 DNS TXT 记录
4. 提交 sitemap：https://yourbrand.com/sitemap_index.xml
5. 安装 Yoast 后会自动生成 sitemap
```

### 7.3 结构化数据（Schema）基础

**Yoast SEO Premium 自动生成以下 Schema**：

| 页面 | Schema 类型 | 说明 |
|------|------------|------|
| 首页 | Organization | 品牌信息 |
| 产品页 | Product | 价格/库存/评分 |
| 文章页 | Article | 博客文章 |
| 联系我们 | LocalBusiness | 实体信息 |

**灯具产品需要手动补充的 Schema**：

```
产品页需在 Yoast → Schema → 产品中填写：
  □ SKU（产品编号）
  □ Brand（品牌名）
  □ MPN（制造商编号）
  □ GTIN（UPC/EAN）
  □ 产品状态：New / Used / Refurbished
```

### 7.4 图片 SEO

```
□ 所有产品图片添加 ALT 文本：格式为 "产品名 + 核心规格"
  例：Alt="Modern Gold Chandelier for Dining Room 5-Light"
□ 产品主图：正方形或 4:3 比例，背景白色或透明
□ 图片命名：不用 IMG_1234.jpg，用 modern-gold-chandelier-5-light.jpg
□ 页面中非装饰图片必须加 ALT 文本
```

---

## 8. 安全与性能优化

### 8.1 安全配置（必须做）

**Wordfence 基础配置**：

```
Wordfence → 防火墙：
  □ 开启所有基本保护
  □ 启用 "Brute Force Protection"
  □ 登录安全：连续 5 次失败锁定 15 分钟

Wordfence → 全局设置：
  □ 启用 "Prominent Notice of Login Protection"
  □ 禁用 "Let Wordfence login security prompt appear on the login page"
  □ 定期查看 Wordfence 威胁日志

登录安全（必做）：
  □ 将 wp-admin 目录限权改为管理员 IP 可访问
  □ 登录密码改为强密码（16 位以上，大小写+数字+符号）
  □ 安装 Two-Factor Authentication（2FA）插件
```

**管理员账户安全**：

| 操作 | 说明 |
|------|------|
| 用户名不用 admin | 创建新管理员，删除默认 admin |
| 强密码 | 16 位以上，用密码管理器 |
| 2FA | 必装插件：Wordfence Login Security / WP 2FA |
| 定期更换密码 | 每 3-6 个月更换一次 |

### 8.2 Cloudflare 安全配置

```
Cloudflare → Security → WAF：
  □ Managed Rules → 开启"Cloudflare Managed Ruleset"
  □ Rate Limiting → 设置限制（可选）

Cloudflare → Security → Settings：
  □ Challenge Passage：30 分钟
  □ Browser Integrity Check：开启

Cloudflare → SSL/TLS：
  □ 模式：Full（严格）
  □ TLS 版本：1.2 最低，1.3 推荐
  □ Automatic HTTPS Rewrites：开启
```

### 8.3 性能优化（快速见效）

**LiteSpeed Cache 插件配置（推荐）**：

```
LiteSpeed Cache → 通用：
  □ 启用：开启所有缓存
  □ 缓存访客：开启
  □ 登录用户缓存：关闭（实时性）

LiteSpeed Cache → 优化：
  □ CSS Minify：开启
  □ JS Minify：开启（注意兼容性）
  □ HTML Minify：开启
  □ 延迟加载 JS：开启
  □ 图片优化：开启
```

**Cloudflare 性能配置**：

```
Speed → 优化：
  □ Auto Minify：开启（CSS/JS/HTML）
  □ Brotli：开启
  □ HTTP/3 (QUIC)：开启
  □ Rocket Loader：先"自动"测试，有问题改"手动"

Speed → Content Optimization：
  □ Mirage：开启（图片懒加载）
  □ Polish：开启（图片压缩）
  □ Polish 模式：Lossy（节省带宽）
```

**WordPress 基础优化**：

| 操作 | 位置 | 效果 |
|------|------|------|
| 删除闲置插件 | wp-admin → 插件 | 减少后台加载时间 |
| 关闭 Post Revisions | wp-config.php 添加 | 减少数据库膨胀 |
| 设置 Redis 缓存 | 插件 → LiteSpeed Cache | 提升动态页面速度 |
| 图片 WebP 化 | WebP Express 插件 | 减少 30% 图片体积 |

---

## 9. 产品上架规范

### 9.1 灯具产品分类体系

**建议分类结构**：

```
灯具总类（Lamp & Lighting）
├── 吊灯（Chandeliers）
│   ├── 现代吊灯（Modern Chandeliers）
│   ├── 水晶吊灯（Crystal Chandeliers）
│   ├── 简约吊灯（Minimalist Chandeliers）
│   └── 餐厅吊灯（Dining Room Chandeliers）
├── 吸顶灯（Ceiling Lights）
│   ├── 吸顶灯（Flush Mount）
│   ├── 半吸顶灯（Semi-Flush Mount）
│   └── 吊扇灯（Ceiling Fans with Lights）
├── 台灯（Table Lamps）
│   ├── 床头台灯（Bedside Lamps）
│   ├── 客厅台灯（Living Room Lamps）
│   └── 办公台灯（Desk Lamps）
├── 落地灯（Floor Lamps）
│   ├── 阅读落地灯（Reading Floor Lamps）
│   ├── 氛围落地灯（Ambient Floor Lamps）
│   └── 工业风落地灯（Industrial Floor Lamps）
├── 壁灯（Wall Lights）
│   ├── 床头壁灯（Sconces）
│   ├── 浴室壁灯（Vanity Lights）
│   └── 户外壁灯（Outdoor Wall Lights）
├── 智能灯具（Smart Lighting）
│   ├── 智能灯泡（Smart Bulbs）
│   ├── 智能灯带（Smart LED Strips）
│   └── 智能开关（Smart Switches）
└── 配件（Accessories）
    ├── 灯罩（Shades）
    ├── 灯泡（Bulbs）
    └── 安装配件（Hardware）
```

### 9.2 产品上架 Checklist

**每个产品必须填写的内容**：

| 字段 | 填写要求 | 示例 |
|------|---------|------|
| 产品名称 | 核心词 + 规格 + 场景 | "Modern Gold Chandelier 5-Light Crystal Ceiling Fixture for Dining Room" |
| 简短描述 | 1-2 句话，突出卖点 | "Elegant modern chandelier featuring 5 flickering crystal lights..." |
| 详细描述 | H2/H3 分段，含规格参数表格 | 包含材质/尺寸/光源类型/安装方式等 |
| SKU | 唯一产品编号 | LAMP-CHD-5G-GOLD |
| 分类 | 选至最细分类 | Chandeliers > Modern Chandeliers |
| 标签 | 关键词补充 | gold chandelier, dining room, crystal |
| 重量 | lb（磅），用于物流计算 | 12.5 lb |
| 尺寸 | 长×宽×高 in | 24 in × 24 in × 20 in |
| 价格 | USD | $189.99 |
| 库存 | 数量或无限 | 100 |
| 产品图片 | 主图 + 至少 4 张附图 | 主图白底，附图多角度/细节/场景图 |
| 产品属性 | 颜色/材质/光源数等 | Color: Gold, Material: Crystal + Metal |

### 9.3 产品图片规范

| 图片类型 | 尺寸 | 数量 | 说明 |
|---------|------|------|------|
| 主图 | 1600×1600 px（正方形） | 1 张 | 白底，无水印，无文字 |
| 场景图 | 1600×1200 px（4:3） | 1-2 张 | 安装效果图，展示真实使用场景 |
| 细节图 | 800×800 px | 2-3 张 | 局部特写，材质/做工/Logo |
| 尺寸图 | 800×800 px | 1 张 | 标注尺寸，含人和物对比 |
| 包装图 | 800×800 px | 1 张 | 包装内容物，防止运输损坏纠纷 |

**灯具图片拍摄要点**：
```
✅ 光线充足，自然光或专业摄影灯
✅ 背景纯净（白/灰/黑渐变）
✅ 展示发光效果（如开灯效果 vs 关灯效果对比）
✅ 包含手或参照物对比尺寸
✅ 附上一张安装说明图或配件清单图
❌ 不要加 Logo 水印（影响用户体验）
❌ 不要用过度PS的效果图（实物与图片不符会引发差评）
```

### 9.4 产品描述模板（灯具类）

```html
<h2>About This Product</h2>
<p>1-2段产品核心卖点介绍，突出差异化...</p>

<h2>Specifications</h2>
<table>
  <tr><td>Material</td><td>Crystal + Metal</td></tr>
  <tr><td>Finish</td><td>Polished Gold</td></tr>
  <tr><td>Light Source</td><td>5 × E12 Bulbs (Not Included)</td></tr>
  <tr><td>Wattage</td><td>Max 40W per bulb</td></tr>
  <tr><td>Dimensions</td><td>24" W × 24" D × 20" H</td></tr>
  <tr><td>Chain Length</td><td>36" Adjustable</td></tr>
  <tr><td>Compatible Bulb Types</td><td>LED / Incandescent / CFL</td></tr>
  <tr><td>Dimmable</td><td>Yes (with dimmer switch)</td></tr>
  <tr><td>Certification</td><td>UL Listed</td></tr>
  <tr><td>Weight</td><td>12.5 lbs</td></tr>
</table>

<h2>What's in the Box</h2>
<ul>
  <li>1 × Chandelier Body</li>
  <li>1 × Ceiling Canopy</li>
  <li>1 × Installation Hardware Kit</li>
  <li>1 × User Manual</li>
</ul>

<h2>Shipping & Returns</h2>
<ul>
  <li>Ships within 1-3 business days</li>
  <li>Free shipping on orders over $99</li>
  <li>30-day hassle-free returns</li>
</ul>
```

---

## 10. 跨浏览器兼容性注意要点

### 10.1 各组件兼容性说明

| 组件 | 浏览器兼容 | 移动端 | 备注 |
|------|-----------|--------|------|
| GoDaddy 主机 | ✅ 无影响 | ✅ 无影响 | 后端服务 |
| WordPress 核心 | ✅ IE11+ | ✅ 全支持 | 成熟标准 |
| WooCommerce | ✅ IE11+ | ✅ 全支持 | 成熟电商 |
| Astra 主题 | ✅ IE11+ | ✅ 响应式 | 需选择响应式主题 |
| Stripe Elements | ✅ IE11+ | ✅ 全支持 | 官方保障 |
| PayPal Smart Button | ✅ 全浏览器 | ✅ 全支持 | 自动降级 |
| Cloudflare CDN | ✅ 无影响 | ✅ 无影响 | 仅加速 |
| LiteSpeed Cache | ✅ 无影响 | ✅ 无影响 | 服务端 |

### 10.2 Cloudflare Rocket Loader 配置注意

**Rocket Loader** 是最容易引发兼容性问题的 Cloudflare 功能。

```
默认：关闭 Rocket Loader，先观察页面是否正常
如遇页面元素异常（按钮不响应/动画失效/弹窗不显示）：
  1. 关闭 Rocket Loader 测试
  2. 若问题消失，在特定 script 标签加：data-cfasync="false"
  3. 例：<script data-cfasync="false" src="..."></script>
```

### 10.3 移动端特殊注意点

| 问题 | 原因 | 解决方案 |
|------|------|---------|
| 100vh 高度跳动（iOS Safari） | 地址栏显示/隐藏影响视口 | 用 CSS `height: 100dvh` 或 JS 计算 |
| 字体太小导致 iOS 自动放大 | 输入框 font-size < 16px | 结账表单 input 设为 font-size: 16px |
| 底部导航被 iOS 安全区遮挡 | iPhone 底部安全区域 | CSS 加 `padding-bottom: env(safe-area-inset-bottom)` |
| 图片宽高比变形 | 图片未设宽高比 | CSS `aspect-ratio: 1/1` 统一比例 |
| 视频无法自动播放 | iOS 禁止自动播放 | 用 poster 图片 + 点击播放 |

### 10.4 字体跨平台渲染差异

```
问题：macOS/iOS 的字体渲染比 Windows 细，整体视觉可能有偏差

解决：统一使用 Google Fonts，避免依赖系统字体

CSS 示例：
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 
               'Segoe UI', Roboto, sans-serif;
}

推荐灯具站 Google Fonts：
标题：Poppins / Montserrat
正文：Inter / Lato
```

### 10.5 浏览器兼容性目标

**支持目标矩阵**：

| 浏览器 | 版本要求 | 优先级 | 北美市场占比 |
|--------|---------|--------|-------------|
| Chrome | 最新版 | P0 | ~60% |
| Safari (macOS) | 最新版 | P0 | ~15% |
| Safari (iOS) | iOS 14+ | P0 | ~25% |
| Edge | 最新版 | P1 | ~12% |
| Firefox | 最新版 | P1 | ~8% |
| Chrome Android | 最新版 | P1 | ~15% |
| IE11 | 不测试 | - | <1% 可忽略 |

**实测建议**：重点测试 Chrome（Windows/macOS）、Safari（macOS/iOS）、Chrome Android 三个平台。

---

## 11. 测试验收清单

### 11.1 功能测试（上线前必做）

**首页测试**：
```
□ 页面加载 < 3 秒
□ Logo / 导航 / 搜索框 / 购物车图标 正常显示
□ 轮播图自动播放/手动切换正常
□ 产品列表滚动无卡顿
□ Footer 链接正常（关于我们/联系/隐私政策）
□ 移动端：汉堡菜单正常展开/收起
```

**产品页测试**：
```
□ 产品图片主图 + 缩略图切换正常
□ 图片放大镜功能正常（桌面端）
□ 尺寸/颜色/规格选择切换正常
□ 加入购物车按钮点击正常
□ 加购成功提示显示
□ 产品描述 H2/H3 格式正确
□ 规格表格显示正常
□ 相关产品推荐显示
```

**购物流程测试**：
```
□ 购物车添加/删除/修改数量正常
□ 优惠券输入框可用
□ 结算按钮跳转正常
□ 填写地址表单正常（姓名/地址1/地址2/城市/州/邮编）
□ 运费计算显示
□ Stripe 信用卡输入正常
□ PayPal 按钮跳转正常
□ 订单确认页正常
□ 订单确认邮件收到（买家 + 卖家）
□ 管理后台订单创建成功
```

**支付测试（必须用测试卡）**：

| 卡号 | 场景 | 预期 |
|------|------|------|
| 4242 4242 4242 4242 | 测试成功 | 支付成功 |
| 4000 0000 0000 0002 | 拒付测试 | 显示拒绝原因 |
| 4000 0025 0000 3155 | 3DS 测试 | 弹出验证 |

### 11.2 浏览器兼容性测试

**桌面端**：
```
□ Chrome（Windows）- 首页/产品页/结账/支付全流程
□ Chrome（macOS）- 同上
□ Safari（macOS）- 同上
□ Safari（iOS）- 同上（真机）
□ Firefox（Windows/macOS）- 抽测结账流程
□ Edge（Windows）- 抽测结账流程
□ Chrome（Android 手机）- 真机抽测
```

**控制台报错检查（每个浏览器）**：
```
打开 Chrome DevTools（F12）→ Console 面板
□ 无红色 Error 级别报错
□ 无黄色 Warning 级别报错（可忽略部分第三方插件警告）
□ 无资源加载失败（Network 面板，红色 404/500）
```

### 11.3 移动端专项测试

```
□ iPhone Safari - 所有核心流程
□ iPhone Safari - 输入框聚焦键盘弹出不遮挡表单
□ iPhone Safari - Apple Pay 按钮正常显示（如支持）
□ Android Chrome - 所有核心流程
□ Android Chrome - Google Pay 按钮正常显示（如支持）
□ iPad - 平板布局正常，触摸操作正常
□ 各屏幕尺寸（375px / 390px / 428px / 768px）均测试
```

### 11.4 性能测试

| 指标 | 目标值 | 测试工具 |
|------|--------|---------|
| TTFB（首字节时间） | < 600ms | WebPageTest |
| 首页加载时间 | < 3s | GTmetrix / PageSpeed Insights |
| LCP（最大内容绘制） | < 2.5s | PageSpeed Insights |
| CLS（布局偏移） | < 0.1 | PageSpeed Insights |
| FID（交互延迟） | < 100ms | PageSpeed Insights |
| 图片格式 | WebP 为主 | Chrome DevTools |

**PageSpeed Insights 测试地址**：https://pagespeed.web.dev/

### 11.5 SEO 测试

```
□ site:yourbrand.com 能搜到首页
□ 搜索品牌词，首页出现在 Google 第一页
□ 产品页 title 包含产品核心词
□ 产品页 meta description 存在且有吸引力
□ 产品页有且仅有一个 H1
□ 产品页图片有 ALT 文本
□ sitemap.xml 可访问（yourbrand.com/sitemap_index.xml）
□ robots.txt 可访问（yourbrand.com/robots.txt）
□ 结构化数据无错误（Google Rich Results Test）
```

---

## 12. 实施路线图

### 12.1 第 1-2 周：基础设施搭建（最快速上线）

**目标**：完成网站基础搭建，能跑通从浏览到付款的完整流程。

```
Day 1-2：域名 + DNS
  □ 注册 GoDaddy 主机（Managed WordPress Ultimate）
  □ 注册 Cloudflare 账号，修改 Nameserver
  □ 域名 DNS 配置完成，https 可访问

Day 3-4：WordPress + WooCommerce
  □ 一键安装 WordPress
  □ 安装 WooCommerce
  □ 完成 WooCommerce 向导设置

Day 5-6：支付 + 物流
  □ 注册 Stripe 账号，获取 API Keys
  □ WooCommerce 配置 Stripe（测试模式）
  □ 配置 PayPal（测试模式）
  □ 配置固定运费

Day 7-8：主题 + 基础插件
  □ 安装 Astra 主题（免费版）
  □ 安装必须插件（Yoast/Wordfence/UpdraftPlus/LiteSpeed Cache）
  □ 基础主题设置（Logo/颜色/字体）

Day 9-10：产品上架（10-20 个 SKU）
  □ 确定分类体系
  □ 拍摄/整理产品图片
  □ 按模板上架首批产品
  □ 确保每个产品有：名称/描述/价格/SKU/图片/分类

Day 11-12：测试
  □ 功能测试（首页/产品/购物车/结账）
  □ 支付测试（Stripe 4242 卡号 + PayPal 沙箱）
  □ 移动端测试（iPhone 真机）
  □ PageSpeed Insights 跑分 > 70

Day 13-14：上线准备
  □ 切换 Stripe/PayPal 为生产模式
  □ 检查 SSL 证书有效期
  □ 提交 Google Search Console
  □ 发布上线
```

**第 2 周结束时的站点状态**：
```
✅ 独立站可访问，HTTPS 正常
✅ 产品列表页 + 产品详情页完整
✅ 购物流程完整（浏览→加购→付款→确认）
✅ 移动端体验基本正常
✅ 支付可真实收款（Stripe/PayPal）
✅ SEO 基础配置完成
✅ 安全防护就位（Wordfence/Cloudflare WAF）
```

### 12.2 第 3-4 周：优化 + 内容填充

**目标**：提升体验，填充更多产品，奠定 SEO 基础。

```
□ 上架 50-100 个 SKU（灯具产品线）
□ 产品描述全部按模板完善（规格表格 + 卖点文案）
□ 图片全部添加 ALT 文本
□ Google Analytics 4 安装 + 验证
□ Meta Pixel（Facebook/Instagram）安装
□ Google Search Console 提交 sitemap
□ Google Merchant Center 注册，提交商品 Feed
□ 创建必要页面：关于我们/联系/隐私政策/退货政策
□ 社交媒体账号绑定（Facebook/Instagram/Pinterest）
□ 邮件通知模板定制（订单确认/发货通知/评价邀请）
```

### 12.3 第 5-8 周：流量启动

**目标**：开始广告投放，获取首批订单。

```
□ Google Shopping 广告投放（预算 $10-20/天测试）
□ Facebook/Instagram 广告投放（预算 $10-20/天测试）
□ 社媒账号内容发布（Instagram 3-5篇/周）
□ 第一批 Google Shopping + Meta 广告数据复盘
□ 转化率追踪：加购率 / 结账率 / 支付成功率
□ 弃购率分析（若弃购率高，配置 WooCommerce 弃购挽回邮件）
□ 首批真实订单履约（发货/物流追踪/客户反馈）
```

### 12.4 第 3-6 个月：增长迭代

```
□ SEO 文章开始发布（每周 1-2 篇灯具选购指南）
□ Google Ads 广告预算优化（提升 ROAS > 3 的广告组）
□ Instagram/Pinterest 红人合作（找灯具类小博主）
□ 邮件营销启动（Klaviyo 安装，欢迎序列 + 弃购挽回）
□ 产品线扩展（智能灯具/户外灯具等新类目）
□ 客户评价积累（每单发货后自动发送评价邀请邮件）
□ 日单稳定 > 30 后，评估是否升级 VPS
□ 日单稳定 > 100 后，评估迁移到 SiteGround 或 WP Engine
```

---

## 13. 后续迭代方向

### 13.1 性能升级路径

| 阶段 | 日单量 | 升级建议 |
|------|--------|---------|
| 起步期 | 0-30 | GoDaddy Managed WP，当前配置足够 |
| 成长期 | 30-100 | LiteSpeed Cache + Redis + Cloudflare APO |
| 成熟期 | 100-500 | 迁移到 SiteGround（速度更快）或 VPS |
| 规模化 | 500+ | WP Engine Enterprise 或自建云架构 |

### 13.2 功能扩展方向

**电商功能**：
```
□ 产品变体（同一 SKU 不同颜色/尺寸）
□ 捆绑销售（灯具 + 灯罩套装）
□ 优惠券/满减活动
□ 会员积分系统
□ 多币种切换（加元 CAD 支持）
□ 多语言支持（英语/法语，加拿大市场）
```

**营销功能**：
```
□ Klaviyo 邮件营销（欢迎/弃购/复购/节庆自动化序列）
□ Google Customer Reviews（收集评价）
□ Instagram Shopping 打通
□ Facebook Shop 打通
□ TikTok Shopping（年轻人市场）
```

**运营效率**：
```
□ ShipStation 多渠道订单管理
□ 仓库/WMS 系统接入
□ 客服系统（Zendesk / Freshdesk）
□ 退货处理流程优化
□ 保险理赔流程（如大件灯具破损）
```

### 13.3 品类扩展方向

| 阶段 | 可扩展品类 |
|------|-----------|
| 稳定期 | 智能灯具（WiFi/Bluetooth） |
| 成长期 | 户外灯具（庭院灯/路灯/景观灯） |
| 成熟期 | 家居装饰（镜子/画框/墙饰） |
| 规模化 | 商业照明（店铺灯/办公室灯） |

---

## 附录

### 附录 A：快速参考命令 / 检查项

**DNS 生效检查**：
```
nslookup yourbrand.com
→ 确认返回 Cloudflare IP 而非 GoDaddy IP
```

**SSL 证书检查**：
```
访问 https://yourbrand.com
→ 地址栏锁形图标 → 查看证书有效期
→ 测试：https://www.ssllabs.com/ssltest/（评级 A 以上即可）
```

**WordPress 健康检查**：
```
wp-admin → 工具 → 站点健康
→ 确保无致命错误
→ PHP 内存 > 256M
```

**WooCommerce 状态检查**：
```
WooCommerce → 状态 → 系统状态
→ 检查所有项目是否为绿色
→ 特别注意：Stripe/PayPal 连接状态
→ Cron 事件是否正常执行
```

### 附录 B：常用工具链接

| 工具 | 链接 | 用途 |
|------|------|------|
| Cloudflare | cloudflare.com | DNS/CDN/WAF |
| Stripe Dashboard | dashboard.stripe.com | 支付管理 |
| PayPal Sandbox | developer.paypal.com | PayPal 测试 |
| Google Search Console | search.google.com/search-console | SEO 工具 |
| Google PageSpeed | pagespeed.web.dev | 性能测试 |
| GTmetrix | gtmetrix.com | 性能分析 |
| WebPageTest | webpagetest.org | 多地区速度测试 |
| SSL Labs | ssllabs.com/ssltest | SSL 评级 |
| GTmetrix | gtmetrix.com | 性能测试 |
| WooCommerce Docs | woocommerce.com/documentation | 官方文档 |
| WordPress SEO | yoast.com/wordpress/plugins/seo | Yoast SEO |

---

**文档版本**：v1.0  
**创建日期**：2026-06-10  
**适用项目**：灯具产品出海北美独立站  
**架构方案**：WordPress + WooCommerce + GoDaddy + Cloudflare + Stripe/PayPal
