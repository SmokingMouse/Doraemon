import asyncio
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.error import TimedOut, NetworkError, RetryAfter
from loguru import logger
from config import config
from services.claude_code import ask_claude, _claude_service
from services.user_profile import UserProfileService
from services.memory import MemoryService
from storage.database import Database
from channels.base import User
from core.message_handler import MessageHandler as CoreMessageHandler

db: Database = None
message_handler: CoreMessageHandler = None
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
        "/help  - Show help\n"
        "/new   - Start a new conversation session\n"
        "/clear - Clear current session context\n"
        "/sessions - List your sessions"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me any message and I'll respond using Claude.\n\n"
        "I remember our conversation history within each session.\n\n"
        "Commands:\n"
        "/start - Welcome message\n"
        "/help - Show this help\n"
        "/new - Start a new conversation session\n"
        "/clear - Clear current session context (keeps history but resets Claude's memory)\n"
        "/sessions - List your conversation sessions\n"
        "/switch <number> - Switch to a specific session\n"
        "/stats - Show your usage statistics"
    )


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user statistics."""
    tg_user = update.effective_user

    user = User(
        channel="telegram",
        channel_user_id=str(tg_user.id),
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    stats = await message_handler.get_user_stats(user)

    # Get session info
    session_id, claude_session_id = await message_handler.get_current_session(user)

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


async def new_session_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create a new conversation session."""
    tg_user = update.effective_user

    if not is_allowed(tg_user.id):
        logger.warning(f"Unauthorized access attempt from user {tg_user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    user = User(
        channel="telegram",
        channel_user_id=str(tg_user.id),
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    # Create new session
    session_id, claude_session_id = await message_handler.create_new_session(user)

    logger.info(f"User {tg_user.id} created new session: {claude_session_id}")

    await update.message.reply_text(
        "✨ 新会话已创建！\n\n"
        "现在你可以开始一个全新的对话了。之前的对话历史已保存，"
        "但不会影响新会话。"
    )


async def clear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear current session context."""
    tg_user = update.effective_user

    if not is_allowed(tg_user.id):
        logger.warning(f"Unauthorized access attempt from user {tg_user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    user = User(
        channel="telegram",
        channel_user_id=str(tg_user.id),
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    await message_handler.clear_session_context(user)

    await update.message.reply_text(
        "🧹 上下文已清空！\n\n"
        "当前会话的对话历史已保存，但 Claude 不再记得之前的对话内容。\n"
        "你可以开始一个全新的对话了。"
    )


async def thinking_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle thinking process display."""
    tg_user = update.effective_user

    if not is_allowed(tg_user.id):
        logger.warning(f"Unauthorized access attempt from user {tg_user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    user = User(
        channel="telegram",
        channel_user_id=str(tg_user.id),
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    new_setting = await message_handler.toggle_thinking_display(user)

    if new_setting:
        await update.message.reply_text(
            "💭 思考过程显示已开启\n\n"
            "现在你可以看到 Claude 的思考过程了。"
        )
    else:
        await update.message.reply_text(
            "🤫 思考过程显示已关闭\n\n"
            "现在只显示最终回复，不显示思考过程。"
        )


async def sessions_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List user's conversation sessions."""
    tg_user = update.effective_user

    if not is_allowed(tg_user.id):
        logger.warning(f"Unauthorized access attempt from user {tg_user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    user = User(
        channel="telegram",
        channel_user_id=str(tg_user.id),
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    # Get current session
    current_session_id, _ = await message_handler.get_current_session(user)

    # Get all sessions
    sessions = await message_handler.get_user_sessions(user, limit=10)

    if not sessions:
        await update.message.reply_text("你还没有任何会话。")
        return

    # Format session list
    lines = ["📋 你的会话列表：\n"]
    for idx, session in enumerate(sessions, 1):
        is_current = "✓ " if session["id"] == current_session_id else "  "
        created_at = session["created_at"][:16]  # YYYY-MM-DD HH:MM
        msg_count = session["message_count"]
        lines.append(f"{is_current}{idx}. {created_at} ({msg_count}条消息)")

    lines.append("\n使用 /switch <编号> 切换会话")

    await update.message.reply_text("\n".join(lines))


async def switch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Switch to a specific session."""
    tg_user = update.effective_user

    if not is_allowed(tg_user.id):
        logger.warning(f"Unauthorized access attempt from user {tg_user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    # Parse session number from command
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ 请指定会话编号\n\n"
            "用法: /switch <编号>\n"
            "例如: /switch 2\n\n"
            "使用 /sessions 查看会话列表"
        )
        return

    try:
        session_number = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ 会话编号必须是数字")
        return

    user = User(
        channel="telegram",
        channel_user_id=str(tg_user.id),
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    # Get sessions to find the target session
    sessions = await message_handler.get_user_sessions(user, limit=10)

    if session_number < 1 or session_number > len(sessions):
        await update.message.reply_text(
            f"❌ 会话编号无效。请使用 /sessions 查看可用的会话（1-{len(sessions)}）"
        )
        return

    target_session = sessions[session_number - 1]

    try:
        # Switch to the session
        await message_handler.switch_session(user, target_session["id"])

        logger.info(
            f"User {tg_user.id} switched to session {target_session['id']} "
            f"(claude_session_id: {target_session['claude_session_id']})"
        )

        await update.message.reply_text(
            f"✅ 已切换到会话 {session_number}\n\n"
            f"创建时间: {target_session['created_at'][:16]}\n"
            f"消息数: {target_session['message_count']}"
        )
    except Exception as e:
        logger.error(f"Failed to switch session: {e}")
        await update.message.reply_text("❌ 切换会话失败，请稍后重试。")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_user = update.effective_user

    if not is_allowed(tg_user.id):
        logger.warning(f"Unauthorized access attempt from user {tg_user.id}")
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")
        return

    user = User(
        channel="telegram",
        channel_user_id=str(tg_user.id),
        username=tg_user.username,
        first_name=tg_user.first_name,
    )

    message_text = update.message.text

    # Send typing indicator
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action="typing"
    )

    # 发送初始消息
    reply_message = await update.message.reply_text("💭 思考中...")

    # 流式响应状态
    accumulated_text = ""
    is_streaming = True
    MIN_UPDATE_INTERVAL = 2.0  # 增加到 2 秒，进一步降低速率限制风险
    last_update_time = 0.0

    # 定义降级方案函数（多条消息发送）
    async def send_fallback():
        """发送多条消息（当消息过长时）"""
        try:
            # 分段发送，确保每一段都成功
            total_chunks = (len(accumulated_text) + 4095) // 4096
            for i in range(0, len(accumulated_text), 4096):
                chunk = accumulated_text[i:i+4096]
                chunk_num = i // 4096 + 1

                # 每一段重试 3 次
                for retry in range(3):
                    try:
                        if chunk_num == 1:
                            # 第一段：编辑原消息
                            await reply_message.edit_text(chunk)
                        else:
                            # 后续段：发送新消息
                            await update.message.reply_text(chunk)
                        logger.info(f"Chunk {chunk_num}/{total_chunks} sent successfully")
                        break
                    except Exception as e:
                        if retry < 2:
                            logger.warning(f"Chunk {chunk_num} send failed, retrying ({retry + 1}/3): {e}")
                            await asyncio.sleep(1.0)
                        else:
                            logger.error(f"Chunk {chunk_num} send failed after 3 attempts: {e}")
                # 段与段之间等待，避免速率限制
                if chunk_num < total_chunks:
                    await asyncio.sleep(1.0)
            logger.info(f"All {total_chunks} chunks sent")
        except Exception as e:
            logger.error(f"Fallback function error: {e}")

    async def periodic_update():
        """定期更新消息，持续从 buffer 读取"""
        nonlocal last_update_time
        last_content = ""
        last_update_failed = False

        while is_streaming:
            await asyncio.sleep(MIN_UPDATE_INTERVAL)

            # 如果内容有变化，更新消息
            if accumulated_text != last_content:
                try:
                    # 确保距离上次更新至少 1 秒（Telegram 速率限制）
                    current_time = asyncio.get_event_loop().time()
                    time_since_last = current_time - last_update_time
                    if time_since_last < 1.0:
                        await asyncio.sleep(1.0 - time_since_last)

                    if len(accumulated_text) <= 4096:
                        await asyncio.wait_for(
                            reply_message.edit_text(accumulated_text),
                            timeout=5.0  # 5秒超时
                        )
                    else:
                        truncated = "...\n\n" + accumulated_text[-4000:]
                        await asyncio.wait_for(
                            reply_message.edit_text(truncated + "\n\n⚠️ 消息过长，已截断"),
                            timeout=5.0
                        )
                    last_content = accumulated_text
                    last_update_time = asyncio.get_event_loop().time()
                    last_update_failed = False
                except asyncio.TimeoutError:
                    logger.warning(f"Update message timed out, will retry at end")
                    last_update_failed = True
                except RetryAfter as e:
                    # Telegram 速率限制，等待指定时间
                    wait_time = e.retry_after + 0.5
                    logger.warning(f"Rate limited by Telegram, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                    last_update_failed = True
                except Exception as e:
                    if "message is not modified" not in str(e).lower():
                        logger.debug(f"Failed to update message: {e}")
                        last_update_failed = True

        # 流结束后，最后一次更新确保完整内容
        if accumulated_text != last_content or last_update_failed:
            # 确保距离上次更新至少 1 秒
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - last_update_time
            if time_since_last < 1.0:
                await asyncio.sleep(1.0 - time_since_last)

            # 如果消息超过 4096，直接使用降级方案（多条消息）
            if len(accumulated_text) > 4096:
                logger.info(f"Message too long ({len(accumulated_text)} chars), using multi-message fallback")
                await send_fallback()
                return


            max_retries = 10  # 增加重试次数到 10
            update_success = False

            for attempt in range(max_retries):
                try:
                    if len(accumulated_text) <= 4096:
                        await asyncio.wait_for(
                            reply_message.edit_text(accumulated_text),
                            timeout=10.0
                        )
                    else:
                        truncated = "...\n\n" + accumulated_text[-4000:]
                        await asyncio.wait_for(
                            reply_message.edit_text(truncated + "\n\n⚠️ 消息过长，已截断"),
                            timeout=10.0
                        )
                    update_success = True
                    break  # 成功则退出重试循环
                except asyncio.TimeoutError:
                    logger.warning(f"Final update timed out ({attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1.0)
                except RetryAfter as e:
                    wait_time = e.retry_after + 1.0  # 增加额外等待时间
                    logger.warning(f"Rate limited, waiting {wait_time}s ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                except Exception as e:
                    if "message is not modified" in str(e).lower():
                        # 消息内容相同，但检查是否真的一致
                        if accumulated_text == last_content:
                            # 确实一致，认为成功
                            update_success = True
                            break
                        else:
                            # 不一致但 Telegram 说一致，可能是 bug，继续重试
                            logger.warning(f"Message not modified but content differs, retrying")
                    logger.warning(f"Final update failed ({attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2.0)  # 增加重试等待时间

            # 如果所有重试都失败，使用降级方案
            if not update_success:
                logger.error(f"All {max_retries} update attempts failed, using fallback")
                await send_fallback()

    # 启动定期更新任务
    update_task = asyncio.create_task(periodic_update())

    async def on_chunk(chunk: str):
        nonlocal accumulated_text
        accumulated_text += chunk  # 只负责写入 buffer

    # 使用 MessageHandler 处理消息
    try:
        response = await message_handler.process_message(
            user, message_text, on_chunk=on_chunk
        )

        # 关键修复：确保 accumulated_text 和 response 一致
        # 如果 response 更完整，使用 response
        if len(response) > len(accumulated_text):
            logger.warning(f"Response longer than accumulated_text ({len(response)} vs {len(accumulated_text)}), using response")
            accumulated_text = response

        # 等待足够时间，确保 periodic_update 读取到最后的内容
        await asyncio.sleep(1.5)

        # 标记流结束
        is_streaming = False

        # 等待更新任务完成最后一次更新
        await update_task

        # 验证消息是否完整发送
        # 如果 response 比当前显示的内容长很多，说明可能有问题
        if len(response) > 100:  # 只对长消息检查
            # 这里无法直接获取 Telegram 消息的实际内容，所以依赖日志
            logger.info(f"Message sent, response length: {len(response)}, accumulated length: {len(accumulated_text)}")

        # 如果消息超长，需要分段发送剩余部分
        if len(response) > 4096:
            for i in range(4096, len(response), 4096):
                await update.message.reply_text(response[i : i + 4096])

    except TimedOut:
        logger.error("Telegram send message timed out")
        await reply_message.edit_text(
            "⚠️ 发送响应超时，可能是网络问题。响应已保存，请稍后使用 /history 查看。"
        )
    except NetworkError as e:
        logger.error(f"Telegram network error: {e}")
        await reply_message.edit_text(
            "⚠️ 网络错误，请检查代理设置或稍后重试。"
        )


def create_app(database: Database) -> Application:
    global db, message_handler, user_profile_service
    db = database
    message_handler = CoreMessageHandler(database)
    user_profile_service = UserProfileService(database)

    # Build application with timeout settings
    builder = Application.builder().token(config.TELEGRAM_BOT_TOKEN)

    # Configure timeouts (增加超时时间)
    builder.read_timeout(config.TELEGRAM_READ_TIMEOUT)
    builder.write_timeout(config.TELEGRAM_WRITE_TIMEOUT)
    builder.connect_timeout(30)  # 增加连接超时到 30 秒
    builder.pool_timeout(30)     # 增加连接池超时

    # Configure proxy if provided
    if config.TELEGRAM_PROXY_URL:
        logger.info(f"Using proxy: {config.TELEGRAM_PROXY_URL}")
        builder.proxy(config.TELEGRAM_PROXY_URL)
        builder.get_updates_proxy(config.TELEGRAM_PROXY_URL)

    app = builder.build()

    # Set up bot commands for auto-completion
    async def post_init(application: Application) -> None:
        """Set bot commands after initialization."""
        commands = [
            BotCommand("start", "显示欢迎消息"),
            BotCommand("help", "显示帮助信息"),
            BotCommand("new", "创建新会话"),
            BotCommand("clear", "清空当前会话上下文"),
            BotCommand("thinking", "切换思考过程显示"),
            BotCommand("sessions", "查看会话列表"),
            BotCommand("switch", "切换会话"),
            BotCommand("stats", "查看使用统计"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Bot commands set successfully")

    app.post_init = post_init

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("new", new_session_cmd))
    app.add_handler(CommandHandler("clear", clear_cmd))
    app.add_handler(CommandHandler("thinking", thinking_cmd))
    app.add_handler(CommandHandler("sessions", sessions_cmd))
    app.add_handler(CommandHandler("switch", switch_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    return app
