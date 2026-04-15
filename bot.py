import os
import json
import time
import urllib.request

# Токен читаем из переменной окружения
BOT_TOKEN = "8034751650:AAGerLz5KA9OJAFdhAK0lWOgaZGneYthE5M"
CHANNEL = "-1001788043121"
PDF_PATH = "metodichka.pdf"


def tg(method, params=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def send_message(chat_id, text, keyboard=None):
    params = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        params["reply_markup"] = json.dumps(keyboard)
    return tg("sendMessage", params)


def edit_message(chat_id, message_id, text, keyboard=None):
    params = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        params["reply_markup"] = json.dumps(keyboard)
    return tg("editMessageText", params)


def answer_callback(callback_id):
    tg("answerCallbackQuery", {"callback_query_id": callback_id})


def is_subscribed(user_id):
    try:
        r = tg("getChatMember", {"chat_id": CHANNEL, "user_id": user_id})
        return r["result"]["status"] in ("member", "administrator", "creator")
    except:
        return False


def send_pdf(chat_id):
    boundary = "boundary123456"
    with open(PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        f"{chat_id}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n'
        f"С пожеланием здоровья, Тишкевич Екатерина 🤍\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="document"; filename="Анализы_при_ЗРР.pdf"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + pdf_bytes + f"\r\n--{boundary}--\r\n".encode()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())


def keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📢 Подписаться на канал", "url": "https://t.me/tishkevicdoc"}],
            [{"text": "✅ Я подписался", "callback_data": "check"}]
        ]
    }


def handle(update):
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        if "/start" in text:
            send_message(chat_id,
                "Привет! 👋\n\n"
                "Я пришлю вам бесплатную методичку\n"
                "📄 *«Анализы при задержке речи: что сдать и зачем?»*\n\n"
                "Это руководство от специалиста в нейрометаболизме Тишкевич Е.А.\n\n"
                "Для получения подпишитесь на канал 👇",
                keyboard()
            )

    elif "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        msg_id = cb["message"]["message_id"]
        user_id = cb["from"]["id"]
        answer_callback(cb["id"])

        if cb["data"] == "check":
            if is_subscribed(user_id):
                edit_message(chat_id, msg_id,
                    "✅ Подписка подтверждена!\n\n"
                    "Держите вашу методичку 📄\n\n"
                    "Если захотите разобраться глубже — пишите в Direct 🤍"
                )
                send_pdf(chat_id)
            else:
                edit_message(chat_id, msg_id,
                    "❌ Вы ещё не подписались.\n\n"
                    "Подпишитесь на @tishkevicdoc и нажмите *«Я подписался»* ещё раз.",
                    keyboard()
                )


def main():
    print(f"Бот запущен! Токен начинается с: {BOT_TOKEN[:15]}...")
    offset = 0
    while True:
        try:
            r = tg("getUpdates", {"offset": offset, "timeout": 25})
            for update in r.get("result", []):
                offset = update["update_id"] + 1
                try:
                    handle(update)
                except Exception as e:
                    print(f"Ошибка обработки: {e}")
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
