#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一套上架素材：横幅 750×400 / 封面 240×240 / 图标 50×50 / 角色图 700×700。

用法：
    python3 assets.py 角色透明图.png 输出目录 [--brand-color 12,17,23]

说明（平台硬约束）：
    横幅 —— 不得含文字、logo、二维码；非白底、非透明底
    封面 —— 必须是完整角色，不能只有头部；无文字、无边框
    图标 —— 只用头部正面，特征齐全，无身体手臂
"""
import argparse
import os

import numpy as np

CN_FONT = "/System/Library/Fonts/Hiragino Sans GB.ttc"
W6, W3 = 2, 0
from PIL import Image, ImageDraw, ImageFont


def vgrad(size, c1, c2):
    w, h = size
    arr = np.zeros((h, w, 3), np.uint8)
    for y in range(h):
        t = y / max(h - 1, 1)
        arr[y, :] = [int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)]
    return Image.fromarray(arr, "RGB")


def radial(size, center, radius, color, strength=1.0):
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.sqrt((xx - center[0]) ** 2 + (yy - center[1]) ** 2)
    a = np.clip(1 - d / radius, 0, 1) ** 2.2 * strength
    layer = np.zeros((h, w, 4), np.uint8)
    layer[:, :, :3] = color
    layer[:, :, 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(layer, "RGBA")


def banner(char, base, top, out_dir, logo=None, title="", sub="", tag=""):
    """横幅 750×400。可含标题文字与品牌 logo；禁二维码/联系方式。"""
    W, H = 750, 400
    cx = W // 2
    bg = vgrad((W, H), base, top).convert("RGBA")
    bg = Image.alpha_composite(bg, radial((W, H), (cx + 60, 120), 460, (132, 164, 202), 0.42))
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d0 = ImageDraw.Draw(ring)
    d0.ellipse([cx - 75, -170, cx + 565, 470], outline=(190, 206, 222, 22), width=2)
    d0.ellipse([cx + 17, -60, cx + 473, 396], outline=(190, 206, 222, 13), width=1)
    bg = Image.alpha_composite(bg, ring)

    # 人物：右侧，脚底留 22
    ph = 352 if title else 350
    pw = int(char.width * ph / char.height)
    p = char.resize((pw, ph), Image.LANCZOS)
    x, y = W - pw - 24, H - ph - 22
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse([x + pw * 0.18, y + ph - 10, x + pw * 0.82, y + ph + 2],
                                   fill=(0, 0, 0, 58))
    bg = Image.alpha_composite(bg, shadow)
    bg.alpha_composite(p, (x, y))

    d = ImageDraw.Draw(bg)
    if logo is not None:
        lh = 58
        lg = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
        bg.alpha_composite(lg, (44, 30))

    if title:
        f_title = ImageFont.truetype(CN_FONT, 74, index=W6)
        f_sub = ImageFont.truetype(CN_FONT, 23, index=W3)
        f_tag = ImageFont.truetype(CN_FONT, 15, index=W3)
        d.text((46, 210), title, font=f_title, fill=(244, 247, 250, 255), anchor="ls")
        if sub:
            d.text((47, 264), sub, font=f_sub, fill=(176, 190, 205, 255), anchor="ls")
        if tag:
            tw = d.textlength(tag, font=f_tag)
            d.rounded_rectangle([47, 296, 47 + tw + 28, 328], radius=16,
                                outline=(154, 172, 190, 105), width=1)
            d.text((47 + 14, 312), tag, font=f_tag, fill=(158, 174, 190, 255), anchor="lm")

    out = bg.convert("RGB")
    out.save(os.path.join(out_dir, "横幅_750x400.png"))
    out.save(os.path.join(out_dir, "横幅_750x400.jpg"), quality=95)


def cover(char, base, top, out_dir):
    """平台要求：透明底、完整角色、无文字、无边框。"""
    S = 240
    bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ph = 212
    pw = int(char.width * ph / char.height)
    p = char.resize((pw, ph), Image.LANCZOS)
    bg.alpha_composite(p, ((S - pw) // 2, S - ph - 10))
    bg.save(os.path.join(out_dir, "封面_240x240.png"))


def icon(char, out_dir):
    """平台要求：透明底、仅头部正面、特征齐全。"""
    S = 50
    x0, x1 = int(char.width * 0.10), int(char.width * 0.90)
    head = char.crop((x0, 0, x1, int(char.height * 0.565)))
    scale = min(S / head.width, S / head.height)
    pw, ph = max(1, int(head.width * scale)), max(1, int(head.height * scale))
    h = head.resize((pw, ph), Image.LANCZOS)
    bg = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bg.alpha_composite(h, ((S - pw) // 2, (S - ph) // 2))
    bg.save(os.path.join(out_dir, "图标_50x50.png"))


def role_card(char, out_dir, height=640):
    w = int(char.width * height / char.height)
    c = char.resize((w, height), Image.LANCZOS)
    side = max(w, height) + 60
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.alpha_composite(c, ((side - w) // 2, (side - height) // 2))
    canvas.save(os.path.join(out_dir, "角色图_700.png"))


def main():
    ap = argparse.ArgumentParser(description="生成上架四件套")
    ap.add_argument("char", help="透明角色图（可用 cutout.py 产出）")
    ap.add_argument("out_dir")
    ap.add_argument("--base-color", default="12,17,23", help="背景渐变上端 RGB")
    ap.add_argument("--top-color", default="30,39,51", help="背景渐变下端 RGB")
    ap.add_argument("--logo", help="品牌徽标 PNG（透明底，浅色版），贴左上角")
    ap.add_argument("--title", default="", help="横幅主标题（留空则人物居中、无文字）")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    base = tuple(int(x) for x in a.base_color.split(","))
    top = tuple(int(x) for x in a.top_color.split(","))
    char = Image.open(a.char).convert("RGBA")

    logo = Image.open(a.logo).convert("RGBA") if a.logo else None
    banner(char, base, top, a.out_dir, logo, a.title, a.subtitle, a.tag)
    cover(char, base, top, a.out_dir)
    icon(char, a.out_dir)
    role_card(char, a.out_dir)

    for f in sorted(os.listdir(a.out_dir)):
        if f.lower().endswith((".png", ".jpg")):
            p = os.path.join(a.out_dir, f)
            print(f"{f}  {Image.open(p).size}  {os.path.getsize(p) // 1024}KB")


if __name__ == "__main__":
    main()
