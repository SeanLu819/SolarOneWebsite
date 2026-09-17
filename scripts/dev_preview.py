#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dev Preview — 用真机（手机/平板）直接访问本地开发服务。

用途：解决"改完只能等部署才能看到效果"的问题。手机和电脑连同一个 WiFi，
      跑起这个脚本，用手机浏览器打开它打印的地址即可实时看到本地改动，
      改完刷新就行，不必部署。

用法：
    python scripts/dev_preview.py              # 默认 8000 端口
    python scripts/dev_preview.py --port 8080
    python scripts/dev_preview.py --host 192.168.1.4

注意：
  - Django 的 ALLOWED_HOSTS 默认不含局域网 IP，脚本会自动补上（仅当前进程
    生效，不改 settings.py）。
  - 只应在可信的局域网（自家/公司 WiFi）使用；用完 Ctrl+C 结束。
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
from pathlib import Path

# 本脚本位于 scripts/ 下（只有一级），项目根 = parents[1]。
# 注意：scripts/e2e/ 下的脚本是两级，要用 parents[2] —— 用错层级会静默地
# 在错误目录起服务（不报错，但 manage.py 找不到）。
ROOT = Path(__file__).resolve().parents[1]


def lan_ip() -> str:
    """取本机在局域网中的 IP（不会真的发包）。"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--host", default=None, help="手动指定局域网 IP")
    args = ap.parse_args()

    ip = args.host or lan_ip()

    # settings.py: ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', ...).split(',')
    env = os.environ.copy()
    base = ["localhost", "127.0.0.1", ip]
    extra = [h for h in env.get("ALLOWED_HOSTS", "").split(",") if h.strip()]
    env["ALLOWED_HOSTS"] = ",".join(dict.fromkeys(base + extra))
    env["PYTHONIOENCODING"] = "utf-8"

    print("=" * 62)
    print("  本地预览已启动 —— 手机与电脑连同一个 WiFi 后访问：")
    print(f"      http://{ip}:{args.port}/")
    print("  电脑本机：")
    print(f"      http://127.0.0.1:{args.port}/")
    print("=" * 62)
    print("提示：改完代码刷新手机页面即可看到（模板/CSS 即时生效）。")
    print("      本地静态走 WHITENOISE_MAX_AGE=0（每次向服务器校验），无需手动")
    print("      加 ?v=；若手机上仍是旧样式，说明浏览器缓存了旧的 1 年 max-age，")
    print("      强刷 / 清一次缓存即可（此后不会再出现）。")
    print()
    print("  ⚠️ 手机打不开？按顺序排查：")
    print("     1) 手机与电脑必须是**同一个 WiFi**（不能一个走 5G 一个走 2.4G 之外的网，")
    print("        也不能手机用蜂窝数据）。")
    print("     2) Windows 防火墙会拦入站。用**管理员** PowerShell 执行一次：")
    print(f"        netsh advfirewall firewall add rule name=\"Django Dev {args.port}\" "
          f"dir=in action=allow protocol=TCP localport={args.port}")
    print("        （只需做一次，之后一直有效）")
    print("     3) 直接 `manage.py runserver` 不带地址时**只监听 127.0.0.1**，")
    print("        局域网必然连不上 —— 本脚本已用 0.0.0.0，不要改成手动 runserver。")
    print("Ctrl+C 结束\n")

    cmd = [sys.executable, "manage.py", "runserver",
           f"0.0.0.0:{args.port}", "--noreload", "--insecure"]
    try:
        subprocess.run(cmd, cwd=str(ROOT), env=env)
    except KeyboardInterrupt:
        print("\n已停止。")


if __name__ == "__main__":
    main()
