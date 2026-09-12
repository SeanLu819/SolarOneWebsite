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
# 补 375(iPhone SE/8) 与 360(安卓常见宽) 强化 §15.3 F7 全断点无横向溢出
SIZES = [(320, 568), (360, 800), (375, 667), (390, 844), (768, 1024), (820, 1180), (1024, 768), (1440, 900)]
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

def run_phase2_review(browser):
    """§15.3 阶段二真机复核 7 项 —— 自动化闭环（替代一次性真机点检）。

    设计原则（见 §6.8.3 / §15.4 遗留说明）：
    - iOS 特有项（N-6 / N-11）与防御性 CSS 项：**断言「防御性写法是否存在」**，
      比模拟真机更可靠、可无限重跑。故以源码级断言为主。
    - 可在浏览器内验证的项（F9/F10/F8/F11/N-16 机制）：叠加浏览器级渲染断言。
    """
    base_css = (BASE_DIR / "static/css/base.css").read_text(encoding="utf-8")
    base_html = (BASE_DIR / "templates/base.html").read_text(encoding="utf-8")
    products_html = (BASE_DIR / "templates/products.html").read_text(encoding="utf-8")
    pd_html = (BASE_DIR / "templates/product_detail.html").read_text(encoding="utf-8")

    print("\n=== §15.3 源码级防御断言（N-11/N-6/F10/F9/F8/N-16/F11）===")
    # N-11: 平板 hero 用 svh 跟随动态视口，100vh 作降级，二者成对
    check("min-height: 100vh" in base_css and "min-height: 100svh" in base_css,
          "N-11 .hero 平板 `100vh`+`100svh` 成对降级 (base.css)")
    # N-6: Cookie 横幅不被 Home Indicator / 安卓工具栏遮 —— max() + safe-area 兜底
    check("padding-bottom:max(20px, calc(env(safe-area-inset-bottom, 0px) + 8px))" in base_html,
          "N-6 Cookie 横幅 `padding-bottom:max(20px, calc(env(safe-area-inset-bottom,0px)+8px))` (base.html)")
    # F10: 移动端长项目名允许换行不截断
    check("white-space: normal; overflow: visible" in base_css,
          "F10 `.project-card-title` 移动端 `white-space:normal` (base.css)")
    # F9: products banner 弃固定 aspect-ratio，改 min-height 杜绝超窄屏裁切
    check("min-height: 120px" in products_html and "aspect-ratio:1920/442" not in products_html,
          "F9 products banner 弃 `aspect-ratio` 改 `min-height` (products.html)")
    # F8: 详情页主区折单列从 900 提前到 1024（平板 901-1024 不拥挤）
    check("@media (max-width: 1024px)" in pd_html and "grid-template-columns: 1fr" in pd_html,
          "F8 详情页 `.detail-grid` ≤1024 折单列 (product_detail.html)")
    # N-16: 全局滑动提示样式 + 订购表实例已接（数据触发时自动显形）
    check(".scroll-hint {" in base_css,
          "N-16 `.scroll-hint` 全局样式存在 (base.css)")
    check('class="scroll-hint"' in pd_html,
          "N-16 订购表 `scroll-hint` 实例已接 (product_detail.html)")
    # F11: 无 JS 时 `.reveal` 默认可见 —— 依赖 html.js 前缀 + 注入
    check("classList.add('js')" in base_html and "html.js .reveal {" in base_css,
          "F11 `html.js` 前缀 + 注入存在，无 JS 时 `.reveal` 默认可见 (base.html/base.css)")

    # ---- 浏览器级渲染断言 ----
    print("\n=== §15.3 浏览器级模拟断言 ===")
    # F11: 关 JS 上下文，.reveal 必须全部可见（opacity != 0）
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        is_mobile=True, has_touch=True, device_scale_factor=3,
        java_script_enabled=False,
    )
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/contact/", wait_until="domcontentloaded")
    pg.wait_for_timeout(300)
    res = pg.evaluate(
        "(() => { const all=document.querySelectorAll('.reveal');"
        " const hidden=[...all].filter(el=>parseFloat(getComputedStyle(el).opacity)===0);"
        " return {total:all.length, hidden:hidden.length}; })()")
    check(res["total"] > 0 and res["hidden"] == 0,
          f"F11 无 JS 时 `.reveal` 全可见 (total={res['total']}, hidden={res['hidden']})")
    ctx.close()

    # F10: /projects/ 移动端 .project-card-title 计算 white-space == normal
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True, device_scale_factor=3)
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/projects/", wait_until="domcontentloaded")
    pg.wait_for_timeout(300)
    ws = pg.evaluate(
        "Array.from(document.querySelectorAll('.project-card-title')).map(el=>getComputedStyle(el).whiteSpace)")
    check(bool(ws) and all(v == "normal" for v in ws),
          f"F10 `/projects/` 移动端 `.project-card-title` white-space=normal (sample={ws[:3]})")
    ctx.close()

    # F9: /products/ 320 & 360 下 banner 无 aspect-ratio + 标题不裁切
    for w in (320, 360):
        ctx = browser.new_context(viewport={"width": w, "height": 720},
                                  is_mobile=True, has_touch=True, device_scale_factor=3)
        pg = ctx.new_page()
        pg.goto(BASE_URL + "/products/", wait_until="domcontentloaded")
        try:
            pg.wait_for_function("document.fonts.status === 'loaded'", timeout=3000)
        except Exception:
            pass
        pg.wait_for_timeout(300)
        ar = pg.evaluate("getComputedStyle(document.querySelector('.products-banner')).aspectRatio")
        mh = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.products-banner')).minHeight)")
        clip = pg.evaluate(
            "(() => { const b=document.querySelector('.products-banner');"
            " const t=document.querySelector('.products-banner-title'); if(!b||!t) return null;"
            " const bb=b.getBoundingClientRect(), tb=t.getBoundingClientRect();"
            " return tb.right - bb.right; })()")
        ok = (ar in ("auto", "normal", "")) and mh >= 80 and (clip is None or clip <= 1)
        check(ok, f"F9 `/products/` {w}px banner 无 aspect-ratio(ar={ar}, minH={mh}, titleOverflow={clip})")
        ctx.close()

    # F8: 详情页 1024px 下 .detail-grid 单列（1 个栅格轨道）
    ctx = browser.new_context(viewport={"width": 1024, "height": 768})
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/products/rt410-series/", wait_until="domcontentloaded")
    pg.wait_for_timeout(300)
    gtc = pg.evaluate("getComputedStyle(document.querySelector('.detail-grid')).gridTemplateColumns")
    tracks = len([t for t in gtc.split() if t.strip()])
    check(tracks == 1, f"F8 详情页 1024px `.detail-grid` 单列 (tracks={tracks}: '{gtc}')")
    ctx.close()

    # N-16 机制：产品详情页移动端，能量表容器不得真实横滑（自然换行，无需提示）；
    # 若页面存在 scroll-hint 实例则必须可见。
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True, device_scale_factor=3)
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/products/rt400hb/", wait_until="domcontentloaded")
    pg.wait_for_timeout(300)
    energy_overflow = pg.evaluate(
        "(() => { const w=document.querySelector('.detail-energy-table-wrap');"
        " if(!w) return null; return w.scrollWidth - w.clientWidth; })()")
    check(energy_overflow is not None and energy_overflow <= 1,
          f"N-16 能量表移动端不横滑 (overflow={energy_overflow}px)")
    hint_count = pg.locator(".scroll-hint").count()
    if hint_count > 0:
        check(pg.locator(".scroll-hint").first.is_visible(),
              "N-16 存在的 scroll-hint 移动端可见")
    else:
        print("  [SKIP] N-16 当前无产品含 ordering_cols → scroll-hint 休眠（机制已接，数据触发即显形）")
    ctx.close()


