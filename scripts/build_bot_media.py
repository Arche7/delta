"""Рисует картинки для бота: приветствие и 4 слайда «Как это работает» (1280×720, JPG).

Запуск: uv run python scripts/build_bot_media.py ПАПКА_СО_СКРИНШОТАМИ
В папке должны лежать скриншоты Mini App 390×844 (любой масштаб): promo-home.png, promo-stats.png,
promo-rates.png, promo-add.png — их снимает scripts/promo_shots.py на демо-данных.
Результат: webapp/bot/welcome.jpg, slide-1.jpg … slide-4.jpg (сервер отдаёт их по /static/bot/…).
Шрифт — Inter Display (если его нет, браузер возьмёт системный).
"""
import base64
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
OUT = ROOT / "webapp" / "bot"
OUT.mkdir(parents=True, exist_ok=True)


def img(name):
    return "data:image/png;base64," + base64.b64encode((SRC / name).read_bytes()).decode()


HOLO = "linear-gradient(125deg,#5B3CFF 0%,#A24BFF 38%,#FF6FB5 70%,#FFB27A 100%)"
BASE_CSS = f"""
*{{box-sizing:border-box;margin:0}}
body{{width:1280px;height:720px;overflow:hidden;background:#08061A;color:#F4F1FF;font-family:'Inter Display','Inter',sans-serif;position:relative}}
.b1,.b2,.b3{{position:absolute;border-radius:50%;filter:blur(10px)}}
.b1{{width:760px;height:760px;right:-200px;top:-260px;background:radial-gradient(circle,rgba(124,92,255,.55),transparent 65%)}}
.b2{{width:620px;height:620px;left:-240px;bottom:-300px;background:radial-gradient(circle,rgba(255,111,181,.30),transparent 65%)}}
.b3{{width:420px;height:420px;left:420px;top:-200px;background:radial-gradient(circle,rgba(91,60,255,.25),transparent 65%)}}
.grain{{position:absolute;inset:0;background-image:radial-gradient(rgba(255,255,255,.035) 1px,transparent 1px);background-size:6px 6px}}
.wrap{{position:absolute;inset:0;padding:72px 80px;display:flex;gap:56px;align-items:center}}
.col{{flex:1;display:flex;flex-direction:column;gap:22px;z-index:2}}
.logo{{display:flex;align-items:center;gap:14px;font-weight:800;font-size:22px;letter-spacing:.12em}}
.mark{{width:52px;height:52px;border-radius:16px;background:{HOLO};display:grid;place-items:center;box-shadow:0 12px 30px rgba(162,75,255,.45)}}
.kicker{{font-size:18px;font-weight:600;letter-spacing:.16em;text-transform:uppercase;color:#C6B4FF}}
h1{{font-size:62px;line-height:1.02;font-weight:800;letter-spacing:-.035em}}
h1 em{{font-style:normal;background:{HOLO};-webkit-background-clip:text;background-clip:text;color:transparent}}
p{{font-size:22px;line-height:1.45;color:rgba(244,241,255,.72);max-width:520px}}
.chips{{display:flex;flex-wrap:wrap;gap:10px}}
.chip{{padding:10px 16px;border-radius:999px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);font-size:17px;font-weight:600}}
.phone{{width:290px;height:628px;border-radius:46px;padding:9px;background:linear-gradient(160deg,#3a3352,#14102a);
  box-shadow:0 40px 90px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.12) inset;flex-shrink:0;position:relative}}
.phone img{{width:100%;height:100%;border-radius:38px;object-fit:cover;object-position:top;display:block}}
.phones{{position:relative;width:520px;height:640px;flex-shrink:0;z-index:2}}
.phones .phone{{position:absolute}}
.pg{{position:absolute;left:80px;bottom:54px;font-size:16px;font-weight:700;color:rgba(244,241,255,.5);letter-spacing:.1em;z-index:3}}
"""
DELTA_SVG = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M12 4.5 20 19H4z" fill="none" stroke="#fff" stroke-width="2.6" stroke-linejoin="round"/></svg>'
LOGO = f'<div class="logo"><span class="mark">{DELTA_SVG}</span>DELTA</div>'


