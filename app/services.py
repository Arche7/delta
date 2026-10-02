"""Логика приложения: пользователи, счета, записи, итоги, графики. Здесь нет ничего про HTTP и Telegram."""
import calendar
from datetime import datetime, timedelta

from . import auth, config, db, rates
from .categories import DEFAULT_ACCOUNTS, DEFAULT_CATEGORIES

NB = " "
MON_G = ["янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
SUPPORTED = ["RUB"] + rates.ALL


class ValidationError(Exception):
    pass


# ------------------------------------------------------------------ форматирование
def fmt(n, digits=0):
    """1234567.8 → «1 234 568» (неразрывные пробелы, запятая в дробной части)."""
    s = f"{abs(n):,.{digits}f}".replace(",", NB).replace(".", ",")
    if digits == 2:
        if s.endswith(",00"):
            s = s[:-3]
    elif digits:
        s = s.rstrip("0").rstrip(",")
    return ("−" if n < 0 else "") + s


def money(n, currency="RUB"):
    digits = 8 if currency == "BTC" else 2
    return f"{fmt(n, digits)}{NB}{rates.SYMBOLS.get(currency, currency)}"


def rubles(n):
    """Целые рубли для итогов и остатков: «72 146 ₽»."""
    return f"{fmt(round(n))}{NB}₽"


def dlabel(day):
    d = datetime.fromisoformat(day) if isinstance(day, str) else day
    return f"{d.day}{NB}{MON_G[d.month - 1]}"


def now():
    return datetime.now(config.TZ)


# ------------------------------------------------------------------ пользователи
def ensure_user(user_id, first_name=""):
    u = db.one("SELECT * FROM users WHERE id = ?", (user_id,))
    if u:
        if first_name and first_name != u["first_name"]:
            db.run("UPDATE users SET first_name = ? WHERE id = ?", (first_name, user_id))
            u["first_name"] = first_name
        return u
    db.run("INSERT INTO users(id, first_name, api_key, monthly_limit, created_at) VALUES (?, ?, ?, 0, ?)",
           (user_id, first_name or "", auth.new_api_key(), now().isoformat()))
    db.many("INSERT INTO accounts(user_id, name, kind, currency, style, position) VALUES (?, ?, ?, ?, ?, ?)",
            [(user_id, n, k, c, s, i) for i, (n, k, c, s) in enumerate(DEFAULT_ACCOUNTS)])
    db.many("INSERT INTO categories(user_id, key, name, icon, type, color) VALUES (?, ?, ?, ?, ?, ?)",
            [(user_id, k, n, ic, t, col) for k, n, ic, t, col, _w in DEFAULT_CATEGORIES])
    return db.one("SELECT * FROM users WHERE id = ?", (user_id,))


def get_user(user_id):
    return db.one("SELECT * FROM users WHERE id = ?", (user_id,))


def rotate_key(user_id):
    key = auth.new_api_key()
    db.run("UPDATE users SET api_key = ? WHERE id = ?", (key, user_id))
    return key


def set_limit(user_id, value):
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValidationError("Лимит должен быть числом")
    if v < 0 or v > 1e10:
        raise ValidationError("Лимит должен быть от 0 до 10 млрд")
    db.run("UPDATE users SET monthly_limit = ? WHERE id = ?", (v, user_id))
    return v


# ------------------------------------------------------------------ счета и категории
def accounts(user_id):
    return db.query("SELECT * FROM accounts WHERE user_id = ? AND archived = 0 ORDER BY position, id", (user_id,))


def account(user_id, account_id):
    a = db.one("SELECT * FROM accounts WHERE id = ? AND user_id = ? AND archived = 0", (account_id, user_id))
    if not a:
        raise ValidationError("Счёт не найден")
    return a


def add_account(user_id, name, kind="card", currency="RUB"):
    name = (name or "").strip()[:40]
    if not name:
        raise ValidationError("Нужно название счёта")
    if currency not in SUPPORTED:
        raise ValidationError("Неизвестная валюта")
    if kind not in ("card", "cash", "crypto"):
        raise ValidationError("Неизвестный вид счёта")
    style = {"card": "tb", "cash": "cash", "crypto": "usdt"}[kind]
    pos = len(accounts(user_id))
    aid = db.run("INSERT INTO accounts(user_id, name, kind, currency, style, position) VALUES (?, ?, ?, ?, ?, ?)",
                 (user_id, name, kind, currency, style, pos))
    return account(user_id, aid)


def rename_account(user_id, account_id, name):
    account(user_id, account_id)
    name = (name or "").strip()[:40]
    if not name:
        raise ValidationError("Нужно название счёта")
    db.run("UPDATE accounts SET name = ? WHERE id = ?", (name, account_id))


def categories(user_id, ctype=None):
    if ctype:
        return db.query("SELECT * FROM categories WHERE user_id = ? AND type = ? ORDER BY id", (user_id, ctype))
    return db.query("SELECT * FROM categories WHERE user_id = ? ORDER BY id", (user_id,))


def category_by(user_id, key_or_name, ctype):
    """Категория по ключу («food») или названию («Еда», без учёта регистра)."""
    k = (key_or_name or "").strip().lower()
    for c in categories(user_id, ctype):
        if c["key"] == k or c["name"].lower() == k:
            return c
    fallback = "other_inc" if ctype == "inc" else "other"
    return db.one("SELECT * FROM categories WHERE user_id = ? AND key = ?", (user_id, fallback))


# ------------------------------------------------------------------ записи
def add_transaction(user_id, ttype, amount, currency="RUB", category=None, account_id=None, account_kind=None, note="",
                    source="app", when=None):
    if ttype not in ("exp", "inc"):
        raise ValidationError("Тип записи — расход или доход")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise ValidationError("Сумма должна быть числом")
    if not (0 < amount < 1e10):
        raise ValidationError("Сумма должна быть больше нуля")
    currency = (currency or "RUB").upper()
    if currency not in SUPPORTED:
        raise ValidationError("Неизвестная валюта")

    accs = accounts(user_id)
    if not accs:
        raise ValidationError("Нет ни одного счёта")
    if account_id:
        acc = account(user_id, int(account_id))
    elif account_kind:
        acc = next((a for a in accs if a["kind"] == account_kind), accs[0])
    elif currency in ("USDT", "BTC"):
        acc = next((a for a in accs if a["kind"] == "crypto"), accs[0])
    else:
        acc = accs[0]

    when = when or now()
    day = when.date().isoformat()
    try:
        r = rates.rate(currency, day)
        r_acc = rates.rate(acc["currency"], day)
    except rates.RateUnavailable:
        raise ValidationError("Курс этой валюты пока недоступен, попробуйте позже")
    amount_rub = amount * r
    sign = -1 if ttype == "exp" else 1
    amount_acc = sign * (amount if currency == acc["currency"] else amount_rub / r_acc)
    cat = category_by(user_id, category, ttype)
    tid = db.run(
        "INSERT INTO transactions(user_id, account_id, type, amount, currency, rate, amount_rub, amount_acc, category_id, note,"
        " source, created_at, day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, acc["id"], ttype, amount, currency, r, amount_rub, amount_acc, cat["id"] if cat else None,
         (note or "")[:120], source, when.isoformat(), day))
    return transaction(user_id, tid)