def run_phase3_review(browser):
    """阶段三 F12-F15 + N-13/N-14/N-15/N-17 —— 自动化回归（F15）。

    覆盖：N-13 about 内联 grid hack 消除 + 收敛；N-14 死代码删除；
    N-15 theme-color 跟随；N-17 抽屉焦点管理；F13 RTL(inset-inline-start)。
    源码级断言为主，关键交互项叠加浏览器级渲染断言。
    """
    base_css = (BASE_DIR / "static/css/base.css").read_text(encoding="utf-8")
    base_html = (BASE_DIR / "templates/base.html").read_text(encoding="utf-8")
    about_html = (BASE_DIR / "templates/about.html").read_text(encoding="utf-8")
    ps_html = (BASE_DIR / "templates/product_series.html").read_text(encoding="utf-8")
    pd_html = (BASE_DIR / "templates/product_detail.html").read_text(encoding="utf-8")

    print("\n=== 阶段三 源码级防御断言（N-13/N-14/N-15/N-17/F13）===")
    # N-13 / F12：about.html 内联 <style> 块已删除，属性选择器 hack 消失；
    #         .about-services-grid 已收敛进 base.css
    check(about_html.count("<style>") == 0,
          "N-13/F12 about.html 内联 <style> 块已移除")
    check("div[style*=\"grid-template-columns: 1fr 1fr 1fr\"]" not in about_html,
          "N-13 about.html 属性选择器 hack 已删除")
    check("grid-template-columns: 1fr 1fr 1fr" not in about_html,
          "N-13 about.html 内联 3 列 grid 已收敛")
    check(".about-services-grid {" in base_css,
          "N-13/F12 `.about-services-grid` 已入 base.css")

    # N-14：数字滚动死代码（data-count / about-stat）已从 base.html 移除
    check("[data-count]" not in base_html and ".about-stat" not in base_html,
          "N-14 死代码 data-count/.about-stat 已从 base.html 删除")

    # N-15：theme-color meta + JS 跟随 data-theme
    check('<meta name="theme-color"' in base_html and "themeColorMeta" in base_html,
          "N-15 theme-color meta 已注入 base.html")
    check("meta.setAttribute('content', isLight ? '#F5F7FA' : '#080D1F')" in base_html,
          "N-15 theme-color 随 data-theme 切换（深 #080D1F / 浅 #F5F7FA）")

    # N-17：移动抽屉 a11y —— role/aria-modal + 焦点管理函数
    check('role="dialog"' in base_html and 'aria-modal="true"' in base_html,
          "N-17 #mobilePanel role=dialog + aria-modal=true")
    check("setBackgroundInert" in base_html and "focusablesInPanel" in base_html,
          "N-17 背景 inert / 焦点陷阱函数已接")

    # F13：series-hero 物理 left → inset-inline-start，并补 [dir=rtl] 变体
    check("inset-inline-start: 32px" in ps_html and "inset-inline-start: 32px" in pd_html,
          "F13 series-hero 物理 `left` → `inset-inline-start` (series/detail)")
    check('[dir="rtl"] .series-hero-content' in ps_html and '[dir="rtl"] .series-hero-content' in pd_html,
          "F13 补 `[dir=rtl] .series-hero-content` 右对齐变体")
    check('[dir="rtl"] .series-hero-overlay' in ps_html and '[dir="rtl"] .series-hero-overlay' in pd_html,
          "F13 补 `[dir=rtl] .series-hero-overlay` 镜像渐变")

    # ---- 浏览器级渲染断言 ----
    print("\n=== 阶段三 浏览器级模拟断言 ===")
    # N-15：theme-color meta 存在且默认深色；桌面点导航主题切换后跟随浅色
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(200)
    meta0 = pg.evaluate("(()=>{const m=document.querySelector('meta[name=theme-color]');return m?m.getAttribute('content'):null;})()")
    check(meta0 == "#080D1F", f"N-15 默认深色 theme-color={meta0}")
    # 导航栏主题切换（移动端 .theme-toggle 在抽屉内不可见，故用桌面视口点 .nav 内那个）
    btn = pg.locator(".nav .theme-toggle")
    if btn.is_visible():
        btn.click()
        pg.wait_for_timeout(150)
        meta1 = pg.evaluate("(()=>{const m=document.querySelector('meta[name=theme-color]');return m?m.getAttribute('content'):null;})()")
        check(meta1 == "#F5F7FA", f"N-15 切浅色后 theme-color={meta1}")
    else:
        print("  [SKIP] N-15 导航主题切换按钮不可见，跳过跟随断言")
    ctx.close()

    # N-17：手机端打开抽屉 → 背景（footer）置 inert；关闭后恢复
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True, device_scale_factor=3)
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/", wait_until="domcontentloaded")
    pg.wait_for_timeout(200)
    role = pg.get_attribute("#mobilePanel", "role")
    am = pg.get_attribute("#mobilePanel", "aria-modal")
    check(role == "dialog" and am == "true",
          f"N-17 #mobilePanel role={role} aria-modal={am}")
    pg.locator("#hamburgerBtn").click()
    pg.wait_for_timeout(250)
    bg_inert = pg.evaluate("(()=>{const f=document.querySelector('footer');return f?f.inert:null;})()")
    check(bg_inert is True, f"N-17 抽屉打开时背景 footer.inert={bg_inert}")
    panel_focus = pg.evaluate("document.activeElement === document.getElementById('mobileClose')"
                              " || document.activeElement.closest('#mobilePanel') !== null")
    check(panel_focus, "N-17 抽屉打开后焦点进入面板")
    pg.locator("#mobileClose").click()
    pg.wait_for_timeout(250)
    bg_restored = pg.evaluate("(()=>{const f=document.querySelector('footer');return f?f.inert:null;})()")
    check(bg_restored is False, f"N-17 抽屉关闭后背景 footer.inert 恢复={bg_restored}")
    ctx.close()

    # N-13：/about/ 移动端 .about-services-grid / .about-optics-grid 计算为 grid，
    #      且页面无残留内联 grid-template-columns
    ctx = browser.new_context(viewport={"width": 390, "height": 844},
                              is_mobile=True, has_touch=True, device_scale_factor=3)
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/about/", wait_until="domcontentloaded")
    pg.wait_for_timeout(300)
    grids = pg.evaluate(
        "(()=>{const sel=['.about-services-grid','.about-optics-grid'];"
        " const disp=sel.map(s=>{const e=document.querySelector(s);"
        " return e?getComputedStyle(e).display:'MISSING';});"
        " const inline=document.querySelectorAll('[style*=grid-template-columns]').length;"
        " return {disp, inline};})()")
    check(grids["disp"][0] == "grid" and grids["disp"][1] == "grid",
          f"N-13 `/about/` 两栅格计算为 grid (services={grids['disp'][0]}, optics={grids['disp'][1]})")
    check(grids["inline"] == 0, f"N-13 `/about/` 无残留内联 grid-template-columns (count={grids['inline']})")
    ctx.close()

    # F13：LTR 详情页 .series-hero-content 计算 left=32px；RTL 阿语版计算 right=32px
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/products/rt410-series/", wait_until="domcontentloaded")
    pg.wait_for_timeout(300)
    ltr_left = pg.evaluate(
        "(()=>{const e=document.querySelector('.series-hero-content');return e?getComputedStyle(e).left:'MISSING';})()")
    check(ltr_left == "32px", f"F13 LTR `.series-hero-content` left={ltr_left}")
    ctx.close()

    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.goto(BASE_URL + "/ar/products/rt410-series/", wait_until="domcontentloaded")
    pg.wait_for_timeout(300)
    rtl = pg.evaluate(
        "(()=>{const e=document.querySelector('.series-hero-content');"
        " if(!e) return {miss:true, dir:document.documentElement.dir};"
        " return {miss:false, dir:document.documentElement.dir, right:getComputedStyle(e).right,"
        " left:getComputedStyle(e).left};})()")
    if rtl.get("miss"):
        print(f"  [SKIP] F13 RTL 页面无 .series-hero-content (dir={rtl.get('dir')})")
    else:
        check(rtl["dir"] == "rtl" and rtl["right"] == "32px",
              f"F13 RTL `.series-hero-content` dir={rtl['dir']} right={rtl['right']} (left={rtl['left']})")
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
                run_phase2_review(browser)
                run_phase3_review(browser)
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