#!/usr/bin/env python3
"""
Render assets/contributions.json as a classic "snake" that crawls the
whole grid in a serpentine (boustrophedon) path and eats each active
contribution square exactly as it passes over it.

Pure SVG + SMIL: the snake's body segments move along one long
polyline path via <animateMotion>, which is arc-length-parametrized
by default (constant speed). Each contribution square's fade-out time
is computed from its exact position along that same path, so the
"eat" always lines up with the snake's head — no JS needed.

Usage:
    python tools/render_snake.py
    PREVIEW=1 python tools/render_snake.py   # static mid-crawl frame
"""
import json
import math
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
IN_JSON = ASSETS / "contributions.json"
OUT_SVG = ROOT / "snake.svg"

# --- palette sampled from the user's avatar -------------------------
BG = "#0a0e1c"
ACCENT = "#00f0c0"      # mint teal — snake body
ACCENT2 = "#7c5cff"     # indigo/purple — snake head accent
EMPTY_CELL = "#141a30"  # inactive day squares
ACTIVE_LEVELS = ["#0f3d34", "#0f6e5c", "#0fae90", "#00f0c0"]  # low -> high
# ---------------------------------------------------------------------

CELL = 11
GAP = 3
PAD = 24
LABEL_H = 20
SNAKE_SEGMENTS = 6
SEGMENT_SIZE = CELL - 1
TOTAL_DURATION_S = 34  # one full lap of the grid


def build_weeks(days):
    if not days:
        return []
    by_date = {d["date"]: d for d in days}
    dates = sorted(by_date.keys())
    start = datetime.strptime(dates[0], "%Y-%m-%d")
    end = datetime.strptime(dates[-1], "%Y-%m-%d")

    start_weekday = (start.weekday() + 1) % 7  # Sunday=0
    start = start - timedelta(days=start_weekday)

    weeks = []
    current_week = []
    d = start
    while d <= end:
        key = d.strftime("%Y-%m-%d")
        cell = by_date.get(key, {"date": key, "count": 0, "level": 0})
        current_week.append(cell)
        if len(current_week) == 7:
            weeks.append(current_week)
            current_week = []
        d += timedelta(days=1)
    if current_week:
        while len(current_week) < 7:
            current_week.append({"date": None, "count": 0, "level": 0})
        weeks.append(current_week)
    return weeks


def cell_center(col, row):
    x = PAD + col * (CELL + GAP) + CELL / 2
    y = PAD + LABEL_H + row * (CELL + GAP) + CELL / 2
    return x, y


def serpentine_order(n_weeks):
    """Boustrophedon path: down a column, then across, then up the next."""
    order = []
    for col in range(n_weeks):
        rows = range(7) if col % 2 == 0 else range(6, -1, -1)
        for row in rows:
            order.append((col, row))
    return order


def build_path_and_arclengths(order):
    points = [cell_center(c, r) for c, r in order]
    cumulative = [0.0]
    for i in range(1, len(points)):
        x0, y0 = points[i - 1]
        x1, y1 = points[i]
        d = math.hypot(x1 - x0, y1 - y0)
        cumulative.append(cumulative[-1] + d)
    return points, cumulative


