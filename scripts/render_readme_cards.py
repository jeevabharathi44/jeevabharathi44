#!/usr/bin/env python3
"""Render animated SVG cards for Jeeva Bharathi M's GitHub Profile README."""

from __future__ import annotations

import base64
import html
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "contributions.json"
FONTS_DIR = ROOT / "fonts"
CARDS_DIR = ROOT / "cards"

STATIC = os.environ.get("STATIC", "0") == "1"

SUBSET_CHARS = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    ".,:;!?@#$%&*+-=/\\|()[]{}<>\"'`~_ \u2192\u2197\u00b7\u2014\u2013\u2022"
)

FONT_SPECS = [
    (
        "instrument-serif-regular.woff2",
        "Instrument Serif",
        "normal",
        "400",
        "https://fonts.googleapis.com/css2?family=Instrument+Serif&text="
        + urllib.parse.quote(SUBSET_CHARS),
    ),
    (
        "instrument-serif-italic.woff2",
        "Instrument Serif",
        "italic",
        "400",
        "https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@1&text="
        + urllib.parse.quote(SUBSET_CHARS),
    ),
    (
        "plus-jakarta-sans.woff2",
        "Plus Jakarta Sans",
        "normal",
        "400 600",
        "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600&text="
        + urllib.parse.quote(SUBSET_CHARS),
    ),
    (
        "ibm-plex-mono.woff2",
        "IBM Plex Mono",
        "normal",
        "400 500",
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&text="
        + urllib.parse.quote(SUBSET_CHARS),
    ),
]

THEMES = {
    "light": {
        "bg": "#f6f4ef",
        "bg_alt": "#ede9e0",
        "surface": "#ffffff",
        "ink": "#161615",
        "muted": "#5c5952",
        "rule": "#d5cfc3",
        "accent": "#c84623",
        "accent_soft": "#f4dfd8",
        "ok": "#146c43",
        "ok_soft": "#d7ece2",
        "warn": "#b45309",
        "warn_soft": "#f5e6d0",
        "levels": ["#ede9e0", "#f0c9bc", "#e3967d", "#d46a49", "#c84623"],
        "shine": "#ffffff",
    },
    "dark": {
        "bg": "#0e1318",
        "bg_alt": "#141b22",
        "surface": "#19222b",
        "ink": "#eef2f6",
        "muted": "#93a1b0",
        "rule": "#283543",
        "accent": "#e86a42",
        "accent_soft": "#2c1e1d",
        "ok": "#34d399",
        "ok_soft": "#132924",
        "warn": "#fbbf24",
        "warn_soft": "#292316",
        "levels": ["#19222b", "#452721", "#783b2c", "#b05136", "#e86a42"],
        "shine": "#eef2f6",
    },
}

# 14-row ASCII/block monogram emblem ("JB") for the hero card
MONOGRAM_ROWS = [
    "  +----------------+",
    "  |  _JB // 2026   |",
    "  +----------------+",
    "      ######  ##### ",
    "        ##    ##  ##",
    "        ##    ##### ",
    "    ##  ##    ##  ##",
    "     ####     ##### ",
    "  ------------------",
    "  > SWE · AI/ML     ",
    "  > FastAPI · React ",
    "  > EBM · LLM APIs  ",
    "  +----------------+",
]


def ensure_fonts() -> str:
    """Load subsetted WOFF2 fonts from fonts/ (downloading if absent) and return @font-face CSS."""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    css_parts: list[str] = []
    ua = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    for filename, family, style, weight, url in FONT_SPECS:
        path = FONTS_DIR / filename
        if not path.exists():
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            with urllib.request.urlopen(req, timeout=20) as resp:
                css_text = resp.read().decode("utf-8", errors="ignore")
            m = re.search(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css_text)
            if m:
                font_req = urllib.request.Request(m.group(1), headers={"User-Agent": ua})
                with urllib.request.urlopen(font_req, timeout=20) as f_resp:
                    path.write_bytes(f_resp.read())
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            for w in weight.split():
                css_parts.append(
                    f"@font-face{{font-family:'{family}';font-style:{style};"
                    f"font-weight:{w};src:url(data:font/woff2;base64,{b64}) format('woff2');}}"
                )
    return "\n".join(css_parts)


