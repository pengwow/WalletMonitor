#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

SKIP_FRONTEND=false
for arg in "$@"; do
    case "$arg" in
        --skip-frontend) SKIP_FRONTEND=true ;;
    esac
done

MANIFEST="manifest.json"
if [ ! -f "$MANIFEST" ]; then
    error "manifest.json 不存在"
fi

PLUGIN_NAME=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['name'])" "$MANIFEST")
PLUGIN_VERSION=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "$MANIFEST")

info "插件: $PLUGIN_NAME v$PLUGIN_VERSION"

if [ "$SKIP_FRONTEND" = false ]; then
    if [ -d "frontend" ]; then
        info "构建前端..."
        cd frontend
        bun install --frozen-lockfile 2>/dev/null || bun install
        bun run build
        cd ..
        info "前端构建完成"
    fi
else
    info "跳过前端构建"
    if [ -d "frontend" ] && [ ! -d "frontend/dist" ]; then
        error "frontend/dist/ 不存在，请先执行完整构建（不带 --skip-frontend）"
    fi
fi

OUTPUT_DIR="$SCRIPT_DIR/dist"
mkdir -p "$OUTPUT_DIR"

ZIP_NAME="${PLUGIN_NAME}-${PLUGIN_VERSION}.zip"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME"
rm -f "$ZIP_PATH"

STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT

# 复制前端文件到 staging 根目录
rsync -a \
    --exclude='node_modules' \
    --exclude='frontend/node_modules' \
    "$SCRIPT_DIR/frontend/" "$STAGING/frontend/"

# 复制后端代码（从 wallet_monitor/ 子目录）到 staging 根目录
rsync -a \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.db' \
    --exclude='.DS_Store' \
    --exclude='*.egg-info' \
    "$SCRIPT_DIR/wallet_monitor/" "$STAGING/"

# 复制根目录的 manifest.json 和 build.sh
cp "$SCRIPT_DIR/manifest.json" "$STAGING/"
cp "$SCRIPT_DIR/build.sh" "$STAGING/"

(cd "$STAGING" && zip -r "$ZIP_PATH" . -q)

info "打包完成: $ZIP_PATH"
info ""
info "ZIP 结构:"
python3 -c "
import zipfile, sys
with zipfile.ZipFile(sys.argv[1]) as zf:
    for name in sorted(zf.namelist()):
        print(f'  {name}')
" "$ZIP_PATH"
