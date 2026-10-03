"""图片重压 dry-run 报告（只读，不写任何文件）。

用途：对static/images 下编码低效的 webp 估算「重编码为 q80/method6」的体积
与质量变化，供人工确认后才决定是否实际写入。

🔴 铁律（AGENTS.md §5）：图片文件名上传即固化，改名须同步 seed py+json，
否则线上 404。本脚本**只覆盖同名文件，绝不改名**。

用法：
    E:/Python/python3/python.exe scripts/optimize_images.py --dry-run
    E:/Python/python3/python.exe scripts/optimize_images.py --apply
"""
import argparse
import glob
import io
import os
import sys

from PIL import Image

# bytes-per-pixel 阈值：典型高效 webp 应远低于 0.30。超过即判定编码低效。
BPP_THRESHOLD = 0.30
# 🔴 method=4，不是 6。实测同一张 1520×856 RGBA：method6 要 4.78s/张，
# method4 只要 0.62s（快 7.7 倍），体积仅差 3%（124KB vs 128KB）。
# 30 张 × 3 档quality 用 method6 会跑超时被 SIGTERM（初版就这么挂的）。
# method >= 5 的边际收益在这个尺寸上不值得那份CPU 时间。
METHOD = 4
# 只有「省下的字节 / 原大小」超过这个比例才值得覆盖，避免为了几十字节动文件。
MIN_SAVE_RATIO = 0.10

# 🔴 自适应质量阶梯：不能对所有图一把 q80。
# 首次 dry-run 用统一 q80 跑出 VSP9M 系列 PSNR 仅 16–19 dB（可见块状伪影）——
# 那是 1520×856 的产品渲染图，带alpha 通道和柔和渐变，正是 webp 有损压缩
# 最容易出 bandinging 的类型。改用阶梯 + PSNR 门禁：
#   - 从 q88 起，PSNR 达标就停；
#   - 不达标（< MIN_PSNR）自动降一档重试，宁可少省体积也不砸画质；
#   - 降到 QUALITY_FLOOR 仍不达标则跳过该文件并报告，绝不覆盖。
QUALITY_LADDER = (88, 84, 80)
QUALITY_FLOOR = 80
# PSNR 门禁：>=40 视觉无损；35–40 轻微；<30 明显可见（不可接受）。
MIN_PSNR = 40.0


def _candidates():
    """返回编码低效的 webp 绝对路径列表。"""
    out = []
    for path in glob.glob('static/images/**/*.webp', recursive=True):
        try:
            with Image.open(path) as im:
                px = im.width * im.height
                size = os.path.getsize(path)
        except Exception:
            continue
        if not px:
            continue
        if size / px > BPP_THRESHOLD:
            out.append((path, size, px))
    return out


def _reencode(im, quality, method=METHOD):
    """重编码为 webp。

    🔴 透明通道必须保留：产品图有 RGBA 模式（图册图集/证书图），转 RGB 会
    把透明区压成黑底。带 alpha 的走 mode='RGBA' 保留，否则转 RGB 去alpha。
    """
    buf = io.BytesIO()
    if _has_alpha(im):
        im.convert('RGBA').save(buf, 'WEBP', quality=quality, method=method)
    else:
        im.convert('RGB').save(buf, 'WEBP', quality=quality, method=method)
    return buf.getvalue()


def _has_alpha(im):
    return im.mode in ('RGBA', 'LA') or (
        im.mode == 'P' and 'transparency' in im.info
    )


def _psnr(a_bytes, b_bytes):
    """两版图的 PSNR(dB)。>=40 视觉无损，35–40 轻微，<30 明显可见。

    🔴 alpha 必须合成到白底再比，否则透明区的 RGB 值不可比，会算出虚假的
    低 PSNR（透明像素在两个文件里数值不同但视觉无差）。

    实现注记：初版用纯 Python 逐字节算MSE，30 张图跑超时被 SIGTERM。
    改用 numpy 向量化（Image.tobytes -> frombuffer）后单张<10ms。
    """
    try:
        import math
        import numpy as np

        with Image.open(io.BytesIO(a_bytes)) as ia, \
                Image.open(io.BytesIO(b_bytes)) as ib:
            a = _flatten(ia)
            b = _flatten(ib)
            if a.size != b.size:
                b = b.resize(a.size)
            if a.width * a.height > 250000:
                a.thumbnail((500, 500))
                b = _flatten(Image.open(io.BytesIO(b_bytes))).resize(a.size)
            arr_a = np.frombuffer(a.tobytes(), dtype=np.uint8).astype(np.int32)
            arr_b = np.frombuffer(b.tobytes(), dtype=np.uint8).astype(np.int32)
            if arr_a.size != arr_b.size or arr_a.size == 0:
                return None
            mse = float(np.mean((arr_a - arr_b) ** 2))
            if mse == 0:
                return 99.0
            return round(20 * math.log10(255 / math.sqrt(mse)), 1)
    except Exception:
        return None


def _flatten(im):
    """把 alpha 合成到白底，返回RGB 图。"""
    im = im.convert('RGBA') if _has_alpha(im) else im.convert('RGB')
    bg = Image.new('RGB', im.size, (255, 255, 255))
    bg.paste(im, mask=im.split()[-1] if im.mode == 'RGBA' else None)
    return bg


