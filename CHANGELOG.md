# Changelog

All notable changes to this project will be documented in this file.

## v1.5.5 - 2026-09-12

### Hotfix: every page returned HTTP 500 on Vercel (missing static manifest)

- **Symptom:** the deploy finally succeeded (v1.5.4), but every page answered
  *"Server Error — Something went wrong on our end"* (500).
- **Root cause:** v1.5.3 excluded `staticfiles/**` from the Python function
  bundle (necessary: it is ~59 MB of already-CDN-served assets), which also
  removed **`staticfiles.json`** — the manifest that
  `CompressedManifestStaticFilesStorage` needs at *request* time. With the
  manifest gone the storage falls back to looking the original file up on disk,
  but `static/` is excluded too, so it raised:

  ```
  ValueError: The file 'css/base.css' could not be found with
              <whitenoise.storage.CompressedManifestStaticFilesStorage ...>
  ```

  `base.html` calls `{% static %}` on every page, so a single unresolvable name
  takes the **whole site** down. `includeFiles: "staticfiles/staticfiles.json"`
  did not reliably put it back (and the file itself is only ~1 file among
  hundreds the builder juggles).

- **Fix — two layers:**
  1. **Ship the manifest as bundled Python source.** `pages/static_index.py`
     (already run by `build.sh` after `collectstatic`) now also copies the
     `staticfiles.json` → `paths` map into `pages/static_index_data.py` as
     `HASHED_FILES`. That module lives under `pages/`, which is never excluded,
     so the mapping is guaranteed to be inside the Lambda.
     `vercel.json` no longer needs `includeFiles` at all.
  2. **Never raise.** New backend
     `pages/storage.BundledManifestStaticFilesStorage` (used when `IS_VERCEL`)
     loads the map from the bundled module, falls back to Django's file-based
     manifest, and wraps `stored_name()` so an unresolvable name degrades to the
     **un-hashed URL** (the pre-v1.5.2 behaviour, still served by the edge CDN
     because WhiteNoise keeps both copies). Losing one cache header is an
     acceptable price; 500-ing the entire site is not.

- **Why the earlier verification missed it:** the v1.5.3 smoke test ran with the
  *local* plain `StaticFilesStorage` (only `IS_VERCEL` selects the Manifest
  backend), so the storage that actually breaks in production was never
  exercised. Fix confirmed by replaying both configurations:
  old backend + no manifest → **18/20 pages 500** (identical traceback); new
  backend → **20/20 pages 200**, hashed URLs when the map is present and
  un-hashed ones when it is not.

- **Diagnosability:** `api/index.py` now logs, at cold start, which storage class
  is active, how many entries the bundled manifest has, and the resolved URL for
  `css/base.css` / `images/hero-main.webp` — the exact facts that were missing
  while debugging this.

- **Tests:** `BundledStaticManifestTests` (7) + index-generator manifest tests
  (2). Includes an **inverted guard** asserting the old backend *does* raise
  `ValueError` in the same situation, so the subclass cannot be "simplified
  away". L1: 92 → **101 tests OK (skipped=2)**.

## v1.5.4 - 2026-09-12

### Hotfix: v1.5.3 wrote an invalid `vercel.json` (deploy blocked before build)

- **Symptom:** pushing v1.5.3 made Vercel fail in ~15 s with
  *"A Configuration error — Vercel couldn't load a valid project configuration
  for this deployment"*. This is a **config-schema** failure, not a bundle-size
  failure: the build never started.
- **Root cause:** `functions["api/index.py"].excludeFiles` was written as an
  **array**. Per the official schema (`https://openapi.vercel.sh/vercel.json`)
  both `excludeFiles` and `includeFiles` are `{"type": "string", "maxLength": 256}`,
  and that `patternProperties` node has `"additionalProperties": false` — so any
  array value is rejected outright. (`$schema` itself is a legal top-level key.)
- **Fix:** collapse the list into a **single glob with brace expansion**:
  `"excludeFiles": "{static,staticfiles,media,docs,screenshots}/**"`.
  - The builder's `normalizeGlobs()` wraps a string as `[value]` and **does not
    split on commas**; the pattern ends up in `@vercel/build-utils`' `glob()`
    (npm `glob` / minimatch underneath), and minimatch **does** support `{a,b}`.
  - **Verified with node + the real `glob` package** on a synthetic tree that
    mirrors the repo, replaying the builder's exact order
    (`glob("**", {cwd, ignore:[...predefined, ...excludeFiles]})` then
    `Object.assign(files, glob(includeFiles))`): zero heavy-directory files leak.
