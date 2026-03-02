import asyncio
from collections import defaultdict
from loguru import logger
from config import config

# Session locks to prevent concurrent access to the same Claude Code session
_session_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


async def ask_claude(message: str, session_id: str = None) -> str:
    """Call Claude Code CLI and return the response.

    Args:
        message: The user's message
        session_id: Optional Claude Code session ID for context persistence
    """
    # Acquire lock for this session to prevent concurrent access
    lock = _session_locks[session_id] if session_id else None

    async def _call_claude():
        try:
            # Build command with optional session ID
            cmd = [config.CLAUDE_CODE_PATH, "--print"]
            if session_id:
                cmd.extend(["--session-id", session_id])

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=message.encode()),
                timeout=120,
            )
            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Claude Code error (rc={process.returncode}): {error_msg}")

                # Check for specific error messages
                if "already in use" in error_msg.lower():
                    return "⚠️ 会话正在处理中，请稍等片刻再试。"

                return "抱歉，遇到了错误。请稍后重试。"

            return stdout.decode().strip()

        except asyncio.TimeoutError:
            logger.error("Claude Code timed out after 120s")
            return "请求超时，请稍后重试。"
        except FileNotFoundError:
            logger.error(f"Claude Code not found at: {config.CLAUDE_CODE_PATH}")
            return "Claude Code CLI 未找到，请检查配置。"
        except Exception as e:
            logger.exception(f"Unexpected error calling Claude Code: {e}")
            return "抱歉，出现了问题。请稍后重试。"

    # Use lock if session_id is provided
    if lock:
        async with lock:
            return await _call_claude()
    else:
        return await _call_claude()
