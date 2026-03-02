# Doraemon - Personal AI Assistant

A personal AI assistant powered by Claude Code CLI with Telegram interface.

## Features

- 🤖 Telegram Bot interface
- 💬 Conversation history persistence with Claude Code sessions
- 🧠 Memory system - remembers context across messages
- 📊 User statistics and profile tracking
- 🔐 User authorization
- 📊 SQLite database for data storage

## Setup

1. **Install dependencies**:
```bash
uv pip install -e .
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env and set your TELEGRAM_BOT_TOKEN
```

3. **Get Telegram Bot Token**:
   - Talk to [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Copy the token to `.env`

4. **Set allowed users** (optional):
   - Get your Telegram user ID (use [@userinfobot](https://t.me/userinfobot))
   - Add it to `TELEGRAM_ALLOWED_USERS` in `.env`

## Usage

Start the bot:
```bash
python main.py
```

Then message your bot on Telegram!

## Commands

- `/start` - Welcome message
- `/help` - Show help
- `/stats` - Show your usage statistics

## Requirements

- Python 3.10+
- Claude Code CLI installed and authenticated
- Telegram Bot Token

## Architecture

```
Telegram Bot → Claude Code CLI → SQLite Database
```

Phase 1 (MVP) - ✅ Complete:
- Basic Telegram → Claude Code integration
- Conversation history saved to SQLite
- User authorization

Phase 2 (Memory System) - ✅ Complete:
- Claude Code session management for context persistence
- User profile and statistics tracking
- Memory service for conversation context
- /stats command

Future phases:
- Phase 3: Streaming responses
- Phase 4: Multi-session management