def base_styles(font_css: str, extra_css: str) -> str:
    reduced = (
        "@media (prefers-reduced-motion: reduce){"
        "*{animation:none !important;transition:none !important;opacity:1 !important;transform:none !important;}"
        "}"
    )
    return f"<style>\n{font_css}\n{extra_css}\n{reduced}\n</style>"


def esc(val: object) -> str:
    return html.escape(str(val), quote=True)


def render_hero(t: dict, font_css: str) -> str:
    w, h = 880, 224
    anim_rise = "" if STATIC else "opacity:0;animation:rise 0.65s cubic-bezier(.22,1,.36,1) forwards;"
    pulse_css = "" if STATIC else "animation:pulse 2.2s ease-in-out infinite;"
    extra = f"""
    .serif {{ font-family: 'Instrument Serif', Georgia, serif; }}
    .sans {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }}
    .mono {{ font-family: 'IBM Plex Mono', monospace; }}
    .r1 {{ {anim_rise} animation-delay: 0.05s; }}
    .r2 {{ {anim_rise} animation-delay: 0.18s; }}
    .r3 {{ {anim_rise} animation-delay: 0.30s; }}
    .dot {{ {pulse_css} transform-box: fill-box; transform-origin: center; }}
    .ascii-row {{ {'opacity:1;' if STATIC else 'opacity:0;animation:fadeIn 0.25s ease forwards;'} }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
    @keyframes fadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    @keyframes pulse {{ 0%,100% {{ transform:scale(1); opacity:1; }} 50% {{ transform:scale(1.45); opacity:0.55; }} }}
    """

    shine_grad = f"""
    <linearGradient id="nameShine" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{t['accent']}" />
      <stop offset="42%" stop-color="{t['accent']}" />
      <stop offset="50%" stop-color="{t['shine']}" />
      <stop offset="58%" stop-color="{t['accent']}" />
      <stop offset="100%" stop-color="{t['accent']}" />
      {'' if STATIC else '<animateTransform attributeName="gradientTransform" type="translate" from="-1 0" to="2 0" dur="4.5s" repeatCount="indefinite" />'}
    </linearGradient>
    """

    ascii_lines = []
    for idx, line in enumerate(MONOGRAM_ROWS):
        y = 38 + idx * 12.5
        delay = f"{0.12 + idx * 0.025:.3f}s"
        fill = t["accent"] if ("#" in line or "_JB" in line) else t["muted"]
        style = "" if STATIC else f'style="animation-delay:{delay}"'
        ascii_lines.append(
            f'<text x="646" y="{y:.1f}" class="mono ascii-row" font-size="10.5" '
            f'fill="{fill}" xml:space="preserve" {style}>{esc(line)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Jeeva Bharathi M Hero Card">
  <defs>{shine_grad}</defs>
  {base_styles(font_css, extra)}
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{t['bg']}" stroke="{t['rule']}" />
  <rect x="626" y="18" width="234" height="{h-36}" rx="8" fill="{t['bg_alt']}" stroke="{t['rule']}" />
  <g class="r1">
    <circle cx="38" cy="39" r="4.5" fill="{t['ok']}" class="dot" />
    <text x="52" y="43" class="mono" font-size="11.5" fill="{t['muted']}" letter-spacing="0.08em">AVAILABLE FOR SWE / FULL-STACK / AI-ML ROLES · MADURAI, IN</text>
  </g>
  <g class="r2">
    <text x="34" y="108" class="serif" font-size="56" fill="{t['ink']}">Jeeva <tspan font-style="italic" fill="url(#nameShine)">Bharathi M</tspan></text>
  </g>
  <g class="r3">
    <text x="36" y="144" class="sans" font-size="15.5" font-weight="600" fill="{t['ink']}">Final-Year B.E. CSE Student · Software &amp; AI Engineering</text>
    <text x="36" y="169" class="sans" font-size="13.5" fill="{t['muted']}">Building explainable ML systems, LLM pipelines, and full-stack web apps</text>
    <text x="36" y="196" class="mono" font-size="11.5" fill="{t['accent']}">PYTHON · FASTAPI · REACT · NODE.JS · EBM · LLM APIS · DOCKER</text>
  </g>
  {''.join(ascii_lines)}
</svg>"""


def render_graph(data: dict, t: dict, font_css: str) -> str:
    w, h = 880, 168
    days = data.get("days", [])
    # Group into columns of 7 (weeks)
    weeks: list[list[dict]] = []
    for i in range(0, len(days), 7):
        weeks.append(days[i : i + 7])
    weeks = weeks[-53:]

    extra = f"""
    .mono {{ font-family: 'IBM Plex Mono', monospace; }}
    .sans {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }}
    .cell {{ {'opacity:1;' if STATIC else 'opacity:0;animation:pop 0.25s ease forwards;'} }}
    @keyframes pop {{ from {{ opacity:0; transform:scale(0.6); }} to {{ opacity:1; transform:scale(1); }} }}
    """

    cells = []
    start_x = 34
    start_y = 48
    step = 15.4
    size = 11.4
    for wi, week in enumerate(weeks):
        delay = 0.45 + wi * 0.018
        for di, day in enumerate(week):
            cx = start_x + wi * step
            cy = start_y + di * step
            lvl = max(0, min(4, int(day.get("level", 0))))
            fill = t["levels"][lvl]
            style = "" if STATIC else f'style="animation-delay:{delay:.3f}s;transform-origin:{cx + size/2:.1f}px {cy + size/2:.1f}px"'
            cells.append(
                f'<rect x="{cx:.1f}" y="{cy:.1f}" width="{size}" height="{size}" rx="2.5" '
                f'fill="{fill}" class="cell" {style}><title>{esc(day["date"])}: {day["count"]} contributions</title></rect>'
            )

    legend_rects = []
    for i, col in enumerate(t["levels"]):
        lx = 768 + i * 15
        legend_rects.append(f'<rect x="{lx}" y="22" width="11" height="11" rx="2" fill="{col}" />')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Contribution Graph">
  {base_styles(font_css, extra)}
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{t['bg']}" stroke="{t['rule']}" />
  <text x="34" y="31" class="mono" font-size="11.5" fill="{t['muted']}" letter-spacing="0.08em">CONTRIBUTION MATRIX · LAST 53 WEEKS</text>
  <text x="732" y="31" class="mono" font-size="10.5" fill="{t['muted']}">LESS</text>
  {''.join(legend_rects)}
  <text x="846" y="31" class="mono" font-size="10.5" fill="{t['muted']}">MORE</text>
  {''.join(cells)}
</svg>"""


