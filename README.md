# Doraemon - Multi-Channel AI Assistant

基于 Claude Code 的多渠道 AI 助手，支持 Telegram Bot 和 Web 界面。

## 🚀 快速开始

```bash
# 1. 安装依赖
uv pip install -e .

# 2. 启动服务
bash scripts/start_all.sh

# 3. 访问 Web 界面
# http://localhost:5173/index.html
# 用户名: admin, 密码: admin123
```

详细说明请查看 [快速启动指南](QUICKSTART.md)

## 📚 文档

### 用户文档
- [快速启动指南](QUICKSTART.md) - 5 分钟上手
- [Web 渠道使用文档](README_WEB.md) - 完整功能说明
- [项目结构](PROJECT_STRUCTURE.md) - 代码组织

### 开发文档
- [实现总结](docs/implementation/IMPLEMENTATION_SUMMARY.md) - 实现细节
- [Web 实现文档](docs/implementation/WEB_IMPLEMENTATION.md) - Web 架构
- [验证清单](docs/implementation/VERIFICATION_CHECKLIST.md) - 功能检查

## ✨ 功能特性

- 🤖 **多渠道支持**: Telegram Bot + Web 界面
- 💬 **流式响应**: 实时显示 AI 回复
- 🔄 **会话管理**: 多会话支持，随时切换
- 💭 **思考过程**: 可选显示 Claude 的思考过程
- 🔐 **安全认证**: JWT token 认证
- 📱 **响应式设计**: 支持桌面和移动端

## 🏗️ 架构

```
Channels Layer (Telegram, Web)
    ↓
BaseChannel (抽象接口)
    ↓
MessageHandler (通用消息处理)
    ↓
Services (claude_code, database)
```

详细架构请查看 [项目结构](PROJECT_STRUCTURE.md)

## 📦 项目结构

```
Doraemon/
├── channels/       # 渠道层 (Telegram, Web)
├── core/           # 核心逻辑
├── services/       # 服务层
├── storage/        # 数据库
├── frontend/       # Web 前端
├── scripts/        # 运维脚本
├── tests/          # 测试文件
└── docs/           # 文档
```

## 🔧 配置

创建 `.env` 文件:

```env
# Telegram 配置
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_ALLOWED_USERS=123456789

# Web 配置
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_SECRET_KEY=your-secret-key
WEB_ALLOWED_ORIGINS=http://localhost:5173

# Claude Code
CLAUDE_CODE_PATH=claude

# 数据库
DATABASE_PATH=./data/doraemon.db
```

## 🧪 测试

```bash
# 测试 Web API
bash tests/test_api.sh

# 测试 WebSocket
python tests/test_websocket.py

# 测试 Telegram
python main.py
```

## 📖 使用说明

### Telegram Bot

1. 在 Telegram 搜索你的 bot
2. 发送 `/start` 开始对话
3. 可用命令: `/new`, `/clear`, `/thinking`, `/sessions`, `/stats`

### Web 界面

1. 访问 http://localhost:5173/index.html
2. 使用默认账号登录 (admin/admin123)
3. 开始聊天！

### API

- API 文档: http://localhost:8765/docs
- 健康检查: http://localhost:8765/health
- WebSocket: ws://localhost:8765/ws

详细 API 说明请查看 [Web 文档](README_WEB.md)

## 🛠️ 开发

### 添加新渠道

1. 在 `channels/` 创建新文件
2. 继承 `BaseChannel` 类
3. 实现必要方法
4. 使用 `MessageHandler` 处理消息

示例代码请查看 [项目结构](PROJECT_STRUCTURE.md)

### 运行测试

```bash
# 所有测试
pytest tests/

# 特定测试
python tests/test_web.py
```

## 📝 更新日志

### v0.2.0 (2024-03-04)
- ✅ 添加 Web 渠道支持
- ✅ 重构为多渠道架构
- ✅ 数据库支持多渠道
- ✅ 完整的 REST API 和 WebSocket
- ✅ 简单的 Web 界面

### v0.1.0
- ✅ Telegram Bot 基础功能
- ✅ Claude Code 集成
- ✅ 会话管理
- ✅ 流式响应

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT

## 🙏 致谢

- [Claude Code](https://github.com/anthropics/claude-code) - AI 助手核心
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) - Telegram Bot 框架
- [FastAPI](https://fastapi.tiangolo.com/) - Web 框架

---

**快速链接**:
- [快速启动](QUICKSTART.md)
- [完整文档](README_WEB.md)
- [项目结构](PROJECT_STRUCTURE.md)
- [实现细节](docs/implementation/IMPLEMENTATION_SUMMARY.md)
