# AGENTS.md — SolarOne 外贸站开发约定

面向编码 Agent 的项目速查。只写「不做就会踩坑」的约束，通用 Django 知识不重复。
对外内容摘要见 `llm.txt`；详细方案见 `docs/`。

## 1. 技术栈与运行

| 项 | 值 |
|---|---|
| 框架 | Django 6.0（本地）→ Vercel（`api/index.py` + `build.sh`） |
| Python | `E:/Python/python3/python.exe`（Django 相关一律用它；Playwright 只在 `.venv`） |
| 静态 | Whitenoise + `build.sh` 输出到 `public/static/`，由 Vercel 边缘 CDN 直供 |
| 语言 | 六语种 en/fr/es/de/ru/ar（ar 为 RTL），`i18n_patterns`，**英文无 `/en/` 前缀** |
| 版本 | `VERSION` 文件，当前 v1.8.1 |

常用命令：

```bash
E:/Python/python3/python.exe manage.py check
E:/Python/python3/python.exe manage.py test          # 全量约 253 用例
E:/Python/python3/python.exe scripts/dev_preview.py  # 本地预览 :8000，runserver --noreload
E:/Python/python3/python.exe -m pages.seed_sync --json   # JSON → 构建产物（见 §3）
```

改代码后 `runserver` 不会自动重载，必须手动重启。

## 2. 目录地图

- `pages/` 主应用：`models.py`（Product/Project/NewsArticle/SiteConfig）、
  `views/`（`views_products|projects|other|contact.py`，`utils.py` 图片路径解析）、
  `admin/`、`cards.py`、`storage.py`、`static_index.py`
- `templates/` 22 个模板 + `sitemap.xml` + `robots.txt`
- `static/css/base.css` 全站样式单文件（含主题 token）
- `seed_data.json` **生产内容真源**（24 产品 / 22 项目 / 1 新闻 / SiteConfig）
- `pages/seed_data.py` 构建产物（git 忽略，由 build.sh 重新生成）
- `scripts/` `dev_preview.py`、`verify_static_build.py`、`e2e/`（run_checks、visual_review）
- `locale/` 6 个 `.po` + `.mo`（都进 git；本机无 gettext，用 polib 编译）

## 3. 内容真源 — 最高频事故区

- 生产**零数据库**：内容来自 `seed_data.json` → 构建期生成 `pages/seed_data.py`。
- 🔴 `pages/seed_sync.py` **默认是 DB → JSON**，且会被 admin 保存自动触发。
  只改 JSON 会被静默覆盖；只改 DB 也进不了生产。
  **改文案：DB 与 JSON 同改，然后显式跑 `--json`**；改 DB 用 `.update()`（不触发 post_save）。
- 写 JSON 前必须验证字节往返一致（文件为 CRLF，读出改完要 `.replace('\n','\r\n')`）。
- 图片文件名上传即固化，改名须同步 JSON 才能避免线上 404。

## 4. 三套翻译机制（互不相通，改动要分别处理）

1. **gettext** `{% trans %}` / `.po`+`.mo`：只吃字面量；欠账冻结在 `KNOWN_UNTRANSLATED`，只许缩小。
   追加文案用文本追加（不重排既有条目、保 CRLF），再用 polib 编译。
2. **`_SIDEBAR_I18N` + `_t()`**：查不到静默回退英文；新增调用点必须登记
   `KNOWN_DYNAMIC_SITES`（common=8 / enrich=1 / views_other=4）。
3. **`translations` JSONField + `t()`**：Product/Project/NewsArticle；缺译回退英文，绝不空串。

铁律：**基础字段必须是英文**；型号（RT410、FL6M、VSP-4200W-9M-YP）、订购代码、数字单位不译；
品牌 `SolarOne` 永不音译。⚠️ HTML 注释里写 `{% trans %}` 字面也会被模板引擎解析 → TemplateSyntaxError。

## 5. 静态、构建、部署

- 生产用 `BundledManifestStaticFilesStorage`（哈希名 + 边缘长缓存）；哈希映射经
  build.sh 写入 `pages/static_index_data.HASHED_FILES`。改 CSS **不需要** bump `?v=N`。
- `build.sh` 对 collectstatic / manifest / 静态索引 **fail-closed**，任一失败即中止构建。
- `vercel.json` 的 `functions.*.excludeFiles` 只能是一条 ≤256 字符的字符串；
  **绝不能写 `"**"`**（会让 exclude 全失效）。
- main 每次推送产出 Preview + Production 两条部署；看线上以 Production 最新为准。
  Preview 有登录墙，curl 到 Next.js 登录页别误判为应用输出。
