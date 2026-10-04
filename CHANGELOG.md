# Changelog

All notable changes to this project will be documented in this file.

## v1.10.4 - 2026-10-04

## Put news figures in the paragraph they illustrate, and one card size

Three changes, all on the news pages.

**Figures now sit inside the article body.** Until now every gallery photo
rendered in one bento grid above the text, so the market article showed all five
images before its first sentence. Editors asked for each figure to sit with the
paragraph it supports.

- New `pages/views/news_body.py` splits the body into blocks and consumes
  `{{figure:identifier}}` markers that live in the copy itself. The template
  only loops; it never assembles arrays (project rule).
- The first figure is `loading="eager"`, the rest lazy.
- **A broken figure can only ever cost one photo.** An unknown or duplicated
  marker drops the marker and keeps the paragraph — a typo in the copy must not
  swallow a paragraph of body text.
- Images no marker references fall back to `unplaced_images` and still render
  in the old top grid, so a forgotten marker degrades instead of silently
  losing a photo.

**Three original charts for the market article.** The three screenshots that
came with the source report carry the publisher's logo, a page-number marker and
a domain watermark; reusing them would put a third party's trademark on a
commercial page. The **numbers** are facts and are free to use, so the charts
are drawn from the figures the article itself states — nothing appears in a
chart that does not appear in the copy. Where a curve is interpolated it is
labelled as such, and no "rest of world" wedge is drawn because no such figure
is published.

**Every news card is the same size.** The latest article used to be a featured
card spanning two columns with a horizontal layout — roughly twice the area of
its neighbours. It keeps its "Featured" pill but no longer changes geometry;
`grid-auto-rows: 1fr` plus `height: 100%` give all cards one height and
`margin-top: auto` aligns the "Read article" footers.

### Two real bugs found while verifying

- **News images 404'd locally** (`pages/views/data_loaders.py`). The DB path
  resolved gallery fields through `field.url`, i.e. `MEDIA_URL` (`/media/…`),
  while every news photo lives in `static/images/…`. Products and projects
  were unaffected because they resolve via `_product_image_url` /
  `_project_image_url`; only news used the storage URL. Now resolved against
  `static/` first, with the storage URL kept as the fallback for genuine admin
  uploads that exist only under `MEDIA_ROOT`.
- **The news media sync could delete committed photos** (`pages/models.py`).
  `_sync_news_media_to_static` pruned `static/images/news/<slug>/` on every
  save, and any save that saw a short reference list — a half-imported
  article, a test creating rows before the gallery was attached — deleted
  committed files, 404'ing them on the next page load. The prune pass now runs
  only when the sync actually copied something; `static/` is a tracked source of
  truth here, not a build artifact.

Guard: new `pages/tests_news_figures.py` (26 tests). All 10 mutations used to
verify it turn red.

## v1.10.3 - 2026-10-04

## Cache HTML at the edge so returning visitors stop re-running Django

Measured on production before this change: every HTML response came back
`Cache-Control: public, max-age=0, must-revalidate` with `Age: 0` and
`X-Vercel-Cache: MISS`. That is Vercel's default for a Serverless Function
response, and it means **every page view executed Django** — a visitor
reloading the page they were already reading paid full TTFB again.

`pages/edge_cache.py` attaches `Vercel-CDN-Cache-Control:
public, s-maxage=300, stale-while-revalidate=86400` to public HTML. The
edge-only header name is deliberate: Vercel's proxy consumes it and never
forwards it, so the browser keeps revalidating (a deploy is visible
immediately, content never goes stale for a visitor) while the edge stops
invoking Django.

### Why this could not go in vercel.json

The `headers` block is the only other place that can set these headers, and two
documented facts rule it out:

* `source` "matches each incoming pathname (**excluding querystring**)", so no
  rule can distinguish `/news/` from `/news/?category=Case+Studies` — and those
  are genuinely different documents (confirmed by md5: the bodies differ).
* `missing` requires one concrete `key` with no wildcard, so "has no query
  string at all" is not expressible.

A catch-all rule would have cached one category's filtered news page under
`/news/` and served it to every visitor.

### What is deliberately not cached

* `/contact/` — it renders `{% csrf_token %}`. Replaying a cached copy hands
  the next visitor a token bound to someone else's cookie and their form POST
  fails with 403.
* `/news/feed.xml` — startswith the cacheable `/news/` prefix, so it needed an
  **exact-match** exclusion list rather than a prefix one. Caching it would
  hold a newly published article back from every RSS subscriber.
* `/admin/`, `/__diag__/`, anything with a query string, anything carrying
  `Set-Cookie`, and every non-200 status (a cached 301 would freeze the
  apex→www target into the edge forever).
* `/static/` — already served with a one-year `immutable` rule from
  vercel.json.

Language needs no exclusion: `i18n_patterns` puts it in the path, and
production confirms `Accept-Language` does not change the response.

### On the test that mattered

The first implementation had 15 direct-call tests green while **every real
request carried no header at all**. `IS_VERCEL` is read from the `VERCEL` env
var at settings-import time and Django freezes the middleware chain then, so
`override_settings` cannot install a middleware the non-Vercel branch skipped —
the feature was silently inert.

`tests_edge_cache.EdgeCacheOnVercelSubprocessTests` re-imports the settings
module in a child process with `VERCEL=1` and asserts against live responses.
That test is what caught the `/news/feed.xml` gap above.

The four policy lists were mutation-probed: dropping the `/contact/` exclusion,
dropping the query-string check, switching to plain `Cache-Control`, and
emptying the exact-match list each turn the suite red. All files were restored
byte-identically afterwards.

## v1.10.2 - 2026-10-04

## First industry-reporting article, and a `Industry Insights` news category

Added `global-led-lighting-market-2034` — an independent summary of a
third-party LED-lighting market report (Fortune Business Insights), rewritten
rather than republished: five short body paragraphs plus an explicit source
statement naming the original publisher. Its figures (2025 USD 109.11 bn →
2034 USD 336.90 bn, 13.40% CAGR, Asia-Pacific 54.40% share) come from that
report; the page states it is a summary and links readers to the source, which
is the only honest option when the underlying text is someone else's.

* `pages/models.py` — new `NEWS_CATEGORIES` choice `Industry Insights`.
  Market reporting is neither a company nor a product announcement, so
  lumping it into `Company News` would have mislabelled the entry in the
  list-page chips and the article badge. Choices-only: no schema effect, and
  `build.sh` only runs `migrate` when a real external DB is configured.
* `pages/views/i18n.py` — its label in fr/es/de/ru/ar. Without this the chip
  falls back to English on five of six language versions.
* `static/images/news/global-led-lighting-market-2034/` — 3 new 1280×720 WebP
  illustrations (cover + 2 gallery photos).

Three guards had been written against the *single* article the site carried,
so publishing a second one turned them red. All three now derive their
expectations from the seed instead of hardcoding a count, a date or a
keyword — the actual lesson being that such a guard tests the fixture, not the
behaviour:

* `pages/tests_qa_bgroup.py` — the RSS `pubDate` check compared against a
  literal `(2026, 9, 25)`; it now compares against the seed's own newest
  `published_at`.
* `pages/tests.py` — the list-page cover count was `assertEqual(1, ...)`; it is
  now "one cover per published article".
* `pages/tests_product_seo_description_budget.py` — the keyword assertion
  demanded `FL6M-480W` and the literal string `Tianjin Binhai Airport` (which
  never matched the real title `Tianjin Binhai International Airport`) on
  *every* article; it is now scoped to the one slug it was written about.

`pages/views/views_other.py` — `news_feed()` now sorts newest-first itself.
It previously relied on the seed file's physical order, which only happened to
be correct because `seed_sync` writes it in `Meta.ordering` order; RSS readers
present the first item as the newest, so that is now a property of the
function rather than of the file layout (`_get_news_from_json` got the same
treatment).

Both reworked guards were mutation-probed: reversing the feed sort and
inflating the expected cover count each turn the suite red, and both files
were restored byte-identically afterwards.

## v1.10.1 - 2026-10-04

## Stop downloading the two hidden hero slides on every homepage view

`.hero-slide` is `position:absolute; inset:0` — permanently inside the viewport —
so the `loading="lazy"` attribute that slides 2 and 3 carried had **no effect**.
Chrome fetched all three full-bleed images on every homepage view. Measured
weight of the two invisible slides: 467 KB, i.e. 86% of the 541.9 KB first-screen
image budget (measurements in `docs/home-image-size-analysis.md`).

* `templates/home.html` — slides 2 and 3 now ship `data-src` / `data-srcset`,
  the `<picture><source>` portrait variant included: leaving that one eager
  would still pull the mobile crop on load.
* `templates/base.html` — the carousel fills the deferred attributes through
  `ensureLoaded()`, always `<source>` before `<img src>` (otherwise the mobile
  3:4 crop is skipped), and warms the next frame inside `requestIdleCallback`
  so the 1.2s cross-fade never plays over an empty `<img>`.
* `static/css/base.css` — `.hero-slide:not(.active) { visibility: hidden }` so
  a not-yet-filled frame cannot flash its alt text.

