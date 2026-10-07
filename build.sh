#!/bin/bash
# Vercel build script
# Key strategy: Vercel AUTOMATICALLY deploys the ./public/ directory as a CDN
# static root (files in public/foo.bar served at https://domain/foo.bar).
# So after Django collectstatic writes to ./staticfiles, we mirror the output
# into ./public/static/. This way /static/* is served FIRST by Vercel's global
# edge CDN — no Python Lambda coldstart, no WhiteNoise needed for plain assets.
#
# NOTE (verified live 2026-09-12): the catch-all rewrite alone is sufficient —
# Vercel's edge CDN already serves public/static/* (probe returns
# `X-Vercel-Cache: HIT`), so NO `handle: filesystem` route is required.
#
# 🔴 CORRECTION (v1.9.7, re-verified live 2026-10-03): the claim below that
# hashing alone yields `immutable, max-age=31536000` is FALSE. Because these
# files are served straight out of public/ by the edge CDN, no Django setting
# can influence their response headers — a live probe of the already-hashed
# `/static/css/base.<hash>.css` still returned `max-age=0, must-revalidate`.
# The `headers` block in vercel.json is what actually sets them. Content
# hashing is still necessary (it is what makes `immutable` safe), but it is
# not sufficient on its own.

set -e
set -o pipefail

# Silence non-fatal build warnings:
# - UV_LINK_MODE=copy: Vercel's build FS has no hardlink support, so `uv pip
#   install` would warn "Failed to hardlink files; falling back to full copy".
#   Copying directly suppresses it (no real perf impact at our scale).
# - PIP_ROOT_USER_ACTION=ignore: Vercel installs as root; this quietens pip's
#   "Running pip as the 'root' user" warning on any pip step that runs inside
#   this script (Vercel's own native pip step is silenced via a project env
#   var — see commit note).
export UV_LINK_MODE=copy
export PIP_ROOT_USER_ACTION=ignore

echo "=== [build.sh] Starting ==="
echo "  Working dir: $(pwd)"
echo "  Python: $(which python)"
python --version
echo "  uv check: $(command -v uv || echo 'not found')"

# 1. Install Python deps — prefer uv (pre-installed on Vercel, much faster),
#    fall back to pip with --break-system-packages, then plain pip.
export SECRET_KEY=build-time-placeholder
set +e
INSTALL_SUCCESS=0
if command -v uv &> /dev/null; then
    echo "  Using uv..."
    # Install into the system Python (Vercel Lambda runs on system Python, no
    # venv). --system avoids "No virtual environment found"; --break-system-packages
    # is required on PEP 668 externally-managed runtimes and is a harmless no-op
    # elsewhere. The pip fallback below stays as a safety net.
    uv pip install --system --break-system-packages -r requirements.txt 2>&1 | tail -10
    INSTALL_SUCCESS=$?
fi

if [ $INSTALL_SUCCESS -ne 0 ]; then
    echo "  Falling back to pip..."
    pip install --break-system-packages --root-user-action=ignore -r requirements.txt 2>&1 | tail -10
    INSTALL_SUCCESS=$?
fi

if [ $INSTALL_SUCCESS -ne 0 ]; then
    echo "  ERROR: Failed to install dependencies"
    exit 1
fi
set -e
echo "=== [build.sh] pip install done ==="

# 2.2. Contact-form durability gate (J1): fail the build if Vercel has NO
# durable delivery channel for contact submissions. pages.W001 is raised by
# pages/checks.py when (a) DATABASE_URL is empty (build time — the /tmp runtime
# default isn't injected yet) or points at the ephemeral /tmp SQLite, AND (b)
# email is not fully configured (CONTACT_NOTIFY_EMAIL + SMTP creds). Under these
# conditions submissions are lost on every redeploy, so we refuse to ship rather
# than silently deploy a lead-losing config. Set CONTACT_NOTIFY_EMAIL +
# EMAIL_HOST_USER/PASSWORD (or a persistent DATABASE_URL) to clear it.
echo "=== [build.sh] Contact durability check ==="
if python manage.py check 2>&1 | tee /tmp/contact_check.log | grep -q "pages.W001"; then
  echo "  ✗ ERROR: pages.W001 — contact form has no durable delivery on Vercel."
  echo "    Set CONTACT_NOTIFY_EMAIL + EMAIL_HOST_USER + EMAIL_HOST_PASSWORD"
  echo "    (Gmail app password), or set DATABASE_URL to Neon/Supabase Postgres."
  echo "    Refusing to deploy a config that loses leads on redeploy (J1)."
  exit 1
