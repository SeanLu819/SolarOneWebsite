# SolarOne Website — 故障排除记录与架构文档

## 项目概况

SolarOne 是一个 Django 多语言企业网站，部署在 Vercel 上。展示 LED 照明产品、工程项目案例，支持 6 种语言（英/法/西/德/俄/阿），包含深色/浅色主题切换。

## 技术栈

- **框架**: Django 6.0 + Python 3.12
- **部署**: Vercel（`@vercel/python` + `@vercel/static-build`）
- **静态文件**: WhiteNoise 6.x（通过 `collectstatic` 收集到 `staticfiles/`）
- **数据库**: 本地 SQLite；Vercel 上用 `seed_data.py` 内嵌数据替代 DB
- **国际化**: Django i18n（`.po`/`.mo` 文件）+ 模型级 JSON translations 字段

## 项目结构

```
website/
├── index.py              # Vercel 入口：WSGI + WhiteNoise 配置
├── manage.py             # Django 管理脚本
├── build.sh              # Vercel 构建脚本（pip install + collectstatic）
├── vercel.json           # Vercel 部署配置（builds + routes）
├── requirements.txt      # Python 依赖
├── seed_data.json        # 种子数据 JSON（本地开发数据源）
│
├── solarone/             # Django 项目配置
│   ├── settings.py       # 环境检测 + DB + i18n + 静态文件配置
│   ├── urls.py           # 根 URL 路由（i18n_patterns）
│   └── wsgi.py           # WSGI 应用
│
├── pages/                # 主应用
│   ├── views.py          # 视图函数（DB 查询 + JSON fallback）
│   ├── models.py         # Product / Project / SiteConfig / Visitor 等模型
│   ├── seed_data.py      # 内嵌种子数据（Vercel 上数据来源）
│   ├── urls.py           # 页面路由
│   ├── middleware.py     # 访问者追踪中间件（仅本地）
│   ├── admin.py          # Admin 后台配置
│   └── migrations/       # 数据库迁移文件
│
├── templates/            # Django 模板
│   ├── base.html         # 基础模板（含全站 CSS + 导航 + 页脚）
│   ├── home.html         # 首页
│   ├── products.html     # 产品列表
│   ├── product_detail.html # 产品详情
│   ├── projects.html     # 项目列表
│   ├── about.html        # 关于我们
│   └── contact.html      # 联系我们
│
├── static/               # 静态资源（CSS/JS/图片）
│   └── images/
│       ├── hero-main.fw.png    # 首页 hero 背景（2.7MB — 待优化）
│       ├── processed/          # 产品/项目图片
│       └── *.png / *.jpg       # 其他图片资源
│
├── locale/               # 翻译文件
│   ├── en/LC_MESSAGES/   # 英语
│   ├── fr/LC_MESSAGES/   # 法语
│   ├── es/LC_MESSAGES/   # 西班牙语
│   ├── de/LC_MESSAGES/   # 德语
│   ├── ru/LC_MESSAGES/   # 俄语
│   └── ar/LC_MESSAGES/   # 阿拉伯语
│
└── .gitignore
```

## 数据架构（关键设计决策）

### 本地开发
- 使用 SQLite 数据库（`db.sqlite3`）
- 通过 Django Admin 管理产品/项目/站点配置
- `seed_data.json` 是数据源的备份

### Vercel 生产环境
- SQLite 是临时文件系统，每次冷启动都会丢失
- **数据来源**: `pages/seed_data.py`（从 `seed_data.json` 生成的 Python 模块）
- `views.py` 先尝试查 DB，失败后自动 fallback 到 `seed_data.py`
- `SiteConfig` 同样有 JSON fallback（跳过 ImageField，用默认值）

### 为什么不用 `seed_data.json` 直接读文件？
Vercel 的 `@vercel/python` runtime 不会自动打包非 Python 文件到 serverless function 中。`seed_data.json` 在 Vercel 运行时不可访问。改用 Python 模块（`seed_data.py`）后，`import` 会自动包含在部署包里。

