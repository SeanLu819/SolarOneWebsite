"""One-off generator for static/images/og-default.webp (1200x630).

Run from the repo root:
    E:/Python/python3/python.exe scripts/make_og_default.py

Why a generated file instead of a photo: Open Graph wants exactly 1200x630
(1.91:1). None of the shipped photos have that ratio, and cropping one loses the
floodlight array that makes the brand recognisable. So we take a hero shot,
crop it to 1.91:1, lay a dark scrim over it and print the brand line, which is
what a social card actually needs to be readable at thumbnail size.

Deterministic: same inputs -> byte-identical output, so re-running is safe and
the guard can hash the result.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / 'static' / 'images' / 'og-default.webp'
HERO = BASE / 'static' / 'images' / 'hero-main-2-1280.webp'
LOGO = BASE / 'static' / 'images' / 'logo.webp'

W, H = 1200, 630
FONT_BOLD = r'C:\Windows\Fonts\arialbd.ttf'
FONT_REG = r'C:\Windows\Fonts\arial.ttf'

HEADLINE = 'LED Stadium Lighting Solutions'
SUBLINE = 'Floodlights since 2007  |  solaronelighting.com'


def main():
    # 1. Crop the hero to 1.91:1, centred.
    hero = Image.open(HERO).convert('RGB')
    target_ratio = W / H
    src_ratio = hero.width / hero.height
    if src_ratio > target_ratio:
        # too wide -> trim sides
        new_w = int(hero.height * target_ratio)
        left = (hero.width - new_w) // 2
        hero = hero.crop((left, 0, left + new_w, hero.height))
    else:
        new_h = int(hero.width / target_ratio)
        top = (hero.height - new_h) // 2
        hero = hero.crop((0, top, hero.width, top + new_h))
    hero = hero.resize((W, H), Image.LANCZOS)

    # 2. Dark scrim so white text passes contrast on any part of the photo.
    #    Two layers: a flat 45% wash to tame the whole frame, plus a bottom
    #    gradient that darkens further where the copy sits.
    dark = Image.new('RGB', (W, H), (4, 8, 20))
    out = Image.blend(hero, dark, 0.45)

    grad = Image.new('L', (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(150 * ((y / (H - 1)) ** 1.4)))
    grad = grad.resize((W, H))
    grad_out = Image.composite(dark, out, grad)
    out = Image.blend(out, grad_out, 0.55)

    d = ImageDraw.Draw(out)

    # 3. Logo, top-left, with padding.
    logo = Image.open(LOGO).convert('RGBA')
    target_w = 300
    scale = target_w / logo.width
    logo = logo.resize((target_w, int(logo.height * scale)), Image.LANCZOS)
    out.paste(logo, (60, 56), logo)

    # 4. Headline + subline, bottom-left. The accent rule sits ABOVE the
    #    headline: the 62px type occupies roughly H-210..H-148, so a rule at
    #    H-168 would cut through the glyphs.
    f_head = ImageFont.truetype(FONT_BOLD, 62)
    f_sub = ImageFont.truetype(FONT_REG, 30)
    d.rectangle([60, H - 250, 60 + 120, H - 246], fill=(0, 160, 220))
    d.text((60, H - 210), HEADLINE, font=f_head, fill=(255, 255, 255))
    d.text((60, H - 118), SUBLINE, font=f_sub, fill=(196, 214, 255))

    out.save(OUT, 'WEBP', quality=82, method=6)
    print(f'wrote {OUT} {out.size} {OUT.stat().st_size} bytes')


if __name__ == '__main__':
    main()
