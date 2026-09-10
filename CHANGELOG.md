# Changelog

All notable changes to this project will be documented in this file.

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