def render_activity(data: dict, t: dict, font_css: str) -> str:
    w, h = 880, 210
    months = data.get("months", [])[-12:]
    max_cnt = max((m["count"] for m in months), default=1) or 1
    best_idx = max(range(len(months)), key=lambda i: months[i]["count"]) if months else -1

    extra = f"""
    .serif {{ font-family: 'Instrument Serif', Georgia, serif; }}
    .sans {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }}
    .mono {{ font-family: 'IBM Plex Mono', monospace; }}
    .bar {{ transform-box: fill-box; transform-origin: bottom; {'transform:scaleY(1);' if STATIC else 'transform:scaleY(0);animation:grow 0.65s cubic-bezier(.22,1,.36,1) forwards;'} }}
    .peak {{ {'opacity:1;' if STATIC else 'opacity:0;animation:fadeIn 0.35s ease 1.7s forwards;'} }}
    @keyframes grow {{ from {{ transform:scaleY(0); }} to {{ transform:scaleY(1); }} }}
    @keyframes fadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
    """

    bars = []
    base_y = 164
    max_bar_h = 96
    bar_w = 32
    gap = 16
    start_x = 34
    for i, m in enumerate(months):
        bx = start_x + i * (bar_w + gap)
        bh = max(4, (m["count"] / max_cnt) * max_bar_h) if m["count"] > 0 else 4
        by = base_y - bh
        is_best = i == best_idx and m["count"] > 0
        fill = t["accent"] if is_best else t["rule"]
        delay = f"{0.95 + i * 0.045:.3f}s"
        style = "" if STATIC else f'style="animation-delay:{delay}"'
        bars.append(
            f'<rect x="{bx}" y="{by:.1f}" width="{bar_w}" height="{bh:.1f}" rx="4" fill="{fill}" class="bar" {style} />'
        )
        bars.append(
            f'<text x="{bx + bar_w/2:.1f}" y="182" text-anchor="middle" class="mono" font-size="10.5" '
            f'fill="{t["accent"] if is_best else t["muted"]}">{esc(m["label"].upper())}</text>'
        )
        if is_best:
            bars.append(
                f'<text x="{bx + bar_w/2:.1f}" y="{by - 8:.1f}" text-anchor="middle" class="mono peak" '
                f'font-size="11" font-weight="500" fill="{t["accent"]}">{m["count"]}</text>'
            )

    busiest = data.get("busiest_day", {})
    busiest_cnt = busiest.get("count", 0)
    busiest_date = busiest.get("date", "—")

    stats = [
        ("TOTAL (12M)", str(data.get("total", 0)), "contributions"),
        ("ACTIVE DAYS", str(data.get("active_days", 0)), "days coded"),
        ("BEST STREAK", f"{data.get('longest_streak', 0)}d", f"current: {data.get('current_streak', 0)}d"),
        ("BUSIEST DAY", str(busiest_cnt), busiest_date),
    ]
    stat_nodes = []
    for idx, (label, val, sub) in enumerate(stats):
        col = idx % 2
        row = idx // 2
        sx = 626 + col * 120
        sy = 64 + row * 68
        stat_nodes.append(
            f'<text x="{sx}" y="{sy}" class="mono" font-size="10" fill="{t["muted"]}" letter-spacing="0.06em">{esc(label)}</text>'
            f'<text x="{sx}" y="{sy + 26}" class="serif" font-size="28" fill="{t["ink"]}">{esc(val)}</text>'
            f'<text x="{sx}" y="{sy + 41}" class="mono" font-size="10" fill="{t["muted"]}">{esc(sub)}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Monthly Activity Chart">
  {base_styles(font_css, extra)}
  <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{t['bg']}" stroke="{t['rule']}" />
  <text x="34" y="31" class="mono" font-size="11.5" fill="{t['muted']}" letter-spacing="0.08em">MONTHLY CADENCE · PEAK HIGHLIGHTED</text>
  <line x1="34" y1="{base_y}" x2="594" y2="{base_y}" stroke="{t['rule']}" stroke-width="1" />
  <line x1="608" y1="24" x2="608" y2="{h - 24}" stroke="{t['rule']}" stroke-width="1" />
  {''.join(bars)}
  {''.join(stat_nodes)}
</svg>"""


def count_up_frames(target: int, x: float, y: float, fill: str, delay_start: float) -> str:
    """Generate 18 SMIL <set> frames to count up from 0 to target (since CSS cannot animate text)."""
    if STATIC or target <= 0:
        return f'<text x="{x}" y="{y}" class="serif" font-size="48" fill="{fill}">{target}</text>'

    steps = 18
    dur = 0.045
    nodes = []
    for i in range(steps):
        val = round((i / (steps - 1)) * target)
        begin = delay_start + i * dur
        end_attr = f'dur="{dur:.3f}s"' if i < steps - 1 else 'fill="freeze"'
        nodes.append(
            f'<text x="{x}" y="{y}" class="serif" font-size="48" fill="{fill}" visibility="hidden">'
            f'<set attributeName="visibility" to="visible" begin="{begin:.3f}s" {end_attr} />'
            f"{val}</text>"
        )
    return "".join(nodes)


def render_tile(
    t: dict,
    font_css: str,
    tag: str,
    title: str,
    subtitle: str,
    metric: int,
    metric_suffix: str,
    accent_key: str,
    soft_key: str,
    delay: float,
) -> str:
    w, h = 286, 176
    ac = t[accent_key]
    soft = t[soft_key]
    enter_css = (
        "transform:none;opacity:1;"
        if STATIC
        else f"opacity:0;transform-box:fill-box;transform-origin:center bottom;animation:swingUp 0.7s cubic-bezier(.22,1.28,.36,1) {delay:.2f}s forwards;"
    )
    ring_css = "" if STATIC else f"transform-box:fill-box;transform-origin:center;animation:ring 3.2s ease-out {delay + 0.8:.2f}s infinite;"
    arrow_css = "" if STATIC else f"animation:nudge 2.4s ease-in-out {delay + 1.0:.2f}s infinite;"

    extra = f"""
    .serif {{ font-family: 'Instrument Serif', Georgia, serif; }}
    .sans {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }}
    .mono {{ font-family: 'IBM Plex Mono', monospace; }}
    .card {{ {enter_css} }}
    .ring {{ {ring_css} }}
    .arrow {{ {arrow_css} }}
    @keyframes swingUp {{
      0% {{ opacity:0; transform:translateY(22px) rotate(-2.5deg); }}
      65% {{ opacity:1; transform:translateY(-3px) rotate(0.6deg); }}
      100% {{ opacity:1; transform:translateY(0) rotate(0deg); }}
    }}
    @keyframes ring {{
      0% {{ transform:scale(0.8); opacity:0.85; }}
      100% {{ transform:scale(2.4); opacity:0; }}
    }}
    @keyframes nudge {{
      0%,100% {{ transform:translate(0,0); }}
      50% {{ transform:translate(2.5px,-2.5px); }}
    }}
    """

    shine = ""
    if not STATIC:
        shine = f"""
        <linearGradient id="tileShine" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{t['shine']}" stop-opacity="0" />
          <stop offset="45%" stop-color="{t['shine']}" stop-opacity="0" />
          <stop offset="50%" stop-color="{t['shine']}" stop-opacity="0.18" />
          <stop offset="55%" stop-color="{t['shine']}" stop-opacity="0" />
          <stop offset="100%" stop-color="{t['shine']}" stop-opacity="0" />
          <animateTransform attributeName="gradientTransform" type="translate" from="-1 -1" to="2 2" dur="5.5s" begin="{delay + 1.2:.2f}s" repeatCount="indefinite" />
        </linearGradient>
        """

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)} Tile">
  <defs>{shine}</defs>
  {base_styles(font_css, extra)}
  <g class="card">
    <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{t['bg']}" stroke="{t['rule']}" />
    <rect x="1" y="1" width="{w-2}" height="5" rx="3" fill="{ac}" />
    {'' if STATIC else f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="11" fill="url(#tileShine)" />'}
    <rect x="20" y="24" width="118" height="22" rx="11" fill="{soft}" />
    <text x="30" y="38.5" class="mono" font-size="10.5" font-weight="500" fill="{ac}">{esc(tag)}</text>
    <circle cx="{w - 28}" cy="35" r="4" fill="{ac}" />
    <circle cx="{w - 28}" cy="35" r="5" fill="none" stroke="{ac}" stroke-width="1.5" class="ring" />
    {count_up_frames(metric, 20, 102, t['ink'], delay + 0.35)}
    <text x="{24 + len(str(metric)) * 24}" y="100" class="mono" font-size="13" fill="{ac}">{esc(metric_suffix)}</text>
    <text x="20" y="132" class="sans" font-size="16" font-weight="600" fill="{t['ink']}">{esc(title)}</text>
    <text x="20" y="152" class="sans" font-size="12" fill="{t['muted']}">{esc(subtitle)}</text>
    <text x="{w - 30}" y="152" class="mono arrow" font-size="15" fill="{ac}">&#x2197;</text>
  </g>
</svg>"""


