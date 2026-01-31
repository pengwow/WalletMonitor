from web3 import Web3
from typing import List, Dict, Any, Optional
from .base import BlockchainBase
import json


class EthereumBlockchain(BlockchainBase):
    """
    以太坊区块链交互类
    """
    
    def __init__(self, rpc_url: str = "https://mainnet.infura.io/v3/YOUR_API_KEY"):
        """
        初始化以太坊区块链接口
        
        Args:
            rpc_url: RPC服务地址
        """
        super().__init__("ethereum", rpc_url)
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.connected = self.web3.is_connected()
    
    def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """
        获取钱包余额
        
        Args:
            address: 钱包地址
            token_address: 代币地址，None表示获取原生代币余额
            
        Returns:
            余额
        """
        if not self.connected:
            return 0.0
        
        try:
            checksum_address = self.web3.to_checksum_address(address)
            
            if token_address:
                # 获取ERC-20代币余额
                token_contract = self.get_contract(token_address, self._get_erc20_abi())
                balance_wei = token_contract.functions.balanceOf(checksum_address).call()
                decimals = token_contract.functions.decimals().call()
                return balance_wei / (10 ** decimals)
            else:
                # 获取原生代币余额
                balance_wei = self.web3.eth.get_balance(checksum_address)
                return self.web3.from_wei(balance_wei, "ether")
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
        if not self.connected:
            return []
        
        try:
            checksum_address = self.web3.to_checksum_address(address)
            # 这里使用etherscan API获取交易历史，需要替换为实际的API调用
            # 或者使用本地节点的trace_filter方法
            transactions = []
            # 模拟返回交易数据
            return transactions
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
        if not self.connected:
            return
        
        try:
            checksum_address = self.web3.to_checksum_address(address)
            # 这里使用web3的事件订阅功能
            # 实际实现需要根据具体的节点类型和API进行调整
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
        if not self.connected:
            return {}
        
        try:
            if block_number is None:
                block = self.web3.eth.get_block("latest")
            else:
                block = self.web3.eth.get_block(block_number)
            
            return {
                "number": block.number,
                "hash": block.hash.hex(),
                "timestamp": block.timestamp,
                "transactions": len(block.transactions),
                "difficulty": block.difficulty
            }
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
        if not self.connected:
            return None
        
        try:
            checksum_address = self.web3.to_checksum_address(contract_address)
            return self.web3.eth.contract(address=checksum_address, abi=abi)
        except Exception as e:
            print(f"获取合约实例失败: {e}")
            return None
    
    def _get_erc20_abi(self) -> List[Dict[str, Any]]:
        """
        获取ERC-20代币的标准ABI
        
        Returns:
            ERC-20 ABI
        """
        return json.loads('''[
            {
                "constant": true,
                "inputs": [],
                "name": "name",
                "outputs": [{"name": "", "type": "string"}],
                "payable": false,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": false,
                "inputs": [
                    {"name": "_spender", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "approve",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": false,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "totalSupply",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": false,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": false,
                "inputs": [
                    {"name": "_from", "type": "address"},
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transferFrom",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": false,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "payable": false,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "payable": false,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [],
                "name": "symbol",
                "outputs": [{"name": "", "type": "string"}],
                "payable": false,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "constant": false,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "payable": false,
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "constant": true,
                "inputs": [
                    {"name": "_owner", "type": "address"},
                    {"name": "_spender", "type": "address"}
                ],
                "name": "allowance",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": false,
                "stateMutability": "view",
                "type": "function"
            },
            {
                "payable": true,
                "stateMutability": "payable",
                "type": "fallback"
            },
            {
                "anonymous": false,
                "inputs": [
                    {"indexed": true, "name": "owner", "type": "address"},
                    {"indexed": true, "name": "spender", "type": "address"},
                    {"indexed": false, "name": "value", "type": "uint256"}
                ],
                "name": "Approval",
                "type": "event"
            },
            {
                "anonymous": false,
                "inputs": [
                    {"indexed": true, "name": "from", "type": "address"},
                    {"indexed": true, "name": "to", "type": "address"},
                    {"indexed": false, "name": "value", "type": "uint256"}
                ],
                "name": "Transfer",
                "type": "event"
            }
        ]''')
