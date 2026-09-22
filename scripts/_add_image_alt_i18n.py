#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Add the image-`alt` strings (image SEO change) to every non-English catalog
and recompile the .mo files.

The i18n guard (``I18nCatalogGuardTests``) checks the compiled ``.mo``, not the
``.po`` — so *both* the ``.po`` and ``.mo`` must be written, and both are
git-tracked. This mirrors ``scripts/_add_404_i18n.py``: patch in place with
polib (never regenerate the 248-entry catalogs from scratch) and stay
idempotent so re-running is a no-op.

New msgids (deliberately lower-case first letter so they read as a phrase
fragment after the product name, e.g. "M Series — ordering information"):

  * ``ordering information``  — product_detail.html ordering-table image alt
  * ``Old HID lighting``      — project_detail.html before/after compare alt
  * ``New LED lighting``      — project_detail.html before/after compare alt
"""
from pathlib import Path
import polib

ROOT = Path(r'E:/Python/PROJECT/website')
LOCALES = ['fr', 'es', 'de', 'ru', 'ar']

TRANSLATIONS = {
    "ordering information": {
        'fr': "informations de commande",
        'es': "información de pedido",
        'de': "Bestellinformationen",
        'ru': "информация для заказа",
        'ar': "معلومات الطلب",
    },
    "Old HID lighting": {
        'fr': "ancien éclairage HID",
        'es': "iluminación HID antigua",
        'de': "alte HID-Beleuchtung",
        'ru': "старое освещение HID",
        'ar': "إضاءة HID القديمة",
    },
    "New LED lighting": {
        'fr': "nouvel éclairage LED",
        'es': "nueva iluminación LED",
        'de': "neue LED-Beleuchtung",
        'ru': "новое светодиодное освещение",
        'ar': "إضاءة LED الجديدة",
    },
}

for lang in LOCALES:
    po_path = ROOT / 'locale' / lang / 'LC_MESSAGES' / 'django.po'
    mo_path = ROOT / 'locale' / lang / 'LC_MESSAGES' / 'django.mo'
    po = polib.pofile(str(po_path))
    added = updated = 0
    for msgid, per_lang in TRANSLATIONS.items():
        msgstr = per_lang[lang]
        entry = po.find(msgid)
        if entry is None:
            po.append(polib.POEntry(msgid=msgid, msgstr=msgstr))
            added += 1
        elif not entry.translated():
            entry.msgstr = msgstr
            updated += 1
    po.save(str(po_path))
    po.save_as_mofile(str(mo_path))
    print(f'{lang}: +{added} added, {updated} filled  '
          f'({po_path.name} + {mo_path.name} written)')

print('done')
