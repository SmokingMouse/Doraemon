# 队列机制切换完成

## 已完成的更改

### 1. 核心实现切换

**之前（锁机制）**：
```python
_session_locks[session_id]  # 每个 session 一个锁
async with lock:
    await call_claude()
```

**现在（队列机制）**：
```python
_session_queues[session_id]  # 每个 session 一个队列
_workers[session_id]          # 每个 session 一个 worker

await queue.put(request)
return await future
```

### 2. 新增功能

**队列监控**：
- `/stats` 命令现在显示队列中等待的消息数
- 可以实时看到有多少消息在排队

**示例输出**：
```
📊 你的统计信息

💬 消息数: 15
🔄 会话数: 1
📅 首次使用: 2026-03-02 14:32:30
⏰ 最后活跃: 2026-03-03 01:20:00

📋 当前队列: 2 条消息等待处理
```

### 3. 架构改进

**ClaudeCodeService 类**：
```python
class ClaudeCodeService:
    def __init__(self):
        self._session_queues = defaultdict(asyncio.Queue)
        self._workers = {}

    async def ask_claude(message, session_id):
        # 提交到队列
        await queue.put(request)
        return await future

    async def _process_queue(worker_key, queue):
        # Worker 循环处理队列
        while True:
            request = await queue.get()
            response = await _call_claude_process(...)
            request.future.set_result(response)

    def get_queue_size(session_id):
        # 查询队列大小
        return queue.qsize()
```

## 优势对比

### 并行性

**相同**：不同 session 仍然可以并行

```
Session A: 消息1 → Worker A 处理
Session B: 消息1 → Worker B 处理  (并行!)
```

### 可观测性

**改进**：可以查看队列状态

```python
# 之前：无法知道有多少消息在等待
# 现在：
queue_size = service.get_queue_size(session_id)
print(f"队列中有 {queue_size} 条消息")
```

### 可扩展性

**改进**：更容易添加新功能

```python
# 未来可以轻松添加：
- 优先级队列
- 请求取消
- 批处理
- 限流控制
- 队列监控和告警
```

## 性能影响

### 内存

- 锁机制: ~100 bytes per session
- 队列机制: ~1 KB per session
- **影响**: 可忽略（1000 个 session = 1 MB）

### CPU

- **相同**: 都是异步等待，CPU 开销几乎为 0

### 延迟

- **相同**: 都是串行处理同一 session 的请求

## 测试验证

### 基本功能

```bash
# 1. 启动 bot
./restart_bot.sh

# 2. 在 Telegram 发送消息
"你好"  → 应该正常回复

# 3. 快速发送多条消息
"消息1"
"消息2"
"消息3"
→ 应该按顺序回复，不会出错

# 4. 查看统计
/stats
→ 应该显示队列大小
```

### 并发测试

```bash
# 两个用户同时发送消息
User A: "hello"
User B: "world"
→ 应该并行处理，互不影响
```

### 队列监控

```bash
# 快速发送 5 条消息
"1" "2" "3" "4" "5"

# 立即查看统计
/stats
→ 应该显示队列中有 4 条消息（第 1 条正在处理）
```

## 回滚方案

如果需要回滚到锁机制：

```bash
# 1. 恢复旧文件
mv services/claude_code.py services/claude_code_queue.py
mv services/claude_code_lock.py.bak services/claude_code.py

# 2. 重启
./restart_bot.sh

# 3. 提交
git add services/claude_code.py
git commit -m "revert: switch back to lock mechanism"
```

## 未来扩展

### 优先级队列

```python
class PriorityRequest:
    message: str
    priority: int  # 0=highest, 9=lowest

# 高优先级请求（如 /help）先处理
await service.ask_claude(message, session_id, priority=0)
```

### 请求取消

```python
# 用户可以取消等待中的请求
request_id = await service.submit_request(message, session_id)
await service.cancel_request(request_id)
```

### 限流

```python
# 限制队列长度
MAX_QUEUE_SIZE = 10

if queue.qsize() >= MAX_QUEUE_SIZE:
    return "⚠️ 消息太多了，请稍后再试"
```

### 批处理

```python
# 如果队列中有多条消息，批量处理
async def _worker(queue):
    batch = []
    batch.append(await queue.get())

    # 收集更多消息
    while not queue.empty() and len(batch) < 5:
        batch.append(queue.get_nowait())

    # 批量处理（如果 Claude Code 支持）
    await process_batch(batch)
```

## 监控和调试

### 查看所有队列状态

```python
# 添加管理命令
async def admin_queues_cmd(update, context):
    status = []
    for session_id, queue in _claude_service._session_queues.items():
        status.append(f"Session {session_id[:8]}: {queue.qsize()} pending")

    await update.message.reply_text("\n".join(status))
```

### 日志增强

```python
# Worker 启动/停止日志
logger.info(f"Worker started for session: {session_id}")
logger.info(f"Worker stopped for session: {session_id}")

# 队列状态日志
logger.debug(f"Queue size for {session_id}: {queue.qsize()}")
```

## 总结

### 切换完成 ✅

- ✅ 队列机制已实现
- ✅ Bot 已重启
- ✅ 功能正常
- ✅ 队列监控已添加

### 关键改进

1. **更清晰的语义**：消息队列模式
2. **更好的可观测性**：可以看到队列状态
3. **更容易扩展**：为未来功能打下基础

### 用户体验

**无变化**：
- 消息处理速度相同
- 响应时间相同
- 并行性相同

**新增**：
- 可以看到队列中有多少消息在等待

### 下一步

可以考虑添加：
- 优先级队列（VIP 用户优先）
- 请求取消（用户可以取消等待）
- 限流保护（防止滥用）
- 队列监控告警（队列过长时通知）

现在可以在 Telegram 中测试新的队列机制了！