- 图片候选排序铁律：`_product_image_url` / `_dict_product_image_url` 中
  `images/products/{slug}/…` 必须排在 legacy 规范化路径 `images/{path}` **之前**，
  否则会命中 `staticfiles/`（本地不对外服务）里的陈旧副本 → 浏览器 404。
  守卫：`ProductImagePathResolutionTests`。

## 6. 测试约定

- 单文件 `pages/tests.py`（约 258 个 test 方法），改动必须配守卫用例。
- admin 测试 Client 需先 `setup_test_environment()`；打页面要带 `HTTP_HOST='localhost'`
  （ALLOWED_HOSTS 不含 testserver，否则 400）。
- 已知**与改动无关的 2 个 errors**：`ProductAdminSidebarTreeTests` 缺 `lookup_opts`
  （`pages/admin/product.py:114`）。另有 2 处故意 fail-closed 的 traceback（cache/SMTP down）。
- 反转既有契约时，必须同步重写或删除旧守卫（例：bento 布局的 `object-fit: cover`
  与「原尺寸不裁剪」断言直接冲突）。
- 新增视图要同步导出到 `pages/views/__init__.py`；新增公开路由要登记
  `scripts/e2e/visual_review.py:DEFAULT_PATHS`（守卫会强制）。
- 断点白名单（N-31 守卫，含模板内联 `@media`）：max-width ∈ {767,1024,1199}，
  min-width ∈ {768,1025,1200}。平板导航阈值是 1024/1025。

## 7. 已知缺口状态（v1.8.2）

- ✅ **联系表单**（2026-09-27 已闭环）：`api/index.py` 冷启动 `_ensure_runtime_schema()`
  建表 + Gmail **应用专用密码**（不是账号密码，开了 2FA 才能生成 16 位）。
  线上已实测收发成功。仍配 `CONTACT_NOTIFY_EMAIL` + `EMAIL_HOST_USER/PASSWORD`。
  注意：/tmp DB 仍会随重部署清空 —— 邮件是唯一持久副本，长期仍建议迁 Neon/Supabase。
- 🟡 **RTL 隔离（部分修复）**：卡片/详情标题、项目地点与 Results、型号已包 `<bdi>`，
  base.css 有 `[dir="rtl"] bdi { unicode-bidi: isolate; }`，守卫 `RtlBidiIsolationTests`。
  **未覆盖**：规格表数值（specs/energy_data 表格）、面包屑、导航下拉、footer 联络信息。
- ✅ **未知产品 slug**（v1.8.2 已修）：`product_detail()` 中 `product is None` → `Http404`
  （旧行为是渲染 "Product Not Found" 但返回 200 的软 404）。守卫
  `ProductPageLayoutSplitTests.test_unknown_slug_returns_real_404`。
- 🟢 **本地 sqlite 锁**：已设 `timeout: 2`；VisitorTrackingMiddleware 每个前台 GET 都写库，
  长跑的 `manage.py test` 会与 runserver 抢锁，别并行跑。中间件 except-pass 吞写失败，页面不受影响。
- ✅ **每日独立访客统计**（v1.8.2 修）：原 `visited_at__date=today` 在 SQLite 上按 UTC 求值，
  而 today 是 Asia/Shanghai → 每天 00:00–08:00 CST 每条访问都算 unique（统计虚高）。
  现用 `_site_day_bounds_utc()` 显式按站点时区日界转 UTC 区间比较。
  ⚠️ 该 bug 只在 UTC 与本地日期不同的窗口可复现，白天跑测试是绿的。
- 另见（2026-09-27 日志）：preview 子域名 `*.vercel.app` 未进 ALLOWED_HOSTS → 预览站 400；
  `images/hero-main.webp` 不在静态哈希清单 → 回退未哈希 URL（能显示但无长效缓存）。

### 改模板前必查
给动态文本加包裹元素（如 RTL 的 `<bdi>`）会打破「标签内纯文本」型正则断言
（例如 `<h3 ...>([^<]+?)</h3>` 匹配为空）。改前先 grep 该类断言，改后断言应
**剥内层标签再比文本**（断言行为，不断言标记）；
或用模板源码断言（测试 DB 常无 Product/Project 行，渲染 HTML 断言会空通过）。

## 8. 硬性禁区

- **禁用 `git rm`**（曾误删 `pages/`）。
- **不要动** `old-hid-lighting.webp` / `new-led-lighting.webp`（文件名写死）。
- 样式改在 `static/css/base.css`；新增响应式断点须同步 N-31 白名单。
- JS 增强的隐藏一律用 `html.js` 门控（无 JS 时全可见）。
- 本项目有 `.workbuddy/memory/`：动工前先读最近几天的日志，收工后追加。
