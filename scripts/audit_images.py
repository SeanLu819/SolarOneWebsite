"""全站图片扫描器 —— 只读，绝不修改任何文件。

输出 JSON 到 .workbuddy/preview/image_audit.json，并打印人读报告。
涵盖：字节/尺寸/宽高比/格式/alpha/重复内容(md5)/引用位置(seed + 模板)/命名与目录语义。
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
from collections import defaultdict

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_IMAGES = os.path.join(ROOT, 'static', 'images')
SEED_JSON = os.path.join(ROOT, 'seed_data.json')
OUT_JSON = os.path.join(ROOT, '.workbuddy', 'preview', 'image_audit.json')
SKIP_DIR_PARTS = {'_source'}

IMAGE_EXTS = {'.webp', '.jpg', '.jpeg', '.png', '.gif', '.avif'}


def _md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _fmt_ratio(w: int, h: int) -> str:
    from math import gcd
    g = gcd(w, h) or 1
    return f'{w // g}:{h // g}'


def scan_files() -> list[dict]:
    rows = []
    for dirpath, dirnames, filenames in os.walk(STATIC_IMAGES):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in IMAGE_EXTS:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, os.path.join(ROOT, 'static')).replace('\\', '/')
            rec = {
                'rel': rel,
                'name': fn,
                'ext': ext.lstrip('.'),
                'dir': os.path.relpath(dirpath, STATIC_IMAGES).replace('\\', '/'),
                'bytes': os.path.getsize(full),
                'md5': None,
                'width': None,
                'height': None,
                'ratio': None,
                'mode': None,
                'has_alpha': None,
                'error': None,
            }
            try:
                rec['md5'] = _md5(full)
                with Image.open(full) as im:
                    rec['width'], rec['height'] = im.size
                    rec['mode'] = im.mode
                    rec['has_alpha'] = im.mode in ('RGBA', 'LA') or (
                        im.mode == 'P' and 'transparency' in im.info)
                rec['ratio'] = _fmt_ratio(rec['width'], rec['height'])
            except Exception as exc:  # noqa: BLE001
                rec['error'] = f'{type(exc).__name__}: {exc}'
            rows.append(rec)
    rows.sort(key=lambda r: -r['bytes'])
    return rows


def load_seed() -> dict:
    if not os.path.exists(SEED_JSON):
        return {}
    with io.open(SEED_JSON, encoding='utf-8') as fh:
        return json.load(fh)


def build_index(seed: dict) -> tuple[dict, list[dict]]:
    """路径片段 -> [{kind, slug, field, index}]，并记录 seed 中出现的所有图片路径。"""
    idx: dict[str, list[dict]] = defaultdict(list)
    problems: list[dict] = []

    def walk(node, trail):
        if isinstance(node, dict):
            for k, v in node.items():
                walk(v, trail + [str(k)])
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, trail + [str(i)])
        elif isinstance(node, str):
            if '/images/' in node or node.startswith('images/'):
                # 规范化：取最后两段作为匹配键（目录/文件名）
                norm = node.split('?')[0]
                idx[norm].append({'trail': '/'.join(trail)})

    walk(seed, [])

    # 也建立 basename -> refs 便于宽松匹配
    by_name: dict[str, list[dict]] = defaultdict(list)
    for path, refs in idx.items():
        by_name[os.path.basename(path)].extend(refs)
    return idx, by_name, problems


def find_refs(rel: str, exact: dict, by_name: dict) -> list[str]:
    """rel形如 images/products/slug/file.webp"""
    hits = []
    if rel in exact:
        hits += [r['trail'] for r in exact[rel]]
    base = os.path.basename(rel)
    if base in by_name:
        hits += [r['trail'] for r in by_name[base]]
    return sorted(set(hits))


def main() -> int:
    rows = scan_files()
    seed = load_seed()
    exact, by_name, _ = build_index(seed)

    for r in rows:
        r['refs'] = find_refs(r['rel'], exact, by_name)
        r['ref_count'] = len(r['refs'])

    # 重复内容分组
    by_md5: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r['md5']:
            by_md5[r['md5']].append(r)
    dup_groups = [
        {'md5': k, 'bytes_each': v[0]['bytes'], 'count': len(v),
         'wasted': v[0]['bytes'] * (len(v) - 1), 'files': [x['rel'] for x in v]}
        for k, v in by_md5.items() if len(v) > 1
    ]
    dup_groups.sort(key=lambda g: -g['wasted'])

    total = sum(r['bytes'] for r in rows)
    payload = {
        'totals': {
            'count': len(rows),
            'bytes': total,
            'mb': round(total / 1048576, 2),
            'webp': sum(1 for r in rows if r['ext'] == 'webp'),
            'non_webp': sum(1 for r in rows if r['ext'] != 'webp'),
            'unreadable': sum(1 for r in rows if r['error']),
            'dupe_bytes': sum(g['wasted'] for g in dup_groups),
            'unreferenced': sum(1 for r in rows if r['ref_count'] == 0),
            'unreferenced_bytes': sum(r['bytes'] for r in rows if r['ref_count'] == 0),
        },
        'files': rows,
        'dup_groups': dup_groups,
    }

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with io.open(OUT_JSON, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, indent=1))

    t = payload['totals']
    print('=== 全站图片扫描 ===')
    print('  总数 %d张/ %.2f MB  (webp %d, 非webp %d, 不可读 %d)' % (
        t['count'], t['mb'], t['webp'], t['non_webp'], t['unreadable']))
    print('  重复内容浪费: %.2f MB (%d 组)' % (
        t['dupe_bytes'] / 1048576, len(dup_groups)))
    print('  seed 未引用:%d 张 / %.2f MB' % (
        t['unreferenced'], t['unreferenced_bytes'] / 1048576))
    print('  → %s' % OUT_JSON)
    return 0


if __name__ == '__main__':
    sys.exit(main())