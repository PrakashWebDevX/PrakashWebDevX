#!/usr/bin/env python3
"""
Draw assets/contributions.json as a 52-ish-week x 7-day grid of
rounded squares, animated in column by column (a "wave" reveal
rather than the more common row-by-row wipe).

Usage:
    python tools/render_graph.py
    # writes graph.svg
"""
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
IN_JSON = ASSETS / "contributions.json"
OUT_SVG = ROOT / "graph.svg"

# index 0 = no activity ... index 4 = top activity tier (neon-cyan terminal theme)
LEVELS = ["#0f2b28", "#0d5c50", "#00a389", "#00e6b8", "#00ffcc"]

CELL = 11
GAP = 3
PAD = 24
LABEL_H = 20
COL_DELAY_MS = 18
CELL_FADE_MS = 260


def build_weeks(days):
    """Group days into week-columns, Sunday-first, matching GitHub's layout."""
    if not days:
        return []

    by_date = {d["date"]: d for d in days}
    dates = sorted(by_date.keys())
    start = datetime.strptime(dates[0], "%Y-%m-%d")
    end = datetime.strptime(dates[-1], "%Y-%m-%d")

    # rewind start to the preceding Sunday so weeks align
    start_weekday = (start.weekday() + 1) % 7  # Sunday=0
    from datetime import timedelta
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


def render_svg(weeks, stats, username, static=False) -> str:
    n_weeks = len(weeks)
    width = PAD * 2 + n_weeks * (CELL + GAP)
    height = PAD + LABEL_H + 7 * (CELL + GAP) + 70  # extra for legend + stats line

    parts = []
    parts.append(
        f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" '
        f'font-family="Consolas, Menlo, monospace">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="#0d1117" rx="10"/>')
    parts.append(
        f'<text x="{PAD}" y="{PAD}" font-size="13" fill="#8b949e">'
        f'$ cat contributions.log --user {username}</text>'
    )

    grid_top = PAD + LABEL_H
    for wi, week in enumerate(weeks):
        x = PAD + wi * (CELL + GAP)
        delay = wi * COL_DELAY_MS
        for di, day in enumerate(week):
            y = grid_top + di * (CELL + GAP)
            level = min(day.get("level", 0), len(LEVELS) - 1)
            color = LEVELS[level]
            title = day.get("date") or ""
            count = day.get("count", 0)
            if static:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}">'
                    f'<title>{title}: {count} contribution{"s" if count != 1 else ""}</title>'
                    f'</rect>'
                )
            else:
                parts.append(
                    f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                    f'fill="{color}" opacity="0">'
                    f'<title>{title}: {count} contribution{"s" if count != 1 else ""}</title>'
                    f'<animate attributeName="opacity" from="0" to="1" '
                    f'begin="{delay}ms" dur="{CELL_FADE_MS}ms" fill="freeze"/>'
                    f'</rect>'
                )

    # legend
    legend_y = grid_top + 7 * (CELL + GAP) + 22
    parts.append(f'<text x="{PAD}" y="{legend_y}" font-size="11" fill="#8b949e">Less</text>')
    lx = PAD + 34
    for level, color in enumerate(LEVELS):
        parts.append(f'<rect x="{lx}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="2.5" fill="{color}"/>')
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 4}" y="{legend_y}" font-size="11" fill="#8b949e">More</text>')

    # stats line
    stats_y = legend_y + 26
    stats_line = (
        f'{stats.get("total", 0)} contributions in the last year · '
        f'current streak {stats.get("current_streak", 0)}d · '
        f'longest streak {stats.get("longest_streak", 0)}d · '
        f'busiest day {stats.get("busiest_day", "—")}'
    )
    parts.append(f'<text x="{PAD}" y="{stats_y}" font-size="11" fill="#00FFCC">{stats_line}</text>')

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
        preview_path = ROOT / "graph-preview.svg"
        preview_path.write_text(svg, encoding="utf-8")
        print(f"Wrote {preview_path} (static frame, for previewing only) ({len(weeks)} weeks)")
    else:
        OUT_SVG.write_text(svg, encoding="utf-8")
        print(f"Wrote {OUT_SVG} ({len(weeks)} weeks)")


if __name__ == "__main__":
    main()
