#!/bin/bash
# 重启 Doraemon Bot 的脚本

echo "🔄 重启 Doraemon Bot..."

# 1. 停止现有进程
echo "1. 停止现有进程..."
pkill -f "python.*main.py" 2>/dev/null && echo "   ✓ 已停止旧进程" || echo "   ✓ 没有运行中的进程"

# 2. 等待进程完全退出
sleep 1

# 3. 启动新进程
echo "2. 启动新进程..."
source .venv/bin/activate
nohup python main.py > ./data/logs/bot.log 2>&1 &
BOT_PID=$!

# 4. 等待启动
sleep 2

# 5. 检查是否成功启动
if ps -p $BOT_PID > /dev/null; then
    echo "   ✓ Bot 已启动 (PID: $BOT_PID)"
    echo ""
    echo "✅ 重启完成！"
    echo ""
    echo "查看日志: tail -f ./data/logs/bot.log"
    echo "停止 Bot: kill $BOT_PID"
else
    echo "   ❌ Bot 启动失败"
    echo ""
    echo "查看错误: cat ./data/logs/bot.log"
    exit 1
fi
