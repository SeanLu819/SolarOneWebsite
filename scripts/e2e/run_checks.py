r"""L2 — Playwright (channel="msedge") responsive regression checks.

三屏响应式方案 §6.3 / §8.4 / §6.8。零浏览器下载：直接驱动系统 Microsoft Edge
（channel="msedge"）。唯一安装成本：pip install playwright

用法：
    .\.venv\Scripts\python.exe scripts\e2e\run_checks.py

脚本自举 manage.py runserver 127.0.0.1:8123 --noreload，跑完断言后关闭。
截图存 screenshots/<视口>-<页面>.png。任何断言失败 → 退出码 1。
覆盖：无横向滚动、手机端导航契约（F1'/F2'）、F4' 侧栏默认收起+点击展开（≤900px）、
N-1 输入框 computed font-size ≥16px（§6.8.3 静态防御）、N-10 overflow-wrap=anywhere、
N-8 reduced-motion 下 scroll-behavior=auto。
"""
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
PORT = 8123
BASE_URL = f"http://127.0.0.1:{PORT}"
SHOTS = BASE_DIR / "screenshots"

PAGES = ["/", "/products/", "/projects/", "/news/", "/about/", "/contact/"]
# N-12/F7: 覆盖 1024–1279 夹缝区（900 拆栏 / 1024 栅格的中间地带）+ 平板竖屏
SIZES = [(320, 568), (390, 844), (768, 1024), (820, 1180), (1024, 768), (1440, 900)]
SIDEBAR_PAGES = ("/products/", "/projects/", "/news/")

failures = []


def check(cond, label):
    print(f"  [{'OK ' if cond else 'FAIL'}] {label}")
    if not cond:
        failures.append(label)


