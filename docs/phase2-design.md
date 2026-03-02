# Phase 2 记忆系统技术方案

## 1. 核心机制

### 问题
Phase 1 中，每次调用 `claude --print "message"` 都是独立的，Claude 无法记住之前的对话。

### 解决方案
使用 Claude Code CLI 的 `--session-id` 参数：
```bash
claude --print --session-id "unique-session-id" "message"
```

Claude Code 会在本地维护这个 session 的完整上下文，包括：
- 所有历史消息
- 对话状态
- 工作目录状态（如果涉及文件操作）

## 2. 数据流程

```
用户发送消息 (Telegram)
    ↓
获取/创建用户 (Database)
    ↓
获取/创建会话 (Database) → 返回 (session_id, claude_session_id)
    ↓
保存用户消息 (Database)
    ↓
调用 Claude Code CLI
    claude --print --session-id "uuid" "message"
    ↓
Claude Code 读取本地 session 文件
    ~/.claude/sessions/{session-id}.jsonl
    ↓
Claude 基于完整历史生成响应
    ↓
返回响应
    ↓
保存助手响应 (Database)
    ↓
发送给用户 (Telegram)
```

## 3. 数据库设计

### sessions 表
```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY,           -- 内部 session ID
    user_id INTEGER,                  -- 关联用户
    claude_session_id TEXT UNIQUE,    -- Claude Code 的 session ID (UUID)
    created_at TIMESTAMP,
    last_active TIMESTAMP
);
```

**关键点**：
- `id`: 我们的内部 session ID，用于关联消息
- `claude_session_id`: 传递给 Claude Code 的 UUID，Claude Code 用它来查找本地会话文件

### 为什么需要两个 ID？
- `id`: 数据库主键，方便查询和关联
- `claude_session_id`: Claude Code 需要的标识符，必须是全局唯一的 UUID

## 4. 会话生命周期

### 创建会话
```python
# 第一次对话时
session_id, claude_session_id = await db.get_or_create_session(user_id)
# 生成: session_id=1, claude_session_id="72df8e4c-4985-4b33-aa04-9675059fb3ad"
```

### 使用会话
```python
# 后续对话时
response = await ask_claude(message, session_id=claude_session_id)
# Claude Code 会读取 ~/.claude/sessions/72df8e4c-4985-4b33-aa04-9675059fb3ad.jsonl
```

### 会话持久化
- **Claude Code 侧**: 会话数据存储在 `~/.claude/sessions/` 目录
- **我们的数据库**: 存储会话元数据和消息历史（用于统计和未来的高级功能）

## 5. 与 Phase 1 的对比

### Phase 1 (无记忆)
```python
# 每次都是新对话
response = await ask_claude("今天天气怎么样？")
response = await ask_claude("那明天呢？")  # Claude 不知道你在问天气
```

### Phase 2 (有记忆)
```python
# 第一次
response = await ask_claude("今天天气怎么样？", session_id="uuid-123")
# 第二次 - 使用相同的 session_id
response = await ask_claude("那明天呢？", session_id="uuid-123")
# Claude 知道你在继续问天气！
```

## 6. 优势

### 简洁性
- 不需要自己实现复杂的上下文管理
- 不需要手动拼接历史消息
- 不需要担心 token 限制和截断策略

### 可靠性
- Claude Code 已经处理好了所有边缘情况
- 会话数据自动持久化到本地文件
- 支持长对话和复杂上下文

### 扩展性
- 未来可以添加多会话管理（Phase 4）
- 可以基于数据库中的历史做分析和统计
- 可以实现会话导出、分享等功能

## 7. 实现细节

### services/claude_code.py
```python
async def ask_claude(message: str, session_id: str = None) -> str:
    cmd = [config.CLAUDE_CODE_PATH, "--print"]
    if session_id:
        cmd.extend(["--session-id", session_id])  # 关键：传递 session ID

    process = await asyncio.create_subprocess_exec(*cmd, ...)
    # ...
```

### storage/database.py
```python
async def get_or_create_session(self, user_id: int) -> tuple[int, str]:
    # 查找现有会话
    row = await db.execute("SELECT id, claude_session_id FROM sessions ...")
    if row:
        return row[0], row[1]  # 返回现有的 session ID

    # 创建新会话
    claude_session_id = str(uuid.uuid4())  # 生成 UUID
    cursor = await db.execute(
        "INSERT INTO sessions (user_id, claude_session_id) VALUES (?, ?)",
        (user_id, claude_session_id)
    )
    return cursor.lastrowid, claude_session_id
```

## 8. 用户体验

### 对话示例
```
用户: 我想学 Python
Claude: 太好了！Python 是一门很适合初学者的语言...

用户: 从哪里开始？
Claude: 基于你想学 Python，我建议从以下几个方面开始...
         ↑ Claude 记得之前的对话！
```

### 统计功能
```
用户: /stats
Bot: 📊 你的统计信息
     💬 消息数: 15
     🔄 会话数: 1
     📅 首次使用: 2026-03-02 14:32:30
     ⏰ 最后活跃: 2026-03-02 15:00:00
```

## 9. 未来扩展

### Phase 3: 流式响应
- 使用 `--output-format=stream-json`
- 实时显示 Claude 的回复

### Phase 4: 多会话管理
- 用户可以创建多个会话（工作、学习、闲聊）
- 在不同会话间切换
- 每个会话有独立的上下文

### 高级记忆功能
- 基于数据库历史做语义搜索
- 自动提取重要信息
- 构建用户画像和偏好
