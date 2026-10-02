"""Обработка сообщений бота. Каждое обновление от Telegram приходит в handle_update()."""
import html
import logging
import uuid

from . import auth, config, services, telegram
from .parser import parse_conversion, parse_entry

log = logging.getLogger("delta.bot")

HELP = (
    "<b>DELTA</b> — учёт денег без лишних кнопок.\n\n"
    "Просто пишите сюда:\n"
    "• <code>кофе 350</code> — расход\n"
    "• <code>такси 640 нал</code> — расход с наличных\n"
    "• <code>20$ сувенир</code> — расход в долларах, пересчитаю в рубли\n"
    "• <code>+120000 зарплата</code> — доход\n"
    "• <code>100 usd</code> — сколько это в рублях\n\n"
    "Команды: /balance — баланс, /undo — отменить последнюю запись, /limit 100000 — лимит на месяц, "
    "/rate 100 eur — курс, /key — ключ для команды iPhone, /web — открыть без Telegram.\n\n"
    "Графики и все записи — в приложении: кнопка «DELTA» внизу."
)


def _app_button():
    if not config.PUBLIC_URL:
        return None
    return [[{"text": "Открыть DELTA", "web_app": {"url": config.PUBLIC_URL + "/"}}]]


def handle_update(update):
    try:
        if "message" in update:
            _message(update["message"])
        elif "callback_query" in update:
            _callback(update["callback_query"])
        elif "inline_query" in update:
            _inline(update["inline_query"])
    except Exception:
        log.exception("Ошибка обработки обновления")


def _message(msg):
    chat_id = msg["chat"]["id"]
    if msg["chat"].get("type") != "private":
        return
    frm = msg.get("from") or {}
    user = services.ensure_user(frm["id"], frm.get("first_name", ""))
    text = (msg.get("text") or "").strip()
    if not text:
        telegram.send(chat_id, "Пришлите текстом, например: <code>кофе 350</code>")
        return

    cmd, _, arg = text.partition(" ")
    cmd = cmd.split("@")[0].lower()
    arg = arg.strip()
    if cmd in ("/start", "/help"):
        name = html.escape(user["first_name"] or "")
        hello = f"Привет, {name}! " if name else "Привет! "
        telegram.send(chat_id, hello + HELP, _app_button())
    elif cmd == "/balance":
        telegram.send(chat_id, html.escape(services.balance_text(user)), _app_button())
    elif cmd == "/undo":
        t = services.undo_last(user["id"])
        if t:
            sign = "−" if t["type"] == "exp" else "+"
            telegram.send(chat_id, f"Отменил {sign}{services.money(t['amount'], t['currency'])} · "
                                   f"{html.escape(t.get('cat_name') or '')}")
        else:
            telegram.send(chat_id, "Записей пока нет.")
    elif cmd == "/limit":
        if not arg:
            info = services.limit_info(user)
            if info["limit"]:
                telegram.send(chat_id, f"Лимит на месяц: {services.money(info['limit'])}\n"
                                       f"Потрачено: {services.money(info['spent'])}\nОсталось: {services.money(info['left'])}")
            else:
                telegram.send(chat_id, "Лимит не задан. Пример: <code>/limit 100000</code>")
            return
        p = parse_entry("x " + arg)
        try:
            v = services.set_limit(user["id"], p["amount"] if p else arg)
            telegram.send(chat_id, f"Лимит на месяц: {services.money(v)}" if v else "Лимит выключен.")
        except services.ValidationError as e:
            telegram.send(chat_id, html.escape(str(e)))
    elif cmd == "/rate":
        conv = parse_conversion(arg or "100 usd") or parse_conversion("1 " + arg)
        if not conv:
            telegram.send(chat_id, "Пример: <code>/rate 100 usd</code> или <code>/rate 5000 руб в евро</code>")
            return
        telegram.send(chat_id, html.escape(services.conversion_text(*conv)))
    elif cmd == "/key":
        key = services.rotate_key(user["id"]) if arg.lower() == "new" else user["api_key"]
        # Ключ передаётся после «#»: страница подставит его в инструкцию, а на сервер он не уходит.
        guide = f"{config.PUBLIC_URL}/ios#k={key}" if config.PUBLIC_URL else "docs/ios-shortcut.md"
        telegram.send(chat_id,
                      "Ваш ключ для команды iPhone (никому не показывайте):\n"
                      f"<code>{key}</code>\n\nКак настроить двойное касание крышки: {guide}\n"
                      "Если ключ попал не туда — <code>/key new</code> выдаст новый, старый перестанет работать.")
    elif cmd == "/web":
        if not config.PUBLIC_URL:
            telegram.send(chat_id, "Адрес приложения ещё не настроен (переменная PUBLIC_URL).")
            return
        token = auth.new_login_token(user["id"])
        telegram.send(chat_id,
                      "Ссылка для входа без Telegram (действует 15 минут, одноразовая):\n"
                      f"{config.PUBLIC_URL}/?login={token}\n\n"
                      "Откройте её в Safari → «Поделиться» → «На экран Домой». Появится иконка DELTA.")
    elif text.startswith("/"):
        telegram.send(chat_id, "Не знаю такой команды. /help — подсказка.")
    else:
        _record(chat_id, user, text)


def _record(chat_id, user, text):
    entry = parse_entry(text)
    if not entry:
        telegram.send(chat_id, "Не нашёл сумму. Напишите, например: <code>кофе 350</code> или <code>+50000 зарплата</code>")
        return
    # «100 usd» без пояснений — это вопрос про курс, а не трата
    if entry["currency"] != "RUB" and not entry["note"] and entry["category"] in ("other", "other_inc") \
            and not text.strip().startswith("+"):
        telegram.send(chat_id, html.escape(services.conversion_text(entry["amount"], entry["currency"], "RUB")) +
                      "\n\nЧтобы записать трату, добавьте слово: <code>" + html.escape(text) + " сувенир</code>")
        return
    try:
        t = services.add_transaction(user["id"], entry["type"], entry["amount"], entry["currency"], entry["category"],
                                     account_kind=entry["account_kind"], note=entry["note"], source="bot")
    except services.ValidationError as e:
        telegram.send(chat_id, html.escape(str(e)))
        return
    telegram.send(chat_id, html.escape(services.recorded_text(user, t)),
                  [[{"text": "↩ Отменить", "callback_data": f"undo:{t['id']}"}]])


def _callback(cb):
    data = cb.get("data") or ""
    frm = cb.get("from") or {}
    user = services.get_user(frm.get("id"))
    if data.startswith("undo:") and user:
        try:
            t = services.delete_transaction(user["id"], int(data.split(":", 1)[1]))
            telegram.answer_callback(cb["id"], "Отменено")
            m = cb.get("message")
            if m:
                sign = "−" if t["type"] == "exp" else "+"
                telegram.edit(m["chat"]["id"], m["message_id"],
                              f"<s>{sign}{services.money(t['amount'], t['currency'])} · "
                              f"{html.escape(t.get('cat_name') or '')}</s> — отменено")
        except (services.ValidationError, ValueError):
            telegram.answer_callback(cb["id"], "Запись уже удалена")
    else:
        telegram.answer_callback(cb["id"])


def _inline(q):
    conv = parse_conversion(q.get("query", ""))
    if not conv:
        telegram.answer_inline(q["id"], [])
        return
    text = services.conversion_text(*conv)
    title = text.split("\n")[0]
    telegram.answer_inline(q["id"], [{
        "type": "article", "id": uuid.uuid4().hex[:16], "title": title, "description": "DELTA · курс ЦБ РФ / CoinGecko",
        "input_message_content": {"message_text": text},
    }])
