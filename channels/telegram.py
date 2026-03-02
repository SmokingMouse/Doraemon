from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from loguru import logger
from config import config
from services.claude_code import ask_claude
from storage.database import Database

db: Database = None


def is_allowed(user_id: int) -> bool:
    if not config.TELEGRAM_ALLOWED_USERS:
        return True
    return user_id in config.TELEGRAM_ALLOWED_USERS


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I'm Doraemon, your personal AI assistant.\n"
        "Just send me a message and I'll help you out!\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/help  - Show help"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me any message and I'll respond using Claude.\n\n"
        "I save our conversation history so you can refer back to it."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_allowed(user.id):
        logger.warning(f"Unauthorized access attempt from user {user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    user_id = await db.get_or_create_user(user.id, user.username, user.first_name)
    session_id = await db.get_or_create_session(user_id)

    message_text = update.message.text
    await db.save_message(session_id, "user", message_text)

    logger.info(f"User {user.id} ({user.first_name}): {message_text[:50]}...")

    response = await ask_claude(message_text)
    await db.save_message(session_id, "assistant", response)

    # Split long messages (Telegram limit is 4096 chars)
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await update.message.reply_text(response[i : i + 4096])
    else:
        await update.message.reply_text(response)


def create_app(database: Database) -> Application:
    global db
    db = database

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
