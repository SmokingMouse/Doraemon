#!/bin/bash

echo "重启 Doraemon 后端服务..."

# 查找并停止现有进程
PID=$(ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}')

if [ -n "$PID" ]; then
    echo "停止现有进程 (PID: $PID)..."
    kill $PID
    sleep 2
fi

# 启动新进程
echo "启动后端服务..."
cd /home/smokingmouse/python/ai/Doraemon
nohup python main.py > logs/backend.log 2>&1 &

NEW_PID=$!
echo "后端服务已启动 (PID: $NEW_PID)"
echo "日志文件: logs/backend.log"
echo ""
echo "测试删除端点..."
sleep 3

# 测试删除端点
curl -X OPTIONS http://localhost:8765/api/sessions/1 -v 2>&1 | grep -i "allow"

echo ""
echo "完成！"
