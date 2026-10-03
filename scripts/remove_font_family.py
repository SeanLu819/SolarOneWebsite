"""从 fonts.css 移除指定的 @font-face 块，并删除对应字体文件。

为什么需要脚本：`fonts.css` 有 52 个 @font-face，手工编辑容易漏删 url()
或破坏块结构。Space Grotesk 的 9 个 face 自 v1.6.3 起无任何渲染栈引用，
删掉可省 156 KB 仓库体积 + collectstatic 拷贝时间。

🔴 安全前提（调用方必须先验证）：
  1. 该 family 不在任何 --ff-* 渲染栈里（base.css /内联 critical CSS / SiteConfig）。
  2. 该 family 不被任何模板/JS 的 style 属性引用。
本脚本会自己再查一遍 base.css 与 base.html，查到就拒绝执行。

用法：
    E:/Python/python3/python.exe scripts/remove_font_family.py --family "Space Grotesk" --apply
"""
import argparse
import os
import re
import sys

FONTS_CSS = os.path.join('static', 'css', 'fonts.css')
FONTS_DIR = os.path.join('static', 'fonts')
BASE_CSS = os.path.join('static', 'css', 'base.css')
BASE_HTML = os.path.join('templates', 'base.html')
SEED_JSON = 'seed_data.json'


def _read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


def _render_stack_sources():
    """所有可能声明 font-family 的地方。"""
    return [BASE_CSS, BASE_HTML, SEED_JSON]


def _assert_unused(family):
    """确认 family 不在任何渲染路径上。"""
    hits = []
    for path in _render_stack_sources():
        if not os.path.exists(path):
            continue
        text = _read(path)
        if family not in text:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if family in line:
                hits.append(f'{path}:{i}: {line.strip()[:110]}')
    # fonts.css 自身的 @font-face 声明不算引用
    if hits:
        print(f'拒绝执行 —— {family} 仍被引用：')
        for h in hits:
            print('   ', h)
        return False
    return True


def _split_faces(css):
    """返回 [(前置文本, @font-face 块全文, 该块内的 url 文件名)]。"""
    out = []
    pos = 0
    for m in re.finditer(r'@font-face\s*\{', css):
        start = m.start()
        # 找配对的 }
        depth = 0
        i = m.end() - 1
        while i < len(css):
            if css[i] == '{':
                depth += 1
            elif css[i] == '}':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        block = css[start:i + 1]
        url = re.search(r'url\(\.\./fonts/([^)]+)\)', block)
        out.append((css[pos:start], block, url.group(1) if url else None))
        pos = i + 1
    out.append((css[pos:], '', None))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--family', required=True)
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    if not _assert_unused(args.family):
        return 1

    css = _read(FONTS_CSS)
    pieces = _split_faces(css)

    kept = []
    removed_files = []
    for prefix, block, fname in pieces:
        if block and f"font-family: '{args.family}'" in block:
            removed_files.append(fname)
            continue
        kept.append(prefix if not block else prefix + block)
    new_css = ''.join(kept)

    # 校验：删完后不得残留该family 的任何痕迹
    assert args.family not in new_css, '删除后 fonts.css 仍有残留'

    before = len(pieces) - 1
    print(f'@font-face: {before} -> {before - len(removed_files)}')
    print(f'将删除字体文件 {len(removed_files)} 个:')
    total = 0
    for f in removed_files:
        p = os.path.join(FONTS_DIR, f)
        sz = os.path.getsize(p) if os.path.exists(p) else 0
        total += sz
        print(f'    {sz/1024:6.1f} KB  {f}')
    print(f'合计 {total/1024:.0f} KB')

    if not args.apply:
        print('\n[dry-run] 未写入。加 --apply 执行。')
        return 0

    with open(FONTS_CSS, 'w', encoding='utf-8', newline='') as fh:
        fh.write(new_css)
    for f in removed_files:
        p = os.path.join(FONTS_DIR, f)
        if os.path.exists(p):
            os.remove(p)
    print(f'\n[apply] fonts.css 已更新，{len(removed_files)} 个字体文件已删除。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
