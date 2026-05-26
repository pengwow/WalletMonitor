from plugins.plugin_base import PluginBase
from fastapi import APIRouter

from .api.wallets import router as wallets_router
from .api.transactions import router as transactions_router
from .api.alerts import router as alerts_router
from .api.whales import router as whales_router
from .blockchain.factory import BlockchainFactory
from .data.storage import DataStorage
from .alert.engine import AlertRuleEngine


class WalletMonitorPlugin(PluginBase):
    def __init__(self):
        super().__init__("wallet_monitor", "1.0.0")
        self.load_type = "hot"
        self.description = "多链区块链钱包监控系统，支持以太坊、BSC、Polygon、Solana的钱包追踪、交易监控、智能告警和巨鲸监控"
        self.author = "WalletMonitor Team"
        self.router = APIRouter(prefix="/api/plugins/wallet-monitor")

        self._setup_routes()
        self._init_modules()

    def _init_modules(self):
        import os
        db_path = os.path.join(os.path.dirname(__file__), "wallet_monitor.db")
        self.storage = DataStorage(db_path=db_path)
        self.alert_engine = AlertRuleEngine()
        self.blockchain_factory = BlockchainFactory()

    def _setup_routes(self):
        self.router.include_router(wallets_router)
        self.router.include_router(transactions_router)
        self.router.include_router(alerts_router)
        self.router.include_router(whales_router)

        @self.router.get("/health")
        async def health():
            return {
                "status": "ok",
                "plugin": self.name,
                "version": self.version,
            }

    def register(self, plugin_manager):
        super().register(plugin_manager)
        self.logger.info(f"{self.name} 注册成功，版本: {self.version}")

    def start(self):
        super().start()
        self.logger.info(f"{self.name} 启动成功")

    def stop(self):
        super().stop()
        self.logger.info(f"{self.name} 停止成功")

    def on_enable(self):
        self.logger.info(f"{self.name} 已启用")

    def on_disable(self):
        self.logger.info(f"{self.name} 已禁用")

    def get_config_schema(self):
        return {
            "type": "object",
            "properties": {
                "ethereum_rpc_url": {
                    "type": "string",
                    "title": "以太坊 RPC URL",
                    "default": "https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
                },
                "bsc_rpc_url": {
                    "type": "string",
                    "title": "BSC RPC URL",
                    "default": "https://bsc-dataseed.binance.org/",
                },
                "solana_rpc_url": {
                    "type": "string",
                    "title": "Solana RPC URL",
                    "default": "https://api.mainnet-beta.solana.com",
                },
                "whale_refresh_interval": {
                    "type": "integer",
                    "title": "巨鲸监控刷新间隔(秒)",
                    "default": 30,
                },
            },
        }


def register_plugin():
    return WalletMonitorPlugin()