def page(inner, extra_css=""):
    return f'<html><head><meta charset="utf-8"><style>{BASE_CSS}{extra_css}</style></head><body>' \
           f'<div class="b1"></div><div class="b2"></div><div class="b3"></div><div class="grain"></div>{inner}</body></html>'


def phone(src, style=""):
    return f'<div class="phone" style="{style}"><img src="{src}"></div>'


SLIDES = {
    "welcome": page(f"""<div class="wrap"><div class="col">{LOGO}
      <h1>Деньги<br>под контролем.<br><em>Красиво.</em></h1>
      <p>Траты одной фразой, графики как на бирже и курсы валют — в Telegram и прямо с iPhone.</p>
      <div class="chips"><span class="chip">кофе 350 → записано</span><span class="chip">графики</span><span class="chip">курсы ЦБ</span><span class="chip">без Telegram</span></div></div>
      <div class="phones">{phone(img('promo-stats.png'), 'left:0;top:40px;transform:rotate(-7deg) scale(.92);opacity:.92')}
      {phone(img('promo-home.png'), 'right:10px;top:0;transform:rotate(4deg)')}</div></div>"""),

    "slide-1": page(f"""<div class="wrap"><div class="col"><span class="kicker">01 · запись</span>
      <h1>Пишите,<br>как <em>другу</em></h1>
      <p>Сумма и пара слов — DELTA сама поймёт категорию и валюту, пересчитает в рубли и покажет остаток лимита.</p></div>
      <div class="chat">
        <div class="me">кофе 350</div>
        <div class="bot"><b>−350 ₽ · Еда</b><span>Лимит: осталось 44 828 ₽ · ≈ 2 800 ₽ в день</span></div>
        <div class="me">20$ сувенир</div>
        <div class="bot"><b>−20 $ · Покупки</b><span>≈ 1 630 ₽ по курсу ЦБ</span></div>
        <div class="me">+120000 зарплата</div>
        <div class="bot"><b>+120 000 ₽ · Зарплата</b><span>Записано на Т-Банк</span></div>
      </div></div><div class="pg">1 / 4</div>""",
      """.chat{width:470px;display:flex;flex-direction:column;gap:14px;z-index:2}
      .me,.bot{padding:16px 20px;border-radius:24px;font-size:21px;max-width:380px;box-shadow:0 14px 34px rgba(0,0,0,.35)}
      .me{align-self:flex-end;background:linear-gradient(125deg,#5B3CFF,#A24BFF);border-bottom-right-radius:8px;font-weight:600}
      .bot{align-self:flex-start;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-bottom-left-radius:8px;
        display:flex;flex-direction:column;gap:4px;backdrop-filter:blur(20px)}
      .bot span{font-size:16px;color:rgba(244,241,255,.66)}"""),

    "slide-2": page(f"""<div class="wrap"><div class="col"><span class="kicker">02 · графики</span>
      <h1>Деньги —<br>как <em>биржевой</em><br>актив</h1>
      <p>Баланс счёта за 30 дней, категории с мини-графиками и процентом к прошлому месяцу, траты по дням и прогноз до конца месяца.</p></div>
      <div class="phones">{phone(img('promo-home.png'), 'left:0;top:18px;transform:rotate(-5deg)')}
      {phone(img('promo-stats.png'), 'right:0;top:0;transform:rotate(5deg)')}</div></div><div class="pg">2 / 4</div>"""),

    "slide-3": page(f"""<div class="wrap"><div class="col"><span class="kicker">03 · без Telegram</span>
      <h1>Тук-тук<br>по <em>крышке</em> —<br>и записано</h1>
      <p>Двойное касание задней крышки iPhone открывает меню DELTA: сумма, категория, готово. Telegram открывать не нужно.</p></div>
      <div class="scene"><div class="back"><div class="cam"><i></i><i></i></div>
        <div class="tap"><span></span><span></span><span></span><b></b></div></div>
        <div class="note"><span class="ic">{DELTA_SVG}</span><div><div class="r"><b>DELTA</b><span>сейчас</span></div>
          <div>Записано −350 ₽ · Еда</div><div class="s">Лимит: осталось 44 828 ₽</div></div></div></div></div><div class="pg">3 / 4</div>""",
      """.scene{position:relative;width:500px;height:600px;z-index:2}
      .back{position:absolute;left:120px;top:20px;width:270px;height:560px;border-radius:52px;background:linear-gradient(160deg,#2f2a44,#15112a);
        box-shadow:0 40px 90px rgba(0,0,0,.6),0 0 0 1px rgba(255,255,255,.12) inset}
      .cam{position:absolute;left:22px;top:22px;width:110px;height:110px;border-radius:30px;background:#1f1a33;border:1px solid rgba(255,255,255,.1)}
      .cam i{position:absolute;width:38px;height:38px;border-radius:50%;background:#0b0918;border:4px solid #3a3352}
      .cam i:first-child{left:12px;top:12px}.cam i:last-child{right:12px;bottom:12px}
      .tap{position:absolute;left:135px;top:300px}
      .tap span{position:absolute;border:3px solid #B49CFF;border-radius:50%;transform:translate(-50%,-50%)}
      .tap span:nth-child(1){width:70px;height:70px;opacity:.9}.tap span:nth-child(2){width:120px;height:120px;opacity:.5}.tap span:nth-child(3){width:170px;height:170px;opacity:.22}
      .tap b{position:absolute;width:26px;height:26px;border-radius:50%;background:#C6B4FF;transform:translate(-50%,-50%);box-shadow:0 0 30px #A24BFF}
      .note{position:absolute;left:0;right:0;bottom:30px;padding:18px 20px;border-radius:26px;background:rgba(60,56,90,.72);backdrop-filter:blur(30px);
        border:1px solid rgba(255,255,255,.14);display:flex;gap:16px;align-items:center;font-size:19px;box-shadow:0 30px 60px rgba(0,0,0,.45)}
      .note .ic{width:52px;height:52px;border-radius:14px;background:linear-gradient(125deg,#5B3CFF,#A24BFF 38%,#FF6FB5 70%,#FFB27A);display:grid;place-items:center;flex-shrink:0}
      .note .r{display:flex;justify-content:space-between;width:340px;font-size:16px}.note .r span,.note .s{color:rgba(244,241,255,.6);font-size:16px}"""),

    "slide-4": page(f"""<div class="wrap"><div class="col"><span class="kicker">04 · валюты</span>
      <h1>Курсы<br>и <em>конвертер</em></h1>
      <p>Доллар, евро и юань — по ЦБ РФ, USDT и биткоин — по бирже. Траты в валюте сами пересчитываются в рубли по курсу дня.</p>
      <div class="chips"><span class="chip">/rate 100 usd</span><span class="chip">20$ сувенир</span></div></div>
      <div class="phones">{phone(img('promo-rates.png'), 'left:40px;top:0;transform:rotate(-4deg)')}
      {phone(img('promo-add.png'), 'right:-20px;top:40px;transform:rotate(6deg) scale(.9);opacity:.95')}</div></div><div class="pg">4 / 4</div>"""),
}

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=1.5)
    for name, html in SLIDES.items():
        pg.set_content(html)
        pg.wait_for_timeout(250)
        pg.screenshot(path=str(OUT / f"{name}.jpg"), type="jpeg", quality=88)
    b.close()
print("готово:", ", ".join(f"webapp/bot/{n}.jpg" for n in SLIDES))
