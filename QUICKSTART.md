# Quick Start Guide

## Prerequisites

1. **Claude Code CLI** must be installed and authenticated
   ```bash
   claude --version
   ```

2. **Telegram Bot Token** from [@BotFather](https://t.me/botfather)

## Setup Steps

1. **Install dependencies**:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set:
   - `TELEGRAM_BOT_TOKEN` - Your bot token from BotFather
   - `TELEGRAM_ALLOWED_USERS` - Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))

3. **Run the bot**:
   ```bash
   python main.py
   ```

4. **Test it**:
   - Open Telegram and find your bot
   - Send `/start` to begin
   - Send any message and get a response from Claude!

## Troubleshooting

**"Claude Code CLI not found"**
- Make sure `claude` is in your PATH
- Or set `CLAUDE_CODE_PATH` in `.env` to the full path

**"TELEGRAM_BOT_TOKEN is required"**
- Check that `.env` file exists and has the token
- Make sure there are no extra spaces

**"Unauthorized access"**
- Add your Telegram user ID to `TELEGRAM_ALLOWED_USERS` in `.env`
- Format: `TELEGRAM_ALLOWED_USERS=123456789,987654321`

## What's Working (Phase 1)

✅ Telegram Bot receives messages
✅ Calls Claude Code CLI for responses
✅ Saves conversation history to SQLite
✅ User authorization
✅ Basic commands (/start, /help)

## Next Steps (Future Phases)

- Phase 2: Memory system with context building
- Phase 3: Streaming responses for better UX
- Phase 4: Multi-session management
