"""HTTP-сервер: Mini App, API, webhook бота. Запуск: uv run uvicorn app.web:app --port 8000"""
import asyncio
import contextlib
import logging
from pathlib import Path

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, PlainTextResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import auth, bot, config, db, rates, services, telegram
from .parser import parse_conversion

log = logging.getLogger("delta.web")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

WEBAPP = Path(__file__).resolve().parent.parent / "webapp"


class HTTPError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def current_user(request: Request):
    """Mini App присылает подпись Telegram, команда iPhone и Safari — личный ключ."""
    init = request.headers.get("x-telegram-init-data")
    if init:
        tg = auth.check_init_data(init, config.BOT_TOKEN)
        if not tg or "id" not in tg:
            raise HTTPError(401, "Подпись Telegram не прошла проверку. Откройте приложение заново.")
        return services.ensure_user(int(tg["id"]), tg.get("first_name", ""))
    authz = request.headers.get("authorization", "")
    key = authz[7:].strip() if authz.lower().startswith("bearer ") else request.query_params.get("key", "")
    user = auth.user_by_key(key)
    if not user:
        raise HTTPError(401, "Нужен вход. Откройте DELTA из Telegram или по ссылке /web из бота.")
    return user


async def body(request):
    try:
        data = await request.json()
    except Exception:
        raise HTTPError(400, "Ожидался JSON")
    if not isinstance(data, dict):
        raise HTTPError(400, "Ожидался объект JSON")
    return data


def api(handler):
    """Обёртка: пользователь, ошибки → JSON."""
    async def endpoint(request: Request):
        try:
            user = await run_in_threadpool(current_user, request)
            result = await handler(request, user)
            return JSONResponse(result)
        except HTTPError as e:
            return JSONResponse({"error": e.message}, status_code=e.status)
        except services.ValidationError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
    return endpoint


# ------------------------------------------------------------------ API для Mini App
async def home(request, user):
    return await run_in_threadpool(services.home, user)


async def stats(request, user):
    return await run_in_threadpool(services.stats, user, request.query_params.get("range", "1m"))


async def rates_list(request, user):
    return {"rates": await run_in_threadpool(services.rates_view)}


async def create_tx(request, user):
    d = await body(request)
    t = await run_in_threadpool(services.add_transaction, user["id"], d.get("type", "exp"), d.get("amount"),
                                d.get("currency", "RUB"), d.get("category"), d.get("account_id"), None,
                                str(d.get("note", ""))[:120], "app")
    return {"transaction": services.tx_view(t), "text": services.recorded_text(user, t)}


async def delete_tx(request, user):
    t = await run_in_threadpool(services.delete_transaction, user["id"], int(request.path_params["tid"]))
    return {"deleted": t["id"]}


async def create_account(request, user):
    d = await body(request)
    a = await run_in_threadpool(services.add_account, user["id"], d.get("name"), d.get("kind", "card"),
                                d.get("currency", "RUB"))
    return {"account": a}


async def update_account(request, user):
    d = await body(request)
    aid = int(request.path_params["aid"])
    if "name" in d:
        await run_in_threadpool(services.rename_account, user["id"], aid, d["name"])
    if "balance" in d:
        await run_in_threadpool(services.set_balance, user["id"], aid, d["balance"])
    return {"ok": True}


async def get_settings(request, user):
    return {"key": user["api_key"], "limit": user["monthly_limit"], "first_name": user["first_name"],
            "ios_url": (config.PUBLIC_URL or "") + "/ios"}


async def update_settings(request, user):
    d = await body(request)
    out = {}
    if "limit" in d:
        out["limit"] = await run_in_threadpool(services.set_limit, user["id"], d["limit"])
    if d.get("rotate_key"):
        out["key"] = await run_in_threadpool(services.rotate_key, user["id"])
    return out


async def convert(request, user):
    q = request.query_params
    try:
        amount = float(q.get("amount", "1").replace(",", "."))
    except ValueError:
        raise HTTPError(400, "Сумма должна быть числом")
    src, dst = q.get("from", "USD").upper(), q.get("to", "RUB").upper()
    try:
        res = await run_in_threadpool(rates.convert, amount, src, dst)
    except rates.RateUnavailable:
        raise HTTPError(503, "Курс пока недоступен")
    return {"amount": amount, "from": src, "to": dst, "result": res}


