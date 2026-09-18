#!/usr/bin/env python
"""Import i18n translations from a single CSV into the SolarOne codebase.

The CSV is the single delivery format for the translation pipeline
(see docs/i18n_翻译工作指引.md §5). One row = one English source string plus its
translations for fr/es/de/ru/ar. Rows are routed by their ``key`` prefix:

    template: / po:     -> gettext catalog  locale/<lang>/LC_MESSAGES/django.po
                           (msgid == the English string); compiled to .mo
    sidebar: / siteconfig: -> pages/views/i18n_overrides.json
                           (merged into _SIDEBAR_I18N at import; mechanism ②)
    product: / project:   -> seed_data.json  <type>s[<slug>].translations.<lang>
                           (then regenerate_seed so pages/seed_data.py stays in sync)

The script is idempotent: re-running it re-applies the same CSV without duplicating
or destroying unrelated entries. Untranslated cells (empty) are skipped, never
overwritten with blanks.

Usage:
    python scripts/import_i18n_csv.py docs/i18n_p0_draft.csv
    python scripts/import_i18n_csv.py path/to/file.csv --dry-run
    python scripts/import_i18n_csv.py path/to/file.csv --verify   # run guard tests after

Columns: key,en,fr,es,de,ru,ar,note   (note is optional)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys

try:
    import polib
except ImportError:  # pragma: no cover - dependency guard
    sys.stderr.write(
        "ERROR: polib is required (pip install polib). It compiles .po -> .mo.\n"
    )
    sys.exit(2)

LANGS = ["fr", "es", "de", "ru", "ar"]
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCALE_DIR = os.path.join(REPO_ROOT, "locale")
OVERRIDES_PATH = os.path.join(REPO_ROOT, "pages", "views", "i18n_overrides.json")
SEED_JSON_PATH = os.path.join(REPO_ROOT, "seed_data.json")


def _prefix(key: str) -> str:
    # Accept either ':' or '.' as the prefix delimiter so both
    # 'template.home_title' and 'po:foo' style keys route correctly.
    for sep in (":", "."):
        if sep in key:
            return key.split(sep, 1)[0].strip().lower()
    return "po"


def _get_or_create(po: "polib.POFile", msgid: str) -> "polib.POEntry":
    entry = po.find(msgid)
    if entry is None:
        entry = polib.POEntry(msgid=msgid)
        po.append(entry)
    return entry


def _apply_po(row: dict, dirty_langs: set) -> None:
    msgid = row["en"]
    if not msgid:
        return
    for lang in LANGS:
        msgstr = (row.get(lang) or "").strip()
        if not msgstr:
            continue
        po_path = os.path.join(LOCALE_DIR, lang, "LC_MESSAGES", "django.po")
        if not os.path.exists(po_path):
            sys.stderr.write(f"  ! skip {lang}: {po_path} missing\n")
            continue
        po = polib.pofile(po_path)
        entry = _get_or_create(po, msgid)
        entry.msgstr = msgstr
        po.save()
        mo_path = po_path[: -len(".po")] + ".mo"
        po.save_as_mofile(mo_path)
        dirty_langs.add(lang)


def _apply_overrides(row: dict, overrides: dict) -> None:
    label = row["en"]
    if not label:
        return
    target = overrides.setdefault(label, {})
    for lang in LANGS:
        val = (row.get(lang) or "").strip()
        if not val:
            continue
        target[lang] = val


def _apply_seed(row: dict, seed: dict, dirty_seed: set) -> None:
    # key like "product.fl1m.description" or "project.foo.title"
    parts = row["key"].split(":", 1)[1] if ":" in row["key"] else row["key"]
    segs = parts.split(".")
    if len(segs) < 3:
        sys.stderr.write(f"  ! skip seed row (need slug.field): {row['key']}\n")
        return
    kind, slug, field = segs[0], segs[1], segs[2]
    coll_key = "products" if kind == "product" else "projects"
    coll = seed.get(coll_key)
    if not isinstance(coll, list):
        sys.stderr.write(f"  ! skip seed row (no {coll_key} in seed): {row['key']}\n")
        return
    match = next((item for item in coll if item.get("slug") == slug), None)
    if match is None:
        sys.stderr.write(f"  ! skip seed row (slug not found): {row['key']}\n")
        return
    translations = match.setdefault("translations", {})
    for lang in LANGS:
        val = (row.get(lang) or "").strip()
        if not val:
            continue
        translations.setdefault(lang, {})[field] = val
    dirty_seed.add(coll_key)


def _load_overrides() -> dict:
    if os.path.exists(OVERRIDES_PATH):
        try:
            with open(OVERRIDES_PATH, encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data
        except (OSError, ValueError):
            pass
    return {}


def _load_seed() -> dict:
    if os.path.exists(SEED_JSON_PATH):
        with open(SEED_JSON_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {}


def main() -> int:
    ap = argparse.ArgumentParser(description="Import i18n CSV into the codebase.")
    ap.add_argument("csv", help="Path to the i18n CSV file")
    ap.add_argument("--dry-run", action="store_true", help="Parse and report, write nothing")
    ap.add_argument("--verify", action="store_true", help="Run guard tests after importing")
    args = ap.parse_args()

    if not os.path.exists(args.csv):
        sys.stderr.write(f"ERROR: CSV not found: {args.csv}\n")
        return 2

    overrides = _load_overrides()
    seed = _load_seed() if not args.dry_run else {}
    dirty_langs: set = set()
    dirty_seed: set = set()
    stats = {"po": 0, "overrides": 0, "seed": 0, "skipped": 0, "missing_cells": 0}

    with open(args.csv, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for i, row in enumerate(reader, start=2):  # line 1 is the header
            key = (row.get("key") or "").strip()
            en = (row.get("en") or "").strip()
            if not key or not en:
                if key or en:
                    stats["skipped"] += 1
                    sys.stderr.write(f"  ! row {i}: missing key/en, skipped\n")
                continue
            prefix = _prefix(key)
            if prefix in ("po", "template"):
                if args.dry_run:
                    stats["po"] += 1
                else:
                    _apply_po(row, dirty_langs)
                    stats["po"] += 1
            elif prefix in ("sidebar", "siteconfig"):
                if args.dry_run:
                    stats["overrides"] += 1
                else:
                    _apply_overrides(row, overrides)
                    stats["overrides"] += 1
            elif prefix in ("product", "project"):
                if args.dry_run:
                    stats["seed"] += 1
                else:
                    _apply_seed(row, seed, dirty_seed)
                    stats["seed"] += 1
            else:
                stats["skipped"] += 1
                sys.stderr.write(f"  ! row {i}: unknown prefix '{prefix}', skipped\n")
                continue
            stats["missing_cells"] += sum(
                1 for lang in LANGS if not (row.get(lang) or "").strip()
            )

    if args.dry_run:
        print("[dry-run] no files written")
    else:
        if overrides:
            with open(OVERRIDES_PATH, "w", encoding="utf-8") as fh:
                json.dump(overrides, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
        if dirty_seed:
            with open(SEED_JSON_PATH, "w", encoding="utf-8") as fh:
                json.dump(seed, fh, ensure_ascii=False, indent=2)
                fh.write("\n")
            try:
                subprocess.run(
                    [sys.executable, "manage.py", "regenerate_seed"],
                    cwd=REPO_ROOT, check=True, capture_output=True, text=True,
                )
            except (subprocess.CalledProcessError, OSError) as exc:
                sys.stderr.write(f"  ! regenerate_seed failed ({exc}); seed_data.json updated, run manually.\n")

    print(
        "Import summary:\n"
        f"  gettext (.po/.mo) rows : {stats['po']}\n"
        f"  sidebar/siteconfig rows : {stats['overrides']}\n"
        f"  seed (product/project)  : {stats['seed']}\n"
        f"  skipped                 : {stats['skipped']}\n"
        f"  empty translation cells : {stats['missing_cells']}\n"
        f"  langs recompiled (.mo)  : {', '.join(sorted(dirty_langs)) or 'none'}"
    )

    if args.verify and not args.dry_run:
        print("\nRunning guard tests...")
        rc = subprocess.run(
            [sys.executable, "manage.py", "test",
             "pages.I18nCatalogGuardTests", "pages.DataDrivenTranslationTests",
             "--keepdb"],
            cwd=REPO_ROOT,
        ).returncode
        return rc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
