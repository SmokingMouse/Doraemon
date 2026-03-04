import asyncio
import json
import os
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Callable, Awaitable
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
        self, message: str, session_id: Optional[str] = None, context: Optional[str] = None
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

    async def ask_claude_streaming(
        self,
        message: str,
        session_id: Optional[str] = None,
        on_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        max_retries: int = 3,
    ) -> tuple[str, Optional[str]]:
        """流式调用 Claude，实时返回响应片段

        Args:
            message: 用户消息
            session_id: 会话 ID
            on_chunk: 接收到新内容时的回调函数
            max_retries: 最大重试次数

        Returns:
            (完整响应内容, 新的 session_id)
        """
        if on_chunk is None:
            # 如果没有提供回调，使用普通方式
            response = await self.ask_claude(message, session_id)
            return (response, session_id)

        # 重试逻辑（指数退避）
        for attempt in range(max_retries):
            # 直接调用流式方法（不经过队列）
            response, new_session_id, error_type = await self._call_claude_process_streaming(
                message, session_id, on_chunk
            )

            # 如果成功或不可重试的错误，直接返回
            if not error_type:
                return (response, new_session_id)

            # 可重试的错误类型
            retryable_errors = {"session_in_use", "session_not_found"}
            if error_type not in retryable_errors:
                # 不可重试的错误，直接返回
                error_messages = {
                    "timeout": response,
                    "not_found": response,
                    "other": f"❌ 错误：{response}"
                }
                return (error_messages.get(error_type, response), session_id)

            # 如果是最后一次尝试，返回错误
            if attempt == max_retries - 1:
                error_messages = {
                    "session_in_use": f"❌ 会话被占用（已重试 {max_retries} 次）：{response}",
                    "session_not_found": f"❌ 会话不存在（已重试 {max_retries} 次）：{response}",
                }
                return (error_messages.get(error_type, response), session_id)

            # 指数退避：1s, 2s, 4s
            wait_time = 2 ** attempt
            logger.warning(
                f"Retrying due to {error_type}, attempt {attempt + 1}/{max_retries}, "
                f"waiting {wait_time}s"
            )

            # 通知用户正在重试
            if on_chunk:
                retry_msg = f"\n⚠️ {error_type}，{wait_time}秒后重试...\n"
                await on_chunk(retry_msg)

            await asyncio.sleep(wait_time)

            # 对于 session 错误，尝试使用新 session
            if error_type in {"session_in_use", "session_not_found"}:
                session_id = None  # 清除 session_id，让系统创建新会话

        # 理论上不会到这里
        return ("❌ 重试失败", session_id)

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
                    response, _, error_type = await self._call_claude_process(
                        request.message, request.session_id
                    )

                    # 如果有错误，返回带错误类型的信息
                    if error_type:
                        error_messages = {
                            "session_in_use": f"❌ 会话被占用：{response}\n\n提示：可以尝试重新发送消息创建新会话。",
                            "session_not_found": f"❌ 会话不存在：{response}\n\n提示：可以尝试重新发送消息创建新会话。",
                            "timeout": response,
                            "not_found": response,
                            "other": f"❌ 错误：{response}"
                        }
                        error_msg = error_messages.get(error_type, response)
                        request.response_future.set_result(error_msg)
                    else:
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
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """实际调用 Claude Code CLI

        Returns:
            Tuple[str, Optional[str], Optional[str]]: (response, session_id, error_type)
            - response: 响应内容或错误信息
            - session_id: 会话 ID
            - error_type: 错误类型 ("session_in_use", "session_not_found", "timeout", "other", None)
        """
        process = None
        try:
            # Build command
            cmd = [
                config.CLAUDE_CODE_PATH, 
                "--print",
                "--dangerously-skip-permissions",
                # '--output-format', 'stream-json',
                # "--verbose"
            ]

            # 优先使用 resume
            if session_id:
                cmd.extend(["--resume", session_id])
                logger.debug(f"Attempting to resume session: {session_id}")

            logger.debug(f"Starting Claude Code process: {' '.join(cmd)}")

            # 清除 CLAUDECODE 环境变量，避免嵌套会话错误
            env = os.environ.copy()
            env.pop('CLAUDECODE', None)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
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
                return ("⏱️ 请求超时（120秒），请尝试发送更简短的消息。", session_id, "timeout")

            if process.returncode != 0:
                error_msg = stderr.decode()
                logger.error(
                    f"Claude Code error (rc={process.returncode}): {error_msg}"
                )

                # 识别错误类型，但不做处理
                error_type = None
                if "already in use" in error_msg.lower():
                    error_type = "session_in_use"
                elif "no conversation found" in error_msg.lower():
                    error_type = "session_not_found"
                else:
                    error_type = "other"

                return (error_msg, session_id, error_type)

            response = stdout.decode().strip()
            logger.debug(f"Claude Code response: {len(response)} chars")
            return (response, session_id, None)

        except FileNotFoundError:
            logger.error(f"Claude Code not found at: {config.CLAUDE_CODE_PATH}")
            return ("Claude Code CLI 未找到，请检查配置。", session_id, "not_found")
        except Exception as e:
            logger.exception(f"Unexpected error calling Claude Code: {e}")
            return ("抱歉，出现了问题。请稍后重试。", session_id, "other")
        finally:
            # Ensure process is cleaned up
            if process and process.returncode is None:
                try:
                    logger.warning(f"Cleaning up process {process.pid}")
                    process.kill()
                    await process.wait()
                except Exception as e:
                    logger.error(f"Failed to cleanup process: {e}")

    async def _call_claude_process_streaming(
        self,
        message: str,
        session_id: Optional[str],
        on_chunk: Callable[[str], Awaitable[None]],
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """流式调用 Claude Code CLI，实时回调输出

        Args:
            message: 用户消息
            session_id: 会话 ID
            on_chunk: 接收到新内容时的回调函数

        Returns:
            Tuple[str, Optional[str], Optional[str]]: (response, session_id, error_type)
        """
        process = None
        accumulated_output = []
        current_block_type = None  # 追踪当前内容块类型
        current_tool_name = None  # 追踪当前工具名称
        tool_start_time = None  # 追踪工具开始时间
        actual_session_id = session_id  # 实际的 session ID（可能从响应中提取）

        # 创建日志文件
        log_dir = Path("logs/streaming")
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"stream_{timestamp}.jsonl"

        logger.info(f"Streaming output will be logged to: {log_file}")

        try:
            # Build command with streaming JSON output
            cmd = [
                config.CLAUDE_CODE_PATH,
                "--print",
                "--output-format", "stream-json",
                "--include-partial-messages",
                "--dangerously-skip-permissions",
                "--verbose"
            ]

            if session_id:
                cmd.extend(["--resume", session_id])
                logger.debug(f"Attempting to resume session: {session_id}")

            logger.debug(f"Starting Claude Code streaming process: {' '.join(cmd)}")

            # 清除 CLAUDECODE 环境变量，避免嵌套会话错误
            env = os.environ.copy()
            env.pop('CLAUDECODE', None)

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            # 发送消息
            if process.stdin:
                process.stdin.write(message.encode())
                process.stdin.close()

            # 流式读取输出
            if not process.stdout:
                return ("无法读取输出", session_id, "other")

            try:
                async for line in process.stdout:
                    if line:
                        line_text = line.decode('utf-8', errors='ignore').strip()
                        logger.debug(f"Received line: {line_text[:100]}")

                        # 写入日志文件（原始 JSON）
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(line_text + '\n')

                        try:
                            # 解析 JSON 流事件
                            event = json.loads(line_text)
                            event_type = event.get('type')
                            logger.debug(f"Parsed event type: {event_type}")

                            # 提取 session_id（从第一个 system 事件）
                            if event_type == "system" and not actual_session_id:
                                actual_session_id = event.get("session_id")
                                if actual_session_id:
                                    logger.info(f"Extracted new session_id: {actual_session_id}")

                            # 处理 stream_event 类型
                            if event_type == "stream_event":
                                inner_event = event.get("event", {})
                                inner_type = inner_event.get("type")
                                logger.debug(f"Inner event type: {inner_type}")

                                # 处理 content_block_start 事件（标记内容块类型）
                                if inner_type == "content_block_start":
                                    content_block = inner_event.get("content_block", {})
                                    block_type = content_block.get("type")
                                    current_block_type = block_type  # 记录当前块类型
                                    logger.debug(f"Content block started: {block_type}")

                                    # 如果是思考块，添加思考标记
                                    if block_type == "thinking":
                                        thinking_marker = "\n\n💭 **思考过程：**\n"
                                        accumulated_output.append(thinking_marker)
                                        await on_chunk(thinking_marker)

                                    # 如果是工具调用块，记录工具名称和开始时间
                                    elif block_type == "tool_use":
                                        tool_name = content_block.get("name", "unknown")
                                        current_tool_name = tool_name
                                        tool_start_time = asyncio.get_event_loop().time()
                                        tool_marker = f"\n🔧 调用工具: {tool_name}\n"
                                        accumulated_output.append(tool_marker)
                                        await on_chunk(tool_marker)

                                # 处理 content_block_delta 事件（文本增量）
                                elif inner_type == "content_block_delta":
                                    delta = inner_event.get("delta", {})
                                    delta_type = delta.get("type")
                                    logger.debug(f"Delta type: {delta_type}")

                                    if delta_type == "text_delta":
                                        text = delta.get("text", "")
                                        if text:
                                            logger.debug(f"Got text delta: {text[:50]}")
                                            accumulated_output.append(text)
                                            # 回调新内容
                                            await on_chunk(text)
                                        else:
                                            logger.debug("Text delta is empty")
                                    elif delta_type == "thinking_delta":
                                        # 处理思考过程的增量
                                        thinking_text = delta.get("thinking", "")
                                        if thinking_text:
                                            logger.debug(f"Got thinking delta: {thinking_text[:50]}")
                                            accumulated_output.append(thinking_text)
                                            await on_chunk(thinking_text)
                                    else:
                                        logger.debug(f"Skipping non-text delta: {delta_type}")

                                # 处理 content_block_stop 事件
                                elif inner_type == "content_block_stop":
                                    logger.debug(f"Content block stopped: {current_block_type}")

                                    # 只在思考块结束后添加分隔符
                                    if current_block_type == "thinking":
                                        separator = "\n\n---\n\n"
                                        accumulated_output.append(separator)
                                        await on_chunk(separator)

                                    # 工具调用结束，显示耗时
                                    elif current_block_type == "tool_use" and tool_start_time:
                                        elapsed = asyncio.get_event_loop().time() - tool_start_time
                                        tool_end_marker = f"✅ {current_tool_name} 完成 ({elapsed:.1f}s)\n"
                                        accumulated_output.append(tool_end_marker)
                                        await on_chunk(tool_end_marker)
                                        current_tool_name = None
                                        tool_start_time = None

                                    current_block_type = None  # 重置块类型

                                # 处理 message_stop 事件
                                elif inner_type == "message_stop":
                                    logger.debug("Stream completed")
                                else:
                                    logger.debug(f"Skipping inner event type: {inner_type}")

                            # 处理 result 事件（可能包含错误信息）
                            elif event_type == "result":
                                if event.get("is_error"):
                                    error_detail = event.get("error", "Unknown error")
                                    logger.error(f"Result event indicates error: {error_detail}")

                        except json.JSONDecodeError as e:
                            logger.debug(f"Failed to parse JSON line: {e}, line: {line_text[:100]}")
                            continue

                # 等待进程结束
                await asyncio.wait_for(process.wait(), timeout=120)

            except asyncio.TimeoutError:
                logger.error(f"Claude Code timed out, killing process {process.pid}")
                try:
                    process.kill()
                    await process.wait()
                except Exception as e:
                    logger.error(f"Failed to kill process: {e}")
                return ("⏱️ 请求超时（120秒），请尝试发送更简短的消息。", session_id, "timeout")

            # 读取错误输出
            stderr_data = await process.stderr.read() if process.stderr else b""

            if process.returncode != 0:
                error_msg = stderr_data.decode()
                logger.error(
                    f"Claude Code error (rc={process.returncode}): {error_msg}"
                )

                # 识别错误类型
                error_type = None
                if "already in use" in error_msg.lower():
                    error_type = "session_in_use"
                elif "no conversation found" in error_msg.lower():
                    error_type = "session_not_found"
                else:
                    error_type = "other"

                return (error_msg, actual_session_id, error_type)

            response = ''.join(accumulated_output).strip()
            logger.debug(f"Claude Code streaming response: {len(response)} chars")
            return (response, actual_session_id, None)

        except FileNotFoundError:
            logger.error(f"Claude Code not found at: {config.CLAUDE_CODE_PATH}")
            return ("Claude Code CLI 未找到，请检查配置。", actual_session_id, "not_found")
        except Exception as e:
            logger.exception(f"Unexpected error calling Claude Code: {e}")
            return ("抱歉，出现了问题。请稍后重试。", actual_session_id, "other")
        finally:
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

    def get_queue_size(self, session_id: Optional[str] = None) -> int:
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


async def ask_claude(message: str, session_id: Optional[str] = None) -> str:
    """兼容接口"""
    return await _claude_service.ask_claude(message, session_id)
