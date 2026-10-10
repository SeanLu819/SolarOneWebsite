"""Guard: the contact page must render the CURRENT headquarters address.

2026-10-08 relocation: Changping (Xisha Industrial Park) -> Shunyi (Jinma
Industrial Park). The address is a gettext literal in ``contact.html``; the
msgid was re-keyed in all six locales in the same batch (a changed msgid
orphans every translation -- i18n iron rule), so this guard asserts the
RENDERED value per language, not the template source.

* the localized new address must appear on /contact/ in all six languages;
* any trace of the old address (Xisha / Beiqijia / Changping) must be gone.
"""
from django.test import Client, TestCase

#: lang -> the exact localized address the page must render. Literal: an
#: address is an independent product decision, not something to derive.
EXPECTED = {
    'en': 'No. 7 Jinyi Street, Jinma Industrial Park, Gaoliying Town, '
          'Shunyi District, Beijing 101300, China',
    'de': 'Nr. 7 Jinyi-Straße, Jinma Industriepark, Gemeinde Gaoliying, '
          'Bezirk Shunyi, Peking 101300, China',
    'fr': 'N° 7 rue Jinyi, parc industriel de Jinma, ville de Gaoliying, '
          'district de Shunyi, Pékin 101300, Chine',
    'es': 'N.º 7 calle Jinyi, parque industrial de Jinma, pueblo de '
          'Gaoliying, distrito de Shunyi, Pekín 101300, China',
    'ru': '№ 7 ул. Цзиньи, промышленный парк Цзиньма, г. Гаолиин, '
          'р-н Шуньи, Пекин 101300, Китай',
    'ar': 'رقم 7 شارع جين يي، مدينة جينما الصناعية، بلدة قاوليينغ، '
          'منطقة شون يي، بكين 101300، الصين',
}

#: Any of these in a rendered contact page means the old Changping address
#: is back (msgid drift, stale .mo, or a reverted template).
OLD_ADDRESS_MARKERS = ('Xisha', 'Beiqijia', 'Changping')


class ContactAddressTests(TestCase):
    #: en lives at the bare path (no /en/ prefix); the other five are prefixed.
    PATHS = {'en': '/contact/', 'de': '/de/contact/', 'fr': '/fr/contact/',
             'es': '/es/contact/', 'ru': '/ru/contact/', 'ar': '/ar/contact/'}

    def _body(self, lang):
        resp = Client().get(self.PATHS[lang], HTTP_HOST='localhost')
        self.assertEqual(resp.status_code, 200)
        return resp.content.decode()

    def test_contact_page_renders_the_new_address_in_every_language(self):
        for lang, expected in sorted(EXPECTED.items()):
            with self.subTest(lang=lang):
                body = self._body(lang)
                self.assertIn(expected, body,
                              '%s contact page does not render the new '
                              'Shunyi address' % lang)

    def test_the_old_changping_address_is_gone_everywhere(self):
        for lang in sorted(EXPECTED):
            with self.subTest(lang=lang):
                body = self._body(lang)
                for marker in OLD_ADDRESS_MARKERS:
                    self.assertNotIn(
                        marker, body,
                        '%s contact page still shows the old Changping '
                        'address (%s)' % (lang, marker))