else
  echo "  ✓ contact durability OK (persistent DB or email configured)"
fi

# 1.5. Regenerate pages/seed_data.py from seed_data.json (Vercel only uses seed_data.py).
# Uses the unified seed_sync.py in JSON mode (no Django DB needed on Vercel).
# pages/seed_data.py is git-ignored — this step is what produces it on every build.
# seed_data.json is the source of truth and is left untouched.
echo "=== [build.sh] Regenerating seed_data.py from seed_data.json ==="
python -m pages.seed_sync --json 2>&1

# 1.5b. Stamp the deploy date for sitemap <lastmod>.
# Vercel's serverless checkout rewrites file mtimes — a live probe showed all 59
# <lastmod> values collapsed to a stale 2018 date, so the sitemap can no longer
# rely on os.path.getmtime(). Write the build date into a git-ignored build
# artifact (same pattern as pages/seed_data.py); views_other._site_last_modified()
# prefers it and falls back to the seed mtime locally, where the file is absent.
echo "=== [build.sh] Stamping build date for sitemap lastmod ==="
printf "SITE_LAST_MODIFIED = '%s'\n" "$(date -u +%Y-%m-%d)" > pages/build_meta.py
cat pages/build_meta.py

# 1.6. Prepare the Vercel CDN root (public/) and point collectstatic AT it.
# On Vercel the build output directory is `public/` (vercel.json outputDirectory),
# and static assets are served straight from the edge CDN at /static/*. So we
# collectstatic directly into public/static instead of ./staticfiles and THEN copying
# the whole ~140 MB tree across — that copy was the single heaviest step in the old
# build (2026-09-28 build-speed fix).
echo "=== [build.sh] Preparing public/ CDN root ==="
rm -rf public
mkdir -p public
export VERCEL_STATIC_ROOT=public/static

echo "=== [build.sh] Generating responsive image variants (batch C) ==="
python scripts/gen_image_variants.py
echo ""

# 2. Run Django collectstatic -> writes the hashed assets into $VERCEL_STATIC_ROOT
#    (public/static) per STATIC_ROOT. No separate ./staticfiles -> public/ copy.
#    FAIL CLOSED (P3-1): collectstatic 产出 staticfiles.json（原名 → 哈希名），
#    生产用 BundledManifestStaticFilesStorage，运行期只认这份映射。它缺失时
#    {% static %} 只能退回未哈希 URL，而 public/static/ 里只有哈希文件名
#    → 全站资源 404。所以这里**不能**沿用旧的「WARNING 后继续」语义。
echo "=== [build.sh] Running collectstatic ==="
if ! python manage.py collectstatic --noinput 2>&1; then
    echo "  ERROR: collectstatic failed — aborting the build."
    echo "         Without staticfiles.json the hashed public/static/ assets"
    echo "         would be unreachable from every page (HTTP 404)."
    exit 1
fi
echo "  ✓ collectstatic OK"

