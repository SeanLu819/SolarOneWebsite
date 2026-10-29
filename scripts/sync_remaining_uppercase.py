#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""补齐剩余大写/下划线/分辨率token 源文件(E:项目 static/images), 用确定性规范规则,
不依赖母素材匹配, 不猜词。 改名 + 刷新引用(seed/templates/pages) + 删旧大写变体。"""
import os, re, sys, json, uuid

STATIC = r'E:\Python\PROJECT\website\static\images'
PROJECT = r'E:\Python\PROJECT\website'
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

def safe_rename(old, new):
    if os.path.abspath(old).lower() == os.path.abspath(new).lower():
        tmp = old + '.' + uuid.uuid4().hex + '.tmpcase'
        os.rename(old, tmp)
        os.rename(tmp, new)
    else:
        os.rename(old, new)

def main():
    dry = '--dry-run' in sys.argv
    plan = []
    for r, _, fs in os.walk(STATIC):
        rp = r.replace('\\','/')
        if '/_variants/' in rp or rp.endswith('_variants') or '/_source/' in rp or rp.endswith('_source'):
            continue
        for f in fs:
            if f.lower().rsplit('.',1)[-1] not in KNOWN_EXT:
                continue
            s, ext = norm(f)
            if not s:
                continue
            target = s + '.' + ext
            if target == f:
                continue
            # 只处理需要改名的(大写/下划线/token)
            plan.append((os.path.join(r,f), os.path.join(r,target),
                         os.path.relpath(os.path.join(r,f),STATIC).replace('\\','/'),
                         os.path.relpath(os.path.join(r,target),STATIC).replace('\\','/')))
    print(f"计划改名: {len(plan)}")
    for o,n,ro,rn in plan:
        print(f"  {ro}  ->  {rn}")
    if dry:
        print("[DRY-RUN] 未改动。")
        return
    done=0
    for old,new,ro,rn in plan:
        if os.path.abspath(old).lower() != os.path.abspath(new).lower() and os.path.exists(new):
            print("SKIP 真碰撞:", rn); continue
        safe_rename(old,new); done+=1
    print("改名完成:", done)
    # 引用刷新
    ref_files=[os.path.join(PROJECT,'seed_data.json')]
    sp=os.path.join(PROJECT,'pages','seed_data.py')
    if os.path.exists(sp): ref_files.append(sp)
    for r,_,fs in os.walk(os.path.join(PROJECT,'templates')):
        for f in fs:
            if f.endswith('.html'): ref_files.append(os.path.join(r,f))
    for r,_,fs in os.walk(os.path.join(PROJECT,'pages')):
        for f in fs:
            if f.endswith('.py'): ref_files.append(os.path.join(r,f))
    repl=0
    for rf in ref_files:
        try: data=open(rf,encoding='utf-8',errors='ignore').read()
        except Exception: continue
        orig=data
        for old,new,ro,rn in plan:
            ob=os.path.basename(ro); nb=os.path.basename(rn)
            if ob in data: data=data.replace(ob,nb); repl+=1
        if data!=orig: open(rf,'w',encoding='utf-8',newline='').write(data)
    print("引用文件:",len(ref_files)," 替换:",repl)
    # 删旧大写变体
    removed=0
    for old,new,ro,rn in plan:
        sob=os.path.basename(ro).rsplit('.',1)[0].lower()
        for r,_,fs in os.walk(os.path.join(STATIC,'_variants')):
            for f in fs:
                if f.lower().rsplit('.',1)[-1] in KNOWN_EXT and sob in f.lower() and f!=f.lower():
                    try: os.remove(os.path.join(r,f)); removed+=1
                    except Exception: pass
    print("删旧大写变体:",removed)

if __name__=='__main__':
    main()
