import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ALLOWED_USERS: list[int] = [
        int(uid.strip())
        for uid in os.getenv("TELEGRAM_ALLOWED_USERS", "").split(",")
        if uid.strip()
    ]

    # Proxy settings (for users in China or behind firewall)
    TELEGRAM_PROXY_URL: str = os.getenv("TELEGRAM_PROXY_URL", "")

    CLAUDE_CODE_PATH: str = os.getenv("CLAUDE_CODE_PATH", "claude")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "./data/doraemon.db")

    # Timeout settings
    TELEGRAM_READ_TIMEOUT: int = int(os.getenv("TELEGRAM_READ_TIMEOUT", "30"))
    TELEGRAM_WRITE_TIMEOUT: int = int(os.getenv("TELEGRAM_WRITE_TIMEOUT", "30"))
    TELEGRAM_CONNECT_TIMEOUT: int = int(os.getenv("TELEGRAM_CONNECT_TIMEOUT", "10"))

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required. Set it in .env file.")


config = Config()