Slide 1 keeps a real `src` plus `fetchpriority="high"` (it is the LCP image),
and with JavaScript disabled the homepage looks exactly as it did before.
First-screen image weight drops from 541.9 KB to 74.9 KB.

Guarded by `pages/tests_static_assets.py::HeroDeferredSlideLoadingTests` (5
cases). Each case was mutation-probed: restoring a bare `src`, dropping
`setAttribute('src')`, or removing the `:not(.active)` rule turns the suite red.
The runtime behaviour was additionally verified in jsdom (13 assertions, 4
scenarios: no-JS, `setTimeout` fallback, `requestIdleCallback`, exact URLs).

## v1.10.0 - 2026-10-04

## Retire the three keyword landing pages; replace them with real project collections

`/products/sports-lighting/`, `/products/football-stadium-lights/` and
`/products/tennis-court-lights/` were built *for* keywords rather than around
content. They are gone, and they 301:

| retired | → |
|---|---|
| `/products/sports-lighting/` | `/products/` |
| `/products/football-stadium-lights/` | `/projects/football/` |
| `/products/tennis-court-lights/` | `/projects/tennis/` |

The obvious replacement — 301 straight to
`/projects/?venue=OUTDOOR&sport=FOOTBALL_FIELD` — was measured and rejected for
three independent reasons:

1. **The enum splits one sport across two values.** Football is
   `FOOTBALL_FIELD` (3) + `SOCCER_FIELD` (2); tennis is `TENNIS_COURTS` (3,
   all OUTDOOR) + `TENNIS` (2, **both INDOOR**). A single-value filter drops
   the only genuine stadium in the portfolio (`yuanshen-sports-centre-stadium`)
   and both indoor tennis courts — while the retired tennis page's copy
   promised indoor coverage.
2. **`request.path` carries no query string**, so every filtered URL renders
   `<link rel="canonical" href="…/projects/">`. Verified live for four
   filtered URLs: Google collapses them all into `/projects/`, so the keyword
   would never own a distinct indexable URL. The filter is a UI affordance,
   not an SEO surface.
3. **The redirect table cannot express a query string at all** — its values are
   bare URL names for `reverse()` — so the redirect was not implementable
   without first extending the mechanism.

`/projects/football/` and `/projects/tennis/` fix all three: real paths,
self-referencing canonical, and a merged multi-value filter
(`data_loaders._sport_filter_values`, DB *and* seed paths) that lists exactly
the five real projects per sport. Because they are real paths they also inherit
hreflang and sitemap coverage for free. Static routes are registered **before**
`projects/<slug:slug>/` — the slug converter matches `football` too, so the
wrong order would hand the URL to `project_detail()` and 404.

Removed with them: three templates, three views and the shared
`_sports_landing()` helper, their sitemap entries, `llm.txt` bullets, the
`visual_review.py` paths, `project_detail.html`'s related-solutions links
(now pointing at the collections), and two test modules (32 cases) that
asserted the retired pages. `docs/keyword-inventory.csv` retargets 7 keyword
rows.

Guarded by `pages/tests_project_collections.py` (12 cases). Three mutation
probes confirm the guards bite: narrowing either collection to a single enum
value turns 2 cases red, emptying the redirect table turns 2 red, and dropping
the sitemap entries turns 1 red. Restored byte-identical (md5 verified).

Titles/intros/descriptions for both collections go through `_t()`, so six new
`_SIDEBAR_I18N` entries cover fr/es/de/ru/ar — **these translations are new and
worth a native review**.

## v1.9.10 - 2026-10-04

## Image de-duplication — fix the root cause, then remove the 30 copies

A full re-audit found **no broken images**: every one of the 269 image URLs the
production (seed) path resolves lands on a real file under `static/`, all 248 DB
image fields resolve, zero orphans, zero naming problems. What remained was
2.02 MB of byte-identical duplicate files in 21 groups.

**The root cause was the admin upload path, not the files.** Every save ran
`shutil.copy2` into a per-slug directory unconditionally
(`pages/admin/product.py`, four call sites), so the same badge or beam-angle
chart uploaded for N products became N byte-identical copies — and deleting them
by hand only works until the next upload. `_static_copy_deduped()` now hashes
the upload first: if identical content already exists anywhere under
`static/images/`, the existing path is recorded and nothing is written. The
hash index is built once per process and trusts only `static/` — never the
stale `staticfiles/` snapshot. Guarded by `pages/tests_admin_image_dedupe.py`
(4 cases, including one that fails if the index ever reaches outside the true
source); mutation probe confirmed two of them go red when dedupe is disabled.

**Then the existing 30 copies were removed** (2.02 MB, 318 → 288 files,
36.31 → 34.29 MB). Because a deletion is only safe if nothing still points at
the file, references were resolved with the **real resolver** rather than by
filename guesswork: 19 seed references were repointed (CRLF preserved) and 18 DB
rows updated with `.update()` so `post_save` never fired. Before/after snapshots
of all 275 image slots differ in exactly 4 places — all four are the intended
repoint; no slot silently changed because of directory enumeration.

Two false starts are worth recording:

* A reference scan that only covered `products` missed `productspagecards`,
  which store their image as a plain string — `products_page/VSP9M-01.webp`
  was flagged safe to delete while a card still pointed at it.
* Matching DB rows by basename reported one row eight times, making eight
  distinct files look referenced. Resolving each row through
  `_product_image_url` is the only reliable way to know what it points at.

`static/images/products/ordering/` became empty and was removed — the existing
"no empty product image directory" guard caught this, which is the guard doing
its job.

**Verification**: `519 tests / 32 failures`, unchanged from the `515 / 32`
baseline plus the 4 new cases; duplicate-content groups 0; URL resolution
failures 0; DB resolution failures 0.

---

## v1.9.9 - 2026-10-03

## Production-parity fixes — cert badge paths, build-artifact fidelity, gallery alt

Three defects that all share one root cause: **the local render path and the
production (seed) path disagree**, and the disagreement is invisible locally.

### The seed build artifact was silently rewriting English copy

`pages/seed_sync.py` generated `pages/seed_data.py` by running three naive
`str.replace()` calls over `json.dumps()` output — `true`→`True`,
`false`→`False`, `null`→`None`. Because the replacement was **not
string-aware**, any occurrence inside copy was rewritten too. This shipped:
`projects[13].description` renders as `a True "shadowless" effect` on
production instead of `a true "shadowless" effect`.

Replaced with `_json_to_python_literals()`, a single-pass scanner that tracks
whether the cursor is inside a JSON string and only rewrites bare literals at
word boundaries (`json.dumps` never emits `True`, so a bare `true` outside a
string is always a boolean). Guarded by
`SeedPythonArtifactFidelityTests` (3 cases) — field-by-field equality between
the JSON and the generated module, plus two direct probes of the string and
word-boundary behaviour.

### 21 products pointed their certification badge at a deleted directory

The DB (`pages_product.cert_image`) still held `products/certs/<name>` for 21
rows after those files were de-duplicated in v1.9.8. The resolver normalises to
`static/images/products/certs/…`, which no longer exists, so the URL fell back
to `/media/` — **and `/media/` is excluded from the Vercel bundle**, so every
one of those badges was a live 404 that local browsing cannot show.

Fixed with `.update()` (never `post_save`, so no seed rewrite): 18 rows cleared
to `''` (they now render the shared `DEFAULT_CERT_IMAGE`, which exists) and 3
RGBW rows repointed to `products/rgb-rgbw/<file>`. Media-only resolution went
from **19 fields to 0**. Guarded by `CertDatabasePathTests` (5 cases), which
reads the real `db.sqlite3` read-only — the test database is empty in this
project, so any ORM-backed assertion here would pass vacuously.

### Project gallery alt text lost the real project name (local only)

`pages/views/enrich.py` builds gallery alt text as
`"{title} — {location} — view N"`, but the DB branch wraps it in
`img.alt_text or _gallery_alt(...)` while the **seed branch — the one Vercel
runs — never reads `alt_text` at all**. Three projects (16 images) carried an
override, and the override was slug-derived:

    prod : 'Bohemia Manor High School — United States — view 1'   ✅
    local: 'Football Field LED Retrofit — view 1'                 ❌

so the local page dropped both the entity name and the country. The overrides
were **cleared**, not rewritten — writing new copy would recreate the same
local/production drift on the next deploy. Guarded by
`pages/tests_project_gallery_alt.py` (3 cases): the seed-path alt must carry
the real title and location, and no `ProjectImage.alt_text` may be non-empty
until `seed_sync` exports it.

⚠️ Writing that guard produced a false positive worth recording: a blacklist
keyed on `slug.replace('-', ' ').title()` flagged **52 legitimate alt strings**,
because 11 of 22 project titles are *already* the humanised slug
(`nanshan-ski-village` → "Nanshan Ski Village"), and because `led` title-cases
to "Led" while the real bad string said "LED" — so the blacklist both
over-reported and missed the actual defect. The guard now asserts a positive
contract (subject segment == title, location present) instead.

**Verification**: full suite `515 tests / 32 failures`, unchanged from the
`512 / 32` baseline (the 3 new cases pass); mutation probes confirmed each new
guard fails when its invariant is broken.

---

## v1.9.8 - 2026-10-03

