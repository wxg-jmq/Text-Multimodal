#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clipboard_save.py — 从系统剪贴板提取图片保存为文件（跨平台）

用途：客户端拦截"粘贴图片"输入（纯文本模型）时，用户刚粘贴的图片仍留在
系统剪贴板——本脚本把它提取出来，技能即可走委托管线识别，实现"直接扔图"。

用法:
  python clipboard_save.py               # 保存到当前目录 clip-<时间戳>.png
  python clipboard_save.py out.png       # 指定输出路径
  python clipboard_save.py --check       # 仅检测剪贴板是否有图片

平台支持:
  Windows: PowerShell 内置（System.Windows.Forms），零依赖
  macOS:   需 pngpaste（brew install pngpaste）；无则提示安装
  Linux:   需 xclip（sudo apt install xclip / 等价包）
"""
import argparse
import subprocess
import sys
import time
from pathlib import Path


def run(cmd, timeout=20):
    try:
        return subprocess.run(cmd, capture_output=True, timeout=timeout)
    except Exception:
        return None


def save_windows(out):
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$img = [System.Windows.Forms.Clipboard]::GetImage(); "
        "if ($img -eq $null) { Write-Error 'NO_IMAGE'; exit 1 }; "
        f"$img.Save('{out}')"
    )
    r = run(['powershell', '-NoProfile', '-Command', ps])
    return r is not None and r.returncode == 0 and Path(out).exists()


def save_macos(out):
    r = run(['pngpaste', str(out)])
    if r is not None and r.returncode == 0 and Path(out).stat().st_size > 0:
        return True
    print('macOS 需要 pngpaste：brew install pngpaste', file=sys.stderr)
    return False


def save_linux(out):
    r = run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'])
    if r is not None and r.returncode == 0 and r.stdout:
        Path(out).write_bytes(r.stdout)
        return True
    print('Linux 需要 xclip：sudo apt install xclip', file=sys.stderr)
    return False


def main():
    ap = argparse.ArgumentParser(description='从系统剪贴板提取图片')
    ap.add_argument('out', nargs='?', default=None, help='输出路径（缺省 clip-<时间戳>.png）')
    ap.add_argument('--check', action='store_true', help='仅检测剪贴板是否有图片')
    a = ap.parse_args()

    if sys.platform.startswith('win'):
        saver, plat = save_windows, 'Windows'
    elif sys.platform == 'darwin':
        saver, plat = save_macos, 'macOS'
    else:
        saver, plat = save_linux, 'Linux'

    if a.check:
        out = Path('__clip_check__.png')
        ok = saver(str(out))
        if ok:
            print(f'✅ 剪贴板有图片（{plat}）')
            out.unlink(missing_ok=True)
            return
        print(f'❌ 剪贴板没有图片（{plat}）——请先复制/粘贴一张图片再试')
        sys.exit(1)

    out = Path(a.out or f'clip-{time.strftime("%Y%m%d-%H%M%S")}.png')
    if saver(str(out)):
        print(f'✅ 已从剪贴板提取图片: {out.resolve()}')
        print(f'相对路径: {out.as_posix()}')
        print('下一步：用识别模型走委托管线（recognize <该路径>）')
    else:
        print(f'❌ 提取失败（{plat}）——剪贴板可能没有图片，或缺少依赖工具')
        sys.exit(1)


if __name__ == '__main__':
    main()
