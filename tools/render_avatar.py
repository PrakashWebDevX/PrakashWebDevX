#!/usr/bin/env python3
"""
Turn assets/avatar-src.png (the user's own illustrated avatar) into a
premium, fully-animated "system scan" reveal: a glowing ring that
draws itself on, a horizontal scan-line sweep that reveals the
portrait, corner HUD brackets, and an ambient looping glow/scan after
the initial reveal.

No ASCII conversion here — the avatar is embedded as-is (base64),
since the user supplied finished art rather than a photo.

Usage:
    python tools/render_avatar.py
    PREVIEW=1 python tools/render_avatar.py   # static mid-animation frame
"""
import base64
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC_IMAGE = ASSETS / "avatar-src.png"
OUT_SVG = ROOT / "avatar.svg"

# --- palette sampled directly from the user's avatar ---------------
BG = "#0a0e1c"
ACCENT = "#00f0c0"      # mint teal
ACCENT2 = "#7c5cff"     # indigo/purple secondary
# ---------------------------------------------------------------------

SIZE = 420          # avatar render size
PAD = 30            # canvas padding around the ring
CANVAS = SIZE + PAD * 2
RING_R = SIZE / 2 + 8
CENTER = CANVAS / 2

REVEAL_MS = 1400        # initial scan-reveal duration
RING_DRAW_MS = 1100
LOOP_SCAN_MS = 4200      # ambient scan sweep period after reveal


def load_avatar_b64() -> str:
    data = SRC_IMAGE.read_bytes()
    return base64.b64encode(data).decode("ascii")


def render_svg(static: bool = False) -> str:
    b64 = load_avatar_b64()
    img_x = PAD
    img_y = PAD

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {CANVAS} {CANVAS}" xmlns="http://www.w3.org/2000/svg" '
        f'xmlns:xlink="http://www.w3.org/1999/xlink" font-family="Consolas, Menlo, monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG}" rx="16"/>')

    parts.append(
        f'<defs>'
        f'<clipPath id="circleClip"><circle cx="{CENTER}" cy="{CENTER}" r="{SIZE/2}"/></clipPath>'
        f'<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0%" stop-color="{ACCENT}" stop-opacity="0.55"/>'
        f'<stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>'
        f'</radialGradient>'
        f'<linearGradient id="scanGrad" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0%" stop-color="{ACCENT}" stop-opacity="0"/>'
        f'<stop offset="45%" stop-color="{ACCENT}" stop-opacity="0.85"/>'
        f'<stop offset="55%" stop-color="{ACCENT}" stop-opacity="0.85"/>'
        f'<stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>'
        f'</linearGradient>'
        f'</defs>'
    )

    # ambient glow behind the ring
    parts.append(
        f'<circle cx="{CENTER}" cy="{CENTER}" r="{SIZE/2 + 26}" fill="url(#glow)">'
        + (
            ""
            if static
            else (
                f'<animate attributeName="r" values="{SIZE/2+22};{SIZE/2+34};{SIZE/2+22}" '
                f'dur="3.4s" repeatCount="indefinite"/>'
            )
        )
        + f'</circle>'
    )

    # --- the avatar image, clipped to a circle, revealed by a mask ---
    mask_id = "scanMask"
    if static:
        # settled state: fully visible
        parts.append(
            f'<image href="data:image/png;base64,{b64}" x="{img_x}" y="{img_y}" '
            f'width="{SIZE}" height="{SIZE}" clip-path="url(#circleClip)"/>'
        )
    else:
        parts.append(f'<mask id="{mask_id}">')
        parts.append(
            f'<rect x="{img_x}" y="{img_y}" width="{SIZE}" height="0" fill="white">'
            f'<animate attributeName="height" from="0" to="{SIZE}" '
            f'begin="0s" dur="{REVEAL_MS}ms" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
            f'</rect>'
        )
        parts.append(f'</mask>')
        parts.append(
            f'<image href="data:image/png;base64,{b64}" x="{img_x}" y="{img_y}" '
            f'width="{SIZE}" height="{SIZE}" clip-path="url(#circleClip)" '
            f'mask="url(#{mask_id})"/>'
        )

    # scan-line bar: sweeps down once during reveal, then loops gently forever
    bar_h = 14
    if static:
        pass
    else:
        parts.append(
            f'<g clip-path="url(#circleClip)">'
            f'<rect x="{img_x}" y="{img_y - bar_h}" width="{SIZE}" height="{bar_h}" '
            f'fill="url(#scanGrad)">'
            f'<animate attributeName="y" '
            f'values="{img_y - bar_h};{img_y + SIZE - bar_h};{img_y - bar_h};{img_y + SIZE - bar_h}" '
            f'keyTimes="0;{REVEAL_MS/(REVEAL_MS+LOOP_SCAN_MS):.4f};'
            f'{REVEAL_MS/(REVEAL_MS+LOOP_SCAN_MS):.4f};1" '
            f'dur="{(REVEAL_MS+LOOP_SCAN_MS)/1000:.2f}s" repeatCount="indefinite"/>'
            f'</rect>'
            f'</g>'
        )

    # glowing ring outline, drawn on with a dash-offset animation
    circumference = 2 * 3.14159265 * RING_R
    if static:
        parts.append(
            f'<circle cx="{CENTER}" cy="{CENTER}" r="{RING_R}" fill="none" '
            f'stroke="{ACCENT}" stroke-width="3.5"/>'
        )
    else:
        parts.append(
            f'<circle cx="{CENTER}" cy="{CENTER}" r="{RING_R}" fill="none" '
            f'stroke="{ACCENT}" stroke-width="3.5" '
            f'stroke-dasharray="{circumference:.1f}" '
            f'stroke-dashoffset="{circumference:.1f}" transform="rotate(-90 {CENTER} {CENTER})">'
            f'<animate attributeName="stroke-dashoffset" from="{circumference:.1f}" to="0" '
            f'begin="0s" dur="{RING_DRAW_MS}ms" fill="freeze" '
            f'calcMode="spline" keySplines="0.3 0 0.2 1"/>'
            f'</circle>'
        )

    # corner HUD brackets (small targeting-style accents)
    bl = 22  # bracket leg length
    inset = PAD - 10
    corners = [
        (inset, inset, 1, 1),
        (CANVAS - inset, inset, -1, 1),
        (inset, CANVAS - inset, 1, -1),
        (CANVAS - inset, CANVAS - inset, -1, -1),
    ]
    for cx, cy, sx, sy in corners:
        parts.append(
            f'<path d="M{cx},{cy + sy*bl} L{cx},{cy} L{cx + sx*bl},{cy}" '
            f'fill="none" stroke="{ACCENT2}" stroke-width="3" stroke-linecap="round" opacity="0.9"/>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not SRC_IMAGE.exists():
        print(f"Missing {SRC_IMAGE} — save the avatar there first.")
        return

    static = os.environ.get("PREVIEW") == "1"
    svg = render_svg(static=static)

    if static:
        preview_path = ROOT / "avatar-preview.svg"
        preview_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {preview_path} (static settled frame, for previewing only)")
    else:
        OUT_SVG.write_text(svg, encoding="utf-8")
        print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