## Image audit — cert badge de-duplication, dead fallback fixed, full-site report

A full-site image audit (337 files / 38.48 MB) produced three tools and two
code fixes.

**The certification badge fallback pointed at a file that does not exist.**
`pages/views/enrich.py` fell back to
`images/products/m-series-flood-light-certifications.webp` whenever a product had
no `cert_image`. That file is not on disk — verified `404` live on 2026-10-03 —
so every product with an empty `cert_image` silently rendered **no certification
badge at all**. The constant is now `DEFAULT_CERT_IMAGE`, pointing at
`images/products/m-series/certifications-ul-dlc-gs-ce-ip66.webp`, which exists.
The dead literal is additionally banned from executable code by
`test_no_dead_cert_fallback_literal_remains_in_code`.

**18 byte-identical copies of the same badge.** The UL/DLC/GS/CE/IP66 badge was
stored separately in 18 product directories (19 files including the RGBW
interface badge). All 18 products now reference one shared file, and the 19
redundant copies were removed (782 KB freed, backed up under
`.workbuddy/backup/cert_dedupe_20261003/`). Three sources were updated in the
required order — `seed_data.json` (CRLF preserved), the DB via `.update()` so
`post_save` never fired, then `python -m pages.seed_sync --json` to regenerate
`pages/seed_data.py`. The root cause is the admin upload path
(`pages/admin/product.py:283`), which copies each upload into the per-slug
directory; Django's 8-char hash suffix meant every re-upload minted another
copy — 19 identical files under `media/products/certs/`.

**Pre-cropping to 16:9 was investigated and rejected.** It looked safe because
the project carousel uses a fixed `aspect-ratio: 16/9` with `object-fit: cover`,
but the same files are also rendered by `.project-card-img`
(`height: 180px` with cover, ≈6.8:1) on the projects list, so cropping to either
ratio changes what the other slot shows. Re-encoding at identical pixel size
(`method=6`, quality 86→80, PSNR ≥ 40 dB gate) saved **0 KB across 110 project
images** — the existing encodes are already efficient. The savings must come from
exporting new source material at the right ratio, not from re-processing.

**Naming is already compliant — no renames needed.** The first report flagged
137 images; every one was a false positive from two bad rules (filename vs.
directory semantics, and "filename duplicates the directory name"). Both were
removed. All 337 images carry descriptive names such as
`llq-roadway-1080p-01.webp` and `glare-shield-rt410-bar-03.webp`; zero contain
CJK characters, spaces, uppercase or hash suffixes.

New read-only tools: `scripts/audit_images.py` (per-file size/dimensions/format/
md5 plus duplicate grouping and seed references),
`scripts/audit_img_slots.py` (maps every `<img>` slot to its CSS box),
`scripts/gen_image_issue_report.py` (writes
`.workbuddy/preview/image_issue_report.html` with per-image issues and an
export-spec table). Guards: `pages/tests_cert_images.py` (7 cases), all
mutation-probed.

## A full-site sweep of all 58 sitemap URLs in six locales found two places where
the SEO budget was still not enforced. Both are closed here, together with the
guards that keep them closed.

**Non-English product descriptions were never clamped.** ``Product.seo_description``
returns the translated ``description`` for every locale except English, and in
the seed most products have no translated description at all, so those branches
fell back to the English original and shipped 168-387 characters into a 160-char
tag. ``/fr/products/fl6m/`` served 343 characters while ``/products/fl6m/``
served the 156-char formula. The project side never had this gap —
``_DictProject.seo_description`` clamps in every locale.

- New ``pages.utils.fit_description`` clamps on a sentence boundary, reusing the
  policy ``_fit_project_description`` already gives projects.
- The English formula is deliberately *not* reused for non-English: it is English
  prose, and putting it on a /fr/ page would contradict the hreflang that same
  page emits. Clamping keeps the locale's own copy.
- Applied in both mirrored paths — ``Product.seo_description`` (DB) and
  ``_DictProduct.seo_description`` (seed, what ``IS_VERCEL`` runs) — plus the
  test mirror in ``tests_seo_keywords.py``. Verified: 24 products x 6 locales =
  144 strings, all within budget, English unchanged.
- **Two mutation probes caught real blind spots in the new guards**: the first
  version only exercised the seed path, so deleting the clamp from
  ``Product.seo_description`` stayed green. The rendered pages in the test
  environment come from the seed mirror, so a DB-path test had to be added
  explicitly, along with a direct model-vs-seed equality check.

**Two titles exceeded the 60-character budget.** ``/products/`` carried a 64-char
literal, and ``news_detail.html`` appends ' — SolarOne News' to the stored
article title, which put that page at 80. Both now fit (54 and 57). The news
title is data, not copy — it lives in ``seed_data.json`` and its build artifact
``pages/seed_data.py``, both of which were edited together. The products title
was rekeyed in all five locales with the translations carried over.

- Guards: 18 cases in ``pages/tests_product_seo_description_budget.py``, covering
  the clamp policy, both code paths, the rendered /fr/ pages, every
  ``{% blocktrans %}`` title, and both seed mirrors with a drift check.
- The i18n coverage guard in ``pages/tests.py`` earned its keep immediately: it
  failed on the og:title block that still held the 64-char string because the
  ``<title>`` beside it had already been shortened. A ``title`/`og_title``
  pairing test now locks that directly.

Full suite: 493 tests, 0 failures, 0 errors.

## v1.9.7 - 2026-10-03

Performance and correctness pass driven by a full-site audit. The headline
finding is not an image size: **no static asset on the production site was
cacheable by the browser**, which costs every visitor a conditional
revalidation on all 30-odd assets per page.

- Static caching was configured in the wrong layer. `build.sh` mirrors the
  collectstatic output into `public/static/`, and Vercel serves those bytes
  straight from its edge CDN, so they never pass through the Django process.
  `WHITENOISE_MAX_AGE` was therefore dead config, and the code comments
  claiming hashed files get `immutable, max-age=31536000` were simply wrong. A
  live probe of the already-hashed `/static/css/base.<hash>.css` returned
  `Cache-Control: public, max-age=0, must-revalidate`. Fixed by adding the
  `headers` block to `vercel.json`; the misleading comments in `settings.py`
  and `build.sh` are corrected in place so this does not get "re-fixed" the
  wrong way again. A catch-all `source: /(.*)` rule is deliberately NOT used
  because it can shadow the `/static/` rule and silently undo the year-long
  cache. HTML keeps `must-revalidate` from Django, which is correct for a
  six-language site.
- Unknown project slugs were still soft 404s. `project_detail()` fell through
  to `render()` with no project in context, producing HTTP 200 with a
  "Project Not Found" title and a self-referencing canonical - an invitation
  for Google to index any fabricated `/projects/<garbage>/` URL. The product
  side was already fixed in v1.8.2; this closes the gap. The redirect table is
  still consulted first, so renamed pages keep their 301.
- Re-encoded four VSP9M product renders that were stored at roughly 3x the
  necessary size (859 KB -> 128 KB, 401 KB -> 65 KB, 2.04 MB -> 0.32 MB
  total). Filenames, pixel dimensions and the alpha channel are unchanged.
- Removed 9 Space Grotesk faces (140 KB). They had no render-stack reference
  since v1.6.3, so they were dead weight in every build. Verified against
  `base.css`, the inline critical CSS, and `seed_data.json` first.
- Tooling: `scripts/optimize_images.py` and `scripts/remove_font_family.py`.
  The optimizer refuses any file whose PSNR falls below 40 dB, which correctly
  left 26 of 30 candidates untouched - most were already better encoded than
  any re-encode we could produce.

Notable non-changes, all measured rather than assumed: the remaining 43
@font-face entries look like duplicates on disk (the four Inter latin weights
share an md5) but each is a distinct weight gated by `unicode-range`, so the
browser fetches only what a page's glyphs need - deleting them would drop real
weights and break Cyrillic coverage on `/ru/`.


## v1.9.6 - 2026-10-03

v1.9.2 clamped the *project* descriptions, but the hand-written site-level
ones were never in scope. A production sweep of all 58 sitemap URLs found five
pages shipping over the 160-character budget — `/` 180, `/products/` 187,
`/about/` 179, `/products/football-stadium-lights/` 171 and
`/products/tennis-court-lighting/` 187 — so Google was cutting every one of
them mid-sentence.

The fix is five reworded English strings, now 148-157 characters. Each drop
was filler, not fact: "at every level of play", "field-proven reliability",
"worldwide", "solutions". Every commercial term survived, and
`test_each_reworded_string_keeps_its_head_term` locks that.

- Root cause was the source strings, not a missing clamp. These five pages are
  static templates, so a `|truncatechars` filter would have cut mid-thought
  instead of rewriting the sentence.
- Changing an English literal inside `{% blocktrans %}` orphans its
  translations, so all five msgids were rekeyed in fr/es/de/ru/ar with
  `msgstr` carried over untouched. Verified by dumping every entry from all
  five `.mo` files before and after: only the five keys changed name, every
  other value was byte-identical, none lost.
- Non-English copy is intentionally left whole. Google truncates on rendered
  width, not character count, and a 190-character Russian description occupies
  less space than a 160-character English one; clipping translations to 160
  would delete facts. The Arabic set already lands at 126-143.
