# 告警系统模块
# 负责告警规则的管理和告警的触发

from typing import Dict, List, Any
import re
import json
from datetime import datetime

class AlertEngine:
    def __init__(self, storage):
        """初始化告警引擎
        
        Args:
            storage: 数据存储实例
        """
        self.storage = storage
        self.rules = []
        self._load_rules()
    
    def _load_rules(self):
        """加载告警规则"""
        self.rules = self.storage.get_alert_rules(is_active=True)
    
    def check_transaction(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检查交易是否触发告警规则
        
        Args:
            transaction: 交易数据
            
        Returns:
            告警列表
        """
        alerts = []
        
        for rule in self.rules:
            if self._match_rule(transaction, rule):
                alert = self._create_alert(transaction, rule)
                alerts.append(alert)
        
        return alerts
    
    def _match_rule(self, transaction: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """检查交易是否匹配告警规则
        
        Args:
            transaction: 交易数据
            rule: 告警规则
            
        Returns:
            是否匹配
        """
        rule_type = rule.get("type")
        rule_def = rule.get("rule")
        
        if rule_type == "large_transaction":
            return self._match_large_transaction(transaction, rule_def)
        elif rule_type == "unknown_address":
            return self._match_unknown_address(transaction, rule_def)
        elif rule_type == "frequent_transactions":
            return self._match_frequent_transactions(transaction, rule_def)
        else:
            return False
    
    def _match_large_transaction(self, transaction: Dict[str, Any], rule_def: str) -> bool:
        """匹配大额转账规则
        
        Args:
            transaction: 交易数据
            rule_def: 规则定义，如 "value > 1000000000000000000" (1 ETH)
            
        Returns:
            是否匹配
        """
        # 解析规则，如 "value > 1000000000000000000"
        pattern = r"value\s*(>|<|>=|<=|==)\s*(\d+)"
        match = re.match(pattern, rule_def)
        
        if not match:
            return False
        
        operator = match.group(1)
        threshold = int(match.group(2))
        value = transaction.get("value", 0)
        
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        else:
            return False
    
    def _match_unknown_address(self, transaction: Dict[str, Any], rule_def: str) -> bool:
        """匹配陌生地址规则
        
        Args:
            transaction: 交易数据
            rule_def: 规则定义，如 "unknown_address"
            
        Returns:
            是否匹配
        """
        # 这里简化实现，实际应该检查地址是否在已知地址列表中
        # 例如，检查是否与用户的其他钱包地址交互过
        from_address = transaction.get("from")
        to_address = transaction.get("to")
        
        # 获取所有已知钱包地址
        wallets = self.storage.get_wallets()
        known_addresses = [wallet.get("address") for wallet in wallets]
        
        # 检查是否与陌生地址交互
        if from_address not in known_addresses and to_address not in known_addresses:
            return True
        
        return False
    
    def _match_frequent_transactions(self, transaction: Dict[str, Any], rule_def: str) -> bool:
        """匹配频繁交易规则
        
        Args:
            transaction: 交易数据
            rule_def: 规则定义，如 "count > 10 in 3600" (10笔交易/小时)
            
        Returns:
            是否匹配
        """
        # 解析规则，如 "count > 10 in 3600"
        pattern = r"count\s*(>|<|>=|<=|==)\s*(\d+)\s*in\s*(\d+)"
        match = re.match(pattern, rule_def)
        
        if not match:
            return False
        
        operator = match.group(1)
        count_threshold = int(match.group(2))
        time_window = int(match.group(3))
        
        # 获取当前时间
        current_time = transaction.get("timestamp", int(datetime.now().timestamp()))
        
        # 获取时间窗口内的交易数量
        wallet_address = transaction.get("from") or transaction.get("to")
        recent_transactions = self.storage.get_transactions(
            wallet_address=wallet_address,
            chain=transaction.get("chain"),
            limit=100
        )
        
        # 统计时间窗口内的交易数量
        window_start = current_time - time_window
        window_transactions = [
            tx for tx in recent_transactions
            if tx.get("timestamp", 0) >= window_start
        ]
        
        transaction_count = len(window_transactions)
        
        if operator == ">":
            return transaction_count > count_threshold
        elif operator == "<":
            return transaction_count < count_threshold
        elif operator == ">=":
            return transaction_count >= count_threshold
        elif operator == "<=":
            return transaction_count <= count_threshold
        elif operator == "==":
            return transaction_count == count_threshold
        else:
            return False
    
    def _create_alert(self, transaction: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """创建告警
        
        Args:
            transaction: 交易数据
            rule: 告警规则
            
        Returns:
            告警数据
        """
        message = f"交易触发告警: {rule.get('name')}"
        
        alert_data = {
            "rule_id": rule.get("id"),
            "wallet_address": transaction.get("from") or transaction.get("to"),
            "transaction_hash": transaction.get("hash"),
            "message": message,
            "level": rule.get("level")
        }
        
        # 保存告警到数据库
        alert_id = self.storage.add_alert(
            rule_id=alert_data["rule_id"],
            wallet_address=alert_data["wallet_address"],
            transaction_hash=alert_data["transaction_hash"],
            message=alert_data["message"],
            level=alert_data["level"]
        )
        
        alert_data["id"] = alert_id
        return alert_data
    
    def add_rule(self, name: str, type: str, rule: str, level: str) -> int:
        """添加告警规则
        
        Args:
            name: 规则名称
            type: 规则类型
            rule: 规则定义
            level: 风险等级
            
        Returns:
            规则ID
        """
        rule_id = self.storage.add_alert_rule(name, type, rule, level)
        self._load_rules()  # 重新加载规则
        return rule_id
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """获取告警规则列表
        
        Returns:
            告警规则列表
        """
        return self.rules

# 示例用法
if __name__ == "__main__":
    from data.storage import DataStorage
    
    storage = DataStorage()
    engine = AlertEngine(storage)
    
    # 添加测试规则
    engine.add_rule(
        name="大额转账",
        type="large_transaction",
        rule="value > 1000000000000000000",  # 1 ETH
        level="high"
    )
    
    # 测试交易
    test_transaction = {
        "hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
        "from": "0x1234567890123456789012345678901234567890",
        "to": "0x0987654321098765432109876543210987654321",
        "value": 2000000000000000000,  # 2 ETH
        "gas": 21000,
        "gas_price": 20000000000,
        "nonce": "0",
        "input": "0x",
        "block_hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
        "block_number": 1000000,
        "transaction_index": 0,
        "chain": "ethereum",
        "timestamp": int(datetime.now().timestamp()),
        "processed_at": int(datetime.now().timestamp())
    }
    
    # 检查交易
    alerts = engine.check_transaction(test_transaction)
    print(f"触发告警数量: {len(alerts)}")
    for alert in alerts:
        print(f"告警: {alert.get('message')}, 等级: {alert.get('level')}")