def render_repo(
    t: dict,
    font_css: str,
    badge: str,
    name: str,
    desc1: str,
    desc2: str,
    stack: str,
    delay: float,
) -> str:
    w, h = 432, 146
    anim = "" if STATIC else f"opacity:0;animation:rise 0.55s cubic-bezier(.22,1,.36,1) {delay:.2f}s forwards;"
    extra = f"""
    .serif {{ font-family: 'Instrument Serif', Georgia, serif; }}
    .sans {{ font-family: 'Plus Jakarta Sans', system-ui, sans-serif; }}
    .mono {{ font-family: 'IBM Plex Mono', monospace; }}
    .wrap {{ {anim} }}
    @keyframes rise {{ from {{ opacity:0; transform:translateY(10px); }} to {{ opacity:1; transform:translateY(0); }} }}
    """
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(name)} Repository Card">
  {base_styles(font_css, extra)}
  <g class="wrap">
    <rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="12" fill="{t['bg']}" stroke="{t['rule']}" />
    <text x="24" y="30" class="mono" font-size="10.5" fill="{t['accent']}" letter-spacing="0.06em">{esc(badge)}</text>
    <text x="{w - 32}" y="30" class="mono" font-size="14" fill="{t['muted']}">&#x2197;</text>
    <text x="24" y="64" class="serif" font-size="29" fill="{t['ink']}">{esc(name)}</text>
    <text x="24" y="88" class="sans" font-size="12.5" fill="{t['muted']}">{esc(desc1)}</text>
    <text x="24" y="106" class="sans" font-size="12.5" fill="{t['muted']}">{esc(desc2)}</text>
    <text x="24" y="128" class="mono" font-size="10.5" fill="{t['ink']}">{esc(stack)}</text>
  </g>
