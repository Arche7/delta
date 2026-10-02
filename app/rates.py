"""Курсы валют: доллар, евро, юань, дирхам — ЦБ РФ; USDT и биткоин — CoinGecko.

Курс хранится как «сколько рублей стоит 1 единица валюты» на каждый день.
Сеть вызывается только из refresh_*; всё остальное читает базу.
"""
import json
import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta

from . import config, db

log = logging.getLogger("delta.rates")

CBR_CODES = {"USD": "R01235", "EUR": "R01239", "CNY": "R01375", "AED": "R01230"}
CG_IDS = {"USDT": "tether", "BTC": "bitcoin"}
ALL = ["USD", "EUR", "CNY", "USDT", "BTC", "AED"]
NAMES = {"RUB": "Российский рубль", "USD": "Доллар США", "EUR": "Евро", "CNY": "Китайский юань", "USDT": "Tether",
         "BTC": "Bitcoin", "AED": "Дирхам ОАЭ"}
SYMBOLS = {"RUB": "₽", "USD": "$", "EUR": "€", "CNY": "¥", "USDT": "₮", "BTC": "₿", "AED": "AED"}

UA = {"User-Agent": "DELTA-finance-bot/1.0"}


def today():
    return datetime.now(config.TZ).date()


# ------------------------------------------------------------------ разбор ответов (без сети, покрыто тестами)
def _num(text):
    return float(text.replace(" ", "").replace(" ", "").replace(",", "."))


def parse_cbr_daily(xml_bytes):
    """XML_daily.asp → {'USD': 81.5, ...} (рублей за 1 единицу)."""
    root = ET.fromstring(xml_bytes)
    out = {}
    for v in root.findall("Valute"):
        code = v.findtext("CharCode")
        if code in CBR_CODES:
            out[code] = _num(v.findtext("Value")) / _num(v.findtext("Nominal"))
    return out


def parse_cbr_dynamic(xml_bytes):
    """XML_dynamic.asp → [(date, rub_per_unit), ...]."""
    root = ET.fromstring(xml_bytes)
    out = []
    for r in root.findall("Record"):
        d = datetime.strptime(r.get("Date"), "%d.%m.%Y").date()
        out.append((d, _num(r.findtext("Value")) / _num(r.findtext("Nominal"))))
    return out


def parse_cg_simple(json_bytes):
    data = json.loads(json_bytes)
    return {code: float(data[cid]["rub"]) for code, cid in CG_IDS.items() if cid in data and "rub" in data[cid]}


def parse_cg_chart(json_bytes):
    data = json.loads(json_bytes)
    out = {}
    for ms, price in data.get("prices", []):
        d = datetime.fromtimestamp(ms / 1000, config.TZ).date()
        out[d] = float(price)  # последняя цена дня
    return sorted(out.items())


# ------------------------------------------------------------------ сеть
def _get(url, headers=None):
    req = urllib.request.Request(url, headers={**UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def _cg_headers():
    return {"x-cg-demo-api-key": config.COINGECKO_KEY} if config.COINGECKO_KEY else {}


def save(code, day, rub):
    db.run("INSERT INTO rates(code, day, rub) VALUES (?, ?, ?) ON CONFLICT(code, day) DO UPDATE SET rub = excluded.rub",
           (code, day.isoformat(), rub))


def refresh_today():
    d = today()
    try:
        for code, rub in parse_cbr_daily(_get(f"https://www.cbr.ru/scripts/XML_daily.asp?date_req={d:%d/%m/%Y}")).items():
            save(code, d, rub)
    except Exception as e:  # сеть или формат — оставляем вчерашний курс
        log.warning("ЦБ РФ недоступен: %s", e)
    try:
        ids = ",".join(CG_IDS.values())
        for code, rub in parse_cg_simple(_get(f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=rub",
                                              _cg_headers())).items():
            save(code, d, rub)
    except Exception as e:
        log.warning("CoinGecko недоступен: %s", e)


def backfill(days=35):
    """Заполняет историю за ~месяц, если её нет (нужна для графиков)."""
    d2 = today()
    d1 = d2 - timedelta(days=days)
    for code, rid in CBR_CODES.items():
        if count_days(code) >= 20:
            continue
        try:
            url = (f"https://www.cbr.ru/scripts/XML_dynamic.asp?date_req1={d1:%d/%m/%Y}&date_req2={d2:%d/%m/%Y}"
                   f"&VAL_NM_RQ={rid}")
            for d, rub in parse_cbr_dynamic(_get(url)):
                save(code, d, rub)
        except Exception as e:
            log.warning("История ЦБ %s недоступна: %s", code, e)
    for code, cid in CG_IDS.items():
        if count_days(code) >= 20:
            continue
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{cid}/market_chart?vs_currency=rub&days={days}&interval=daily"
            for d, rub in parse_cg_chart(_get(url, _cg_headers())):
                save(code, d, rub)
        except Exception as e:
            log.warning("История CoinGecko %s недоступна: %s", code, e)


def count_days(code):
    r = db.one("SELECT COUNT(*) AS n FROM rates WHERE code = ?", (code,))
    return r["n"] if r else 0


# ------------------------------------------------------------------ чтение
class RateUnavailable(Exception):
    pass


def rate(code, day=None):
    """Рублей за 1 единицу на дату (берётся последний известный курс не позже даты)."""
    if code == "RUB":
        return 1.0
    day = (day or today()).isoformat() if isinstance(day, (date, type(None))) else day
    r = db.one("SELECT rub FROM rates WHERE code = ? AND day <= ? ORDER BY day DESC LIMIT 1", (code, day))
    if not r:
        r = db.one("SELECT rub FROM rates WHERE code = ? ORDER BY day ASC LIMIT 1", (code,))
    if not r:
        raise RateUnavailable(code)
    return r["rub"]


def convert(amount, src, dst, day=None):
    return amount * rate(src, day) / rate(dst, day)


def history(code, days=30):
    """Курс на каждый из последних `days` дней (пропуски заполняются предыдущим значением)."""
    end = today()
    start = end - timedelta(days=days - 1)
    rows = db.query("SELECT day, rub FROM rates WHERE code = ? AND day <= ? ORDER BY day", (code, end.isoformat()))
    if not rows:
        return []
    known = {r["day"]: r["rub"] for r in rows}
    last = None
    for r in rows:
        if r["day"] < start.isoformat():
            last = r["rub"]
    out = []
    for i in range(days):
        d = (start + timedelta(days=i)).isoformat()
        if d in known:
            last = known[d]
        if last is not None:
            out.append((d, last))
    return out
