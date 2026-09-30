"""B4 内容深度 · 子步①：手写 24 个产品的英文 seo_description（替代通用公式）。

- SEO 字段真源在 `translations[lang]['seo_description']`（`get_seo_override` 读取路径；
  top-level `seo_description` 字段是死字段，代码不读）。
- 本脚本为每款产品创建/补全 `translations['en']['seo_description']`，覆盖
  `build_seo_description()` 的通用公式，得到每页独立、质量更高的 meta 描述。
- 非英文 meta 继续走 `t('description', lang)`（缺译回退英文），全语翻译属 B5 批次，本轮不动。
- 守卫：`tests_seo_keywords.py:118` 要求 `seo_description('en')` 全唯一 + 长度 50-160；
  本脚本内置同样校验，越界即 abort，防止破坏既有守卫。
- 写回保持 CRLF，与仓库现有 seed_data.json 行尾一致。

用法：python scripts/seo_b4_write_seo_description.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE, 'seed_data.json')

# 英文 seo_description（手写，每页独立；50-160 字符；含品类词+型号+应用+品牌）
SEO_DESC = {
    'mseries-gs': (
        "SolarOne Mseries GS mounts M Series LED fixtures to poles, walls and towers with tool-free install "
        "and rugged aluminum build for sports and site lighting."
    ),
    'm-series': (
        "SolarOne M Series modular LED area and site lighting scales 80W to 1280W+ for lots, campuses and "
        "yards. Tool-free modules, stable color, low maintenance."
    ),
    'rt410-series': (
        "SolarOne RT410 Series (RT410FL-260W) area and site lighting gives 260W of efficient, uniform output "
        "for parking, paths and yards. Rugged, low-maintenance."
    ),
    'rgb-rgbw': (
        "SolarOne RGB / RGBW LED area and site lighting adds dynamic color, tunable white and DMX control for "
        "facades, landscapes and events. Weatherproof, easy program."
    ),
    'accessory': (
        "SolarOne LED accessories - brackets, drivers, lenses, kits - keep M Series and RT fixtures installed "
        "and maintained. Long-life genuine parts."
    ),
    'fl1m': (
        "SolarOne FL1M (FL1M-80W-30K-S) compact LED area luminaire gives 80W of efficient, uniform light for "
        "small lots, walkways and perimeters. Slim, tool-free design."
    ),
    'fl4m': (
        "SolarOne FL4M (FL4M-320W-30K-S) modular LED area lighting gives 320W of uniform output for mid "
        "fields, parking and yards with tool-free service."
    ),
    'fl6m': (
        "SolarOne FL6M (FL6M-480W-30K-S) high-output LED area lighting gives 480W for large parking, logistics "
        "yards and sports perimeters. Modular, low-maintenance."
    ),
    'fl9m': (
        "SolarOne FL9M (FL9M-720W) high-power LED area lighting gives 630W for stadium surrounds, freight "
        "yards and big sites. Modular build, stable color."
    ),
    'fl12m': (
        "SolarOne FL12M (FL12M-1000W) high-output LED area lighting gives 1000W for ports, rail yards and "
        "sports complexes. Modular, weatherproof, low-maintenance."
    ),
    'fl16m': (
        "SolarOne FL16M (FL16M-1280W) flagship LED area luminaire gives 1280W for airports, ports and "
        "stadiums. Modular high-mast build, broadcast-grade color."
    ),
    'fl9m-rgbw': (
        "SolarOne FL9M-RGBW area luminaire blends white with RGBW effects for facades, events and sports "
        "perimeters. DMX control, weatherproof, easy to program."
    ),
    'glare-shield-for-rt410': (
        "SolarOne glare shield for RT410 cuts up-light and spill, taming glare for homes and roads while "
        "keeping lighting effective. Tool-free, durable, code-friendly."
    ),
    'vsp-xxxxw-9m-yp': (
        "SolarOne VSP-4200W-9M-YP LED stadium pole gives high-output uniform light for 9m football, tennis "
        "and training pitches. Low glare, long life."
    ),
    'vsp-xxxxw-12m-yp': (
        "SolarOne VSP-4200W-12M-YP LED stadium pole gives high-output uniform light for 12m football, rugby "
        "and athletics fields. Low glare, long life."
    ),
    'rt590fl-s': (
        "SolarOne RT590FL-S (RT590FL-160W) compact LED flood light gives 160W of uniform light for facades, "
        "yards, sports and security. Slim, weatherproof, easy-aim."
    ),
    'rt390fl': (
        "SolarOne RT390FL-S (RT390FL-80W) compact LED flood light gives 80W of crisp, uniform light for "
        "facades, signage, yards and security. Slim, weatherproof."
    ),
    'rt400hb': (
        "SolarOne RT400HB (RT400HB-130W) high bay LED light gives 130W of uniform, glare-free light for "
        "warehouses, factories and gyms. Rugged, low-maintenance."
    ),
    'rt500hb': (
        "SolarOne RT500HB (RT500HB-280W) high bay LED luminaire gives 280W of uniform, glare-free light for "
        "large warehouses and logistics hubs. Rugged, low-maintenance."
    ),
    'rt220ub': (
        "SolarOne RT220UB (FL1M-80W) compact LED flood light gives 80W of uniform, weatherproof light for "
        "facades, yards, signage and security. Slim, easy-aim."
    ),
    'rt420fs-s': (
        "SolarOne RT420FS-S (RT420FS-S100W) LED flood light gives 100W of crisp, uniform light for facades, "
        "yards, sports and security. Slim, weatherproof, easy-aim."
    ),
    'rt410-rgbw': (
        "SolarOne RT410-RGBW area luminaire blends white with RGBW color for facades, events and sports "
        "perimeters. DMX control, weatherproof, easy programming."
    ),
    'rt600sl-t': (
        "SolarOne RT600SL-T LED roadway and street light gives efficient, uniform, glare-controlled light for "
        "highways, arterials and city streets. Rugged, easy-install."
    ),
    'rt820sl-t': (
        "SolarOne RT820SL-T roadway and street light gives high-output, uniform, glare-controlled light for "
        "highways, arterials and city streets. Rugged, easy-install."
    ),
}


def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    products = data['products']
    slugs = [p.get('slug') for p in products]

    # 校验脚本覆盖全部产品
    missing = [s for s in slugs if s not in SEO_DESC]
    if missing:
        raise SystemExit(f'ABORT: SEO_DESC 缺少这些 slug: {missing}')
    extra = [s for s in SEO_DESC if s not in slugs]
    if extra:
        raise SystemExit(f'ABORT: SEO_DESC 有多余 slug（seed 无此产品）: {extra}')

    changed = []
    seen = {}
    for p in products:
        slug = p['slug']
        new = SEO_DESC[slug]
        n = len(new)
        if not (50 <= n <= 160):
            raise SystemExit(f'ABORT: {slug} seo_description 长度 {n} 越界（需 50-160）')
        if new in seen:
            raise SystemExit(f'ABORT: {slug} 与 {seen[new]} seo_description 重复（需唯一）')
        seen[new] = slug

        tr = p.setdefault('translations', {})
        if not isinstance(tr, dict):
            raise SystemExit(f'ABORT: {slug} translations 不是 dict')
        en = tr.setdefault('en', {})
        if not isinstance(en, dict):
            raise SystemExit(f'ABORT: {slug} translations.en 不是 dict')
        old = en.get('seo_description', '')
        if new != old:
            en['seo_description'] = new
            changed.append((slug, len(old), n))

    # 写回：保持 CRLF 行尾
    text = json.dumps(data, ensure_ascii=False, indent=2)
    text = text.replace('\n', '\r\n')
    with open(JSON_PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

    print(f'Updated {len(changed)} product seo_description(s):')
    for slug, old, new in changed:
        print(f'  {slug:24} {old:4} -> {new}')


if __name__ == '__main__':
    main()
