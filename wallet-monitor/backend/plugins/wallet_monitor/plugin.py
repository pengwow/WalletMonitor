from plugins.plugin_base import PluginBase
from fastapi import APIRouter

# 导入API路由
import sys
import os

# 添加插件目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入模块
from api.wallets import router as wallets_router
from api.transactions import router as transactions_router
from blockchain.ethereum import EthereumClient
from blockchain.bsc import BSCClient
from data.processor import DataProcessor
from data.storage import DataStorage
from alert.engine import AlertEngine

class WalletMonitorPlugin(PluginBase):
    def __init__(self):
        super().__init__("wallet-monitor", "1.0.0")
        self.router = APIRouter(prefix="/api/plugins/wallet-monitor")
        self._setup_routes()
        self._init_modules()
    
    def _init_modules(self):
        """初始化模块"""
        # 区块链客户端
        self.ethereum_client = EthereumClient()
        self.bsc_client = BSCClient()
        
        # 数据处理
        self.processor = DataProcessor()
        self.storage = DataStorage()
        
        # 告警引擎
        self.alert_engine = AlertEngine(self.storage)
    
    def _setup_routes(self):
        @self.router.get("/")
        def plugin_root():
            return {
                "message": "Hello from wallet monitor plugin!",
                "plugin_name": self.name,
                "version": self.version
            }
        
        @self.router.get("/test")
        def test_endpoint():
            return {
                "test": "success",
                "data": {
                    "key1": "value1",
                    "key2": "value2"
                }
            }
        
        # 直接定义钱包路由
        wallets = []
        
        @self.router.get("/wallets")
        def get_wallets():
            return wallets
        
        @self.router.post("/wallets")
        def add_wallet(wallet: dict):
            if "address" not in wallet or "chain" not in wallet:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail="钱包地址和链不能为空")
            
            for existing_wallet in wallets:
                if existing_wallet["address"] == wallet["address"] and existing_wallet["chain"] == wallet["chain"]:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=400, detail="钱包已存在")
            
            wallet_id = len(wallets) + 1
            wallet["id"] = wallet_id
            wallets.append(wallet)
            return wallet
        
        # 直接定义交易路由
        transactions = [
            {
                "id": 1,
                "hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
                "from": "0x1234567890123456789012345678901234567890",
                "to": "0x0987654321098765432109876543210987654321",
                "value": 1000000000000000000,
                "gas": 21000,
                "gas_price": 20000000000,
                "nonce": "0",
                "input": "0x",
                "block_hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
                "block_number": 1000000,
                "transaction_index": 0,
                "chain": "ethereum",
                "timestamp": 1640995200,
                "processed_at": 1640995200
            }
        ]
        
        @self.router.get("/transactions")
        def get_transactions():
            return transactions
    
    def register(self, plugin_manager):
        super().register(plugin_manager)
        self.logger.info(f"{self.name} 插件注册成功")
    
    def start(self):
        super().start()
        self.logger.info(f"{self.name} 插件启动成功")
        # 启动监控任务
        self._start_monitoring()
    
    def _start_monitoring(self):
        """启动监控任务"""
        # 这里可以启动后台任务，例如区块监听、交易监控等
        # 简化版实现，仅作示例
        self.logger.info("开始监控区块链交易...")

def register_plugin():
    return WalletMonitorPlugin()
