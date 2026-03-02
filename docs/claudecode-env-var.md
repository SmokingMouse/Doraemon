# CLAUDECODE 环境变量详解

## 什么是 CLAUDECODE？

`CLAUDECODE` 是 Claude Code CLI 设置的一个环境变量，用于标识当前进程是否在 Claude Code 会话中运行。

## 作用

### 1. 防止嵌套会话

**问题场景**：
```bash
# 你在 Claude Code 会话中
claude> python script.py
  └─ script.py 内部调用: subprocess.run(["claude", "--print", "hello"])
      └─ 错误! 嵌套会话会导致资源冲突
```

**Claude Code 的检查逻辑**：
```python
# Claude Code 启动时（伪代码）
if os.environ.get('CLAUDECODE'):
    print("Error: Claude Code cannot be launched inside another Claude Code session.")
    print("Nested sessions share runtime resources and will crash all active sessions.")
    print("To bypass this check, unset the CLAUDECODE environment variable.")
    sys.exit(1)
```

### 2. 资源共享问题

嵌套会话会导致：
- **端口冲突**：Claude Code 使用特定端口（如 SSE_PORT）
- **文件锁冲突**：共享配置文件和 session 文件
- **内存冲突**：共享运行时资源
- **状态混乱**：两个会话可能互相干扰

## 环境变量详情

### 相关的 Claude Code 环境变量

```bash
# 当前会话中的 Claude Code 环境变量
env | grep CLAUDE

# 输出示例:
CLAUDECODE=1                                    # 标识在 Claude Code 会话中
CLAUDE_CODE_ENTRYPOINT=cli                      # 入口点类型
CLAUDE_CODE_SSE_PORT=21483                      # Server-Sent Events 端口
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1      # 禁用非必要流量
```

### CLAUDECODE 的值

```bash
CLAUDECODE=1    # 在 Claude Code 会话中
CLAUDECODE=     # 未设置（不在会话中）
```

## 我们的问题

### 问题场景

```
1. 你在终端启动 Claude Code:
   $ claude
   └─ 设置: CLAUDECODE=1

2. 在 Claude Code 中启动 Bot:
   claude> python main.py
   └─ Bot 继承环境变量: CLAUDECODE=1

3. Bot 尝试调用 Claude Code:
   subprocess.run(["claude", "--print", "hello"])
   └─ Claude Code 检查到 CLAUDECODE=1
   └─ 错误: "cannot be launched inside another session"
```

### 错误信息

```
Error: Claude Code cannot be launched inside another Claude Code session.
Nested sessions share runtime resources and will crash all active sessions.
To bypass this check, unset the CLAUDECODE environment variable.
```

## 解决方案

### 方案 1: 在启动脚本中 unset（推荐）

```bash
# restart_bot.sh
#!/bin/bash

# 取消 CLAUDECODE 环境变量
unset CLAUDECODE

# 启动 bot
python main.py
```

**优点**：
- ✅ 简单直接
- ✅ 不影响其他环境变量
- ✅ 只影响 bot 进程

### 方案 2: 在 Python 代码中 unset

```python
# main.py
import os

# 在启动前取消环境变量
if 'CLAUDECODE' in os.environ:
    del os.environ['CLAUDECODE']

# 然后启动 bot
asyncio.run(main())
```

**优点**：
- ✅ 代码层面控制
- ✅ 不依赖启动脚本

**缺点**：
- ❌ 可能影响子进程
- ❌ 不够优雅

### 方案 3: 在子进程调用时 unset

```python
# services/claude_code.py
import os

async def ask_claude(message: str, session_id: str = None):
    # 创建新的环境变量字典，不包含 CLAUDECODE
    env = os.environ.copy()
    env.pop('CLAUDECODE', None)  # 移除 CLAUDECODE

    process = await asyncio.create_subprocess_exec(
        "claude", "--print", "--session-id", session_id,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env  # 使用修改后的环境变量
    )
```

**优点**：
- ✅ 精确控制
- ✅ 只影响 Claude Code 调用
- ✅ 不影响 bot 本身的环境

**缺点**：
- ❌ 需要复制整个环境变量字典
- ❌ 代码稍复杂

### 我们采用的方案

**组合方案**：在启动脚本中 unset（方案 1）

```bash
# restart_bot.sh
unset CLAUDECODE
python main.py
```

**原因**：
- 简单有效
- 在进程启动前就解决问题
- 不需要修改 Python 代码

## 验证

### 检查环境变量

```bash
# 在 bot 进程中检查
ps aux | grep "python.*main.py"
# 获取 PID，比如 12345

# 查看进程的环境变量
cat /proc/12345/environ | tr '\0' '\n' | grep CLAUDE
```

### 测试是否能调用 Claude Code

```bash
# 在 bot 外部测试
unset CLAUDECODE
echo "test" | claude --print
# 应该正常工作

# 在 bot 内部测试（有 CLAUDECODE）
export CLAUDECODE=1
echo "test" | claude --print
# 应该报错: "cannot be launched inside another session"
```

## 其他相关环境变量

### CLAUDE_CODE_SSE_PORT

```bash
CLAUDE_CODE_SSE_PORT=21483
```

**作用**：Server-Sent Events 端口，用于流式输出

**冲突**：如果嵌套会话，两个进程会尝试使用同一个端口

### CLAUDE_CODE_ENTRYPOINT

```bash
CLAUDE_CODE_ENTRYPOINT=cli
```

**作用**：标识 Claude Code 的入口点类型
- `cli`: 命令行界面
- `api`: API 模式
- `agent`: Agent 模式

### CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC

```bash
CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1
```

**作用**：禁用非必要的网络流量（如遥测、更新检查）

## 最佳实践

### 1. 在 Claude Code 外部运行 Bot

```bash
# ❌ 错误方式
claude> python main.py

# ✅ 正确方式
# 在普通终端运行
$ ./restart_bot.sh
```

### 2. 使用启动脚本

```bash
# restart_bot.sh
#!/bin/bash
unset CLAUDECODE
unset CLAUDE_CODE_SSE_PORT
unset CLAUDE_CODE_ENTRYPOINT
python main.py
```

### 3. 检查环境

```python
# main.py
import os
import sys

if os.environ.get('CLAUDECODE'):
    print("Warning: Running inside Claude Code session")
    print("This may cause issues. Consider using restart_bot.sh")
    # 可以选择退出或继续
```

## 调试技巧

### 查看所有环境变量

```bash
# 当前 shell
env | sort

# 特定进程
cat /proc/<PID>/environ | tr '\0' '\n' | sort
```

### 临时测试

```bash
# 临时 unset
unset CLAUDECODE
python main.py

# 临时 set
export CLAUDECODE=1
python main.py
```

### 在 Python 中检查

```python
import os

print("CLAUDECODE:", os.environ.get('CLAUDECODE', 'not set'))
print("All CLAUDE vars:")
for key, value in os.environ.items():
    if 'CLAUDE' in key:
        print(f"  {key}={value}")
```

## 总结

### 关键点

1. **CLAUDECODE=1** 表示在 Claude Code 会话中
2. **防止嵌套** 是为了避免资源冲突
3. **解决方法** 是在启动 bot 前 `unset CLAUDECODE`
4. **最佳实践** 是使用 `restart_bot.sh` 启动

### 记住

- ✅ 使用 `./restart_bot.sh` 启动 bot
- ❌ 不要在 Claude Code 会话中直接运行 `python main.py`
- ✅ 如果必须在 Claude Code 中测试，先 `unset CLAUDECODE`

这就是 CLAUDECODE 环境变量的完整说明！
