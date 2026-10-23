"""Dump full readable text of selected answer blocks."""
import re
import sys

doc = open('.cgpt_share_tmp.html', encoding='utf-8', errors='replace').read()
seg = doc.replace('\\"', '"').replace('\\n', '\n').replace('\\/', '/')
blocks = [(m.start(), m.end()) for m in re.finditer(r'DIL\.render\(', seg)]

want = [int(x) for x in sys.argv[1:]] or list(range(16))

for i, (s, e) in enumerate(blocks):
    if i not in want:
        continue
    nxt = blocks[i + 1][0] if i + 1 < len(blocks) else min(len(seg), s + 45000)
    body = seg[e:nxt]
    strs = re.findall(r'"((?:[^"\\]|\\.){8,3000})"', body)
    texts = []
    for x in strs:
        if x.startswith(('http', 'function', '__dil', 'text', 'size', 'color', 'gap',
                         'align', 'block', 'inline', 'header', 'secondary', 'primary')):
            continue
        x = x.replace('\\n', '\n').replace('\\"', '"')
        if re.search(r'[A-Za-z]{3,}\s+[a-z]{2,}', x) or re.search(r'[\u0600-\u06FF\u0400-\u04FF\u00C0-\u024F]{4,}', x):
            texts.append(x)
    print('=' * 70)
    print(f'BLOCK {i}')
    print('=' * 70)
    for t in texts:
        print(t[:600])
    print()