- **Belt and suspenders:** the builder additionally does
  `if (djangoStatic?.manifestRelPath) files[manifestRelPath] = new FileFsRef(...)`,
  i.e. it force-adds `staticfiles.json` back for Django projects regardless of
  excludes — so the explicit `includeFiles` is redundant but kept as insurance.
- **Reusable check:** a small script that downloads the official schema and
  asserts ① every top-level key exists in `properties` and ② each `functions`
  entry matches the declared `type` / `maxLength` / `additionalProperties`.
  It reproduces Vercel's error exactly on the v1.5.3 config
  (`excludeFiles : expected string, got list`).
- **New offline guard:** `pages/tests.py` → `VercelConfigTests` (4 tests, no
  network). It asserts top-level keys are known, `excludeFiles` / `includeFiles`
  are **strings** within `maxLength: 256`, no unknown function options are used,
  and the size fix's invariants hold (`static/**` + `staticfiles/**` excluded
  while `staticfiles/staticfiles.json` stays included). L1: **92 tests OK**
  (was 88, skipped=2).

## v1.5.3 - 2026-09-12

> ⚠️ **Superseded by v1.5.4** — the `excludeFiles` array below is invalid config
> and blocks the deploy. Use the v1.5.4 single-string form.

### Deploy blocker: Vercel function bundle exceeded the size limit (closes N-34)

- **Symptom:** the v1.5.2 deploy failed with *"Total bundle size (270.23 MB)
  exceeds the maximum function size (225 MB)"*.
- **Root cause:** `vercel.json` pinned `"includeFiles": "**"` on `api/index.py`.
  Vercel's Python builder globs `**` (excluding built-ins) and applies
  `includeFiles` **after** `excludeFiles`, so the wildcard forced the entire
  repository — including the 58 MB source `static/` tree and the 59 MB
  `staticfiles/` collectstatic output — into the Lambda. Static assets were
  then shipped twice: once to the edge CDN (via `public/`) and once into the
  function. Verified by reading `@vercel/python@latest` (`dist/index.js`):
  `files = glob("**", {ignore: [...excludeFiles]})` then
  `for (pattern of includeFiles) Object.assign(files, glob(pattern, workPath))`.
- **Fix:** `includeFiles` no longer contains `**`; the heavy trees are listed in
  `excludeFiles` (`static/**`, `staticfiles/**`, `media/**`, `docs/**`,
  `screenshots/**`). `public/**` was already excluded by the runtime itself.
  Expected bundle: ~270 MB → ~150 MB.
- **Static manifest kept:** `whitenoise`'s `CompressedManifestStaticFilesStorage`
  needs `staticfiles.json` at runtime. It is force-included with
  `"includeFiles": "staticfiles/staticfiles.json"` (applied last, so it survives
  the exclusion), and the Python builder also re-copies it for Django projects.
- **No asset cleanup was needed:** a DB-aware orphan audit (templates + CSS +
  `seed_data.json` + every text column of `db.sqlite3`) found **0** unreferenced
  files under `static/` and `media/` — all 377 images and 17 PDFs are live.

### Static index: image resolution survives the slim bundle (closes N-35)

- Removing `static/` from the function bundle would have broken request-time
  image resolution: `pages/views/utils.py` walks `STATICFILES_DIRS`/`STATIC_ROOT`
  to decide which candidate path really exists (`_find_static`) and to discover
  gallery/product images (`_list_static_dir`, `_list_product_dir_images`).
  Without it, products and project galleries would silently fall back to
  `/media/...` URLs that do not exist on Vercel.
- New `pages/static_index.py` writes a names-only index
  (`pages/static_index_data.py`, ~20 KB, git-ignored, rebuilt every deploy by
  `build.sh` after `collectstatic`) — the same convention as `pages/seed_data.py`.
- `utils.py` imports that index and treats it as a **union** with the disk scan,
  so local dev and CI behaviour is unchanged. `_list_product_dir_images` now
  delegates to `_list_static_dir` instead of its own `os.listdir` loop.
- Verified by simulating the Vercel filesystem (no `static/`, no `staticfiles/`):
  all 6 page types return 200 with identical static-image counts to the
  disk-backed baseline (`/`=6, `/products/`=9, `/projects/`=11, `/about/`=5,
  `/contact/`=4, `/news/`=1, project detail gallery=12) and **zero** `media-src`
  or empty-`src` regressions.

### CI was never green: missing Pillow (closes N-25 follow-up)

