#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""N-4: 从 1920 横版 hero 生成 1280 宽桌面档（webp q82 method=6，规格 §13.2）。
临时脚本，产物提交；脚本本身不提交（.workbuddy/tmp/）。"""
from pathlib import Path
from PIL import Image

SRC = Path(__file__).resolve().parents[2] / "static" / "images"
NAMES = ["hero-main-1", "hero-main-2", "hero-main-3"]

for name in NAMES:
    src = SRC / f"{name}.webp"
    dst = SRC / f"{name}-1280.webp"
    im = Image.open(src)
    width = 1280
    height = round(im.height * width / im.width)
    im2 = im.resize((width, height), Image.LANCZOS)
    im2.save(dst, "WEBP", quality=82, method=6)
    print(f"{dst.name}: {im.size} -> {im2.size}  {dst.stat().st_size // 1024} KB")