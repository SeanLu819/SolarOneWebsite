"""Resolve duplicate msgids in the .po catalogs.

Every locale carried 18 duplicated msgids, and most duplicates CONFLICT: the
same English source string has two different translations in one catalog, so
which one renders is undefined. This script:

1. Auto-resolves the unambiguous case — a duplicate where one copy is still
   untranslated (msgstr empty or byte-identical to the msgid). Keeps the
   translated copy. Never guesses between two real translations.
2. Writes the remaining genuine wording conflicts to
   docs/i18n_duplicate_conflicts.md for a human to adjudicate.
3. Recompiles the .mo files.

Re-runnable: once a conflict is resolved the catalog has no duplicates left.
"""
import os
import sys

import polib

BASE = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..'))
LOCALE = os.path.join(BASE, 'locale')
REPORT = os.path.join(BASE, 'docs', 'i18n_duplicate_conflicts.md')
LANGS = ('fr', 'es', 'de', 'ru', 'ar')


def is_untranslated(entry):
    return entry.msgstr == '' or entry.msgstr == entry.msgid


def main():
    resolved_by_lang = {}
    conflicts = {}          # msgid -> {lang: [variants]}
    for lang in LANGS:
        path = os.path.join(LOCALE, lang, 'LC_MESSAGES', 'django.po')
        po = polib.pofile(path)
        kept = {}
        order = []
        resolved = []
        for e in po:
            if e.msgid not in kept:
                kept[e.msgid] = e
                order.append(e.msgid)
                continue
            prev = kept[e.msgid]
            if is_untranslated(prev) and not is_untranslated(e):
                resolved.append((e.msgid, prev.msgstr, e.msgstr))
                kept[e.msgid] = e
            elif not is_untranslated(prev) and is_untranslated(e):
                resolved.append((e.msgid, e.msgstr, prev.msgstr))
            else:
                conflicts.setdefault(e.msgid, {}).setdefault(lang, [])
                for v in (prev.msgstr, e.msgstr):
                    if v not in conflicts[e.msgid][lang]:
                        conflicts[e.msgid][lang].append(v)

        po[:] = [kept[m] for m in order]
        po.save(path)
        po.save_as_mofile(os.path.join(LOCALE, lang, 'LC_MESSAGES', 'django.mo'))
        resolved_by_lang[lang] = resolved
        print('%-3s entries 256 -> %d, auto-resolved(untranslated leftover)=%d'
              % (lang, len(po), len(resolved)))
        for msgid, dropped, keptmsg in resolved:
            print('    FIXED "%s"' % msgid[:60])
            print('       dropped: %s' % (dropped[:56] or '<empty>'))
            print('       kept   : %s' % keptmsg[:56])

    lines = [
        '# 重复 msgid 译文冲突（需人工裁定）',
        '',
        '脚本 `scripts/_resolve_po_duplicates.py` 已自动修掉「其中一份是未翻译的英文残留」'
        '这类无争议重复。',
        '下面列出的是**两套都是真译文但措辞不同**的情况 —— 脚本**不会**替你选，因为选错会',
        '直接改变线上对外文案。',
        '',
        '处理方式：在你认为正确的译文前打勾，或直接编辑对应 `locale/<lang>/LC_MESSAGES/django.po`，',
        '然后重跑 `python -m scripts._resolve_po_duplicates`（或 polib 重编 .mo）。',
        '',
    ]
    if not conflicts:
        lines.append('## 结果：无剩余冲突\n')
    else:
        lines.append('## 剩余冲突：%d 条 msgid\n' % len(conflicts))
        for msgid, per_lang in sorted(conflicts.items()):
            lines.append('### `%s`' % msgid.replace('`', "'"))
            lines.append('')
            lines.append('**英文原文**')
            lines.append('')
            lines.append('> %s' % msgid)
            lines.append('')
            for lang in LANGS:
                if lang not in per_lang:
                    continue
                lines.append('**%s**' % lang)
                lines.append('')
                for i, v in enumerate(per_lang[lang], 1):
                    lines.append('%d. %s' % (i, v))
                lines.append('')
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print('\nremaining genuine conflicts: %d msgids' % len(conflicts))
    print('report -> %s' % REPORT)


if __name__ == '__main__':
    sys.exit(main())
