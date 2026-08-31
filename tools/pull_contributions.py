#!/usr/bin/env python3
"""
Pull the public contribution calendar for GITHUB_USERNAME from the
plain HTML fragment GitHub itself uses to render profile pages — no
OAuth token needed.

Usage:
    python tools/pull_contributions.py
    # writes assets/contributions.json
"""
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import httpx
from lxml import html

USERNAME = os.environ.get("GITHUB_USERNAME", "PrakashWebDevX")
URL = f"https://github.com/users/{USERNAME}/contributions"

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)
OUT_JSON = ASSETS / "contributions.json"


def fetch_calendar_html() -> str:
    resp = httpx.get(URL, timeout=20, headers={"User-Agent": "living-terminal-readme"})
    resp.raise_for_status()
    return resp.text


def parse_days(fragment_html: str):
    """
    GitHub renders each day as a <td data-date="..." data-level="..." id="...">
    with NO count on the cell itself — the count lives in the text of a
    sibling <tool-tip for="that-id">N contributions on <date>.</tool-tip>
    (or "No contributions on <date>." for zero).
    """
    tree = html.fromstring(fragment_html)
    cells = tree.xpath('//td[@data-date]')

    # map cell id -> tooltip text, via the tool-tip's `for` attribute
    tooltip_by_for = {}
    for tip in tree.xpath('//tool-tip[@for]'):
        tooltip_by_for[tip.get("for")] = "".join(tip.itertext()).strip()

    days = []
    for cell in cells:
        date_str = cell.get("data-date")
        level = int(cell.get("data-level") or 0)
        cell_id = cell.get("id")

        count = 0
        tooltip_text = tooltip_by_for.get(cell_id, "")
        if tooltip_text and not tooltip_text.lower().startswith("no contributions"):
            for token in tooltip_text.split():
                token = token.replace(",", "")
                if token.isdigit():
                    count = int(token)
                    break

        if date_str:
            days.append({"date": date_str, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)

    # current streak (from the most recent day backwards)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break

    # longest streak
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    # busiest day of week
    by_weekday = defaultdict(int)
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        by_weekday[dt.strftime("%A")] += d["count"]

    busiest_day = max(by_weekday, key=by_weekday.get) if by_weekday else None

    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "busiest_day": busiest_day,
    }


def main():
    print(f"Fetching contribution calendar for {USERNAME}...")
    fragment = fetch_calendar_html()
    days = parse_days(fragment)

    if not days:
        print("Warning: no day cells parsed — GitHub's markup may have changed.")

    stats = compute_stats(days)

    payload = {
        "username": USERNAME,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "days": days,
        "stats": stats,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_JSON}: {len(days)} days, {stats}")


if __name__ == "__main__":
    main()
