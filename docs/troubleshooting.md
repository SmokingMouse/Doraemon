# 故障排查指南

## 常见问题

### 1. Telegram 超时错误 (TimedOut)

**错误信息**：
```
telegram.error.TimedOut: Timed out
```

**可能原因**：
1. 网络连接问题（特别是在中国大陆）
2. Claude Code 响应时间过长
3. Telegram API 服务器响应慢

**解决方案**：

#### 方案 1: 配置代理（推荐）

如果你在中国大陆或需要代理访问 Telegram：

1. 确保已安装 socks 支持：
   ```bash
   uv pip install "python-telegram-bot[socks]"
   ```

2. 在 `.env` 文件中配置代理：
   ```bash
   # SOCKS5 代理
   TELEGRAM_PROXY_URL=socks5://127.0.0.1:1080

   # 或 HTTP 代理
   TELEGRAM_PROXY_URL=http://127.0.0.1:7890
   ```

3. 重启 bot

#### 方案 2: 调整超时设置

在 `.env` 文件中增加超时时间：
```bash
TELEGRAM_READ_TIMEOUT=60
TELEGRAM_WRITE_TIMEOUT=60
TELEGRAM_CONNECT_TIMEOUT=20
```

#### 方案 3: 检查网络连接

测试 Telegram API 连接：
```bash
curl -v https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

### 2. Claude Code 超时

**错误信息**：
```
Request timed out. Please try again.
```

**原因**：Claude Code CLI 执行超过 120 秒

**解决方案**：
1. 检查 Claude Code 是否正常工作：
   ```bash
   claude --print "hello"
   ```

2. 检查是否有大量历史消息导致处理变慢
3. 考虑清理旧的 session 文件：
   ```bash
   ls -lh ~/.claude/sessions/
   ```

### 3. 代理配置问题

**常见代理格式**：
- SOCKS5: `socks5://host:port`
- SOCKS5 with auth: `socks5://user:pass@host:port`
- HTTP: `http://host:port`
- HTTPS: `https://host:port`

**测试代理**：
```bash
# 测试 SOCKS5 代理
curl --socks5 127.0.0.1:1080 https://api.telegram.org

# 测试 HTTP 代理
curl --proxy http://127.0.0.1:7890 https://api.telegram.org
```

### 4. 响应已保存但未发送

如果遇到超时错误，响应已经保存到数据库，可以：

1. 查看数据库中的消息：
   ```bash
   sqlite3 ./data/doraemon.db "SELECT * FROM messages ORDER BY created_at DESC LIMIT 5;"
   ```

2. 未来版本会添加 `/history` 命令来查看历史消息

### 5. Bot 无响应

**检查清单**：
1. Bot 是否正在运行？
   ```bash
   ps aux | grep python | grep doraemon
   ```

2. 检查日志：
   ```bash
   tail -f ./data/logs/doraemon.log
   ```

3. 检查 Telegram Bot Token 是否正确：
   ```bash
   curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
   ```

4. 检查用户是否在允许列表中（如果配置了 TELEGRAM_ALLOWED_USERS）

## 调试技巧

### 启用详细日志

修改 `utils/logger.py`，将日志级别改为 DEBUG：
```python
logger.add(sys.stderr, level="DEBUG", ...)
```

### 测试 Claude Code 集成

```bash
source .venv/bin/activate
python -c "
import asyncio
from services.claude_code import ask_claude

async def test():
    response = await ask_claude('hello', session_id='test-123')
    print(response)

asyncio.run(test())
"
```

### 测试数据库连接

```bash
source .venv/bin/activate
python -c "
import asyncio
from storage.database import Database

async def test():
    db = Database('./data/doraemon.db')
    await db.init()
    print('Database OK')

asyncio.run(test())
"
```

## 性能优化建议

1. **定期清理旧 session**：
   - Claude Code 的 session 文件会随时间增长
   - 考虑定期归档或删除旧 session

2. **监控响应时间**：
   - 如果 Claude Code 响应变慢，可能需要优化 prompt 或清理历史

3. **数据库维护**：
   - 定期备份数据库
   - 考虑添加索引以提高查询速度

## 获取帮助

如果问题仍未解决：
1. 查看完整日志：`cat ./data/logs/doraemon.log`
2. 检查 GitHub Issues
3. 提供错误日志和配置信息（注意隐藏敏感信息）
