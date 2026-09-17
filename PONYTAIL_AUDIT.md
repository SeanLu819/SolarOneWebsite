# SolarOne 代码精简审计报告（Ponytail 体检）

> 生成日期：2026-09-16
> 方法：以 `ponytail` 最小主义视角，对 `E:/Python/PROJECT/website` 做**只读**审计（视图层 / 共享模块 / 模板三个角度并行扫描）。
> 原则：可复用的重复逻辑 → 提取为单一可调用模块；过度设计/重造轮子/死代码 → 直接精简。
> 状态：A4+A1 **已实施并通过回归**（118 tests OK，2026-09-16）；其余待办。

---

## 0. 审计结论总览

| 类别 | 项数 | 说明 |
|------|------|------|
| A. 可提取为单一可调用模块 | A1–A11 | 重复逻辑收口（你最关心的"复用 → 模块"） |
| B. 可直接精简 | B1–B9 | 删死代码 / 无效分支 / 重造轮子 |
| C. 边界项（建议保留） | C1–C2 | 勿过度精简 |
| 顺带发现 Bug | 2 | 见 §4 |

---

## 1. A 组：可提取为「单一可调用模块」的重复

### A1. 数据读取兜底编排被复制 4 处 + news 内联一份
- 位置：`views_products.py:96-98 / 208-210`、`views_projects.py:37-39 / 58-60` 手写 `if not x: x = _from_json(...)`；`views_other.py:49-74` 的 `news()` 内联整段 `IS_VERCEL→seed / 否则 try DB 失败回退 seed`。
- 已有设施：`pages/views/data_loaders.py` 的 `_get_*_from_db` / `_get_*_from_json`。
- 建议：`data_loaders.py` 加 `get_products / get_product_detail / get_projects / get_project_detail / get_news` 五个编排函数，内部统一 `from_db or from_json`；5 处调用点缩成一行。**（本轮实施）**

### A2. 侧栏「按 active_key 反查 label」循环抄 3 份（同文件两份逐字相同）
- 位置：`views_products.py:82-93`、`views_projects.py:24-35` 与 `:72-83`。
- 建议：`i18n.py` 加 `_resolve_active_labels(sidebar, active_key, active_sub_key)` 返回 `(label, sub_label)`，三处循环统一调用，删 40+ 行。

### A3. 图像 URL 解析 5+ 份同构
- 位置：`views/utils.py:207-247 / 250-315 / 425-448`、`views_products.py:9-43 / 46-67`。
- 建议：合并为唯一 `_image_url_from_path(path, slug, static_dir='images/products')`，5 个变体全部委托。

### A4. admin / model 手写「改 seed_data.json + seed_data.py 文本」手术 5 处
- 位置：`admin/product.py:180-219`、`admin/project.py:78-118 & 179-238`、`admin/products_page.py:119-154`、`models.py:675-733`。
- 已有设施：`pages.seed_sync.sync_seed_from_db()`（整文件重写）+ `admin/mixins._sync_seed_files` 已调用。
- 建议：删掉手写 seed 文本改写，只保留「media→static 文件拷贝」，seed 内容交给 `sync_seed_from_db()` 重生成（顺带消除与 mixin 重复触发导致的竞态）。**（本轮实施）**

### A5. 静态文件扫描两份实现
- 位置：`views/utils.py:89-154` vs `seed_sync.py:95-169`（含 `_find_static` vs `_static_file_exists`）。
- 建议：抽 `pages/static_scan.py` 共用。

### A6. 项目封面解析两份
- 位置：`seed_sync.py:514-570` vs `views/utils.py:360-422`。
- 建议：单一 `resolve_project_cover(slug, db_path)`。

### A7. `t()` 翻译回退 4 份逐字相同
- 位置：`models.py:180-186 / 293-299`、`views/utils.py:517-522 / 540-545`。
- 建议：抽模块级 `translate(getter, translations, field, lang)`，模型方法与 dict shim 共用。

