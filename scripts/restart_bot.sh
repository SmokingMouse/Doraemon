#!/bin/bash
# 重启 Doraemon Bot 的脚本

echo "🔄 重启 Doraemon Bot..."

# 1. 停止所有现有进程（包括 uv run 和 python）
echo "1. 停止所有现有进程..."
pkill -9 -f "python.*main.py" 2>/dev/null
pkill -9 -f "uv run.*main.py" 2>/dev/null
sleep 2

# 验证是否还有进程在运行
REMAINING=$(ps aux | grep -E "python.*main.py" | grep -v grep | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo "   ⚠️  警告: 仍有 $REMAINING 个进程在运行"
    ps aux | grep -E "python.*main.py" | grep -v grep
    echo "   请手动停止这些进程"
    exit 1
else
    echo "   ✓ 所有旧进程已停止"
fi

# 2. 启动新进程
echo "2. 启动新进程..."
cd "$(dirname "$0")"
source .venv/bin/activate

# 重要: 在 Python 中取消 Claude Code 环境变量
# 创建一个启动包装脚本
cat > /tmp/start_doraemon.sh <<'EOF'
#!/bin/bash
unset CLAUDECODE
unset CLAUDE_CODE_SSE_PORT
unset CLAUDE_CODE_ENTRYPOINT
unset CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC
exec python main.py
EOF
chmod +x /tmp/start_doraemon.sh

nohup /tmp/start_doraemon.sh > ./data/logs/bot.log 2>&1 &
BOT_PID=$!

# 3. 等待启动
sleep 2

# 4. 检查是否成功启动
if ps -p $BOT_PID > /dev/null; then
    echo "   ✓ Bot 已启动 (PID: $BOT_PID)"
    echo ""
    echo "✅ 重启完成！"
    echo ""
    echo "查看日志: tail -f ./data/logs/bot.log"
    echo "停止 Bot: kill $BOT_PID"
    echo ""
    echo "⚠️  重要: 请确保只运行一个 bot 实例！"
else
    echo "   ❌ Bot 启动失败"
    echo ""
    echo "查看错误: cat ./data/logs/bot.log"
    exit 1
fi
