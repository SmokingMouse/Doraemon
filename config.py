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

    # Web settings
    WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8765"))  # 小众端口，避免冲突
    WEB_SECRET_KEY: str = os.getenv("WEB_SECRET_KEY", "change-me-in-production")
    WEB_ALLOWED_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv("WEB_ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if origin.strip()
    ]

    # Frontend settings
    FRONTEND_PORT: int = int(os.getenv("FRONTEND_PORT", "5173"))  # Vite 默认端口

    @classmethod
    def validate(cls):
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is required. Set it in .env file.")


config = Config()