def transaction(user_id, tid):
    return db.one(
        "SELECT t.*, c.key AS cat_key, c.name AS cat_name, c.icon AS cat_icon, c.color AS cat_color, a.name AS account_name "
        "FROM transactions t LEFT JOIN categories c ON c.id = t.category_id JOIN accounts a ON a.id = t.account_id "
        "WHERE t.id = ? AND t.user_id = ?", (tid, user_id))


def recent(user_id, limit=30):
    return db.query(
        "SELECT t.*, c.key AS cat_key, c.name AS cat_name, c.icon AS cat_icon, c.color AS cat_color, a.name AS account_name "
        "FROM transactions t LEFT JOIN categories c ON c.id = t.category_id JOIN accounts a ON a.id = t.account_id "
        "WHERE t.user_id = ? ORDER BY t.created_at DESC, t.id DESC LIMIT ?", (user_id, limit))


def delete_transaction(user_id, tid):
    t = transaction(user_id, tid)
    if not t:
        raise ValidationError("Запись не найдена")
    db.run("DELETE FROM transactions WHERE id = ? AND user_id = ?", (tid, user_id))
    return t


def undo_last(user_id):
    t = db.one("SELECT id FROM transactions WHERE user_id = ? AND type != 'adj' ORDER BY created_at DESC, id DESC LIMIT 1",
               (user_id,))
    return delete_transaction(user_id, t["id"]) if t else None


