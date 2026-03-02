# Claude Code 进程机制详解

## 进程生命周期

### 阶段 1: 进程启动 (0-100ms)

```
Bot (Python)
    ↓ fork + exec
Claude Process (PID: 12345)
    ↓
启动检查:
1. 检查 CLAUDECODE 环境变量
   - 存在 → 退出 (rc=1): "cannot be launched inside another session"
   - 不存在 → 继续

2. 检查 session 文件
   - ~/.claude/sessions/<uuid>.jsonl
   - 如果不存在 → 创建新文件
   - 如果存在 → 准备读取

3. 获取 session 锁
   - 尝试获取文件锁或进程锁
   - 如果已被锁 → 退出 (rc=1): "Session ID already in use"
   - 成功获取 → 继续
```

### 阶段 2: 读取历史 (100-500ms)

```
Claude Process
    ↓
读取 session 文件:
1. 打开 ~/.claude/sessions/<uuid>.jsonl
2. 逐行解析 JSON
   - 每行是一条消息
   - 格式: {"role": "user", "content": "...", "timestamp": "..."}
3. 构建对话历史数组
   - [msg1, msg2, msg3, ...]
4. 加载到内存
```

**Session 文件示例**：
```jsonl
{"role":"user","content":"你好","timestamp":"2026-03-03T00:00:00Z"}
{"role":"assistant","content":"你好！我是 Doraemon...","timestamp":"2026-03-03T00:00:01Z"}
{"role":"user","content":"我刚才说了什么？","timestamp":"2026-03-03T00:00:10Z"}
```

### 阶段 3: API 调用 (1-30秒)

```
Claude Process
    ↓
准备 API 请求:
1. 构建完整的消息数组
   - 历史消息 + 新消息
   - [history..., {"role": "user", "content": "new message"}]

2. 调用 Claude API
   - POST https://api.anthropic.com/v1/messages
   - 包含完整对话历史
   - 等待响应...

3. 接收响应
   - 流式接收（如果使用 --output-format=stream-json）
   - 或一次性接收（--print 模式）
```

### 阶段 4: 保存结果 (100-500ms)

```
Claude Process
    ↓
保存到 session 文件:
1. 追加新的用户消息
   - 写入 ~/.claude/sessions/<uuid>.jsonl
   - 追加模式（append）

2. 追加 AI 响应
   - 写入同一文件
   - 追加模式

3. 刷新缓冲区
   - 确保数据写入磁盘
```

### 阶段 5: 进程退出 (0-100ms)

```
Claude Process
    ↓
清理和退出:
1. 释放 session 锁
   - 解锁文件
   - 允许其他进程访问

2. 关闭文件描述符
   - 关闭 session 文件
   - 关闭 stdin/stdout/stderr

3. 退出进程
   - 返回退出码 (0=成功, 1=错误)
   - 进程终止

Bot (Python)
    ↓
接收结果:
- stdout: AI 的响应文本
- stderr: 错误信息（如果有）
- returncode: 退出码
```

---

## 并发问题详解

### 问题场景

```
时间线:
T0: 用户发送消息 1 "hello"
T1: Bot 启动 Claude Process A (PID: 100)
    └─ 获取 session 锁
    └─ 开始 API 调用...

T5: 用户发送消息 2 "world" (Process A 还在运行!)
T6: Bot 启动 Claude Process B (PID: 101)
    └─ 尝试获取 session 锁
    └─ 失败! 锁已被 Process A 持有
    └─ 退出: "Session ID already in use"
```

### 锁的实现方式

Claude Code 可能使用以下几种锁机制之一：

**方式 1: 文件锁 (flock)**
```c
// Claude Code 内部（伪代码）
int fd = open("~/.claude/sessions/uuid.jsonl", O_RDWR);
if (flock(fd, LOCK_EX | LOCK_NB) == -1) {
    // 锁已被占用
    error("Session ID already in use");
}
// 持有锁，继续执行...
// ...
flock(fd, LOCK_UN);  // 释放锁
close(fd);
```

**方式 2: PID 文件**
```bash
# Claude Code 内部（伪代码）
LOCK_FILE="~/.claude/sessions/uuid.lock"
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if kill -0 $PID 2>/dev/null; then
        # 进程还在运行
        error("Session ID already in use")
    fi
fi
echo $$ > "$LOCK_FILE"  # 写入当前 PID
# 执行...
rm "$LOCK_FILE"  # 清理
```

**方式 3: 进程检查**
```bash
# 检查是否有其他 claude 进程使用相同的 session-id
ps aux | grep "claude.*--session-id uuid-123"
```

---

## 我们的解决方案

### Bot 层面的锁机制

```python
# services/claude_code.py
_session_locks = defaultdict(asyncio.Lock)

async def ask_claude(message: str, session_id: str = None):
    lock = _session_locks[session_id]

    async with lock:  # 获取 asyncio 锁
        # 只有一个协程能进入这里
        process = await asyncio.create_subprocess_exec(...)
        stdout, stderr = await process.communicate(...)
        # 进程完成，释放锁
```

**工作原理**：

```
请求 1:
    获取 asyncio 锁 → 启动 Claude Process → 等待完成 → 释放锁

请求 2 (并发):
    尝试获取 asyncio 锁 → 等待... → 请求 1 完成 → 获取锁 → 启动 Claude Process

结果: 串行化，不会有两个 Claude 进程同时使用同一个 session ID
```

### 双重保护

```
第一层: Bot 的 asyncio.Lock
    └─ 防止 Bot 同时启动多个 Claude 进程

第二层: Claude Code 的文件锁/进程锁
    └─ 防止不同程序同时访问同一个 session
```

