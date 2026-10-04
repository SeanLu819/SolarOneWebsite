#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Site speed probe — repeatable TTFB / total-time baseline for the live site.

Why this exists
---------------
The project used to judge "the site is fast" by eyeballing a screenshot. This
script turns it into a number you can diff week over week, and it fails loudly
when a regression slips in.

It measures the split that actually matters for a Vercel + Django site:
    dns  -> name resolution
    tcp  -> TCP handshake
    tls  -> TLS handshake
    ttfb -> time to first byte  (network + function cold/warm start + render)
    total-> end of body download
On a cross-border request (CN -> Vercel edge) the handshake is often half the
budget, so a raw "TTFB is 0.7s" is meaningless without the breakdown.

Usage
-----
    E:/Python/python3/python.exe scripts/e2e/perf_probe.py
    E:/Python/python3/python.exe scripts/e2e/perf_probe.py --repeats 5 \
        --origin https://www.solaronelighting.com / /products/ /projects/football/

Exit code: 1 when any URL is slower than --ttfb-budget (default 800 ms) or
--total-budget (default 1500 ms), so it can run in CI.

Notes
-----
* ``--noproxy '*'`` is forced on because the dev machine runs Clash, which
  hijacks local and sometimes LAN traffic and silently inflates the numbers.
* ``--compressed`` is always on: Vercel serves Brotli, and without the request
  header the origin answers uncompressed, skewing the byte counts.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import os
import subprocess
import sys

DEFAULT_ORIGIN = "https://www.solaronelighting.com"
DEFAULT_PATHS = [
    "/",
    "/products/",
    "/projects/",
    "/projects/football/",
    "/projects/tennis/",
    # Real slug taken from sitemap.xml, NOT from memory — picking one by hand
    # produced a 404 here (stadium-led-floodlights) and poisoned the baseline.
    "/products/mseries-gs/",
    "/news/",
]
TIMEOUT = "25"


def measure(origin: str, path: str, repeats: int) -> list:
    """Return one dict per measured request."""
    url = origin.rstrip("/") + path
    fmt = (
        "dns=%{time_namelookup} tcp=%{time_connect} tls=%{time_appconnect} "
        "ttfb=%{time_starttransfer} total=%{time_total} size=%{size_download} "
        "code=%{http_code}"
    )
    rows = []
    for _ in range(repeats):
        cmd = [
            "curl", "-s", "-o", os.devnull,
            "--compressed",
            "--noproxy", "*",
            "--max-time", TIMEOUT,
            "-w", fmt,
            url,
        ]
        out = subprocess.run(cmd, capture_output=True, text=True)
        text = (out.stdout or "").strip()
        if not text:
            continue
        row = {}
        for part in text.split():
            if "=" not in part:
                continue
            key, _, value = part.partition("=")
            with contextlib.suppress(ValueError):
                value = float(value)
            row[key] = value
        row["url"] = url
        # A truncated or non-200 response would poison the medians (it has
        # already burned a 25 s timeout and reports size=0). Drop those rows
        # instead of reporting them as "the site is slow on this URL".
        code = int(row.get("code", 0) or 0)
        if code != 200 or not row.get("size"):
            continue
        rows.append(row)
    return rows


def median(items):
    if not items:
        return 0.0
    ordered = sorted(items)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def main() -> int:
    parser = argparse.ArgumentParser(description="SolarOne site speed probe")
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--ttfb-budget", type=float, default=800.0,
                        help="fail when the median TTFB exceeds this many ms")
    parser.add_argument("--total-budget", type=float, default=1500.0,
                        help="fail when the median total exceeds this many ms")
    args = parser.parse_args()

    rows = []
    for path in args.paths:
        # Warm the serverless function once before measuring: the first hit on
        # a cold Vercel instance cost 2.4 s once and dragged the median up.
        measure(args.origin, path, 1)
        rows.extend(measure(args.origin, path, args.repeats))

    if not rows:
        print("probe produced no measurements — is the origin reachable?")
        return 2

    per_url = {}
    for row in rows:
        per_url.setdefault(row["url"], []).append(row)

    buf = io.StringIO()
    buf.write("%-58s %7s %7s %7s %7s %7s %8s\n"
              % ("url", "dns", "tcp", "tls", "ttfb", "total", "KB"))
    buf.write("-" * 104 + "\n")

    failing = []
    for url, items in per_url.items():
        dns = median([i.get("dns", 0) for i in items]) * 1000
        tcp = median([i.get("tcp", 0) for i in items]) * 1000
        tls = median([i.get("tls", 0) for i in items]) * 1000
        ttfb = median([i.get("ttfb", 0) for i in items]) * 1000
        total = median([i.get("total", 0) for i in items]) * 1000
        size = median([i.get("size", 0) for i in items])
        buf.write("%-58s %6.0f %6.0f %6.0f %6.0f %6.0f %8.1f\n"
                  % (url, dns, tcp, tls, ttfb, total, size / 1024))
        if ttfb > args.ttfb_budget:
            failing.append((url, "ttfb", ttfb))
        if total > args.total_budget:
            failing.append((url, "total", total))

    buf.write("-" * 104 + "\n")
    buf.write("all values in milliseconds (median of %d runs); "
              "budgets: ttfb<=%.0fms total<=%.0fms\n"
              % (args.repeats, args.ttfb_budget, args.total_budget))
    sys.stdout.write(buf.getvalue())

    if failing:
        for url, metric, value in failing:
            sys.stdout.write("SLOW %s=%0.fms  %s\n" % (metric, value, url))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