- Guards: 10 cases in `pages/tests_meta_description_budget.py` — every
  template description literal within budget, meta and og copy identical per
  template, no CJK marker, English render within budget and equal to source,
  and all five locales resolving each string to a translation. Four mutation
  probes confirmed the guards fail when the literals go long, the meta/og pair
  diverges, the rendered copy drifts, or an msgid is broken.
- Measuring note: the raw HTML is up to 5 characters per apostrophe longer
  than what Google shows (`&#x27;`), so an earlier sweep of the project pages
  reported five false positives. Budget assertions unescape first.

## v1.9.5 - 2026-10-02

The site had no redirect mechanism at all: zero entries in `pages/urls.py`,
no redirect table anywhere. Renaming any slug would have 404'd, which is what
blocked B3 (keyword renames for five project slugs). This builds the
mechanism; no redirect is registered yet, because every entry is a decision
that content actually moved.

- New `pages/redirects.py` is the single source of truth, and deliberately
  not the DB or `seed_data.json`: production runs stateless off the seed, so
  a DB table would be invisible there, and a seed table would have to pay the
  DB/seed double-write every content field already pays.
- Two slug tables (project/product) are consulted inside the detail views,
  and only when the requested slug fails to resolve — so registering a
  redirect can never shadow a page that still exists.
- A third table retires whole routes. Its value is a URL name, not a path
  string, so the target is reversed and keeps the visitor's language.
  (`RedirectView.as_view(kwargs=...)` raises TypeError — `kwargs` is not a
  class attribute — which is why the target stays a bare `pattern_name`.)
- Synthesised routes go first in `urlpatterns`; a catch-all like
  `products/<slug:slug>/` would otherwise swallow the legacy path.
- Guards: 21 cases in `pages/tests_redirects.py`, covering table validity
  (self-reference, chains, dangling targets, relative paths), 301 not 302,
  language preservation, and that live slugs are never redirected. Two
  mutation probes confirmed the guards fail when the lookups are disabled.
- Full suite: 452 tests, 0 failures, 0 errors.

## v1.9.4 - 2026-10-02

The suite is green: `manage.py test` now reports **431 tests, 0 failures, 0
errors**. Two `ProductAdminSidebarTreeTests` cases had errored on every run
since they were written, which trained everyone to read "2 errors" as the
baseline and stopped the suite from being a real gate.

- Root cause was in the tests, not the admin: both cases build a
  `SidebarOrderedChangeList` with `__new__` to exercise `get_ordering` in
  isolation, but `ChangeList.__init__` is what sets `lookup_opts`, and Django's
  `_get_deterministic_ordering()` introspects it — so the calls died with
  AttributeError before reaching the sidebar logic they were meant to cover.
- Fixed by building the skeleton in one `_make_change_list()` helper that sets
  every attribute Django reads (`params`, `model_admin`, `model`, `lookup_opts`,
  `list_display`). One place to keep correct instead of two copies to forget.
- Verified with a mutation probe: flipping the `_sidebar_rank` injection in
  `pages/admin/product.py` to `False` turns the case red, so the two tests
  really assert the sidebar ordering instead of passing vacuously.

## v1.9.3 - 2026-10-02

CJK section markers stopped leaking into the visible project body copy. v1.9.2
cleaned them out of the `<meta>` tag, but the page body (`detail-desc`) and the
project listing cards still rendered the raw `description`, so every project
page opened with a Chinese bracket — `【Customer Profile】` — in front of English
prose, in the body and in the JSON-LD value alike.

- New `scrub_project_markers()` in `pages/utils.py`: deletes the markers and
  **nothing else**. Line breaks are left exactly as authored — no `\r` → `\n`
  promotion — because the SERP channel and the body channel want different
  whitespace and share only the marker deletion; `clean_project_prose()` keeps
  its own flattening so v1.9.2 output is unchanged.
- New `descrub` template filter in `pages/templatetags/text_filters.py`. **One
  definition covers both data paths**: it acts on the rendered value, so the DB
  model and the seed mirror cannot drift apart (the classic two-path bug).
  SafeString identity is preserved, so escaping still belongs to `nl2para`.
- Templates: `project_detail.html` body and JSON-LD `description`, and
  `projects.html` cards and JSON-LD `description` all route through `descrub`
  before `escapejs` / `nl2para`.
- Verified across all 22 seeded projects: paragraph count identical before and
  after (body is repackaged the same way), length drop equals the markers alone,
  and the markers gone everywhere. Guard
  `pages/tests_project_prose_scrub.py` (13 cases) covers the scrubber, the
  filter, raw-input escaping, SafeString passthrough, per-project paragraph
  stability, and the rendered detail page, listing page and JSON-LD.

## v1.9.2 - 2026-10-02

Project meta descriptions are SERP snippets again. All 22 project pages used to
ship the raw `description` body copy — 599 to 1215 characters measured — into a
tag Google truncates at ~155, opening with a CJK `【Customer Profile】` /
`【Scope of Work】` marker and never mentioning the category keyword at all.

- New `MAX_SEO_DESCRIPTION_LEN` (160), `clean_project_prose()`,
  `build_project_seo_description()` and `build_project_og_description()` in
  `pages/utils.py` (pure stdlib, no Django import — an import would re-trigger
  the `pages.views` → models cycle).
- The formula is `{品类词} — {first sentence}`: the keyword leads because it is
  the part worth paying for and the part a tail truncation eats last; the body
  is cut on a sentence boundary when that boundary sits past the halfway mark of
  the budget, otherwise on a word boundary with an ellipsis. CJK section markers
  are stripped, newlines collapsed. Empty prose still yields a keyword-only tag.
- `Project.seo_description()` and `_DictProject.seo_description()` both route
  through the formula. **The seed path is not optional** — production runs on
  `IS_VERCEL` `_load_seed()`, so a one-sided edit would look fine locally and
  ship the 1200-char body copy online only.
- og:description now uses `build_project_og_description()` (full project name +
  keyword, never clamped) via a new `og_description()` on both paths, exposed to
  templates as `project.og_description_t` in `pages/views/enrich.py`. Reusing
  the meta description would have ended every shared card in an ellipsis.
- Guard `pages/tests_project_seo_description.py` (17 cases): formula shape,
  marker stripping, 160-char budget across all 17 sport types, sentence- vs
  word-boundary behaviour, empty-prose fallback, all 22 seeded projects clamped
  and keyword-led, seed↔formula agreement, override precedence, and the two
  rendered `<meta>` tags on `/projects/perryville-high-school/`.

## v1.9.1 - 2026-10-02

Project pages carry their category keyword in `<title>` — 22 of 22 project URLs
used to share one generic suffix (`{title} — SolarOne LED Lighting Project`)
with no sport keyword at all.

- New `PROJECT_CATEGORY_KEYWORD` map + `project_category_keyword()` /
  `build_project_seo_title()` in `pages/utils.py` (pure Python, no Django
  import, shared by the DB and seed paths).
- `Project.seo_title()` (`pages/models.py`) and its seed mirror
  `_DictProject.seo_title()` (`pages/views/utils.py`) both render
  `{title} — {品类词} Project | SolarOne`:
  - `FOOTBALL_FIELD` → `LED football Stadium Lights`
  - `TENNIS_COURTS` / `TENNIS` → `LED tennis Court Lights`
  - the other 14 `sport_type` values get their own phrase; unknown values fall
    back to `LED Lighting` (never an empty middle segment).
- Brand separator switched to the `| SolarOne` form already used by the three
  keyword landing pages, so project and landing titles agree.
- Length clamp (`MAX_SEO_TITLE_LEN = 60`) — the first pass emitted titles up to
  99 characters, which Google truncates, cutting the keyword and the brand off
  the SERP line. `build_project_seo_title()` now drops the word "Project" (9
  free characters) and, when the title still overflows, clamps the **project
  name** on a word boundary with an ellipsis. The keyword and the brand are
  never shortened — the full project name still lives in the H1, the
  og:title (`project_detail.html` now renders `{{ project.title_t }} | SolarOne`
  there instead of the clamped title), the breadcrumb JSON-LD and the body.
  All 22 project titles land in 50–59 characters; guards assert the budget.
- Non-English locales fall back to the English phrase (same B8/E2 convention as
  the product side) — per-language keyword phrasing is a later batch.
- Guards: new `pages/tests_project_seo_title.py` (8 cases, asserts the exact
  campaign strings byte for byte) plus a fix to the pre-existing
  `P3StaticBuildGateTests` marker bug (it looked for a `build.sh` echo that
  never existed, so it raised `ValueError` instead of checking the contract).
- Full suite: 396 tests, 0 failures, 2 pre-existing `ProductAdminSidebarTreeTests`
  errors (missing `lookup_opts`, unrelated to content).

## v1.9.0 - 2026-10-02

Keyword landing pages for the Semrush sport-lighting cluster (Tier-1 + Tier-2),
project → landing cross-links, and an automated Vercel deployment cleanup.

