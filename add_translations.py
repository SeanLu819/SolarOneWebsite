"""Add missing translations to all .po files and compile them."""
import polib

LOCALE_DIR = r'e:\Python\PROJECT\website\locale'

# Translations for "Since 2007"
SINCE_2007 = {
    'fr': 'Depuis 2007',
    'es': 'Desde 2007',
    'de': 'Seit 2007',
    'ru': 'С 2007 года',
    'ar': 'منذ 2007',
}

for lang, translation in SINCE_2007.items():
    po_path = f'{LOCALE_DIR}\\{lang}\\LC_MESSAGES\\django.po'
    try:
        po = polib.pofile(po_path)
        # Check if entry already exists
        existing = po.find('Since 2007')
        if existing:
            existing.msgstr = translation
            print(f'  Updated "Since 2007" in {lang}')
        else:
            entry = polib.POEntry(msgid='Since 2007', msgstr=translation)
            po.append(entry)
            print(f'  Added "Since 2007" to {lang}')
        po.save(po_path)
        # Compile to .mo
        mo_path = po_path.replace('.po', '.mo')
        po.save_as_mofile(mo_path)
        print(f'  Compiled {lang}.mo')
    except FileNotFoundError:
        print(f'  WARNING: {po_path} not found')

print('\nDone!')
