@echo off
echo === Rebuilding Database ===

echo Step 1: Deleting old database...
if exist db.sqlite3 (
    del db.sqlite3
    echo Database deleted.
) else (
    echo No database file found.
)

echo Step 2: Running migrations...
python manage.py migrate

echo Step 3: Loading seed data...
python manage.py loaddata seed_data.json

echo === Done! ===
pause