### New landing pages
- `/products/sports-lighting/` — the **LED stadium lights hub**, built on a new
  shared `views_products._sports_landing()` helper. Absorbs the head terms
  `stadium lights`, `led stadium lights`, `stadium light`, `led sports lighting`
  (one term per page, to avoid cannibalisation with product detail titles).
- `/products/football-stadium-lights/` — football & soccer stadium lighting.
- `/products/tennis-court-lighting/` — tennis court lighting; copy explicitly
  covers **both** outdoor (pole + floodlight) and indoor (ceiling / wall mount,
  same optics).
- All three routes registered in `pages/urls.py` **before** the `<slug>`
  catch-all; views exported from `pages/views/__init__.py`; sitemap priority
  0.8 (`views_other.py`); new paths registered in
  `scripts/e2e/visual_review.py:DEFAULT_PATHS`.

### Keyword strategy
- `pages/utils.py` `CATEGORY_KEYWORD['SPORTS_LIGHTING']` → `LED Stadium Light`
  (singular, no "pole"). Product detail titles therefore read
  `LED Stadium Light {model} | SolarOne`, leaving the plural head term to the
  hub. Descriptions re-checked case-insensitively (`stadium light`).
- Home title shortened/trimmed to
  `SolarOne — LED Stadium Lighting Solutions Since 2007` (64 → 52 chars, no SERP
  truncation).
- `seed_data.json` VSP `seo_description` wording updated to
  `LED stadium light pole`; `pages/seed_data.py` regenerated from the JSON
  source of truth.
- `docs/keyword-inventory.csv` retargeted to the three new URLs.

### Cross-links from project pages
- `views_projects.SPORT_TYPE_TO_LANDING` maps each project's existing
  `sport_type` (`FOOTBALL_FIELD`/`SOCCER_FIELD` → football, `TENNIS*`/`TENNIS_COURT`
  → tennis, `MULTI_SPORT`/`BASEBALL` → hub, `AIRPORT`/`ROADWAY` → none) into
  `context['related_landing']`; `project_detail.html` renders a
  "Related Lighting Solutions" block with keyword anchor text. **No model change.**
- Lets the 22 high-authority project pages pass internal links to the three new
  landing pages without rewriting product/project copy.

### Fixes
- 🔴 `pages/views/data_loaders.py`: an **empty DB result no longer populates the
  shared enrichment cache**. Previously `_get_products_from_db()` cached `[]`
  for `en|SPORTS_LIGHTING|`, so `_get_products_from_json()` saw a non-`None`
  cache and returned nothing — the seed fallback was dead and hub pages listed
  0 products. Same fix applied to `_get_projects_from_db()`. Production
  (`IS_VERCEL`) does not take the DB path, so it was unaffected.
- Hub templates: the 5 marketing strings intentionally kept in English
  (verbatim keyword copy, guarded by `I18nCatalogGuardTests`) and all comments
  reduced to single-line `{# #}` so `TemplateCommentHygieneTests` passes.

### i18n
- Five locales' `.po` + compiled `.mo` updated (text append, CRLF preserved,
  existing entries not reordered) with the new home title and the four project
  anchor strings (Related Lighting Solutions / Football Stadium Lights /
  Tennis Court Lighting / LED Stadium Lights, incl. French
  `Projecteurs de stade de football`).

### Tests
- `pages/tests_sports_lighting_hub.py` rewritten as a mixin covering **all three**
  landing pages (200, keyword in title, title ≤ 60 chars, keyword family
  coverage, product grid, ItemList JSON-LD, sitemap) + route registration —
  27 cases.
- `pages/tests_project_related_link.py` — 6 cases (football/tennis/baseball
  mapping, airport block absent, `/fr/` anchor text, `<a>` structure).
- Full suite: **379 tests / 0 failures / 3 errors** (3 errors are the pre-existing
  baseline: `ProductAdminSidebarTreeTests` missing `lookup_opts`, plus the
  `build.sh` static-index gate).

### Ops
- `.github/workflows/vercel-cleanup.yml`: **weekly cron (Mon 03:00 UTC) + manual
  `workflow_dispatch`**. Resolves the team id via `v2/teams`, lists deploys via
  `v6/deployments`, and deletes **previews older than 7 days** and
  **production deployments older than 30 days** via `v13/deployments`. The live
  production deploy is rejected by the API and skipped; the run aborts if a
  whole page yields zero successful deletes. Secret `VERCEL_TOKEN` configured.

### Notes
- Version bump to v1.9.0 in `VERSION` **and** `settings.APP_VERSION` (admin
  header reads the latter).
- `llm.txt` synced with the three landing-page URLs.
- Deployment Storage had reached 8.94/10 GB on Vercel; Usage figures lag the
  deletes by several hours up to 24 h.
- Pending after deploy: run the cleanup workflow once by hand, request indexing
  for the three new URLs in GSC, then review rank/query data in 2–4 weeks.

## v1.6.3 - 2026-09-24

### P0 前端风格一致性修复（设计审计 P0 三项）

- **P0-1 未定义 token**：Cookie 横幅 `background: var(--surface)` 引用了从未定义的
  变量 → 无效声明 → 背景 transparent 透底。改用双主题均已定义的 `var(--bg-raised)`。
- **P0-2 accent 单一色源 + light 主题覆盖修复**：`--accent` 此前有 4 个分歧值
  （base.css 暗 `#0077ED` / light `#0062C4` / admin 注入 `#0088FF` / critical CSS
  `#0077ED`），且 admin 注入块以相同 specificity + 更靠后源序直接写
  `:root{--accent:…}`，把 `[data-theme="light"]` 的压暗覆盖冲掉——浅色模式实际
  渲染深色主题亮蓝（对小字号 mono 标签对比度不足）。重构为单一色源：admin 只注入
  `--accent-brand`（默认 `#0088FF` = SiteConfig 默认值），`--accent` 及全部派生
  （hover/soft/glow/deep/渐变/阴影）由 base.css 从 brand 推导；color-mix 派生包在
  `@supports` 内（自定义属性不做语法校验，裸写 color-mix 会让不支持的浏览器把该
  字面量代入消费属性 → 整条声明失效），字面量保留为老浏览器 fallback。附带修复
  `.btn-primary:hover` 写死 `#0088FF`（恰与默认 accent 同色 → hover 无色差）。
- **P0-3 字体栈对齐 + 字重补全**：critical CSS 的 `--ff-display` 仍指向从未真正
  生效的 `'Space Grotesk'`（首帧与 base.css/admin 注入不一致，且 9 个 woff2 白
  下载），统一为 canonical 栈 `'Inter', system-ui, -apple-system, BlinkMacSystemFont,
  'PingFang SC', …, Roboto, sans-serif`——critical CSS / base.css / seed_data.py /
  seed_data.json / models.py 默认值五处对齐（seed 原缺 CJK 兜底，运行时中文回退
  与 base.css 意图相悖）。`fonts.css` 原只自托管 Inter 400/600 与 Plex Mono 400，
  而全站大量使用 `font-weight:500/700` 与 mono `500/600` → 字重回退/合成粗体跨
  OS 不一致；新增 24 个 woff2（Inter 500/700、IBM Plex Mono 500/600，共 12 子集）
  + 24 个 @font-face（合计 52 faces），全部通过 wOF2 magic 校验。生成脚本
  `scripts/_add_font_weights.py`（幂等、可 --dry-run）。Space Grotesk 的
  @font-face 保留（无渲染栈引用即零下载；admin 仍可手动选用）。
- **Data migration `0026`**：已知旧字体栈（seed 的 Segoe UI 栈、0024 前后默认值）
  升级到 canonical，仅匹配已知默认值才改写，保护管理员自定义。
- **防回归**：新增 `P0StyleConsistencyTests`（surface token / accent 单源跨层一致 /
  字体栈五处一致 / 字重文件存在且可解析 / btn hover 走 token）。
  `scripts/_add_font_weights.py` 纳入仓库。

### P1–P3 发布前优化与验证

- **P1 Contact 表单公共化**：将 Contact 字段布局、标签、输入框与 textarea 的重复样式收敛到
  `static/css/base.css` 的共享 class，保留原有间距、字号、边框和移动端 16px 输入规则；
  未强行套用参数不同的通用 `.form-group`。详情页侧栏的页面级差异保持原样。
- **P2 视觉 token 与眉标整理**：新增 `--radius-control`，统一公共交互控件圆角；Projects
  与 News 使用共享 eyebrow/label 组件。Banner、详情页网格、轮播、RTL、页面 section
  间距和 Contact 提交按钮等真实视觉差异保留，不做机械统一。
- **P3-1 静态构建门禁**：`build.sh` 在生产路径对 collectstatic、manifest 和静态索引失败
  采取 fail-closed；新增 `scripts/verify_static_build.py`，验证 manifest → hashed index →
  `public/static/` 完整链路。
- **P3-2 视觉评审覆盖**：`scripts/e2e/visual_review.py` 默认覆盖 8 个公开页面，并支持
  Dark/Light 双主题、主题漂移检测、HTTP 状态检查与合法横向滚动排除。
- **P3-3 浏览器安全门禁**：E2E 新增 CSP nonce、console error、pageerror、requestfailed
  与 HTTP 4xx/5xx 响应检查；当前仍明确保留 `style-src 'unsafe-inline'`，待页面内联样式
  渐进迁移后再收紧。
