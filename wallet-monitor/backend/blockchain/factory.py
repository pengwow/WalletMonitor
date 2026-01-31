from typing import Optional, Dict, Any
from .ethereum import EthereumBlockchain
from .solana import SolanaBlockchain
from .base import BlockchainBase


class BlockchainFactory:
    """
    区块链工厂类，用于创建不同区块链的实例
    """
    
    # 预定义的RPC URL
    DEFAULT_RPC_URLS = {
        "ethereum": "https://mainnet.infura.io/v3/YOUR_API_KEY",
        "bsc": "https://bsc-dataseed.binance.org/",
        "polygon": "https://polygon-rpc.com/",
        "solana": "https://api.mainnet-beta.solana.com"
    }
    
    @staticmethod
    def create_blockchain(chain_type: str, rpc_url: Optional[str] = None) -> Optional[BlockchainBase]:
        """
        创建区块链实例
        
        Args:
            chain_type: 区块链类型，支持ethereum、bsc、polygon、solana
            rpc_url: RPC服务地址，None表示使用默认地址
            
        Returns:
            区块链实例
        """
        if rpc_url is None:
            rpc_url = BlockchainFactory.DEFAULT_RPC_URLS.get(chain_type)
            if rpc_url is None:
                print(f"不支持的区块链类型: {chain_type}")
                return None
        
        try:
            if chain_type in ["ethereum", "bsc", "polygon"]:
                # BSC和Polygon都是基于以太坊的，使用EthereumBlockchain类
                return EthereumBlockchain(rpc_url)
            elif chain_type == "solana":
                return SolanaBlockchain(rpc_url)
            else:
                print(f"不支持的区块链类型: {chain_type}")
                return None
        except Exception as e:
            print(f"创建区块链实例失败: {e}")
            return None
    
    @staticmethod
    def get_supported_chains() -> list:
        """
        获取支持的区块链列表
        
        Returns:
            支持的区块链列表
        """
        return list(BlockchainFactory.DEFAULT_RPC_URLS.keys())