### A8. 哈希后缀剥离：已有单一真源却仍活 3 薄包 + 1 内联
- 位置：`models.py:576-591`（内联正则）、`seed_sync.py:27-33`、`views/utils.py:181-187`（透传别名）、`models.py:783 _clean_hashed_filename`（保留）。
- 建议：统一 `utils.strip_hash_suffix` + `models._clean_hashed_filename`，删其余。

### A9. 模板侧栏 3 份 + 2 份
- 位置：产品侧栏 `products.html:28-62 / product_detail.html:32-66 / product_series.html:29-63`；项目侧栏 `projects.html:28-51 / project_detail.html:32-55`。
- 建议：抽 `includes/product_sidebar.html` + `project_sidebar.html`（仿已成功的 `includes/nav_items.html`）。

### A10. BreadcrumbList JSON-LD 5 份副本（且 URL 来源不一致）
- 位置：`products.html:11-20 / product_detail.html:13-23 / product_series.html:11-21 / projects.html:11-20 / project_detail.html:13-23`。
- 建议：抽 `includes/breadcrumb_jsonld.html(crumbs)`，**顺手修掉 URL 不一致 Bug**（见 §4）。

### A11. 轮播 JS / CSS 各 3 份
- 位置：JS `product_detail.html:941-1005 / product_series.html:401-469 / project_detail.html:464-527`；CSS 同三页 `683-778 / 209-300 / 359-450`。
- 建议：JS 抽 `includes/carousel_js.html`；CSS 移入 `base.css`。

---

## 2. B 组：可直接精简（删死代码 / 无效分支 / 重造轮子）

- **B1/B2. 无意义 if/else**：`views/utils.py:190-204 _static_url` 与 `:425-448 _project_image_url` 两个分支都 `return static(rel)`，`_find_static` 检查是死代码 → 直接 `static(...)`。
- **B3. DATABASES 重复块**：`settings.py:213-239` 的 except/else 两块 SQLite 配置逐字相同 → 合并为共享常量。
- **B4. IP 解析手造且重复**：`middleware.py:87-93` 与 `views_contact.py:12-16` 各自手写 `x_forwarded_for.split(',')[0]`，回退语义不一致 → 统一收口到单一真源。⚠️ 实测 **Django 6.0.7 无 `django.utils.http.get_client_ip`**（audit 误判该内置符号存在，'3.2+ 已处理 XFF' 说法不成立），故改为新建 `pages/ip.py::get_client_ip` 作为唯一真源收口点，两处调用点统一路由，行为逐字一致；未来若 Django 补回该 helper，只需改 `pages/ip.py` 一处 import，调用点零改动。
- **B5. 死代码**：`models.py:778 _update_seed_project`（docstring 自认 legacy，全仓无调用）、`seed_sync.py:20 import copy`（未用）、`views/utils.py:5 SimpleNamespace`（未用）→ 删。
- **B6. 模板内联样式 6 份**（`padding:100px 0 80px`、`position:sticky;top:100px`、`sidebar-nav-header` 等）→ 在 `base.css` 引入 `.page-top / .sidebar-nav` 类替代。
- **B7. 404/500 互相复制**（`404.html:1-26` vs `500.html:1-26`）→ 抽 `includes/error_page.html(code/title/message)`；附带两者都不 `extends base.html`，多语环境缺导航/语言切换。
- **B8. base.html 内 theme/language 切换标记各 2 份**（`:119-123/152-155`、`:124-137/156-169`）→ 抽 `includes/theme_toggle.html` + `lang_switch.html`。
- **B9. admin 图片预览硬编码 60×45**：`admin/product.py:74-83` 与 `products_page.py:185-191` → 抽 `admin_image_preview(field, size=...)`。

---

## 3. C 组：边界项（建议保留，勿过度精简）

- **C1. `_load_local_env`**（`settings.py:18-35` 自写极简 `.env` 解析）— 注释已说明"minimal on purpose"，保留或换 `python-dotenv` 皆可，非必须。
- **C2. `_hash_ip`**（`middleware.py` 用 `hashlib` 做 peppered SHA-256）— 用法合理，不是重造轮子。

---

## 4. 顺带发现的 Bug / 风险