def set_balance(user_id, account_id, target):
    """Корректировка: делает остаток счёта равным target (в валюте счёта). В статистику трат не попадает."""
    acc = account(user_id, int(account_id))
    try:
        target = float(target)
    except (TypeError, ValueError):
        raise ValidationError("Остаток должен быть числом")
    diff = target - balance_native(acc["id"])
    if abs(diff) < 1e-9:
        return None
    day = now().date().isoformat()
    r = rates.rate(acc["currency"], day)
    db.run(
        "INSERT INTO transactions(user_id, account_id, type, amount, currency, rate, amount_rub, amount_acc, category_id, note,"
        " source, created_at, day) VALUES (?, ?, 'adj', ?, ?, ?, ?, ?, NULL, 'Корректировка остатка', 'app', ?, ?)",
        (user_id, acc["id"], abs(diff), acc["currency"], r, abs(diff) * r, diff, now().isoformat(), day))
    return diff


def balance_native(account_id, until_day=None):
    if until_day:
        r = db.one("SELECT COALESCE(SUM(amount_acc), 0) AS s FROM transactions WHERE account_id = ? AND day <= ?",
                   (account_id, until_day))
    else:
        r = db.one("SELECT COALESCE(SUM(amount_acc), 0) AS s FROM transactions WHERE account_id = ?", (account_id,))
    return r["s"]


def to_rub(value, currency, day=None):
    try:
        return value * rates.rate(currency, day)
    except rates.RateUnavailable:
        return 0.0


# ------------------------------------------------------------------ периоды
def month_bounds(d=None):
    d = d or now().date()
    first = d.replace(day=1)
    last = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return first, last


def spent_between(user_id, d1, d2):
    r = db.one("SELECT COALESCE(SUM(amount_rub), 0) AS s FROM transactions WHERE user_id = ? AND type = 'exp' "
               "AND day >= ? AND day <= ?", (user_id, d1.isoformat(), d2.isoformat()))
    return r["s"]


def daily_spend(user_id, d1, d2, category_id=None):
    sql = ("SELECT day, SUM(amount_rub) AS s FROM transactions WHERE user_id = ? AND type = 'exp' AND day >= ? AND day <= ?")
    args = [user_id, d1.isoformat(), d2.isoformat()]
    if category_id:
        sql += " AND category_id = ?"
        args.append(category_id)
    rows = {r["day"]: r["s"] for r in db.query(sql + " GROUP BY day", args)}
    out = []
    d = d1
    while d <= d2:
        out.append((d.isoformat(), rows.get(d.isoformat(), 0.0)))
        d += timedelta(days=1)
    return out


MONTHLY_KEYS = ("home", "subs")  # аренда и подписки бывают раз в месяц — в «обычный день» их не считаем


def typical_day(user_id, days=28):
    """Обычные траты за день: среднее за 4 недели без аренды и подписок (иначе 1-го числа прогноз взлетает)."""
    today = now().date()
    start = today - timedelta(days=days - 1)
    r = db.one("SELECT COALESCE(SUM(t.amount_rub), 0) AS s FROM transactions t LEFT JOIN categories c ON c.id = t.category_id "
               "WHERE t.user_id = ? AND t.type = 'exp' AND t.day >= ? AND t.day <= ? AND COALESCE(c.key, '') NOT IN (?, ?)",
               (user_id, start.isoformat(), today.isoformat(), *MONTHLY_KEYS))
    first_tx = db.one("SELECT MIN(day) AS d FROM transactions WHERE user_id = ? AND type = 'exp'", (user_id,))["d"]
    if not first_tx:
        return 0.0
    span = min(days, (today - datetime.fromisoformat(first_tx).date()).days + 1)
    return r["s"] / max(1, span)


def limit_info(user):
    first, last = month_bounds()
    today = now().date()
    spent = spent_between(user["id"], first, today)
    lim = user["monthly_limit"] or 0
    days_left = (last - today).days + 1
    left = lim - spent if lim else None
    return {"limit": lim, "spent": round(spent, 2), "left": round(left, 2) if left is not None else None,
            "per_day": round(left / days_left, 2) if (left is not None and left > 0) else 0, "days_left": days_left}


