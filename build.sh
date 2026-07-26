#!/bin/bash
# Vercel's build environment uses uv-managed Python (PEP 668), which blocks
# direct `pip install`. The --break-system-packages flag overrides this and
# installs into the system Python (3.12+), which satisfies Django 6.0's
# requirement. Do NOT use `uv pip install` — it defaults to Python 3.9.
pip install --break-system-packages -r requirements.txt

export SECRET_KEY=build-time-placeholder
python manage.py collectstatic --noinput 2>&1
# compilemessages requires GNU gettext (msgfmt) which is not available in
# Vercel's build environment. Make it non-fatal — pre-compiled .mo files
# are committed to the repo, so runtime translations work without recompiling.
python manage.py compilemessages 2>&1 || true
