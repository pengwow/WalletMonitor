#!/bin/bash

# 启动脚本 - 区块链钱包监控系统

echo "================================"
echo "区块链钱包监控系统启动脚本"
echo "================================"

# 检查是否在正确的目录
if [ ! -d "wallet-monitor" ] || [ ! -d "quantcell" ]; then
    echo "错误：请在项目根目录运行此脚本"
    exit 1
fi

# 启动后端服务
echo "\n启动后端服务..."
cd wallet-monitor/backend
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install -r ../requirements.txt >/dev/null 2>&1
python app.py &
BACKEND_PID=$!
echo "后端服务已启动，PID: $BACKEND_PID"

# 等待后端服务启动
sleep 3

# 启动前端开发服务器
echo "\n启动前端开发服务器..."
cd ../..
cd wallet-monitor
npm install >/dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
echo "前端开发服务器已启动，PID: $FRONTEND_PID"

# 显示访问信息
echo "\n================================"
echo "服务已启动成功！"
echo "================================"
echo "后端API地址: http://localhost:8000"
echo "前端应用地址: http://localhost:3000"
echo "API文档地址: http://localhost:8000/docs"
echo "================================"
echo "按 Ctrl+C 停止所有服务"
echo "================================"

# 等待用户输入
wait

# 停止服务
echo "\n停止服务..."
kill $BACKEND_PID 2>/dev/null
kill $FRONTEND_PID 2>/dev/null
echo "服务已停止"
