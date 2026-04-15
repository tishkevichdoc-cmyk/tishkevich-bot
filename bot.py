import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.error import BadRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_USERNAME = "tishkevichdoc"  # без @
PDF_PATH = "metodichka.pdf"

WELCOME_TEXT = (
    "Привет! 👋\n\n"
    "Я пришлю вам бесплатную методичку\n"
    "📄 *«Анализы при задержке речи: что сдать и зачем?»*\n\n"
    "Это руководство от специалиста в нейрометаболизме Тишкевич Е.А. — "
    "о том, какие исследования помогают найти причину задержки речи у ребёнка.\n\n"
    "Для получения методички, пожалуйста, подпишитесь на канал 👇"
)

SUBSCRIBED_TEXT = (
    "✅ Подписка подтверждена!\n\n"
    "Держите вашу методичку 📄\n\n"
    "Если после изучения захотите разобраться глубже — "
    "вы всегда можете написать мне в Direct 🤍"
)

NOT_SUBSCRIBED_TEXT = (
    "❌ Кажется, вы ещё не подписались на канал.\n\n"
    "Подпишитесь на @tishkevichdoc и нажмите *«Я подписался»* ещё раз."
)


def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME}")],
        [InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=get_keyboard()
    )


async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        is_subscribed = member.status in ("member", "administrator", "creator")
    except BadRequest:
        is_subscribed = False

    if is_subscribed:
        await query.edit_message_text(SUBSCRIBED_TEXT, parse_mode="Markdown")
        with open(PDF_PATH, "rb") as pdf:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=pdf,
                filename="Анализы_при_ЗРР_Тишкевич.pdf",
                caption="📄 *Анализы при задержке речи: что сдать и зачем?*\n\nС пожеланием здоровья, Тишкевич Екатерина 🤍",
                parse_mode="Markdown"
            )
    else:
        await query.edit_message_text(
            NOT_SUBSCRIBED_TEXT,
            parse_mode="Markdown",
            reply_markup=get_keyboard()
        )


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    logger.info("Бот запущен!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
