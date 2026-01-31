from solana.rpc.api import Client
from solana.account import Account
from solana.publickey import PublicKey
from typing import List, Dict, Any, Optional
from .base import BlockchainBase


class SolanaBlockchain(BlockchainBase):
    """
    Solana区块链交互类
    """
    
    def __init__(self, rpc_url: str = "https://api.mainnet-beta.solana.com"):
        """
        初始化Solana区块链接口
        
        Args:
            rpc_url: RPC服务地址
        """
        super().__init__("solana", rpc_url)
        self.client = Client(rpc_url)
        self.connected = True  # Solana客户端没有is_connected()方法，暂时默认为True
    
    def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """
        获取钱包余额
        
        Args:
            address: 钱包地址
            token_address: 代币地址，None表示获取原生代币余额
            
        Returns:
            余额
        """
        try:
            public_key = PublicKey(address)
            
            if token_address:
                # 获取SPL代币余额
                # 这里需要实现SPL代币余额查询逻辑
                # 暂时返回0.0
                return 0.0
            else:
                # 获取原生代币余额
                balance_response = self.client.get_balance(public_key)
                if "result" in balance_response:
                    # Solana的余额单位是lamports，1 SOL = 10^9 lamports
                    return balance_response["result"] / 1e9
                return 0.0
        except Exception as e:
            print(f"获取余额失败: {e}")
            return 0.0
    
    def get_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取钱包交易历史
        
        Args:
            address: 钱包地址
            limit: 交易数量限制
            
        Returns:
            交易列表
        """
        try:
            public_key = PublicKey(address)
            # 使用get_signatures_for_address方法获取交易签名
            signatures_response = self.client.get_signatures_for_address(public_key, limit=limit)
            
            if "result" in signatures_response:
                transactions = []
                for sig_info in signatures_response["result"]:
                    # 通过签名获取交易详情
                    tx_response = self.client.get_transaction(sig_info["signature"])
                    if "result" in tx_response:
                        tx = tx_response["result"]
                        transactions.append({
                            "signature": sig_info["signature"],
                            "slot": sig_info["slot"],
                            "block_time": sig_info.get("blockTime"),
                            "transaction": tx
                        })
                return transactions
            return []
        except Exception as e:
            print(f"获取交易历史失败: {e}")
            return []
    
    def subscribe_events(self, address: str, callback: callable):
        """
        订阅钱包事件
        
        Args:
            address: 钱包地址
            callback: 事件回调函数
        """
        try:
            # Solana的WebSocket订阅功能
            # 这里需要实现WebSocket订阅逻辑
            pass
        except Exception as e:
            print(f"订阅事件失败: {e}")
    
    def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """
        获取区块信息
        
        Args:
            block_number: 区块号，None表示获取最新区块
            
        Returns:
            区块信息
        """
        try:
            if block_number is None:
                # 获取最新区块
                block_response = self.client.get_latest_blockhash()
                if "result" in block_response:
                    return block_response["result"]
            else:
                # 获取指定区块
                block_response = self.client.get_block(block_number)
                if "result" in block_response:
                    return block_response["result"]
            return {}
        except Exception as e:
            print(f"获取区块信息失败: {e}")
            return {}
    
    def get_contract(self, contract_address: str, abi: List[Dict[str, Any]]):
        """
        获取智能合约实例
        
        Args:
            contract_address: 合约地址
            abi: 合约ABI
            
        Returns:
            合约实例
        """
        try:
            # Solana的智能合约是Program
            # 这里需要实现Program实例获取逻辑
            return None
        except Exception as e:
            print(f"获取合约实例失败: {e}")
            return None
