from typing import List, Dict, Any, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - alert-engine - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertRuleEngine:
    """
    告警规则引擎，用于管理和执行告警规则
    """
    
    def __init__(self):
        """
        初始化告警规则引擎
        """
        self.rules = []
        self.load_rules()
    
    def load_rules(self):
        """
        加载告警规则
        """
        try:
            from data.storage import DataStorage
            storage = DataStorage()
            self.rules = storage.get_alert_rules(enabled_only=True)
            logger.info(f"加载了 {len(self.rules)} 条告警规则")
        except Exception as e:
            # 尝试使用相对路径导入
            try:
                from ..data.storage import DataStorage
                storage = DataStorage()
                self.rules = storage.get_alert_rules(enabled_only=True)
                logger.info(f"加载了 {len(self.rules)} 条告警规则（使用相对路径）")
            except Exception as e2:
                logger.error(f"加载告警规则失败: {e2}")
                self.rules = []
    
    def evaluate_transaction(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        评估交易是否触发告警规则
        
        Args:
            transaction: 交易数据
            
        Returns:
            触发的告警列表
        """
        alerts = []
        
        for rule in self.rules:
            if rule.get("rule_type") == "transaction":
                alert = self._evaluate_transaction_rule(rule, transaction)
                if alert:
                    alerts.append(alert)
        
        return alerts
    
    def evaluate_balance(self, wallet_address: str, chain: str, balance: float) -> List[Dict[str, Any]]:
        """
        评估钱包余额是否触发告警规则
        
        Args:
            wallet_address: 钱包地址
            chain: 区块链类型
            balance: 钱包余额
            
        Returns:
            触发的告警列表
        """
        alerts = []
        
        for rule in self.rules:
            if rule.get("rule_type") == "balance":
                alert = self._evaluate_balance_rule(rule, wallet_address, chain, balance)
                if alert:
                    alerts.append(alert)
        
        return alerts
    
    def evaluate_contract(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        评估合约交互是否触发告警规则
        
        Args:
            transaction: 交易数据
            
        Returns:
            触发的告警列表
        """
        alerts = []
        
        for rule in self.rules:
            if rule.get("rule_type") == "contract":
                alert = self._evaluate_contract_rule(rule, transaction)
                if alert:
                    alerts.append(alert)
        
        return alerts
    
    def evaluate_anomaly(self, transaction: Dict[str, Any], wallet_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        评估交易是否为异常交易
        
        Args:
            transaction: 交易数据
            wallet_history: 钱包历史交易
            
        Returns:
            触发的告警列表
        """
        alerts = []
        
        for rule in self.rules:
            if rule.get("rule_type") == "anomaly":
                alert = self._evaluate_anomaly_rule(rule, transaction, wallet_history)
                if alert:
                    alerts.append(alert)
        
        return alerts
    
    def _evaluate_transaction_rule(self, rule: Dict[str, Any], transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        评估交易规则
        """
        try:
            amount = transaction.get("amount", 0)
            threshold = rule.get("threshold", 0)
            
            if amount > threshold:
                return {
                    "wallet_address": transaction.get("wallet_address"),
                    "chain": transaction.get("chain"),
                    "alert_type": "transaction",
                    "message": f"交易金额超过阈值: ${amount} > ${threshold}",
                    "risk_level": "high" if amount > threshold * 2 else "medium",
                    "transaction_hash": transaction.get("hash")
                }
            return None
        except Exception as e:
            logger.error(f"评估交易规则失败: {e}")
            return None
    
    def _evaluate_balance_rule(self, rule: Dict[str, Any], wallet_address: str, chain: str, balance: float) -> Optional[Dict[str, Any]]:
        """
        评估余额规则
        """
        try:
            threshold = rule.get("threshold", 0)
            
            if balance < threshold:
                return {
                    "wallet_address": wallet_address,
                    "chain": chain,
                    "alert_type": "balance",
                    "message": f"钱包余额低于阈值: ${balance} < ${threshold}",
                    "risk_level": "high" if balance < threshold * 0.5 else "medium"
                }
            return None
        except Exception as e:
            logger.error(f"评估余额规则失败: {e}")
            return None
    
    def _evaluate_contract_rule(self, rule: Dict[str, Any], transaction: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        评估合约交互规则
        """
        try:
            if transaction.get("is_contract_interaction"):
                return {
                    "wallet_address": transaction.get("wallet_address"),
                    "chain": transaction.get("chain"),
                    "alert_type": "contract",
                    "message": f"检测到合约交互: {transaction.get('contract_address')}",
                    "risk_level": "medium",
                    "transaction_hash": transaction.get("hash")
                }
            return None
        except Exception as e:
            logger.error(f"评估合约规则失败: {e}")
            return None
    
    def _evaluate_anomaly_rule(self, rule: Dict[str, Any], transaction: Dict[str, Any], wallet_history: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        评估异常交易规则
        """
        try:
            # 计算历史交易的平均金额
            if wallet_history:
                avg_amount = sum(tx.get("amount", 0) for tx in wallet_history) / len(wallet_history)
                current_amount = transaction.get("amount", 0)
                
                threshold = rule.get("threshold", 3)
                if current_amount > avg_amount * threshold:
                    return {
                        "wallet_address": transaction.get("wallet_address"),
                        "chain": transaction.get("chain"),
                        "alert_type": "anomaly",
                        "message": f"检测到异常交易: ${current_amount} (平均: ${avg_amount})",
                        "risk_level": "high",
                        "transaction_hash": transaction.get("hash")
                    }
            return None
        except Exception as e:
            logger.error(f"评估异常规则失败: {e}")
            return None
    
    def add_alert(self, alert: Dict[str, Any]) -> bool:
        """
        添加告警
        
        Args:
            alert: 告警数据
            
        Returns:
            是否添加成功
        """
        try:
            from data.storage import DataStorage
            storage = DataStorage()
            success = storage.add_alert(alert)
            if success:
                logger.info(f"添加告警成功: {alert.get('message')}")
            else:
                logger.error(f"添加告警失败: {alert.get('message')}")
            return success
        except Exception as e:
            # 尝试使用相对路径导入
            try:
                from ..data.storage import DataStorage
                storage = DataStorage()
                success = storage.add_alert(alert)
                if success:
                    logger.info(f"添加告警成功: {alert.get('message')}（使用相对路径）")
                else:
                    logger.error(f"添加告警失败: {alert.get('message')}（使用相对路径）")
                return success
            except Exception as e2:
                logger.error(f"添加告警失败: {e2}")
                return False
    
    def get_alerts(self, wallet_address: Optional[str] = None, chain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取告警列表
        
        Args:
            wallet_address: 钱包地址
            chain: 区块链类型
            
        Returns:
            告警列表
        """
        try:
            from data.storage import DataStorage
            storage = DataStorage()
            return storage.get_alerts(wallet_address=wallet_address, chain=chain)
        except Exception as e:
            # 尝试使用相对路径导入
            try:
                from ..data.storage import DataStorage
                storage = DataStorage()
                return storage.get_alerts(wallet_address=wallet_address, chain=chain)
            except Exception as e2:
                logger.error(f"获取告警列表失败: {e2}")
                return []
