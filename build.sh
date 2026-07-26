#!/bin/bash
# Vercel's build environment now uses uv-managed Python (PEP 668), which
# blocks direct `pip install`. Prefer `uv pip install`; fall back to
# `pip install --break-system-packages` if uv is not on PATH.
if command -v uv >/dev/null 2>&1; then
    uv pip install --system -r requirements.txt
else
    pip install --break-system-packages -r requirements.txt
fi

export SECRET_KEY=build-time-placeholder
python manage.py collectstatic --noinput 2>&1
# compilemessages requires GNU gettext (msgfmt) which is not available in
# Vercel's build environment. Make it non-fatal — Django falls back to
# source-language strings when .mo files are absent.
python manage.py compilemessages 2>&1 || true
