#!/usr/bin/env python3
"""
Render a terminal-style "system info" panel as a self-animating SVG.
Each row fades/types in with a staggered delay.

Set PREVIEW=1 to also write a still PNG-equivalent (last frame) for
quick viewing in a normal image viewer — since SVG animation only
plays in a renderer that supports SMIL (like a browser or GitHub).

Usage:
    python tools/render_panel.py
    PREVIEW=1 python tools/render_panel.py
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_SVG = ROOT / "sysinfo.svg"

# --- content: based on github.com/PrakashWebDevX -----------------
ROWS = [
    ("user", "Prakash (PrakashWebDevX)"),
    ("role", "AI Agent Developer"),
    ("focus", "LLM apps, AI agents, Gen-AI web platforms"),
    ("stack", "Python, LangChain, React, Next.js, Node.js"),
    ("now", "Interning at Webnox Technologies"),
    ("project", "AI Business Research Agent (RAG)"),
    ("site", "prtech.netlify.app"),
]
# -------------------------------------------------------------------

WIDTH = 540
HEADER_H = 40
ROW_H = 34
PAD_X = 20
FONT_SIZE = 14
LABEL_COLOR = "#00FFCC"
VALUE_COLOR = "#e6edf3"
BG = "#0d1117"
HEADER_BG = "#161b22"
BORDER = "#30363d"
DOT_COLORS = ["#ff5f56", "#ffbd2e", "#27c93f"]
ROW_DELAY_MS = 220
FADE_DUR_MS = 400


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg() -> str:
    height = HEADER_H + len(ROWS) * ROW_H + 24

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {WIDTH} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace">'
    )
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>'
    )
    # header bar
    parts.append(
        f'<path d="M1,10 A9,9 0 0 1 10,1 H{WIDTH - 10} A9,9 0 0 1 {WIDTH - 1},10 '
        f'V{HEADER_H} H1 Z" fill="{HEADER_BG}"/>'
    )
    for i, color in enumerate(DOT_COLORS):
        parts.append(f'<circle cx="{20 + i * 18}" cy="{HEADER_H / 2:.0f}" r="5.5" fill="{color}"/>')
    parts.append(
        f'<text x="{WIDTH / 2:.0f}" y="{HEADER_H / 2 + 4:.0f}" text-anchor="middle" '
        f'font-size="12" fill="#8b949e">whoami --verbose</text>'
    )

    parts.append(
        '<style>'
        f'.label {{ font-size:{FONT_SIZE}px; fill:{LABEL_COLOR}; }}'
        f'.value {{ font-size:{FONT_SIZE}px; fill:{VALUE_COLOR}; }}'
        '</style>'
    )

    label_col_w = 78
    static = os.environ.get("PREVIEW") == "1"
    for i, (label, value) in enumerate(ROWS):
        y = HEADER_H + 26 + i * ROW_H
        delay = i * ROW_DELAY_MS
        row_id = f"row{i}"
        if static:
            # render the settled (post-animation) frame directly, since
            # tools like cairosvg don't execute SMIL <animate> tags
            parts.append(
                f'<g id="{row_id}" opacity="1" transform="translate(0,0)">'
                f'<text class="label" x="{PAD_X}" y="{y}">{escape_xml(label)}</text>'
                f'<text class="value" x="{PAD_X + label_col_w}" y="{y}">{escape_xml(value)}</text>'
                f'</g>'
            )
        else:
            parts.append(
                f'<g id="{row_id}" opacity="0" transform="translate(-6,0)">'
                f'<animate attributeName="opacity" from="0" to="1" begin="{delay}ms" '
                f'dur="{FADE_DUR_MS}ms" fill="freeze"/>'
                f'<animateTransform attributeName="transform" type="translate" '
                f'from="-6,0" to="0,0" begin="{delay}ms" dur="{FADE_DUR_MS}ms" fill="freeze"/>'
                f'<text class="label" x="{PAD_X}" y="{y}">{escape_xml(label)}</text>'
                f'<text class="value" x="{PAD_X + label_col_w}" y="{y}">{escape_xml(value)}</text>'
                f'</g>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    static = os.environ.get("PREVIEW") == "1"
    svg = render_svg()

    if static:
        preview_path = ROOT / "sysinfo-preview.svg"
        preview_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {preview_path} (static frame, for previewing only)")
    else:
        OUT_SVG.write_text(svg, encoding="utf-8")
        print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
