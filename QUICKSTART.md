# 🚀 快速启动指南

## 1. 安装依赖

```bash
uv pip install -e .
```

## 2. 配置 (可选)

编辑 `.env` 文件，或使用默认配置。

## 3. 启动服务

```bash
bash scripts/start_all.sh
```

## 4. 访问

打开浏览器访问: **http://localhost:5173/index.html**

默认账号:
- 用户名: `admin`
- 密码: `admin123`

## 5. 开始聊天！

输入消息，享受与 Claude 的对话 🤖

---

## 其他访问方式

### API 文档
http://localhost:8765/docs

### Telegram Bot
如果配置了 `TELEGRAM_BOT_TOKEN`，Telegram Bot 也会同时运行。

---

## 停止服务

按 `Ctrl+C` 停止所有服务。

---

## 故障排除

### 端口被占用
修改 `.env` 中的 `WEB_PORT` 和前端端口。

### 无法连接
检查防火墙设置，确保端口 8000 和 3000 开放。

### 数据库错误
运行迁移: `python scripts/migrate_to_multichannel.py ./data/doraemon.db`

---

更多信息请查看 [README_WEB.md](README_WEB.md)
