"""Настройки из переменных окружения (на Railway их задают во вкладке Variables)."""
import hashlib
import os
from datetime import timedelta, timezone

# Токен бота от @BotFather. Без него бот молчит, но API и Mini App работают (удобно для локальной проверки).
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Публичный адрес сервиса, например https://delta-production.up.railway.app (без «/» в конце).
PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

# Файл базы SQLite. На Railway подключите Volume и укажите путь внутри него, например /data/delta.db.
DB_PATH = os.environ.get("DB_PATH", "data/delta.db")

# Необязательный ключ CoinGecko (бесплатный demo-ключ), если без него курсы криптовалют не грузятся.
COINGECKO_KEY = os.environ.get("COINGECKO_KEY", "")

# Включить фоновое обновление курсов (в тестах выключаем).
RATES_REFRESH = os.environ.get("RATES_REFRESH", "1") == "1"

# Секрет, которым Telegram подписывает запросы к нашему webhook. Выводится из токена, задавать не нужно.
WEBHOOK_SECRET = hashlib.sha256(("delta-webhook:" + BOT_TOKEN).encode()).hexdigest()[:48]

# Москва, без перехода на летнее время.
TZ = timezone(timedelta(hours=3))

# Основная валюта.
BASE = "RUB"
