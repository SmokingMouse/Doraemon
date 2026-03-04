#!/bin/bash

# Start backend
echo "Starting backend on http://localhost:8765..."
python main.py > /tmp/doraemon_backend.log 2>&1 &
BACKEND_PID=$!

sleep 3

# Start frontend
echo "Starting frontend on http://localhost:5173..."
python scripts/serve_frontend.py > /tmp/doraemon_frontend.log 2>&1 &
FRONTEND_PID=$!

echo ""
echo "✅ Doraemon is running!"
echo ""
echo "Backend:  http://localhost:8765"
echo "Frontend: http://localhost:5173/index.html"
echo "API Docs: http://localhost:8765/docs"
echo ""
echo "Press Ctrl+C to stop..."

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo 'Stopped'; exit" INT
wait
