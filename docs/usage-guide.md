# Doraemon 使用指南

## 快速开始

### 1. 启动 Bot

```bash
./restart_bot.sh
```

**重要**：
- ✅ 使用 `restart_bot.sh` 启动（已自动处理环境变量）
- ❌ 不要直接运行 `python main.py`（会继承 CLAUDECODE 环境变量）

### 2. 停止 Bot

```bash
./stop_bot.sh
```

### 3. 查看状态

```bash
# 查看日志
tail -f ./data/logs/bot.log

# 检查进程
ps aux | grep "python.*main.py" | grep -v grep

# 查看统计
sqlite3 ./data/doraemon.db "SELECT * FROM sessions;"
```

---

## 常见问题

### Q1: "Session ID already in use" 错误

**原因**：旧的 session ID 可能有问题

**解决**：
```bash
python cleanup_sessions.py
# 选择选项 1: 重新生成所有 session ID
./restart_bot.sh
```

### Q2: "Conflict: terminated by other getUpdates" 错误

**原因**：多个 bot 实例在运行

**解决**：
```bash
./stop_bot.sh  # 停止所有实例
./restart_bot.sh  # 启动单个实例
```

### Q3: "Claude Code cannot be launched inside another Claude Code session"

**原因**：在 Claude Code 会话内启动了 bot

**解决**：
- ✅ 使用 `./restart_bot.sh`（已自动 unset CLAUDECODE）
- ❌ 不要直接运行 `python main.py`

### Q4: Bot 无响应

**检查清单**：
1. Bot 是否在运行？
   ```bash
   ps aux | grep "python.*main.py" | grep -v grep
   ```

2. 查看日志错误：
   ```bash
   tail -50 ./data/logs/bot.log | grep ERROR
   ```

3. 检查代理配置（如果在中国）：
   ```bash
   cat .env | grep PROXY
   ```

4. 测试 Claude Code：
   ```bash
   unset CLAUDECODE
   echo "test" | claude --print
   ```

---

## 正确的工作流程

### 开发/调试

```bash
# 1. 停止现有实例
./stop_bot.sh

# 2. 修改代码
vim channels/telegram.py

# 3. 重启
./restart_bot.sh

# 4. 查看日志
tail -f ./data/logs/bot.log
```

### 日常使用

```bash
# 启动
./restart_bot.sh

# 后台运行，查看日志
tail -f ./data/logs/bot.log

# 停止
./stop_bot.sh
```

---

## 环境变量说明

### 必需配置

```bash
# .env 文件
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_ALLOWED_USERS=your_telegram_id
```

### 可选配置

```bash
# 代理（中国大陆用户需要）
TELEGRAM_PROXY_URL=socks5://127.0.0.1:1080

# 超时设置
TELEGRAM_READ_TIMEOUT=30
TELEGRAM_WRITE_TIMEOUT=30
TELEGRAM_CONNECT_TIMEOUT=10

# Claude Code 路径
CLAUDE_CODE_PATH=claude

# 数据库路径
DATABASE_PATH=./data/doraemon.db
```

---

## 维护任务

### 定期清理

```bash
# 清理旧日志（保留最近 7 天）
find ./data/logs -name "*.log" -mtime +7 -delete

# 备份数据库
cp ./data/doraemon.db ./data/doraemon.db.backup.$(date +%Y%m%d)

# 查看数据库大小
du -h ./data/doraemon.db
```

### 性能监控

```bash
# 查看消息统计
sqlite3 ./data/doraemon.db "SELECT COUNT(*) FROM messages;"

# 查看用户数
sqlite3 ./data/doraemon.db "SELECT COUNT(*) FROM users;"

# 查看会话数
sqlite3 ./data/doraemon.db "SELECT COUNT(*) FROM sessions;"
```

---

## 故障排查流程

1. **检查进程**
   ```bash
   ps aux | grep "python.*main.py" | grep -v grep
   ```

2. **查看最新错误**
   ```bash
   tail -50 ./data/logs/bot.log | grep ERROR
   ```

3. **停止所有实例**
   ```bash
   ./stop_bot.sh
   ```

4. **清理 session**
   ```bash
   python cleanup_sessions.py
   ```

5. **重启**
   ```bash
   ./restart_bot.sh
   ```

6. **测试**
   - 在 Telegram 发送消息
   - 查看日志：`tail -f ./data/logs/bot.log`

---

## 高级技巧

### 在后台运行

```bash
# 使用 nohup（restart_bot.sh 已自动使用）
nohup python main.py > ./data/logs/bot.log 2>&1 &

# 或使用 screen
screen -S doraemon
python main.py
# Ctrl+A, D 分离会话
```

### 自动启动（systemd）

创建 `~/.config/systemd/user/doraemon.service`：

```ini
[Unit]
Description=Doraemon Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/smokingmouse/python/ai/Doraemon
Environment="CLAUDECODE="
ExecStart=/home/smokingmouse/python/ai/Doraemon/.venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

启用：
```bash
systemctl --user enable doraemon
systemctl --user start doraemon
systemctl --user status doraemon
```

---

## 更新日志

### 2026-03-03
- ✅ 修复：unset CLAUDECODE 环境变量
- ✅ 修复：进程管理和清理
- ✅ 修复：session 锁机制
- ✅ 添加：cleanup_sessions.py 工具
- ✅ 添加：stop_bot.sh 脚本
- ✅ 文档：architecture.md, troubleshooting.md

### 2026-03-02
- ✅ Phase 2: 记忆系统实现
- ✅ 代理支持
- ✅ 超时处理

### 2026-03-02
- ✅ Phase 1: MVP 实现
- ✅ Telegram Bot 基础功能
- ✅ Claude Code 集成
- ✅ SQLite 数据库

---

## 获取帮助

1. 查看文档：
   - `docs/architecture.md` - 系统架构
   - `docs/troubleshooting.md` - 故障排查
   - `docs/phase2-design.md` - Phase 2 设计

2. 查看日志：
   ```bash
   tail -100 ./data/logs/bot.log
   ```

3. 检查配置：
   ```bash
   cat .env
   ```

4. 测试组件：
   ```bash
   # 测试数据库
   python -c "import asyncio; from storage.database import Database; asyncio.run(Database('./data/doraemon.db').init())"

   # 测试 Claude Code
   unset CLAUDECODE && echo "test" | claude --print
   ```
