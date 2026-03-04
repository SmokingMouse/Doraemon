# 智能回复过滤功能

## 功能说明

在 AI 回复时：
- **过程中**：实时 stream 展示思考过程（💭）和工具调用（🔧）
- **完成后**：只保留最终回复，隐藏思考/工具过程

## 实现原理

### 后端（Python）

1. **流式输出**：`services/claude_code.py` 的 `_call_claude_process_streaming` 方法实时推送所有内容
2. **内容提取**：`_extract_final_response` 方法从完整响应中提取最终回复
3. **完成事件**：WebSocket 的 `complete` 事件发送提取后的纯净内容

### 前端（TypeScript）

1. **流式展示**：`StreamingMessage` 组件实时显示所有内容（包括思考/工具）
2. **最终保存**：`completeStreaming` 方法接收后端传来的纯净内容并保存到消息列表
3. **状态管理**：Zustand store 管理 streaming 和 messages 两个状态

## 内容识别规则

### 思考块
```
💭 **思考过程：**
思考内容...

---
```

### 工具调用
```
🔧 调用工具: ToolName
✅ ToolName 完成 (1.2s)
```

## 代码位置

### 后端
- `services/claude_code.py:509-515` - 提取最终回复
- `services/claude_code.py:528-565` - `_extract_final_response` 方法
- `channels/web/websocket.py:117-123` - 发送 complete 事件

### 前端
- `store/chatStore.ts:43-60` - `completeStreaming` 方法
- `hooks/useWebSocket.ts:37-39` - 处理 complete 事件
- `lib/websocket.ts:86-88` - WebSocket 消息处理

## 测试

运行测试：
```bash
python tests/test_final_response.py
```

## 示例

### 输入（完整响应）
```
💭 **思考过程：**
我需要先读取文件

---

这是最终回复

🔧 调用工具: Read
✅ Read 完成 (1.2s)
```

### 输出（最终回复）
```
这是最终回复
```

## 优势

1. **用户体验**：过程中看到 AI 的思考，增加透明度
2. **消息历史**：历史记录简洁，只保留有用信息
3. **性能优化**：减少存储空间，提高加载速度
4. **灵活性**：前端可以选择是否展示思考过程

## 未来优化

- [ ] 支持用户配置是否保留思考过程
- [ ] 支持折叠/展开思考块
- [ ] 支持工具调用详情查看
- [ ] 支持思考过程的语法高亮