- All five CI runs so far failed (`run #1`–`#5`), including at `e0c1d85` and
  `9075205` — the failure predates v1.5.2 and was masked because the suite is
  usually run locally, where Pillow happens to be installed globally.
- **Root cause:** `requirements.txt` never declared Pillow, so a clean install
  fails Django's system check for all 14 `ImageField`s
  (`fields.E210: Cannot use ImageField because Pillow is not installed`) and
  `manage.py test` aborts with `SystemCheckError`. `Pillow>=10.0` added.
- Reproduced and verified in a disposable venv with `django>=6.0,<7.0`
  resolving to 6.1.1 (same as Vercel): before the fix
  `SystemCheckError (14 issues)`, after `Ran 80 tests … OK (skipped=2)`.
- CI now also generates `pages/static_index_data.py` before running tests, so
  `GeneratedStaticIndexCoverageTests` guards the index against going stale.

### Tests

- L1: **88 tests OK** (was 80, skipped=2) — new `StaticIndexBuildTests` (3),
  `StaticIndexFallbackTests` (4), `GeneratedStaticIndexCoverageTests` (1).

## v1.5.2 - 2026-09-12

### Loading performance: content-hashed static assets (P0, closes N-32)

- **Static storage is now content-hashed in production.** Live probing showed
  static assets already hit the Vercel edge (`X-Vercel-Cache: HIT`) but were
  served with `Cache-Control: public, max-age=0, must-revalidate`, so repeat
  visitors re-validated CSS/JS/images on every visit.
- **Root cause:** Django 6.0 **removed** the `STATICFILES_STORAGE` setting and
  silently ignores it. The project only assigned a backend through that legacy
  setting, so `collectstatic` kept emitting un-hashed filenames.
