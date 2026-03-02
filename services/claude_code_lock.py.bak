import asyncio
import signal
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
        process = None
        try:
            # Build command with optional session ID
            cmd = [config.CLAUDE_CODE_PATH, "--print"]
            if session_id:
                cmd.extend(["--session-id", session_id])

            logger.debug(f"Starting Claude Code process: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=message.encode()),
                    timeout=120,
                )
            except asyncio.TimeoutError:
                logger.error(f"Claude Code timed out, killing process {process.pid}")
                # Force kill the process
                try:
                    process.kill()
                    await process.wait()
                except Exception as e:
                    logger.error(f"Failed to kill process: {e}")
                return "⏱️ 请求超时（120秒），请尝试发送更简短的消息。"

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(f"Claude Code error (rc={process.returncode}): {error_msg}")

                # Check for specific error messages
                if "already in use" in error_msg.lower():
                    return "⚠️ 会话正在处理中，请稍等片刻再试。"

                return "抱歉，遇到了错误。请稍后重试。"

            response = stdout.decode().strip()
            logger.debug(f"Claude Code response: {len(response)} chars")
            return response

        except FileNotFoundError:
            logger.error(f"Claude Code not found at: {config.CLAUDE_CODE_PATH}")
            return "Claude Code CLI 未找到，请检查配置。"
        except Exception as e:
            logger.exception(f"Unexpected error calling Claude Code: {e}")
            return "抱歉，出现了问题。请稍后重试。"
        finally:
            # Ensure process is cleaned up
            if process and process.returncode is None:
                try:
                    logger.warning(f"Cleaning up process {process.pid}")
                    process.kill()
                    await process.wait()
                except Exception as e:
                    logger.error(f"Failed to cleanup process: {e}")

    # Use lock if session_id is provided
    if lock:
        async with lock:
            return await _call_claude()
    else:
        return await _call_claude()