---

## 故障排除记录：产品/项目页空白问题

### 症状
Vercel 部署后，`/products/` 和 `/projects/` 页面能渲染框架（导航、标题、页脚），但产品/项目卡片区域完全空白。本地开发一切正常。

### 根本原因（三重叠加）

#### 原因 1：Vercel 构建失败 — PEP 668 阻止 pip install

Vercel 构建环境切换到了 uv 管理的 Python，符合 PEP 668 规范，默认阻止 `pip install` 修改系统 Python。

**错误日志**:
```
error: externally-managed-environment
× This environment is externally managed
╰─> This Python installation is managed by uv and should not be modified.
```

**结果**: Django 根本没有被安装，`collectstatic` 和 `compilemessages` 全部失败。Vercel 回退到上一次成功的部署（旧代码）。

**修复**: `build.sh` 改用 `pip install --break-system-packages`。

```bash
# ❌ 失败
pip install -r requirements.txt

# ❌ 失败（uv 用 Python 3.9，不满足 Django 6.0 的 Python>=3.12 要求）
uv pip install --system -r requirements.txt

# ✅ 成功
pip install --break-system-packages -r requirements.txt
```

#### 原因 2：Vercel 构建失败 — compilemessages 缺少 msgfmt

Django 的 `compilemessages` 命令需要 GNU gettext 工具（`msgfmt`），但 Vercel 构建环境没有安装。

**错误日志**:
```
CommandError: Can't find msgfmt. Make sure you have GNU gettext tools 0.19 or newer installed.
```

**修复**: 预编译的 `.mo` 文件已提交到 git，运行时不需要重新编译。在 `build.sh` 里加 `|| true` 让这个命令非致命。

```bash
# ✅ 非致命，构建继续
python manage.py compilemessages 2>&1 || true
```

#### 原因 3：seed_data.json 不在 serverless function 包里

即使构建成功，`seed_data.json` 作为非 Python 文件不会被 `@vercel/python` 自动打包。`_load_seed()` 读文件失败，返回空列表。

**验证**: 浏览器检查 `.products-grid` 的 `innerHTML.length` 为 20（只有空白字符），`children.length` 为 0。

**修复**: 将 `seed_data.json` 转换为 Python 模块 `pages/seed_data.py`，通过 `import` 加载数据。`_load_seed()` 优先用 import，JSON 文件读取作为本地开发兜底。

### 其他清理

- 移除了 `pages/urls.py` 中引用已删除视图的 `debug/seed/` 路由（会导致 ImportError）
- 移除了 `index.py` 中冗余的 `_seed_database()` raw SQL 逻辑（与 JSON fallback 冲突）
- 加固了 `get_common_context()` 对 JSON fallback 场景下 ImageField 访问的兼容性

### 验证结果

修复后线上验证（2026-07-26）:
- `/products/` — 4 个产品卡片正常渲染（图片 + 标题 + 描述 + 规格）
- `/projects/` — 4 个项目卡片正常渲染（图片 + 标题 + 描述 + 结果）
- `/products/m-series/` — 产品详情页正常（图片 + 描述 + 规格）

---

## Vercel 部署架构

```
GitHub push → Vercel 自动构建
  │
  ├─ build.sh (@vercel/static-build)
  │   ├─ pip install --break-system-packages -r requirements.txt
  │   ├─ python manage.py collectstatic --noinput
  │   └─ python manage.py compilemessages || true  (非致命)
  │   → 产出 staticfiles/ 目录
  │
  └─ index.py (@vercel/python)
      ├─ Django WSGI application
      ├─ WhiteNoise (serve staticfiles/)
      └─ 所有路由 → /index.py (catch-all)
```

### `vercel.json` 配置

```json
{
  "builds": [
    {"src": "build.sh", "use": "@vercel/static-build", "config": {"distDir": "staticfiles"}},
    {"src": "index.py", "use": "@vercel/python"}
  ],
  "routes": [{"src": "/(.*)", "dest": "/index.py"}]
}
```

