# Next.js Frontend Quick Start

## 快速启动

### 方式 1：使用启动脚本（推荐）

```bash
bash scripts/start_nextjs.sh
```

### 方式 2：手动启动

```bash
# 终端 1：启动后端
python main.py

# 终端 2：启动前端
cd frontend-next
npm run dev
```

## 访问应用

打开浏览器访问：http://localhost:3000

默认账号：
- 用户名：`admin`
- 密码：`admin123`

## 功能测试

1. **登录测试**
   - 输入用户名和密码
   - 点击 Login 按钮
   - 应该跳转到聊天页面

2. **消息发送测试**
   - 在输入框输入消息
   - 按 Enter 或点击 Send 按钮
   - 应该看到消息显示在右侧（紫色背景）
   - 等待 AI 回复（左侧，白色背景）

3. **流式响应测试**
   - 发送消息后，应该看到 "Thinking..." 状态
   - 然后逐字显示 AI 回复
   - 回复完成后，可以继续发送下一条消息

4. **新建会话测试**
   - 点击左侧 "New Chat" 按钮
   - 消息列表应该清空
   - 可以开始新的对话

5. **退出登录测试**
   - 点击左侧 "Logout" 按钮
   - 应该跳转回登录页面

## 开发说明

### 项目结构

```
frontend-next/
├── app/                    # Next.js 页面
│   ├── login/             # 登录页
│   └── chat/              # 聊天页
├── components/            # React 组件
│   ├── auth/             # 认证相关
│   ├── chat/             # 聊天 UI
│   └── layout/           # 布局组件
├── lib/                   # 工具库
│   ├── api.ts            # API 客户端
│   └── websocket.ts      # WebSocket 管理
├── hooks/                 # 自定义 Hooks
├── store/                 # Zustand 状态管理
└── types/                 # TypeScript 类型
```

### 技术栈

- **Next.js 15** - React 框架（App Router）
- **TypeScript** - 类型安全
- **Tailwind CSS 4** - 样式框架
- **Zustand** - 状态管理
- **WebSocket** - 实时通信

### 环境变量

`.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8765
NEXT_PUBLIC_WS_URL=ws://localhost:8765/ws
```

### 常用命令

```bash
# 开发模式
npm run dev

# 生产构建
npm run build

# 启动生产服务器
npm start

# 代码检查
npm run lint
```

## 对比原版

| 特性 | 原版 (Vite) | Next.js 版本 |
|------|------------|-------------|
| 框架 | 原生 HTML/JS | Next.js + React |
| 样式 | 原生 CSS | Tailwind CSS |
| 状态管理 | 无 | Zustand |
| 类型安全 | 无 | TypeScript |
| 组件化 | 无 | React 组件 |
| 热重载 | 有 | 有 |
| 开发体验 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 已知问题

1. **会话管理**：目前只有 "New Chat" 功能，完整的会话列表和切换功能待实现
2. **Markdown 渲染**：AI 回复暂时以纯文本显示，Markdown 渲染待添加
3. **代码高亮**：代码块暂时无高亮，待集成语法高亮库

## 下一步优化

- [ ] 实现完整的会话管理（列表、切换、删除）
- [ ] 添加 Markdown 渲染（react-markdown）
- [ ] 添加代码高亮（prism-react-renderer）
- [ ] 添加深色模式
- [ ] 优化移动端体验
- [ ] 添加消息搜索功能
- [ ] 添加文件上传功能
