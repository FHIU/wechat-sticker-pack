#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""工作室/品牌纯图形徽标（车标式，无文字）。

一个标记：实心椭圆鱼身（字母 J 的圆钩）+ 直线 V 形尾鳍（字母 Y）＋ 负空间眼孔。
单色、可任意缩放、无文字，作车标式徽记使用。

用法：
    python3 mark.py --height 512 --out 目录 --color EDF1F6 --suffix 浅色
    python3 mark.py --height 512 --out 目录 --color 14181D --suffix 深色

改造点（换成自己的标记时只动这三处）：
    BODY  主体（椭圆/圆角矩形等单色块）
    TAIL  尾鳍/次要形状的多边形顶点
    EYE   负空间圆孔（眼睛/镂空），位置决定"生物感"
"""
import argparse
import os

from PIL import Image, ImageDraw

LIGHT = (0xED, 0xF1, 0xF6)
DARK = (0x14, 0x18, 0x1D)

CW, CH = 110, 100                       # 画布（单位）
BODY = (46, 50, 28, 16)                 # cx, cy, rx, ry
TAIL = [(69, 42), (106, 23), (98, 50), (106, 77), (69, 58)]
EYE = (34, 47, 3.8)


def mark(h, color, ss=4):
    S = ss * h / CH
    big = Image.new("RGBA", (int(CW * h / CH) * ss // 1, h * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy, rx, ry = BODY
    d.ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=color + (255,))
    d.polygon([(x * S, y * S) for x, y in TAIL], fill=color + (255,))
    ex, ey, er = EYE
    hole = Image.new("L", big.size, 0)
    ImageDraw.Draw(hole).ellipse([(ex - er) * S, (ey - er) * S, (ex + er) * S, (ey + er) * S], fill=255)
    big.putalpha(Image.composite(Image.new("L", big.size, 0), big.getchannel("A"), hole))
    return big.resize((int(CW * h / CH), h), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--height", type=int, default=512)
    ap.add_argument("--out", required=True)
    ap.add_argument("--color", default="EDF1F6")
    ap.add_argument("--suffix", default="浅色")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    color = tuple(int(a.color[i:i + 2], 16) for i in (0, 2, 4))
    im = mark(a.height, color)
    p = os.path.join(a.out, f"徽标_{a.suffix}.png")
    im.save(p)
    print(os.path.basename(p), im.size, os.path.getsize(p) // 1024, "KB")


if __name__ == "__main__":
    main()
