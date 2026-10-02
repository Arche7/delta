"""Проверка API на запущенном локальном сервере (ключ берётся из базы и не печатается).

DB_PATH=data/demo.db uv run python scripts/smoke_api.py
"""
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import db  # noqa: E402

db.connect()
user_key = db.one("SELECT api_key FROM users WHERE id = 1")["api_key"]
BASE = "http://127.0.0.1:8000"


def call(path, method="GET", data=None, auth=True):
    headers = {"Content-Type": "application/json"}
    if auth:
        headers["Authorization"] = "Bearer " + user_key
    req = urllib.request.Request(BASE + path, method=method, headers=headers,
                                 data=json.dumps(data).encode() if data is not None else None)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


ok = True


def check(name, cond, extra=""):
    global ok
    ok &= bool(cond)
    print(("OK   " if cond else "FAIL ") + name, extra)


s, h = call("/api/home")
check("home", s == 200 and len(h["accounts"]) == 3, f"total={h.get('total')} cats={len(h.get('categories', []))}")
for rng in ("14d", "1m", "3m"):
    s, st = call("/api/stats?range=" + rng)
    check("stats " + rng, s == 200 and st["bars"], f"bars={len(st['bars'])} spent={st['spent']}")
s, r = call("/api/rates")
check("rates", s == 200 and len(r["rates"]) == 6, r["rates"][0]["code"] + "=" + str(round(r["rates"][0]["rate"], 2)))
s, q = call("/api/quick", "POST", {"amount": "500", "type": "exp", "category": "Транспорт"})
check("quick add (iPhone)", s == 200 and "Записано" in q["text"], q.get("text", "").split("\n")[0])
s, q = call("/api/quick/balance")
check("quick balance", s == 200 and "Всего" in q["text"])
s, q = call("/api/quick/rate?amount=100&code=usd")
check("quick rate", s == 200 and "=" in q["text"], q.get("text", "").split("\n")[0])
s, t = call("/api/transactions", "POST", {"type": "exp", "amount": 20, "currency": "USD", "category": "shop"})
check("add USD", s == 200, t.get("text", "").split("\n")[0])
s, d = call(f"/api/transactions/{t['transaction']['id']}", "DELETE")
check("delete", s == 200)
s, e = call("/api/transactions", "POST", {"type": "exp", "amount": -1})
check("bad amount → 400", s == 400, e.get("error"))
s, e = call("/api/home", auth=False)
check("no auth → 401", s == 401)
s, e = call("/api/transactions/999999", "DELETE")
check("foreign/missing tx → 400", s == 400)
req = urllib.request.Request(BASE + "/tg/webhook", method="POST", data=b"{}", headers={"Content-Type": "application/json"})
try:
    urllib.request.urlopen(req)
    check("webhook without secret → 403", False)
except urllib.error.HTTPError as e:
    check("webhook without secret → 403", e.code == 403)
sys.exit(0 if ok else 1)
