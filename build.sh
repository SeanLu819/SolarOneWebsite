#!/bin/bash
# Vercel build script
# Key strategy: Vercel AUTOMATICALLY deploys the ./public/ directory as a CDN
# static root (files in public/foo.bar served at https://domain/foo.bar).
# So after Django collectstatic writes to ./staticfiles, we mirror the output
# into ./public/static/. This way /static/* is served FIRST by Vercel's global
# edge CDN — no Python Lambda coldstart, no WhiteNoise needed for plain assets.
#
# CRITICAL: vercel.json must include { "handle": "filesystem" } as the FIRST
# route so that Vercel checks public/ before falling through to index.py.

set -e
set -o pipefail

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
    uv pip install -r requirements.txt 2>&1 | tail -10
    INSTALL_SUCCESS=$?
fi

if [ $INSTALL_SUCCESS -ne 0 ]; then
    echo "  Falling back to pip..."
    pip install --break-system-packages -r requirements.txt 2>&1 | tail -10
    INSTALL_SUCCESS=$?
fi

if [ $INSTALL_SUCCESS -ne 0 ]; then
    echo "  ERROR: Failed to install dependencies"
    exit 1
fi
set -e
echo "=== [build.sh] pip install done ==="

# 1.5. Regenerate seed_data.py from seed_data.json (Vercel only uses seed_data.py)
echo "=== [build.sh] Regenerating seed_data.py ==="
python regen_seed_data.py 2>&1

# 2. Run Django collectstatic -> outputs to ./staticfiles per STATIC_ROOT
echo "=== [build.sh] Running collectstatic ==="
python manage.py collectstatic --noinput 2>&1
COLLECTSTATIC_EXIT=$?
echo "  collectstatic exit code: $COLLECTSTATIC_EXIT"

if [ $COLLECTSTATIC_EXIT -ne 0 ]; then
    echo "  WARNING: collectstatic failed with exit code $COLLECTSTATIC_EXIT"
fi

echo "=== [build.sh] Checking staticfiles/ ==="
if [ -d staticfiles ]; then
    echo "  staticfiles/ exists ✓"
    ls staticfiles/ 2>&1 | head -20
    echo "  Total files in staticfiles/: $(find staticfiles -type f | wc -l)"
else
    echo "  ERROR: staticfiles/ does NOT exist!"
    echo "  Contents of current dir:"
    ls -la
    exit 1
fi

echo "=== [build.sh] collectstatic done ==="

# 3. Mirror staticfiles/* into public/static/*  (Vercel CDN auto-deploys public/)
echo "=== [build.sh] Creating public/ directory for Vercel CDN ==="
rm -rf public
mkdir -p public

# Ensure public/static contains everything Django collected
if [ -d staticfiles ]; then
    cp -R staticfiles public/static
    echo "  ✓ Copied staticfiles/ -> public/static/"
else
    echo "  ✗ WARNING: staticfiles/ not found, skipping copy"
fi

# Merge anything in source static/ that collectstatic may have skipped
if [ -d static ]; then
    cp -R -n static/* public/static/ 2>/dev/null || true
    echo "  ✓ Merged static/ -> public/static/ (no-clobber)"
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

# 7. Translations (non-fatal)
python manage.py compilemessages 2>&1 || true

echo ""
echo "=== [build.sh] ✅ FINISHED SUCCESSFULLY ==="