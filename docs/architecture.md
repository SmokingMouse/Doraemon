# Doraemon 系统架构和工作原理

## 核心理念

**问题**：如何让 Telegram Bot 能够"记住"对话历史？

**解决方案**：利用 Claude Code CLI 自带的会话管理功能，而不是自己实现上下文管理。

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                         用户 (Telegram)                      │
└────────────────────────┬────────────────────────────────────┘
                         │ 发送消息
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Doraemon Bot (Python)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  channels/telegram.py                                │   │
│  │  - 接收 Telegram 消息                                │   │
│  │  - 权限检查                                          │   │
│  │  - 调用服务层                                        │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│               ↓                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  storage/database.py                                 │   │
│  │  - 获取/创建用户                                     │   │
│  │  - 获取/创建会话 → 返回 claude_session_id           │   │
│  │  - 保存消息历史                                      │   │
│  └────────────┬─────────────────────────────────────────┘   │
│               │                                              │
│               ↓                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  services/claude_code.py                             │   │
│  │  - 获取 session 锁 (防止并发)                       │   │
│  │  - 调用 Claude Code CLI                             │   │
│  │  - 管理进程生命周期                                  │   │
│  └────────────┬─────────────────────────────────────────┘   │
└───────────────┼──────────────────────────────────────────────┘
                │ subprocess 调用
                ↓
┌─────────────────────────────────────────────────────────────┐
│              Claude Code CLI (外部进程)                      │
│                                                              │
│  命令: claude --print --session-id <uuid> <message>         │
│                                                              │
│  1. 读取 ~/.claude/sessions/<uuid>.jsonl                    │
│  2. 加载完整对话历史                                         │
│  3. 调用 Claude API                                         │
│  4. 保存新的对话到 session 文件                             │
│  5. 返回响应                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 数据流详解

### 第一次对话

```
1. 用户发送: "你好"
   ↓
2. Telegram Bot 接收消息
   ↓
3. 查询数据库:
   - 用户存在吗? → 不存在，创建用户 (user_id=1)
   - 会话存在吗? → 不存在，创建会话
     * session_id = 1 (数据库内部 ID)
     * claude_session_id = "20d5abca-f650-..." (UUID)
   ↓
4. 保存用户消息到数据库:
   INSERT INTO messages (session_id=1, role='user', content='你好')
   ↓
5. 调用 Claude Code:
   claude --print --session-id "20d5abca-f650-..." "你好"
   ↓
6. Claude Code 执行:
   - 检查 ~/.claude/sessions/20d5abca-f650-....jsonl
   - 文件不存在 → 创建新 session
   - 调用 Claude API
   - 保存对话到 session 文件
   - 返回: "你好！我是 Doraemon..."
   ↓
7. 保存助手响应到数据库:
   INSERT INTO messages (session_id=1, role='assistant', content='你好！...')
   ↓
8. 发送响应到 Telegram
```

### 第二次对话（关键！）

```
1. 用户发送: "我刚才说了什么？"
   ↓
2. Telegram Bot 接收消息
   ↓
3. 查询数据库:
   - 用户存在吗? → 存在 (user_id=1)
   - 会话存在吗? → 存在
     * session_id = 1
     * claude_session_id = "20d5abca-f650-..." (同一个!)
   ↓
4. 保存用户消息到数据库
   ↓
5. 获取 session 锁 (关键步骤!)
   - 检查这个 claude_session_id 是否有锁
   - 如果有锁 → 等待
   - 如果没锁 → 获取锁，继续
   ↓
6. 调用 Claude Code (使用相同的 session_id):
   claude --print --session-id "20d5abca-f650-..." "我刚才说了什么？"
   ↓
7. Claude Code 执行:
   - 读取 ~/.claude/sessions/20d5abca-f650-....jsonl
   - 文件存在! → 加载历史对话:
     * User: "你好"
     * Assistant: "你好！我是 Doraemon..."
   - 调用 Claude API (带上完整历史)
   - Claude 看到历史，回答: "你说了'你好'"
   - 保存新对话到 session 文件
   - 返回响应
   ↓
8. 释放 session 锁
   ↓
9. 保存响应到数据库
   ↓
10. 发送响应到 Telegram
```

---

## 关键机制

### 1. Session ID 映射

**为什么需要两个 ID？**