1. **Breadcrumb URL 不一致**（A10）：产品页内部混用 `{{ canonical_origin }}` 与 `{{ request.scheme }}://{{ request.get_host }}`，跨产品页不统一 → 抽 include 时一并修。
2. **Seed 文本手术竞态**（A4）：5 处手写 seed 改写与 `CacheClearMixin` 已调用的 `sync_seed_files` 重复触发，正则手术脆弱且可能冲突。
3. `_static_url` 死分支（B1）只是冗余，不是故障。

---

## 5. 建议的实施顺序（最小阻力）

1. **A4 + A1** — 删 5 处 seed 文本手术 + data_loaders 收口。收益最大、范围清晰、风险可控。✅ **已完成（2026-09-16，118 tests OK，含 QA 发现的 D1 完整性缺陷修复）**
2. **A8 + B4 + B1/B2 + B5** — 低风险清理：哈希剥离统一、IP 用内置、死 if/死代码删除。
3. **A2 + A3 + A7 + A5 + A6** — 中等重构，抽公共模块（label 反查 / 图像 URL / translate / static_scan / cover）。
4. **A9 + A10 + A11 + B6/B7/B8** — 纯 DRY 模板 include，视觉零变化。

---

## 6. 进度跟踪

| 项 | 状态 |
|----|------|
| A1 data_loaders 收口 | ✅ 已完成（2026-09-16，118 tests OK） |
| A2 侧栏 label 反查 | ✅ 已完成（2026-09-17 批次一，`7ca3b61`；233 例穷举等价） |
| A3 图像 URL 解析 | ✅ 已完成（2026-09-17 批次一，`7ca3b61`；抽 `_passthrough_url` + `_first_static`） |
| A4 删 5 处 seed 文本手术 | ✅ 已完成（2026-09-16，118 tests OK） |
| A5 静态扫描模块 | ✅ 已完成（2026-09-17 批次一，`pages/static_scan.py`；两径 510 路径集合逐字一致） |
| A6 封面解析模块 | ❌ **不合并**（2026-09-17 论证：两者契约不同，22 个种子项目中 9 个结果不同。已改写 docstring 互相交叉引用，防止后续误合并） |
| A7 translate 模块 | ✅ 已完成（2026-09-17 批次一，`pages.utils.translate`） |
| A8 哈希剥离统一 | ✅ 已完成（2026-09-17 step-2，`1bc6863`） |
| A9 模板侧栏 include | ❌ **不提取**（2026-09-17 论证：三份侧栏语义不同，见 §9.3。零变化 include 需 ≥8 个参数，比重复更难读） |
| A10 breadcrumb include | ✅ 已完成（2026-09-17 批次二，`8db122a`；顺修 §4-1 的 URL 不一致 Bug） |
| A11 轮播 JS 集中 | ✅ 已完成（2026-09-17 批次二，`8db122a`；含 `nonce`，删死代码 `restartAuto` 与永不触发的兜底） |
| A11 轮播 CSS 集中 | ❌ **不合并**（2026-09-17 论证：三份存在实质差异，见 §9.3。合并会改变两个页面的观感） |
| B1/B2 死 if | ✅ 已完成（2026-09-17 批次一，`7ca3b61`；塌缩 `_project_image_url` 残留的两处同值分支） |
| B3 DATABASES 合并 | ✅ 已完成（2026-09-17 批次一，`7ca3b61`；合入 `_LOCAL_SQLITE`） |
| B4 IP 统一收口（→pages/ip.py） | ✅ 已完成（2026-09-17 step-2，`1bc6863`） |
| B5 死代码 | ✅ 已完成（2026-09-17 step-2 + 批次一续清 `import re`） |
| B6 模板内联样式 | 🟡 **部分完成**（2026-09-17 批次三：`position:sticky;top:100px` 6 份收口 `base.css`，并删 4 处重复的移动端规则。其余内联样式与 `base.css` 类**不等价**，属"外观分歧"而非重复，见 §9.3） |
| B7 错误页 include | ✅ 已完成（2026-09-17 批次二，`8db122a`） |
| B8 base theme/lang | ✅ 已完成（2026-09-17 批次二，`8db122a`） |
| B9 admin 预览 | ✅ 已完成（2026-09-17 批次一，`7ca3b61`；`admin_image_preview`） |
| C1/C2 保留 | — |

