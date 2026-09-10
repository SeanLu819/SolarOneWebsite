#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Visual Review — 本地可视化评审脚本（解决"改完只能靠部署才看得到"的黑盒问题）

做什么：
  1. 自动拉起 Django dev server（随机端口）
  2. 用 Playwright 驱动本机 Edge，按 手机 / 平板 / 桌面 三档视口渲染指定页面
  3. 扫描"横向溢出"元素（元素级 scrollWidth > clientWidth，排除合法滚动容器）
  4. 生成一份自包含 HTML 报告：三档截图并排 + 溢出元素清单 + 关键测量值

用法：
    python scripts/e2e/visual_review.py
    python scripts/e2e/visual_review.py --paths /products/rt400hb/ /products/
    python scripts/e2e/visual_review.py --widths 390 768 --no-fullpage

产物：
    .workbuddy/preview/review_<时间戳>/index.html   ← 浏览器直接打开
    .workbuddy/preview/review_<时间戳>/shots/*.png

注意：本脚本在 scripts/e2e/ 下，项目根目录 = Path(__file__).resolve().parents[2]
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATHS = [
    "/",
    "/products/",
    "/products/rt400hb/",
    "/projects/",
]

# 视口定义：(标签, 宽, 高, 是否模拟移动端)
VIEWPORTS = [
    ("mobile", 390, 844, True),
    ("tablet", 768, 1024, False),
    ("desktop", 1280, 800, False),
]


# --------------------------------------------------------------------------
# 服务端
# --------------------------------------------------------------------------
def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port: int) -> subprocess.Popen:
    """后台启动 Django dev server。"""
    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "solarone.settings")
    env["PYTHONIOENCODING"] = "utf-8"
    cmd = [
        sys.executable, "manage.py", "runserver",
        f"127.0.0.1:{port}", "--noreload", "--insecure",
    ]
    proc = subprocess.Popen(
        cmd, cwd=str(ROOT), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    # 等待端口就绪
    deadline = time.time() + 45
    while time.time() < deadline:
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            raise RuntimeError(f"dev server 启动失败：\n{out}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return proc
        except OSError:
            time.sleep(0.3)
    proc.terminate()
    raise RuntimeError("dev server 启动超时（45s）")


# --------------------------------------------------------------------------
# 浏览器侧探针
# --------------------------------------------------------------------------
SCAN_JS = r"""
() => {
  const VW = __TARGET_VW__;
  const out = [];
  const isScrollable = (cs) => {
    const ox = cs.overflowX;
    return ox === 'auto' || ox === 'scroll';
  };
  const path = (el) => {
    if (!el || el.nodeType !== 1) return '';
    const parts = [];
    let cur = el, depth = 0;
    while (cur && cur.nodeType === 1 && depth < 5) {
      let seg = cur.tagName.toLowerCase();
      if (cur.id) { parts.unshift(seg + '#' + cur.id); break; }
      const cls = (cur.className && typeof cur.className === 'string')
        ? cur.className.trim().split(/\s+/).slice(0, 2).join('.') : '';
      if (cls) seg += '.' + cls;
      parts.unshift(seg);
      cur = cur.parentElement; depth++;
    }
    return parts.join(' > ');
  };
  document.querySelectorAll('*').forEach((el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden') return;
    const sw = el.scrollWidth, cw = el.clientWidth;
    if (cw <= 0) return;
    if (sw - cw > 1 && !isScrollable(cs)) {
      const r = el.getBoundingClientRect();
      out.push({
        sel: path(el),
        scrollWidth: sw, clientWidth: cw, over: sw - cw,
        rectW: Math.round(r.width),
        overflowX: cs.overflowX,
      });
    }
  });
  // 按超出量降序，去重
  const seen = new Set(); const uniq = [];
  out.sort((a, b) => b.over - a.over);
  for (const it of out) {
    const k = it.sel + '|' + it.over;
    if (seen.has(k)) continue;
    seen.add(k); uniq.push(it);
    if (uniq.length >= 12) break;
  }
  return {
    // 页面级：必须用"设定视口宽度"做基准。
    // is_mobile=True 时内容过宽会把 window.innerWidth 一起撑大，
    // 用 innerWidth 当基准会让断言永远为 0（自我掩盖）。
    docScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body ? document.body.scrollWidth : 0,
    innerWidth: window.innerWidth,
    targetVW: VW,
    pageOverflow: document.documentElement.scrollWidth - VW,
    overflow: uniq,
  };
}
"""


def _slug(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_") or "root"


def run(playwright, base: str, paths, widths, fullpage: bool, outdir: Path):
    browser = playwright.chromium.launch(channel="msedge")
    results = []

    for p in paths:
        url = base + p
        entry = {"path": p, "url": url, "shots": {}, "data": {}}
        for label, w, h, mobile in VIEWPORTS:
            if widths and w not in widths:
                continue
            ctx = browser.new_context(
                viewport={"width": w, "height": h},
                device_scale_factor=2 if mobile else 1,
                is_mobile=mobile,
                has_touch=mobile,
            )
            page = ctx.new_page()
            try:
                # domcontentloaded 比 load 快得多：只等 HTML 解析 + 同步脚本，
                # 不等所有图片/iframe/web 字体。配合 wait_for_timeout 给静态资源
                # 留时间渲染，足够拿到真实 layout。
                page.goto(url, wait_until="domcontentloaded", timeout=25000)
                page.wait_for_timeout(1200)  # 等轮播/字体/懒加载稳定
                probe = page.evaluate(
                    SCAN_JS.replace("__TARGET_VW__", str(w))
                )
                shot = outdir / "shots" / f"{_slug(p)}__{label}.png"
                shot.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(shot), full_page=fullpage)
                entry["shots"][label] = shot.relative_to(outdir).as_posix()
                entry["data"][label] = probe
            except Exception as e:  # noqa: BLE001
                entry["data"][label] = {"error": str(e)[:300]}
            finally:
                ctx.close()
        results.append(entry)
    browser.close()
    return results


# --------------------------------------------------------------------------
# HTML 报告
# --------------------------------------------------------------------------
CSS = """
:root{--bg:#0f1219;--card:#171b26;--line:#2a3040;--ink:#e8ecf5;--mute:#98a2b8;
--ok:#3ddc97;--warn:#ffb454;--bad:#ff6b6b;--accent:#5b9cff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.6 -apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;padding:28px}
h1{font-size:22px;margin:0 0 4px}
h2{font-size:17px;margin:0 0 14px;padding-bottom:8px;border-bottom:1px solid var(--line)}
.sub{color:var(--mute);font-size:13px;margin-bottom:24px}
.page{background:var(--card);border:1px solid var(--line);border-radius:14px;
padding:20px;margin-bottom:22px}
.page-head{display:flex;align-items:baseline;gap:12px;margin-bottom:16px}
.path{font-family:ui-monospace,Consolas,monospace;font-size:15px;color:var(--accent)}
.badge{font-size:11px;padding:2px 9px;border-radius:20px;font-weight:600}
.b-ok{background:rgba(61,220,151,.15);color:var(--ok)}
.b-bad{background:rgba(255,107,107,.15);color:var(--bad)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.vp{background:#0b0e14;border:1px solid var(--line);border-radius:10px;overflow:hidden}
.vp-head{display:flex;justify-content:space-between;align-items:center;
padding:8px 12px;border-bottom:1px solid var(--line);font-size:12px}
.vp-name{font-weight:600;letter-spacing:.04em;text-transform:uppercase}
.vp-dim{color:var(--mute);font-family:ui-monospace,Consolas,monospace}
.vp img{display:block;width:100%;height:auto;background:#fff}
.ov{margin-top:12px;font-size:12.5px}
.ov-title{color:var(--mute);margin-bottom:6px}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line)}
th{color:var(--mute);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.05em}
td.num{font-family:ui-monospace,Consolas,monospace;text-align:right}
.sel{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;color:var(--warn);
word-break:break-all}
.err{background:rgba(255,107,107,.1);color:var(--bad);padding:10px;border-radius:8px;font-size:12.5px}
.note{background:rgba(91,156,255,.1);border-left:3px solid var(--accent);
padding:12px 16px;border-radius:0 8px 8px 0;margin-bottom:22px;font-size:13px;color:#cfd8ea}
.kv{display:flex;gap:18px;flex-wrap:wrap;margin-top:10px;font-size:12px;color:var(--mute)}
.kv b{color:var(--ink);font-family:ui-monospace,Consolas,monospace}
"""


def render(results, outdir: Path, generated: str) -> Path:
    order = [v[0] for v in VIEWPORTS]
    parts = [
        "<!doctype html><html lang='zh-CN'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>响应式可视化评审 {generated}</title><style>{CSS}</style></head><body>",
        "<h1>响应式可视化评审报告</h1>",
        f"<div class='sub'>生成时间 {generated} &nbsp;·&nbsp; "
        "三档视口（390 手机 / 768 平板 / 1280 桌面）真实渲染截图 + 横向溢出扫描</div>",
        "<div class='note'><b>怎么读这份报告：</b>每个页面三张截图并排，"
        "手机档应能看到完整内容、不应出现需要左右拖动才能看全的区块。"
        "下方表格列出 <b>横向溢出元素</b>（元素内容宽度 &gt; 可见宽度，"
        "且自身不是合法的横向滚动容器）——这些就是手机上「只能看到一小部分」的元凶。"
        "已排除 <code>overflow-x:auto/scroll</code> 的表格容器（那是刻意允许横向滚动的）。</div>",
    ]

    for r in results:
        worst = 0
        for lbl in order:
            d = r["data"].get(lbl) or {}
            worst = max(worst, int(d.get("pageOverflow") or 0))
        cls = "b-ok" if worst <= 1 else "b-bad"
        txt = "无页面级溢出" if worst <= 1 else f"页面级溢出 {worst}px"
        parts.append(f"<div class='page'><div class='page-head'>"
                     f"<span class='path'>{r['path']}</span>"
                     f"<span class='badge {cls}'>{txt}</span></div>")

        # 截图
        parts.append("<div class='grid'>")
        for lbl in order:
            if lbl not in r["shots"]:
                continue
            w = h = ""
            for L, W, H, _ in VIEWPORTS:
                if L == lbl:
                    w, h = W, H
            dims = {"mobile": "iPhone 12", "tablet": "iPad", "desktop": "Desktop"}[lbl]
            parts.append(
                f"<div class='vp'><div class='vp-head'>"
                f"<span class='vp-name'>{dims}</span>"
                f"<span class='vp-dim'>{w}×{h}</span></div>"
                f"<a href='{r['shots'][lbl]}' target='_blank'>"
                f"<img src='{r['shots'][lbl]}' loading='lazy'></a></div>"
            )
        parts.append("</div>")

        # 溢出表
        rows = []
        for lbl in order:
            d = r["data"].get(lbl)
            if not d:
                continue
            if "error" in d:
                rows.append(f"<tr><td colspan='5'><div class='err'>"
                            f"[{lbl}] {d['error']}</div></td></tr>")
                continue
            for it in d.get("overflow", []):
                rows.append(
                    f"<tr><td>{lbl}</td>"
                    f"<td class='sel'>{it['sel']}</td>"
                    f"<td class='num'>{it['scrollWidth']}</td>"
                    f"<td class='num'>{it['clientWidth']}</td>"
                    f"<td class='num' style='color:var(--bad)'>+{it['over']}</td></tr>"
                )
        if rows:
            parts.append("<div class='ov'><div class='ov-title'>横向溢出元素（超出量降序）</div>"
                         "<table><thead><tr><th>视口</th><th>元素</th>"
                         "<th style='text-align:right'>内容宽</th>"
                         "<th style='text-align:right'>可见宽</th>"
                         "<th style='text-align:right'>超出</th></tr></thead>"
                         f"<tbody>{''.join(rows)}</tbody></table></div>")
        else:
            parts.append("<div class='ov'><div class='ov-title'>"
                         "横向溢出元素：无 ✔</div></div>")

        # 测量值
        kv = []
        for lbl in order:
            d = r["data"].get(lbl) or {}
            if "error" in d:
                continue
            kv.append(f"<span>{lbl}: docScroll=<b>{d.get('docScrollWidth')}</b> "
                      f"innerWidth=<b>{d.get('innerWidth')}</b> "
                      f"基准=<b>{d.get('targetVW')}</b></span>")
        if kv:
            parts.append(f"<div class='kv'>{''.join(kv)}</div>")

        parts.append("</div>")

    parts.append("</body></html>")
    out = outdir / "index.html"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paths", nargs="*", default=DEFAULT_PATHS)
    ap.add_argument("--widths", nargs="*", type=int, default=None,
                    help="只跑指定宽度，如 --widths 390 768")
    ap.add_argument("--no-fullpage", action="store_true",
                    help="只截首屏（默认整页长截图）")
    ap.add_argument("--out", default=str(ROOT / ".workbuddy" / "preview"))
    args = ap.parse_args()

    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = Path(args.out) / f"review_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)

    port = _free_port()
    srv = start_server(port)
    base = f"http://127.0.0.1:{port}"
    print(f"[server] {base}")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            results = run(pw, base, args.paths, set(args.widths or []),
                          not args.no_fullpage, outdir)
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=8)
        except Exception:  # noqa: BLE001
            srv.kill()

    report = render(results, outdir, dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(f"[report] {report}")
    # 打印摘要
    for r in results:
        for lbl in ("mobile", "tablet", "desktop"):
            d = r["data"].get(lbl) or {}
            if not d:
                continue
            if "error" in d:
                print(f"  {r['path']:28s} [{lbl:7s}] ERROR {d['error'][:160]}")
            else:
                print(f"  {r['path']:28s} [{lbl:7s}] "
                      f"docScroll={d.get('docScrollWidth')} 基准={d.get('targetVW')} "
                      f"溢出={d.get('pageOverflow')} 元素数={len(d.get('overflow', []))}")


if __name__ == "__main__":
    main()
