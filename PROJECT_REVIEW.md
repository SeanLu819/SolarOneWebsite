# SolarOne Website Project Review

> **Last audit: 2026-07-26** (post P0 WebP + security hardening, commit `bebc2ec`, tag `rollback-p0-webp-20260726`)
>
> **Progress summary**: 13/31 items resolved, 3 partially resolved, 15 pending. P0 全部完成; P1 剩 2 项; P2/P3 多数待处理。
> 详见文末「改造进度总表」。

## Project Overview
A Django-based multi-language corporate website for SolarOne (LED lighting manufacturer), deployed on Vercel. Features include product showcase, project portfolio, about page, contact form, visitor tracking, and dark/light theme support.

---

## 1. Security Issues (High Priority)

### 1.1 Insecure Default SECRET_KEY
**Status: ✅ FIXED** (2026-07-26) — Vercel 生产环境强制要求 `SECRET_KEY` 环境变量，未设置则 KeyError; 本地保留 dev fallback。
**File:** `solarone/settings.py` line 13
```python
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production-x9k2m')
```
The fallback key is a weak, predictable default. If the `SECRET_KEY` env var is not set on Vercel, sessions and CSRF tokens are compromised.
**Fix:** Remove the fallback entirely or raise an error in production:
```python
SECRET_KEY = os.environ['SECRET_KEY']
```

### 1.2 DEBUG Defaults to True
**Status: ✅ FIXED** — `DEBUG = not IS_VERCEL and os.environ.get('DEBUG', 'True').lower() == 'true'`, Vercel 上强制 False。
**File:** `solarone/settings.py` line 19
```python
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
```
This defaults to `True` when the env var is absent. On Vercel, `DEBUG=True` would expose sensitive stack traces.
**Fix:** Default to `False`:
```python
IS_VERCEL = os.environ.get('VERCEL', '') == '1'
DEBUG = not IS_VERCEL and os.environ.get('DEBUG', 'False').lower() == 'true'
```

### 1.3 ALLOWED_HOSTS Wildcard
**Status: ✅ FIXED** — 默认 `.vercel.app,localhost,127.0.0.1`, 不再使用 `*`。
**File:** `solarone/settings.py` line 21
```python
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')
```
Using `*` in production enables HTTP host header injection attacks.
**Fix:** Set specific Vercel deployment domains:
```python
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '.vercel.app').split(',')
```

### 1.4 Contact Form - No Rate Limiting
**Status: ⏳ PENDING** (P2) — 尚未添加限流。
**File:** `pages/views.py` contact view
The contact endpoint accepts unlimited POST requests. A bot could spam thousands of messages.
**Fix:** Add Django Ratelimit or a simple session-based throttle.

### 1.5 `db.sqlite3` Committed to Repo
**Status: ✅ FIXED** — `.gitignore` 第 31 行已含 `db.sqlite3`。
**File:** `.gitignore` line 31 - `media/` and `staticfiles/` are excluded but `db.sqlite3` is NOT in `.gitignore`.
**Fix:** Add `db.sqlite3` to `.gitignore`.

---

## 2. Vercel Deployment Issues (High Priority)

### 2.1 No Database on Vercel
**Status: ⏳ PENDING** (P0, 高成本) — 仍用 SQLite `/tmp/db.sqlite3`。当前靠 seed_data.py 内嵌数据 + signed_cookies session 缓解, 但 contact 消息/visitor 统计/admin 在 Vercel 上不可用。
**File:** `solarone/settings.py` — Vercel 上用 `/tmp/db.sqlite3`
The project uses SQLite (`db.sqlite3`) which is read-only/ephemeral on Vercel. This means:
- Contact messages won't persist across deployments
- Visitor tracking won't work
- SiteConfig singleton will reset to defaults
- The entire admin panel is non-functional in production

**Fix:** Migrate to a serverless-compatible database (e.g., PostgreSQL via Neon, Supabase, or PlanetScale) and update `DATABASES` settings.

