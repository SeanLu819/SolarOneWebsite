import hashlib
from pathlib import Path
import urllib.request

pairs=[
    ('staticfiles/images/projects/football-field-led-retrofit/new led lighting.webp','http://localhost:8000/static/images/projects/football-field-led-retrofit/new%20led%20lighting.webp'),
    ('staticfiles/images/projects/football-field-led-retrofit/old hid lighting.webp','http://localhost:8000/static/images/projects/football-field-led-retrofit/old%20hid%20lighting.webp')
]
for disk, url in pairs:
    p=Path(disk)
    if p.exists():
        db=p.read_bytes()
        dh=hashlib.sha256(db).hexdigest()
        print(f"DISK:{disk}:{len(db)}:{dh}")
    else:
        print(f"DISK:{disk}:MISSING")
    try:
        data=urllib.request.urlopen(url,timeout=5).read()
        uh=hashlib.sha256(data).hexdigest()
        print(f"URL :{url}:{len(data)}:{uh}")
    except Exception as e:
        print(f"URL :{url}:ERROR:{e}")