def escape_xml(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_svg(weeks, stats, username, static=False) -> str:
    n_weeks = len(weeks)
    width = PAD * 2 + n_weeks * (CELL + GAP)
    height = PAD + LABEL_H + 7 * (CELL + GAP) + 70

    order = serpentine_order(n_weeks)
    points, cumulative = build_path_and_arclengths(order)
    total_len = cumulative[-1] if cumulative[-1] > 0 else 1

    # map (col,row) -> arrival time fraction along the path
    arrive_frac = {}
    for (col, row), dist in zip(order, cumulative):
        arrive_frac[(col, row)] = dist / total_len

    path_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG}" rx="10"/>')
    parts.append(
        f'<text x="{PAD}" y="{PAD}" font-size="13" fill="#7d8aa8">'
        f'$ snake --eat contributions.log --user {username}</text>'
    )
    parts.append(f'<path id="snakePath" d="{path_d}" fill="none" stroke="none"/>')

    grid_top = PAD + LABEL_H

    # --- background/active day squares, each fades out when eaten ---
    for col, week in enumerate(weeks):
        x = PAD + col * (CELL + GAP)
        for row, day in enumerate(week):
            y = grid_top + row * (CELL + GAP)
            level = min(day.get("level", 0), len(ACTIVE_LEVELS) - 1)
            count = day.get("count", 0)
            title = day.get("date") or ""

            if count > 0:
                color = ACTIVE_LEVELS[level] if level > 0 else ACTIVE_LEVELS[0]
            else:
                color = EMPTY_CELL

            if static or count == 0:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}">'
                    f'<title>{title}: {count} contribution{"s" if count != 1 else ""}</title>'
                    f'</rect>'
                )
            else:
                f = arrive_frac.get((col, row), 0.0)
                eat_time = f * TOTAL_DURATION_S
                eps = min(0.15, TOTAL_DURATION_S * 0.01)
                kt0 = max(0.0, (eat_time - eps) / TOTAL_DURATION_S)
                kt1 = min(1.0, (eat_time) / TOTAL_DURATION_S)
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}">'
                    f'<title>{title}: {count} contribution{"s" if count != 1 else ""}</title>'
                    f'<animate attributeName="opacity" '
                    f'keyTimes="0;{kt0:.4f};{kt1:.4f};1" '
                    f'values="1;1;0;0" '
                    f'dur="{TOTAL_DURATION_S}s" repeatCount="indefinite"/>'
                    f'</rect>'
                )

    # --- the snake itself: segments trailing along the same path ---
    if not static:
        for i in range(SNAKE_SEGMENTS):
            is_head = i == 0
            color = ACCENT2 if is_head else ACCENT
            opacity = 1.0 if is_head else max(0.35, 1 - i * 0.15)
            delay = -(i * (TOTAL_DURATION_S / max(len(order), 1)) * 2.2)
            parts.append(
                f'<rect x="{-SEGMENT_SIZE/2:.1f}" y="{-SEGMENT_SIZE/2:.1f}" '
                f'width="{SEGMENT_SIZE}" height="{SEGMENT_SIZE}" rx="2" '
                f'fill="{color}" opacity="{opacity:.2f}">'
                f'<animateMotion dur="{TOTAL_DURATION_S}s" begin="{delay:.2f}s" '
                f'repeatCount="indefinite" rotate="0">'
                f'<mpath href="#snakePath"/>'
                f'</animateMotion>'
                f'</rect>'
            )
    else:
        # static preview: draw the head partway along the path
        mid_idx = len(points) // 3
        hx, hy = points[mid_idx]
        parts.append(
            f'<rect x="{hx - SEGMENT_SIZE/2:.1f}" y="{hy - SEGMENT_SIZE/2:.1f}" '
            f'width="{SEGMENT_SIZE}" height="{SEGMENT_SIZE}" rx="2" fill="{ACCENT2}"/>'
        )
        for i in range(1, SNAKE_SEGMENTS):
            idx = max(0, mid_idx - i * 2)
            sx, sy = points[idx]
            parts.append(
                f'<rect x="{sx - SEGMENT_SIZE/2:.1f}" y="{sy - SEGMENT_SIZE/2:.1f}" '
                f'width="{SEGMENT_SIZE}" height="{SEGMENT_SIZE}" rx="2" '
                f'fill="{ACCENT}" opacity="{max(0.35, 1 - i * 0.15):.2f}"/>'
            )

    # legend + stats
    legend_y = grid_top + 7 * (CELL + GAP) + 22
    parts.append(f'<text x="{PAD}" y="{legend_y}" font-size="11" fill="#7d8aa8">Less</text>')
    lx = PAD + 34
    for color in [EMPTY_CELL] + ACTIVE_LEVELS:
        parts.append(f'<rect x="{lx}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y}" font-size="11" fill="#7d8aa8">More</text>')

    stats_y = legend_y + 26
    stats_line = (
        f'{stats.get("total", 0)} contributions in the last year &#183; '
        f'streak {stats.get("current_streak", 0)}d &#183; '
        f'longest {stats.get("longest_streak", 0)}d &#183; '
        f'busiest {stats.get("busiest_day", "-")}'
    )
    parts.append(f'<text x="{PAD}" y="{stats_y}" font-size="11" fill="{ACCENT}">{stats_line}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not IN_JSON.exists():
        print(f"Missing {IN_JSON} — run pull_contributions.py first.")
        return

    payload = json.loads(IN_JSON.read_text(encoding="utf-8"))
    weeks = build_weeks(payload.get("days", []))

    static = os.environ.get("PREVIEW") == "1"
    svg = render_svg(weeks, payload.get("stats", {}), payload.get("username", ""), static=static)

    if static:
        preview_path = ROOT / "snake-preview.svg"
        preview_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {preview_path} (static mid-crawl frame, for previewing only)")
    else:
        OUT_SVG.write_text(svg, encoding="utf-8")
        print(f"Wrote {OUT_SVG} ({len(weeks)} weeks, {len(weeks)*7} cells)")


if __name__ == "__main__":
    main()
