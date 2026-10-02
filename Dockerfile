# Образ для Railway: Python 3.12 + uv. Railway сам находит этот файл и собирает по нему.
FROM python:3.12-slim

# uv — менеджер пакетов проекта (официальный образ astral-sh/uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Сначала только зависимости — так пересборка после правки кода быстрее
COPY pyproject.toml uv.lock* ./
RUN uv sync --no-dev --no-install-project

COPY app ./app
COPY webapp ./webapp

ENV PATH="/app/.venv/bin:$PATH"
# Railway передаёт порт в переменной PORT
CMD ["sh", "-c", "uvicorn app.web:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
