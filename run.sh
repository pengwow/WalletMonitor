#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-5173}

cleanup() {
    echo ""
    info "正在停止服务..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        info "后端已停止"
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        info "前端已停止"
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           🐋 WalletMonitor 启动脚本                      ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 启动后端
info "启动后端服务 (端口: $BACKEND_PORT)..."
python3 run.py --port $BACKEND_PORT > /tmp/walletmonitor-backend.log 2>&1 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 检查后端是否启动成功
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    error "后端启动失败，查看日志: /tmp/walletmonitor-backend.log"
fi

info "后端已启动: http://localhost:$BACKEND_PORT"
info "API 文档: http://localhost:$BACKEND_PORT/docs"

# 启动前端
if [ -d "frontend" ] && [ -f "frontend/package.json" ]; then
    info "启动前端服务 (端口: $FRONTEND_PORT)..."
    cd frontend
    
    # 检查是否安装了依赖
    if [ ! -d "node_modules" ]; then
        info "安装前端依赖..."
        npm install 2>/dev/null || bun install
    fi
    
    # 使用 bun 启动开发服务器
    bun run dev --port $FRONTEND_PORT > /tmp/walletmonitor-frontend.log 2>&1 &
    FRONTEND_PID=$!
    cd ..
    
    sleep 3
    
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        info "前端已启动: http://localhost:$FRONTEND_PORT"
    else
        warn "前端启动失败，查看日志: /tmp/walletmonitor-frontend.log"
        warn "后端仍在运行"
    fi
else
    warn "未找到前端目录，仅启动后端"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
info "服务已启动"
echo -e "  后端: ${GREEN}http://localhost:$BACKEND_PORT${NC}"
echo -e "  前端: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  API:  ${GREEN}http://localhost:$BACKEND_PORT/docs${NC}"
echo ""
warn "按 Ctrl+C 停止所有服务"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"

# 等待子进程
wait
