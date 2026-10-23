"""Per-query own-site citation check + competitor list + SolarOne context lines."""
import re

doc = open('.cgpt_share_tmp.html', encoding='utf-8', errors='replace').read()
seg = doc.replace('\\"', '"').replace('\\n', '\n').replace('\\/', '/')
blocks = [(m.start(), m.end()) for m in re.finditer(r'DIL\.render\(', seg)]

mapping = [
    ('B1', [15]), ('B2', [14]), ('C1', [13]), ('C2', [11, 12]), ('C3', [10]),
    ('C5', [7]), ('followup', [8, 9]), ('C6', [6]),
    ('L1', [5]), ('L2', [4]), ('L3', [3]), ('S1', [2]), ('X1', [1]), ('X3', [0]),
]

for qid, idxs in mapping:
    own_urls = []
    solar_lines = []
    for i in idxs:
        s, e = blocks[i]
        nxt = blocks[i + 1][0] if i + 1 < len(blocks) else min(len(seg), s + 45000)
        body = seg[e:nxt]
        own_urls += re.findall(r'https?://(?:www\.)?solaronelighting\.com[^\s"<>\)\]\\,\}]*', body)
        strs = re.findall(r'"((?:[^"\\]|\\.){10,2000})"', body)
        for x in strs:
            if x.startswith(('http', 'function', '__dil')):
                continue
            t = x.replace('\\n', ' ').replace('\\"', '"')
            if 'SolarOne' in t and len(t) > 30:
                solar_lines.append(t)
    uniq = sorted(set(u.rstrip('.,') for u in own_urls))
    print(f'=== {qid} ===')
    print('  own URLs cited: %d' % len(uniq))
    for u in uniq[:6]:
        print('    ', u[:110])
    print('  SolarOne lines: %d' % len(solar_lines))
    for t in solar_lines[:3]:
        print('     *', t[:170])
    print()
