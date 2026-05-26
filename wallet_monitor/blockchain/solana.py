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
        # solana 库为可选依赖，延迟导入避免插件加载失败
        from solana.rpc.api import Client
        super().__init__("solana", rpc_url)
        self.client = Client(rpc_url)
        self.connected = True

    def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """
        获取钱包余额
        """
        from solana.publickey import PublicKey
        try:
            public_key = PublicKey(address)

            if token_address:
                return 0.0
            else:
                balance_response = self.client.get_balance(public_key)
                if "result" in balance_response:
                    return balance_response["result"] / 1e9
                return 0.0
        except Exception as e:
            print(f"获取余额失败: {e}")
            return 0.0

    def get_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取钱包交易历史
        """
        from solana.publickey import PublicKey
        try:
            public_key = PublicKey(address)
            signatures_response = self.client.get_signatures_for_address(public_key, limit=limit)

            if "result" in signatures_response:
                transactions = []
                for sig_info in signatures_response["result"]:
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
        """
        try:
            pass
        except Exception as e:
            print(f"订阅事件失败: {e}")

    def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """
        获取区块信息
        """
        try:
            if block_number is None:
                block_response = self.client.get_latest_blockhash()
                if "result" in block_response:
                    return block_response["result"]
            else:
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
        """
        try:
            return None
        except Exception as e:
            print(f"获取合约实例失败: {e}")
            return None
