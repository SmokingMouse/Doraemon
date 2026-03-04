#!/bin/bash

# Start Doraemon with Next.js frontend

echo "Starting Doraemon backend..."
python main.py &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 3

echo "Starting Next.js frontend..."
cd frontend-next && npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "🌐 Access the application:"
echo "  - Next.js UI: http://localhost:3000"
echo "  - Original UI: http://localhost:5173/index.html"
echo "  - Backend API: http://localhost:8765"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for both processes
wait
