#!/usr/bin/env python3
"""
Convert assets/photo-ready.png into a monochrome ASCII-art SVG that
draws itself in, row by row, top to bottom.

Usage:
    python tools/render_portrait.py
    # writes portrait.svg
"""
import os
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC_IMAGE = ASSETS / "photo-ready.png"
OUT_SVG = ROOT / "portrait.svg"

# Left = light/empty, right = dense/dark. A softer ramp than @%#-style blocks.
GLYPHS = " '.,:;~+*xXO#"

# Grid + rendering knobs
COLS = 70
CHAR_W = 7.2
CHAR_H = 13
FONT_SIZE = 13
ACCENT = "#4dabf7"
BG = "#0d1117"
ROW_STAGGER_MS = 40  # gap between each row's reveal start


def load_and_downscale(path: Path, cols: int):
    img = Image.open(path).convert("L")  # grayscale
    w, h = img.size
    # character cells are taller than they are wide, so compensate
    aspect_correction = 0.55
    rows = max(1, round(cols * (h / w) * aspect_correction))
    small = img.resize((cols, rows), Image.LANCZOS)
    return small, cols, rows


def pixel_to_glyph(value: int) -> str:
    # value: 0 (black) .. 255 (white). White background -> should map to " ".
    inv = 255 - value
    idx = round((inv / 255) * (len(GLYPHS) - 1))
    return GLYPHS[idx]


def build_ascii_rows(img, cols, rows):
    pixels = img.load()
    ascii_rows = []
    for y in range(rows):
        row_chars = []
        for x in range(cols):
            row_chars.append(pixel_to_glyph(pixels[x, y]))
        ascii_rows.append("".join(row_chars))
    return ascii_rows


def escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_svg(ascii_rows, cols, rows, static=False) -> str:
    width = cols * CHAR_W + 40
    height = rows * CHAR_H + 40

    lines = []
    lines.append(
        f'<svg viewBox="0 0 {width:.1f} {height:.1f}" '
        f'xmlns="http://www.w3.org/2000/svg" font-family="Consolas, Menlo, monospace">'
    )
    lines.append(f'<rect width="100%" height="100%" fill="{BG}" rx="10"/>')
    lines.append(
        f'<style>'
        f'.row {{ font-size:{FONT_SIZE}px; fill:{ACCENT}; white-space:pre; }}'
        f'</style>'
    )

    for i, row in enumerate(ascii_rows):
        y = 30 + i * CHAR_H
        delay = i * ROW_STAGGER_MS
        clip_id = f"clip{i}"
        text_escaped = escape_xml(row)

        if static:
            width_val = cols * CHAR_W
            lines.append(f'<clipPath id="{clip_id}">')
            lines.append(
                f'  <rect x="20" y="{y - FONT_SIZE:.1f}" width="{width_val:.1f}" height="{FONT_SIZE + 4}"/>'
            )
            lines.append(f'</clipPath>')
        else:
            lines.append(f'<clipPath id="{clip_id}">')
            lines.append(f'  <rect x="20" y="{y - FONT_SIZE:.1f}" width="0" height="{FONT_SIZE + 4}">')
            lines.append(
                f'    <animate attributeName="width" from="0" to="{cols * CHAR_W:.1f}" '
                f'begin="{delay}ms" dur="260ms" fill="freeze" calcMode="spline" '
                f'keySplines="0.25 0.1 0.25 1"/>'
            )
            lines.append(f'  </rect>')
            lines.append(f'</clipPath>')

        lines.append(
            f'<text class="row" x="20" y="{y:.1f}" clip-path="url(#{clip_id})">'
            f'{text_escaped}</text>'
        )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    if not SRC_IMAGE.exists():
        print(f"Missing {SRC_IMAGE} — run clean_photo.py first.")
        return

    img, cols, rows = load_and_downscale(SRC_IMAGE, COLS)
    ascii_rows = build_ascii_rows(img, cols, rows)

    static = os.environ.get("PREVIEW") == "1"
    svg = render_svg(ascii_rows, cols, rows, static=static)

    if static:
        preview_path = ROOT / "portrait-preview.svg"
        preview_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {preview_path} (static frame, for previewing only)")
    else:
        OUT_SVG.write_text(svg, encoding="utf-8")
        print(f"Wrote {OUT_SVG} ({cols}x{rows} chars)")


if __name__ == "__main__":
    main()
