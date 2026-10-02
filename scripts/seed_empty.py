"""Пустой пользователь без записей — проверка первого входа (на сервере не запускать).

uv run python scripts/seed_empty.py data/empty.db  → печатает ключ для входа (#k=…)
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db, rates, services  # noqa: E402

path = sys.argv[1] if len(sys.argv) > 1 else "data/empty.db"
Path(path).unlink(missing_ok=True)
db.connect(path)
base = {"USD": 83.2, "EUR": 97.1, "CNY": 11.7, "USDT": 83.4, "BTC": 9_100_000, "AED": 22.6}
for i in range(35):
    d = rates.today() - timedelta(days=i)
    for k, v in base.items():
        rates.save(k, d, v * (1 + 0.002 * ((i * 7) % 5 - 2)))
u = services.ensure_user(2, "Арсений")
print(u["api_key"])
