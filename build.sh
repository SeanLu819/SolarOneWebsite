#!/bin/bash
# Vercel build script — collect static assets and compile translations
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py compilemessages
