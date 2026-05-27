import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.wallets import router as wallets_router
from .api.transactions import router as transactions_router
from .api.alerts import router as alerts_router
from .api.whales import router as whales_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="WalletMonitor",
        description="区块链钱包监控 + 巨鲸监控",
        version="1.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = "/api"
    app.include_router(wallets_router, prefix=prefix)
    app.include_router(transactions_router, prefix=prefix)
    app.include_router(alerts_router, prefix=prefix)
    app.include_router(whales_router, prefix=prefix)

    @app.get("/")
    async def root():
        return {
            "name": "WalletMonitor",
            "version": "1.1.0",
            "mode": "standalone",
            "endpoints": {
                "wallets": f"{prefix}/wallets",
                "transactions": f"{prefix}/transactions",
                "alerts": f"{prefix}/alerts",
                "whales": f"{prefix}/whales",
            },
        }

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


app = create_app()
