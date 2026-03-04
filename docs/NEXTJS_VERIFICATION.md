# Next.js Frontend Verification Checklist

## 环境检查

- [x] Node.js 和 npm 已安装
- [x] 依赖已安装（`npm install`）
- [x] 环境变量已配置（`.env.local`）
- [x] 后端服务正在运行（http://localhost:8765/health）
- [x] 前端服务正在运行（http://localhost:3000）

## 功能测试

### 1. 登录功能
- [ ] 访问 http://localhost:3000 自动跳转到 /login
- [ ] 输入错误密码显示错误提示
- [ ] 输入正确密码（admin/admin123）成功登录
- [ ] 登录后跳转到 /chat
- [ ] 刷新页面保持登录状态

### 2. 聊天界面
- [ ] 侧边栏正常显示
- [ ] 消息列表区域正常显示
- [ ] 输入框正常显示
- [ ] 布局响应式（桌面/移动端）

### 3. 消息发送
- [ ] 输入消息并点击 Send 按钮
- [ ] 消息显示在右侧（紫色背景）
- [ ] 按 Enter 键发送消息
- [ ] Shift+Enter 换行
- [ ] 发送中禁用输入框和按钮

### 4. 流式响应
- [ ] 发送消息后显示 "Thinking..." 状态
- [ ] AI 回复逐字显示
- [ ] 显示闪烁光标动画
- [ ] 回复完成后消息固定
- [ ] 可以继续发送下一条消息

### 5. WebSocket 连接
- [ ] 打开页面自动连接 WebSocket
- [ ] 控制台显示 "WebSocket connected"
- [ ] 控制台显示 "Authentication successful"
- [ ] 关闭页面自动断开连接

### 6. 会话管理
- [ ] 点击 "New Chat" 清空消息列表
- [ ] 可以开始新的对话

### 7. 退出登录
- [ ] 点击 "Logout" 按钮
- [ ] 跳转到登录页面
- [ ] Token 被清除
- [ ] 访问 /chat 自动跳转到 /login

## UI 测试

### 样式检查
- [ ] 登录页面渐变背景正确
- [ ] 用户消息紫色背景（#667eea）
- [ ] AI 消息白色背景 + 灰色边框
- [ ] 按钮 hover 效果正常
- [ ] 输入框 focus 效果正常

### 响应式布局
- [ ] 桌面端：侧边栏 + 聊天区域
- [ ] 移动端：全屏聊天（侧边栏可折叠）
- [ ] 消息列表自动滚动到底部

### 交互体验
- [ ] 输入框自动聚焦
- [ ] 消息发送后输入框清空
- [ ] 流式消息平滑显示
- [ ] 无明显卡顿或闪烁

## 错误处理

### 网络错误
- [ ] 后端未启动时显示错误提示
- [ ] WebSocket 连接失败时显示错误
- [ ] 登录失败显示错误提示

### 边缘情况
- [ ] 发送空消息被阻止
- [ ] 发送中不能重复发送
- [ ] Token 过期自动跳转登录页

## 性能检查

- [ ] 首次加载时间 < 2 秒
- [ ] 页面切换流畅
- [ ] 消息渲染流畅
- [ ] 无内存泄漏（长时间使用）

## 浏览器兼容性

- [ ] Chrome/Edge（最新版）
- [ ] Firefox（最新版）
- [ ] Safari（最新版）

## 开发工具

- [ ] 无 TypeScript 编译错误
- [ ] 无 ESLint 警告
- [ ] 无控制台错误（除预期的）
- [ ] React DevTools 正常工作

## 文档检查

- [x] README.md 已创建
- [x] NEXTJS_QUICKSTART.md 已创建
- [x] NEXTJS_IMPLEMENTATION.md 已创建
- [x] 代码注释清晰

## 部署准备

- [ ] `npm run build` 成功
- [ ] 生产构建无错误
- [ ] 环境变量配置文档完整
- [ ] 启动脚本可用

## 测试命令

```bash
# 检查后端健康
curl http://localhost:8765/health

# 测试登录 API
curl -X POST http://localhost:8765/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 检查前端页面
curl http://localhost:3000

# 检查 TypeScript 编译
cd frontend-next && npx tsc --noEmit

# 检查 ESLint
cd frontend-next && npm run lint
```

## 已知问题

1. **会话列表**: 目前只有 "New Chat" 功能，完整的会话列表待实现
2. **Markdown 渲染**: AI 回复暂时以纯文本显示
3. **代码高亮**: 代码块暂时无高亮

## 下一步

1. [ ] 完成所有功能测试
2. [ ] 修复发现的 bug
3. [ ] 添加 Markdown 渲染
4. [ ] 添加代码高亮
5. [ ] 实现完整的会话管理