# 2.3. Protected migrate — only when a REAL external DB is configured.
# In the stateless seed mode DATABASE_URL is empty or points at /tmp/ (Vercel
# runtime uses sqlite:///tmp/db.sqlite3), so we skip migrate there to avoid
# building tables that are never used / spurious errors. A genuine external
# DATABASE_URL (e.g. Neon/Supabase) triggers the migration.
if [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" != *"/tmp/"* ]]; then
  echo "=== [build.sh] Running migrate (external DB detected) ==="
  python manage.py migrate --noinput
fi

echo "=== [build.sh] Checking public/static/ ==="
if [ -d public/static ]; then
    echo "  public/static/ exists ✓"
    ls public/static/ 2>&1 | head -20
    echo "  Total files in public/static/: $(find public/static -type f | wc -l)"
else
    echo "  ERROR: public/static/ does NOT exist!"
    echo "  Contents of current dir:"
    ls -la
    exit 1
fi

echo "=== [build.sh] collectstatic done ==="

# 2.5. Generate the names-only static index (pages/static_index_data.py).
# Runtime image path resolution (pages/views/utils.py) needs to know which
# static files exist, but static/ + staticfiles/ are EXCLUDED from the Python
# function bundle (vercel.json -> functions.excludeFiles) because they are
# ~118 MB of assets already served by the edge CDN from public/static/.
# This step keeps that lookup working inside the Lambda.
#
# The SAME module also carries HASHED_FILES (copied from staticfiles.json).
# Production uses content-hashed static URLs; the manifest MUST be readable at
# runtime or every page 500s ("The file 'css/base.css' could not be found").
# staticfiles.json itself is excluded from the bundle, so the mapping has to
# travel as bundled Python source — see pages/storage.py.
# git-ignored, rebuilt on every deploy.
echo "=== [build.sh] Generating static index (pages/static_index_data.py) ==="
# --require-manifest = 严格模式（fail closed）：staticfiles.json 缺失或没有 paths
# 时以退出码 2 结束 → 构建立即失败。CI 走的是 `--root static` 的宽松模式，不受影响。
if ! python -m pages.static_index --root public/static --out pages/static_index_data.py --require-manifest 2>&1; then
    echo "  ERROR: static index generation failed — aborting the build."
    echo "         Runtime image/CSS resolution and hashed static URLs depend on it."
    exit 1
fi
echo "  ✓ pages/static_index_data.py generated"

# 3. Mirror staticfiles/* into public/static/*  (Vercel CDN auto-deploys public/)
echo "=== [build.sh] Verifying public/static/ contents ==="
# collectstatic already wrote the hashed assets directly into public/static
# (via VERCEL_STATIC_ROOT). This no-clobber merge is a safety net for any source
# file collectstatic might have skipped — normally a no-op (all already present).
if [ -d static ]; then
    cp -R -n static/* public/static/ 2>/dev/null || true
    echo "  ✓ Merged static/ -> public/static/ (no-clobber safety net)"
fi

# 4. Verify public/static/ has content
echo "=== [build.sh] Verifying public/static/ contents ==="
if [ -d public/static ]; then
    PUBLIC_FILE_COUNT=$(find public/static -type f | wc -l)
    echo "  Total files in public/static/: $PUBLIC_FILE_COUNT"

    if [ "$PUBLIC_FILE_COUNT" -eq 0 ]; then
        echo "  ✗ ERROR: public/static/ is EMPTY! Build will fail."
        exit 1
    fi
else
    echo "  ✗ ERROR: public/static/ does not exist!"
    exit 1
fi

# 5. Root favicon shortcut (browsers hit /favicon.ico directly)
if [ -f public/static/images/favicon.webp ]; then
    cp public/static/images/favicon.webp public/favicon.webp
    cp public/static/images/favicon.webp public/favicon.ico
    echo "  ✓ Copied favicon -> public/"
else
    echo "  ✗ WARNING: favicon.webp not found in public/static/images/"
fi

# 5.5. Root AI summary (llm.txt) — must be reachable at https://<domain>/llm.txt.
# public/ is Vercel's CDN root, and the filesystem hit takes precedence over the
# catch-all rewrite to Django, so a plain copy here is what makes it live.
# Source of truth is the repo-root llm.txt (do NOT put it in public/ — step 3
# does `rm -rf public`).
if [ -f llm.txt ]; then
    cp llm.txt public/llm.txt
    # B1 (SEO/GEO 2026-09): also publish the plural llm.txt convention name
    # (Jeremy Howard's llms.txt proposal). Some AI crawlers only recognise
    # /llms.txt, so copy the same source to both filenames.
    cp llm.txt public/llms.txt
    echo "  ✓ Copied llm.txt + llms.txt -> public/"
else
    echo "  ✗ WARNING: repo-root llm.txt not found — /llm.txt and /llms.txt will 404."
fi

# 6. Detailed listing for debugging
echo ""
echo "=== [build.sh] BUILD SUMMARY ==="
echo "  public/ top-level:"
ls public/ 2>&1 | head -15
echo ""
echo "  public/static/ top-level:"
ls public/static/ 2>&1 | head -15
echo ""
echo "  Image counts:"
echo "    Total images: $(find public/static/images -type f 2>/dev/null | wc -l)"
echo "    Products:     $(find public/static/images/products -type f 2>/dev/null | wc -l)"
echo "    Projects:     $(find public/static/images/projects -type f 2>/dev/null | wc -l)"
echo "    Processed:    $(find public/static/images/processed -type f 2>/dev/null | wc -l)"
echo "    PDFs:         $(find public/static/files -type f 2>/dev/null | wc -l)"

# 7. Translations — compile .po -> .mo at build time (non-fatal).
# Vercel ships NO GNU gettext, so Django's `compilemessages`/`msgfmt` fails there
# (2026-09-28 build log: "CommandError: Can't find msgfmt" silently swallowed by
# the old `|| true`). We compile with polib (pure-Python, declared in
# requirements.txt) so .mo always tracks .po even if a .po was edited without a
# local compile. A compile failure warns but does NOT abort the deploy — the site
# still renders (English fallback) without translations.
python - <<'PY'
import glob, os, sys, subprocess
PO_FILES = sorted(glob.glob("locale/*/LC_MESSAGES/*.po"))
if not PO_FILES:
    print("[build.sh] no .po files found — skipping translation compile")
    sys.exit(0)
try:
    import polib
except ImportError:
    print("[build.sh] polib missing — falling back to Django compilemessages")
    sys.exit(subprocess.call([sys.executable, "manage.py", "compilemessages"]))
ok = 0
fail = 0
for po in PO_FILES:
    mo = os.path.splitext(po)[0] + ".mo"
    try:
        polib.pofile(po).save_as_mofile(mo)
        ok += 1
    except Exception as e:  # noqa: BLE001 - non-fatal: warn, never abort deploy
        fail += 1
        print(f"[build.sh] WARN: failed to compile {po}: {e}")
print(f"[build.sh] compiled {ok} .po -> .mo via polib"
      + (f" ({fail} failed)" if fail else ""))
PY

# 8. Notify IndexNow (Bing / Yandex / Seznam / Naver) of the deployed URLs.
# Runs ONLY in the Vercel build env (VERCEL=1) so local/test builds don't ping
# Bing/Yandex on every dev run. Non-fatal: a transient IndexNow outage must NOT
# fail the deploy — search engines just fall back to their scheduled crawl.
# The key file is served at /<key>.txt by the Django view, and CANONICAL_ORIGIN
# defaults to the production domain, so no extra env is required here.
# seed_data.py is already regenerated above (step 1.5), so build_urls() sees the
# current product/project/news slug set at ping time.
if [ -n "$VERCEL" ]; then
  echo "=== [build.sh] Notifying IndexNow (Bing/Yandex/Seznam/Naver) ==="
  if python scripts/indexnow_ping.py --live 2>&1; then
    echo "  ✓ IndexNow notified of deployed URLs"
  else
    echo "  ⚠ WARNING: IndexNow ping failed (non-fatal) — search engines fall back to scheduled crawl."
  fi
else
  echo "=== [build.sh] Skipping IndexNow ping (not in Vercel build env) ==="
fi

echo ""
echo "=== [build.sh] ✅ FINISHED SUCCESSFULLY ==="