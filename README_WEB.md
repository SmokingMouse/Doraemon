# Doraemon - Multi-Channel AI Assistant

基于 Claude Code 的多渠道 AI 助手，支持 Telegram 和 Web 界面。

## 功能特性

- 🤖 **多渠道支持**: Telegram Bot + Web 界面
- 💬 **流式响应**: 实时显示 AI 回复
- 🔄 **会话管理**: 多会话支持，随时切换
- 💭 **思考过程**: 可选显示 Claude 的思考过程
- 🔐 **安全认证**: JWT token 认证
- 📱 **响应式设计**: 支持桌面和移动端

## 快速开始

### 1. 安装依赖

```bash
# 使用 uv (推荐)
uv pip install -e .

# 或使用 pip
pip install -e .
```

### 2. 配置环境变量

创建 `.env` 文件:

```env
# Telegram 配置
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_ALLOWED_USERS=123456789,987654321
TELEGRAM_PROXY_URL=http://127.0.0.1:7890  # 可选

# Claude Code 配置
CLAUDE_CODE_PATH=claude

# 数据库配置
DATABASE_PATH=./data/doraemon.db

# Web 配置
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_SECRET_KEY=your-secret-key-here
WEB_ALLOWED_ORIGINS=http://localhost:5173
```

### 3. 数据库迁移 (如果从旧版本升级)

```bash
python scripts/migrate_to_multichannel.py ./data/doraemon.db
```

### 4. 启动服务

**方式 1: 同时启动 Telegram 和 Web**

```bash
python main.py
```

**方式 2: 使用启动脚本 (包含前端)**

```bash
bash scripts/start_all.sh
```

然后访问:
- Web 界面: http://localhost:5173/index.html
- API 文档: http://localhost:8765/docs
- 健康检查: http://localhost:8765/health

## 使用说明

### Telegram Bot

1. 在 Telegram 中搜索你的 bot
2. 发送 `/start` 开始对话
3. 可用命令:
   - `/new` - 创建新会话
   - `/clear` - 清空当前会话上下文
   - `/thinking` - 切换思考过程显示
   - `/sessions` - 查看会话列表
   - `/switch <编号>` - 切换会话
   - `/stats` - 查看使用统计

### Web 界面

1. 访问 http://localhost:5173/index.html
2. 使用默认账号登录:
   - 用户名: `admin`
   - 密码: `admin123`
3. 开始聊天！

## API 文档

### 认证

```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}

# 响应
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 会话管理

```bash
# 获取会话列表
GET /api/sessions
Authorization: Bearer <token>

# 创建新会话
POST /api/sessions
Authorization: Bearer <token>

# 获取消息历史
GET /api/messages/:session_id?limit=50
Authorization: Bearer <token>
```

### WebSocket

```javascript
// 连接
const ws = new WebSocket('ws://localhost:8765/ws');

// 认证
ws.send(JSON.stringify({
  type: 'auth',
  token: '<your-token>'
}));

// 发送消息
ws.send(JSON.stringify({
  type: 'message',
  content: 'Hello!'
}));

// 接收响应
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // data.type: 'status' | 'chunk' | 'complete' | 'error'
};
```

## 架构说明

```
Doraemon/
├── channels/          # 渠道层
│   ├── base.py       # 渠道抽象接口
│   ├── telegram.py   # Telegram Bot
│   └── web/          # Web 渠道
│       ├── app.py    # FastAPI 应用
│       ├── auth.py   # JWT 认证
│       ├── routes.py # REST API
│       └── websocket.py # WebSocket 处理
├── core/             # 核心逻辑
│   └── message_handler.py # 通用消息处理
├── services/         # 服务层
│   └── claude_code.py # Claude Code 调用
├── storage/          # 存储层
│   └── database.py   # SQLite 数据库
├── frontend/         # 前端
│   └── index.html    # 简单 Web 界面
└── main.py           # 主程序
```

## 开发

### 测试

```bash
# 测试 Web API
bash tests/test_api.sh

# 测试 WebSocket
python tests/test_websocket.py

# 测试 Telegram
python main.py
```

### 添加新渠道

1. 在 `channels/` 创建新文件
2. 继承 `BaseChannel` 类
3. 实现必要的方法
4. 使用 `MessageHandler` 处理消息

示例:

```python
from channels.base import BaseChannel, User
from core.message_handler import MessageHandler

class MyChannel(BaseChannel):
    def __init__(self, db):
        self.handler = MessageHandler(db)

    async def send_message(self, user: User, message: str):
        # 实现消息发送逻辑
        pass
```

## 故障排除

### Telegram Bot 无法连接

- 检查 `TELEGRAM_BOT_TOKEN` 是否正确
- 如果在中国，配置 `TELEGRAM_PROXY_URL`

### Web 界面无法连接

- 确保后端运行在 http://localhost:8765
- 检查 CORS 配置
- 查看浏览器控制台错误

### 数据库错误

- 运行迁移脚本: `python scripts/migrate_to_multichannel.py`
- 检查数据库文件权限

## 许可证

MIT

## 贡献

欢迎提交 Issue 和 Pull Request！
