#!/usr/bin/env python3
"""WalletMonitor 独立运行入口"""

import argparse
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="WalletMonitor 独立服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认: 8000)")
    parser.add_argument("--reload", action="store_true", help="开发模式热重载")
    args = parser.parse_args()

    print(f"🐋 WalletMonitor 启动中... http://{args.host}:{args.port}")
    print(f"   API 文档: http://localhost:{args.port}/docs")
    print()

    uvicorn.run(
        "wallet_monitor.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
