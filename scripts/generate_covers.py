#!/usr/bin/env python3
"""
Generates a placeholder book-cover SVG for every title in website/server.py's BOOKS
catalog, written to website/static/covers/<id>.svg. Build-time only — the Flask app
just serves the resulting static files, no image generation happens at request time.

Re-run after adding/renaming books:
    python3 scripts/generate_covers.py
"""

from __future__ import annotations

import html
import sys
import textwrap
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "website"))
from server import BOOKS  # noqa: E402

OUT_DIR = ROOT / "website" / "static" / "covers"

WIDTH, HEIGHT = 240, 360

# A broad palette of background/ink/accent combos, assigned per BOOK (not per genre) so
# a genre page — which now holds 20 titles — doesn't render as 20 copies of one color.
# Selection is a deterministic hash of the book id, so it's "random-looking" but stable
# across restarts (no RNG/seed to manage).
PALETTE = [
    {"bg": ("#b5563c", "#7a331f"), "ink": "#fdf3ea", "accent": "#f2c9a3"},  # terracotta
    {"bg": ("#232733", "#0e1016"), "ink": "#f4d488", "accent": "#f4d488"},  # charcoal gold
    {"bg": ("#0f4c5c", "#082b34"), "ink": "#e8fbff", "accent": "#7fe3ff"},  # teal
    {"bg": ("#4c1d95", "#2c0f5c"), "ink": "#f6ecff", "accent": "#c9a6ff"},  # royal purple
    {"bg": ("#92400e", "#5c2a08"), "ink": "#fff3e6", "accent": "#f2b872"},  # amber brown
    {"bg": ("#065f46", "#023d2c"), "ink": "#eafff6", "accent": "#7fe0bd"},  # forest green
    {"bg": ("#9f1239", "#5c0a20"), "ink": "#fff0f4", "accent": "#f6a8c0"},  # crimson
    {"bg": ("#1e3a8a", "#0f1f4d"), "ink": "#eef2ff", "accent": "#93b4ff"},  # indigo
    {"bg": ("#6b21a8", "#3b0f63"), "ink": "#f8ecff", "accent": "#d6a6ff"},  # plum
    {"bg": ("#c2410c", "#7c2d0a"), "ink": "#fff4ec", "accent": "#ffb37a"},  # burnt orange
    {"bg": ("#4d5c1f", "#28300d"), "ink": "#f5f8e8", "accent": "#c3d675"},  # olive
    {"bg": ("#be185d", "#6b0f36"), "ink": "#fff0f6", "accent": "#ffa8cf"},  # rose
    {"bg": ("#155e63", "#0a3033"), "ink": "#e7fbfa", "accent": "#7fd8d1"},  # steel teal
    {"bg": ("#0b1f3a", "#040d1c"), "ink": "#eaf2ff", "accent": "#7fa8e0"},  # midnight navy
    {"bg": ("#92722a", "#5c4712"), "ink": "#fff8e5", "accent": "#e3c25f"},  # mustard
    {"bg": ("#334155", "#111827"), "ink": "#eef2f7", "accent": "#94a8c9"},  # slate
]


def style_for(book: dict) -> dict:
    idx = zlib.crc32(book["id"].encode("utf-8")) % len(PALETTE)
    return PALETTE[idx]

MOTIFS = {
    "Fiction": lambda a: f'<circle cx="{WIDTH-40}" cy="52" r="26" fill="none" stroke="{a}" stroke-width="2" opacity="0.5"/>',
    "Mystery": lambda a: f'<path d="M{WIDTH-70} 30 L{WIDTH-30} 30 L{WIDTH-50} 66 Z" fill="none" stroke="{a}" stroke-width="2" opacity="0.55"/>',
    "Sci-Fi": lambda a: (
        f'<circle cx="{WIDTH-52}" cy="46" r="18" fill="none" stroke="{a}" stroke-width="2" opacity="0.6"/>'
        f'<ellipse cx="{WIDTH-52}" cy="46" rx="30" ry="10" fill="none" stroke="{a}" stroke-width="1.5" opacity="0.45"/>'
    ),
    "Fantasy": lambda a: f'<path d="M{WIDTH-52} 24 L{WIDTH-40} 52 L{WIDTH-64} 52 Z M{WIDTH-52} 24 L{WIDTH-52} 60" fill="none" stroke="{a}" stroke-width="2" opacity="0.55"/>',
    "Non-Fiction": lambda a: f'<rect x="{WIDTH-78}" y="28" width="40" height="30" fill="none" stroke="{a}" stroke-width="2" opacity="0.5"/>',
    "Biography": lambda a: f'<circle cx="{WIDTH-52}" cy="44" r="16" fill="none" stroke="{a}" stroke-width="2" opacity="0.55"/><path d="M{WIDTH-68} 68 Q{WIDTH-52} 52 {WIDTH-36} 68" fill="none" stroke="{a}" stroke-width="2" opacity="0.5"/>',
}


def wrap_lines(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width) or [text]


def title_font_size(title: str) -> int:
    if len(title) <= 14:
        return 24
    if len(title) <= 24:
        return 20
    return 17


def render_cover(book: dict) -> str:
    style = style_for(book)
    bg_top, bg_bottom = style["bg"]
    ink, accent = style["ink"], style["accent"]
    motif = MOTIFS[book["genre"]](accent)

    font_size = title_font_size(book["title"])
    wrap_width = max(10, int(20 * 20 / font_size))
    title_lines = wrap_lines(book["title"], wrap_width)
    line_height = font_size + 6
    title_block_height = line_height * len(title_lines)
    title_start_y = 150 - title_block_height / 2 + font_size

    title_tspans = "".join(
        f'<tspan x="{WIDTH/2}" dy="{0 if i == 0 else line_height}">{html.escape(line)}</tspan>'
        for i, line in enumerate(title_lines)
    )

    gid = f"bg-{book['id']}"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Cover of {html.escape(book['title'])} by {html.escape(book['author'])}">
  <defs>
    <linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{bg_top}"/>
      <stop offset="1" stop-color="{bg_bottom}"/>
    </linearGradient>
  </defs>
  <rect width="{WIDTH}" height="{HEIGHT}" fill="url(#{gid})"/>
  <rect x="6" y="6" width="{WIDTH-12}" height="{HEIGHT-12}" fill="none" stroke="{accent}" stroke-width="1.5" opacity="0.55"/>
  {motif}
  <text x="{WIDTH/2}" y="26" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="10" letter-spacing="2" fill="{accent}" opacity="0.9">{html.escape(book['genre'].upper())}</text>
  <text x="{WIDTH/2}" y="{title_start_y}" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="{font_size}" font-weight="700" fill="{ink}">{title_tspans}</text>
  <text x="{WIDTH/2}" y="{title_start_y + title_block_height + 20}" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-style="italic" font-size="13" fill="{accent}">{html.escape(book['author'])}</text>
  <line x1="{WIDTH/2-30}" y1="{HEIGHT-34}" x2="{WIDTH/2+30}" y2="{HEIGHT-34}" stroke="{accent}" stroke-width="1" opacity="0.6"/>
  <text x="{WIDTH/2}" y="{HEIGHT-16}" text-anchor="middle" font-family="Georgia, 'Times New Roman', serif" font-size="10" letter-spacing="3" fill="{ink}" opacity="0.85">FERNWOOD PRESS</text>
</svg>
'''


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for book in BOOKS:
        svg = render_cover(book)
        (OUT_DIR / f"{book['id']}.svg").write_text(svg, encoding="utf-8")
    print(f"Wrote {len(BOOKS)} covers to {OUT_DIR}")


if __name__ == "__main__":
    main()
