import os
import json
import time
import urllib.request
import urllib.parse

TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL = "tishkevichdoc"
PDF_PATH = "metodichka.pdf"
API = f"https://api.telegram.org/bot{TOKEN}"

def api_call(method, data=None, files=None):
    url = f"{API}/{method}"
    if files:
        import urllib.request
        boundary = "----boundary"
        body = b""
        for key, val in (data or {}).items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{val}\r\n".encode()
        for key, (filename, content, ctype) in files.items():
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\nContent-Type: {ctype}\r\n\r\n".encode()
            body += content + b"\r\n"
        body += f"--{boundary}--\r\n".encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    else:
        body = json.dumps(data or {}).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"API error {method}: {e}")
        return {}

def send_message(chat_id, text, keyboard=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        data["reply_markup"] = json.dumps(keyboard)
    api_call("sendMessage", data)

def send_pdf(chat_id):
    with open(PDF_PATH, "rb") as f:
        content = f.read()
    caption = "📄 *Анализы при задержке речи: что сдать и зачем?*\n\nС пожеланием здоровья, Тишкевич Екатерина 🤍"
    api_call("sendDocument", {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
             files={"document": ("Анализы_при_ЗРР.pdf", content, "application/pdf")})

def check_subscribed(user_id):
    r = api_call("getChatMember", {"chat_id": f"@{CHANNEL}", "user_id": user_id})
    status = r.get("result", {}).get("status", "")
    return status in ("member", "administrator", "creator")

def get_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📢 Подписаться на канал", "url": f"https://t.me/{CHANNEL}"}],
            [{"text": "✅ Я подписался", "callback_data": "check"}]
        ]
    }

def handle_update(update):
    # Команда /start
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")
        if text.startswith("/start"):
            welcome = (
                "Привет! 👋\n\n"
                "Я пришлю вам бесплатную методичку\n"
                "📄 *«Анализы при задержке речи: что сдать и зачем?»*\n\n"
                "Это руководство от специалиста в нейрометаболизме Тишкевич Е.А.\n\n"
                "Для получения методички подпишитесь на канал 👇"
            )
            send_message(chat_id, welcome, get_keyboard())

    # Нажатие кнопки
    elif "callback_query" in update:
        cb = update["callback_query"]
        chat_id = cb["message"]["chat"]["id"]
        user_id = cb["from"]["id"]
        msg_id = cb["message"]["message_id"]

        # Ответить на callback
        api_call("answerCallbackQuery", {"callback_query_id": cb["id"]})

        if cb["data"] == "check":
            if check_subscribed(user_id):
                api_call("editMessageText", {
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": "✅ Подписка подтверждена!\n\nДержите вашу методичку 📄\n\nЕсли захотите разобраться глубже — пишите в Direct 🤍",
                    "parse_mode": "Markdown"
                })
                send_pdf(chat_id)
            else:
                api_call("editMessageText", {
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": "❌ Вы ещё не подписались.\n\nПодпишитесь на @tishkevichdoc и нажмите *«Я подписался»* ещё раз.",
                    "parse_mode": "Markdown",
                    "reply_markup": json.dumps(get_keyboard())
                })

def main():
    print("Бот запущен!")
    offset = 0
    while True:
        try:
            r = api_call("getUpdates", {"offset": offset, "timeout": 30})
            updates = r.get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                handle_update(update)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