```sql
sessions 表:
  id                  claude_session_id
  1                   20d5abca-f650-4a19-aa6d-4852d730ee5d
  2                   a3b2c1d4-5678-...
```

- `id`: 数据库主键，方便查询和关联
- `claude_session_id`: Claude Code 需要的 UUID，用于查找 session 文件

### 2. Session 锁机制

**问题**：用户快速发送两条消息会怎样？

```python
# 没有锁的情况:
消息1: claude --session-id "xxx" "hello"  ← 进程启动
消息2: claude --session-id "xxx" "world"  ← 进程启动
       ↑ 错误! Session ID already in use
```

**解决方案**：使用 asyncio.Lock

```python
_session_locks = defaultdict(asyncio.Lock)

async with _session_locks[session_id]:
    # 只有一个请求能进入这里
    # 其他请求会自动排队等待
    await call_claude_code()
```

```
消息1: 获取锁 → 调用 Claude → 释放锁
消息2: 等待锁 → 获取锁 → 调用 Claude → 释放锁
       ↑ 自动排队，不会冲突
```

### 3. 进程管理

**问题**：Claude Code 进程可能不会正常退出

**解决方案**：
1. 设置 120 秒超时
2. 超时后强制 kill 进程
3. finally 块确保清理

```python
try:
    stdout, stderr = await asyncio.wait_for(
        process.communicate(input=message.encode()),
        timeout=120
    )
except asyncio.TimeoutError:
    process.kill()  # 强制终止
    await process.wait()
finally:
    if process.returncode is None:
        process.kill()  # 确保清理
        await process.wait()
```

---

## 当前问题诊断

### 问题 1: "Session ID already in use"

**可能原因**：
1. ✅ 并发访问 → 已通过锁机制解决
2. ✅ 进程未清理 → 已添加强制清理
3. ❓ 锁机制未生效？

**检查方法**：
```bash
# 查看是否有僵尸 Claude Code 进程
ps aux | grep claude | grep session-id
```

### 问题 2: "Conflict: terminated by other getUpdates"

**原因**：多个 bot 实例同时运行

**检查方法**：
```bash
ps aux | grep "python.*main.py" | grep -v grep
```

**解决方法**：
```bash
./stop_bot.sh  # 停止所有实例
./restart_bot.sh  # 启动单个实例
```

---

## 正确的使用方式

### 启动 Bot

**❌ 错误方式**：
```bash
# 在多个终端运行
python main.py  # 终端 1
python main.py  # 终端 2  ← 冲突!
```

**✅ 正确方式**：
```bash
# 只在一个地方运行
./restart_bot.sh

# 或者
python main.py
```

### 停止 Bot

**❌ 错误方式**：
```bash
Ctrl+C  # 可能没有完全停止
```

**✅ 正确方式**：
```bash
./stop_bot.sh  # 确保所有实例都停止
```

### 查看状态

```bash
# 检查运行中的实例
ps aux | grep "python.*main.py" | grep -v grep

# 查看日志
tail -f ./data/logs/bot.log

# 查看最近的错误
tail -50 ./data/logs/bot.log | grep ERROR
```

---

## 调试技巧

### 1. 确认只有一个实例

```bash
ps aux | grep "python.*main.py" | grep -v grep | wc -l
# 应该输出: 1
```

### 2. 查看 session 状态

```bash
sqlite3 ./data/doraemon.db "SELECT * FROM sessions;"
```

### 3. 测试 Claude Code

```bash
# 在 bot 外部测试
echo "test" | claude --print --session-id test-123
```

### 4. 清理 session

```bash
python cleanup_sessions.py
# 选择选项 1: 重新生成所有 session ID
```

---

## 总结

**核心原理**：
1. 每个 Telegram 用户 → 一个 Claude Code session ID
2. 使用锁机制防止并发访问
3. Claude Code 自动管理对话历史
4. 我们的数据库只存储元数据和统计

**关键点**：
- ⚠️ 只能运行一个 bot 实例
- ⚠️ Session ID 必须唯一且持久
- ⚠️ 必须正确清理 Claude Code 进程

**如果还有问题**：
1. 停止所有实例: `./stop_bot.sh`
2. 清理 session: `python cleanup_sessions.py`
3. 重启: `./restart_bot.sh`
4. 查看日志: `tail -f ./data/logs/bot.log`
