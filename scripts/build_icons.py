"""Рисует PNG-иконки для экрана «Домой» iPhone из того же рисунка, что webapp/icon.svg.

Запуск (нужен Playwright с Chromium): uv run python scripts/build_icons.py
iOS сам скругляет углы, поэтому PNG — квадрат без скругления.
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180" width="{s}" height="{s}">'
       '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5B3CFF"/>'
       '<stop offset=".38" stop-color="#A24BFF"/><stop offset=".7" stop-color="#FF6FB5"/><stop offset="1" stop-color="#FFB27A"/>'
       '</linearGradient><radialGradient id="h" cx=".85" cy=".1" r=".6"><stop offset="0" stop-color="#fff" stop-opacity=".45"/>'
       '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>'
       '<rect width="180" height="180" fill="url(#g)"/><rect width="180" height="180" fill="url(#h)"/>'
       '<path d="M90 44 136 132H44z" fill="none" stroke="#fff" stroke-width="13" stroke-linejoin="round"/></svg>')

with sync_playwright() as p:
    b = p.chromium.launch()
    for size in (180, 512):
        pg = b.new_page(viewport={"width": size, "height": size})
        pg.set_content(f'<html><body style="margin:0">{SVG.format(s=size)}</body></html>')
        pg.screenshot(path=str(ROOT / "webapp" / f"icon-{size}.png"))
        pg.close()
    b.close()
print("webapp/icon-180.png и webapp/icon-512.png готовы")