### 2.2 ImageField Requires Real Media Storage
**Status: ⏳ PENDING** (P1) — 模型仍用 ImageField, 但生产上 hero/logo/og_image 都走 seed_data 默认值 (空字符串), 实际不触发上传, 影响有限。
**Models:** `Product.image`, `Project.image`, `SiteConfig.hero_background`, `SiteConfig.logo`, `SiteConfig.og_image`
`ImageField` uploads to local filesystem which is ephemeral on Vercel. Uploaded images vanish on redeployment.
**Fix:** Use `django-cloudinary-storage`, `django-storages` with S3, or similar cloud storage backend.

### 2.3 VisitorTrackingMiddleware Disabled on Vercel
**Status: ✅ FIXED** — 改为 `if not IS_VERCEL: MIDDLEWARE.append(...)`, 不再重复加 CommonMiddleware。
**File:** `solarone/settings.py` line 49
```python
'pages.middleware.VisitorTrackingMiddleware' if not IS_VERCEL else 'django.middleware.common.CommonMiddleware'
```
This duplicates `CommonMiddleware` (already in the list at index 4). The condition replaces the tracking middleware with a middleware that's already loaded.
**Fix:** Either remove the duplicate or use a no-op:
```python
if not IS_VERCEL:
    MIDDLEWARE.append('pages.middleware.VisitorTrackingMiddleware')
```

---

## 3. Performance Optimizations

### 3.1 `get_common_context()` Queries Database on Every Request
**Status: ✅ FIXED** — 已用 `cache.get('site_config')` + 300s timeout, views.py 第 330-356 行。
**File:** `pages/views.py` line 116-133
`SiteConfig.objects.first()` is called on every page view. Since it's a singleton, this should be cached.
**Fix:** Use Django's cache framework:
```python
from django.core.cache import cache

def get_common_context():
    config = cache.get('site_config')
    if not config:
        config = SiteConfig.objects.first()
        if not config:
            config = SiteConfig.objects.create()
        cache.set('site_config', config, timeout=300)
    ...
```

