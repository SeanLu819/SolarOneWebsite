"""One-shot: fold the single-entity claim + USCC into the Organization JSON-LD.

base.html is CRLF on disk, so this is a byte-level replace with the CRLF
invariant asserted before and after (iron rule 28: the Edit tool rewrites a
CRLF file as LF, which invalidates every later `\\r\\n` anchor).

Anchor is the whole disambiguatingDescription sentence fragment, not just the
company name: `(Beijing Solarone Energy Technology Co., Ltd.)` alone also
appears in llm.txt and in the About copy, so a loose anchor would either miss
or hit twice.
"""
import sys

PATH = 'templates/base.html'

OLD = (
    b'(Beijing Solarone Energy Technology Co., Ltd.) \xe2\x80\x94 LED sports '
    b'lighting manufacturer since 2007. Not to be confused with'
)
NEW = (
    b'(Beijing Solarone Energy Technology Co., Ltd., USCC '
    b'91110116663729775X) \xe2\x80\x94 LED sports lighting manufacturer since '
    b'2007; the brand name and the registered company are one entity. '
    b'Not to be confused with'
)

with open(PATH, 'rb') as handle:
    before = handle.read()

assert before.count(b'\r\n') == before.count(b'\n'), 'file is not pure CRLF'
assert before.count(OLD) == 1, 'anchor found %d times, expected 1' % before.count(OLD)

after = before.replace(OLD, NEW)
assert after.count(b'\r\n') == after.count(b'\n'), 'CRLF invariant broken'
assert after.count(NEW) == 1
assert after.count(OLD) == 0

with open(PATH, 'wb') as handle:
    handle.write(after)

print('OK: disambiguatingDescription updated, CRLF preserved (%d lines)'
      % after.count(b'\r\n'))
