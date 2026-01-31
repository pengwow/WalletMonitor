from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta


class DataAnalyzer:
    """
    数据分析类，用于分析和统计区块链数据
    """
    
    @staticmethod
    def analyze_wallet_activity(wallet_address: str, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析钱包活动
        
        Args:
            wallet_address: 钱包地址
            transactions: 交易列表
            
        Returns:
            钱包活动分析结果
        """
        try:
            if not transactions:
                return {
                    "wallet_address": wallet_address,
                    "total_transactions": 0,
                    "total_incoming": 0,
                    "total_outgoing": 0,
                    "total_volume": 0,
                    "avg_transaction_amount": 0,
                    "most_active_day": None,
                    "transaction_count_by_day": {},
                    "contract_interactions": 0,
                    "anomaly_count": 0
                }
            
            # 计算总交易数
            total_transactions = len(transactions)
            
            # 计算收入和支出
            total_incoming = 0
            total_outgoing = 0
            total_volume = 0
            
            for tx in transactions:
                amount = tx.get("amount", 0)
                total_volume += amount
                
                if tx.get("from_address") == wallet_address:
                    total_outgoing += amount
                elif tx.get("to_address") == wallet_address:
                    total_incoming += amount
            
            # 计算平均交易金额
            avg_transaction_amount = total_volume / total_transactions if total_transactions > 0 else 0
            
            # 分析交易时间分布
            transaction_count_by_day = {}
            for tx in transactions:
                timestamp = tx.get("timestamp")
                if timestamp:
                    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                    transaction_count_by_day[date] = transaction_count_by_day.get(date, 0) + 1
            
            # 找出最活跃的一天
            most_active_day = None
            max_count = 0
            for date, count in transaction_count_by_day.items():
                if count > max_count:
                    max_count = count
                    most_active_day = date
            
            # 计算合约交互次数
            contract_interactions = sum(1 for tx in transactions if tx.get("is_contract_interaction"))
            
            # 计算异常交易次数
            anomaly_count = sum(1 for tx in transactions if tx.get("risk_level") in ["medium", "high"])
            
            return {
                "wallet_address": wallet_address,
                "total_transactions": total_transactions,
                "total_incoming": total_incoming,
                "total_outgoing": total_outgoing,
                "total_volume": total_volume,
                "avg_transaction_amount": avg_transaction_amount,
                "most_active_day": most_active_day,
                "transaction_count_by_day": transaction_count_by_day,
                "contract_interactions": contract_interactions,
                "anomaly_count": anomaly_count
            }
        except Exception as e:
            print(f"分析钱包活动失败: {e}")
            return {}
    
    @staticmethod
    def analyze_asset_distribution(wallets: List[Dict[str, Any]], blockchain_instances: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析资产分布
        
        Args:
            wallets: 钱包列表
            blockchain_instances: 区块链实例字典
            
        Returns:
            资产分布分析结果
        """
        try:
            asset_distribution = {
                "total_value": 0,
                "by_chain": {},
                "by_wallet": {}
            }
            
            for wallet in wallets:
                address = wallet.get("address")
                chain = wallet.get("chain")
                
                if address and chain and chain in blockchain_instances:
                    blockchain = blockchain_instances.get(chain)
                    balance = blockchain.get_balance(address)
                    
                    # 更新总价值
                    asset_distribution["total_value"] += balance
                    
                    # 更新按链分布
                    if chain not in asset_distribution["by_chain"]:
                        asset_distribution["by_chain"][chain] = 0
                    asset_distribution["by_chain"][chain] += balance
                    
                    # 更新按钱包分布
                    asset_distribution["by_wallet"][address] = {
                        "balance": balance,
                        "chain": chain,
                        "name": wallet.get("name")
                    }
            
            return asset_distribution
        except Exception as e:
            print(f"分析资产分布失败: {e}")
            return {}
    
    @staticmethod
    def analyze_transaction_trends(transactions: List[Dict[str, Any]], days: int = 30) -> Dict[str, Any]:
        """
        分析交易趋势
        
        Args:
            transactions: 交易列表
            days: 分析天数
            
        Returns:
            交易趋势分析结果
        """
        try:
            # 计算起始时间
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)
            start_timestamp = int(start_time.timestamp())
            
            # 过滤时间范围内的交易
            recent_transactions = [tx for tx in transactions if tx.get("timestamp") and tx.get("timestamp") >= start_timestamp]
            
            # 按天分组交易
            transactions_by_day = {}
            for tx in recent_transactions:
                timestamp = tx.get("timestamp")
                if timestamp:
                    date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                    if date not in transactions_by_day:
                        transactions_by_day[date] = {
                            "count": 0,
                            "volume": 0,
                            "incoming": 0,
                            "outgoing": 0
                        }
                    transactions_by_day[date]["count"] += 1
                    transactions_by_day[date]["volume"] += tx.get("amount", 0)
                    
                    # 这里简化处理，假设所有交易都是与钱包相关的
                    # 实际应用中需要根据from_address和to_address判断
                    transactions_by_day[date]["incoming"] += tx.get("amount", 0)
            
            # 计算每日平均值
            avg_daily_count = sum(data["count"] for data in transactions_by_day.values()) / len(transactions_by_day) if transactions_by_day else 0
            avg_daily_volume = sum(data["volume"] for data in transactions_by_day.values()) / len(transactions_by_day) if transactions_by_day else 0
            
            # 计算趋势
            trend = "stable"
            if len(transactions_by_day) >= 2:
                dates = sorted(transactions_by_day.keys())
                first_half = dates[:len(dates)//2]
                second_half = dates[len(dates)//2:]
                
                first_half_volume = sum(transactions_by_day[date]["volume"] for date in first_half)
                second_half_volume = sum(transactions_by_day[date]["volume"] for date in second_half)
                
                if second_half_volume > first_half_volume * 1.2:
                    trend = "increasing"
                elif second_half_volume < first_half_volume * 0.8:
                    trend = "decreasing"
            
            return {
                "period": f"{days}天",
                "total_transactions": len(recent_transactions),
                "total_volume": sum(tx.get("amount", 0) for tx in recent_transactions),
                "avg_daily_count": avg_daily_count,
                "avg_daily_volume": avg_daily_volume,
                "transactions_by_day": transactions_by_day,
                "trend": trend
            }
        except Exception as e:
            print(f"分析交易趋势失败: {e}")
            return {}
    
    @staticmethod
    def analyze_alert_patterns(alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析告警模式
        
        Args:
            alerts: 告警列表
            
        Returns:
            告警模式分析结果
        """
        try:
            alert_analysis = {
                "total_alerts": len(alerts),
                "by_risk_level": {
                    "low": 0,
                    "medium": 0,
                    "high": 0
                },
                "by_type": {},
                "by_wallet": {},
                "by_chain": {}
            }
            
            for alert in alerts:
                risk_level = alert.get("risk_level", "low")
                alert_type = alert.get("alert_type")
                wallet_address = alert.get("wallet_address")
                chain = alert.get("chain")
                
                # 更新按风险等级分布
                if risk_level in alert_analysis["by_risk_level"]:
                    alert_analysis["by_risk_level"][risk_level] += 1
                
                # 更新按类型分布
                if alert_type:
                    if alert_type not in alert_analysis["by_type"]:
                        alert_analysis["by_type"][alert_type] = 0
                    alert_analysis["by_type"][alert_type] += 1
                
                # 更新按钱包分布
                if wallet_address:
                    if wallet_address not in alert_analysis["by_wallet"]:
                        alert_analysis["by_wallet"][wallet_address] = 0
                    alert_analysis["by_wallet"][wallet_address] += 1
                
                # 更新按链分布
                if chain:
                    if chain not in alert_analysis["by_chain"]:
                        alert_analysis["by_chain"][chain] = 0
                    alert_analysis["by_chain"][chain] += 1
            
            return alert_analysis
        except Exception as e:
            print(f"分析告警模式失败: {e}")
            return {}
    
    @staticmethod
    def detect_wallet_anomalies(wallet_address: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检测钱包异常
        
        Args:
            wallet_address: 钱包地址
            transactions: 交易列表
            
        Returns:
            异常列表
        """
        try:
            anomalies = []
            
            if not transactions:
                return anomalies
            
            # 计算统计数据
            amounts = [tx.get("amount", 0) for tx in transactions if tx.get("amount", 0) > 0]
            if not amounts:
                return anomalies
            
            avg_amount = sum(amounts) / len(amounts)
            max_amount = max(amounts)
            
            # 检测大额交易
            for tx in transactions:
                amount = tx.get("amount", 0)
                if amount > avg_amount * 3:
                    anomalies.append({
                        "type": "大额交易",
                        "transaction_hash": tx.get("hash"),
                        "amount": amount,
                        "average_amount": avg_amount,
                        "timestamp": tx.get("timestamp"),
                        "risk_level": "high" if amount > max_amount * 0.8 else "medium"
                    })
            
            # 检测频繁交易
            transaction_times = sorted([tx.get("timestamp") for tx in transactions if tx.get("timestamp")])
            for i in range(1, len(transaction_times)):
                time_diff = transaction_times[i] - transaction_times[i-1]
                if time_diff < 60:  # 60秒内的交易
                    anomalies.append({
                        "type": "频繁交易",
                        "time_diff": time_diff,
                        "timestamp": transaction_times[i],
                        "risk_level": "medium"
                    })
            
            return anomalies
        except Exception as e:
            print(f"检测钱包异常失败: {e}")
            return []
