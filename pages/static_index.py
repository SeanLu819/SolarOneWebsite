"""构建期静态资源索引（Vercel 部署用）。

背景
----
`pages/views/utils.py` 在**请求期**需要知道 `static/` 下有哪些文件（`_find_static`
做候选图存在性判定、`_list_static_dir` 做相册/产品图目录列举）。本地与 CI 直接
`os.walk` 磁盘即可；但 Vercel 部署时 `static/` 与 `staticfiles/` 已被
`vercel.json -> functions.excludeFiles` 排除出函数包（约 118 MB，占函数包体积
主体，静态资源本身由边缘 CDN 服务），运行时磁盘上不再存在这两个目录。

因此构建期把「目录 → 文件名列表」压成一个 Python 模块 `pages/static_index_data.py`
（与 `pages/seed_data.py` 同一套约定：git-ignored、每次构建重建），请求期
`utils._load_static_index()` 只做一次 import。索引只存**文件名**，不含任何图片
字节，故体积可忽略（约 20 KB）。

用法（build.sh）::

    python -m pages.static_index --root staticfiles --out pages/static_index_data.py

本地开发无需运行：utils 的磁盘扫描路径保持原样，索引仅作并集补充。
"""

import os
import sys

DEFAULT_ROOT = 'staticfiles'
DEFAULT_OUT = os.path.join('pages', 'static_index_data.py')

SKIP_NAMES = {'.DS_Store', 'Thumbs.db'}


def build_index(root):
    """扫描 root，返回 {'dirs': {相对目录: [文件名, ...]}}。目录用 '/' 分隔，根目录为 ''。"""
    dirs = {}
    if not os.path.isdir(root):
        return {'dirs': dirs}
    for cur, _sub, files in os.walk(root):
        rel = os.path.relpath(cur, root).replace('\\', '/')
        if rel == '.':
            rel = ''
        names = sorted(f for f in files if f not in SKIP_NAMES and not f.startswith('.'))
        if names:
            dirs[rel] = names
    return {'dirs': dirs}


def render_module(index):
    """把索引渲染成可 import 的 Python 源码。"""
    lines = [
        '"""构建期生成的静态资源索引 —— 请勿手工编辑。',
        '',
        '由 build.sh -> `python -m pages.static_index` 生成（git-ignored）。',
        '运行时 pages/views/utils.py 依赖它，在 static/ 目录未随函数包发布时',
        '仍能解析图片路径。本地开发该文件不存在时 utils 回退到磁盘扫描。',
        '"""',
        '',
        'STATIC_INDEX = {',
        "    'dirs': {",
    ]
    for rel in sorted(index['dirs']):
        names = index['dirs'][rel]
        lines.append('        %r: [' % rel)
        for n in names:
            lines.append('            %r,' % n)
        lines.append('        ],')
    lines.append('    },')
    lines.append('}')
    lines.append('')
    return '\n'.join(lines)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    root = DEFAULT_ROOT
    out = DEFAULT_OUT
    i = 0
    while i < len(argv):
        if argv[i] == '--root' and i + 1 < len(argv):
            root = argv[i + 1]
            i += 2
        elif argv[i] == '--out' and i + 1 < len(argv):
            out = argv[i + 1]
            i += 2
        else:
            i += 1

    if not os.path.isdir(root):
        # 不抛错：collectstatic 失败已在上游报错，这里给出明显告警即可，
        # 避免新增一条会让整个部署挂掉的失败路径。
        print('[static_index] WARNING: %s/ not found — writing empty index' % root)
        index = {'dirs': {}}
    else:
        index = build_index(root)

    total = sum(len(v) for v in index['dirs'].values())
    out_dir = os.path.dirname(out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(render_module(index))
    print('[static_index] %s → %s: %d dirs, %d files'
          % (root, out, len(index['dirs']), total))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
