"""Обработка сообщений бота. Каждое обновление от Telegram приходит в handle_update()."""
import html
import logging
import uuid

from . import auth, config, services, telegram
from .parser import parse_conversion, parse_entry

log = logging.getLogger("delta.bot")

HELP = (
    "<b>Как пользоваться DELTA</b>\n\n"
    "<b>Расход</b> — сумма и пара слов\n"
    "<code>кофе 350</code>  ·  <code>такси 640 нал</code>  ·  <code>20$ сувенир</code>\n\n"
    "<b>Доход</b> — со знаком плюс\n"
    "<code>+120000 зарплата</code>\n\n"
    "<b>Курс</b> — сумма и валюта\n"
    "<code>100 usd</code>  ·  <code>/rate 5000 руб в евро</code>\n\n"
    "<b>Команды</b>\n"
    "/balance — баланс и траты за месяц\n"
    "/undo — отменить последнюю запись\n"
    "/limit 100000 — лимит трат на месяц\n"
    "/key — запись с iPhone без Telegram\n"
    "/web — открыть DELTA в Safari\n\n"
    "Графики и все записи — в приложении: кнопка <b>DELTA</b> внизу чата."
)

WELCOME = (
    "<b>DELTA</b> — деньги под контролем.\n\n"
    "Записывайте траты одной фразой, смотрите графики как на бирже и пересчитывайте валюты "
    "по курсу ЦБ — в Telegram и прямо с iPhone.\n\n"
    "<b>Попробуйте сейчас</b> — отправьте:\n<code>кофе 350</code>"
)

TOUR = [
    ("slide-1", "<b>Пишите, как другу.</b> Сумма и пара слов — категорию и валюту DELTA поймёт сама."),
    ("slide-2", "<b>Графики как на бирже.</b> Баланс за 30 дней, категории и прогноз до конца месяца."),
    ("slide-3", "<b>Без Telegram.</b> Двойное касание задней крышки iPhone — и трата записана."),
    ("slide-4", "<b>Курсы и конвертер.</b> Доллар, евро, юань — по ЦБ, USDT и биткоин — по бирже."),
]

TOUR_TEXT = (
    "<b>DELTA за 30 секунд</b>\n\n"
    "<b>1 · Запись.</b> Сумма и пара слов — категорию и валюту DELTA поймёт сама.\n"
    "<b>2 · Графики.</b> Баланс, категории и прогноз до конца месяца — в приложении.\n"
    "<b>3 · Без Telegram.</b> Двойное касание крышки iPhone — настройка в /key.\n"
    "<b>4 · Валюты.</b> Траты в долларах, евро и крипте сами пересчитываются в рубли.\n\n"
    "Начните с первой записи: <code>кофе 350</code>"
)

MEDIA_VERSION = "1"  # меняйте, когда перерисовываете картинки в webapp/bot — Telegram кэширует их по ссылке


def _media(name):
    return f"{config.PUBLIC_URL}/static/bot/{name}.jpg?v={MEDIA_VERSION}"


def _app_button():
    if not config.PUBLIC_URL:
        return None
    return [[{"text": "Открыть DELTA", "web_app": {"url": config.PUBLIC_URL + "/"}}]]


def _welcome_keyboard():
    rows = _app_button() or []
    return rows + [[{"text": "Как это работает", "callback_data": "tour"},
                    {"text": "Подсказки", "callback_data": "help"}]]


def _rich(text):
    """Первая строка — жирным: так главное видно сразу, остальное — спокойным текстом."""
    first, _, rest = text.partition("\n")
    out = f"<b>{html.escape(first)}</b>"
    return out + ("\n" + html.escape(rest) if rest else "")


def _welcome(chat_id, user):
    name = html.escape(user["first_name"] or "")
    text = (f"Привет, {name}!\n\n" if name else "") + WELCOME
    if config.PUBLIC_URL:
        if telegram.send_photo(chat_id, _media("welcome"), text, _welcome_keyboard()).get("ok"):
            return
    telegram.send(chat_id, text, _welcome_keyboard())


