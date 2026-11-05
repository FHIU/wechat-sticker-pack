#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""成品目录校验：尺寸 / 透明 / 体积 / 白边 / 文字区侵入 / GIF 帧透明。

用法：
    python3 validate.py 成品目录 [--text-box 176,24,64,48] [--max-kb 500]

退出码 0 = 全部通过；1 = 有未通过项。
"""
import argparse
import glob
import os

import cv2
import numpy as np
from PIL import Image

OK, BAD = "达标", "不达标"


def edge_stats(arr):
    """边缘带（距透明区 ≤2px）内浅色像素统计。"""
    al = arr[:, :, 3]
    mn = arr[:, :, :3].astype(np.int16).min(2)
    t = (al == 0).astype(np.uint8)
    dist = cv2.distanceTransform(1 - t, cv2.DIST_L2, 5)
    band = (al > 0) & (dist <= 2.0)
    total = int(band.sum())
    light200 = int((band & (mn >= 200)).sum())
    light230 = int((band & (mn >= 230)).sum())
    ratio = light200 / total if total else 0.0
    return total, light200, light230, ratio


def check_png(path, max_kb, box, max_light=0.03):
    im = Image.open(path)
    arr = np.array(im.convert("RGBA"))
    problems = []

    if im.size != (240, 240):
        problems.append(f"尺寸 {im.size} ≠ (240,240)")
    if im.mode not in ("RGBA", "P"):
        problems.append(f"模式 {im.mode} 非 RGBA")

    corners = [int(arr[0, 0, 3]), int(arr[0, -1, 3]), int(arr[-1, 0, 3]), int(arr[-1, -1, 3])]
    if max(corners) != 0:
        problems.append(f"四角未透明 {corners}")

    kb = os.path.getsize(path) / 1024
    if kb > max_kb:
        problems.append(f"体积 {kb:.0f}KB > {max_kb}KB")

    total, l200, l230, ratio = edge_stats(arr)
    if ratio > max_light:
        problems.append(f"边缘浅色占比 {ratio*100:.1f}% > {max_light*100:.0f}%")
    if l230 > 0:
        problems.append(f"边缘存在纯白像素 {l230} 个")

    if box:
        x, y, w, h = box
        zone = int((arr[y:y + h, x:x + w, 3] > 0).sum())
        if zone > 0:
            problems.append(f"文字区被人物侵占 {zone} 像素")

    return problems, dict(kb=kb, corners=corners, light=l200, ratio=ratio)


def check_gif(path, max_kb):
    im = Image.open(path)
    problems, frames, worst = [], 0, 1.0
    while True:
        arr = np.array(im.convert("RGBA"))
        al = arr[:, :, 3]
        worst = min(worst, float((al == 0).mean()))
        corners = [int(al[0, 0]), int(al[0, -1]), int(al[-1, 0]), int(al[-1, -1])]
        if max(corners) != 0:
            problems.append(f"第 {frames+1} 帧四角不透明 {corners}")
        frames += 1
        try:
            im.seek(frames)
        except EOFError:
            break
    kb = os.path.getsize(path) / 1024
    if kb > max_kb:
        problems.append(f"体积 {kb:.0f}KB > {max_kb}KB")
    if worst < 0.6:
        problems.append(f"最低透明占比 {worst:.2f} 过低，疑似透明未生效")
    return problems, dict(frames=frames, kb=kb, transparency=worst)


def main():
    ap = argparse.ArgumentParser(description="成品校验")
    ap.add_argument("dir")
    ap.add_argument("--max-kb", type=float, default=500)
    ap.add_argument("--text-box", default="", help="文字区 x,y,w,h；留空则不校验")
    ap.add_argument("--gif-frames", type=int, default=0, help="期望帧数；0 不校验")
    ap.add_argument("--max-light-ratio", type=float, default=0.03,
                    help="边缘带浅色像素占比上限（默认 3%%，镜片反光等主体浅色会计入）")
    a = ap.parse_args()

    box = tuple(int(v) for v in a.text_box.split(",")) if a.text_box else None
    files = sorted(glob.glob(os.path.join(a.dir, "*.png")) + glob.glob(os.path.join(a.dir, "*.gif")))
    if not files:
        print("目录内没有 png/gif")
        return 1

    failed = 0
    for f in files:
        name = os.path.basename(f)
        if f.lower().endswith(".png"):
            problems, meta = check_png(f, a.max_kb, box, a.max_light_ratio)
            line = (f"{name:<24} {OK if not problems else BAD}  "
                    f"{meta['kb']:.0f}KB 边浅{meta['light']}({meta['ratio']*100:.1f}%)")
        else:
            problems, meta = check_gif(f, a.max_kb)
            if a.gif_frames and meta["frames"] != a.gif_frames:
                problems.append(f"帧数 {meta['frames']} ≠ {a.gif_frames}")
            line = (f"{name:<24} {OK if not problems else BAD}  "
                    f"{meta['kb']:.0f}KB {meta['frames']}帧 透明{meta['transparency']:.2f}")
        print(line)
        for p in problems:
            print("    · ", p)
        failed += 1 if problems else 0

    print(f"\n{len(files)} 个文件，{failed} 个不达标")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
