#!/usr/bin/env python3
"""Fetch GitHub contribution calendar for jeevabharathi44 and write data/contributions.json."""

from __future__ import annotations

import json
import os
import re
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "jeevabharathi44")
ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "data" / "contributions.json"

TD_RE = re.compile(r"<td\b[^>]*data-date=\"([^\"]+)\"[^>]*>")
ID_RE = re.compile(r'\bid="([^"]+)"')
LEVEL_RE = re.compile(r'\bdata-level="(\d)"')
TIP_RE = re.compile(r'<tool-tip\b[^>]*\bfor="([^"]+)"[^>]*>([^<]+)<')
COUNT_RE = re.compile(r"^(\d+)\s+contribution")


def fetch_html(username: str) -> str:
    url = f"https://github.com/users/{username}/contributions"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; readme-card-bot/1.0)",
            "Accept": "text/html",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def compute_streaks(days: list[dict]) -> tuple[int, int]:
    """Return (current_streak, longest_streak) across chronologically sorted days."""
    longest = 0
    run = 0
    for d in days:
        if d["count"] > 0:
            run += 1
            if run > longest:
                longest = run
        else:
            run = 0

    current = 0
    # Walk backwards from the latest day; allow today to be 0 if yesterday was active.
    idx = len(days) - 1
    if idx >= 0 and days[idx]["count"] == 0:
        idx -= 1
    while idx >= 0 and days[idx]["count"] > 0:
        current += 1
        idx -= 1

    return current, longest


def parse_contributions(html: str) -> dict:
    tips = {m.group(1): m.group(2).strip() for m in TIP_RE.finditer(html)}

    days: list[dict] = []
    for m in TD_RE.finditer(html):
        tag = m.group(0)
        date_str = m.group(1)
        id_m = ID_RE.search(tag)
        lvl_m = LEVEL_RE.search(tag)
        cell_id = id_m.group(1) if id_m else ""
        level = int(lvl_m.group(1)) if lvl_m else 0
        tip = tips.get(cell_id, "")
        cnt_match = COUNT_RE.match(tip)
        count = int(cnt_match.group(1)) if cnt_match else 0
        days.append(
            {
                "date": date_str,
                "level": level,
                "count": count,
            }
        )

    days.sort(key=lambda d: d["date"])

    monthly: dict[str, int] = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    # Keep the most recent 12 months in chronological order
    sorted_months = sorted(monthly.items())[-12:]
    months_list = [
        {
            "month": ym,
            "label": datetime.strptime(ym, "%Y-%m").strftime("%b"),
            "count": cnt,
        }
        for ym, cnt in sorted_months
    ]

    total = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    busiest = max(days, key=lambda d: d["count"], default={"date": "", "count": 0})
    current_streak, longest_streak = compute_streaks(days)

    return {
        "username": USERNAME,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total": total,
        "active_days": active_days,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "busiest_day": {
            "date": busiest["date"],
            "count": busiest["count"],
        },
        "months": months_list,
        "days": days,
    }


def main() -> None:
    html = fetch_html(USERNAME)
    data = parse_contributions(html)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(
        f"Saved {len(data['days'])} days, total={data['total']}, "
        f"active={data['active_days']}, streak={data['current_streak']}d"
    )


if __name__ == "__main__":
    main()
