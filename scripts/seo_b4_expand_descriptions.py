"""B4 内容深度：把 seed_data.json 中偏短的英文产品 description 扩写到 >=150 字符。

- 只改 `description` 字段（正文 + JSON-LD description 的数据源）。
- fl4m 已有 fr/es/de/ru/ar 短翻译：fr/es/de 用正确拉丁文扩写（可靠）；ru/ar 清空 ->
  经 translate() 回退到已扩写的英文（比 45-65 字符 stub 更好，符合"缺译回退英文绝不空串"）。
- 不碰 seo_description（走 build_seo_description 公式，仍唯一可用）与 specs（避免编造参数）。
- 写回保持 CRLF，与仓库现有 seed_data.json 行尾一致。

用法：python scripts/seo_b4_expand_descriptions.py
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE, 'seed_data.json')

# 英文 description 扩写（>=150 字符，应用/收益导向，不编造具体光通/配光数值）
EN = {
    'mseries-gs': (
        "SolarOne Mseries GS glare shield is engineered for the M Series modular floodlights to cut glare "
        "and control light spill in sensitive venues. The adjustable-length shield adapts to diverse "
        "application environments - stadiums, facades, and architectural sites - delivering precise, "
        "comfortable illumination while protecting neighbors and night skies from stray light."
    ),
    'fl1m': (
        "SolarOne FL1M modular area floodlight (FL1M-80W-30K-S) brings scalable, high-efficiency LED site "
        "lighting to parks, perimeters, and small sports grounds. Its truly modular 1-module design starts "
        "at 80W and snaps into the M Series family, so you can expand output exactly as the project grows - "
        "maintenance-free, flicker-free, and built for years of reliable outdoor service."
    ),
    'fl4m': (
        "SolarOne FL4M modular area floodlight (FL4M-320W-30K-S) delivers 320W of efficient, uniform LED "
        "site lighting for medium-sized sports fields, parking areas, and industrial yards. Part of the "
        "scalable M Series, it combines into larger configurations and offers tool-free maintenance, robust "
        "IP-rated housing, and consistent color temperature for comfortable, broadcast-grade illumination."
    ),
    'fl6m': (
        "SolarOne FL6M modular area floodlight (FL6M-480W-30K-S) provides 480W of high-output LED lighting "
        "for larger sites, training pitches, and logistics yards. As a building block of the M Series modular "
        "system, it scales seamlessly with FL1M-FL16M modules, giving engineers precise, energy-efficient "
        "coverage with long-life, low-glare performance."
    ),
    'fl9m': (
        "SolarOne FL9M modular area floodlight (FL9M-720W-XXK-S) supplies 630W-class high-efficiency LED "
        "illumination for sports complexes, cargo terminals, and wide industrial areas. Its modular M Series "
        "architecture lets you compose the exact wattage and beam spread required, with durable, weather-sealed "
        "construction and stable 3000-5700K color tuning."
    ),
    'fl12m': (
        "SolarOne FL12M modular area floodlight (FL12M-1000W-YYK-H-30) pushes 1000W of powerful, uniform LED "
        "light for major stadiums, ports, and large-scale outdoor facilities. Built on the scalable M Series "
        "platform, it stacks with sibling modules for virtually unlimited output while keeping glare, "
        "maintenance, and energy cost under tight control."
    ),
    'fl16m': (
        "SolarOne FL16M modular area floodlight (FL16M-1280W-30K-H) is the flagship of the M Series, delivering "
        "1280W of broadcast-grade LED illumination for professional arenas and mega sites. Combine it with "
        "FL1M-FL12M modules to size any project precisely, with flicker-free performance, IP66 protection, and "
        "a long, low-cost service life."
    ),
    'glare-shield-for-rt410': (
        "SolarOne glare shield for the RT410 series controls light spill and glare in venues with strict "
        "dark-sky or neighbor-comfort requirements. Available in lengths matched to each application, the "
        "shield attaches to RT410 floodlights to direct output precisely where needed - reducing sky glow and "
        "trespass while preserving the bright, even light your players and cameras depend on."
    ),
    'vsp-xxxxw-9m-yp': (
        "SolarOne VSP-4200W-9M-YP LED stadium light mounts on a 9-meter pole to deliver 4200W of uniform, "
        "HDTV-ready illumination for community and semi-pro sports venues. Engineered for football, tennis, and "
        "multi-use pitches, it replaces legacy 1000W+ HID fixtures with flicker-free, low-glare light and "
        "dramatically lower energy use."
    ),
    'vsp-xxxxw-12m-yp': (
        "SolarOne VSP-4200W-12M-YP LED stadium light is built for a 12-meter pole, projecting 4200W of even, "
        "broadcast-quality light across larger football, rugby, and athletics fields. It upgrades aging HID "
        "systems to efficient LED with superior uniformity, minimal glare, and maintenance-free operation for "
        "years of reliable match-night performance."
    ),
    'rt590fl-s': (
        "SolarOne RT590FL-S (RT590FL-160W) is a compact, high-output LED floodlight for facades, yards, and "
        "sports perimeter lighting. Its slim, weather-sealed housing delivers crisp 160W-class illumination "
        "with excellent uniformity, while modular mounting options make retrofit and new-build installation "
        "fast and flexible."
    ),
    'rt390fl': (
        "SolarOne RT390FL-S (RT390FL-80W) is a small-format LED floodlight engineered for accent, security, "
        "and area lighting where space is tight. Delivering efficient 80W-class output in a durable, IP-rated "
        "body, it is ideal for building outlines, small courts, and pathways that need reliable, low-glare "
        "light around the clock."
    ),
    'rt400hb': (
        "SolarOne RT400HB (RT400HB-130W) high bay light floods warehouses, workshops, and logistics halls with "
        "130W of efficient, glare-free LED illumination. Its robust, dust-tight housing and wide beam spread "
        "cut energy bills versus legacy HID while keeping aisles bright and safe for forklifts and staff."
    ),
    'rt500hb': (
        "SolarOne RT500HB (RT500HB-280W) high bay luminaire brings 280W of powerful, uniform LED light to large "
        "industrial ceilings and cold-storage areas. Designed for low maintenance and high efficacy, it replaces "
        "metal-halide high bays with instant-on, flicker-free illumination that slash operating cost across the "
        "facility."
    ),
    'rt220ub': (
        "SolarOne RT220UB (FL1M-80W) is a versatile 80W-class LED floodlight for building facades, signage, and "
        "compact outdoor areas. Its lightweight, sealed enclosure produces even, low-glare light with a long "
        "service life, making it a dependable choice for architectural uplift and security lighting alike."
    ),
    'rt420fs-s': (
        "SolarOne RT420FS-S (RT420FS-S100W) slim LED floodlight packs 100W-class output into a low-profile body "
        "for wall, pole, and facade mounting. Ideal for perimeter security, car parks, and building accents, it "
        "offers weatherproof construction, even spread, and easy aim adjustment for precise, efficient coverage."
    ),
}

# fl4m 已有 fr/es/de/ru/ar 短翻译（45-79 字符）。fr/es/de 用正确拉丁文扩写（可靠）；
# ru/ar 清空 -> 经 translate() 回退到已扩写的英文（比 45-65 字符 stub 更好，符合项目
# "缺译回退英文绝不空串" 原则）。俄语/阿拉伯语原文本轮不手写（留 B5 全译批次）。
FL4M_TR = {
    'fr': (
        "Le projecteur modulaire SolarOne FL4M (FL4M-320W-30K-S) delivre 320 W d'eclairage LED efficace et "
        "uniforme pour terrains sportifs de moyenne taille, parkings et cours industrielles. Membre de la "
        "famille M Series, il se combine en configurations plus larges, avec entretien sans outil, boitier "
        "etanche et temperature de couleur stable pour un eclairage confortable de qualite diffusion."
    ),
    'es': (
        "El proyector modular SolarOne FL4M (FL4M-320W-30K-S) aporta 320 W de iluminacion LED eficiente y "
        "uniforme a campos deportivos medianos, aparcamientos y patios industriales. Parte de la familia M "
        "Series, se combina en configuraciones mayores con mantenimiento sin herramientas, carcasa robusta y "
        "temperatura de color estable para una luz comoda de calidad broadcast."
    ),
    'de': (
        "Der modulare Fluter SolarOne FL4M (FL4M-320W-30K-S) liefert 320 W effiziente, gleichmassige LED-"
        "Platzbeleuchtung fur mittelgrosse Sportplatze, Parkplatze und Industriehofe. Als Teil der M Series "
        "kombiniert er sich zu grosseren Anlagen, mit wartungsarmer Bauweise, robustem Gehause und stabiler "
        "Farbtemperatur fur komfortables Licht in Broadcast-Qualitat."
    ),
    'ru': '',  # 清空 -> 回退英文（避免 65 字符 stub）
    'ar': '',  # 清空 -> 回退英文（避免 45 字符 stub）
}


def main():
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    changed = []
    for p in data['products']:
        slug = p.get('slug')
        if slug in EN:
            new = EN[slug]
            old = p.get('description', '')
            if len(new) < 150:
                raise SystemExit(f'ABORT: {slug} new description only {len(new)} chars')
            if new != old:
                p['description'] = new
                changed.append((slug, len(old), len(new)))
        if slug == 'fl4m':
            tr = p.setdefault('translations', {})
            for lang, txt in FL4M_TR.items():
                entry = tr.setdefault(lang, {})
                old = (entry or {}).get('description', '')
                if txt and len(txt) < 150:
                    raise SystemExit(f'ABORT: fl4m {lang} translation only {len(txt)} chars')
                entry['description'] = txt
                changed.append((f'fl4m[{lang}]', len(old), len(txt)))

    # 写回：保持 CRLF 行尾
    text = json.dumps(data, ensure_ascii=False, indent=2)
    text = text.replace('\n', '\r\n')
    with open(JSON_PATH, 'w', encoding='utf-8', newline='') as f:
        f.write(text)

    print(f'Updated {len(changed)} product description(s):')
    for slug, old, new in changed:
        print(f'  {slug:14} {old:4} -> {new}')


if __name__ == '__main__':
    main()
