"""提取每个 <img> 位的 CSS 规则 —— 只读。
输出: 位 -> {容器最大宽度, object-fit, aspect-ratio, 是否会裁切}
"""
from __future__ import annotations
import io, re, glob, os, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, 'templates')
CSS_LIST = [os.path.join(ROOT, 'static', 'css', 'base.css')]

RULE_RE = re.compile(r'([^{}]+)\{([^{}]*)\}', re.S)


def load_css() -> str:
    parts = []
    for p in CSS_LIST:
        if os.path.exists(p):
            parts.append(io.open(p, encoding='utf-8').read())
    for p in glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True):
        for m in re.finditer(r'<style[^>]*>(.*?)</style>', io.open(p, encoding='utf-8').read(), re.S):
            parts.append('/* %s */\n%s' % (p, m.group(1)))
    return '\n'.join(parts)


def parse_rules(css: str) -> list[tuple[str, str]]:
    out = []
    for sel, body in RULE_RE.findall(css):
        sel = ' '.join(sel.split())
        if sel.startswith('@') or sel.startswith('/*'):
            continue
        out.append((sel, ' '.join(body.split())))
    return out


def props_for(rules, classes: list[str], tag_scope: str | None = None) -> dict:
    """合并所有命中该 class 的规则，后者覆盖前者（同优先级下靠后 = 更新）。"""
    acc = {}
    keys = ('width', 'max-width', 'height', 'object-fit', 'aspect-ratio',
            'object-position', 'padding-top', 'background')
    for sel, body in rules:
        if tag_scope and tag_scope not in sel:
            continue
        if any(('.' + c) in sel for c in classes):
            for decl in body.split(';'):
                if ':' not in decl:
                    continue
                k, v = decl.split(':', 1)
                k = k.strip()
                if k in keys:
                    acc[k] = v.strip()
    return acc


def main():
    css = load_css()
    rules = parse_rules(css)

    print('=== 图片位 CSS 规则（合并 class 命中）===\n')
    report = []
    for p in sorted(glob.glob(os.path.join(TPL, '**', '*.html'), recursive=True)):
        rel = os.path.relpath(p, TPL).replace('\\', '/')
        if rel.startswith('admin/'):
            continue
        lines = io.open(p, encoding='utf-8').read().split('\n')
        for i, ln in enumerate(lines):
            if '<img' not in ln:
                continue
            m_src = re.search(r'src="([^"]*)"', ln)
            m_cls = re.search(r'class="([^"]*)"', ln)
            src = m_src.group(1) if m_src else ''
            classes = (m_cls.group(1).split() if m_cls else [])
            acc = props_for(rules, classes)
            # 向上找最近的父容器 class（缩进更少 + class 更长）
            parent = ''
            for j in range(i - 1, max(-1, i - 12), -1):
                pm = re.search(r'class="([^"]*)"', lines[j])
                if pm and lines[j].strip().startswith('<div'):
                    parent = pm.group(1)
                    break
            parent_props = props_for(rules, parent.split()) if parent else {}
            report.append({
                'tpl': rel, 'line': i + 1, 'src': src, 'classes': classes,
                'parent': parent, 'props': acc, 'parent_props': parent_props,
            })
            fit = acc.get('object-fit', '(inherited/initial)')
            ar = acc.get('aspect-ratio', '-')
            w = acc.get('max-width') or acc.get('width') or parent_props.get('max-width') or '-'
            print('%-26s:%-4d %-26s' % (rel, i + 1, ','.join(classes) or '(no class)'))
            print('      src=%s' % src[:70])
            print('      width=%-22s fit=%-12s ratio=%s' % (w, fit, ar))
            if parent:
                print('      parent=%-22s parent_width=%s' % (
                    parent, parent_props.get('max-width') or parent_props.get('width') or '-'))
    out = os.path.join(ROOT, '.workbuddy', 'preview', 'img_slots.json')
    with io.open(out, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(report, ensure_ascii=False, indent=1))
    print('\n→ %s  (%d 个位)' % (out, len(report)))


if __name__ == '__main__':
    sys.exit(main())