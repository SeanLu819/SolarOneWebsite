"""Per-block analysis: SolarOne mention, own-site citation, competitors, spec claims."""
import json
import re

doc = open('.cgpt_share_tmp.html', encoding='utf-8', errors='replace').read()
seg = doc.replace('\\"', '"').replace('\\n', '\n').replace('\\/', '/')
blocks = [(m.start(), m.end()) for m in re.finditer(r'DIL\.render\(', seg)]

# question anchors in doc order (reverse chronological)
anchors = [
    ('X3', 519845), ('X1', 573693), ('S1', 603249), ('L3', 639935), ('L2', 672233),
    ('L1', 690000), ('C6', 737129), ('C5', 762618), ('C3', 850691), ('C2', 910988),
    ('C1', 1017504), ('B2', 1046065), ('B1', 1060047),
]

def block_text(s, e):
    body = seg[s:e]
    strs = re.findall(r'"((?:[^"\\]|\\.){10,3000})"', body)
    out = []
    for x in strs:
        if x.startswith(('http', 'function', '__dil', 'text', 'size', 'color', 'gap', 'align', 'block', 'inline')):
            continue
        x = x.replace('\\n', '\n').replace('\\"', '"')
        if re.search(r'[A-Za-z]{3,}\s+[a-z]{2,}', x) or re.search(r'[\u0600-\u06FF\u0400-\u04FF\u00C0-\u024F]{4,}', x):
            out.append(x)
    return out

print('=== per-answer SolarOne facts ===')
for i, (s, e) in enumerate(blocks):
    nxt = blocks[i + 1][0] if i + 1 < len(blocks) else min(len(seg), s + 45000)
    body = seg[e:nxt]
    # which question does this block answer? (block sits BEFORE its question in reverse order)
    q = next((qid for qid, pos in anchors if pos > s), '?')
    texts = block_text(e, nxt)
    full = '\n'.join(texts)
    solar = len(re.findall(r'SolarOne', full, re.I))
    own_urls = sorted(set(re.findall(r'solaronelighting\.com[^\s"<>\)\]\\]*', full)))
    comps = sorted(set(re.findall(r'\b(Musco|Signify|Philips|HISHINE|Hishine|SCL|Seven Continents|ZGSM|RC Lighting|Ephesus|Sportsbeams|Cooper|LEDone|Ledvance|VEGA|CHZ)\b', full)))
    print(f'--- block {i} (answers {q}) | SolarOne x{solar} | comps: {comps}')
    if own_urls:
        print(f'    own URLs: {own_urls[:4]}')
    # first meaningful line
    if texts:
        print(f'    head: {texts[0][:130]}')
