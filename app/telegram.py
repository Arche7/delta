"""Минимальный клиент Telegram Bot API на стандартной библиотеке (без aiogram)."""
import json
import logging
import urllib.error
import urllib.request

from . import config

log = logging.getLogger("delta.telegram")

# Для тестов: если задан, вместо сети вызовы складываются сюда.
SENT = None


def call(method, **params):
    params = {k: v for k, v in params.items() if v is not None}
    if SENT is not None:
        SENT.append((method, params))
        return {"ok": True, "result": {"message_id": len(SENT)}}
    if not config.BOT_TOKEN:
        log.info("BOT_TOKEN не задан, пропускаю %s", method)
        return {"ok": False}
    data = json.dumps(params).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{config.BOT_TOKEN}/{method}", data=data,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        # Telegram объясняет причину в теле ответа («description») — пишем её в лог Railway.
        try:
            reason = json.loads(e.read()).get("description", "")
        except Exception:
            reason = ""
        log.warning("Telegram %s не выполнен: %s %s", method, e, reason)
        return {"ok": False, "description": reason}
    except Exception as e:
        log.warning("Telegram %s не выполнен: %s", method, e)
        return {"ok": False}


def send(chat_id, text, keyboard=None):
    return call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True,
                reply_markup={"inline_keyboard": keyboard} if keyboard else None)


def edit(chat_id, message_id, text):
    return call("editMessageText", chat_id=chat_id, message_id=message_id, text=text, parse_mode="HTML")


def answer_callback(callback_id, text=None):
    return call("answerCallbackQuery", callback_query_id=callback_id, text=text)


def answer_inline(query_id, results):
    return call("answerInlineQuery", inline_query_id=query_id, results=results, cache_time=60)


def setup_webhook():
    """Регистрирует webhook, команды и кнопку меню «DELTA» (вызывается при старте сервера)."""
    if not (config.BOT_TOKEN and config.PUBLIC_URL):
        log.info("BOT_TOKEN или PUBLIC_URL не заданы — webhook не настраиваю")
        return
    call("setWebhook", url=f"{config.PUBLIC_URL}/tg/webhook", secret_token=config.WEBHOOK_SECRET,
         allowed_updates=["message", "callback_query", "inline_query"], drop_pending_updates=False)
    call("setMyCommands", commands=[
        {"command": "balance", "description": "Баланс и траты за месяц"},
        {"command": "rate", "description": "Курс: /rate 100 usd"},
        {"command": "undo", "description": "Отменить последнюю запись"},
        {"command": "limit", "description": "Лимит трат в месяц: /limit 100000"},
        {"command": "key", "description": "Ключ для команды iPhone"},
        {"command": "web", "description": "Открыть DELTA в Safari без Telegram"},
        {"command": "help", "description": "Как пользоваться"},
    ])
    call("setChatMenuButton", menu_button={"type": "web_app", "text": "DELTA", "web_app": {"url": config.PUBLIC_URL + "/"}})