---

## 7. 实施记录（A4+A1，2026-09-16）

- **收口函数**（`pages/views/data_loaders.py`）：新增 `get_products / get_product_detail / get_projects / get_project_detail / get_news` 五個编排函数 + 内部 `_normalize_news_article` / `_get_news_from_db` / `_get_news_from_json`；统一 `from_db or from_json` 兜底。
- **调用点改造**：`views_products.py`、`views_projects.py`、`views_other.py(news)` 的内联兜底缩成一行；`views_other.py` 删除整段 `IS_VERCEL→seed / 否则 try DB 失败回退 seed` 分支。
- **A4 删除**：`models.py:_rewrite_seed_project` + 4 处调用、`admin/product.py:_sync_product_images` 内 seed 改写块、`admin/project.py:_update_seed_pdf_url` + `_sync_project_images` 内 seed 改写块（保留 `re.search(r'_([a-zA-Z0-9]{7})$')` 用于文件名哈希剥离，非 seed 手术）、`admin/products_page.py:_sync_ppc_image` 内 seed 写回块。seed 内容统一交给 `sync_seed_from_db()` 重生成。
- **D1（QA 独立验证发现）**：`views_products.py:206-208` 残留内联 `_get_product_detail_from_db/_from_json`，但这两个函数本文件未 import，是潜在 `NameError`（测试套件未覆盖该视图故未暴露）。已收口为 `product = get_product_detail(slug, lang)`。
- **验证**：`manage.py test pages --keepdb` → **Ran 118 tests ... OK**；`System check identified no issues (0 silenced)`。第 21–46 行 traceback 为故意触发的失败路径单测（`cache down` / `SMTP down` 验证 fail-closed），属预期内。
- **状态**：已 commit/push —— **v1.6.2 @ `6936038`（main，`ef32e34..6936038`）**；Vercel 将自动部署（main 自 2026-09-15 起为 Production Branch）。本地回归 118 tests OK。

---

## 8. 实施记录（A8+B4+B1/B2/B5，2026-09-17 step-2）

- **A8 哈希剥离统一**：唯一真源 `pages.utils.strip_hash_suffix`；删除 `views/utils._clean_hashed_name` 透传别名、`views_products.py`/`seed_sync.py`/`models.py` 内联正则与透传实现，移除无用 `import re`（`models.py`、`admin/project.py`）。保留 `models._clean_hashed_filename`（仅 basename 薄包）。
- **B4 IP 统一收口**：新建 `pages/ip.py::get_client_ip`（取 XFF 首跳否则 REMOTE_ADDR）作唯一真源；`middleware.py`/`views_contact.py` 改调用（middleware 用导入别名避免与实例方法 `self.get_client_ip` 递归）。Django 6.0.7 无内置 `get_client_ip`，故自建。
- **B1/B2 死 if 塌缩**：`_static_url`（utils.py:181）与 `_project_image_url`（utils.py:416）内部的 `if _find_static(x): return static(x); return static(x)` 两分支同值，塌缩为 `return static(x)`。**函数保留**（仍被 `enrich.py`/`data_loaders.py`/同文件调用），仅删死判断，不是删函数。
- **B5 死代码删除**：`models._update_seed_project`（全仓无调用，含误导注释"retained for external callers"）、`seed_sync.py import copy`（未用）、`views/utils.py from types import SimpleNamespace`（未用）。
- **重要偏差**：审计原始行号基于 pre-A8；grep 复核发现 `_static_url`/`_project_image_url` 实为活跃函数（共约 12 处调用），故 B1/B2 定为"塌缩死分支"而非"删函数"，避免误伤 `enrich`/`data_loaders`。
- **验证**：`manage.py test pages --keepdb` 通过 **118 tests OK**，`System check identified no issues (0 silenced)`。
- **状态**：已 commit/push —— step-2 @ `1bc6863`（main，`6936038..1bc6863`）；Vercel 从 main 自动部署。

---

