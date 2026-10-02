"""Варианты логотипа/аватарки DELTA: 640×640 PNG каждый + общий лист для выбора.

Запуск: uv run python scripts/build_logos.py ПАПКА_ДЛЯ_РЕЗУЛЬТАТА
Telegram обрезает аватар бота по кругу — всё важное держим в центральном круге.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "logos")
OUT.mkdir(parents=True, exist_ok=True)

STOPS = ('<stop offset="0" stop-color="#5B3CFF"/><stop offset=".38" stop-color="#A24BFF"/>'
         '<stop offset=".7" stop-color="#FF6FB5"/><stop offset="1" stop-color="#FFB27A"/>')
GRAD = f'<linearGradient id="g" x1="0" y1="0" x2="1" y2="1">{STOPS}</linearGradient>'
SHINE = ('<radialGradient id="sh" cx=".82" cy=".12" r=".7"><stop offset="0" stop-color="#fff" stop-opacity=".5"/>'
         '<stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>')
NIGHT = ('<radialGradient id="n" cx=".5" cy=".35" r=".8"><stop offset="0" stop-color="#2A1E66"/>'
         '<stop offset="1" stop-color="#08061A"/></radialGradient>')

VARIANTS = {
    "1-holo": ("Голограмма", "Фирменный перелив и контурная Δ — как в приложении",
               f'<defs>{GRAD}{SHINE}</defs><rect width="640" height="640" fill="url(#g)"/><rect width="640" height="640" fill="url(#sh)"/>'
               '<path d="M320 178 472 452H168z" fill="none" stroke="#fff" stroke-width="44" stroke-linejoin="round"/>'),
    "2-night": ("Ночной кристалл", "Тёмный фон, Δ залита переливом, мягкое свечение",
                f'<defs>{GRAD}{NIGHT}<filter id="bl" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="38"/></filter></defs>'
                '<rect width="640" height="640" fill="url(#n)"/>'
                '<path d="M320 170 480 462H160z" fill="url(#g)" opacity=".75" filter="url(#bl)"/>'
                '<path d="M320 170 480 462H160z" fill="url(#g)" stroke="#fff" stroke-opacity=".35" stroke-width="6" stroke-linejoin="round"/>'
                '<path d="M320 170 400 316 320 462 240 316z" fill="#fff" opacity=".12"/>'),
    "3-chart": ("Растущий график", "Стрелка роста из линии графика: деньги как актив",
                f'<defs>{GRAD}{NIGHT}</defs><rect width="640" height="640" fill="url(#n)"/>'
                '<path d="M150 450 L245 345 L300 392 L420 232" fill="none" stroke="url(#g)" stroke-width="40" stroke-linecap="round" stroke-linejoin="round"/>'
                '<path d="M372 222 L432 222 L432 282" fill="none" stroke="url(#g)" stroke-width="40" stroke-linecap="round" stroke-linejoin="round"/>'
                '<path d="M150 470 H490" stroke="#fff" stroke-opacity=".18" stroke-width="10" stroke-linecap="round"/>'),
    "4-coin": ("Монета", "Голографическая монета с выдавленной Δ",
               f'<defs>{GRAD}{SHINE}{NIGHT}</defs><rect width="640" height="640" fill="url(#n)"/>'
               '<circle cx="320" cy="320" r="220" fill="url(#g)"/><circle cx="320" cy="320" r="220" fill="url(#sh)"/>'
               '<circle cx="320" cy="320" r="182" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="6" stroke-dasharray="3 14" stroke-linecap="round"/>'
               '<path d="M320 214 418 392H222z" fill="#fff" fill-opacity=".92"/><path d="M320 214 418 392H320z" fill="#000" fill-opacity=".12"/>'),
    "5-candles": ("Свечи", "Три биржевые свечи — центральная выше всех, как вершина Δ",
                  f'<defs>{GRAD}{NIGHT}</defs><rect width="640" height="640" fill="url(#n)"/>'
                  '<g fill="url(#g)"><rect x="196" y="330" width="56" height="130" rx="14"/><rect x="292" y="190" width="56" height="270" rx="14"/>'
                  '<rect x="388" y="270" width="56" height="190" rx="14"/></g>'
                  '<g stroke="url(#g)" stroke-width="10" stroke-linecap="round"><path d="M224 300v30M224 460v26M320 160v30M320 460v26M416 240v30M416 460v26"/></g>'),
    "6-mono": ("Минимал", "Белая Δ на чёрном с тонким голографическим кольцом",
               f'<defs>{GRAD}</defs><rect width="640" height="640" fill="#050409"/>'
               '<circle cx="320" cy="320" r="232" fill="none" stroke="url(#g)" stroke-width="10"/>'
               '<path d="M320 196 448 428H192z" fill="none" stroke="#fff" stroke-width="30" stroke-linejoin="round"/>'),
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 640, "height": 640})
    for key, (_, _, svg) in VARIANTS.items():
        pg.set_content(f'<html><body style="margin:0"><svg xmlns="http://www.w3.org/2000/svg" width="640" height="640" viewBox="0 0 640 640">{svg}</svg></body></html>')
        pg.screenshot(path=str(OUT / f"delta-logo-{key}.png"))
    # общий лист: квадрат (иконка iPhone) и круг (аватар Telegram)
    cells = "".join(
        f'<div class="c"><div class="row"><div class="sq"><svg viewBox="0 0 640 640">{svg}</svg></div>'
        f'<div class="ci"><svg viewBox="0 0 640 640">{svg}</svg></div></div>'
        f'<div class="n">{i}. {name}</div><div class="d">{desc}</div></div>'
        for i, (key, (name, desc, svg)) in enumerate(VARIANTS.items(), 1))
    sheet = f"""<html><head><meta charset="utf-8"><style>
      body{{margin:0;width:1500px;background:#0B0920;color:#F4F1FF;font-family:'Inter Display','Inter',sans-serif;padding:56px 60px}}
      h1{{margin:0 0 6px;font-size:40px;letter-spacing:-.02em}} .sub{{color:rgba(244,241,255,.6);font-size:18px;margin-bottom:36px}}
      .grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}}
      .c{{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);border-radius:28px;padding:24px;display:flex;flex-direction:column;gap:10px}}
      .row{{display:flex;gap:18px;align-items:center}} .sq svg{{width:190px;height:190px;border-radius:44px;display:block}}
      .ci svg{{width:120px;height:120px;border-radius:50%;display:block}} .n{{font-size:22px;font-weight:700;margin-top:6px}}
      .d{{font-size:15px;color:rgba(244,241,255,.62);line-height:1.4}}</style></head><body>
      <h1>DELTA — варианты логотипа</h1><div class="sub">Слева — иконка iPhone (скругляет iOS), справа — аватар бота (Telegram обрезает по кругу)</div>
      <div class="grid">{cells}</div></body></html>"""
    pg.set_viewport_size({"width": 1500, "height": 1000})
    pg.set_content(sheet)
    pg.screenshot(path=str(OUT / "delta-logos-sheet.png"), full_page=True)
    b.close()
print("логотипы готовы:", OUT)
