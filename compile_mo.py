"""Recompile all .mo files from .po files."""
import polib

LOCALE_DIR = r'e:\Python\PROJECT\website\locale'
langs = ['fr', 'es', 'de', 'ru', 'ar']

for lang in langs:
    po_path = f'{LOCALE_DIR}\\{lang}\\LC_MESSAGES\\django.po'
    mo_path = po_path.replace('.po', '.mo')
    try:
        po = polib.pofile(po_path)
        po.save_as_mofile(mo_path)
        print(f'Compiled {lang}.mo ({len(po)} entries)')
    except FileNotFoundError:
        print(f'WARNING: {po_path} not found')

print('\nDone!')
