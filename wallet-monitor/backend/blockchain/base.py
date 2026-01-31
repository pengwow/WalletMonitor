from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime


class BlockchainBase(ABC):
    """
    区块链基础接口
    """
    
    def __init__(self, chain_name: str, rpc_url: str):
        """
        初始化区块链接口
        
        Args:
            chain_name: 区块链名称
            rpc_url: RPC服务地址
        """
        self.chain_name = chain_name
        self.rpc_url = rpc_url
    
    @abstractmethod
    def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """
        获取钱包余额
        
        Args:
            address: 钱包地址
            token_address: 代币地址，None表示获取原生代币余额
            
        Returns:
            余额
        """
        pass
    
    @abstractmethod
    def get_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取钱包交易历史
        
        Args:
            address: 钱包地址
            limit: 交易数量限制
            
        Returns:
            交易列表
        """
        pass
    
    @abstractmethod
    def subscribe_events(self, address: str, callback: callable):
        """
        订阅钱包事件
        
        Args:
            address: 钱包地址
            callback: 事件回调函数
        """
        pass
    
    @abstractmethod
    def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """
        获取区块信息
        
        Args:
            block_number: 区块号，None表示获取最新区块
            
        Returns:
            区块信息
        """
        pass
    
    @abstractmethod
    def get_contract(self, contract_address: str, abi: List[Dict[str, Any]]):
        """
        获取智能合约实例
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            
        Returns:
            合约实例
        """
        pass
