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
    # macOS
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", (2, 0)),
    ("/System/Library/Fonts/PingFang.ttc", (2, 0)),
    ("/System/Library/Fonts/STHeiti Medium.ttc", (1, 0)),
    # Windows
    ("C:/Windows/Fonts/msyhbd.ttc", (0, 0)),
    ("C:/Windows/Fonts/msyh.ttc", (0, 0)),
    ("C:/Windows/Fonts/simhei.ttf", (0, 0)),
    # Linux
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", (2, 0)),
    ("/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc", (2, 0)),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", (0, 0)),
]
TEXT_FILL = (244, 247, 250, 255)
STROKE_FILL = (16, 24, 32, 255)
_FONT_CACHE = {}


def load_font(size: int = 25, font_path=None) -> ImageFont.FreeTypeFont:
    """按平台探测中文字体；找不到就报错，不静默画方框。"""
    key = (size, font_path)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    cands = ([(font_path, (0, 0))] if font_path else []) + FONT_CANDIDATES
    for path, (bold_idx, reg_idx) in cands:
        if not path or not os.path.exists(path):
            continue
        for idx in (bold_idx, reg_idx):
            try:
                f = ImageFont.truetype(path, size, index=idx)
                _FONT_CACHE[key] = f
                return f
            except Exception:
                continue
    raise SystemExit(
        "找不到可用的中文字体，无法写文字。\n"
        "  macOS   系统自带 Hiragino Sans GB，一般不需要处理\n"
        "  Windows 系统自带微软雅黑，一般不需要处理\n"
        "  Linux   执行：sudo apt install fonts-noto-cjk\n"
        "  或手动指定  --font /路径/字体.ttc"
    )


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


def label(text: str, size: int = 25, font_path=None) -> Image.Image:
    layer = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((211, 47), text, font=load_font(size, font_path),
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
          make_gif: bool = True, font_size: int = 25, font_path=None) -> dict:
    char = Image.open(char_path).convert("RGBA")
    canvas = place(char, subject_height)
    tl = label(text, font_size, font_path)
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
        for o in (0, -1, -2, -1, 0):  # 5 帧，上下浮动 0/1/2/1/0（口径固定，勿改）
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
    ap.add_argument("--font", default=None, help="中文字体路径（默认按 macOS/Windows/Linux 顺序自动探测）")
    a = ap.parse_args()
    d = os.path.dirname(a.out)
    if d:
        os.makedirs(d, exist_ok=True)
    info = build(a.char, a.out, a.text, a.subject_height, not a.no_gif, a.font_size, a.font)
    print("文字区人物侵入:", info["intrusion"], "像素")
    print("输出:", info["png"], info.get("gif", ""))


if __name__ == "__main__":
    main()
