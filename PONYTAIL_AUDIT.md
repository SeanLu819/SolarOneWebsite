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
- **B4. IP 解析手造且重复**：`middleware.py:87-93` 与 `views_contact.py:12-16` 各自手写 `x_forwarded_for.split(',')[0]`，回退语义不一致 → 统一用 `django.utils.http.get_client_ip`（3.2+ 已处理 XFF 与可信代理）。
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
| A2 侧栏 label 反查 | ⬜ 待办 |
| A3 图像 URL 解析 | ⬜ 待办 |
| A4 删 5 处 seed 文本手术 | ✅ 已完成（2026-09-16，118 tests OK） |
| A5 静态扫描模块 | ⬜ 待办 |
| A6 封面解析模块 | ⬜ 待办 |
| A7 translate 模块 | ⬜ 待办 |
| A8 哈希剥离统一 | ⬜ 待办 |
| A9 模板侧栏 include | ⬜ 待办 |
| A10 breadcrumb include | ⬜ 待办 |
| A11 轮播 JS/CSS 集中 | ⬜ 待办 |
| B1/B2 死 if | ⬜ 待办 |
| B3 DATABASES 合并 | ⬜ 待办 |
| B4 IP 用内置 | ⬜ 待办 |
| B5 死代码 | ⬜ 待办 |
| B6 模板内联样式 | ⬜ 待办 |
| B7 错误页 include | ⬜ 待办 |
| B8 base theme/lang | ⬜ 待办 |
| B9 admin 预览 | ⬜ 待办 |
| C1/C2 保留 | — |

---

## 7. 实施记录（A4+A1，2026-09-16）

- **收口函数**（`pages/views/data_loaders.py`）：新增 `get_products / get_product_detail / get_projects / get_project_detail / get_news` 五個编排函数 + 内部 `_normalize_news_article` / `_get_news_from_db` / `_get_news_from_json`；统一 `from_db or from_json` 兜底。
- **调用点改造**：`views_products.py`、`views_projects.py`、`views_other.py(news)` 的内联兜底缩成一行；`views_other.py` 删除整段 `IS_VERCEL→seed / 否则 try DB 失败回退 seed` 分支。
- **A4 删除**：`models.py:_rewrite_seed_project` + 4 处调用、`admin/product.py:_sync_product_images` 内 seed 改写块、`admin/project.py:_update_seed_pdf_url` + `_sync_project_images` 内 seed 改写块（保留 `re.search(r'_([a-zA-Z0-9]{7})$')` 用于文件名哈希剥离，非 seed 手术）、`admin/products_page.py:_sync_ppc_image` 内 seed 写回块。seed 内容统一交给 `sync_seed_from_db()` 重生成。
- **D1（QA 独立验证发现）**：`views_products.py:206-208` 残留内联 `_get_product_detail_from_db/_from_json`，但这两个函数本文件未 import，是潜在 `NameError`（测试套件未覆盖该视图故未暴露）。已收口为 `product = get_product_detail(slug, lang)`。
- **验证**：`manage.py test pages --keepdb` → **Ran 118 tests ... OK**；`System check identified no issues (0 silenced)`。第 21–46 行 traceback 为故意触发的失败路径单测（`cache down` / `SMTP down` 验证 fail-closed），属预期内。
- **状态**：代码已闭环、本地回归全绿；改动**尚未 commit/push**（沙箱无凭证，需用户本机执行）。