## 9. 实施记录（A2/A3/A5/A7/B3/B9 → A10/A11-JS/B7/B8/A6 → B6，2026-09-17 批次一/二/三）

### 9.1 批次一 —— 抽公共模块（commit `7ca3b61`）

- **A2**：`i18n._resolve_active_labels(sidebar, active_key, active_sub_key)` 收口 3 处逐字相同的 label 反查循环（`views_products.py`、`views_projects.py` ×2），−33 行。
- **A3**：`views/utils.py` 新增 `_passthrough_url()`（统一绝对 URL / `/static/` / `/media/` 透传守卫）与 `_first_static()`（统一"候选列表 → 第一个存在的静态文件"循环），4 处手写候选循环 + 3 处根路径守卫全部委托。
- **A5**：新增 `pages/static_scan.py`（`static_dirs()` / `build_file_set()`），`views.utils._build_static_file_set` 与 `seed_sync._build_static_set` 共用；**纯计算不缓存**，各自的缓存与失效语义保持不变。
- **A7**：`pages/utils.translate(getter, translations, field, lang)` 收口 `models.Product.t` / `Project.t` 与 `views.utils._DictProduct.t` / `_DictProject.t` 四份逐字相同实现。
- **B3**：`settings.py` 的 `except ImportError` / `else` 两块逐字相同的 SQLite 配置合并为 `_LOCAL_SQLITE` 常量。
- **B9**：`admin_image_preview(field, size, placeholder)` 收口 `ProductAdmin` 与 `ProductsPageCardAdmin` 的 60×45 缩略图；两处标记串逐字一致（含 `(no image)` 占位差异，用 `placeholder` 参数保留）。
- **顺带收尾 B1/B2**：`_project_image_url` 中 A8 轮漏改的两处 `if _find_static(x): return static(x)` / `return static(x)` 同值分支塌缩。
- **顺带收尾 B5**：删 `views/utils.py` 与 `seed_sync.py` 中 A8 后已成死引用的 `import re`、`views_products.py` 未使用的 `settings` 导入、`seed_sync.py` 两处冗余局部 `import os`。
- **验证**：118 tests OK；A2/A3 **233 例穷举等价**；A5 两个实现 510 条路径集合逐字一致；B9 标记串逐字一致；12 页渲染冒烟 200 / 无空 `img src` / 标签正确；`python -m pages.seed_sync --json`（build.sh 走的 CLI 路径）正常。
- **⚠️ 验证救回一次真回归**：抽取 `_static_url` 时，`_static_url('')` 一度从 `''` 变成 `'/static/'`（空值未提前返回）。等价性验证脚本捕获后修复 —— 这是"先写等价性断言再改"的价值所在。

### 9.2 批次二 —— 模板去重（commit `8db122a`）

- **A10**：5 处近重复面包屑 JSON-LD 收口为 `includes/breadcrumb_jsonld.html`（`section` / `leaf_name` / `leaf_url` 参数化）；**顺修 §4-1 的 Bug** —— 产品详情页原先混用 `request.scheme://request.get_host`，本地/预览下会向搜索引擎吐出 `http://testserver`，现全站统一 `canonical_origin`（实测已从 `http://testserver/` 变为 `https://www.solaronelighting.com/`）。
- **A11（JS）**：三处轮播脚本收口为 `includes/carousel_js.html`，`nonce="{{ request.csp_nonce }}"` 随 `<script>` 标签一起进 include。顺删 `product_series.html` 中定义但**从未调用**的 `restartAuto()`，以及永不触发的 `|| 3000/4000` 兜底（三页均显式设置 `data-interval`）。
- **B7**：`404.html` / `500.html` 收口为 `includes/error_page.html`（`code` / `title` / `message` / `accent` 参数化）；保留独立版式，按审计要求**不**改为继承 `base.html`。
- **B8**：`base.html` 中抽屉与桌面导航各两份的主题/语言切换标记收口为 `includes/theme_toggle.html` + `includes/lang_switch.html`，以 `variant="panel"` 区分抽屉变体（`.panel-action` + label span）。
- **验证**：118 tests OK；**80 组渲染矩阵**（10 路由 × 2 主题 × 2 视口 × 2 语言）与改前逐字节对比，差异仅三类且全部为预期 ——（a）面包屑 origin 修正，（b）`{% include %}` 引入的空白，（c）`{% now "U" %}` 渲染时间戳；全部标记计数相等（无内容丢失）；Playwright **32 例计算样式 0 处变化**（级联未受影响）；PNG 差异经两次对照运行分离，全部落在轮播/滑块页的已知抖动范围内。