- **认证图片迁移**：旧 `cert-3.webp` / `m-series-certs.webp` 已确认不再作为当前生产
  seed 引用，删除并改用新的认证图片资源；静态构建门禁和图片引用测试作为发布前防线。
- **局域网人工检查**：已使用项目既有 `scripts/dev_preview.py` 完成 Windows/移动端
  多浏览器人工检查；脚本自动绑定局域网地址并注入当前进程 `ALLOWED_HOSTS`，无需修改
  生产设置。
- **发布验证**：`manage.py check`、迁移漂移检查、全量 Django 测试、静态构建门禁、
  Playwright E2E 与 `git diff --check` 均通过；E2E 汇总为 `ALL CHECKS PASSED`。


## v1.6.2 - 2026-09-22

### Two product page templates (overview vs detail) + sidebar-mirrored admin changelist

- **Two-template split.** Products now render either `templates/product_overview.html`
  (series landing: banner + gallery carousel + copy + spec highlights, no beam-angle /
  dimension / energy-table / request-a-sample blocks) or `templates/product_detail.html`
  (full specs, unchanged). The choice is data-driven via a new `Product.page_layout`
  field (`detail` / `overview`, default `detail`) selected in the admin — the old
  hardcoded `product.slug != 'm-series'` conditionals in the detail template are gone.
  Migration `0025_add_product_page_layout`.
- **Sidebar hierarchy.** Two new series-home products (`rgb-rgbw`, `accessory`,
  `page_layout=overview`) with their model pages (`fl9m-rgbw`, `glare-shield-for-rt410`)
  nested underneath — the same shape as M Series. The public products sidebar
  (`pages/views/i18n.py`) now nests `RGB / RGBW` and `Accessory`; the child label
  `RT410 GS` replaces the long "Glare Shield for RT410". No URL changed.
- **Seed double-channel sync.** `page_layout` is exported in
  `pages/seed_sync.py::_product_to_dict` and present in both `pages/seed_data.py` and
  `seed_data.json`, guarded by an `IS_VERCEL=True` split-identical test (a missed export
  would silently turn every overview page back into a detail page in production).
- **Admin changelist mirrors the public sidebar.** New `Sidebar Position` column shows
  the breadcrumb `Category ▸ Series ▸ Model` (e.g. `Area and Site ▸ M Series ▸ FL4M`)
  and rows are sorted in sidebar traversal order. The rank map's single source of
  truth is `pages/views/i18n._get_products_sidebar('en')`, so sidebar edits flow into
  the admin automatically; slugs not in the sidebar sort last and a sidebar build
  failure can never break the admin. Implementation note (two Django internals that
  cost one 500 each): `ModelAdmin.get_queryset` runs `get_ordering()` before any
  annotation could exist, and `RelatedFieldListFilter.field_choices` borrows
  `get_ordering()` for its *own* choices queryset — so `ProductAdmin.get_queryset`
  only annotates `_sidebar_rank` via a slug-keyed SQL `CASE`, and the ordering is
  injected in `SidebarOrderedChangeList.get_ordering(request, queryset)` (the hook
  that runs after the annotation exists; explicit `?o=` column sorts win).
  Filters/search/pagination intact.
- **Guards.** `manage.py test pages` covers: A/B template split (local + stateless),
  overview-template source contract (LCP hero, 1024px breakpoint, RTL logical
  properties, shared carousel include, no dead table/CTA CSS), detail-template leaf-only
  (no slug/category special cases), sidebar nesting, seed export, and the new
  `ProductAdminSidebarTreeTests` (rank coverage/order/parent-child grouping, breadcrumb
  labels, queryset CASE + fallback, empty-sidebar survival).
- **Sidebar gap for `rt410-rgbw`** (admin-created model under the `rgb-rgbw` series
  home): it was missing from `RGB_RGBW.subseries` in `pages/views/i18n.py`, so the
  product had no frontend entry point and the admin `Sidebar Position` column showed
  "— outside sidebar". Added `RT410_RGBW`; the seed-driven sidebar-nesting test now
  fails closed if a seed `parent_slug` has no sidebar entry.
- **Local static 404s after admin image uploads**: WhiteNoise without autorefresh
  serves only the file snapshot taken at process start — anything written into
  `static/` while `runserver` keeps running (admin uploads + its `collectstatic`)
  404s: admin changelist icons missing, frontend product images broken. New
  `WHITENOISE_AUTOREFRESH = not IS_VERCEL` (local re-resolves per request via
  finders; Vercel unchanged, build-time collectstatic). Guard:
  `WhiteNoiseLocalDevTests`.
- **Version**: `VERSION` and `solarone/settings.py:APP_VERSION` → `1.6.2`.

## v1.6.1 - 2026-09-14

### Low-cost / independent hardening: ALLOWED_HOSTS lockdown, self-hosted fonts, edge rate limiting (#4 / #2 / #5)

- **#4 — ALLOWED_HOSTS lockdown.** `solarone/settings.py:83` drops the bare `.vercel.app`
  wildcard (which let ANY `*.vercel.app` host — incl. attacker-controlled — be accepted, an
  SEO/canonical-poisoning vector given the fixed `CANONICAL_ORIGIN`). Default is now the
  production custom domains + the known Vercel preview host `solar-one-website.vercel.app` +
  `localhost`/`127.0.0.1`; still overridable via the `ALLOWED_HOSTS` env var. Random
  per-branch preview URLs need `ALLOWED_HOSTS` set in the Vercel "Preview" env scope.
  New guard `pages/tests.py::test_disallowed_host_rejected` asserts a spoofed
  `evil.vercel.app` Host returns HTTP 400.
- **#2 — self-hosted fonts (no third-party request).** Downloaded Space Grotesk (400/600/700),
  Inter (400/600) and IBM Plex Mono (400) woff2 subsets into `static/fonts/` and added
  `static/css/fonts.css` with `@font-face { font-display: swap }`. Removed the Google Fonts
  `<link>`/`preconnect` from `templates/base.html`; CSP tightened to `font-src 'self'`
  (the prior `https://fonts.googleapis.com https://fonts.gstatic.com` allowance is gone).
  Fonts are committed and served by the Vercel CDN from our own origin — GDPR-friendly, no
  render-blocking third party, identical coverage to Google Fonts for en/fr/es/de/ru (ar falls
  back to system Arabic as before).
- **#5 — edge rate limiting.** `vercel.json`'s `routes[].mitigate` only supports `challenge`
  and `deny`; **`rate_limit` cannot be expressed in `vercel.json`** (confirmed against Vercel
  docs — it requires the dashboard or the REST API). The in-code app-layer limiter
  (`pages/views/views_contact.py::_is_rate_limited`, LocMem cache, fail-closed) is kept as a
  per-instance best-effort safety net. A ready-to-apply Vercel Firewall rule is shipped as
  `vercel-firewall-rate-limit.json` (rate_limit, fixed_window 60s, 10/min, keyed by IP, deny
  on breach, scoped to POST `/contact/`) — enable it in the Vercel Firewall UI or via
  `PATCH /v1/security/firewall/config` to get true distributed edge rate limiting.
- **Version**: `VERSION` and `solarone/settings.py:APP_VERSION` → `1.6.1`.
- **Verification**: full `manage.py test` suite green; `git status` shows no deletions.

## v1.6.0 - 2026-09-14

### Production becomes fully stateless — seed JSON is the sole content source (A1 / B3 / B4 / B7)

Decision (user, 2026-09-14): **the committed `seed_data.json` is the single source of truth for
content; the database is only a local admin preview.** In production (`IS_VERCEL=True`) no request
ever reads content from the database; the DB (SQLite `/tmp` or `DATABASE_URL`) is reserved for the
local admin preview only.

- **A1 + B7 — products/projects never touch the DB in production.** `pages/views/data_loaders.py`:
  each of the four `_get_*_from_db` / `_get_*_detail_from_db` loaders now early-returns to its
  `_get_*_from_json` counterpart when `settings.IS_VERCEL` is true. This removes the DB-first query
  path (and the per-request DB retry that could mask a missing connection) for every content view.
  Local dev is unchanged.
- **A1.1 + B4 — `get_common_context()` builds from seed in prod, no hidden GET-write.** Extracted
  `_build_siteconfig_from_seed()` (mirrors the old `except` fallback). When `IS_VERCEL` is true the
  site config is built from seed and the database is never queried. In local dev the `if not config`
  branch no longer calls `SiteConfig.objects.create()` on a GET — when the singleton row is missing
  it now falls back to seed defaults instead of auto-creating a DB row (removes the hidden write
  that the production path could have triggered). The hero/logo URL + translation enrichment runs
  for **both** paths, so production renders identically to local.
- **B3 — news seeded + seed fallback.** `pages/seed_sync.sync_seed_from_db()` now serializes
  `NewsArticle` rows into a new top-level `news` key in `seed_data.json` (fields `slug, title,
  summary, content, image` (static-resolved path), `published_at` (ISO string), `is_published`),
  carrying all keys through to the generated `.py`. `pages/views/views_other.py::news()` gains an
  `IS_VERCEL` branch that renders from `_load_seed()['news']` (filtered by `is_published`); the local
  branch is unchanged except it now also sets `article.image_url` so the template is unified.
  `templates/news.html` renders `article.image_url` (works for both DB objects and seed dicts).
  `seed_data.json` gained `"news": []` (mechanism ready; content appears once news is added locally
  and re-synced).
