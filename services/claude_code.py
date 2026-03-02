import asyncio
from loguru import logger
from config import config


async def ask_claude(message: str) -> str:
    """Call Claude Code CLI and return the response."""
    try:
        process = await asyncio.create_subprocess_exec(
            config.CLAUDE_CODE_PATH,
            "--print",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(input=message.encode()),
            timeout=120,
        )
        if process.returncode != 0:
            logger.error(f"Claude Code error (rc={process.returncode}): {stderr.decode()}")
            return "Sorry, I encountered an error. Please try again."

        return stdout.decode().strip()

    except asyncio.TimeoutError:
        logger.error("Claude Code timed out after 120s")
        return "Request timed out. Please try again."
    except FileNotFoundError:
        logger.error(f"Claude Code not found at: {config.CLAUDE_CODE_PATH}")
        return "Claude Code CLI not found. Please check your configuration."
    except Exception as e:
        logger.exception(f"Unexpected error calling Claude Code: {e}")
        return "Sorry, something went wrong. Please try again."
