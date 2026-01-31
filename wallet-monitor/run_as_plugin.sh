#!/bin/bash

# 插件运行脚本
echo "以插件模式运行..."

echo "请将wallet-monitor目录复制到quantcell的对应插件目录中："
echo "后端插件：quantcell/backend/plugins/"
echo "前端插件：quantcell/frontend/src/plugins/"

echo "然后启动quantcell服务："
echo "cd quantcell/backend && uvicorn main:app --reload"
echo "cd quantcell/frontend && npm run dev"
