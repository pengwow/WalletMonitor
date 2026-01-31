# 数据存储模块
# 负责存储和管理区块链数据

import sqlite3
import json
from typing import Dict, List, Any
import os

class DataStorage:
    def __init__(self, db_path: str = "wallet_monitor.db"):
        """初始化数据存储
        
        Args:
            db_path: SQLite数据库文件路径
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
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
            balance INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建交易表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE NOT NULL,
            from_address TEXT NOT NULL,
            to_address TEXT NOT NULL,
            value INTEGER NOT NULL,
            gas INTEGER NOT NULL,
            gas_price INTEGER NOT NULL,
            nonce TEXT,
            input TEXT,
            block_hash TEXT,
            block_number INTEGER,
            transaction_index INTEGER,
            chain TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            processed_at INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建区块表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash TEXT UNIQUE NOT NULL,
            number INTEGER NOT NULL,
            parent_hash TEXT,
            nonce TEXT,
            sha3_uncles TEXT,
            logs_bloom TEXT,
            transactions_root TEXT,
            state_root TEXT,
            receipts_root TEXT,
            miner TEXT,
            difficulty INTEGER,
            total_difficulty INTEGER,
            size INTEGER,
            extra_data TEXT,
            gas_limit INTEGER,
            gas_used INTEGER,
            timestamp INTEGER,
            transactions_count INTEGER,
            chain TEXT NOT NULL,
            processed_at INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建告警规则表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            rule TEXT NOT NULL,
            level TEXT NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 创建告警历史表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id INTEGER,
            wallet_address TEXT,
            transaction_hash TEXT,
            message TEXT NOT NULL,
            level TEXT NOT NULL,
            status TEXT DEFAULT 'unprocessed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (rule_id) REFERENCES alert_rules (id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_wallet(self, address: str, chain: str, name: str = None, description: str = None) -> int:
        """添加钱包
        
        Args:
            address: 钱包地址
            chain: 区块链名称
            name: 钱包名称
            description: 钱包描述
            
        Returns:
            钱包ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT OR IGNORE INTO wallets (address, chain, name, description) VALUES (?, ?, ?, ?)",
            (address, chain, name, description)
        )
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid
    
    def get_wallets(self, chain: str = None) -> List[Dict[str, Any]]:
        """获取钱包列表
        
        Args:
            chain: 区块链名称，None表示所有链
            
        Returns:
            钱包列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if chain:
            cursor.execute("SELECT * FROM wallets WHERE chain = ? AND is_active = 1", (chain,))
        else:
            cursor.execute("SELECT * FROM wallets WHERE is_active = 1")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_transaction(self, transaction: Dict[str, Any]) -> int:
        """添加交易
        
        Args:
            transaction: 交易数据
            
        Returns:
            交易ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            INSERT OR IGNORE INTO transactions (
                hash, from_address, to_address, value, gas, gas_price, nonce, input, 
                block_hash, block_number, transaction_index, chain, timestamp, processed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                transaction.get("hash"),
                transaction.get("from"),
                transaction.get("to"),
                transaction.get("value"),
                transaction.get("gas"),
                transaction.get("gas_price"),
                transaction.get("nonce"),
                transaction.get("input"),
                transaction.get("block_hash"),
                transaction.get("block_number"),
                transaction.get("transaction_index"),
                transaction.get("chain"),
                transaction.get("timestamp"),
                transaction.get("processed_at")
            )
        )
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid
    
    def get_transactions(self, wallet_address: str = None, chain: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取交易列表
        
        Args:
            wallet_address: 钱包地址，None表示所有地址
            chain: 区块链名称，None表示所有链
            limit: 返回数量限制
            
        Returns:
            交易列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM transactions WHERE 1=1"
        params = []
        
        if wallet_address:
            query += " AND (from_address = ? OR to_address = ?)"
            params.extend([wallet_address, wallet_address])
        
        if chain:
            query += " AND chain = ?"
            params.append(chain)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_alert_rule(self, name: str, type: str, rule: str, level: str) -> int:
        """添加告警规则
        
        Args:
            name: 规则名称
            type: 规则类型
            rule: 规则定义
            level: 风险等级
            
        Returns:
            规则ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO alert_rules (name, type, rule, level) VALUES (?, ?, ?, ?)",
            (name, type, rule, level)
        )
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid
    
    def get_alert_rules(self, is_active: bool = True) -> List[Dict[str, Any]]:
        """获取告警规则
        
        Args:
            is_active: 是否只获取激活的规则
            
        Returns:
            告警规则列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if is_active:
            cursor.execute("SELECT * FROM alert_rules WHERE is_active = 1")
        else:
            cursor.execute("SELECT * FROM alert_rules")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def add_alert(self, rule_id: int, wallet_address: str, transaction_hash: str, message: str, level: str) -> int:
        """添加告警
        
        Args:
            rule_id: 规则ID
            wallet_address: 钱包地址
            transaction_hash: 交易哈希
            message: 告警消息
            level: 风险等级
            
        Returns:
            告警ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO alert_history (rule_id, wallet_address, transaction_hash, message, level) VALUES (?, ?, ?, ?, ?)",
            (rule_id, wallet_address, transaction_hash, message, level)
        )
        
        conn.commit()
        conn.close()
        
        return cursor.lastrowid
    
    def get_alerts(self, wallet_address: str = None, level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取告警历史
        
        Args:
            wallet_address: 钱包地址，None表示所有地址
            level: 风险等级，None表示所有等级
            limit: 返回数量限制
            
        Returns:
            告警历史列表
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM alert_history WHERE 1=1"
        params = []
        
        if wallet_address:
            query += " AND wallet_address = ?"
            params.append(wallet_address)
        
        if level:
            query += " AND level = ?"
            params.append(level)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

# 示例用法
if __name__ == "__main__":
    storage = DataStorage()
    
    # 添加钱包
    wallet_id = storage.add_wallet(
        address="0x1234567890123456789012345678901234567890",
        chain="ethereum",
        name="Test Wallet",
        description="Test wallet for demonstration"
    )
    print(f"Added wallet with ID: {wallet_id}")
    
    # 获取钱包列表
    wallets = storage.get_wallets()
    print("Wallets:")
    for wallet in wallets:
        print(wallet)
