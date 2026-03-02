import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_dir: str = "./data/logs"):
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger.remove()
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
    )
    logger.add(
        f"{log_dir}/doraemon.log",
        rotation="10 MB",
        retention="7 days",
        level="DEBUG",
    )
    return logger
