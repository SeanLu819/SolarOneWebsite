#!/bin/bash
pip install -r requirements.txt
export SECRET_KEY=build-time-placeholder
python manage.py collectstatic --noinput 2>&1
python manage.py compilemessages 2>&1