# ------------------------------------------------------------------ API для команды iPhone (быстрый ввод)
async def quick_add(request, user):
    d = await body(request)
    amount = str(d.get("amount", "")).replace(",", ".").replace(" ", "").replace(" ", "")
    t = await run_in_threadpool(services.add_transaction, user["id"], d.get("type", "exp"), amount,
                                d.get("currency", "RUB"), d.get("category"), None, d.get("account"),
                                str(d.get("note", ""))[:120], "ios")
    return {"text": services.recorded_text(user, t), "id": t["id"]}


async def quick_balance(request, user):
    return {"text": await run_in_threadpool(services.balance_text, user)}


async def quick_rate(request, user):
    q = request.query_params
    conv = parse_conversion(f"{q.get('amount', '100')} {q.get('code', 'usd')}")
    if not conv:
        raise HTTPError(400, "Пример: ?amount=100&code=usd")
    return {"text": await run_in_threadpool(services.conversion_text, *conv)}


# ------------------------------------------------------------------ вход по ссылке и webhook
async def login(request: Request):
    try:
        d = await body(request)
    except HTTPError as e:
        return JSONResponse({"error": e.message}, status_code=e.status)
    user = await run_in_threadpool(auth.use_login_token, d.get("token"))
    if not user:
        return JSONResponse({"error": "Ссылка устарела. Отправьте боту /web ещё раз."}, status_code=401)
    return JSONResponse({"key": user["api_key"]})


async def webhook(request: Request):
    if request.headers.get("x-telegram-bot-api-secret-token") != config.WEBHOOK_SECRET:
        return PlainTextResponse("forbidden", status_code=403)
    update = await request.json()
    await run_in_threadpool(bot.handle_update, update)
    return PlainTextResponse("ok")


async def index(request):
    return FileResponse(WEBAPP / "index.html", headers={"Cache-Control": "no-cache"})


async def ios_page(request):
    return FileResponse(WEBAPP / "ios.html", headers={"Cache-Control": "no-cache"})


async def health(request):
    return PlainTextResponse("ok")


# ------------------------------------------------------------------ запуск
async def _rates_loop():
    while True:
        try:
            await run_in_threadpool(rates.backfill)
            await run_in_threadpool(rates.refresh_today)
        except Exception:
            log.exception("Обновление курсов не удалось")
        await asyncio.sleep(3600)


@contextlib.asynccontextmanager
async def lifespan(app):
    db.connect()
    task = asyncio.create_task(_rates_loop()) if config.RATES_REFRESH else None
    await run_in_threadpool(telegram.setup_webhook)
    yield
    if task:
        task.cancel()


routes = [
    Route("/", index),
    Route("/ios", ios_page),
    Route("/health", health),
    Route("/tg/webhook", webhook, methods=["POST"]),
    Route("/api/login", login, methods=["POST"]),
    Route("/api/home", api(home)),
    Route("/api/stats", api(stats)),
    Route("/api/rates", api(rates_list)),
    Route("/api/convert", api(convert)),
    Route("/api/transactions", api(create_tx), methods=["POST"]),
    Route("/api/transactions/{tid:int}", api(delete_tx), methods=["DELETE"]),
    Route("/api/accounts", api(create_account), methods=["POST"]),
    Route("/api/accounts/{aid:int}", api(update_account), methods=["PATCH"]),
    Route("/api/settings", api(get_settings)),
    Route("/api/settings", api(update_settings), methods=["PATCH"]),
    Route("/api/quick", api(quick_add), methods=["POST"]),
    Route("/api/quick/balance", api(quick_balance)),
    Route("/api/quick/rate", api(quick_rate)),
    Mount("/static", StaticFiles(directory=WEBAPP), name="static"),
]

app = Starlette(routes=routes, lifespan=lifespan, middleware=[Middleware(GZipMiddleware, minimum_size=800)])
