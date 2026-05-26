#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="$SCRIPT_DIR/wallet_monitor"
MANIFEST="$PLUGIN_DIR/manifest.json"
OUTPUT_DIR="$SCRIPT_DIR/dist"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

if [ ! -d "$PLUGIN_DIR" ]; then
    error "插件目录不存在: $PLUGIN_DIR"
fi

if [ ! -f "$MANIFEST" ]; then
    error "manifest.json 不存在: $MANIFEST"
fi

PLUGIN_NAME=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['name'])" "$MANIFEST")
PLUGIN_VERSION=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "$MANIFEST")

if [ -z "$PLUGIN_NAME" ] || [ -z "$PLUGIN_VERSION" ]; then
    error "无法从 manifest.json 中读取 name 或 version"
fi

info "插件: $PLUGIN_NAME v$PLUGIN_VERSION"

STAGING=$(mktemp -d)
trap 'rm -rf "$STAGING"' EXIT

STAGING_PLUGIN="$STAGING/$PLUGIN_NAME"
mkdir -p "$STAGING_PLUGIN"

rsync -a \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='*.db' \
    --exclude='.DS_Store' \
    --exclude='*.egg-info' \
    "$PLUGIN_DIR/" "$STAGING_PLUGIN/"

mkdir -p "$OUTPUT_DIR"

ZIP_NAME="${PLUGIN_NAME}-${PLUGIN_VERSION}.zip"
ZIP_PATH="$OUTPUT_DIR/$ZIP_NAME"

rm -f "$ZIP_PATH"

(cd "$STAGING" && zip -r "$ZIP_PATH" "$PLUGIN_NAME/" -q)

info "打包完成: $ZIP_PATH"
info "ZIP 结构:"
python3 -c "
import zipfile, sys
with zipfile.ZipFile(sys.argv[1]) as zf:
    for name in sorted(zf.namelist()):
        print(f'  {name}')
" "$ZIP_PATH"

info "可通过 QuantCell 插件管理页面上传此 ZIP 文件安装插件"
