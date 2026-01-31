import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


class DataStorage:
    """
    数据存储类，用于存储和管理区块链数据
    """
    
    def __init__(self, db_path: str = "wallet_monitor.db"):
        """
        初始化数据存储
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """
        初始化数据库表结构
        """
        try:
            # 确保数据库目录存在
            os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建钱包表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                address TEXT UNIQUE NOT NULL,
                chain TEXT NOT NULL,
                name TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建交易表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE NOT NULL,
                wallet_address TEXT NOT NULL,
                chain TEXT NOT NULL,
                from_address TEXT,
                to_address TEXT,
                amount REAL DEFAULT 0,
                status TEXT DEFAULT 'unknown',
                timestamp INTEGER,
                block_number INTEGER,
                block_hash TEXT,
                gas_used INTEGER,
                gas_price INTEGER,
                input_data TEXT,
                is_contract_interaction INTEGER DEFAULT 0,
                contract_address TEXT,
                anomaly_score REAL DEFAULT 0,
                risk_level TEXT DEFAULT 'low',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # 创建告警表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                chain TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                risk_level TEXT DEFAULT 'low',
                transaction_hash TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
            ''')
            
            # 创建告警规则表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                rule_type TEXT NOT NULL,
                threshold REAL,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"初始化数据库失败: {e}")
    
    def add_wallet(self, address: str, chain: str, name: Optional[str] = None, description: Optional[str] = None) -> bool:
        """
        添加钱包
        
        Args:
            address: 钱包地址
            chain: 区块链类型
            name: 钱包名称
            description: 钱包描述
            
        Returns:
            是否添加成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR IGNORE INTO wallets (address, chain, name, description) VALUES (?, ?, ?, ?)",
                (address, chain, name, description)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加钱包失败: {e}")
            return False
    
    def get_wallets(self, chain: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取钱包列表
        
        Args:
            chain: 区块链类型，None表示获取所有链的钱包
            
        Returns:
            钱包列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if chain:
                cursor.execute("SELECT * FROM wallets WHERE chain = ? AND is_active = 1", (chain,))
            else:
                cursor.execute("SELECT * FROM wallets WHERE is_active = 1")
            
            wallets = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return wallets
        except Exception as e:
            print(f"获取钱包列表失败: {e}")
            return []
    
    def add_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        添加交易
        
        Args:
            transaction: 交易数据
            
        Returns:
            是否添加成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT OR IGNORE INTO transactions (
                    hash, wallet_address, chain, from_address, to_address, amount, status, 
                    timestamp, block_number, block_hash, gas_used, gas_price, input_data, 
                    is_contract_interaction, contract_address, anomaly_score, risk_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    transaction.get("hash"),
                    transaction.get("wallet_address"),
                    transaction.get("chain"),
                    transaction.get("from_address"),
                    transaction.get("to_address"),
                    transaction.get("amount", 0),
                    transaction.get("status", "unknown"),
                    transaction.get("timestamp"),
                    transaction.get("block_number"),
                    transaction.get("block_hash"),
                    transaction.get("gas_used"),
                    transaction.get("gas_price"),
                    transaction.get("input_data"),
                    1 if transaction.get("is_contract_interaction") else 0,
                    transaction.get("contract_address"),
                    transaction.get("anomaly_score", 0),
                    transaction.get("risk_level", "low")
                )
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加交易失败: {e}")
            return False
    
    def get_transactions(self, wallet_address: Optional[str] = None, chain: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取交易列表
        
        Args:
            wallet_address: 钱包地址，None表示获取所有钱包的交易
            chain: 区块链类型，None表示获取所有链的交易
            limit: 交易数量限制
            
        Returns:
            交易列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM transactions WHERE 1=1"
            params = []
            
            if wallet_address:
                query += " AND wallet_address = ?"
                params.append(wallet_address)
            
            if chain:
                query += " AND chain = ?"
                params.append(chain)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            transactions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return transactions
        except Exception as e:
            print(f"获取交易列表失败: {e}")
            return []
    
    def add_alert(self, alert: Dict[str, Any]) -> bool:
        """
        添加告警
        
        Args:
            alert: 告警数据
            
        Returns:
            是否添加成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT INTO alerts (
                    wallet_address, chain, alert_type, message, risk_level, transaction_hash
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    alert.get("wallet_address"),
                    alert.get("chain"),
                    alert.get("alert_type"),
                    alert.get("message"),
                    alert.get("risk_level", "low"),
                    alert.get("transaction_hash")
                )
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加告警失败: {e}")
            return False
    
    def get_alerts(self, wallet_address: Optional[str] = None, chain: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取告警列表
        
        Args:
            wallet_address: 钱包地址，None表示获取所有钱包的告警
            chain: 区块链类型，None表示获取所有链的告警
            limit: 告警数量限制
            
        Returns:
            告警列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM alerts WHERE 1=1"
            params = []
            
            if wallet_address:
                query += " AND wallet_address = ?"
                params.append(wallet_address)
            
            if chain:
                query += " AND chain = ?"
                params.append(chain)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            alerts = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return alerts
        except Exception as e:
            print(f"获取告警列表失败: {e}")
            return []
    
    def add_alert_rule(self, rule: Dict[str, Any]) -> bool:
        """
        添加告警规则
        
        Args:
            rule: 规则数据
            
        Returns:
            是否添加成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT OR IGNORE INTO alert_rules (
                    name, description, rule_type, threshold, enabled
                ) VALUES (?, ?, ?, ?, ?)
                ''',
                (
                    rule.get("name"),
                    rule.get("description"),
                    rule.get("rule_type"),
                    rule.get("threshold"),
                    1 if rule.get("enabled", True) else 0
                )
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"添加告警规则失败: {e}")
            return False
    
    def get_alert_rules(self, enabled_only: bool = True) -> List[Dict[str, Any]]:
        """
        获取告警规则列表
        
        Args:
            enabled_only: 是否只获取启用的规则
            
        Returns:
            规则列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if enabled_only:
                cursor.execute("SELECT * FROM alert_rules WHERE enabled = 1")
            else:
                cursor.execute("SELECT * FROM alert_rules")
            
            rules = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return rules
        except Exception as e:
            print(f"获取告警规则列表失败: {e}")
            return []
    
    def close(self):
        """
        关闭数据库连接
        """
        # SQLite是文件数据库，不需要显式关闭连接
        pass
