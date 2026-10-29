#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把母素材库(D:/外贸项目/website/正式产品素材 / 正式项目素材)的清洗后文件名,
同步到 E:项目 static/images(即 Vercel 部署源), 并刷新所有引用。

规则(与 image-naming-spec.md 一致, 纯可推导, 不靠人工日志):
  1) 小写化
  2) 删分辨率 token: 1080p/855p/720p/540p/650p
  3) 空格/下划线 -> 连字符, 折叠重复连字符
只处理: E:项目源文件(非 _variants / 非 _source) 且 母素材库存在同 normkey 的清洗文件。
变体: 源改名后由 gen_image_variants.py 重生, 这里删除旧大写变体, 本地重跑生成。
引用: seed_data.json + pages/seed_data.py(若存在) + templates/** + pages/** 中的旧 basename -> 新 basename。
NTFS 大小写不敏感: 用 uuid 临时名两步走。
"""
import os, re, sys, json, uuid, shutil

MOTHERS = [r'D:\外贸项目\website\正式产品素材', r'D:\外贸项目\website\正式项目素材']
STATIC = r'E:\Python\PROJECT\website\static\images'
KNOWN_EXT = {'webp','png','jpg','jpeg','svg','avif','gif'}
TOKEN_RE = re.compile(r'(?:1080|855|720|540|650)p', re.I)

def norm(name):
    stem, ext = os.path.splitext(name)
    ext = ext.lower().lstrip('.')
    s = stem.lower()
    s = TOKEN_RE.sub('', s)
    s = re.sub(r'[ _]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s, ext

def build_mother_index():
    idx = {}  # normkey -> actual stem (lowercase)
    for M in MOTHERS:
        for r, _, fs in os.walk(M):
            for f in fs:
                if f.lower().rsplit('.',1)[-1] not in KNOWN_EXT:
                    continue
                s, ext = norm(f)
                if s:
                    idx.setdefault(s, f[: -len(os.path.splitext(f)[1])].lower())
    return idx

def find_source_images():
    out = []
    for r, _, fs in os.walk(STATIC):
        if '/_variants/' in r.replace('\\','/') or r.replace('\\','/').endswith('_variants'):
            continue
        if '/_source/' in r.replace('\\','/') or r.replace('\\','/').endswith('_source'):
            continue
        for f in fs:
            if f.lower().rsplit('.',1)[-1] not in KNOWN_EXT:
                continue
            out.append(os.path.join(r, f))
    return out

def safe_rename(old, new):
    if os.path.abspath(old).lower() == os.path.abspath(new).lower():
        tmp = old + '.' + uuid.uuid4().hex + '.tmpcase'
        os.rename(old, tmp)
        os.rename(tmp, new)
    else:
        os.rename(old, new)

def main():
    dry = '--dry-run' in sys.argv
    mother_idx = build_mother_index()
    sources = find_source_images()
    plan = []  # (old_abs, new_abs, old_rel, new_rel)
    skipped_no_match = 0
    noop = 0
    for full in sources:
        d, f = os.path.split(full)
        s, ext = norm(f)
        if not s:
            continue
        target_stem = mother_idx.get(s)
        if target_stem is None:
            skipped_no_match += 1
            continue
        new_name = target_stem + '.' + ext
        if new_name == f:
            noop += 1
            continue
        new_full = os.path.join(d, new_name)
        rel_old = os.path.relpath(full, STATIC).replace('\\','/')
        rel_new = os.path.relpath(new_full, STATIC).replace('\\','/')
        plan.append((full, new_full, rel_old, rel_new))
    print(f"母素材 normkey 索引: {len(mother_idx)}")
    print(f"E:项目源文件扫描: {len(sources)}")
    print(f"  跳过(母素材无对应清洗名, 编辑稿/_source): {skipped_no_match}")
    print(f"  无需改动(已一致): {noop}")
    print(f"  计划改名: {len(plan)}")
    print()
    for old, new, ro, rn in plan[:60]:
        print(f"  {ro}  ->  {rn}")
    if len(plan) > 60:
        print(f"  ... 其余 {len(plan)-60} 个")
    print()
    if dry:
        print("[DRY-RUN] 未改动任何文件。")
        return
    # ---- apply ----
    # 1) 改名源文件
    done = 0
    skipped = 0
    for old, new, ro, rn in plan:
        # NTFS 大小写不敏感: old.lower()==new.lower() 时是同一物理文件, 必须小写化(不跳过)
        if os.path.abspath(old).lower() != os.path.abspath(new).lower() and os.path.exists(new):
            print(f"  SKIP 目标已存在(真碰撞): {rn}")
            skipped += 1
            continue
        safe_rename(old, new)
        done += 1
    print(f"源文件改名完成: {done}  跳过(真碰撞): {skipped}")
    # 2) 刷新引用
    ref_files = []
    ref_files.append(os.path.join(r'E:\Python\PROJECT\website', 'seed_data.json'))
    sp = os.path.join(r'E:\Python\PROJECT\website', 'pages', 'seed_data.py')
    if os.path.exists(sp):
        ref_files.append(sp)
    for r, _, fs in os.walk(os.path.join(r'E:\Python\PROJECT\website','templates')):
        for f in fs:
            if f.endswith('.html'):
                ref_files.append(os.path.join(r,f))
    for r, _, fs in os.walk(os.path.join(r'E:\Python\PROJECT\website','pages')):
        for f in fs:
            if f.endswith('.py'):
                ref_files.append(os.path.join(r,f))
    total_repl = 0
    for rf in ref_files:
        try:
            data = open(rf, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue
        original = data
        for old, new, ro, rn in plan:
            ob = os.path.basename(ro); nb = os.path.basename(rn)
            if ob in data:
                data = data.replace(ob, nb)
                total_repl += 1
        if data != original:
            open(rf,'w',encoding='utf-8',newline='').write(data)
    print(f"引用刷新文件数: {len(ref_files)}  替换次数: {total_repl}")
    # 3) 删除旧大写变体(构建会重生)
    removed = 0
    for old, new, ro, rn in plan:
        ob = os.path.basename(ro); nb = os.path.basename(rn)
        # 遍历 _variants 找含旧 basename(去扩展)的
        stem_old = ob.rsplit('.',1)[0]
        for r, _, fs in os.walk(os.path.join(STATIC,'_variants')):
            for f in fs:
                if f.lower().rsplit('.',1)[-1] in KNOWN_EXT and stem_old.lower() in f.lower() and f != f.lower():
                    try:
                        os.remove(os.path.join(r,f)); removed += 1
                    except Exception:
                        pass
    print(f"删除旧大写变体: {removed}")

if __name__ == '__main__':
    main()