def _tour(chat_id):
    if config.PUBLIC_URL:
        telegram.send_album(chat_id, [(_media(n), cap) for n, cap in TOUR])
    telegram.send(chat_id, TOUR_TEXT, _app_button())


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
    if cmd == "/start":
        _welcome(chat_id, user)
    elif cmd == "/help":
        telegram.send(chat_id, HELP, _app_button())
    elif cmd == "/balance":
        telegram.send(chat_id, _rich(services.balance_text(user)), _app_button())
    elif cmd == "/undo":
        t = services.undo_last(user["id"])
        if t:
            sign = "−" if t["type"] == "exp" else "+"
            telegram.send(chat_id, f"Отменено: {sign}{services.money(t['amount'], t['currency'])} · "
                                   f"{html.escape(t.get('cat_name') or '')}")
        else:
            telegram.send(chat_id, "Записей пока нет — отменять нечего.")
    elif cmd == "/limit":
        if not arg:
            info = services.limit_info(user)
            if info["limit"]:
                telegram.send(chat_id, f"<b>Лимит на месяц: {services.rubles(info['limit'])}</b>\n"
                                       f"Потрачено: {services.rubles(info['spent'])}\nОсталось: {services.rubles(info['left'])}")
            else:
                telegram.send(chat_id, "Лимит не задан. Пример: <code>/limit 100000</code>")
            return
        p = parse_entry("x " + arg)
        try:
            v = services.set_limit(user["id"], p["amount"] if p else arg)
            telegram.send(chat_id, f"<b>Лимит на месяц: {services.rubles(v)}</b>\nБуду подсказывать остаток после каждой траты."
                          if v else "Лимит выключен.")
        except services.ValidationError as e:
            telegram.send(chat_id, html.escape(str(e)))
    elif cmd == "/rate":
        conv = parse_conversion(arg or "100 usd") or parse_conversion("1 " + arg)
        if not conv:
            telegram.send(chat_id, "Пример: <code>/rate 100 usd</code> или <code>/rate 5000 руб в евро</code>")
            return
        telegram.send(chat_id, _rich(services.conversion_text(*conv)))
    elif cmd == "/key":
        key = services.rotate_key(user["id"]) if arg.lower() == "new" else user["api_key"]
        # Ключ передаётся после «#»: страница подставит его в инструкцию, а на сервер он не уходит.
        guide = f"{config.PUBLIC_URL}/ios#k={key}" if config.PUBLIC_URL else "docs/ios-shortcut.md"
        telegram.send(chat_id,
                      "<b>Ключ для записи с iPhone</b>\n"
                      f"<code>{key}</code>\n\n"
                      f"Пошаговая настройка двойного касания крышки:\n{guide}\n\n"
                      "Никому не показывайте ключ. Если он попал не туда — <code>/key new</code> выдаст новый, "
                      "старый сразу перестанет работать.")
    elif cmd == "/web":
        if not config.PUBLIC_URL:
            telegram.send(chat_id, "Адрес приложения ещё не настроен (переменная PUBLIC_URL).")
            return
        token = auth.new_login_token(user["id"])
        telegram.send(chat_id,
                      "<b>Вход без Telegram</b>\n"
                      f"{config.PUBLIC_URL}/?login={token}\n\n"
                      "Откройте ссылку в Safari → «Поделиться» → «На экран Домой» — появится иконка DELTA.\n"
                      "Ссылка одноразовая и действует 15 минут.")
    elif text.startswith("/"):
        telegram.send(chat_id, "Такой команды нет. /help — все подсказки.")
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
        telegram.send(chat_id, _rich(services.conversion_text(entry["amount"], entry["currency"], "RUB")) +
                      "\n\nЧтобы записать трату, добавьте слово: <code>" + html.escape(text) + " сувенир</code>")
        return
    try:
        t = services.add_transaction(user["id"], entry["type"], entry["amount"], entry["currency"], entry["category"],
                                     account_kind=entry["account_kind"], note=entry["note"], source="bot")
    except services.ValidationError as e:
        telegram.send(chat_id, html.escape(str(e)))
        return
    row = [{"text": "↩ Отменить", "callback_data": f"undo:{t['id']}"}]
    if config.PUBLIC_URL:
        row.append({"text": "Открыть DELTA", "web_app": {"url": config.PUBLIC_URL + "/"}})
    telegram.send(chat_id, _rich(services.recorded_text(user, t)), [row])


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
    elif data in ("tour", "help"):
        telegram.answer_callback(cb["id"])
        chat_id = (cb.get("message") or {}).get("chat", {}).get("id") or frm.get("id")
        if data == "tour":
            _tour(chat_id)
        else:
            telegram.send(chat_id, HELP, _app_button())
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
