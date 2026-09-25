#!/usr/bin/env python
"""P3-1 production static build gate (end-to-end smoke test).

Reproduces the same chain build.sh runs on Vercel and asserts every hop:

    collectstatic (production storage) -> staticfiles/staticfiles.json
        -> pages/static_index_data.py (HASHED_FILES)
        -> public/static/  (the Vercel CDN root)

collectstatic is executed with ``VERCEL=1`` on purpose: locally settings uses
plain ``StaticFilesStorage`` (no manifest, un-hashed names), and only
``IS_VERCEL=True`` switches to ``pages.storage.BundledManifestStaticFilesStorage``
— i.e. the production code path. Any unexpected state exits non-zero, and
``--require-manifest`` makes the index generator fail closed as well.

Usage::

    .venv\\Scripts\\python.exe scripts/verify_static_build.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
REQUIRED = (
    "css/base.css",
    "css/fonts.css",
    "images/hero-main.webp",
    "images/logo.webp",
    "images/favicon.webp",
)


def build_env() -> dict:
    """build.sh 的构建期环境：VERCEL=1 触发生产静态存储；SECRET_KEY 给占位值。"""
    env = os.environ.copy()
    env["VERCEL"] = "1"
    env.setdefault("SECRET_KEY", "build-time-placeholder")
    return env


def run(*args: str) -> None:
    subprocess.run([PYTHON, *args], cwd=ROOT, check=True, env=build_env())


def main() -> int:
    run("manage.py", "collectstatic", "--noinput")
    static_root = ROOT / "staticfiles"
    manifest_path = static_root / "staticfiles.json"
    if not manifest_path.is_file():
        raise SystemExit("[p3-1] FAIL: staticfiles.json missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = manifest.get("paths", {})
    missing = [name for name in REQUIRED if name not in paths]
    if missing:
        raise SystemExit(f"[p3-1] FAIL: required manifest entries missing: {missing}")

    index_path = ROOT / "pages" / "static_index_data.py"
    run("-m", "pages.static_index", "--root", str(static_root),
        "--out", str(index_path), "--require-manifest")
    if not index_path.is_file():
        raise SystemExit("[p3-1] FAIL: bundled static index missing")
    namespace: dict = {}
    exec(compile(index_path.read_text(encoding="utf-8"), str(index_path), "exec"), namespace)
    hashed = namespace.get("HASHED_FILES", {})
    missing = [name for name in REQUIRED if name not in hashed]
    if missing:
        raise SystemExit(f"[p3-1] FAIL: bundled hash entries missing: {missing}")
    drift = [n for n in REQUIRED if hashed.get(n) != paths.get(n)]
    if drift:
        raise SystemExit(f"[p3-1] FAIL: bundled hash map drifted from the manifest: {drift}")

    # Rebuild only public/static — public/.gitkeep is tracked by git and must
    # survive (build.sh regenerates the whole tree on Vercel, where that is moot).
    public_static = ROOT / "public" / "static"
    if public_static.exists():
        shutil.rmtree(public_static)
    public_static.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(static_root, public_static)
    missing = [name for name in REQUIRED if not (public_static / name).is_file()]
    if missing:
        raise SystemExit(f"[p3-1] FAIL: public assets missing: {missing}")
    # The hashed copies are what production actually serves (immutable CDN URLs).
    missing = [name for name in REQUIRED
               if not (public_static / paths[name]).is_file()]
    if missing:
        raise SystemExit(f"[p3-1] FAIL: hashed public assets missing: {missing}")
    plain_total = sum(1 for p in public_static.rglob("*") if p.is_file())
    print(f"[p3-1] PASS: {len(paths)} manifest entries, {len(hashed)} bundled hashes, "
          f"{len(REQUIRED)} key assets (plain + hashed) in public/static/ "
          f"({plain_total} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