### 9.3 论证后**不实施**的项（重要：审计前提有误）

审计假设这几项是"逐字重复"，实测它们是**语义分歧**。强行 DRY 需要"参数化重复"，比原状更难读，且会改变观感。

- **A6 不合并**：`seed_sync._discover_project_cover` 与 `views/utils._find_project_cover_path` 是**两种契约** —— 前者"修复磁盘上已不存在的路径"（忽略记录名，取第一个可用图），后者"解析用于展示的封面"（优先尊重作者记录的文件）。实测在 **22 个种子项目中 9 个结果不同**。合并必然二选一地改变行为。原 docstring 写的 "mirroring _find_project_cover_path logic" 正是诱导后续错误合并的根源，已改写为明确的契约说明并互相交叉引用。
- **A9 不提取**：三份产品侧栏至少有 5 处语义分歧 ——（1）父级高亮比较的是不同变量（`products.html` → `active_category`；`product_series.html` → `active_series`；`product_detail.html` **不做**父级高亮）；（2）`sidebar-nav-header` 在 `products.html` 用类，在 detail/series 用内联样式且**数值不同**（12px/0.15em/mb20 且无下边框 vs 类定义的 11px/0.14em/mb18 + `font-weight:600` + 下边框）；（3）`.sidebar-nav-group` 仅 detail/series 有 `margin-bottom:3px`，而该 class 在 `base.css` **根本没有定义**；（4）"View All" 链接同样是"类 vs 不等价内联"；（5）项目侧栏无孙级层。要做成零变化 include 需 ≥8 个参数 —— 典型的"参数化重复"反模式，故保留重复并在本记录留证。
- **A11（CSS）不合并**：三份 `.ps-*` 规则块并非相同 —— `.ps-carousel-slide img` 在 `product_detail`/`product_series` 是 `max-width:760px; object-fit:contain`，在 `project_detail` 是 `object-fit:cover`（无 max-width）；`.ps-thumbnails` 的 `margin-top` 是 `12px` vs `8px`；`.ps-carousel` 的 `background:transparent; border-radius:0` 仅 `product_detail` 有。合并会改变两个页面的观感。
- **B6 其余内联样式不动**：同理 —— 侧栏那几处内联样式与 `base.css` 的类**数值不等价**（见 A9 第 2/3/4 点），照审计"移动进 base.css"会改变页面外观。`about.html` 另有约 40 处内联样式（审计估"约 6 处"），量级不同，需先确认设计意图再动。

### 9.4 批次三 —— B6 的可零变化子集（本次）

只做**真重复**且**可证零变化**的部分：

- 6 个模板（`products` / `product_detail` / `product_series` / `projects` / `project_detail` / `news`）的 `<aside class="sidebar-nav" style="position: sticky; top: 100px;">` 内联样式收口到 `base.css` 的 `.sidebar-nav` 规则。
- **为什么零变化**：`base.css:1896` 的 `@media (max-width: 767px)` 块**本来就**用 `position: relative !important; top: auto !important` 覆盖 —— author `!important` 同样能压过普通内联声明，所以移动端在改动前后都是 `relative`；`>767px` 则由新的类规则给出与旧内联完全相同的 `sticky / 100px`。
- **顺带删重复**：`news.html` / `product_detail.html` / `product_series.html` / `project_detail.html` 各自还内联了一份**与 base.css 逐字相同**的 `@media (max-width:767px) .sidebar-nav{...}` 规则（断点与声明都相同）→ 删除。因两份都是同断点的 `!important`，删除模板副本不改变级联。
- **验证**：118 tests OK；Playwright **32 例计算样式 0 处变化**（改前 vs 改后两次独立对照，均 0）；逐页实测 `.sidebar-nav` 计算值 —— 桌面 6/6 为 `sticky / 100px`，移动 6/6 为 `relative / auto`，与改动前的等效预期一致。

