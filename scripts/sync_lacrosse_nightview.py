"""定点: 把 garrison-forest-lacrosse-0N.webp 补场景词 -> -field-night-view-0N.webp
按 docs/image-filename-audit-2026-10-25.md 目标名(确定性, 非猜测)。
只改 5 个源文件 + 刷新 seed 引用 + 删旧变体; 变体重生交给 gen_image_variants.py。
"""
import os, re, json, shutil, sys

STATIC = r'E:\Python\PROJECT\website\static\images'
SEED = r'E:\Python\PROJECT\website\seed_data.json'
SUB = 'projects/garrison-forest-school'
OLD_PAT = re.compile(r'garrison-forest-lacrosse-(\d+)\.webp')
NEW_FMT = 'garrison-forest-lacrosse-field-night-view-{}.webp'

def find_sources():
    d = os.path.join(STATIC, SUB)
    out = []
    for f in os.listdir(d):
        m = OLD_PAT.match(f)
        if m:
            out.append((f, NEW_FMT.format(m.group(1))))
    return sorted(out)

def collected_variants(old_name):
    """返回 _variants 下匹配旧名的变体文件路径(待删)"""
    vd = os.path.join(STATIC, '_variants', SUB)
    if not os.path.isdir(vd):
        return []
    stem = old_name[:-5]  # 去 .webp
    return [os.path.join(vd, f) for f in os.listdir(vd) if f.startswith(stem + '~')]

def plan():
    srcs = find_sources()
    plans = []
    for old, new in srcs:
        oldp = os.path.join(STATIC, SUB, old)
        newp = os.path.join(STATIC, SUB, new)
        plans.append((oldp, newp, old, new, collected_variants(old)))
    return plans

def refresh_seed():
    s = open(SEED, encoding='utf-8').read()
    def rep(m):
        return NEW_FMT.format(m.group(1))
    new_s, n = OLD_PAT.subn(rep, s)
    return new_s, n

def main():
    dry = '--dry-run' in sys.argv
    plans = plan()
    print(f"源文件改名: {len(plans)}")
    total_variants = 0
    for oldp, newp, old, new, vs in plans:
        print(f"  {old} -> {new}   (旧变体 {len(vs)} 个待删)")
        total_variants += len(vs)
        for v in vs:
            print(f"      del {os.path.relpath(v, STATIC)}")
    new_s, n = refresh_seed()
    print(f"\nseed_data.json 引用刷新: {n} 处")
    if dry:
        print("\n[DRY-RUN] 未落盘")
        return
    # 1) 改名源文件
    for oldp, newp, old, new, vs in plans:
        if os.path.exists(newp):
            print(f"  SKIP 目标已存在: {new}")
            continue
        os.rename(oldp, newp)
    # 2) 删旧变体
    deleted = 0
    for oldp, newp, old, new, vs in plans:
        for v in vs:
            if os.path.exists(v):
                os.remove(v); deleted += 1
    print(f"\n已删旧变体: {deleted}")
    # 3) 写回 seed
    open(SEED, 'w', encoding='utf-8').write(new_s)
    print(f"seed 引用刷新已写回: {n} 处")

if __name__ == '__main__':
    main()