- **Version**: `VERSION` and `solarone/settings.py:APP_VERSION` → `1.6.0`.
- **Docs**: `docs/优化建议清单.md` updated (new changelog row + A1/B3/B4/B7 marked done).
- **Verification**: 3 new regression guards in `pages/tests.py`
  (`test_prod_loaders_skip_db`, `test_get_common_context_no_db_write`, `test_news_seed_fallback`).
  Full suite green; `git status` shows no deletions.

## v1.5.9 - 2026-09-14

### B 组立即可做项 + 基础 CSP（无需架构改动）

- **A3 锁依赖版本上界**：`Django>=6.0,<6.1`（把本地 6.0.7 与 Vercel 6.1.1 收敛到 6.0.x，规避 Django 6.x `STATICFILES_STORAGE` 移除类静默大版本升级）；Pillow/whitenoise/dj-database-url/deep-translator/gunicorn/user-agents 加次版本上界以降低漂移（保留 Pillow 注释说明其为 ImageField 运行期依赖）。
- **A2 `build.sh` 受保护 migrate**：`collectstatic` 之后仅在真正外部 DB（`DATABASE_URL` 非空且不含 `/tmp/`）时才跑 `migrate --noinput`；无状态 seed 模式下（`/tmp/` 或空）跳过，避免无意义建表/报错。
- **E1 基础 CSP 响应头**：新增 `pages/middleware.py:ContentSecurityPolicyMiddleware`，在 `process_response` 写入 `Content-Security-Policy`（策略读自 `settings.CONTENT_SECURITY_POLICY`，默认先放行 `unsafe-inline` 换纵深防御）；在 `MIDDLEWARE` 的 `SecurityMiddleware` 之后插入；新增 `ContentSecurityPolicyHeaderTests` 断言首页响应含该头。
- **C1 内容图防 CLS + 懒加载**：`products/projects/product_detail/about/contact` 首屏之下 `<img>` 加 `loading="lazy" decoding="async"`；`about-main.webp` 加显式 `width/height`（800×448），产品卡/项目图/详情图靠容器 `aspect-ratio` 兜底防抖动；不新生成 `-1280` 变体。
- **D2 去掉本地恒跳过的测试**：`VercelSecureCookieTests` 改 `@override_settings(IS_VERCEL=True, SECURE_SSL_REDIRECT=True, SECURE_HSTS_SECONDS=31536000, SESSION_COOKIE_SECURE=True, CSRF_COOKIE_SECURE=True)` 本地可跑；`GeneratedStaticIndexCoverageTests` 改在 `setUp` 用 `pages.static_index.build_index` 基于 `static/` 临时构建索引本地可跑（skipped 2 → 0）。
- **D3 收敛重复哈希解析函数**：新增单一 `pages/utils.py:strip_hash_suffix`，`pages/views/utils.py:_clean_hashed_name` / `pages/models.py:_clean_hashed_filename` / `pages/seed_sync.py:_strip_hash_suffix` 三处改薄包装调用（行为不变，全量测试无回归）。
- **G4 内联首屏关键 CSS**：`templates/base.html` `<head>` 内联首屏 above-the-fold 关键样式（导航 / hero 容器 / body 基础字体背景 / 关键布局 + :root 变量，约 2KB），其余仍走 `base.css` 的 `<link>`，消除首屏 CSS 渲染阻塞 / FOUC 兜底。
- **版本**：`VERSION` 与 `solarone/settings.py:APP_VERSION` → `1.5.9`。
- **验证**：`manage.py test pages --keepdb` 全量 OK，`skipped` 由 2 降到 0；首页响应含 `Content-Security-Policy`。

## v1.5.7 - 2026-09-13

### Fix: contact form silently loses submissions on Vercel (N-39)

- **Root cause (confirmed):** `ContactMessage` is saved to `DATABASE_URL=sqlite:///tmp/db.sqlite3`
  on Vercel (wiped on every redeploy/cold start). `CONTACT_NOTIFY_EMAIL` is empty by default, so
  `_send_contact_notification` early-returns and `send_mail(fail_silently=True)` + a `locmem`
  `EMAIL_BACKEND` fallback mean **no email is ever sent**. Users saw "success" but nothing persisted.
- **Hardening (no env change required to stop the silent loss):**
  - `send_mail(fail_silently=False)` so real SMTP errors are caught and logged.
  - When `CONTACT_NOTIFY_EMAIL` is empty **and** `IS_VERCEL`, log an explicit `logger.error`.
  - On `IS_RUNTIME` (ephemeral `/tmp` DB) with no email delivery, the form **no longer claims
    success** — it tells the user to retry later or email directly.
  - New `pages/checks.check_contact_persistence` (id `pages.W001`): emits a `Warning` when
    Vercel + ephemeral DB + no notify email, so `manage.py check` / CI surfaces it.
  - `api/index.py` cold-start self-check now prints contact persistence facts
    (notify_email set / email backend / DB ephemeral).
- **Guard:** `ContactPersistenceCheckTests` (4) in `pages/tests.py`.
- **The durable fix still requires Vercel env vars:** `CONTACT_NOTIFY_EMAIL` + `EMAIL_HOST_USER` /
  `EMAIL_HOST_PASSWORD` (SMTP). Long term, point `DATABASE_URL` at Neon/Supabase and run migrations.

## v1.5.6 - 2026-09-12

### Fix: `/products/` banner collapsed to its `min-height` floor, cropping the image

- **Symptom (reported on production):** on `https://www.solaronelighting.com/products/`
  the banner got much shorter and the 1920×442 artwork was cut off at the top **and**
  bottom.
- **Root cause:** the F9 change (v1.4.2) removed `aspect-ratio: 1920 / 442` from
  `.products-banner` and kept only `min-height: 120px`. Every child of that box
  (`img`, `.products-banner-overlay`, `.products-banner-content`) is
  `position: absolute`, so the container has **no in-flow content** — its height
  was *exactly* the floor value.

  | Viewport | box | box AR | image AR | vertical crop from `object-fit: cover` |
  | --- | --- | --- | --- | --- |
  | 1440 (before) | 926 × 120 | 7.72 | 4.34 | **43.7%** |
  | 1440 (after) | 926 × 213.2 | 4.344 | 4.344 | **0.0%** |
  | 390 (both) | 358 × 90 | 3.98 | 4.34 | 0% (tiny horizontal crop, as F9 intends) |

- **Fix:** both declarations must coexist — `aspect-ratio` supplies the *preferred*
  height, `min-height` stays as the narrow-screen floor that keeps the text room
  (the original P1-7 goal).
