# 数据处理模块
# 负责清洗、标准化区块链数据

from typing import Dict, List, Any
import time

class DataProcessor:
    def __init__(self):
        """初始化数据处理器"""
        pass
    
    def process_transaction(self, transaction: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """处理交易数据
        
        Args:
            transaction: 原始交易数据
            chain: 区块链名称
            
        Returns:
            处理后的交易数据
        """
        processed_tx = {
            "hash": transaction.get("hash", ""),
            "from": transaction.get("from", ""),
            "to": transaction.get("to", ""),
            "value": self._normalize_value(transaction.get("value", "0x0")),
            "gas": self._normalize_value(transaction.get("gas", "0x0")),
            "gas_price": self._normalize_value(transaction.get("gasPrice", "0x0")),
            "nonce": transaction.get("nonce", "0"),
            "input": transaction.get("input", ""),
            "block_hash": transaction.get("blockHash", ""),
            "block_number": self._normalize_block_number(transaction.get("blockNumber", "0x0")),
            "transaction_index": self._normalize_transaction_index(transaction.get("transactionIndex", "0x0")),
            "chain": chain,
            "timestamp": int(time.time()),
            "processed_at": int(time.time())
        }
        
        return processed_tx
    
    def process_block(self, block: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """处理区块数据
        
        Args:
            block: 原始区块数据
            chain: 区块链名称
            
        Returns:
            处理后的区块数据
        """
        processed_block = {
            "hash": block.get("hash", ""),
            "number": self._normalize_block_number(block.get("number", "0x0")),
            "parent_hash": block.get("parentHash", ""),
            "nonce": block.get("nonce", ""),
            "sha3_uncles": block.get("sha3Uncles", ""),
            "logs_bloom": block.get("logsBloom", ""),
            "transactions_root": block.get("transactionsRoot", ""),
            "state_root": block.get("stateRoot", ""),
            "receipts_root": block.get("receiptsRoot", ""),
            "miner": block.get("miner", ""),
            "difficulty": self._normalize_value(block.get("difficulty", "0x0")),
            "total_difficulty": self._normalize_value(block.get("totalDifficulty", "0x0")),
            "size": self._normalize_value(block.get("size", "0x0")),
            "extra_data": block.get("extraData", ""),
            "gas_limit": self._normalize_value(block.get("gasLimit", "0x0")),
            "gas_used": self._normalize_value(block.get("gasUsed", "0x0")),
            "timestamp": self._normalize_timestamp(block.get("timestamp", "0x0")),
            "transactions_count": len(block.get("transactions", [])),
            "chain": chain,
            "processed_at": int(time.time())
        }
        
        return processed_block
    
    def process_contract_event(self, event: Dict[str, Any], chain: str) -> Dict[str, Any]:
        """处理合约事件数据
        
        Args:
            event: 原始事件数据
            chain: 区块链名称
            
        Returns:
            处理后的事件数据
        """
        processed_event = {
            "address": event.get("address", ""),
            "topics": event.get("topics", []),
            "data": event.get("data", ""),
            "block_number": self._normalize_block_number(event.get("blockNumber", "0x0")),
            "block_hash": event.get("blockHash", ""),
            "transaction_hash": event.get("transactionHash", ""),
            "transaction_index": self._normalize_transaction_index(event.get("transactionIndex", "0x0")),
            "log_index": self._normalize_log_index(event.get("logIndex", "0x0")),
            "removed": event.get("removed", False),
            "chain": chain,
            "processed_at": int(time.time())
        }
        
        return processed_event
    
    def _normalize_value(self, value: str) -> int:
        """标准化数值
        
        Args:
            value: 十六进制字符串或其他格式的数值
            
        Returns:
            标准化后的整数
        """
        if isinstance(value, str) and value.startswith("0x"):
            return int(value, 16)
        elif isinstance(value, (int, float)):
            return int(value)
        else:
            return 0
    
    def _normalize_block_number(self, block_number: str) -> int:
        """标准化区块号
        
        Args:
            block_number: 十六进制字符串或其他格式的区块号
            
        Returns:
            标准化后的整数区块号
        """
        return self._normalize_value(block_number)
    
    def _normalize_transaction_index(self, index: str) -> int:
        """标准化交易索引
        
        Args:
            index: 十六进制字符串或其他格式的交易索引
            
        Returns:
            标准化后的整数交易索引
        """
        return self._normalize_value(index)
    
    def _normalize_log_index(self, index: str) -> int:
        """标准化日志索引
        
        Args:
            index: 十六进制字符串或其他格式的日志索引
            
        Returns:
            标准化后的整数日志索引
        """
        return self._normalize_value(index)
    
    def _normalize_timestamp(self, timestamp: str) -> int:
        """标准化时间戳
        
        Args:
            timestamp: 十六进制字符串或其他格式的时间戳
            
        Returns:
            标准化后的整数时间戳
        """
        return self._normalize_value(timestamp)

# 示例用法
if __name__ == "__main__":
    processor = DataProcessor()
    
    # 示例交易数据
    sample_tx = {
        "hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
        "from": "0x1234567890123456789012345678901234567890",
        "to": "0x0987654321098765432109876543210987654321",
        "value": "0xDE0B6B3A7640000",  # 1 ETH
        "gas": "0x5208",  # 21000
        "gasPrice": "0x4A817C800",  # 20 Gwei
        "nonce": "0x0",
        "input": "0x",
        "blockHash": "0x1234567890123456789012345678901234567890123456789012345678901234",
        "blockNumber": "0x1000000",
        "transactionIndex": "0x0"
    }
    
    processed_tx = processor.process_transaction(sample_tx, "ethereum")
    print("Processed transaction:")
    print(processed_tx)