- **Fix:** configure the backend through the `STORAGES` dict, conditionally:
  production (`IS_VERCEL`) uses
  `whitenoise.storage.CompressedManifestStaticFilesStorage` (hashed filenames →
  Vercel's edge serves them `immutable, max-age=31536000`); local dev keeps plain
  `StaticFilesStorage`, because WhiteNoise's finders serve un-hashed files from
  the source `static/` tree and hashed URLs would 404 everywhere locally.
- `templates/base.html` drops the manual `?v=19` cache-buster (hashing now
  handles invalidation). `pages/tests.py` no longer asserts exact un-hashed image
  paths.
- `APP_VERSION` was stale at `1.2.1` and now tracks `VERSION`.

### Loading performance: above-the-fold (LCP) images (P1, closes N-33)

- First-screen images no longer carry `loading="lazy"` — they are the Largest
  Contentful Paint candidates, and lazy-loading them delayed the layout:
  `products.html` banner, `product_detail.html` hero plus its no-banner fallback,
  and `product_series.html` hero. Each now uses
  `fetchpriority="high" decoding="async"`.
- The light-theme banner variant stays eager but carries **no** `fetchpriority`,
  so it never competes with the primary (dark) banner for bandwidth.
- Deliberately left lazy: the below-the-fold `ps-banner` on series pages, plus
  carousels, thumbnails and galleries.

### SEO: multilingual sitemap (P1, closes N-33)

- Corrections to the previous audit: `robots.txt` and `sitemap.xml` were **not**
  missing — both are routed and return 200. The real gap was that the sitemap
  listed only the 49 English URLs for a six-language site.
- `/sitemap.xml` now emits one `<url>` per canonical path carrying
  `xhtml:link rel="alternate"` entries for all six languages plus `x-default`.
- Paths are reversed inside `with override('en')`, so requesting
  `/fr/sitemap.xml` no longer produces doubly-prefixed `/fr/fr/` URLs.
- No `<lastmod>` is emitted: there is no trustworthy last-modified source, and a
  wrong value is worse than none.

### Tests

- L1: **80 tests OK** (was 73) — new `SitemapMultilingualTests` (3) and
  `AboveTheFoldImageTests` (4).
- L2: new `run_phase4_review()` asserts, in a real browser DOM, that each LCP
  image is eager, `fetchpriority="high"`, `decoding="async"` and actually loaded
  (`naturalWidth > 0`). Full suite: ALL CHECKS PASSED.

## v1.5.1 - 2026-09-11

### seed_data.py → git-ignored build artifact (closes N-22)

- **`pages/seed_data.py` is no longer committed.** It was a ~3192-line generated
  file rebuilt from `seed_data.json` on every Vercel build (`build.sh` calls
  `python -m pages.seed_sync --json`). It is now `git-ignore`d, so the repo no
  longer carries the duplicated data — `seed_data.json` is the single source of truth.
- **`pages/seed_sync.py`**: JSON mode (`sync_seed_from_json`) now writes **only**
  `pages/seed_data.py` and never writes back to `seed_data.json` (previously it
  rewrote the JSON on every build — wrong, since the JSON is the source of truth).
  DB mode still writes both (DB → JSON + py).
- **Generated `.py` stays navigable**: section banners (`# ── products (20 items)`,
  etc.) are injected by `_write_seed_files`, so the artifact remains readable.
- **Local-dev safety**: new `python manage.py regenerate_seed` command rebuilds
  `pages/seed_data.py` from `seed_data.json` (e.g. after a fresh clone). On Vercel
  this is automatic; `pages/views/utils._load_seed` also falls back to the JSON
  file if the module import fails.
- **CI**: `.github/workflows/ci.yml` regenerates `seed_data.py` before tests so the
  test environment matches production (admin imports the module at runtime).
- **`seed_data.json` normalization**: one project cover path fixed
  (`red1-karting-01.webp` → `red1-karting-1080p-01.webp`, the file that exists).

## v1.5.0 - 2026-09-10

### Admin package split + seed_data section headers

- **`pages/admin.py` (1246 lines) → `pages/admin/` package**:
  - `__init__.py` — admin branding + re-exports (`admin_translate`, `ProjectAdmin`)
  - `widgets.py` — Specs / EnergyData / OrderingInfo / Translations widgets + `ENERGY_DATA_FIELDS` / `ORDERING_COLUMNS` / `ORDERING_DEFAULTS`
  - `mixins.py` — `CacheClearMixin` (cache invalidation + seed sync)
  - `product.py` — `ProductAdmin` with `_sync_product_images()` (4 widgets wired)
  - `project.py` — `ProjectAdmin` with `_sync_project_images()` + `_update_seed_pdf_url()`
  - `news.py` / `contact.py` / `siteconfig.py` / `visitor.py` — one admin class each
  - `products_page.py` — `ProductsPageCardAdmin` + custom `/admin/products-page/` view + URL hook
  - `translate.py` — `admin_translate` POST endpoint (MyMemory bulk translate)
- **External API preserved**: `from pages.admin import admin_translate, ProjectAdmin` still works via re-exports. `solarone/urls.py` and `pages/tests.py` unchanged.
- **`pages/seed_data.py` section headers** — added 4 inline `# ─────` comment blocks before each top-level key (`products` / `projects` / `siteconfig` / `productspagecards`) so Ctrl+G jumps to the right section. Total 3183 → 3192 lines (+9). Python dict literal still parses correctly; admin's `re.search(r'"slug": "..."')` still matches (comments are on their own lines, not inside the dict entries).
- **Validation**: `manage.py check` clean, `manage.py test` 73 tests OK (skipped=2), Playwright L2 ALL CHECKS PASSED across 6 viewports including 768×1024 iPad portrait. Admin registered 10 models on first import (verified by inspecting `admin.site._registry`).

## v1.4.6 - 2026-09-10

### Responsive fix (F8 mobile)

- **`product_detail.html:866-880`** — `.detail-specs` on `≤767px` reverted from `1fr` back to `repeat(2, 1fr)` (matches desktop layout). Original F8 decision was wrong: with the desktop font sizes (1.35 rem value, 0.8 rem label) the grid was forced to single column "to avoid cramming", but the right move was to scale the typography, not to collapse the grid. On a 390 px viewport, 4 specs (the `rt410-series` page) now lay out as 2×2 (each 171 px wide, value 17.6 px / label 11.2 px — clearly readable); 6 specs will lay out 2×3 (the documented "two columns, three rows" cap). Gap tightened from 16 px 32 px to 12 px 16 px on mobile.
- **L1 guard strengthened**: `ResponsivePhase2Tests.test_detail_specs_single_column_on_mobile` renamed to `test_detail_specs_two_columns_on_mobile` with **reverse assertion** — must contain `repeat(2, 1fr)` AND (after stripping that token) must NOT contain `grid-template-columns: 1fr`. Prevents the same regression from reappearing.
- **L2 verification**: Playwright + Edge headless on `rt410-series` at 390×844 confirms `grid-template-columns: 171px 171px`, items in 2 rows × 2 cols. Probe saved as `.workbuddy/tmp/probe_detail_specs_2col.py` (permanent regression template).

### Docs

- `docs/三屏响应式优化方案.md` → **v1.1.24** (§15.5 F8 correction record added; update-log entry + status-table row).
- `docs/优化建议清单.md` → **v1.1.5** (N-31 added and closed; priority table updated).

## v1.4.3 - 2026-09-10

### CI

- **GitHub Actions added**: `.github/workflows/ci.yml`. Triggers on `push` to `main` and on every `pull_request`. Runs Python 3.12 → `pip install -r requirements.txt` → `python manage.py test` (73 tests, ~3.3 s) → `pip audit -r requirements.txt` (advisory, `continue-on-error: true`). **Closes** `docs/优化建议清单.md` N-25 (the manual test gap that had already caused one "CSS changed, no test run, only real device caught it" regression during the responsive phase-1 work).
- `SECRET_KEY` is supplied via env (non-empty placeholder); `DEBUG=true` is set so the test runner uses the dev `ALLOWED_HOSTS` defaults — both are required because `solarone/settings.py` reads them from the environment.

### Tooling
- `scripts/dev_preview.py`: add a startup-time LAN troubleshooting block covering the three typical failure points (same-WiFi check, Windows firewall `netsh advfirewall firewall add rule …` template, and the "don't replace this script with bare `manage.py runserver`" warning). `runserver <port>` without a bind address only listens on `127.0.0.1`, which is the original cause of "phone can't reach the laptop preview".

## v1.4.2 - 2026-09-10

### Responsive phase 2 — three-screen consistency (F7-F11 + N-4/N-6/N-11/N-16)

- **F7 breakpoint unification**: all `@media (max-width:900px)` blocks (base.css + 6 templates) collapsed to **767px**; the `768–1024px` special-case removed; content grids moved `min-width:1024px` → **1200px**. Final 3-tier system: `≤767 / 768–1199 / ≥1200`. L2 sidebar assertions re-anchored to 767; **820×1180 added as a new viewport**.
- **F8 detail page single-column earlier**: `.detail-grid{1fr}` moved from `900px` to `@media (max-width:1024px)` in product_detail.html & product_series.html (fixes 901–1024 crowding, P1-6); `.detail-specs` collapses to 1 column ≤767px.
- **F9 products-banner adaptive**: hard `aspect-ratio:1920/442` replaced by `min-height:120px` (mobile `max(90px, 22vw)`), killing ultra-narrow clipping (P1-7).
- **F10 card titles wrap**: `.project-card-title` allows `white-space:normal` on mobile — long project names are no longer truncated to "…" (P1-8).
- **F11 reveal progressive enhancement**: `.reveal{opacity:0}` now gated behind `html.js` prefix everywhere (incl. reduced-motion override); `<head>` injects `document.documentElement.classList.add('js')` pre-render. No-JS visitors see all content (P1-9 root fix).
- **N-11 tablet hero svh**: `.hero` uses `min-height:100vh; min-height:100svh` pair — no address-bar jump on iPad/Android tablets.
- **N-6 cookie banner safe-area (re-judged approach)**: `padding-bottom:max(20px, calc(env(safe-area-inset-bottom, 0px) + 8px))` — max() fallback per N-27 lesson; `viewport-fit=cover` stays out.
- **N-4 desktop hero tiers (option B)**: new `hero-main-{1,2,3}-1280.webp` (downscaled from 1920 sources) + desktop `srcset` `1280w/1920w` with `sizes="(min-width:1200px) 1920px, 1280px"` aligned to the F7 tiers. Non-first-frame lazy deferred (absolute-positioned slides defeat `loading="lazy"`; recorded for later).
- **N-16 global scroll-hint style**: `.scroll-hint` definition centralized in base.css (product_detail keeps only its `display:block` reveal rule).
- **N-31 breakpoint leak (P1)**: 8 leftover `@media (max-width:768px)` blocks (base.css ×6, about.html, contact.html) collapsed to **767px**. They overlapped the tablet tier (`min-width:768px`) exactly at the 768px point — i.e. iPad portrait — so which rule won depended on source order. Missed by the original F7 guard because it only banned `900px`.

### Tests
- `pages/tests.py`: new `ResponsivePhase2Tests` — **12 regression guards** (svh pairing, banner env() fallback, title wrap, html.js gating + no-bare-rule, no 900px breakpoint in any source, 1024→1200 grid, detail-grid 1024 collapse, specs 1-col, banner aspect-ratio ban, hero 1280 srcset + files exist, scroll-hint global). Suite now **73 tests, OK (2 skipped Vercel-only)**.
- New `test_breakpoints_use_canonical_values`: a **white-list** guard replacing the black-list style — every `@media` width must be `max-width ∈ {767,1024,1199}` / `min-width ∈ {768,1200}`. Black-listing a single value (900px) is what allowed the 768px leak in the first place.
- Fixed 3 flawed assertions found during implementation (regex self-matching after prefix substitution; `[^}]*` unable to cross nested blocks; scroll-hint reveal rule misjudged as drift). No source defects involved.

### Tooling
- `scripts/e2e/run_checks.py`: viewport list extended with 820×1180 (tablet tier); sidebar toggle assertions follow the new 767px breakpoint. **L2: ALL CHECKS PASSED (6 viewports + reduced-motion)**.

### Assets
- `?v=17 → ?v=19` cache bump (18 for phase 2, 19 for the N-31 breakpoint fix); `collectstatic` refreshed (`staticfiles/css/base.css` now carries phase-2 rules).

## v1.4.1 - 2026-09-10

### Fixes (responsive phase 1.5 — iOS/Android real-device feedback)
- **N-22 RTL mobile drawer direction**: Arabic/Hebrew users had the drawer sliding from the right (against text flow). Now slides from the left via `[dir="rtl"] .mobile-panel:not(.open){transform:translateX(-100%)}`. `:not(.open)` avoids out-specifying `.mobile-panel.open`.
- **N-23 hero cropping relief**: `.hero-bg` compressed to 62% with `mask-image` linear-gradient fade so iPhone's visible width rose from 27.1% → 43.7%. Root fix (vertical hero + `<picture>`) is §13 / N-26.
- **N-24 carousel gated by reduced-motion**: Users with "Reduce Motion" on were stuck on the first hero slide. Removed the early-return; carousel now switches slides but uses `transition:none` under `prefers-reduced-motion`.
- **N-25 grid blowout resurgent**: Ten `1fr !important` in inline `<style>` blocks were silently overriding N-21's `minmax(0,1fr)`. Product detail `docScrollWidth` measured **921px at 390pt viewport** (only 42% of page visible). Root fix: `.sidebar-layout > *, .about-story-grid > *, .contact-grid > * { min-width: 0 }` on grid items themselves — survives any `!important` on the parent track. All 10 inline overrides rewritten to `minmax(0, 1fr) !important`. Result: 921 → 390, **0 overflow** across all 7 main pages × 3 viewports.
- **N-26 hero portrait + `<picture>`** (root fix for N-23): zero-upscale crops of the existing 1920×1080 hero → 810×1080 portrait webp (3 files, 73/118/98 KB) so the site ships vertical art immediately. Brand spec §13: 1170×1560 / 3:4 / subject in 12–55% vertical band.
- **N-27 mobile bottom buttons hidden by Android UI** (re-judged from v1.1.11): iOS Safari/Chrome auto-avoids the Home Indicator, but Android WebView (Baidu App, WeChat, some Chrome) `env(safe-area-inset-bottom)` returns 0 or is unsupported. **Reverted** the v1.1.11 `viewport-fit=cover` (it actually broke iOS's own avoidance) and now `.panel-actions { padding-bottom: max(80px, calc(env(safe-area-inset-bottom, 0px) + 48px)) }` — max() fallback guarantees coverage on any device.
- **N-28 drawer button vertical + 160px width**: per user feedback "按钮太大、横排占空间" → `.panel-actions { flex-direction: column }`, buttons `width:100%`; drawer 240px → **160px** (`max-width:56vw`).
- **N-29 iOS/Android font visual mismatch (real root cause)**: CSS variable `--ff-body` was being silently rendered as `&#x27;` (HTML entity) because `templates/base.html` `{{ config.font_family_body }}` ran through Django's HTML auto-escape and admin's stored value `'Inter'` got its apostrophes converted. Result: the entire site was falling back to system-ui → Times New Roman; iOS's auto-fallback to **SF Pro (latin) + PingFang SC (CJK)** has a baseline mismatch and looked "mismatched", while Android's fallback to Roboto + Noto Sans CJK is by design baseline-consistent. **Fix in 4 places**: (1) template uses `|safe`; (2) base.css font-stack includes explicit CJK fallback (`-apple-system, BlinkMacSystemFont, system-ui, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", "Source Han Sans CN", "Noto Sans CJK SC", Roboto, sans-serif`); (3) `SiteConfig.font_family_body/heading` defaults updated; (4) `migrations/0024_update_siteconfig_font_chinese_fallback.py` data-migrates existing singleton rows (only if their value matches an old-default pattern — preserves admin customizations).
- **N-30 drawer buttons left-aligned with menu links**: Lang wrapper `<div>` was carrying its own `padding: 0 14px` while the inner button carried another `padding: 6px 10px` — double-padding pushed "EN" 10px to the right. Wrapper padding cleared; inner button owns `padding:0 14px / height:36px / gap:8px / border-radius:8px / justify-content:flex-start`. L2 probe confirms 5 container elements share x=253, both button labels share x=294 — perfect left-alignment with menu links above.

### Tooling
- **`scripts/dev_preview.py`**: starts `manage.py runserver 0.0.0.0:PORT` with `ALLOWED_HOSTS` extended via env var (no settings.py edit). Prints LAN IP for phone testing — solves the "black box, only see results after deploy" pain.
- **`scripts/e2e/visual_review.py`**: Playwright (`channel="msedge"`, zero download) renders each URL at 390 / 768 / 1280, scans for elements whose content width exceeds the viewport (using the **configured** viewport constant, not `innerWidth` — mobile content-overflow inflates it), then writes a self-contained HTML report at `.workbuddy/preview/review_<ts>/index.html` with side-by-side shots + overflow element list.

### Tests
- `pages/tests.py` grew from 44 to **60 cases** (all OK, 2 skipped Vercel-only). New regression coverage:
  - `ResponsiveDeviceFixesTests` (N-22 RTL drawer, N-24 reduced-motion carousel — both defensive style-assertions).
  - `ResponsiveBlowoutAndHeroTests` (N-25: min-width:0 grid-item root + minmax(0,1fr) in all 10 inline overrides + N-26 portrait files exist + ratio + `picture{display:contents}`).
  - `ResponsiveIOSSafeAreaTests` (`viewport` meta must NOT contain `viewport-fit=cover`, panel-actions uses `max()` fallback ≥72px, drawer width 160px, buttons vertical, both buttons share `padding:0 14px` and `height:36px`, font-stack has `PingFang SC` + `Noto Sans CJK` + `-apple-system` + `Microsoft YaHei`, admin font injection uses `|safe`).

### Cleanup (this commit)
- Removed 8 stale `review_*/` directories from `.workbuddy/preview/` (~17 MB), keeping only the latest `review_20260910_122600/` (N-25 baseline) and `panel_buttons/` (N-28/30 drawer proof).
- Removed `.workbuddy/tmp/probe_root.py` and `probe_deep.py` (superseded by `probe_font.py` and `probe_align.py`).
- Removed root `_sf.txt`, `_tmp_git.txt` (UTF-16 debug leftovers from earlier diagnosis), and `/tmp/devsrv.log`.
- Kept `.workbuddy/tmp/`'s four probe templates (`probe_font`, `probe_align`, `probe_button_width`, `probe_panel_buttons`) — these are the documented debugging tools for similar future regressions.
- Verified dead-code still gone: `pages/views_old.py` (82 KB) and `pages/storage.py` (4 KB) — both confirmed absent.
- `pages/seed_data.py` (3183 lines) is **kept** — referenced by `pages/admin.py` for Vercel deployment sync.

### Notes
- CSS `?v=10 → ?v=17` across this phase (must bump on every CSS edit).
- Documentation: `docs/三屏响应式优化方案.md` v1.1.10 → **v1.1.16** (added §13 hero portrait spec, §14 local review workflow, N-22..N-30 issue records).

---

## v1.4.0 - 2026-09-09

### Features
- **Mobile navigation rebuilt (single source of truth)**: New `templates/includes/nav_items.html` holds the nav list once; both the desktop `.nav-links` bar and the mobile drawer include it, so the two can no longer drift. CTA, theme toggle and language switch moved into `.nav-actions` (hidden below 768px) and are re-exposed inside the drawer via `.panel-actions` — mobile loses no functionality.
- **Collapsible sidebars**: Products / projects / news / detail pages use a pure-CSS checkbox-hack toggle. Default collapsed at ≤900px (content first), always expanded on desktop. HTML ships expanded so no-JS users never lose category navigation.
- **L2 Playwright regression harness**: `scripts/e2e/run_checks.py` runs three viewports (320/390/1440) through Edge (`channel="msedge"`, no browser download) asserting no horizontal overflow, hamburger visibility, drawer contents, sidebar toggle, and iOS defensive patterns.

### Fixes
- **P0-1 hamburger invisible on iPhone (390px)**: Below 768px only logo + hamburger remain, so overflow is structurally impossible.
- **P0-3 sidebar pushing content down**: Sidebars now default to collapsed on mobile.
- **N-18 project card image clipped 12px**: `.project-card-img` was `width:100%` plus `margin:12px`, overflowing the card and being silently cut by `overflow:hidden`. Fixed to `width:auto` below 768px.
- **N-21 grid blowout**: `.sidebar-layout` single-column track used `1fr` (= `minmax(auto,1fr)`), letting min-content push the page to 364px at a 320px viewport. Now `minmax(0, 1fr)`.
- **N-1 iOS input zoom**: Visible form inputs now `font-size:16px`.
- **N-5** Google Fonts loaded async with `<noscript>` fallback.
- **N-8** `prefers-reduced-motion` disables smooth scrolling (CSS + JS).
- **N-9** Touch targets ≥44px via pseudo-element hit areas.
- **N-10** `overflow-wrap:anywhere` on body.
- **N-19 / N-20** L2 harness itself: overflow assertions now compare against the configured viewport width (mobile `innerWidth` gets inflated by content, making the old check always green), and hidden inputs are excluded from the font-size check.

### Cleanup
- Removed `pages/views_old.py` (82KB, dead since views was split into a package) and `pages/storage.py` (`OverwriteStorage` never referenced). Both backed up under `.workbuddy/archive/`.
- Removed 62 root `_*.py` / `_*.txt` / `_*.log` debug leftovers, 4 `git_*` output files, `screenshots/` (16MB), `staticfiles/` (66MB, regenerated by `build.sh`), `solarone-website-preview/` (5.1MB), and empty `tests/` `config/` `images/` directories. ~87MB reclaimed.
- `.workbuddy/` added to `.gitignore` (local agent workspace, not product code).

### Notes
- Static version bump `?v=10`.
- L1: 42 tests OK (skipped=2). L2: ALL CHECKS PASSED.
- Docs: `docs/三屏响应式优化方案.md` v1.1.8 — adds §2.5 N-18~N-21, §6.8.5 L3 real-device checklist, §12 progress audit.
- **Only L3 (real-device pass, §6.8.5) remains before phase 1 is fully signed off.**
- Version bump to `v1.4.0`.

## v1.3.0 - 2026-08-21

### Features
- **Certification images on all product pages**: Every product detail page now shows certification badges (UL, DLC, TÜV GS, CE, IP66). Added `cert_image` field to Product model — admins can upload a custom cert image per product, or leave it blank to use the default cert graphic.
- **Flexible project detail layout**: Project pages with comparison (secondary) images render them in a right column alongside the description; projects without compare images span the description full-width. Controlled via `has_compare_images` in `_enrich_project`.
- **Paragraph-aware text rendering**: Added `nl2para` template filter that converts newlines into proper HTML paragraphs and `<br>` line breaks while preserving inline HTML tags (e.g. `<strong>`). Applied to project description, project results, and product description.

### Fixes
- **Project image sync reliability**: Fixed admin image sync to strip Django hash suffixes so filenames are stable; fixed `invalidate_enrichment_cache()` to also clear directory-listing and static-file-set caches so newly uploaded images appear immediately.
- **Stale file protection**: Admin sync no longer deletes template-hardcoded special images (e.g. old-hid-lighting.webp, new-led-lighting.webp) during stale-file cleanup.
- **Cover image fallback**: Fixed `_find_project_cover_path` to return empty string instead of a nonexistent `images/processed/` path when no cover is found, preventing broken-image placeholders.
- **About page crash**: Fixed `TemplateSyntaxError` on `/about/` caused by a stray `/` in a `{% trans %}` tag; moved `<strong>` tags outside translation strings for all cookie list items.

### Cleanup
- Removed 25+ temporary/backup scripts and unused files from project root (`fix_*.py`, `seed_data_backup.*`, `rebuild_db_*.bat`, etc.).
- Removed 24 duplicate hash-suffixed image files from `static/images/products/`.
- Deduplicated `.project-compare` CSS rules in `project_detail.html`.

### Notes
- Version bump to `v1.3.0`.
- Django migration `0018_add_product_cert_image` added for the new `cert_image` field.

## v1.2.1 - 2026-08-13

- Fix: force-refresh static compare images (old HID / new LED) and ensure served files match uploaded originals.
- Feature: add compare images to project detail page with vertical layout and captions (old hid lighting above, new led lighting below).
- Style: centered, bold image captions; constrained image max-height; adjusted layout to keep `Project Results` full-width.
- Admin: improved translations textarea layout and widths in Django admin (`TranslationsWidget` + `admin_overrides.css`).
- UX: moved `Download PDF` button to page bottom and adjusted alignment.
- Ops: updated staticfiles via `collectstatic` and removed stale cached copies to ensure browser sees updated assets.

### Notes
- Version bump to `v1.2.1`.