- **Why the guards missed it:** the L1 test `test_products_banner_no_hard_aspect_ratio`
  and the L2 static check asserted the *inverted* rule ("must **not** have
  `aspect-ratio`") — a guard written to match the bug is no guard at all. Both are
  now bidirectional, plus a new browser-level assertion that the desktop box AR
  matches the image AR within 2% (the only check that actually catches this class
  of regression).

### Fix: multi-line `{# #}` comment leaked into the rendered page

- `templates/products.html` had a 3-line `{# ... #}` comment around the LCP banner.
  Django's `{# #}` only comments a **single line** and the lexer does **not** raise,
  so the comment body was emitted verbatim. It landed inside `.products-banner` as
  **in-flow** inline text (all siblings are absolute), which:
  1. leaked readable text (screen readers announce it; visible if images fail);
  2. inflated the container to 179.2px at a 390px viewport — masking the real
     "height is CSS-only" contract and making the F9 bug look harmless on mobile.
- Fixed with `{% comment %}...{% endcomment %}`; new `TemplateCommentHygieneTests`
  scans every template for multi-line/unterminated `{#` **and** asserts rendered
  pages never contain `{#`.
- This is the second time this trap bit the project (see v1.1.3 `nav_items.html`);
  it is now machine-checked.

### Verification

- L1: 101 → **103 tests OK (skipped=2)**.
- L2 (Playwright + Edge): **ALL CHECKS PASSED** — desktop 1440/1280 banner AR
  deviation 0.0%, 320/360 banner keeps the ratio + floor, no title overflow.

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

## v1.10.10 - 2026-10-04

## Exhibition Information, and a cover that is actually centred

Two corrections to v1.10.9, both reported by an editor looking at the HKTEX
article on the live preview.

### "Company News" is now "Exhibition Information"

The category was named after the publisher rather than the content, so a trade
show notice read as corporate PR. `Case Studies` and `Industry Insights` keep
their names; `Product News` stays available for release notes.

The rename is one literal in five independent places, and **every one of them
fails silently** — no exception, no log line, just a wrong label:

| where | symptom if missed |
|---|---|
| `NewsArticle.NEWS_CATEGORIES` | admin offers a value the feed never uses |
| `_SIDEBAR_I18N` | the chip shows the bare English key in all five locales |
| the seed row | the article is filed under a key absent from `choices`, so `?category=` can never match it |
| the `_t()` fallbacks in `views_other` | an article with no `category` key renders an untranslated chip |
| the seed default in `data_loaders` | same, one layer down |

All five are updated, in the local DB via `QuerySet.update()` (not `save()`,
which fires `post_save` → `seed_sync` in its default DB → JSON direction and
would rewrite `seed_data.json` from the database) and in `seed_data.json` as a
byte-exact single replacement so the file's CRLF endings stay intact. The build
artifact `pages/seed_data.py` is regenerated with
`python -m pages.seed_sync --json` — production reads that file first, so a
JSON-only edit would leave the live site unchanged while local renders looked
correct.

Translations use trade-fair vocabulary, not corporate-PR vocabulary: fr
*salon*, es *feria*, de *Messe* (= trade fair, not *Ausstellung*, which also
means an in-store display), ru *выставка*.

### The cover is cropped to its content, then centred

v1.10.9 scaled the whole 1470px screenshot and pasted it at `x=0`. The file's
alpha channel only covers `x=2..775` — **695px, 47% of the canvas, was pure
transparency** — and that transparent block was flattened into the WebP as a
white slab down the right-hand side. Hence "the picture is too far left, there
is a lot of empty space on the right".

The fix crops to `alpha.getbbox()` first (773x240, 3.221:1 — what the eye
actually reads as the image), scales that to the full 1600px canvas width and
centres it in the 1600x900 frame. Measured result: left/right margins 0/1px,
top/bottom 199/200px.

**Geometry assertions could not have caught this.** The broken cover was a
clean 1600x900 and `NewsCoverGeometryTests` stayed green — the defect was in
the pixels, not the dimensions. So the new guard decodes the image and measures
the inked content box, with a symmetric-centring check as well as a
spans-the-canvas check (a centred postage stamp satisfies the first but not the
second).

Guards: `NewsCategoryTaxonomyTests` (7 tests) and `NewsCoverCentringTests` (3).
The taxonomy guard asserts the old name is *absent* from executable lines in all
five files — the one failure a positive assertion cannot catch is a half-finished
rename, which degrades to English chips in five locales and nothing else. A
4-mutation probe (drop one locale's translation, edit only the JSON without
rebuilding the artifact, misspell a `choices` key, re-whiteout the cover's right
side) turns all of them red.

## v1.10.9 - 2026-10-04

## HKTEX 2026: the Outdoor and Tech Light Expo article

A third news article, covering the HKTDC Outdoor and Tech Light Expo
(26-29 October 2026, AsiaWorld-Expo, Hong Kong).

**The cover is matted into 16:9, not dropped in as-is.** The supplied HKTEX
banner is a 1470x240 strip -- 6.13:1 -- carrying the show wordmark, the Chinese
and English names, the dates and the venue on a single line. Both news surfaces
put a cover in a 16:9 box with `object-fit: cover`, so the raw strip would have
been scaled to fill the height and roughly 71% of its width cropped away: the
wordmark and the dates would simply not appear, and the page would still return
200. The file is therefore flattened onto white and centred in a 1600x900
canvas, so the whole strip survives the crop.

**Copy kept short, and inside the SERP budgets.** The body is four paragraphs
(208 words): what and when, what is shown, what the last edition drew, how to
attend. Every figure is quoted from the official show page -- 25,000 m2, 448
exhibitors, 18,169 visitors, the 770-respondent survey (67% expect growth, 1%
expect decline) and the four segment shares -- and nothing is invented. The
title is 43 characters, so `<title>` renders 59 including the ` -- SolarOne
News` suffix, under the 60-character budget; the summary is 153, under the 160
that `|truncatechars:160` allows.

Guards: `NewsCoverGeometryTests` and `NewsArticleSeoBudgetTests` (8 tests).
The geometry guard reads the real WebP header and asserts 16:9 plus a minimum
width, because a cover's aspect ratio is a property of the asset that no
template assertion can see. A 12-mutation probe -- including re-exporting the
cover at 6.13:1 and at 4:3, and drifting the build artifact away from the JSON
-- turns all of them red.

The five non-English translations start empty, as with every other article;
`translate()` falls back to the English base rather than rendering a blank.

## v1.10.8 - 2026-10-04

## Larger charts, and a visible cover on the market article

Follow-up to v1.10.6, from an editor's review of the market article page.

**The three charts are 20% larger.** v1.10.5 set inserted figures to 50% of the
content column. The content box measures 1216px, so 50% meant 608px, and the
charts' 8-13px labels landed at an effective 3.0-4.8px. They are now 60%
(~730px, a 44.5% scale of the 1639px originals), lifting those labels to
~3.6-5.8px. `height: auto` is unchanged, so both axes still scale together and
the `object-fit` guard that protects the chart edges still holds. Phones
(<=767px) keep their full width.

**The card cover is no longer an empty grey block.** v1.10.6 removed this
article's cover, and `/news/` only ever looked at `article.image_url` -- so the
card fell through to `.news-card-cover-fallback`, a grey gradient. Nothing
errored and the page returned 200; an editor simply saw no picture. A card now
falls back to the article's first gallery image, in the same order as
`social_image_url`, so the card, `og:image` and the `NewsArticle` block all
show one file. An article with a cover of its own still uses it, and the
gradient stays reserved for articles that genuinely have no picture.

**The three photographs are gone** (completed from v1.10.6): the market article
now carries only its three charts.

Guards: `NewsDetailFigureLayoutTests` re-pinned to 60% and
`NewsCardCoverFallbackTests` added (5 tests, including a source-level pin on the
fallback order). A 10-mutation probe turns every one of them red.

## v1.10.5 - 2026-10-04

## Every news figure but the hero now renders at half width, centred

The market article's five in-body images were spanning the full 1216px content
column, which reads as a banner rather than an illustration. They now render at
half the column width and are centred, so the body text and the supporting image
share one visual column.

- `.news-detail-figure img` → `width: 50%; height: auto; margin-inline: auto`.
  `height: auto` is what makes this halve **both** axes: the browser keeps the
  intrinsic ratio instead of letterboxing a portrait photo.
- The article's first image (`.news-detail-media-cell--large`, the cover) is
  untouched — it keeps `width: 100%` and `object-fit: cover`.
- `figcaption` is centred with the image; a left-aligned caption under a centred
  photo reads as a misalignment bug.
- Below the phone breakpoint (`max-width: 767px`) the figure gets its full width
  back: 50% of a ~360px content box is ~180px, which puts a chart label at 2-3px.

Guard: `NewsDetailFigureLayoutTests` (6 cases) in `pages/tests_news_figures.py`.
Mutation probe 7/7 red (half-width reverted, centring removed, height pinned,
`object-fit` added, hero also halved, caption uncentred, 767 override removed).
Full regression 562 tests / 32 failures / 1 skipped — the 32 are the pre-existing
content backlog, no new ones.

## v1.10.6 - 2026-10-04

## The market article keeps only its three charts

Editor removed the three stock photographs from `global-led-lighting-market-2034`
and wants the article to carry nothing but the three generated bar charts: the
market-size chart, the regional split for 2025 and the segment split for 2026.

- Dropped the cover (`led-lighting-market-2034-hero.webp`) and the two in-body
  photos (`-smd-leds`, `-street-lighting`) — from the gallery list, from the
  body copy's `{{figure:…}}` markers, and from the article's cover field.
- The article now has **no cover**, so the top media grid renders nothing at
  all rather than an empty 16:9 shell; the page opens straight into the first
  paragraph and its chart.
- The key stays in `seed_data.json` as `''` rather than being dropped: the test
  fixture indexes `article['image']`, and a DB→JSON export of an empty cover
  writes `''` anyway — so deleting it makes the two shapes disagree.
- `/news/` still shows a cover slot for this article; it now renders the existing
  `.news-card-cover-fallback` placeholder block.

Guard: `NewsDetailFigureRenderTests` no longer hard-codes `5`/`4` — the expected
figure count is read from the article's own gallery, so the next content edit
does not turn into a test edit.

## v1.10.7 - 2026-10-04

## A coverless article no longer advertises a bare origin

Found by reading the rendered page after v1.10.6 removed the market article's
cover — not by a failing test, because nothing failed.

- `NewsArticle` JSON-LD rendered `"image": "https://www.solaronelighting.com"`
  (a bare origin; consumers reject it) and `og:image` disappeared from the page
  entirely, because the site-wide fallback in `base.html` is empty too. Sharing
  the article produced a preview with no image at all.
- New derived key `social_image_url` (`_news_social_image()`): the cover if
  there is one, otherwise the **first gallery image**, otherwise `''`. Added to
  both the DB and the seed path and pinned in `NEWS_DERIVED_KEYS`.
- The JSON-LD `image` key is now conditional and moved last in the object, so an
  article with no images at all omits the key instead of emitting a broken URL.
- `og:image` reads the same value, so the card and the structured data can never
  disagree.

Guard: `NewsSocialImageTests` (5 cases) asserts the *value*, not the syntax —
`JsonLdValidityTests` only checks that the block parses, which is exactly why
this slipped through. Articles that still have a cover are unaffected.
Mutation probe 6/6 red; full regression 574 tests / 32 failures / 1 skipped.