</svg>"""


def main() -> None:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    font_css = ensure_fonts()
    CARDS_DIR.mkdir(parents=True, exist_ok=True)

    for theme_name, theme in THEMES.items():
        outputs = {
            f"hero-{theme_name}.svg": render_hero(theme, font_css),
            f"graph-{theme_name}.svg": render_graph(data, theme, font_css),
            f"activity-{theme_name}.svg": render_activity(data, theme, font_css),
            f"tile-projects-{theme_name}.svg": render_tile(
                theme,
                font_css,
                "01 / BUILD",
                "Featured Projects",
                "Explainable AI & LLM tools",
                2,
                "+ flagship",
                "accent",
                "accent_soft",
                1.40,
            ),
            f"tile-stack-{theme_name}.svg": render_tile(
                theme,
                font_css,
                "02 / AI & STACK",
                "Tech & Testing",
                "Python, FastAPI, React, Docker",
                20,
                "+ tools",
                "ok",
                "ok_soft",
                1.55,
            ),
            f"tile-connect-{theme_name}.svg": render_tile(
                theme,
                font_css,
                "03 / CONNECT",
                "Experience & Certs",
                "98% NASSCOM AI · 2 internships",
                2,
                "internships",
                "warn",
                "warn_soft",
                1.70,
            ),
            f"repo-loan-{theme_name}.svg": render_repo(
                theme,
                font_css,
                "FEATURED REPO · EXPLAINABLE AI",
                "loan-eligibility-ai",
                "Digital personal loan processing with Explainable Boosting",
                "Machine (EBM), FastAPI, React, Express & Docker Compose.",
                "PYTHON · EBM · FASTAPI · REACT · MYSQL",
                1.95,
            ),
            f"repo-driving-{theme_name}.svg": render_repo(
                theme,
                font_css,
                "FEATURED REPO · LLM PIPELINE",
                "driving-scenario-analyzer",
                "Natural-language driving scenarios to validated JSON via LLM",
                "APIs with NumPy risk scoring, scikit-learn & 33 pytest tests.",
                "PYTHON · LLM APIS · NUMPY · SCIKIT-LEARN · PYTEST",
                2.08,
            ),
        }
        for filename, svg in outputs.items():
            (CARDS_DIR / filename).write_text(svg, encoding="utf-8")

    print(f"Rendered 16 SVG cards into {CARDS_DIR} (STATIC={int(STATIC)})")


if __name__ == "__main__":
    main()
