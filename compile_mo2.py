"""Compile .mo files using Python's built-in gettext.GNUTranslations"""
import gettext
import os

LOCALE_DIR = r'e:\Python\PROJECT\website\locale'
langs = ['fr', 'es', 'de', 'ru', 'ar']

for lang in langs:
    po_path = os.path.join(LOCALE_DIR, lang, 'LC_MESSAGES', 'django.po')
    mo_path = po_path.replace('.po', '.mo')
    if os.path.exists(po_path):
        with open(po_path, 'rb') as f:
            po_content = f.read()
        
        # Parse the .po file manually and create .mo
        # Use polib to parse, then write with gettext module format
        import polib
        po = polib.pofile(po_path)
        
        # Remove old .mo
        if os.path.exists(mo_path):
            os.remove(mo_path)
        
        # Write .mo using polib (which uses Python's struct module for binary format)
        po.save_as_mofile(mo_path)
        
        # Verify the .mo file is valid
        with open(mo_path, 'rb') as f:
            magic = f.read(4)
            # Check MO magic number (0x950412de for big-endian or 0xde120495 for little-endian)
            if magic in (b'\x95\x04\x12\xde', b'\xde\x12\x04\x95'):
                print(f'{lang}: Valid .mo file created ({os.path.getsize(mo_path)} bytes)')
            else:
                print(f'{lang}: WARNING - Invalid magic number: {magic.hex()}')
    else:
        print(f'{lang}: {po_path} not found')

# Now test loading the .mo file
print("\nTesting .mo loading:")
import polib
mo = polib.mofile(os.path.join(LOCALE_DIR, 'fr', 'LC_MESSAGES', 'django.mo'))
for entry in mo:
    if 'Higher light' in entry.msgid or 'Proprietary glass' in entry.msgid:
        print(f"  {entry.msgid[:50]}...")
        print(f"  -> {entry.msgstr[:50]}...")
