from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用实例
app = FastAPI(
    title="区块链钱包监控系统",
    description="一个支持多链的区块链钱包监控系统，提供实时交易跟踪、智能合约交互监控、异常行为检测与告警等功能",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该设置为具体的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加当前目录到Python路径
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 注册API路由
try:
    from api.wallets import router as wallets_router
    from api.transactions import router as transactions_router
    from api.alerts import router as alerts_router
    
    app.include_router(wallets_router)
    app.include_router(transactions_router)
    app.include_router(alerts_router)
    
    logger.info("API路由注册成功")
except Exception as e:
    logger.error(f"API路由注册失败: {e}")

# 初始化区块链实例和数据存储
try:
    from blockchain.factory import BlockchainFactory
    from data.storage import DataStorage
    
    # 初始化数据存储
    storage = DataStorage()
    logger.info("数据存储初始化成功")
    
    # 初始化区块链实例缓存
    blockchain_instances = {}
    supported_chains = BlockchainFactory.get_supported_chains()
    for chain in supported_chains:
        blockchain_instances[chain] = BlockchainFactory.create_blockchain(chain)
        logger.info(f"{chain} 区块链实例初始化成功")
    
    logger.info("区块链实例初始化成功")
except Exception as e:
    logger.error(f"初始化失败: {e}")

# 健康检查接口
@app.get("/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "message": "区块链钱包监控系统运行正常"
    }

# 根路径接口
@app.get("/")
async def root():
    """
    根路径接口
    """
    return {
        "message": "欢迎使用区块链钱包监控系统",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 启动服务器
if __name__ == "__main__":
    try:
        logger.info("启动区块链钱包监控系统...")
        uvicorn.run(
            "app:app",
            host="0.0.0.0",
            port=8000,
            reload=True
        )
    except Exception as e:
        logger.error(f"启动失败: {e}")
