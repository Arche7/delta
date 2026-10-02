"""Демо-данные для локальной проверки (на сервере не запускать).

uv run python scripts/seed_demo.py data/demo.db
Потом: DB_PATH=data/demo.db uv run python scripts/dev_login.py — напечатает одноразовую ссылку входа.
"""
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, db, rates, services  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else "data/demo.db"
Path(path).unlink(missing_ok=True)
db.connect(path)
rnd = random.Random(7)
today = rates.today()
base = {"USD": 81.5, "EUR": 95.2, "CNY": 11.4, "USDT": 81.7, "BTC": 8_950_000, "AED": 22.19}
walk = {k: 1.0 for k in base}
for i in range(40, -1, -1):
    d = today - timedelta(days=i)
    for k, v in base.items():
        walk[k] *= 1 + rnd.gauss(0.0005, 0.02 if k == "BTC" else 0.004)
for i in range(40, -1, -1):
    d = today - timedelta(days=i)
    for k, v in base.items():
        walk[k] /= 1 + rnd.gauss(0.0005, 0.02 if k == "BTC" else 0.004)
        rates.save(k, d, v * walk[k])

u = services.ensure_user(1, "Арсений")
accs = services.accounts(1)
start = datetime.now(config.TZ) - timedelta(days=60)
services.set_balance(1, accs[0]["id"], 0)
db.run("INSERT INTO transactions(user_id, account_id, type, amount, currency, rate, amount_rub, amount_acc, category_id, note,"
       " source, created_at, day) VALUES (1, ?, 'adj', 60000, 'RUB', 1, 60000, 60000, NULL, 'Начальный остаток', 'app', ?, ?)",
       (accs[0]["id"], start.isoformat(), start.date().isoformat()))
db.run("INSERT INTO transactions(user_id, account_id, type, amount, currency, rate, amount_rub, amount_acc, category_id, note,"
       " source, created_at, day) VALUES (1, ?, 'adj', 25000, 'RUB', 1, 25000, 25000, NULL, 'Начальный остаток', 'app', ?, ?)",
       (accs[1]["id"], start.isoformat(), start.date().isoformat()))
db.run("INSERT INTO transactions(user_id, account_id, type, amount, currency, rate, amount_rub, amount_acc, category_id, note,"
       " source, created_at, day) VALUES (1, ?, 'adj', 150, 'USDT', 81, 12150, 150, NULL, 'Начальный остаток', 'app', ?, ?)",
       (accs[2]["id"], start.isoformat(), start.date().isoformat()))

spend = [("food", "кофе", 180, 420), ("food", "продукты", 900, 3200), ("transport", "такси", 300, 900),
         ("transport", "метро", 60, 120), ("shop", "Ozon", 600, 4500), ("fun", "кино", 400, 1200), ("health", "аптека", 200, 1500)]
for i in range(60, -1, -1):
    day = datetime.now(config.TZ) - timedelta(days=i)
    if day.day == 10:
        services.add_transaction(1, "inc", 120000, category="salary", note="Зарплата", when=day.replace(hour=10))
    if day.day == 1:
        services.add_transaction(1, "exp", 30000, category="home", note="Аренда", when=day.replace(hour=9))
    if day.day == 5:
        services.add_transaction(1, "exp", 399, category="subs", note="Яндекс Плюс", when=day.replace(hour=8))
    for _ in range(rnd.randint(1, 4)):
        cat, note, lo, hi = rnd.choice(spend)
        when = day.replace(hour=rnd.randint(8, 22), minute=rnd.randint(0, 59))
        if when > datetime.now(config.TZ):
            continue
        services.add_transaction(1, "exp", round(rnd.uniform(lo, hi), -1), category=cat, note=note, when=when,
                                 account_kind="cash" if rnd.random() < 0.15 else None)
services.add_transaction(1, "exp", 20, "USD", "shop", note="сувенир", when=datetime.now(config.TZ) - timedelta(hours=2))
services.set_limit(1, 110000)
print("Демо-данные готовы:", path)
