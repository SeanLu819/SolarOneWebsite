#!/bin/bash
# Vercel's Python environment is now managed by uv (PEP 668), which blocks
# direct `pip install`. --break-system-packages lets the build proceed.
pip install --break-system-packages -r requirements.txt
export SECRET_KEY=build-time-placeholder
python manage.py collectstatic --noinput 2>&1
python manage.py compilemessages 2>&1
