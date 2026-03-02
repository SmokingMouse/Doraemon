import asyncio
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from loguru import logger
from config import config


@dataclass
class ClaudeRequest:
    """Claude Code 请求"""

    message: str
    session_id: Optional[str]
    response_future: asyncio.Future


class ClaudeCodeService:
    """Claude Code 服务，使用队列管理请求"""

    def __init__(self):
        # 每个 session 一个队列
        self._session_queues: dict[str, asyncio.Queue] = defaultdict(
            lambda: asyncio.Queue()
        )
        # 每个 session 一个 worker
        self._workers: dict[str, asyncio.Task] = {}
        # Claude Code 会话文件目录（按项目路径）
        project_path = Path.cwd().as_posix().replace("/", "-")
        self._session_dir = Path.home() / ".claude" / "projects" / project_path

    async def ask_claude(
        self, message: str, session_id: str = None, context: str = None
    ) -> str:
        """提交请求到队列，等待响应

        Args:
            message: 用户消息
            session_id: 会话 ID
            context: 对话历史上下文（可选）
        """
        # 创建响应 future
        response_future = asyncio.Future()

        # 创建请求
        request = ClaudeRequest(
            message=message,
            session_id=session_id,
            response_future=response_future,
        )

        # 如果有上下文，将其添加到消息前
        if context:
            request.message = f"{context}\n\n当前消息：{message}"

        # 获取或创建队列
        queue = self._session_queues[session_id or "default"]

        # 启动 worker（如果还没启动）
        worker_key = session_id or "default"
        if worker_key not in self._workers or self._workers[worker_key].done():
            self._workers[worker_key] = asyncio.create_task(
                self._process_queue(worker_key, queue)
            )

        # 提交请求到队列
        await queue.put(request)
        logger.debug(
            f"Request queued for session {session_id}, queue size: {queue.qsize()}"
        )

        # 等待响应
        return await response_future

    async def _process_queue(self, worker_key: str, queue: asyncio.Queue):
        """处理队列中的请求（每个 session 一个 worker）"""
        logger.info(f"Worker started for session: {worker_key}")

        while True:
            try:
                # 从队列获取请求
                request: ClaudeRequest = await queue.get()

                logger.debug(
                    f"Processing request for session {request.session_id}, "
                    f"remaining in queue: {queue.qsize()}"
                )

                # 执行请求
                try:
                    response = await self._call_claude_process(
                        request.message, request.session_id
                    )
                    request.response_future.set_result(response)
                except Exception as e:
                    # 记录错误但继续处理队列
                    logger.error(f"Failed to process request: {e}")
                    # 返回友好的错误消息
                    request.response_future.set_result(
                        "抱歉，处理消息时出错了。请稍后重试。"
                    )
                finally:
                    queue.task_done()

            except asyncio.CancelledError:
                logger.info(f"Worker cancelled for session: {worker_key}")
                break
            except Exception as e:
                logger.exception(f"Worker error for session {worker_key}: {e}")

    async def _call_claude_process(
        self, message: str, session_id: Optional[str]
    ) -> str:
        """实际调用 Claude Code CLI"""
        process = None
        try:
            # Build command
            cmd = [config.CLAUDE_CODE_PATH, "--print"]
            if session_id:
                # 检查会话文件是否存在
                session_file = self._session_dir / f"{session_id}.jsonl"
                if session_file.exists():
                    # 会话存在，使用 --resume 恢复
                    cmd.extend(["--resume", session_id])
                    logger.debug(f"Resuming existing session: {session_id}")
                else:
                    # 会话不存在，使用 --session-id 创建
                    cmd.extend(["--session-id", session_id])
                    logger.debug(f"Creating new session: {session_id}")

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
                try:
                    process.kill()
                    await process.wait()
                except Exception as e:
                    logger.error(f"Failed to kill process: {e}")
                return "⏱️ 请求超时（120秒），请尝试发送更简短的消息。"

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(
                    f"Claude Code error (rc={process.returncode}): {error_msg}"
                )

                if "already in use" in error_msg.lower():
                    return "⚠️ 会话正在处理中，请稍等片刻再试。"

                return "抱歉，遇到了错误。请稍后重试。"

            response = stdout.decode().strip()
            logger.debug(f"Claude Code response: {len(response)} chars")

            # 清理会话文件，避免锁定问题
            if session_id:
                self._cleanup_session(session_id)

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

    def _cleanup_session(self, session_id: str):
        """清理会话文件，释放 session ID"""
        try:
            # Claude Code 会话文件路径
            session_file = self._session_dir / f"{session_id}.jsonl"
            if session_file.exists():
                session_file.unlink()
                logger.info(f"Cleaned up session file: {session_id}")
            else:
                logger.debug(f"Session file not found: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup session {session_id}: {e}")

    def get_queue_size(self, session_id: str = None) -> int:
        """获取队列大小"""
        key = session_id or "default"
        return self._session_queues[key].qsize()

    async def shutdown(self):
        """关闭所有 worker"""
        for worker in self._workers.values():
            worker.cancel()
        await asyncio.gather(*self._workers.values(), return_exceptions=True)


# 全局实例
_claude_service = ClaudeCodeService()


async def ask_claude(message: str, session_id: str = None) -> str:
    """兼容接口"""
    return await _claude_service.ask_claude(message, session_id)
