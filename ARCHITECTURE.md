# kvant — Architecture

> High-level technical truth. Names used here are the names used everywhere else — do not
> invent parallel vocabulary. Update in the same change as the thing it describes.

## Overview
Один сервер на Python (Starlette + uvicorn) отдаёт API, принимает обновления бота через webhook и раздаёт интерфейс Mini App. Все данные — в одном файле SQLite на постоянном диске (Volume) Railway. В систему ведут три входа: Mini App в Telegram (и та же страница в Safari), бот и команда iOS, которая отправляет запись прямо в API.

```
 Mini App (Telegram / Safari) ─┐
 Бот Telegram (webhook) ───────┼──► Сервер app/web.py (Starlette) ──► SQLite (/data/delta.db на Volume)
 Команда iOS (касание крышки) ─┘            │
                                            └──► Курсы: ЦБ РФ (фиат) + CoinGecko (USDT, BTC)
```

## Components and repositories
| Component | Responsibility | Tech | Owner |
| --- | --- | --- | --- |
| Сервер API (`app/web.py`, `app/services.py`) | Записи, счета, категории, лимит, итоги, графики, курсы, вход по подписи Telegram и по личному ключу | Python 3.12, Starlette, uvicorn | Арсений Чертищев |
| Бот (`app/bot.py`, `app/telegram.py`) | Запись траты текстом, конвертер, баланс, лимит, ключ для iPhone, вход в Safari, кнопка Mini App | Telegram Bot API напрямую, webhook | Арсений Чертищев |
| Mini App (`webapp/`) | Главная, Аналитика, Новая запись, Курсы, Ещё; тёмная и светлая тема; стиль «Голограмма» | HTML/CSS/JS без сборки | Арсений Чертищев |
| Команда iOS (`docs/ios-shortcut.md`, `/ios`) | Быстрый ввод без Telegram по двойному касанию крышки | Приложение «Команды» iOS | Арсений Чертищев |

## Data flow
Пользователь создаёт запись в любом из трёх входов → сервер проверяет пользователя (подпись Telegram для Mini App, личный ключ `dk_…` для команды iOS и Safari) → берёт курс дня из таблицы `rates` и пересчитывает сумму в рубли → сохраняет запись с суммой, валютой, курсом и суммой в рублях → Mini App получает итоги и графики через `/api/home` и `/api/stats`. Бот получает сообщения от Telegram на `/tg/webhook` (проверка секретного заголовка).

## Tech stack and tools
Python 3.12, Starlette, uvicorn, стандартная библиотека (sqlite3, urllib). Курсы: XML ЦБ РФ (`XML_daily.asp`, `XML_dynamic.asp`) и CoinGecko (`simple/price`, `coins/{id}/market_chart`), обновление раз в час в фоне.

Отступление от исходного выбора (FastAPI + aiogram + PostgreSQL): в рабочей среде, где пишется и проверяется код, закрыт доступ к каталогу пакетов PyPI, поэтому взяты только библиотеки, которые можно проверить тестами (Starlette — основа FastAPI). Решение и путь перехода — `DECISIONS/ADR-0001-stack-without-pypi.md`.

## Deployment and environments
Railway: один сервис, собирается по `Dockerfile` (Python 3.12 + uv), Volume смонтирован в `/data`. Переменные: `BOT_TOKEN`, `PUBLIC_URL`, `DB_PATH=/data/delta.db`, необязательно `COINGECKO_KEY`. При старте сервер сам регистрирует webhook, команды и кнопку меню бота. Одно окружение и один бот. Откат — повторный деплой предыдущей версии в Railway; база на Volume при этом сохраняется.

## Boundaries and contracts
Граница — HTTP API сервера: `/api/*` (Mini App и Safari), `/api/quick*` (команда iOS, ответ всегда содержит поле `text` для уведомления), `/tg/webhook` (Telegram). Описание — `specs/mvp/spec.md` и `docs/ios-shortcut.md`.

## Cross-cutting concerns
- Секреты (токен бота) — только в переменных окружения Railway, не в коде и не в git (`.gitignore` исключает `.env`).
- Вход в Mini App — по подписи Telegram (`initData`, HMAC); Safari и команда iOS — по личному ключу, который можно сменить `/key new`; вход в Safari — одноразовая ссылка на 15 минут.
- Webhook проверяет секретный заголовок, выведенный из токена.
- Анимации отключаются при системной настройке «Уменьшение движения».

## Local development
- Тесты: `uv run python -m unittest discover -s tests -v`
- Демо-данные: `uv run python scripts/seed_demo.py data/demo.db`
- Сервер: `DB_PATH=data/demo.db RATES_REFRESH=0 uv run uvicorn app.web:app --port 8000`
- Ссылка входа для браузера: `DB_PATH=data/demo.db uv run python scripts/dev_login.py`
- Пересобрать страницу инструкции iPhone после правки `docs/ios-shortcut.md`: `uv run python scripts/build_ios_page.py`
