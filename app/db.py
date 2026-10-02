"""База данных SQLite: одна таблица на каждую сущность, без сторонних библиотек."""
import os
import sqlite3
import threading

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,          -- id пользователя в Telegram
    first_name    TEXT NOT NULL DEFAULT '',
    api_key       TEXT NOT NULL UNIQUE,         -- личный ключ для команды iPhone и входа из Safari
    monthly_limit REAL NOT NULL DEFAULT 0,      -- лимит трат в месяц, ₽ (0 — без лимита)
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS accounts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    name      TEXT NOT NULL,
    kind      TEXT NOT NULL,                    -- card | cash | crypto
    currency  TEXT NOT NULL,                    -- валюта счёта
    style     TEXT NOT NULL,                    -- цвет голографической карты: tb | cash | usdt
    position  INTEGER NOT NULL DEFAULT 0,
    archived  INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS categories (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id  INTEGER NOT NULL REFERENCES users(id),
    key      TEXT NOT NULL,
    name     TEXT NOT NULL,
    icon     TEXT NOT NULL,
    type     TEXT NOT NULL,                     -- exp | inc
    color    TEXT NOT NULL,
    UNIQUE (user_id, key)
);
CREATE TABLE IF NOT EXISTS transactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    account_id  INTEGER NOT NULL REFERENCES accounts(id),
    type        TEXT NOT NULL,                  -- exp | inc | adj (корректировка остатка)
    amount      REAL NOT NULL,                  -- сумма в валюте записи, всегда положительная
    currency    TEXT NOT NULL,
    rate        REAL NOT NULL,                  -- курс валюты записи к рублю на момент записи
    amount_rub  REAL NOT NULL,                  -- сумма в рублях по курсу на момент записи
    amount_acc  REAL NOT NULL,                  -- сумма в валюте счёта (со знаком)
    category_id INTEGER REFERENCES categories(id),
    note        TEXT NOT NULL DEFAULT '',
    source      TEXT NOT NULL DEFAULT 'app',    -- bot | app | ios
    created_at  TEXT NOT NULL,                  -- ISO-время по Москве
    day         TEXT NOT NULL                   -- дата YYYY-MM-DD по Москве
);
CREATE INDEX IF NOT EXISTS tx_user_day ON transactions(user_id, day);
CREATE TABLE IF NOT EXISTS rates (
    code TEXT NOT NULL,
    day  TEXT NOT NULL,
    rub  REAL NOT NULL,                          -- сколько рублей стоит 1 единица валюты
    PRIMARY KEY (code, day)
);
CREATE TABLE IF NOT EXISTS login_tokens (
    token      TEXT PRIMARY KEY,
    user_id    INTEGER NOT NULL,
    expires_at TEXT NOT NULL
);
"""

_lock = threading.RLock()
_conn = None


def connect(path=None):
    """Открывает (или пересоздаёт для тестов) соединение и создаёт таблицы."""
    global _conn
    if _conn is not None:
        _conn.close()
    path = path or config.DB_PATH
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)
    _conn = conn
    return conn


def conn():
    return _conn or connect()


def query(sql, args=()):
    with _lock:
        return [dict(r) for r in conn().execute(sql, args).fetchall()]


def one(sql, args=()):
    with _lock:
        r = conn().execute(sql, args).fetchone()
        return dict(r) if r else None


def run(sql, args=()):
    """Выполняет запись и возвращает id новой строки."""
    with _lock:
        cur = conn().execute(sql, args)
        return cur.lastrowid


def many(sql, rows):
    with _lock:
        c = conn()
        c.execute("BEGIN")
        try:
            c.executemany(sql, rows)
            c.execute("COMMIT")
        except Exception:
            c.execute("ROLLBACK")
            raise
