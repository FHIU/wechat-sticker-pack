#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""透明角色图 → 240×240 表情成品（PNG + 5 帧透明 GIF）。

用法：
    python3 compose.py 角色.png 输出前缀 --text "就这"
    python3 compose.py 角色.png out/01 --text 就这 --subject-height 208 --gif

产出 输出前缀.png 与 输出前缀.gif
"""
import argparse
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

CANVAS = 240
FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]
TEXT_FILL = (244, 247, 250, 255)
STROKE_FILL = (16, 24, 32, 255)


def load_font(size: int = 25) -> ImageFont.FreeTypeFont:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            for idx in (2, 0, 1):  # Hiragino：index 2 = W6
                try:
                    return ImageFont.truetype(p, size, index=idx)
                except Exception:
                    continue
    return ImageFont.load_default()


def place(char: Image.Image, subject_height: int = 208) -> Image.Image:
    """等比缩放到指定高度，按实际 alpha 外接框精确居中到 (119.5, 119.5)。"""
    w = max(1, int(round(char.width * subject_height / char.height)))
    small = char.resize((w, subject_height), Image.LANCZOS)
    tmp = Image.new("RGBA", (CANVAS + 120, CANVAS + 80), (0, 0, 0, 0))
    tmp.alpha_composite(small, (10, 10))
    ta = np.array(tmp)[:, :, 3]
    ys, xs = np.where(ta > 0)
    ox = int(round((CANVAS - 1 - (xs.min() + xs.max())) / 2.0))
    oy = int(round((CANVAS - 1 - (ys.min() + ys.max())) / 2.0))
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.alpha_composite(tmp, (ox, oy))
    return canvas


def label(text: str, size: int = 25) -> Image.Image:
    layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((211, 47), text, font=load_font(size),
                               fill=TEXT_FILL, anchor="mm",
                               stroke_width=2, stroke_fill=STROKE_FILL)
    return layer


def dedupe(arr: np.ndarray, core_thr: int = 248, alpha_thr: int = 60) -> np.ndarray:
    """边缘颜色回填 + alpha 二值化，避免 GIF 边缘变不透明白圈。"""
    rgb, al = arr[:, :, :3], arr[:, :, 3]
    core = (al >= core_thr).astype(np.uint8)
    if core.sum() == 0:
        return arr
    _, lab = cv2.distanceTransformWithLabels(1 - core, cv2.DIST_L2, 5,
                                             labelType=cv2.DIST_LABEL_PIXEL)
    ys, xs = np.where(core == 1)
    filled = rgb[ys[lab.astype(np.int64) - 1], xs[lab.astype(np.int64) - 1]]
    keep = al >= alpha_thr
    out = np.dstack([filled, np.where(keep, al, 0).astype(np.uint8)])
    out[~keep] = 0
    return out


def build(char_path: str, out_prefix: str, text: str, subject_height: int = 208,
          make_gif: bool = True, font_size: int = 25) -> dict:
    char = Image.open(char_path).convert("RGBA")
    canvas = place(char, subject_height)
    tl = label(text, font_size)
    static = Image.alpha_composite(canvas, tl)

    ca = np.array(static)
    zone = int((ca[24:72, 176:240, 3] > 0).sum())
    text_px = int((np.array(tl)[:, :, 3] > 0).sum())
    intrusion = max(0, zone - text_px)  # 减掉文字自身占位

    png = f"{out_prefix}.png"
    static.save(png)

    info = {"png": png, "intrusion": intrusion}
    if make_gif:
        frames = []
        for o in (0, -1, -2, -2, -1, 0):
            cl = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
            cl.alpha_composite(canvas, (0, o))
            frames.append(Image.alpha_composite(cl, tl))
        base = frames[0].convert("RGB").quantize(colors=255, method=Image.MEDIANCUT,
                                                 dither=Image.NONE)
        paletted = []
        for fr in frames:
            p = fr.convert("RGB").quantize(palette=base, dither=Image.NONE)
            mask = Image.fromarray(
                np.where(np.array(fr)[:, :, 3] == 0, 255, 0).astype(np.uint8), "L")
            p.paste(255, mask=mask)
            paletted.append(p)
        gif = f"{out_prefix}.gif"
        paletted[0].save(gif, save_all=True, append_images=paletted[1:], duration=90,
                         loop=0, transparency=255, disposal=2, optimize=False)
        info["gif"] = gif
    return info


def main() -> None:
    ap = argparse.ArgumentParser(description="透明角色图 → 240×240 PNG/GIF")
    ap.add_argument("char")
    ap.add_argument("out")
    ap.add_argument("--text", default="")
    ap.add_argument("--subject-height", type=int, default=208)
    ap.add_argument("--font-size", type=int, default=25)
    ap.add_argument("--no-gif", action="store_true")
    a = ap.parse_args()
    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    info = build(a.char, a.out, a.text, a.subject_height, not a.no_gif, a.font_size)
    print("文字区人物侵入:", info["intrusion"], "像素")
    print("输出:", info["png"], info.get("gif", ""))


if __name__ == "__main__":
    main()
