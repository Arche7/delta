"""Кто делает запрос: Mini App (подпись Telegram) или команда iPhone / Safari (личный ключ)."""
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta
from urllib.parse import parse_qsl

from . import config, db

INIT_DATA_MAX_AGE = 24 * 3600  # подпись Telegram действует сутки


def check_init_data(init_data, bot_token, now=None):
    """Проверяет строку Telegram.WebApp.initData. Возвращает данные пользователя или None.

    Алгоритм из документации Telegram Mini Apps: secret = HMAC_SHA256("WebAppData", bot_token),
    hash = HMAC_SHA256(secret, отсортированные пары key=value через \\n без поля hash).
    """
    if not init_data or not bot_token:
        return None
    pairs = dict(parse_qsl(init_data, keep_blank_values=True))
    received = pairs.pop("hash", None)
    if not received:
        return None
    check_string = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calc, received):
        return None
    auth_date = int(pairs.get("auth_date", "0") or 0)
    if (now or time.time()) - auth_date > INIT_DATA_MAX_AGE:
        return None
    try:
        return json.loads(pairs.get("user", "{}"))
    except ValueError:
        return None


def sign_init_data(fields, bot_token):
    """Собирает подписанную initData (нужно для тестов и локальной проверки)."""
    from urllib.parse import urlencode
    check_string = "\n".join(f"{k}={fields[k]}" for k in sorted(fields))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    h = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": h})


def new_api_key():
    return "dk_" + secrets.token_urlsafe(24)


def user_by_key(key):
    if not key or not key.startswith("dk_"):
        return None
    return db.one("SELECT * FROM users WHERE api_key = ?", (key,))


def new_login_token(user_id, minutes=15):
    token = secrets.token_urlsafe(18)
    exp = (datetime.now(config.TZ) + timedelta(minutes=minutes)).isoformat()
    db.run("INSERT INTO login_tokens(token, user_id, expires_at) VALUES (?, ?, ?)", (token, user_id, exp))
    return token


def use_login_token(token):
    """Одноразовая ссылка входа из бота → личный ключ."""
    row = db.one("SELECT * FROM login_tokens WHERE token = ?", (token or "",))
    if not row:
        return None
    db.run("DELETE FROM login_tokens WHERE token = ?", (token,))
    if row["expires_at"] < datetime.now(config.TZ).isoformat():
        return None
    return db.one("SELECT * FROM users WHERE id = ?", (row["user_id"],))
