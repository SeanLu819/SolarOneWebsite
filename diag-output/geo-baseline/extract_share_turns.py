"""Extract conversation messages with timestamps (pattern: [idx],"text", then look back for ts)."""
import json
import re
from datetime import datetime, timezone, timedelta

doc = open('.cgpt_share_tmp.html', encoding='utf-8', errors='replace').read()
seg = doc.replace('\\"', '"').replace('\\n', '\n').replace('\\/', '/')

msg_pat = re.compile(r'\[(\d+)\],"((?:[^"\\]|\\.)*?)"')
ts_pat = re.compile(r'(\d{10}\.\d+),\d{10}\.\d+')

msgs = []
for m in msg_pat.finditer(seg):
    idx = int(m.group(1))
    txt = m.group(2).replace('\\n', '\n')
    if len(txt.strip()) < 3:
        continue
    # nearest timestamp before this message
    before = seg[:m.start()]
    tss = ts_pat.findall(before)
    ts = float(tss[-1]) if tss else None
    msgs.append({'ts': ts, 'idx': idx, 'text': txt, 'pos': m.start()})

# keep the occurrence whose nearest ts is closest (dedupe by idx+text, keep first)
seen = set()
uniq = []
for x in msgs:
    key = (x['idx'], x['text'][:60])
    if key not in seen:
        seen.add(key)
        uniq.append(x)

tz = timezone(timedelta(hours=8))
print('messages: %d' % len(uniq))
print()
print('=== chronological order ===')
for x in sorted(uniq, key=lambda v: (v['ts'] or 0, v['idx'])):
    t = datetime.fromtimestamp(x['ts'], tz).strftime('%H:%M:%S') if x['ts'] else '--:--:--'
    print('  %s  [%5d]  %s' % (t, x['idx'], x['text'][:100].replace('\n', ' ')))

with open('.share_msgs.json', 'w', encoding='utf-8') as fh:
    json.dump(sorted(uniq, key=lambda v: (v['ts'] or 0)), fh, ensure_ascii=False, indent=1)
