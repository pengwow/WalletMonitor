# 以太坊区块链交互模块
# 负责与以太坊网络通信，获取交易、区块、合约事件等数据

import requests
import json
from typing import Dict, List, Optional, Any

class EthereumClient:
    def __init__(self, rpc_url: str = "https://mainnet.infura.io/v3/YOUR_API_KEY"):
        """初始化以太坊客户端
        
        Args:
            rpc_url: 以太坊RPC节点URL
        """
        self.rpc_url = rpc_url
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def _send_request(self, method: str, params: List[Any]) -> Dict[str, Any]:
        """发送RPC请求
        
        Args:
            method: RPC方法名
            params: RPC参数列表
            
        Returns:
            RPC响应结果
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }
        
        response = requests.post(
            self.rpc_url,
            headers=self.headers,
            data=json.dumps(payload)
        )
        
        return response.json()
    
    def get_block_number(self) -> int:
        """获取当前区块号
        
        Returns:
            当前区块号
        """
        result = self._send_request("eth_blockNumber", [])
        return int(result.get("result", "0x0"), 16)
    
    def get_block(self, block_number: int, full_transactions: bool = True) -> Dict[str, Any]:
        """获取区块信息
        
        Args:
            block_number: 区块号
            full_transactions: 是否返回完整交易信息
            
        Returns:
            区块信息
        """
        block_param = hex(block_number)
        result = self._send_request(
            "eth_getBlockByNumber",
            [block_param, full_transactions]
        )
        return result.get("result", {})
    
    def get_balance(self, address: str, block_number: str = "latest") -> int:
        """获取地址余额
        
        Args:
            address: 以太坊地址
            block_number: 区块号，默认为latest
            
        Returns:
            地址余额（wei）
        """
        result = self._send_request(
            "eth_getBalance",
            [address, block_number]
        )
        return int(result.get("result", "0x0"), 16)
    
    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """获取交易信息
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            交易信息
        """
        result = self._send_request("eth_getTransactionByHash", [tx_hash])
        return result.get("result", {})
    
    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """获取交易收据
        
        Args:
            tx_hash: 交易哈希
            
        Returns:
            交易收据
        """
        result = self._send_request("eth_getTransactionReceipt", [tx_hash])
        return result.get("result", {})
    
    def watch_address(self, address: str, callback) -> None:
        """监听地址交易
        
        Args:
            address: 以太坊地址
            callback: 回调函数，接收交易信息
        """
        # 这里实现轮询监听，实际生产环境可以使用WebSocket或事件订阅
        # 简化版实现，仅作示例
        pass

# 示例用法
if __name__ == "__main__":
    client = EthereumClient()
    block_number = client.get_block_number()
    print(f"Current block number: {block_number}")
    
    # 获取最新区块
    block = client.get_block(block_number)
    print(f"Block hash: {block.get('hash')}")
    print(f"Number of transactions: {len(block.get('transactions', []))}")
