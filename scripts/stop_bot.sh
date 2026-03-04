#!/bin/bash
# 停止 Doraemon Bot 的脚本

echo "🛑 停止 Doraemon Bot..."

# 检查运行中的进程
RUNNING=$(ps aux | grep -E "python.*main.py" | grep -v grep | wc -l)

if [ $RUNNING -eq 0 ]; then
    echo "✓ 没有运行中的 bot 进程"
    exit 0
fi

echo "找到 $RUNNING 个运行中的进程:"
ps aux | grep -E "python.*main.py" | grep -v grep

echo ""
echo "正在停止..."

# 先尝试优雅停止
pkill -TERM -f "python.*main.py" 2>/dev/null
sleep 2

# 检查是否还有进程
REMAINING=$(ps aux | grep -E "python.*main.py" | grep -v grep | wc -l)

if [ $REMAINING -gt 0 ]; then
    echo "优雅停止失败，强制终止..."
    pkill -9 -f "python.*main.py" 2>/dev/null
    pkill -9 -f "uv run.*main.py" 2>/dev/null
    sleep 1
fi

# 最终检查
FINAL=$(ps aux | grep -E "python.*main.py" | grep -v grep | wc -l)

if [ $FINAL -eq 0 ]; then
    echo "✅ 所有 bot 进程已停止"
else
    echo "❌ 仍有 $FINAL 个进程在运行"
    ps aux | grep -E "python.*main.py" | grep -v grep
    exit 1
fi
