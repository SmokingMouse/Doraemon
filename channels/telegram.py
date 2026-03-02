from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import TimedOut, NetworkError
from loguru import logger
from config import config
from services.claude_code import ask_claude, _claude_service
from services.user_profile import UserProfileService
from services.memory import MemoryService
from storage.database import Database

db: Database = None
user_profile_service: UserProfileService = None
memory_service: MemoryService = None


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
        "I remember our conversation history within each session.\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/stats - Show your usage statistics"
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics."""
    user = update.effective_user
    user_id = await db.get_or_create_user(user.id, user.username, user.first_name)
    stats = await db.get_user_stats(user_id)

    # Get session info
    session_id, claude_session_id = await db.get_or_create_session(user_id)

    # Get queue size
    queue_size = _claude_service.get_queue_size(claude_session_id)

    stats_text = (
        f"📊 你的统计信息\n\n"
        f"💬 消息数: {stats['message_count']}\n"
        f"🔄 会话数: {stats['session_count']}\n"
        f"📅 首次使用: {stats['first_seen']}\n"
        f"⏰ 最后活跃: {stats['last_active']}\n\n"
        f"📋 当前队列: {queue_size} 条消息等待处理"
    )

    await update.message.reply_text(stats_text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_allowed(user.id):
        logger.warning(f"Unauthorized access attempt from user {user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    user_id = await db.get_or_create_user(user.id, user.username, user.first_name)
    session_id, claude_session_id = await db.get_or_create_session(user_id)

    message_text = update.message.text
    await db.save_message(session_id, "user", message_text)

    logger.info(f"User {user.id} ({user.first_name}): {message_text[:50]}...")

    # Send typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # Call Claude Code with session ID for context persistence
    result = await ask_claude(message_text, session_id=claude_session_id)

    # 检查是否返回了新的 session id
    if isinstance(result, tuple):
        response, new_claude_session_id = result
        # 更新数据库中的 claude_session_id
        await db.update_session_claude_id(session_id, new_claude_session_id)
        logger.info(f"Updated claude_session_id to: {new_claude_session_id}")
    else:
        response = result

    await db.save_message(session_id, "assistant", response)

    # Send response with error handling
    try:
        # Split long messages (Telegram limit is 4096 chars)
        if len(response) > 4096:
            for i in range(0, len(response), 4096):
                await update.message.reply_text(response[i : i + 4096])
        else:
            await update.message.reply_text(response)
    except TimedOut:
        logger.error("Telegram send message timed out")
        await update.message.reply_text(
            "⚠️ 发送响应超时，可能是网络问题。响应已保存，请稍后使用 /history 查看。"
        )
    except NetworkError as e:
        logger.error(f"Telegram network error: {e}")
        await update.message.reply_text(
            "⚠️ 网络错误，请检查代理设置或稍后重试。"
        )


def create_app(database: Database) -> Application:
    global db, user_profile_service
    db = database
    user_profile_service = UserProfileService(database)

    # Build application with timeout settings
    builder = Application.builder().token(config.TELEGRAM_BOT_TOKEN)

    # Configure timeouts
    builder.read_timeout(config.TELEGRAM_READ_TIMEOUT)
    builder.write_timeout(config.TELEGRAM_WRITE_TIMEOUT)
    builder.connect_timeout(config.TELEGRAM_CONNECT_TIMEOUT)

    # Configure proxy if provided
    if config.TELEGRAM_PROXY_URL:
        logger.info(f"Using proxy: {config.TELEGRAM_PROXY_URL}")
        builder.proxy_url(config.TELEGRAM_PROXY_URL)

    app = builder.build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
