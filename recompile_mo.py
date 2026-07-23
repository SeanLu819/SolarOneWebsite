"""Compile .mo files using Python's built-in gettext module instead of polib"""
import subprocess
import os

LOCALE_DIR = r'e:\Python\PROJECT\website\locale'
langs = ['fr', 'es', 'de', 'ru', 'ar']

for lang in langs:
    po_path = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'django.po')
    mo_path = po_path.replace('.po', '.mo')
    if os.path.exists(po_path):
        # Remove old .mo
        if os.path.exists(mo_path):
            os.remove(mo_path)
        # Use msgfmt if available, otherwise use polib
        try:
            result = subprocess.run(
                ['msgfmt', '-o', mo_path, po_path],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f'{lang}: Compiled with msgfmt')
            else:
                print(f'{lang}: msgfmt failed: {result.stderr}')
                # Fallback to polib
                import polib
                po = polib.pofile(po_path)
                po.save_as_mofile(mo_path)
                print(f'{lang}: Compiled with polib (fallback)')
        except FileNotFoundError:
            import polib
            po = polib.pofile(po_path)
            po.save_as_mofile(mo_path)
            print(f'{lang}: Compiled with polib (no msgfmt)')
    else:
        print(f'{lang}: {po_path} not found')
