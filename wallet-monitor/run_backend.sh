#!/bin/bash

# 后端独立运行脚本
echo "启动后端服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
uv sync

# 启动后端服务
echo "启动后端服务..."
cd backend
uvicorn main:app --reload
