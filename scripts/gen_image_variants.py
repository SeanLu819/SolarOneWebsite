#!/usr/bin/env python
"""Batch C (v1.10.18): generate responsive image variants.

Walks static/images/{products,projects,news}, and for every source image
creates width variants (360/720/1248) under static/images/_variants/ — the
mirrored, gallery-safe directory tree. Source images are NOT recompressed here
(by default) so the tracked working tree stays clean; source recompression is
the separate C0 step and is opt-in via --recompress.

Run by build.sh immediately BEFORE collectstatic so the variant files are
collected (and content-hashed) into the deploy bundle. Also run locally before
preview so the dev server can serve the variants.
"""
import argparse
import os
import sys

# Allow `python scripts/gen_image_variants.py` from the repo root.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from pages.image_variants import generate_all  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Generate responsive image variants (batch C)")
    ap.add_argument("--recompress", action="store_true",
                    help="also recompress oversize SOURCE images in place (C0 step)")
    ap.add_argument("--categories", nargs="*", default=None,
                    help="override category subdirs (default: products projects news products_page)")
    args = ap.parse_args()

    kwargs = {"recompress": args.recompress}
    if args.categories:
        kwargs["categories"] = tuple(args.categories)

    summary = generate_all(**kwargs)
    print("[gen_image_variants] summary:", summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
