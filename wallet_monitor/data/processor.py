from typing import List, Dict, Any, Optional
from datetime import datetime
import json


class DataProcessor:
    """
    数据处理类，用于清洗、标准化和处理区块链数据
    """
    
    @staticmethod
    def clean_transaction(transaction: Dict[str, Any], chain_type: str) -> Dict[str, Any]:
        """
        清洗交易数据
        
        Args:
            transaction: 原始交易数据
            chain_type: 区块链类型
            
        Returns:
            清洗后的交易数据
        """
        try:
            cleaned_tx = {
                "chain": chain_type,
                "timestamp": DataProcessor._extract_timestamp(transaction, chain_type),
                "hash": DataProcessor._extract_tx_hash(transaction, chain_type),
                "from_address": DataProcessor._extract_from_address(transaction, chain_type),
                "to_address": DataProcessor._extract_to_address(transaction, chain_type),
                "amount": DataProcessor._extract_amount(transaction, chain_type),
                "status": DataProcessor._extract_status(transaction, chain_type),
                "gas_used": DataProcessor._extract_gas_used(transaction, chain_type),
                "gas_price": DataProcessor._extract_gas_price(transaction, chain_type),
                "input_data": DataProcessor._extract_input_data(transaction, chain_type),
                "block_number": DataProcessor._extract_block_number(transaction, chain_type),
                "block_hash": DataProcessor._extract_block_hash(transaction, chain_type),
                "is_contract_interaction": DataProcessor._is_contract_interaction(transaction, chain_type),
                "contract_address": DataProcessor._extract_contract_address(transaction, chain_type)
            }
            return cleaned_tx
        except Exception as e:
            print(f"清洗交易数据失败: {e}")
            return {}
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """
        标准化地址格式
        
        Args:
            address: 原始地址
            
        Returns:
            标准化后的地址
        """
        try:
            # 去除前缀和空格
            address = address.strip()
            # 确保地址是小写
            return address.lower()
        except Exception as e:
            print(f"标准化地址失败: {e}")
            return address
    
    @staticmethod
    def parse_contract_interaction(input_data: str, abi: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        解析智能合约交互
        
        Args:
            input_data: 交易输入数据
            abi: 合约ABI，可选
            
        Returns:
            解析后的合约交互信息
        """
        try:
            # 这里实现合约交互解析逻辑
            # 暂时返回基础信息
            return {
                "function_signature": input_data[:10] if input_data else None,
                "params": input_data[10:] if input_data else None,
                "parsed": False
            }
        except Exception as e:
            print(f"解析合约交互失败: {e}")
            return {}
    
    @staticmethod
    def detect_anomaly(transaction: Dict[str, Any], wallet_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        检测交易异常
        
        Args:
            transaction: 交易数据
            wallet_history: 钱包历史交易
            
        Returns:
            异常检测结果
        """
        try:
            anomaly_score = 0
            anomalies = []
            
            # 检查交易金额是否异常
            amount = transaction.get("amount", 0)
            avg_amount = DataProcessor._calculate_avg_amount(wallet_history)
            if amount > avg_amount * 3:
                anomaly_score += 0.5
                anomalies.append("大额交易")
            
            # 检查是否是陌生地址
            to_address = transaction.get("to_address")
            if not DataProcessor._is_familiar_address(to_address, wallet_history):
                anomaly_score += 0.3
                anomalies.append("陌生地址交易")
            
            # 检查交易频率
            if DataProcessor._is_frequent_transaction(transaction, wallet_history):
                anomaly_score += 0.2
                anomalies.append("频繁交易")
            
            return {
                "anomaly_score": anomaly_score,
                "anomalies": anomalies,
                "risk_level": DataProcessor._calculate_risk_level(anomaly_score)
            }
        except Exception as e:
            print(f"检测异常失败: {e}")
            return {}
    
    # 辅助方法
    @staticmethod
    def _extract_timestamp(transaction: Dict[str, Any], chain_type: str) -> Optional[int]:
        """
        提取时间戳
        """
        if chain_type == "ethereum":
            return transaction.get("blockTime") or transaction.get("timestamp")
        elif chain_type == "solana":
            return transaction.get("block_time")
        return None
    
    @staticmethod
    def _extract_tx_hash(transaction: Dict[str, Any], chain_type: str) -> Optional[str]:
        """
        提取交易哈希
        """
        if chain_type == "ethereum":
            return transaction.get("hash") or transaction.get("transactionHash")
        elif chain_type == "solana":
            return transaction.get("signature")
        return None
    
    @staticmethod
    def _extract_from_address(transaction: Dict[str, Any], chain_type: str) -> Optional[str]:
        """
        提取发送地址
        """
        if chain_type == "ethereum":
            return transaction.get("from") or transaction.get("fromAddress")
        elif chain_type == "solana":
            # Solana交易结构不同，需要特殊处理
            return None
        return None
    
    @staticmethod
    def _extract_to_address(transaction: Dict[str, Any], chain_type: str) -> Optional[str]:
        """
        提取接收地址
        """
        if chain_type == "ethereum":
            return transaction.get("to") or transaction.get("toAddress")
        elif chain_type == "solana":
            # Solana交易结构不同，需要特殊处理
            return None
        return None
    
    @staticmethod
    def _extract_amount(transaction: Dict[str, Any], chain_type: str) -> float:
        """
        提取交易金额
        """
        if chain_type == "ethereum":
            return float(transaction.get("value", 0))
        elif chain_type == "solana":
            return float(transaction.get("amount", 0))
        return 0.0
    
    @staticmethod
    def _extract_status(transaction: Dict[str, Any], chain_type: str) -> str:
        """
        提取交易状态
        """
        if chain_type == "ethereum":
            return transaction.get("status", "unknown")
        elif chain_type == "solana":
            return transaction.get("status", "unknown")
        return "unknown"
    
    @staticmethod
    def _extract_gas_used(transaction: Dict[str, Any], chain_type: str) -> Optional[int]:
        """
        提取使用的gas
        """
        if chain_type == "ethereum":
            return transaction.get("gasUsed")
        return None
    
    @staticmethod
    def _extract_gas_price(transaction: Dict[str, Any], chain_type: str) -> Optional[int]:
        """
        提取gas价格
        """
        if chain_type == "ethereum":
            return transaction.get("gasPrice")
        return None
    
    @staticmethod
    def _extract_input_data(transaction: Dict[str, Any], chain_type: str) -> Optional[str]:
        """
        提取输入数据
        """
        if chain_type == "ethereum":
            return transaction.get("input")
        return None
    
    @staticmethod
    def _extract_block_number(transaction: Dict[str, Any], chain_type: str) -> Optional[int]:
        """
        提取区块号
        """
        if chain_type == "ethereum":
            return transaction.get("blockNumber")
        elif chain_type == "solana":
            return transaction.get("slot")
        return None
    
    @staticmethod
    def _extract_block_hash(transaction: Dict[str, Any], chain_type: str) -> Optional[str]:
        """
        提取区块哈希
        """
        if chain_type == "ethereum":
            return transaction.get("blockHash")
        return None
    
    @staticmethod
    def _is_contract_interaction(transaction: Dict[str, Any], chain_type: str) -> bool:
        """
        判断是否是合约交互
        """
        if chain_type == "ethereum":
            input_data = transaction.get("input", "")
            return len(input_data) > 2  # 非空input数据通常表示合约交互
        return False
    
    @staticmethod
    def _extract_contract_address(transaction: Dict[str, Any], chain_type: str) -> Optional[str]:
        """
        提取合约地址
        """
        if chain_type == "ethereum":
            return transaction.get("to")  # 对于合约交互，to地址就是合约地址
        return None
    
    @staticmethod
    def _calculate_avg_amount(transactions: List[Dict[str, Any]]) -> float:
        """
        计算平均交易金额
        """
        if not transactions:
            return 0.0
        total = sum(tx.get("amount", 0) for tx in transactions)
        return total / len(transactions)
    
    @staticmethod
    def _is_familiar_address(address: str, transactions: List[Dict[str, Any]]) -> bool:
        """
        判断是否是熟悉的地址
        """
        if not address:
            return False
        # 检查该地址是否在历史交易中出现过
        for tx in transactions:
            if tx.get("from_address") == address or tx.get("to_address") == address:
                return True
        return False
    
    @staticmethod
    def _is_frequent_transaction(transaction: Dict[str, Any], transactions: List[Dict[str, Any]]) -> bool:
        """
        判断是否是频繁交易
        """
        if not transactions:
            return False
        # 检查最近1小时内的交易数量
        timestamp = transaction.get("timestamp")
        if not timestamp:
            return False
        recent_transactions = [tx for tx in transactions if tx.get("timestamp") and timestamp - tx.get("timestamp") < 3600]
        return len(recent_transactions) > 10
    
    @staticmethod
    def _calculate_risk_level(anomaly_score: float) -> str:
        """
        计算风险等级
        """
        if anomaly_score >= 0.8:
            return "high"
        elif anomaly_score >= 0.4:
            return "medium"
        else:
            return "low"
