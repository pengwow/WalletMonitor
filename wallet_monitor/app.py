import os
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.wallets import router as wallets_router
from .api.transactions import router as transactions_router
from .api.alerts import router as alerts_router
from .api.whales import router as whales_router
from .api.middleware import register_middleware
from .data.storage import DataStorage
from .logging_config import setup_logging
from .config import settings

# Initialize structured logging (JSON in production, colored dev format locally)
setup_logging(level=settings.log_level)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title="WalletMonitor",
        description="区块链钱包监控 + 巨鲸监控",
        version="1.2.0",
    )

    # --- Middleware & exception handlers ------------------------------------
    register_middleware(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Database ----------------------------------------------------------
    plugin_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    os.makedirs(plugin_data_dir, exist_ok=True)
    db_path = os.path.join(plugin_data_dir, "wallet_monitor.db")
    DataStorage(db_path=db_path)
    logger.info("数据库路径: %s", db_path)

    # --- Routers -----------------------------------------------------------
    prefix = "/api"
    app.include_router(wallets_router, prefix=prefix)
    app.include_router(transactions_router, prefix=prefix)
    app.include_router(alerts_router, prefix=prefix)
    app.include_router(whales_router, prefix=prefix)

    # --- Root & health endpoints -------------------------------------------
    @app.get("/")
    async def root():
        return {
            "name": "WalletMonitor",
            "version": "1.2.0",
            "mode": "standalone",
            "endpoints": {
                "wallets": f"{prefix}/wallets",
                "transactions": f"{prefix}/transactions",
                "alerts": f"{prefix}/alerts",
                "whales": f"{prefix}/whales",
                "health": "/health",
                "docs": "/docs",
            },
        }

    @app.get("/health")
    async def health():
        """Liveness / readiness probe.

        Returns basic app info plus a timestamp so load-balancers and
        orchestrators can verify the service is up and responsive.
        """
        from datetime import datetime, timezone

        return {
            "status": "ok",
            "version": "1.2.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    return app


app = create_app()