---

## 进程状态监控

### 查看运行中的 Claude 进程

```bash
# 查看所有 claude 进程
ps aux | grep claude

# 查看特定 session 的进程
ps aux | grep "claude.*session-id.*uuid-123"

# 查看进程树
pstree -p | grep claude
```

### 进程可能的状态

```
S  - Sleeping (等待 I/O，如 API 响应)
R  - Running (正在执行)
Z  - Zombie (已退出但未被回收)
D  - Uninterruptible sleep (不可中断，通常是 I/O)
T  - Stopped (被暂停)
```

### 僵尸进程问题

```
正常情况:
Claude Process 退出 → 父进程 (Bot) 调用 wait() → 进程被回收

异常情况:
Claude Process 退出 → 父进程没有 wait() → 变成僵尸进程 (Z)
    └─ 仍然占用 PID
    └─ 可能仍然持有文件锁
```

**我们的解决方案**：
```python
try:
    stdout, stderr = await process.communicate(...)
except asyncio.TimeoutError:
    process.kill()  # 强制终止
    await process.wait()  # 等待进程退出，回收资源
finally:
    if process.returncode is None:
        process.kill()
        await process.wait()  # 确保回收
```

---

## 超时和清理机制

### 超时处理

```python
try:
    stdout, stderr = await asyncio.wait_for(
        process.communicate(input=message.encode()),
        timeout=120  # 120 秒超时
    )
except asyncio.TimeoutError:
    # 超时后的处理
    logger.error(f"Process {process.pid} timed out")

    # 1. 发送 SIGTERM (优雅终止)
    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=5)
    except asyncio.TimeoutError:
        # 2. 如果还不退出，发送 SIGKILL (强制终止)
        process.kill()
        await process.wait()
```

### 进程信号

```
SIGTERM (15) - 优雅终止
    └─ 进程可以捕获并清理资源
    └─ process.terminate()

SIGKILL (9) - 强制终止
    └─ 进程无法捕获，立即终止
    └─ process.kill()
    └─ 可能导致资源泄漏（文件锁未释放）
```

---

## 实际执行流程示例

### 成功的情况

```
T0.000s: Bot 接收消息 "hello"
T0.001s: 获取 asyncio 锁
T0.002s: 启动 Claude Process (PID: 12345)
T0.100s: Claude 检查通过，获取文件锁
T0.200s: 读取 session 历史 (10 条消息)
T0.300s: 开始 API 调用
T5.000s: API 返回响应
T5.100s: 写入 session 文件
T5.150s: 释放文件锁
T5.200s: 进程退出 (rc=0)
T5.201s: Bot 接收 stdout
T5.202s: 释放 asyncio 锁
T5.203s: 发送响应到 Telegram
```

### 并发冲突的情况（无 Bot 锁）

```
T0.000s: 消息 1 "hello"
T0.001s: 启动 Process A (PID: 100)
T0.100s: Process A 获取文件锁

T0.500s: 消息 2 "world" (Process A 还在运行!)
T0.501s: 启动 Process B (PID: 101)
T0.600s: Process B 尝试获取文件锁 → 失败!
T0.601s: Process B 退出 (rc=1): "Session ID already in use"

T5.000s: Process A 完成并退出
```

### 有 Bot 锁的情况

```
T0.000s: 消息 1 "hello"
T0.001s: 获取 asyncio 锁
T0.002s: 启动 Process A (PID: 100)

T0.500s: 消息 2 "world"
T0.501s: 尝试获取 asyncio 锁 → 等待...
         (Process A 还在运行，锁未释放)

T5.000s: Process A 完成
T5.001s: 释放 asyncio 锁
T5.002s: 消息 2 获取锁
T5.003s: 启动 Process B (PID: 101)
T5.100s: Process B 成功获取文件锁 (Process A 已释放)
T10.000s: Process B 完成
```

---

## 调试技巧

### 实时监控进程

```bash
# 持续监控 claude 进程
watch -n 1 'ps aux | grep claude | grep -v grep'

# 监控特定 session
watch -n 1 'ps aux | grep "session-id.*uuid-123"'

# 查看进程打开的文件
lsof -p <PID>

# 查看进程持有的锁
lsof | grep "\.lock"
```

### 检查僵尸进程

```bash
# 查找僵尸进程
ps aux | grep 'Z'

# 查找 claude 僵尸进程
ps aux | grep claude | grep 'Z'

# 清理僵尸进程（杀死父进程）
kill -9 <parent_pid>
```

### 手动清理锁文件

```bash
# 如果 Claude Code 使用 PID 文件
rm ~/.claude/sessions/*.lock

# 如果使用文件锁，需要终止持有锁的进程
lsof ~/.claude/sessions/*.jsonl
kill -9 <PID>
```

---

## 总结

### 关键点

1. **每次调用 = 新进程**
   - 不是长期运行的守护进程
   - 每次都要启动、执行、退出

2. **Session 文件是共享资源**
   - 需要锁机制保护
   - 同时只能有一个进程访问

3. **双重锁保护**
   - Bot 层: asyncio.Lock (防止并发启动)
   - Claude 层: 文件锁 (防止跨进程冲突)

4. **进程必须正确清理**
   - 超时后强制 kill
   - finally 块确保回收
   - 防止僵尸进程和锁泄漏

5. **CLAUDECODE 环境变量**
   - 防止嵌套会话
   - Bot 启动时必须 unset

这就是完整的进程机制！