def wait_for_server(timeout=40):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(BASE_URL + "/", timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False

def run_checks(browser):
    for w, h in SIZES:
        is_phone = w < 768
        ctx = browser.new_context(
            viewport={"width": w, "height": h},
            is_mobile=(w <= 768),   # §6.8.1: is_mobile+has_touch 才是真移动端模拟
            has_touch=(w <= 768),
            device_scale_factor=3 if is_phone else (2 if w == 768 else 1),
        )
        pg = ctx.new_page()
        print(f"\n=== viewport {w}x{h} ===")
        for url in PAGES:
            slug = url.strip("/") or "home"
            pg.goto(BASE_URL + url, wait_until="domcontentloaded")
            # 320px 档在 webfont 加载期有 layout 瞬态（≤1.6s 自愈，见 v1.1.6）：
            # 等字体就绪再量，避免把瞬态当回归（超时兜底不阻塞）
            try:
                pg.wait_for_function("document.fonts.status === 'loaded'", timeout=3000)
            except Exception:
                pass
            pg.wait_for_timeout(200)

            # 1) 全站：无横向滚动
            #    N-19：基准必须用「设定的视口宽度 w」，不能用 window.innerWidth。
            #    is_mobile=True 下内容过宽会把 layout viewport 一起撑大
            #    （实测设定 320 → innerWidth 报 364），用 innerWidth 作基准会让
            #    溢出自我掩盖、断言恒绿。同时把 innerWidth 一并报出便于诊断。
            iw = pg.evaluate("window.innerWidth")
            sw = pg.evaluate("document.documentElement.scrollWidth")
            delta = sw - w
            check(delta <= 1,
                  f"{url} no horizontal overflow "
                  f"(scrollWidth={sw} vs viewport={w}, innerWidth={iw}, delta={delta}px)")

            # 2) 手机端导航契约（F1'/F2'）
            if is_phone:
                ham = pg.locator("#hamburgerBtn")
                check(ham.is_visible(), f"{url} hamburger visible")
                box = ham.bounding_box()
                inside = box is not None and 0 <= box["x"] and box["x"] + box["width"] <= w
                if not inside:
                    # 320 档 webfont 加载期有 layout 瞬态（v1.1.6，≤2s 自愈）：
                    # 沉降 1.5s 后重测一次；持续失败仍如实报 FAIL
                    pg.wait_for_timeout(1500)
                    box = ham.bounding_box()
                    inside = box is not None and 0 <= box["x"] and box["x"] + box["width"] <= w
                    check(inside, f"{url} hamburger fully inside viewport (after settle)")
                else:
                    check(True, f"{url} hamburger fully inside viewport")
                check(not pg.locator(".nav-links").is_visible(),
                      f"{url} .nav-links hidden")
                check(not pg.locator(".nav-actions").is_visible(),
                      f"{url} .nav-actions hidden")

            # 3) F4' 侧栏契约：≤767px 默认收起+可展开；平板/桌面恒展开且无 toggle
            #    （F7: 折叠断点 900 → 767 收敛）
            if url in SIDEBAR_PAGES:
                label = pg.locator(".sidebar-toggle-label").first
                nav = pg.locator(".sidebar-nav").first
                if w <= 767:
                    check(label.is_visible(), f"{url} sidebar toggle label visible")
                    check(not nav.is_visible(), f"{url} sidebar collapsed by default")
                    label.click()
                    pg.wait_for_timeout(150)
                    check(nav.is_visible(), f"{url} sidebar expands on toggle")
                    label.click()
                    pg.wait_for_timeout(150)
                    check(not nav.is_visible(), f"{url} sidebar collapses back")
                else:
                    check(not label.is_visible(),
                          f"{url} sidebar toggle hidden on desktop")
                    check(nav.is_visible(),
                          f"{url} sidebar always expanded on desktop")

            # 4) N-1 静态防御（§6.8.3）：computed font-size ≥ 16px
            #    contact.html 表单控件为内联样式（无 .form-group 结构，v1.1.6 修正）；
            #    排除 honeypot（tabindex=-1，用户不可聚焦，无 iOS 放大风险）
            if url == "/contact/":
            #    N-20：必须排除 type="hidden"（其 computed font-size 是浏览器默认
            #    13.3333px，不可聚焦、无 iOS 放大风险），否则整档误报。
                fs = pg.evaluate(
                    "Array.from(document.querySelectorAll("
                    "'#contactForm input, #contactForm textarea'))"
                    ".filter(el => el.type !== 'hidden'"
                    " && el.getAttribute('tabindex') !== '-1')"
                    ".map(el => parseFloat(getComputedStyle(el).fontSize))")
                check(bool(fs) and min(fs) >= 16,
                      f"contact inputs font-size >= 16px (min={min(fs) if fs else 'n/a'})")

            # 5) N-10：全局换行保护生效
            if url == "/":
                ow = pg.evaluate("getComputedStyle(document.body).overflowWrap")
                check(ow == "anywhere", f"body overflow-wrap=anywhere (got {ow})")

            pg.screenshot(path=str(SHOTS / f"{w}x{h}-{slug}.png"))
        ctx.close()

    # 6) N-8：reduced-motion 模拟下 scroll-behavior 必须为 auto
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        is_mobile=True, has_touch=True, device_scale_factor=3,
        reduced_motion="reduce",
    )
    pg = ctx.new_page()
    print("\n=== reduced-motion (390x844) ===")
    pg.goto(BASE_URL + "/", wait_until="domcontentloaded")
    sb = pg.evaluate("getComputedStyle(document.documentElement).scrollBehavior")
    check(sb == "auto", f"reduced-motion: html scroll-behavior=auto (got {sb})")
    ctx.close()

def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("playwright 未安装。请先执行：")
        print(r"  .\.venv\Scripts\python.exe -m pip install playwright")
        return 2

    server_log = open(BASE_DIR / "_l2_server.log", "w", encoding="utf-8")
    server = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "manage.py"), "runserver",
         f"127.0.0.1:{PORT}", "--noreload"],
        cwd=BASE_DIR, stdout=server_log, stderr=subprocess.STDOUT,
    )
    try:
        if not wait_for_server():
            print(f"dev server 未能在 {PORT} 端口启动，见 _l2_server.log")
            return 2
        SHOTS.mkdir(exist_ok=True)
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(channel="msedge")
            except Exception as exc:
                print("无法启动系统 Edge（channel=msedge）：%r" % exc)
                print("请确认已安装 Microsoft Edge，或改跑 playwright install chromium")
                return 2
            try:
                run_checks(browser)
            finally:
                browser.close()
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except Exception:
            server.kill()
        server_log.close()

    print("\n==== L2 SUMMARY ====")
    if failures:
        print(f"FAILED — {len(failures)} check(s):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())