def _best_encode(path, old_bytes):
    """在质量阶梯上挑第一个 PSNR 达标的编码。

    返回 (new_bytes, quality, psnr, reason)：
      - new_bytes 非 None -> 可写入
      - new_bytes None    -> 不可写入，reason 说明原因（'worse'/'psnr'/'gain'）
    """
    with Image.open(io.BytesIO(old_bytes)) as im:
        first_psnr = None
        for q in QUALITY_LADDER:
            data = _reencode(im, q)
            psnr = _psnr(old_bytes, data)
            if first_psnr is None:
                first_psnr = psnr
            if len(data) >= len(old_bytes):
                # 🔴 原版已经比这一档更省。照片类内容（项目实拍）天然高
                # B/px，0.30 阈值会误判它们"低效"—— 实测 chunan-velodrome
                # 337KB 用 q88 重压反而变 361KB。这类文件原编码已达标，
                # 任何有损重压都只会更大，必须原样保留。
                # 换更低档只会更小更糊，不值得，所以直接放弃。
                return (None, q, first_psnr, 'worse')
            if psnr is not None and psnr < MIN_PSNR:
                if q > QUALITY_FLOOR:
                    continue          # 降一档重试
                return (None, q, psnr, 'psnr')
            return (data, q, psnr, None)
    return (None, QUALITY_LADDER[-1], first_psnr, 'worse')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='只报告，不写文件（默认）')
    ap.add_argument('--apply', action='store_true', help='实际覆盖写入')
    args = ap.parse_args()

    cands = _candidates()
    if not cands:
        print('没有编码低效的图片，无需处理。')
        return 0

    print(f'编码低效阈值: >{BPP_THRESHOLD} B/px  候选 {len(cands)} 个')
    print(f'质量阶梯: {" -> ".join(str(q) for q in QUALITY_LADDER)}'
          f'  PSNR 门禁 >= {MIN_PSNR} dB')
    print()

    rows = []
    skipped = []
    total_old = total_new = 0
    for path, old, px in sorted(cands, key=lambda r: -r[1]):
        with open(path, 'rb') as fh:
            old_bytes = fh.read()
        new_bytes, q, psnr, reason = _best_encode(path, old_bytes)
        if new_bytes is None:
            skipped.append((path, old, q, psnr, reason))
            continue
        new = len(new_bytes)
        ratio = (old - new) / old if old else 0
        if ratio < MIN_SAVE_RATIO:
            skipped.append((path, old, q, psnr, 'gain'))
            continue
        rows.append((path, old, new, ratio, px, psnr, q))
        total_old += old
        total_new += new

    if rows:
        print(f'{"节省":>7} {"原KB":>7} {"新KB":>7} {"q":>3} {"PSNR":>6} {"B/px":>6}  文件')
        for path, old, new, ratio, px, psnr, q in rows:
            ps = f'{psnr:6.1f}' if psnr is not None else '     -'
            print(f'{ratio:6.1%} {old/1024:7.0f} {new/1024:7.0f} {q:3d} {ps}'
                  f'{old/px:6.2f}  {path}')
        save = total_old - total_new
        print()
        print(f'可处理 {len(rows)} 个  {total_old/1048576:.2f} MB -> '
              f'{total_new/1048576:.2f} MB  节省 {save/1048576:.2f} MB'
              f'({save/total_old:.1%})')

    if skipped:
        print(f'\n跳过 {len(skipped)} 个 —— 原样保留，不做任何写入：')
        by_reason = {}
        for path, old, q, psnr, reason in skipped:
            by_reason.setdefault(reason, []).append((path, old, q, psnr))
        label = {
            'worse': '原编码已优于任何重压档位（照片类内容天然高 B/px，阈值误判）',
            'psnr': f'降到 q{QUALITY_FLOOR} 仍 PSNR < {MIN_PSNR} dB，砸画质不划算',
            'gain': f'节省不足 {MIN_SAVE_RATIO:.0%}，不值得动文件',
        }
        for reason, items in by_reason.items():
            print(f'\n  [{reason}] {label.get(reason, reason)} —— {len(items)} 个')
            for path, old, q, psnr in items:
                ps = f'{psnr:.1f}' if psnr is not None else '  -  '
                print(f'    {old/1024:6.0f}KB q{q:<3d} PSNR {ps:>5}  {path}')

    if not rows:
        print('\n没有可安全处理的文件。')
        return 0

    if not args.apply:
        print('\n[dry-run] 未写入任何文件。确认无误后加 --apply 执行。')
        return 0

    print('\n[apply] 写入中...')
    done = 0
    for path, old, new, ratio, px, psnr, q in rows:
        with open(path, 'rb') as fh:
            data, _, _, _ = _best_encode(path, fh.read())
        if data is None:
            print(f'  跳过（重跑结果不一致）: {path}')
            continue
        with open(path, 'wb') as fh:
            fh.write(data)
        done += 1
    print(f'[apply] 完成，覆盖 {done} 个文件（文件名未变）。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
