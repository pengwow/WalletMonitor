from fastapi import APIRouter
from typing import Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - wallet-monitor - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入插件基类
class PluginBase:
    """
    插件基类
    """
    def __init__(self, name: str, version: str):
        self.name = name
        self.version = version
        self.logger = logging.getLogger(name)
        self.router = APIRouter(prefix=f"/api/plugins/{name}")
    
    def register(self, plugin_manager):
        self.logger.info(f"{self.name} 插件注册成功")
    
    def start(self):
        self.logger.info(f"{self.name} 插件启动成功")
    
    def stop(self):
        self.logger.info(f"{self.name} 插件停止成功")
    
    def get_info(self):
        return {
            "name": self.name,
            "version": self.version
        }

class WalletMonitorPlugin(PluginBase):
    """
    区块链钱包监控插件
    """
    def __init__(self):
        super().__init__("wallet-monitor", "1.0.0")
        self._setup_routes()
        self._init_resources()
    
    def _setup_routes(self):
        """
        设置插件路由
        """
        try:
            # 注册健康检查接口
            @self.router.get("/")
            async def plugin_root():
                return {
                    "message": "区块链钱包监控插件",
                    "plugin_name": self.name,
                    "version": self.version,
                    "status": "active"
                }
            
            # 注册测试接口
            @self.router.get("/test")
            async def plugin_test():
                return {
                    "test": "success",
                    "data": {
                        "supported_chains": self.supported_chains,
                        "storage_initialized": self.storage_initialized
                    }
                }
            
            # 注册API路由
            from .api.wallets import router as wallets_router
            from .api.transactions import router as transactions_router
            from .api.alerts import router as alerts_router
            
            # 重新注册路由，使用插件前缀
            self.router.include_router(wallets_router, prefix="/wallets", tags=["wallets"])
            self.router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
            self.router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
            
            logger.info("插件路由设置成功")
        except Exception as e:
            logger.error(f"插件路由设置失败: {e}")
    
    def _init_resources(self):
        """
        初始化资源
        """
        try:
            from .blockchain.factory import BlockchainFactory
            from .data.storage import DataStorage
            
            # 初始化数据存储
            self.storage = DataStorage()
            self.storage_initialized = True
            logger.info("数据存储初始化成功")
            
            # 初始化区块链实例缓存
            self.blockchain_instances = {}
            self.supported_chains = BlockchainFactory.get_supported_chains()
            for chain in self.supported_chains:
                self.blockchain_instances[chain] = BlockchainFactory.create_blockchain(chain)
                logger.info(f"{chain} 区块链实例初始化成功")
            
            logger.info("资源初始化成功")
        except Exception as e:
            logger.error(f"资源初始化失败: {e}")
            self.storage_initialized = False
            self.supported_chains = []
    
    def register(self, plugin_manager):
        """
        注册插件
        """
        super().register(plugin_manager)
        logger.info(f"{self.name} 插件注册成功")
    
    def start(self):
        """
        启动插件
        """
        super().start()
        logger.info(f"{self.name} 插件启动成功")
    
    def stop(self):
        """
        停止插件
        """
        super().stop()
        logger.info(f"{self.name} 插件停止成功")
    
    def get_info(self):
        """
        获取插件信息
        """
        info = super().get_info()
        info.update({
            "supported_chains": self.supported_chains,
            "storage_initialized": self.storage_initialized
        })
        return info

def register_plugin():
    """
    注册插件
    """
    try:
        plugin = WalletMonitorPlugin()
        logger.info("钱包监控插件注册成功")
        return plugin
    except Exception as e:
        logger.error(f"钱包监控插件注册失败: {e}")
        raise
