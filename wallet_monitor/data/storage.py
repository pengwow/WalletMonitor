import sqlite3
import json
import logging
import os
import threading
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class DataStorage:
    """
    数据存储类，用于存储和管理区块链数据

    Uses WAL mode for concurrent reads, thread-safe connection pooling,
    and a transaction context manager with auto-commit/rollback.
    """

    _instance: Optional["DataStorage"] = None
    _lock = threading.Lock()

    def __init__(self, db_path: str = ""):
        if not db_path:
            db_path = self._default_db_path()

        self.db_path = db_path
        self._pool_lock = threading.Lock()

        # Ensure directory exists
        os.makedirs(
            os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".",
            exist_ok=True,
        )

        self._init_db()

    @classmethod
    def instance(cls, db_path: str = "") -> "DataStorage":
        """Thread-safe singleton accessor."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance

    @staticmethod
    def _default_db_path() -> str:
        """从调用栈推断插件目录，返回绝对路径的数据库文件路径"""
        import inspect

        try:
            frame = inspect.currentframe()
            while frame:
                filename = frame.f_code.co_filename
                if "wallet_monitor" in filename and "storage.py" not in filename:
                    plugin_dir = os.path.dirname(filename)
                    while plugin_dir and not os.path.exists(
                        os.path.join(plugin_dir, "plugin.py")
                    ):
                        parent = os.path.dirname(plugin_dir)
                        if parent == plugin_dir:
                            break
                        plugin_dir = parent
                    return os.path.join(plugin_dir, "wallet_monitor.db")
                frame = frame.f_back
        finally:
            del frame  # avoid reference cycles

        fallback_dir = os.path.dirname(os.path.dirname(__file__))
        return os.path.join(fallback_dir, "wallet_monitor.db")

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        """Create a new connection with WAL mode and row_factory."""
        conn = sqlite3.connect(self.db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def get_connection(self):
        """Context manager that yields a connection and ensures it is closed."""
        conn = self._connect()
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @contextmanager
    def transaction(self) -> sqlite3.Cursor:
        """
        Context manager that wraps an auto-commit/rollback transaction.

        Usage::

            with storage.transaction() as cur:
                cur.execute("INSERT INTO ...")
                # commit happens automatically on clean exit
                # rollback on any exception
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    def _init_db(self):
        """初始化数据库表结构并创建索引"""
        with self.transaction() as cur:
            cur.execute(
                """
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
                """
            )

            cur.execute(
                """
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
                """
            )

            cur.execute(
                """
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
                """
            )

            cur.execute(
                """
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
                """
            )

            # --- Indexes ---
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_wallets_address_chain "
                "ON wallets (address, chain)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_wallets_is_active "
                "ON wallets (is_active)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_wallet_chain_ts "
                "ON transactions (wallet_address, chain, timestamp)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_transactions_hash "
                "ON transactions (hash)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_wallet_chain "
                "ON alerts (wallet_address, chain)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_status "
                "ON alerts (status)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_alerts_created_at "
                "ON alerts (created_at)"
            )

        logger.info("Database initialized: %s", self.db_path)

    # ------------------------------------------------------------------
    # Wallets
    # ------------------------------------------------------------------

    def add_wallet(
        self,
        address: str,
        chain: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> bool:
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
            with self.transaction() as cur:
                cur.execute(
                    "INSERT OR IGNORE INTO wallets (address, chain, name, description) "
                    "VALUES (?, ?, ?, ?)",
                    (address, chain, name, description),
                )
            return True
        except Exception as e:
            logger.error("添加钱包失败: %s", e, exc_info=True)
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
            with self.get_connection() as conn:
                cur = conn.cursor()
                if chain:
                    cur.execute(
                        "SELECT * FROM wallets WHERE chain = ? AND is_active = 1",
                        (chain,),
                    )
                else:
                    cur.execute("SELECT * FROM wallets WHERE is_active = 1")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error("获取钱包列表失败: %s", e, exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def add_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        添加交易

        Args:
            transaction: 交易数据

        Returns:
            是否添加成功
        """
        try:
            with self.transaction() as cur:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO transactions (
                        hash, wallet_address, chain, from_address, to_address, amount, status,
                        timestamp, block_number, block_hash, gas_used, gas_price, input_data,
                        is_contract_interaction, contract_address, anomaly_score, risk_level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
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
                        transaction.get("risk_level", "low"),
                    ),
                )
            return True
        except Exception as e:
            logger.error("添加交易失败: %s", e, exc_info=True)
            return False

    def get_transactions(
        self,
        wallet_address: Optional[str] = None,
        chain: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
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
            with self.get_connection() as conn:
                cur = conn.cursor()
                query = "SELECT * FROM transactions WHERE 1=1"
                params: list = []

                if wallet_address:
                    query += " AND wallet_address = ?"
                    params.append(wallet_address)
                if chain:
                    query += " AND chain = ?"
                    params.append(chain)

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error("获取交易列表失败: %s", e, exc_info=True)
            return []

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    def add_alert(self, alert: Dict[str, Any]) -> bool:
        """
        添加告警

        Args:
            alert: 告警数据

        Returns:
            是否添加成功
        """
        try:
            with self.transaction() as cur:
                cur.execute(
                    """
                    INSERT INTO alerts (
                        wallet_address, chain, alert_type, message, risk_level, transaction_hash
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        alert.get("wallet_address"),
                        alert.get("chain"),
                        alert.get("alert_type"),
                        alert.get("message"),
                        alert.get("risk_level", "low"),
                        alert.get("transaction_hash"),
                    ),
                )
            return True
        except Exception as e:
            logger.error("添加告警失败: %s", e, exc_info=True)
            return False

    def get_alerts(
        self,
        wallet_address: Optional[str] = None,
        chain: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
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
            with self.get_connection() as conn:
                cur = conn.cursor()
                query = "SELECT * FROM alerts WHERE 1=1"
                params: list = []

                if wallet_address:
                    query += " AND wallet_address = ?"
                    params.append(wallet_address)
                if chain:
                    query += " AND chain = ?"
                    params.append(chain)

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error("获取告警列表失败: %s", e, exc_info=True)
            return []

    def resolve_alert(self, alert_id: int) -> bool:
        """
        解决告警

        Args:
            alert_id: 告警ID

        Returns:
            是否解决成功
        """
        try:
            with self.transaction() as cur:
                cur.execute(
                    "UPDATE alerts SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP "
                    "WHERE id = ?",
                    (alert_id,),
                )
                return cur.rowcount > 0
        except Exception as e:
            logger.error("解决告警失败: %s", e, exc_info=True)
            return False

    def get_alert_by_id(self, alert_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取告警

        Args:
            alert_id: 告警ID

        Returns:
            告警数据，不存在返回None
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error("获取告警失败: %s", e, exc_info=True)
            return None

    # ------------------------------------------------------------------
    # Alert Rules
    # ------------------------------------------------------------------

    def add_alert_rule(self, rule: Dict[str, Any]) -> bool:
        """
        添加告警规则

        Args:
            rule: 规则数据

        Returns:
            是否添加成功
        """
        try:
            with self.transaction() as cur:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO alert_rules (
                        name, description, rule_type, threshold, enabled
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        rule.get("name"),
                        rule.get("description"),
                        rule.get("rule_type"),
                        rule.get("threshold"),
                        1 if rule.get("enabled", True) else 0,
                    ),
                )
            return True
        except Exception as e:
            logger.error("添加告警规则失败: %s", e, exc_info=True)
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
            with self.get_connection() as conn:
                cur = conn.cursor()
                if enabled_only:
                    cur.execute("SELECT * FROM alert_rules WHERE enabled = 1")
                else:
                    cur.execute("SELECT * FROM alert_rules")
                return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error("获取告警规则列表失败: %s", e, exc_info=True)
            return []

    def update_wallet(
        self,
        wallet_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> bool:
        """
        更新钱包

        Args:
            wallet_id: 钱包ID
            name: 钱包名称
            description: 钱包描述
            is_active: 是否激活

        Returns:
            是否更新成功
        """
        try:
            updates: list = []
            params: list = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(1 if is_active else 0)

            if not updates:
                return False

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(wallet_id)

            with self.transaction() as cur:
                cur.execute(
                    f"UPDATE wallets SET {', '.join(updates)} WHERE id = ?", params
                )
                return cur.rowcount > 0
        except Exception as e:
            logger.error("更新钱包失败: %s", e, exc_info=True)
            return False

    def delete_wallet(self, wallet_id: int) -> bool:
        """
        删除钱包（软删除，设置is_active=0）

        Args:
            wallet_id: 钱包ID

        Returns:
            是否删除成功
        """
        try:
            with self.transaction() as cur:
                cur.execute(
                    "UPDATE wallets SET is_active = 0, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ?",
                    (wallet_id,),
                )
                return cur.rowcount > 0
        except Exception as e:
            logger.error("删除钱包失败: %s", e, exc_info=True)
            return False

    def update_alert_rule(
        self,
        rule_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        threshold: Optional[float] = None,
        enabled: Optional[bool] = None,
    ) -> bool:
        """
        更新告警规则

        Args:
            rule_id: 规则ID
            name: 规则名称
            description: 规则描述
            threshold: 阈值
            enabled: 是否启用

        Returns:
            是否更新成功
        """
        try:
            updates: list = []
            params: list = []

            if name is not None:
                updates.append("name = ?")
                params.append(name)
            if description is not None:
                updates.append("description = ?")
                params.append(description)
            if threshold is not None:
                updates.append("threshold = ?")
                params.append(threshold)
            if enabled is not None:
                updates.append("enabled = ?")
                params.append(1 if enabled else 0)

            if not updates:
                return False

            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(rule_id)

            with self.transaction() as cur:
                cur.execute(
                    f"UPDATE alert_rules SET {', '.join(updates)} WHERE id = ?",
                    params,
                )
                return cur.rowcount > 0
        except Exception as e:
            logger.error("更新告警规则失败: %s", e, exc_info=True)
            return False

    def delete_alert_rule(self, rule_id: int) -> bool:
        """
        删除告警规则

        Args:
            rule_id: 规则ID

        Returns:
            是否删除成功
        """
        try:
            with self.transaction() as cur:
                cur.execute("DELETE FROM alert_rules WHERE id = ?", (rule_id,))
                return cur.rowcount > 0
        except Exception as e:
            logger.error("删除告警规则失败: %s", e, exc_info=True)
            return False

    def get_alert_rule_by_id(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取告警规则

        Args:
            rule_id: 规则ID

        Returns:
            规则数据，不存在返回None
        """
        try:
            with self.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("SELECT * FROM alert_rules WHERE id = ?", (rule_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error("获取告警规则失败: %s", e, exc_info=True)
            return None

    def close(self):
        """关闭数据库连接（no-op – connections are pooled and closed per use）"""
        logger.debug("close() called – connections are managed per-context")