# ------------------------------------------------------------------ данные для экранов
def home(user):
    uid = user["id"]
    today = now().date()
    start = today - timedelta(days=29)
    accs = []
    total = 0.0
    for a in accounts(uid):
        bal = balance_native(a["id"])
        bal_rub = to_rub(bal, a["currency"])
        total += bal_rub
        base = balance_native(a["id"], (start - timedelta(days=1)).isoformat())
        moves = {r["day"]: r["s"] for r in db.query(
            "SELECT day, SUM(amount_acc) AS s FROM transactions WHERE account_id = ? AND day >= ? GROUP BY day",
            (a["id"], start.isoformat()))}
        series, labels, running = [], [], base
        for i in range(30):
            d = start + timedelta(days=i)
            running += moves.get(d.isoformat(), 0.0)
            series.append(round(to_rub(running, a["currency"], d.isoformat()), 2))
            labels.append(dlabel(d))
        accs.append({"id": a["id"], "name": a["name"], "kind": a["kind"], "currency": a["currency"], "style": a["style"],
                     "balance": round(bal, 8), "balance_rub": round(bal_rub, 2), "series": series, "labels": labels,
                     "delta": round(series[-1] - series[0], 2)})

    first, _last = month_bounds(today)
    prev_first, _ = month_bounds(first - timedelta(days=1))
    prev_same = prev_first + (today - first)
    cats = []
    for c in categories(uid, "exp"):
        cur = db.one("SELECT COALESCE(SUM(amount_rub),0) AS s FROM transactions WHERE user_id=? AND category_id=? AND type='exp' "
                     "AND day>=? AND day<=?", (uid, c["id"], first.isoformat(), today.isoformat()))["s"]
        if cur <= 0:
            continue
        prev = db.one("SELECT COALESCE(SUM(amount_rub),0) AS s FROM transactions WHERE user_id=? AND category_id=? AND type='exp' "
                      "AND day>=? AND day<=?", (uid, c["id"], prev_first.isoformat(), prev_same.isoformat()))["s"]
        spark = [round(v, 2) for _, v in daily_spend(uid, today - timedelta(days=14), today, c["id"])]
        # накопительный итог читается как «рост актива»
        acc_sum, cum = 0.0, []
        for v in spark:
            acc_sum += v
            cum.append(round(acc_sum, 2))
        cats.append({"key": c["key"], "name": c["name"], "icon": c["icon"], "color": c["color"], "amount": round(cur, 2),
                     "change": round((cur - prev) / prev * 100, 1) if prev > 0 else None, "spark": cum})
    cats.sort(key=lambda x: -x["amount"])

    return {"user": {"first_name": user["first_name"]}, "total": round(total, 2), "accounts": accs, "categories": cats,
            "recent": [tx_view(t) for t in recent(uid, 20)], "limit": limit_info(user),
            "expense_categories": [cat_view(c) for c in categories(uid, "exp")],
            "income_categories": [cat_view(c) for c in categories(uid, "inc")]}


def cat_view(c):
    return {"key": c["key"], "name": c["name"], "icon": c["icon"], "color": c["color"]}


def tx_view(t):
    sign = {"exp": -1, "inc": 1}.get(t["type"], 1 if t["amount_acc"] >= 0 else -1)
    return {"id": t["id"], "type": t["type"], "amount": t["amount"], "currency": t["currency"],
            "amount_rub": round(t["amount_rub"], 2), "sign": sign, "key": t.get("cat_key") or "",
            "category": t.get("cat_name") or "Корректировка",
            "icon": t.get("cat_icon") or "swap", "color": t.get("cat_color") or "#9CA3AF", "note": t["note"],
            "account": t.get("account_name", ""), "day": t["day"], "time": t["created_at"][11:16], "source": t["source"]}