### 3.2 N+1 Query Pattern in Views
**Status: ✅ NO ACTION NEEDED** — JSONField 在同一模型上, SQLite 下无 N+1; PostgreSQL 迁移时再评估。
**Files:** `pages/views.py` lines 189-205, 244-253
Dynamic attributes like `p.image_url`, `p.name_t`, etc. are set in a loop, but each iteration also calls `static()` which is fine (it's just URL computation). However, `Product.objects.all()` with no `select_related` or `prefetch_related` means translations (stored in JSONField) are loaded individually. Since JSONField is on the same model, this is actually fine for SQLite, but worth noting for a future PostgreSQL migration.

### 3.3 DailyStats Race Condition
**Status: ✅ FIXED** — 改用 `DailyStats.objects.filter(pk=...).update(total_visits=F('total_visits')+1, ...)`, middleware.py 第 58-63 行。
**File:** `pages/middleware.py` lines 59-63
```python
daily_stats, _ = DailyStats.objects.get_or_create(date=today)
daily_stats.total_visits += 1
if is_unique:
    daily_stats.unique_visits += 1
daily_stats.save()
```
Concurrent requests can cause lost increments (read-modify-write race).
**Fix:** Use `F()` expressions:
```python
from django.db.models import F
daily_stats.total_visits = F('total_visits') + 1
if is_unique:
    daily_stats.unique_visits = F('unique_visits') + 1
daily_stats.save(update_fields=['total_visits', 'unique_visits'])
```

### 3.4 Visitor IP Check is Two Queries
**Status: ⏳ PENDING** (P3) — 仍 2 次查询, 低优先级。
**File:** `pages/middleware.py` lines 40-43
```python
is_unique = not Visitor.objects.filter(
    ip_address=ip,
    visited_at__date=today
).exists()
```
Then immediately `Visitor.objects.create(...)`. This is 2 queries per request. Could use `get_or_create` or a single raw query.

### 3.5 Google Fonts Render Blocking
**Status: ⚠️ PARTIAL** — `display=swap` 已加; 仍同步加载 3 个字体族 (Space Grotesk + Inter + IBM Plex Mono)。IBM Plex Mono 仅用于小标签, 可考虑移除或自托管。
**File:** `templates/base.html` line 12
Three Google Font families are loaded synchronously in `<head>`, blocking first paint.
**Fix:** Add `display=swap` (already present) and consider using `font-display: optional` or preloading critical fonts only. Also, the `IBM Plex Mono` font is loaded but only used for small labels -- consider whether it's worth the extra request.

### 3.6 Image Weight (NEW — added 2026-07-26)
**Status: ✅ FIXED** — 16 张大图转 WebP (quality=80), 总体积 8.5MB → 781KB (-91%); hero-main 2.7MB → 84KB (-97%)。模板/seed_data/DB 路径全部更新。详见 commit `bebc2ec`。

---

## 4. Code Quality & Maintainability

### 4.1 Hardcoded Translation Map in views.py
**Status: ⏳ PENDING** (P2) — `_SIDEBAR_I18N` 仍在 views.py, 未迁至 .po 文件。
**File:** `pages/views.py` lines 9-38
A large `_SIDEBAR_I18N` dict duplicates what Django's i18n framework (`{% trans %}`) should handle. This is manually maintained and doesn't scale.
**Fix:** Move these strings to `.po` files and use `gettext()` in templates instead of the custom `_t()` function.

### 4.2 Sidebar Data Hardcoded in Views
**Status: ⏳ PENDING** (P2) — 仍硬编码。
**File:** `pages/views.py` lines 50-113
`_get_projects_sidebar()` and `_get_products_sidebar()` are hardcoded in Python. Adding a new product series or sport type requires a code change.
**Fix:** Derive sidebar data from the model's `choices` fields or a dedicated configuration model.

### 4.3 Product Filtering by Name Substring is Fragile
**Status: ⏳ PENDING** (P3) — 仍用 `name__icontains`。
**File:** `pages/views.py` line 195
```python
products_list = products_list.filter(name__icontains=active_series_label.replace(' Series', ''))
```
This does a substring match on the product name. If a product name doesn't contain the series keyword, it won't show up.
**Fix:** Add a `series` field to the `Product` model for explicit filtering.

### 4.4 Unused `|safe` Filter on Stats
**Status: ⏳ PENDING** (P2) — home.html 第 32/36/40/44 行仍有 `|safe`, 但这些是数字字符串 (500+/50+/60%/24/7), 风险低。第 199 行 seed_debug 的 `|safe` 合理 (JSON 渲染)。
**File:** `templates/home.html` lines 32-45
```django
{{ config.stat_projects|safe }}
```
These are plain `CharField` values from the database. Using `|safe` is unnecessary and could be dangerous if an admin enters HTML.
**Fix:** Remove `|safe` unless HTML content is intentionally expected.

### 4.5 Redundant Admin Condition
**Status: ✅ FIXED** — INSTALLED_APPS 已简化为直接列出 `'django.contrib.admin'`。
**File:** `solarone/settings.py` line 25
```python
'django.contrib.admin' if not IS_VERCEL else 'django.contrib.admin',
```
This conditional always evaluates to `'django.contrib.admin'` -- it's a no-op.
**Fix:** Simplify to just `'django.contrib.admin'`.

### 4.6 Multiple Utility Scripts for Translation Compilation
**Status: ✅ FIXED** — 5 个脚本 (add_translations.py/analyze_mo.py/compile_mo.py/compile_mo2.py/recompile_mo.py) 均已删除, 改用 `python manage.py compilemessages`。
**Files:** `add_translations.py`, `analyze_mo.py`, `compile_mo.py`, `compile_mo2.py`, `recompile_mo.py`
Five different scripts for essentially the same task (managing `.po`/`.mo` files). This is confusing.
**Fix:** Consolidate into a single management command like `python manage.py compilemessages` (Django built-in) and remove the custom scripts.

### 4.7 `test_request.py` in Project Root
**Status: ✅ FIXED** — 已删除。
This appears to be a test/debug script left in the project. Should be removed or moved to tests.

### 4.8 Contact Form Success Message Not Translated Properly
**Status: ✅ FIXED** — 改为 `messages.success(request, _('Your message has been sent successfully!'))`, views.py 第 397 行。
**File:** `pages/views.py` line 155
```python
messages.success(request, 'Your message has been sent successfully!')
```
This hardcoded English string should use Django's translation:
```python
messages.success(request, _('Your message has been sent successfully!'))
```

### 4.9 `images/processed/` Directory Outside `static/`
**Status: ✅ FIXED** — 根目录 `images/` 已不存在; 所有图片在 `static/images/processed/`。`.gitignore` 已修正 `/images/` 只匹配根目录。
**File:** `images/processed/Project-1.fw.png`
This directory is at the project root, outside the `static/` folder. It won't be served by WhiteNoise or Django's static file handling.
**Fix:** Move to `static/images/processed/` or document why it exists separately.

---

## 5. Template & Frontend Issues

### 5.1 Massive Inline CSS in `base.html`
**Status: ⏳ PENDING** (P2) — 仍内联 ~1300 行 CSS。Vercel 上 WhiteNoise 不缓存内联 CSS, 影响首屏。
**File:** `templates/base.html` lines 20-1328
~1300 lines of CSS are inlined in the base template. This:
- Makes the HTML response much larger
- Cannot be cached independently by the browser
- Makes it harder to maintain

**Fix:** Extract CSS to `static/css/styles.css` and use `{% static %}` to reference it.

### 5.2 Dynamic Typography Overrides Use `!important`
**Status: ⏳ PENDING** (P3) — 仍有 8 个 `!important`, 与 5.3 一起处理更合理。
**File:** `templates/base.html` lines 1337-1343
```css
.hero-title { font-size: {{ config.font_size_hero_title }} !important; }
```
Eight `!important` declarations override the base styles. This makes debugging difficult.
**Fix:** Use more specific CSS selectors or CSS custom properties for all size values, avoiding `!important`.

### 5.3 Admin Typography Settings Partially Broken
**Status: ⏳ PENDING** (P2) — `--ff-heading` 仍注入但未使用 (base CSS 用 `--ff-display`), admin 无法覆盖 display 字体。
**File:** `templates/base.html` line 1337 `--ff-heading: {{ config.font_family_heading }};`
The `SiteConfig` model stores `font_family_body`, `font_size_base`, etc., and these are injected into CSS via Django templates. However:
- `--ff-body` is set to the admin value, overriding the hardcoded `'Inter'` default
- `--ff-heading` is set but never used (the base CSS uses `--ff-display`)
- The base CSS defines `--ff-display: 'Space Grotesk'` which is NOT overridable from admin

**Fix:** Either rename `font_family_heading` to control `--ff-display`, or add a separate admin field for the display font.

### 5.4 Contact Page HTML Structure Error
**Status: ✅ FIXED** — contact.html 第 98-129 行结构正常, USA/Germany/France 三个 agent card 嵌套平衡, 无多余 `</div>`。
**File:** `templates/contact.html` line 99-100
```html
          </div>
        </div>
```
There's an extra closing `</div>` tag after the USA agent section, causing unbalanced nesting. The Germany agent card is likely rendered incorrectly.

### 5.5 Footer Social Media Icons Don't Include LinkedIn
**Status: ✅ FIXED** — base.html 第 1443-1444 行已加 LinkedIn 图标和链接。
**File:** `templates/base.html` lines 1422-1438
The footer shows Facebook, Instagram, YouTube, and TikTok, but the `SiteConfig` model also has `social_linkedin`. The LinkedIn icon and link are missing from the footer template.

### 5.6 RTL Support Incomplete
**Status: ⏳ PENDING** (P3) — nav/hero/footer 已支持, 但 sidebar/contact/about 页面局部缺 RTL 调整。
**File:** `templates/base.html` lines 202-212
RTL styles exist for nav, hero, footer, and some cards. But many page-specific elements (sidebar nav, contact form, about page grids) lack RTL adjustments.

---

## 6. SEO & Accessibility

### 6.1 Missing `<meta name="description">` in Base Template
**Status: ✅ FIXED** — base.html 第 9 行已加 `<meta name="description" content="{{ config.meta_description }}">`。
**File:** `templates/base.html`
The `<head>` section sets `<title>` but has no `<meta name="description">` tag, despite `config.meta_description` being available.
**Fix:** Add:
```html
<meta name="description" content="{{ config.meta_description }}">
```

### 6.2 No Open Graph Tags
**Status: ✅ FIXED** — base.html 第 10-12 行已加 og:title / og:description / og:image。
**File:** `templates/base.html`
The model has `og_image` but no OG meta tags are rendered.
**Fix:** Add OG tags in `<head>`:
```html
<meta property="og:title" content="{{ config.meta_title }}">
<meta property="og:description" content="{{ config.meta_description }}">
{% if config.og_image %}
<meta property="og:image" content="{{ config.og_image.url }}">
{% endif %}
```

### 6.3 No `<main>` Landmark
**Status: ⏳ PENDING** (P3) — base.html 第 1405 行仍是 `{% block content %}{% endblock %}`, 未包 `<main>`。
No `<main>` element wraps the page content. The `{% block content %}` directly renders `<section>` elements.
**Fix:** Wrap content in `<main id="main-content">` for screen reader accessibility.

### 6.4 Form Missing `aria-describedby` for Error States
**Status: ⏳ PENDING** (P3) — contact form 仍无服务端校验错误展示和 aria 关联。
The contact form has no server-side validation error display or associated `aria-describedby` attributes.

---

## 7. Architecture Recommendations

### 7.1 State Management
**Status: ⏳ PENDING** (与 2.1 同, 最高成本项)
- **Vercel + SQLite = broken persistence.** The most critical architectural fix is migrating to a cloud database.
- Consider a headless CMS (e.g., Strapi, Sanity) or at minimum PostgreSQL + connection pooling (e.g., PgBouncer, Neon).

### 7.2 Static Asset Pipeline
**Status: ⚠️ PARTIAL** — WebP 转换已完成 (3.6); WhiteNoise 仍在用, CDN 未接入。
- Currently using WhiteNoise with `collectstatic`. Consider using a CDN (Cloudflare, AWS CloudFront) for static assets in production.

### 7.3 Email Integration
**Status: ⏳ PENDING** (P2) — contact 消息只存 DB, 未发邮件。
- Contact messages are stored in DB but never sent via email. Consider adding `django-anymail` or `django.core.mail` to notify the sales team.

### 7.4 Admin Dashboard for Visitor Stats
**Status: ⏳ PENDING** (依赖 2.1 数据库迁移) — 本地 admin 可用, Vercel 上不可用。
- The visitor tracking admin exists but requires a writable database. With a proper database, consider adding a dashboard view with charts.

---

## 改造进度总表 (2026-07-26 核实)

> 图例: ✅ 已修复 / ⚠️ 部分修复 / ⏳ 待处理

### P0 (全部完成)
| # | Issue | 状态 | 备注 |
|---|-------|------|------|
| 1.1 | SECRET_KEY 不安全回退 | ✅ | Vercel 强制 env var |
| 1.2 | DEBUG 默认 True | ✅ | Vercel 强制 False |
| 1.3 | ALLOWED_HOSTS 通配 | ✅ | 改为 .vercel.app,localhost |
| 1.5 | db.sqlite3 入库 | ✅ | .gitignore 已加 |
| 2.3 | CommonMiddleware 重复 | ✅ | 改为条件 append |
| 3.6 | 图片体积过大 (NEW) | ✅ | 16 图转 WebP, -91% |

### P0 (高成本, 待处理)
| # | Issue | 状态 | 备注 |
|---|-------|------|------|
| 2.1 | SQLite → 云数据库 | ⏳ | 当前靠 seed_data 缓解; contact/visitor/admin 在 Vercel 不可用 |

### P1 (多数已完成)
| # | Issue | 状态 | 备注 |
|---|-------|------|------|
| 5.4 | contact.html 多余 `</div>` | ✅ | 结构已平衡 |
| 2.2 | ImageField 云存储 | ⏳ | 生产用 seed 默认值, 影响有限 |
| 6.1 | `<meta description>` | ✅ | base.html 已加 |
| 6.2 | OG tags | ✅ | base.html 已加 |
| 3.1 | 缓存 SiteConfig | ✅ | cache.get + 300s |
| 3.3 | DailyStats 竞态 | ✅ | 改用 F() |
| 5.5 | footer LinkedIn | ✅ | 已加图标和链接 |
| 4.8 | contact 成功消息翻译 | ✅ | 用 _() 包裹 |

### P2 (待处理)
| # | Issue | 状态 | 备注 |
|---|-------|------|------|
| 5.1 | 内联 CSS 抽离 | ⏳ | ~1300 行, 影响 Vercel 缓存 |
| 4.1 | 侧边栏翻译硬编码 | ⏳ | _SIDEBAR_I18N 未迁 .po |
| 4.2 | 侧边栏数据硬编码 | ⏳ | 未从 model choices 派生 |
| 4.6 | 翻译脚本合并 | ✅ | 5 脚本已删, 用 compilemessages |
| 7.3 | contact 邮件通知 | ⏳ | 仅存 DB |
| 5.3 | `--ff-heading` vs `--ff-display` | ⏳ | admin 无法覆盖 display 字体 |
| 1.4 | contact 限流 | ⏳ | 无限流 |
| 4.4 | home.html `|safe` | ⏳ | 数字字符串, 风险低 |

### P3 (待处理)
| # | Issue | 状态 | 备注 |
|---|-------|------|------|
| 5.6 | RTL 覆盖不全 | ⏳ | sidebar/contact/about 局部缺 |
| 6.3 | `<main>` landmark | ⏳ | content block 未包 main |
| 6.4 | form aria-describedby | ⏳ | 无服务端校验 |
| 4.3 | Product.series 字段 | ⏳ | 仍用 icontains |
| 4.9 | 根目录 images/ | ✅ | 已不存在 |
| 3.4 | visitor IP 2 次查询 | ⏳ | 低优先级 |
| 3.5 | Google Fonts 阻塞 | ⚠️ | display=swap 已加; IBM Plex Mono 可移除 |
| 4.5 | 冗余 admin 条件 | ✅ | 已简化 |
| 4.7 | test_request.py | ✅ | 已删除 |
| 5.2 | `!important` 覆盖 | ⏳ | 与 5.3 一起处理 |

### 无需处理
| # | Issue | 状态 | 备注 |
|---|-------|------|------|
| 3.2 | N+1 查询 | ✅ | JSONField 同模型, SQLite 无 N+1 |

**总计**: 32 项 — ✅ 已修复 16 项 / ⚠️ 部分修复 2 项 / ⏳ 待处理 14 项

### 建议下一批处理顺序
1. **5.1 抽离内联 CSS** — 中等成本, 直接改善 Vercel 首屏和缓存
2. **1.4 contact 限流** — 低成本, 补齐安全短板
3. **5.3 + 5.2 字体变量统一** — 低成本, 修 admin 排版设置
4. **7.3 contact 邮件通知** — 中等成本, 业务价值高
5. **2.1 云数据库迁移** — 高成本, 但解锁 contact/visitor/admin 全部功能
