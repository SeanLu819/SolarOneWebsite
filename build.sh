#!/bin/bash
# Vercel build script
# Key strategy: Vercel AUTOMATICALLY deploys the ./public/ directory as a CDN
# static root (files in public/foo.bar served at https://domain/foo.bar).
# So after Django collectstatic writes to ./staticfiles, we mirror the output
# into ./public/static/. This way /static/* is served FIRST by Vercel's global
# edge CDN — no Python Lambda coldstart, no WhiteNoise needed for plain assets.
# WhiteNoise + the route fallback in index.py are retained as safety nets.
#
# CRITICAL: vercel.json must include { "handle": "filesystem" } as the FIRST
# route so that Vercel checks public/ before falling through to index.py.

set -e
set -o pipefail
echo "=== [build.sh] Starting ==="

# 1. Install Python deps — prefer uv (pre-installed on Vercel, much faster),
#    fall back to pip with --break-system-packages, then plain pip.
export SECRET_KEY=build-time-placeholder
set +e
uv pip install -r requirements.txt 2>/dev/null
if [ $? -ne 0 ]; then
    pip install --break-system-packages -r requirements.txt 2>/dev/null
    if [ $? -ne 0 ]; then
        pip install -r requirements.txt
    fi
fi
set -e
echo "=== [build.sh] pip install done ==="

# 2. Run Django collectstatic -> outputs to ./staticfiles per STATIC_ROOT
python manage.py collectstatic --noinput 2>&1 | tail -5
echo "=== [build.sh] collectstatic done ==="

# 3. Mirror staticfiles/* into public/static/*  (Vercel CDN auto-deploys public/)
#    Also copy static/* source directly (includes non-collected content like
#    media/ files copied by post_save signals) to ensure nothing is missed.
echo "=== [build.sh] Syncing static -> public/static for Vercel CDN ==="
rm -rf public
mkdir -p public

# Ensure public/static contains everything Django collected
if [ -d staticfiles ]; then
    cp -R staticfiles public/static
    echo "  Copied staticfiles/ -> public/static/"
fi

# Merge anything in source static/ that collectstatic may have skipped
# (e.g. new content not yet in staticfiles, static/media uploads)
if [ -d static ]; then
    # use cp -n (no clobber) so collectstatic versions win conflicts
    cp -R -n static/* public/static/ 2>/dev/null || true
    echo "  Merged static/ -> public/static/ (no-clobber)"
fi

# 4. Root favicon shortcut (browsers hit /favicon.ico directly)
if [ -f public/static/images/favicon.webp ]; then
    cp public/static/images/favicon.webp public/favicon.webp
    cp public/static/images/favicon.webp public/favicon.ico
    echo "  Copied favicon.webp -> public/favicon.webp + public/favicon.ico"
fi

# 5. List contents so we can confirm in Vercel build log
echo "=== [build.sh] public/ top-level ==="
ls public/ 2>&1 | head -20
echo "=== [build.sh] public/static top-level ==="
ls public/static 2>&1 | head -20
echo "=== [build.sh] public/static/images count ==="
find public/static/images -type f 2>/dev/null | wc -l
echo "=== [build.sh] public/static/images/products count ==="
find public/static/images/products -type f 2>/dev/null | wc -l
echo "=== [build.sh] public/static/images/projects count ==="
find public/static/images/projects -type f 2>/dev/null | wc -l
echo "=== [build.sh] public/static/files (PDFs) ==="
ls public/static/files 2>/dev/null

# 6. Translations (non-fatal — .mo files already committed in repo)
python manage.py compilemessages 2>&1 || true
echo "=== [build.sh] FINISHED ==="