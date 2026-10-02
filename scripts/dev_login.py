"""Одноразовая ссылка входа для локальной проверки: DB_PATH=data/demo.db uv run python scripts/dev_login.py [user_id]"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import auth, db  # noqa: E402

db.connect()
uid = int(sys.argv[1]) if len(sys.argv) > 1 else 1
print(f"http://127.0.0.1:8000/?login={auth.new_login_token(uid)}")
