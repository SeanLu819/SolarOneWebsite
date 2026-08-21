# Changelog

All notable changes to this project will be documented in this file.

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
