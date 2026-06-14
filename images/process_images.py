from PIL import Image, ImageFilter
import os

def remove_white_bg(img, threshold=240):
    img = img.convert('RGBA')
    w, h = img.size
    pixels = img.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            if r >= threshold and g >= threshold and b >= threshold:
                pixels[x, y] = (r, g, b, 0)
    return img

def add_soft_shadow(img, offset=(6, 10), shadow_radius=28, shadow_color=(0, 0, 0, 85)):
    img = img.convert('RGBA')
    w, h = img.size
    alpha = img.split()[-1]
    shadow = Image.new('RGBA', (w + shadow_radius * 2, h + shadow_radius * 2), (0, 0, 0, 0))
    shadow_shape = alpha.copy()
    shadow_shape = shadow_shape.filter(ImageFilter.GaussianBlur(radius=shadow_radius))
    shadow_color_layer = Image.new('RGBA', shadow_shape.size, shadow_color)
    shadow.paste(shadow_color_layer, (shadow_radius + offset[0], shadow_radius + offset[1]), shadow_shape)
    shadow.paste(img, (shadow_radius, shadow_radius), img)
    return shadow

def optimize_size(img, max_width):
    w, h = img.size
    if w > max_width:
        new_h = int(h * max_width / w)
        img = img.resize((max_width, new_h), Image.LANCZOS)
    return img

def save_as_png(img, path):
    img.save(path, 'PNG', optimize=True)
    print(f'  saved: {os.path.basename(path)} ({img.size[0]}x{img.size[1]})')

TARGETS = {
    'solarone-logo.fw.png':    {'max_width': 800,  'shadow': False},
    'products.fw.png':         {'max_width': 1600, 'shadow': True},
    'rt200-m.fw.png':          {'max_width': 1200, 'shadow': True},
    'floodlight.fw.png':       {'max_width': 1200, 'shadow': True},
    'rt400hb.fw.png':          {'max_width': 1200, 'shadow': True},
}

os.makedirs('processed', exist_ok=True)

print('=' * 60)
print('  Processing images: remove white bg -> shadow -> resize')
print('=' * 60)

for fname, spec in TARGETS.items():
    if not os.path.exists(fname):
        print(f'  SKIP: {fname} not found')
        continue
    print(f'\n[{fname}]')
    src = Image.open(fname)
    print(f'  original: {src.size}')
    img = src.convert('RGBA')
    img = remove_white_bg(img, threshold=240)
    if spec['shadow']:
        img = add_soft_shadow(img, offset=(6, 10), shadow_radius=28, shadow_color=(0, 0, 0, 85))
    img = optimize_size(img, spec['max_width'])
    out_name = fname.replace('.fw.', '.')
    out_path = os.path.join('processed', out_name)
    save_as_png(img, out_path)

print('\n' + '=' * 60)
print('  Done! Output in images/processed/')
print('=' * 60)
