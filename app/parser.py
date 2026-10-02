"""Разбор сообщений вида «кофе 350», «+120000 зарплата», «20$ сувенир», «такси 1,5к нал»."""
import re

from .categories import ACCOUNT_WORDS, INCOME_WORDS, keyword_index

CURRENCY_WORDS = {
    "RUB": {"₽", "р", "р.", "руб", "руб.", "рубль", "рубля", "рублей", "rub"},
    "USD": {"$", "usd", "долл", "доллар", "доллара", "долларов", "бакс", "бакса", "баксов"},
    "EUR": {"€", "eur", "евро"},
    "CNY": {"¥", "cny", "юань", "юаня", "юаней", "юани"},
    "USDT": {"₮", "usdt", "тезер", "юсдт"},
    "BTC": {"₿", "btc", "биткоин", "биткоина", "биток"},
    "AED": {"aed", "дирхам", "дирхама", "дирхамов"},
}
SYMBOLS = {"₽": "RUB", "$": "USD", "€": "EUR", "¥": "CNY", "₮": "USDT", "₿": "BTC"}
WORD_TO_CUR = {w: code for code, words in CURRENCY_WORDS.items() for w in words}

# число: 350 | 1 500 | 1500,50 | 1.5к | 120k | 2 млн
NUM_RE = re.compile(
    r"(?<![\w.,])([+\-−]?)\s*([$€¥₽₮₿])?\s*(\d{1,3}(?:[  ]\d{3})+|\d+)(?:[.,](\d+))?\s*(к|k|тыс|тыс\.|млн)?(?![\w])",
    re.IGNORECASE,
)

_KW = keyword_index()


def _to_number(int_part, frac, mult):
    n = float(int_part.replace(" ", "").replace(" ", "") + ("." + frac if frac else ""))
    m = (mult or "").lower()
    if m in ("к", "k", "тыс", "тыс."):
        n *= 1000
    elif m == "млн":
        n *= 1_000_000
    return n


def parse_entry(text):
    """Возвращает dict(type, amount, currency, category, account_kind, note) или None, если суммы нет."""
    if not text:
        return None
    raw = text.strip()
    if raw.startswith("/"):
        return None
    m = NUM_RE.search(raw)
    if not m:
        return None
    sign, sym, int_part, frac, mult = m.groups()
    amount = _to_number(int_part, frac, mult)
    if amount <= 0:
        return None

    rest = (raw[: m.start()] + " " + raw[m.end():]).strip()
    tokens = [t for t in re.split(r"\s+", rest) if t]
    currency = SYMBOLS.get(sym) if sym else None
    words = []
    for t in tokens:
        low = t.lower().strip(",.!;:")
        # символ валюты, прилипший к слову («$сувенир» редко, но «350₽» отрезан регуляркой)
        if low in WORD_TO_CUR and currency is None:
            currency = WORD_TO_CUR[low]
            continue
        if low in WORD_TO_CUR:
            continue
        if low and low[0] in SYMBOLS and currency is None:
            currency = SYMBOLS[low[0]]
            low = low[1:]
            t = t[1:]
            if not low:
                continue
        words.append((t, low))
    currency = currency or "RUB"

    is_income = sign == "+" or any(low in INCOME_WORDS for _, low in words)
    entry_type = "inc" if is_income else "exp"

    account_kind = None
    kept = []
    for t, low in words:
        hit = next((kind for kind, ws in ACCOUNT_WORDS.items() if low in ws), None)
        if hit:
            account_kind = hit
            continue
        kept.append((t, low))

    category = None
    for _, low in kept:
        key = _KW.get(low)
        if key is None:
            # «кофейне», «такси,» — ищем по началу слова
            for kw, k in _KW.items():
                if len(kw) >= 4 and low.startswith(kw[: max(4, len(kw) - 2)]):
                    key = k
                    break
        if key:
            from .categories import DEFAULT_CATEGORIES
            ctype = next(c[3] for c in DEFAULT_CATEGORIES if c[0] == key)
            if ctype == entry_type:
                category = key
                break
    if category is None:
        category = "other_inc" if entry_type == "inc" else "other"

    note = " ".join(t for t, _ in kept).strip(" ,.-")
    return {
        "type": entry_type,
        "amount": round(amount, 8),
        "currency": currency,
        "category": category,
        "account_kind": account_kind,
        "note": note[:120],
    }


def parse_conversion(text):
    """«100 usd», «100$», «5000 руб в евро» → (amount, from, to) или None."""
    if not text:
        return None
    t = text.lower().replace("→", " в ").replace("->", " в ")
    m = NUM_RE.search(t)
    if not m:
        return None
    _sign, sym, int_part, frac, mult = m.groups()
    amount = _to_number(int_part, frac, mult)
    rest = re.split(r"\s+", (t[: m.start()] + " " + t[m.end():]).strip())
    codes = []
    if sym:
        codes.append(SYMBOLS[sym])
    for w in rest:
        w = w.strip(",.!?")
        if w in WORD_TO_CUR:
            codes.append(WORD_TO_CUR[w])
    if not codes:
        return None
    src = codes[0]
    dst = codes[1] if len(codes) > 1 and codes[1] != src else ("RUB" if src != "RUB" else "USD")
    return amount, src, dst
