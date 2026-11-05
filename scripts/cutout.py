#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""白底（或已带 alpha）角色图 → 干净透明 PNG。

用法：
    python3 cutout.py 源图.png 输出.png [--height 700] [--no-halo-strip] [--pad 20]

处理顺序（缺一步都会在深色底上露馅）：
    ① 清与画布四边连通的浅色背景
    ② 清闭环空洞（被角色围住的近白区，如珠链与脸颊之间）
    ③ 剥离轮廓外的白描边（两档按亮度压 alpha）
    ④ 最近实心像素颜色回填 + alpha 提纯 + 清孤立碎块
"""
import argparse
import cv2
import numpy as np
from PIL import Image


def base_alpha(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """返回 (alpha, 最小通道值)。清四边连通背景 + 闭环空洞。"""
    mn = rgb.min(2)
    d = rgb.max(2) - mn

    cand = ((mn >= 226) & (d <= 30)).astype(np.uint8)
    n, lab, _ = cv2.connectedComponentsWithStats(cand, 8)
    border = (set(lab[0, :].tolist()) | set(lab[-1, :].tolist())
              | set(lab[:, 0].tolist()) | set(lab[:, -1].tolist()))
    border.discard(0)
    bg = np.isin(lab, list(border)) if border else np.zeros_like(cand, bool)
    fade = np.clip((232.0 - mn) / 18.0, 0.0, 1.0)
    alpha = np.where(bg, fade * 255, 255).astype(np.uint8)

    hmask = ((mn >= 222) & (d <= 24)).astype(np.uint8)
    n2, lab2, st2 = cv2.connectedComponentsWithStats(hmask, 8)[:3]
    b2 = (set(lab2[0, :].tolist()) | set(lab2[-1, :].tolist())
          | set(lab2[:, 0].tolist()) | set(lab2[:, -1].tolist()))
    b2.discard(0)
    for i in range(1, n2):
        if i in b2 or st2[i, 4] < 120:
            continue
        m = lab2 == i
        lum = float(rgb[m].mean(0).mean())
        sat = float((rgb[m].max(1) - rgb[m].min(1)).mean())
        if lum >= 236 and sat <= 14:
            ah = np.clip((238.0 - mn) / 18.0, 0.0, 1.0) * 255
            alpha = np.where(m, np.minimum(alpha, ah.astype(np.uint8)), alpha)

    alpha[alpha < 8] = 0
    return alpha, mn


def strip_white_halo(alpha: np.ndarray, mn: np.ndarray) -> np.ndarray:
    """轮廓外窄带内按亮度压 alpha，不进入主体内部。"""
    t = (alpha == 0).astype(np.uint8)
    dist = cv2.distanceTransform(1 - t, cv2.DIST_L2, 5)
    w1 = np.clip((mn - 194.0) / 46.0, 0, 1)
    m1 = (alpha > 0) & (dist <= 2.5)
    a1 = np.where(m1, alpha * (1 - w1), alpha)
    w2 = 0.55 * np.clip((mn - 212.0) / 38.0, 0, 1)
    m2 = (alpha > 0) & (dist > 2.5) & (dist <= 5.0)
    a2 = np.where(m2, alpha * (1 - w2), a1)
    return np.clip(a2, 0, 255).astype(np.uint8)


def defringe(arr: np.ndarray, core_thr: int = 248, alpha_thr: int = 60) -> np.ndarray:
    """用最近的不透明像素颜色回填边缘，再二值化 alpha，消除混白边缘。"""
    rgb = arr[:, :, :3]
    al = arr[:, :, 3]
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


def clean_small(alpha: np.ndarray, min_area: int = 120) -> np.ndarray:
    n, lab, st = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), 8)[:3]
    if n <= 1:
        return alpha
    big = max(range(1, n), key=lambda i: st[i, 4])
    out = alpha.copy()
    for i in range(1, n):
        if i != big and st[i, 4] < min_area:
            out[lab == i] = 0
    return out


def cutout(src: str, dst: str, height: int | None = None, halo: bool = True,
           pad: int = 0) -> Image.Image:
    img = Image.open(src)
    rgba = np.array(img.convert("RGBA"))
    if rgba[:, :, 3].min() == 255:          # 原图不透明：把 RGB 当白底算
        rgb = rgba[:, :, :3].astype(np.int16)
        alpha, mn = base_alpha(rgb)
    else:                                    # 已有 alpha：沿用，只做净化
        rgb = rgba[:, :, :3].astype(np.int16)
        alpha = rgba[:, :, 3].copy()
        mn = rgb.min(2)

    if halo:
        alpha = strip_white_halo(alpha, mn)
    alpha = clean_small(alpha)
    full = np.dstack([rgba[:, :, :3], alpha])
    full = defringe(full)
    al = np.clip((full[:, :, 3].astype(np.float32) - 45.0) / 150.0, 0, 1) * 255
    full[:, :, 3] = al.astype(np.uint8)
    full[full[:, :, 3] < 45] = 0

    ys, xs = np.where(full[:, :, 3] > 0)
    out = Image.fromarray(full, "RGBA").crop(
        (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))

    if height:
        w = max(1, int(round(out.width * height / out.height)))
        out = out.resize((w, height), Image.LANCZOS)
    if pad:
        big = Image.new("RGBA", (out.width + pad * 2, out.height + pad * 2), (0, 0, 0, 0))
        big.alpha_composite(out, (pad, pad))
        out = big
    out.save(dst)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="白底角色图抠成干净透明 PNG")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--height", type=int, default=None, help="输出高度，等比缩放")
    ap.add_argument("--pad", type=int, default=0, help="四周透明留白像素")
    ap.add_argument("--no-halo-strip", action="store_true", help="不做白描边剥离")
    a = ap.parse_args()
    out = cutout(a.src, a.dst, a.height, not a.no_halo_strip, a.pad)
    arr = np.array(out)
    print(f"输出 {out.size[0]}x{out.size[1]}  不透明像素 {int((arr[:, :, 3] > 200).sum())}")


if __name__ == "__main__":
    main()