def stats(user, rng="1m"):
    uid = user["id"]
    today = now().date()
    first, last = month_bounds(today)
    bars = []
    if rng == "14d":
        for d, v in daily_spend(uid, today - timedelta(days=13), today):
            bars.append({"label": dlabel(d), "value": round(v, 2), "ghost": False})
    elif rng == "3m":
        start = today - timedelta(days=7 * 13 - 1)
        days = daily_spend(uid, start, today)
        for i in range(0, len(days), 7):
            chunk = days[i:i + 7]
            bars.append({"label": "неделя до " + dlabel(chunk[-1][0]), "value": round(sum(v for _, v in chunk), 2),
                         "ghost": False})
    else:
        rng = "1m"
        days = daily_spend(uid, first, today)
        for d, v in days:
            bars.append({"label": dlabel(d), "value": round(v, 2), "ghost": False})
    real = [b["value"] for b in bars if not b["ghost"]]
    typical = typical_day(uid)
    avg = typical if rng == "1m" else (sum(real) / len(real) if real else 0)
    if rng == "1m":
        d = today + timedelta(days=1)
        while d <= last:
            bars.append({"label": dlabel(d), "value": round(typical, 2), "ghost": True})
            d += timedelta(days=1)

    spent = spent_between(uid, first, today)
    days_left = (last - today).days
    forecast = spent + typical * days_left
    avg_day = typical

    shares = []
    for c in categories(uid, "exp"):
        s = db.one("SELECT COALESCE(SUM(amount_rub),0) AS s FROM transactions WHERE user_id=? AND category_id=? AND type='exp' "
                   "AND day>=? AND day<=?", (uid, c["id"], first.isoformat(), today.isoformat()))["s"]
        if s > 0:
            shares.append({"key": c["key"], "name": c["name"], "color": c["color"], "amount": round(s, 2)})
    shares.sort(key=lambda x: -x["amount"])
    income = db.one("SELECT COALESCE(SUM(amount_rub),0) AS s FROM transactions WHERE user_id=? AND type='inc' AND day>=? AND day<=?",
                    (uid, first.isoformat(), today.isoformat()))["s"]
    return {"range": rng, "bars": bars, "avg": round(avg, 2), "spent": round(spent, 2), "income": round(income, 2),
            "avg_day": round(avg_day, 2), "forecast": round(forecast, 2), "limit": user["monthly_limit"] or 0,
            "shares": shares, "month": first.month}


def rates_view():
    out = []
    for code in rates.ALL:
        hist = rates.history(code, 30)
        if not hist:
            out.append({"code": code, "name": rates.NAMES[code], "symbol": rates.SYMBOLS[code], "rate": None})
            continue
        vals = [v for _, v in hist]
        cur = vals[-1]
        prev = vals[-2] if len(vals) > 1 else cur
        out.append({"code": code, "name": rates.NAMES[code], "symbol": rates.SYMBOLS[code], "rate": cur,
                    "change": round((cur - prev) / prev * 100, 2) if prev else 0,
                    "change30": round((cur - vals[0]) / vals[0] * 100, 2) if vals[0] else 0,
                    "series": [round(v, 6) for v in vals], "labels": [dlabel(d) for d, _ in hist]})
    return out


# ------------------------------------------------------------------ тексты для бота и команды iPhone
def recorded_text(user, t):
    sign = "−" if t["type"] == "exp" else "+"
    amount = money(t["amount"], t["currency"])
    line = f"Записано {sign}{amount} · {t.get('cat_name') or 'Другое'}"
    if t["currency"] != "RUB":
        line += f" (≈{NB}{money(t['amount_rub'])})"
    info = limit_info(get_user(user["id"]))
    if t["type"] == "exp" and info["limit"]:
        if info["left"] >= 0:
            line += f"\nЛимит месяца: осталось {rubles(info['left'])} · ≈{NB}{rubles(info['per_day'])} в день"
        else:
            line += f"\nЛимит месяца превышен на {rubles(-info['left'])}"
    return line


def balance_text(user):
    h = home(user)
    lines = [f"Всего: {rubles(h['total'])}"]
    for a in h["accounts"]:
        if a["currency"] == "RUB":
            lines.append(f"• {a['name']}: {rubles(a['balance'])}")
        else:
            lines.append(f"• {a['name']}: {money(a['balance'], a['currency'])} ≈ {rubles(a['balance_rub'])}")
    info = h["limit"]
    lines.append(f"Потрачено в этом месяце: {rubles(info['spent'])}")
    if info["limit"]:
        lines.append(f"Лимит {rubles(info['limit'])}, осталось {rubles(info['left'])}")
    return "\n".join(lines)


def conversion_text(amount, src, dst):
    try:
        res = rates.convert(amount, src, dst)
    except rates.RateUnavailable:
        return "Курс пока недоступен, попробуйте чуть позже."
    one = rates.convert(1, src, "RUB") if src != "RUB" else rates.convert(1, dst, "RUB")
    base = src if src != "RUB" else dst
    return f"{money(amount, src)} = {money(res, dst)}\nКурс: 1 {base} = {money(one)}"
