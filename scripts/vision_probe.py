#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""vision_probe.py — 纯色探测图生成器：验证候选模型是否真的能看图。

用法:
  python vision_probe.py                # 随机 16 色之一，输出 probe-<颜色名>.png
  python vision_probe.py red            # 指定颜色名（可选色见 PALETTE）
  python vision_probe.py --out x.png    # 指定输出路径

识别时把生成的 PNG 发给候选模型问："这张图片是什么颜色？"
能答出正确颜色名的模型才具备视觉能力，可作图片识别用。
"""
import argparse
import random
from PIL import Image

PALETTE = {
    'red': '#E53935', 'green': '#43A047', 'blue': '#1E88E5', 'yellow': '#FDD835',
    'orange': '#FB8C00', 'purple': '#8E24AA', 'cyan': '#00ACC1', 'pink': '#F06292',
    'brown': '#6D4C41', 'lime': '#C0CA33', 'teal': '#00897B', 'indigo': '#3949AB',
    'magenta': '#D81B60', 'olive': '#7B8D3E', 'navy': '#1A237E', 'maroon': '#880E4F',
}


def main():
    ap = argparse.ArgumentParser(description='生成纯色探测图')
    ap.add_argument('color', nargs='?', default=None, help='颜色名（缺省随机）')
    ap.add_argument('--out', default=None, help='输出路径（缺省 probe-<颜色名>.png）')
    a = ap.parse_args()

    name = a.color or random.choice(list(PALETTE))
    if name not in PALETTE:
        raise SystemExit(f'未知颜色: {name}，可选: {", ".join(PALETTE)}')
    hexv = PALETTE[name]
    rgb = tuple(int(hexv[i:i + 2], 16) for i in (1, 3, 5))
    out = a.out or f'probe-{name}.png'

    Image.new('RGB', (64, 64), rgb).save(out)
    print(f'已生成探测图: {out}（{name} #{hexv}）')
    print(f'发给候选模型问: "这张图片是什么颜色？" — 答出「{name}」才算具备视觉')


if __name__ == '__main__':
    main()