### 9.5 本批次的方法论要点（下次复用）

1. **先写等价性断言，再改代码**：`_static_url('')` 的回归就是这样被拦下的。对"无害重构"同样适用。
2. **DRY 审计的前提必须逐条验伪**：本轮 4 个待办项（A6/A9/A11-CSS/B6）经查全是"分歧"而非"重复"。判断标准是**改后是否零变化**，而不是"长得像不像"。
3. **计算样式快照是级联改动的可靠仪器**：`getComputedStyle` 对固定选择器集合完全确定（同输入两次运行 0 差异），而 PNG 截图在轮播/滑块页天然抖动 —— 先跑两遍对照建立"抖动基线"，再分离真实变化。
4. **顺手记录"不做什么、为什么"**：把论证写进文档，比让下一个人重新发现一遍便宜得多。

### 9.6 三个"遗留待办"经实测**证伪**（2026-09-17，勿再处理）

这三条是审计收尾时我列进 P2 清单的，核查后**全部不成立**，记录在此以免后人重复劳动：

- **`settings.py` 的 Vercel `/tmp` SQLite 分支不是死代码**（原判断错误）：`IS_RUNTIME = IS_VERCEL and '/tmp/' in DATABASE_URL`，而 `api/index.py` 在 `VERCEL=1` 且未设 `DATABASE_URL` 时会写入 `sqlite:////tmp/db.sqlite3`；`views_contact.py:117` 正用 `IS_RUNTIME` 决定「已存但未发信 + 临时库」时**不能对用户谎报成功**（见 2026-09-13 事故）。删掉该分支会让联系表单在降级场景从「诚实报错」退化为「谎报成功」—— 是行为回归，不是精简。
- **`checks.py` 的措辞不矛盾**：它建议「设 `CONTACT_NOTIFY_EMAIL` + SMTP 凭据，或把 `DATABASE_URL` 指向持久库（Neon/Supabase）」。内容层的无状态化（v1.6.0 起全走 `seed_data.json`）与**联系表单需要持久落库**是两件独立的事，并不冲突。
- **`templates/product_series.html` 是确认的孤儿**（原判正确，但需用户决策）：`views_products.py:237` 的 `product_series()` 直接 `return product_detail(request, slug)`，故 `product_series.html` 永远不会被渲染；`templates/includes/carousel_js.html:16-17` 亦已记录此事。**注意**：本项目此前还对这个死模板做过 A10/A11/B6 去重（纯浪费）。**待用户决定「删除文件」还是「恢复独立路由」**——后者会改变用户可见布局，不可擅自实施。

---

## 10. 附带发现（非 Ponytail 项）：i18n —— 两套翻译机制，其中一套长期无守卫

核查 §9 遗留项时顺带发现的、与代码精简无关但影响面更大的问题，单独记此备查（详细过程见 `.workbuddy/memory/2026-09-17.md`）。**2026-09-17 已修复并建守卫（N-36/N-37）。**

- 本站有**两套互不相干的翻译机制**：
  1. **gettext 目录** `locale/<lang>/LC_MESSAGES/django.{po,mo}`（`.mo` 才是运行时查表对象）—— 服务模板 `{% trans %}` 与 Python `_()`；
  2. **`pages/views/i18n.py` 的 `_SIDEBAR_I18N` 硬编码字典** + `_t(label, lang)` —— 服务侧栏分类/系列/场馆类型/规格标签与 SiteConfig 文案；**查不到就 `entry.get(lang, label)` 静默回退英文**，既不报错也不记日志。
  此前**只有机制 1 有守卫，机制 2 完全没有**。
