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

同时（v1.5.5 新增）把 collectstatic 产出的 `staticfiles.json` 里的
「原名 → 哈希名」映射也写进同一个模块的 `HASHED_FILES`。原因：生产用
`CompressedManifestStaticFilesStorage`，`{% static %}` 必须能查到映射，否则
（清单缺失时）会抛 `ValueError: The file ... could not be found` —— **每一个
页面都会 500**。`staticfiles/` 本身被排除出函数包，只有把映射变成包内的
Python 源码才能 100% 保证它在运行时可用。

用法（build.sh）::

    python -m pages.static_index --root staticfiles --out pages/static_index_data.py

本地开发无需运行：utils 的磁盘扫描路径保持原样，索引仅作并集补充；
存储层优先读模块、退回磁盘清单，磁盘也没有时退回未哈希 URL。
"""

import json
import os
import sys

DEFAULT_ROOT = 'staticfiles'
DEFAULT_OUT = os.path.join('pages', 'static_index_data.py')

MANIFEST_NAME = 'staticfiles.json'

SKIP_NAMES = {'.DS_Store', 'Thumbs.db'}


def build_index(root):
    """扫描 root，返回 {'dirs': {相对目录: [文件名, ...]}, 'hashed': {原名: 哈希名}}。

    目录用 '/' 分隔，根目录为 ''。'hashed' 来自 collectstatic 写在 root 根下的
    `staticfiles.json`；文件不存在（未跑过带 Manifest storage 的 collectstatic）
    时为空字典。
    """
    dirs = {}
    if os.path.isdir(root):
        for cur, _sub, files in os.walk(root):
            rel = os.path.relpath(cur, root).replace('\\', '/')
            if rel == '.':
                rel = ''
            names = sorted(f for f in files if f not in SKIP_NAMES and not f.startswith('.'))
            if names:
                dirs[rel] = names
    return {'dirs': dirs, 'hashed': read_hashed_files(root)}


def read_hashed_files(root):
    """读取 <root>/staticfiles.json 的 paths（原名 → 哈希名）。读不到返回 {}。"""
    path = os.path.join(root, MANIFEST_NAME)
    try:
        with open(path, encoding='utf-8') as fh:
            payload = json.load(fh)
    except (OSError, ValueError):
        return {}
    paths = payload.get('paths') if isinstance(payload, dict) else None
    if not isinstance(paths, dict):
        return {}
    return {
        k: v for k, v in paths.items()
        if isinstance(k, str) and isinstance(v, str) and k and v
    }


def render_module(index):
    """把索引渲染成可 import 的 Python 源码。"""
    lines = [
        '"""构建期生成的静态资源索引 —— 请勿手工编辑。',
        '',
        '由 build.sh -> `python -m pages.static_index` 生成（git-ignored）。',
        '运行时 pages/views/utils.py 依赖它，在 static/ 目录未随函数包发布时',
        '仍能解析图片路径。本地开发该文件不存在时 utils 回退到磁盘扫描。',
        '',
        'HASHED_FILES = collectstatic 的 staticfiles.json -> paths 映射。生产存储',
        '（pages/storage.BundledManifestStaticFilesStorage）优先读它，因为',
        'staticfiles/ 被排除出 Vercel 函数包，磁盘上的 staticfiles.json 不可用。',
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
    hashed = index.get('hashed') or {}
    lines.append('# 原名 -> 内容哈希名（来自 staticfiles.json）')
    lines.append('HASHED_FILES = {')
    for src in sorted(hashed):
        lines.append('    %r: %r,' % (src, hashed[src]))
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
        index = {'dirs': {}, 'hashed': {}}
    else:
        index = build_index(root)

    total = sum(len(v) for v in index['dirs'].values())
    out_dir = os.path.dirname(out)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as fh:
        fh.write(render_module(index))
    print('[static_index] %s → %s: %d dirs, %d files, %d hashed names'
          % (root, out, len(index['dirs']), total, len(index.get('hashed') or {})))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