> 注意: `builds` 是 legacy 配置格式。`functions` + `includeFiles` 不能与 `builds` 同时使用。如果未来迁移到 `functions` 格式，需要完全重写 `vercel.json`。

---

## 图片优化建议（当前未实施）

### 问题现状

| 图片 | 大小 | 用途 | 问题 |
|------|------|------|------|
| `hero-main.fw.png` | 2.7 MB | 首页 hero 背景 | 最大瓶颈，阻塞首屏渲染 |
| `Baseball.png` | 1.3 MB | 项目图片 | 过大 |
| `floodlight.fw.png` | 1.0 MB | 产品图片 (RT410) | 过大 |
| `basketball.png` | 639 KB | 项目图片 | 偏大 |
| `home-products.png` | 611 KB | 首页产品区 | 偏大 |
| `rt200-m.png` | 518 KB | 产品图片 (M Series) | 偏大 |
| `HB.png` | 457 KB | 产品图片 (RT400/500) | 偏大 |
| `favicon.png` | 77 KB | 网站图标 | 偏大（favicon 通常 < 10KB） |

**总计**: 首页需加载约 5MB 图片，产品页约 2.6MB，项目页约 2.3MB。

### 优化建议（按优先级排序）

#### P0: 格式转换（预计减少 60-80% 体积）

将 PNG/JPG 转换为 WebP 或 AVIF 格式:

```
hero-main.fw.png (2.7MB) → hero-main.webp (~400KB)     减少 85%
Baseball.png (1.3MB)     → baseball.webp (~200KB)      减少 85%
floodlight.fw.png (1MB)  → floodlight.webp (~150KB)    减少 85%
```

工具: `cwebp -q 80 input.png -o output.webp` 或 `sharp` (Node.js) 或 `Pillow` (Python)

#### P1: 响应式图片（srcset）

根据屏幕尺寸加载不同分辨率的图片:

```html
<!-- 当前 -->
<img src="{% static 'images/hero-main.fw.png' %}">

<!-- 优化后 -->
<img srcset="
  {% static 'images/hero-main-480.webp' %} 480w,
  {% static 'images/hero-main-1024.webp' %} 1024w,
  {% static 'images/hero-main-1920.webp' %} 1920w
" sizes="100vw" src="{% static 'images/hero-main-1920.webp' %}">
```

#### P2: 延迟加载（lazy loading）

非首屏图片使用 `loading="lazy"`:

```html
<!-- 产品/项目卡片图片 -->
<img src="..." loading="lazy" alt="...">
```

首页 hero 背景图不应 lazy load（会闪烁），但产品/项目列表的卡片图片可以。

#### P3: CSS 压缩内联样式

`base.html` 内联了约 1300 行 CSS。提取为外部文件后浏览器可以缓存:

```
templates/base.html (1300行 CSS) → static/css/styles.css (可缓存)
```

#### P4: 字体优化

当前加载 3 个 Google Fonts 字族（Space Grotesk + Inter + IBM Plex Mono），同步阻塞渲染:

- 移除未使用的字重（当前每个字族加载 5-7 个 weight）
- 考虑自托管字体文件（避免 Google Fonts CDN 延迟）
- `IBM Plex Mono` 仅用于小标签，考虑用系统等宽字体替代

#### P5: Vercel 图片优化

如果迁移到 Vercel 的 `functions` 配置格式，可以使用 Vercel Image Optimization API 自动处理格式转换和缩放。

### 预期效果

| 优化项 | 首页加载量 | 实施难度 |
|--------|-----------|---------|
| 当前 | ~5 MB | - |
| P0 格式转换 | ~1.2 MB | 低 |
| P0+P1 响应式 | ~0.8 MB | 中 |
| P0+P1+P2 lazy | ~0.5 MB | 中 |
| 全部优化 | ~0.4 MB | 高 |