- **机制 1 实测缺口**：`locale/` 最后同步为 **2026-08-08**（`c88154a`），此后五周无人再跑 makemessages。模板侧 201 个可译串中 **31 个在 `.mo` 中无条目**，Python 侧 **4 条**同样缺失（正是联系表单给访客的全部提示）→ 在 fr/es/de/ru/ar 静默回退英文。重灾区为 **Cookie 同意条**（`base.html`，2026-08-15 由 `7765865` 引入、从未翻译）、`about.html` 的 cookie/隐私政策章节、移动端抽屉标签、产品规格表头。→ 新增 `I18nCatalogGuardTests`（4 例），35 条存量欠账冻结在 `KNOWN_UNTRANSLATED`，**只许缩小**。
- **机制 2 实测缺口**：**6 处现存漏译** —— 侧栏 `Karting Track` / `Fencing` / `Aquatics Centre` / `City Expressway` / `Airports`（`_get_projects_sidebar` 一直在请求，字典里却没有条目；字典里存的是 `Airports and Ports`，**键名对不上**），以及项目页标题 `Featured Projects`（`seed_data.json` 的 `siteconfig.projects_title` 经 `common.py` 的 `_t(config.projects_title, lang)` 下发）。已在 `/de/`、`/fr/`、`/ar/` 的 `/projects/` 运行时实测确认（同页 `Fußballplatz` 已本地化，而这些仍是英文）。六条均已补录五语翻译 → 新增 `DataDrivenTranslationTests`。
- ⚠️ **`templatize()` 的边界（守卫设计的关键教训）**：它会把 `{% trans 变量 %}` **整段 mask**，因此静态扫描对 `product_detail.html:176` 的 `{% trans item.label %}` 是**结构性盲区**（独立验证者把静态 trans 改成动态后，机制 1 的守卫仍然全绿）。故机制 2 的守卫改为扫「**谁会被传给 `_t()`**」的全集：`_t('字面量')` 首参 + `_PRODUCT_CARD_LABELS` / `_PRODUCT_CAT_TO_SIDEBAR_LABEL` 的取值（经 `enrich.py` 以变量传入）+ `_t(config.<字段>)` 对应 `seed_data.json['siteconfig']` 的英文取值。
- ⚠️⚠️ **只做静态提取是不够的 —— 迭代了三轮才闭合（这是本轮最大的教训）**：
  1. **第一版**（纯静态）的残余盲区：`_t()` 首参是变量、且来源不在上述两个映射字典中 → 静态看不见。独立验证者用 `_t(_QA_EXTRA['label'], lang)` 实测确认守卫仍绿。
  2. **第二版**加了两层：① 运行时 spy（patch `i18n._t`，真跑侧栏构建函数，记录**实际流经** `_t()` 的标签）② 非字面量 `_t()` **调用点数量清单** `KNOWN_DYNAMIC_SITES`（`common.py`:6、`enrich.py`:1）。
  3. **第三版才发现第二版仍有洞**：`enrich.py` 的 `card_label = _PRODUCT_CARD_LABELS.get(slug) or _PRODUCT_CAT_TO_SIDEBAR_LABEL.get(...)` —— 把**数据源换成第三张 dict** 时，**调用点数量没变**（清单绿）、静态只认那两张已知映射（也绿）→ 产品卡的分类标签可以在 fr/es/de/ru/ar 静默回退英文**而无人报警**。实测突变 M4 确认漏检后才补上：**必须 patch `pages.views.enrich._t`**（它是 `from .i18n import _t`，拿的是独立引用，patch `i18n` 模块拦不到），用 `seed_data.json` 的真实产品（20 个）驱动 `_enrich_product`（= 生产 `IS_VERCEL` 下的真实路径）再校验。
  - **方法论**：跨模块 `from x import y` 会让 runtime spy 失效 —— **patch 必须打在「调用方模块」上，而不是「定义模块」上**。这条写进 §9.5 之外单独强调。
- **验证**：全量 **131 tests OK**；三批共 **18 项变异测试**（基线绿 + 全部变异红），每条守卫都至少有一个「只有它能抓住」的突变作为非空洞证据。另顺手修掉 `product_detail.html` 的 `{% trans "L\" × W\" × H\"" %}` —— 它运行时渲染正确，但 `templatize` 会切出垃圾 msgid `L\`，下一跑 makemessages 就会污染 `.po`。
