#!/usr/bin/env python3
"""
Clean up a source photo so it converts well to ASCII.

Pipeline:
  1. Strip the background with rembg (subject only, transparent bg).
  2. Even out lighting with CLAHE (adaptive histogram equalization).
  3. Composite onto a plain white canvas so background maps to the
     LIGHT end of the character ramp, not the dark end.

Usage:
    python tools/clean_photo.py my-photo.jpg
    # writes assets/photo-ready.png
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove

ASSETS = Path(__file__).resolve().parent.parent / "assets"
ASSETS.mkdir(exist_ok=True)


def remove_background(src_path: Path) -> Image.Image:
    with open(src_path, "rb") as f:
        input_bytes = f.read()
    output_bytes = remove(input_bytes)
    from io import BytesIO
    return Image.open(BytesIO(output_bytes)).convert("RGBA")


def apply_clahe(img: Image.Image) -> Image.Image:
    """Even out lighting on the RGB channels, keep alpha untouched."""
    rgba = np.array(img)
    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]

    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)

    lab_eq = cv2.merge((l_eq, a, b))
    rgb_eq = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)

    out = np.dstack([rgb_eq, alpha])
    return Image.fromarray(out, mode="RGBA")


def composite_on_white(img: Image.Image) -> Image.Image:
    white_bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    white_bg.alpha_composite(img)
    return white_bg.convert("RGB")


def main():
    if len(sys.argv) != 2:
        print("Usage: python clean_photo.py <source-photo>")
        sys.exit(1)

    src_path = Path(sys.argv[1])
    if not src_path.exists():
        print(f"File not found: {src_path}")
        sys.exit(1)

    print("Removing background...")
    subject = remove_background(src_path)

    print("Evening out lighting (CLAHE)...")
    subject = apply_clahe(subject)

    print("Compositing onto white canvas...")
    final = composite_on_white(subject)

    out_path = ASSETS / "photo-ready.png"
    final.save(out_path)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
