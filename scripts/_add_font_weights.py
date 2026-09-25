#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""P0-3: 下载缺失的 Inter 500/700 + IBM Plex Mono 500/600 woff2 子集并追加 @font-face 到 fonts.css。

背景 (v1.6.3 P0 字体一致性):
  fonts.css (v1.6.1 #2) 只自托管了 Inter 400/600 与 IBM Plex Mono 400，但 base.css 大量使用
  font-weight:500 (标题/按钮/微标签) 与 700 (大数字)、mono 500/600 (按钮/侧栏头) —— 缺失字重
  由浏览器字体匹配算法回退 (500→400, 700→600, mono 600→400) 甚至合成粗体，跨 OS 渲染不一致。

做法:
  1. 以浏览器 UA 请求 Google Fonts css2 API（同一 UA 下才返回 woff2 + unicode-range 子集切分；
     构建期下载，运行时零第三方请求 —— 与 CSP font-src 'self' 不冲突）。
  2. 逐子集下载到 static/fonts/，命名沿用既有风格 inter-latin-500.woff2。
  3. 把对应 @font-face 块追加到 static/css/fonts.css（幂等：文件名已声明则跳过）。

用法:
    python scripts/_add_font_weights.py            # 下载 + 追加声明
    python scripts/_add_font_weights.py --dry-run  # 只打印将要做什么，不写任何文件
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FONTS_DIR = ROOT / 'static' / 'fonts'
FONTS_CSS = ROOT / 'static' / 'css' / 'fonts.css'

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
API = ('https://fonts.googleapis.com/css2'
       '?family=Inter:wght@500;700&family=IBM+Plex+Mono:wght@500;600&display=swap')

# (family, weight) 白名单；其余 (如 css2 兜底返回的 400) 一律忽略
WANT = {('Inter', '500'), ('Inter', '700'),
        ('IBM Plex Mono', '500'), ('IBM Plex Mono', '600')}
PREFIX = {'Inter': 'inter', 'IBM Plex Mono': 'ibm-plex-mono'}
# 与既有文件核对：Inter 7 子集 × 2 字重 + Plex Mono 5 子集 × 2 字重
EXPECTED_NEW_FACES = 24


def fetch(url: str, binary: bool = False):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return data if binary else data.decode('utf-8')


def main() -> int:
    dry = '--dry-run' in sys.argv
    css = fetch(API)
    # css2 输出形如: /* latin */\n@font-face { font-family: 'Inter'; ... }
    blocks = re.findall(r'/\*\s*([\w-]+)\s*\*/\s*@font-face\s*\{(.*?)\}', css, re.S)
    if not blocks:
        print('FAIL: css2 API returned no @font-face blocks (UA rejected?)')
        return 1

    existing = FONTS_CSS.read_text(encoding='utf-8') if FONTS_CSS.exists() else ''
    new_faces, downloaded, seen = [], 0, set()

    for subset, body in blocks:
        fam_m = re.search(r"font-family:\s*'([^']+)'", body)
        wt_m = re.search(r'font-weight:\s*(\d+)', body)
        url_m = re.search(r'url\((https://[^)]+?\.woff2)\)', body)
        ur_m = re.search(r'unicode-range:\s*([^;]+);', body)
        if not (fam_m and wt_m and url_m and ur_m):
            continue
        fam, weight = fam_m.group(1), wt_m.group(1)
        if (fam, weight) not in WANT:
            continue

        fname = f'{PREFIX[fam]}-{subset}-{weight}.woff2'
        key = (fam, weight, fname)
        if key in seen:
            continue
        seen.add(key)

        fpath = FONTS_DIR / fname
        if not dry and (not fpath.exists() or fpath.stat().st_size < 1000):
            data = fetch(url_m.group(1), binary=True)
            if data[:4] != b'wOF2':
                print(f'FAIL: {fname} is not woff2 (magic={data[:4]!r})')
                return 1
            fpath.write_bytes(data)
            downloaded += 1

        if f'../fonts/{fname}' not in existing:
            new_faces.append(
                "@font-face {\n"
                f"  font-family: '{fam}';\n"
                "  font-style: normal;\n"
                f"  font-weight: {weight};\n"
                "  font-display: swap;\n"
                f"  src: url(../fonts/{fname}) format('woff2');\n"
                f"  unicode-range: {ur_m.group(1).strip()};\n"
                "}\n"
            )

    print(f'faces_matched={len(seen)} files_downloaded={downloaded} '
          f'faces_to_append={len(new_faces)} (expected {EXPECTED_NEW_FACES} matched)')
    if len(seen) != EXPECTED_NEW_FACES:
        print('WARN: subset count differs from expectation — review before committing.')

    if dry:
        for face in new_faces:
            print('---- would append ----')
            print(face)
        return 0

    if new_faces:
        with FONTS_CSS.open('a', encoding='utf-8') as fh:
            fh.write('\n' + '\n'.join(new_faces))
        print(f'appended {len(new_faces)} @font-face blocks to {FONTS_CSS}')
    else:
        print('fonts.css already declares all target faces — nothing to append.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
