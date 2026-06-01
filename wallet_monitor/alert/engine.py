"""
Optimized Alert Engine with rule caching, deduplication, and aggregation.

Improvements over original:
1. Rules cached in memory, refreshed every 5 minutes or on explicit call
2. Deduplication: same wallet+chain+alert_type within 1 hour is skipped
3. Aggregation: similar alerts within a 5-min window are batched for notification
4. Proper structured logging throughout
"""

from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
import logging
import threading
import time
import hashlib
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - alert-engine - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AlertDeduplicator:
    """
    Checks storage for recent duplicate alerts and prevents re-alerting.
    
    Deduplication key: wallet_address + chain + alert_type
    Window: 1 hour (configurable)
    """

    def __init__(self, dedup_window_seconds: int = 3600):
        self._dedup_window = dedup_window_seconds
        self._cache: Dict[str, datetime] = {}  # key -> last_alert_time
        self._lock = threading.Lock()

    def _make_key(self, wallet_address: str, chain: str, alert_type: str) -> str:
        """Create a unique deduplication key from alert identifiers."""
        raw = f"{wallet_address}:{chain}:{alert_type}"
        return hashlib.md5(raw.encode()).hexdigest()

    def is_duplicate(self, alert: Dict[str, Any]) -> bool:
        """
        Check if an alert is a duplicate within the deduplication window.
        
        Checks both in-memory cache AND storage for recent duplicates.
        """
        wallet = alert.get("wallet_address", "")
        chain = alert.get("chain", "")
        alert_type = alert.get("alert_type", "")
        key = self._make_key(wallet, chain, alert_type)
        now = datetime.now()

        # Check in-memory cache first (fast path)
        with self._lock:
            cached_time = self._cache.get(key)
            if cached_time and (now - cached_time).total_seconds() < self._dedup_window:
                logger.debug(
                    f"Alert deduplicated (memory cache): {alert_type} for {wallet}:{chain}"
                )
                return True

        # Check storage for recent duplicates (authoritative check)
        try:
            from ..data.storage import DataStorage
            storage = DataStorage()
            cutoff = now - timedelta(seconds=self._dedup_window)
            recent_alerts = storage.get_alerts(
                wallet_address=wallet, chain=chain
            )
            for stored_alert in recent_alerts:
                stored_type = stored_alert.get("alert_type", "")
                stored_time = stored_alert.get("created_at") or stored_alert.get("timestamp")
                if stored_type == alert_type and stored_time:
                    if isinstance(stored_time, str):
                        try:
                            stored_time = datetime.fromisoformat(stored_time)
                        except (ValueError, TypeError):
                            continue
                    if isinstance(stored_time, datetime) and stored_time > cutoff:
                        logger.debug(
                            f"Alert deduplicated (storage check): {alert_type} for {wallet}:{chain}"
                        )
                        # Update memory cache
                        with self._lock:
                            self._cache[key] = now
                        return True
        except Exception as e:
            logger.warning(f"Dedup storage check failed, falling through: {e}")

        # Not a duplicate - record in cache
        with self._lock:
            self._cache[key] = now
        return False

    def cleanup_old_entries(self) -> int:
        """Remove expired entries from the in-memory cache. Returns count removed."""
        cutoff = datetime.now() - timedelta(seconds=self._dedup_window)
        removed = 0
        with self._lock:
            expired_keys = [k for k, v in self._cache.items() if v < cutoff]
            for k in expired_keys:
                del self._cache[k]
                removed += 1
        if removed:
            logger.debug(f"Cleaned up {removed} expired dedup cache entries")
        return removed

    def clear(self):
        """Clear the entire dedup cache (e.g. on config reset)."""
        with self._lock:
            self._cache.clear()
        logger.info("Dedup cache cleared")


class AlertAggregator:
    """
    Aggregates similar alerts within a time window and batch-notifies.
    
    Groups alerts by wallet+chain+alert_type within a configurable window.
    When the window expires, all pending alerts in a group are batched into
    a single aggregated notification.
    """

    def __init__(self, aggregation_window_seconds: int = 300):
        self._window = aggregation_window_seconds
        self._pending: Dict[str, List[Dict[str, Any]]] = {}
        self._window_start: Dict[str, float] = {}
        self._lock = threading.Lock()

    def _make_group_key(self, alert: Dict[str, Any]) -> str:
        """Create a grouping key for aggregation."""
        wallet = alert.get("wallet_address", "")
        chain = alert.get("chain", "")
        alert_type = alert.get("alert_type", "")
        return f"{wallet}:{chain}:{alert_type}"

    def add_alert(self, alert: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Add an alert to the aggregation buffer.
        
        Returns an aggregated alert dict if the window has expired for this group,
        otherwise returns None (alert is buffered).
        """
        key = self._make_group_key(alert)
        now = time.time()

        with self._lock:
            if key not in self._pending:
                self._pending[key] = []
                self._window_start[key] = now

            self._pending[key].append(alert)
            elapsed = now - self._window_start[key]

            if elapsed >= self._window:
                # Window expired - flush this group
                alerts = self._pending.pop(key)
                self._window_start.pop(key, None)
                return self._build_aggregated_alert(alerts)

        return None

    def flush_all(self) -> List[Dict[str, Any]]:
        """
        Force-flush all pending aggregated alerts (e.g. on shutdown or periodic check).
        Returns a list of aggregated alerts.
        """
        results = []
        with self._lock:
            keys = list(self._pending.keys())
            now = time.time()

            for key in keys:
                alerts = self._pending.pop(key, [])
                self._window_start.pop(key, None)
                if alerts:
                    results.append(self._build_aggregated_alert(alerts))

        if results:
            logger.info(f"Flushed {len(results)} aggregated alert groups ({sum(len(a.get('_raw_alerts', [])) for a in results)} raw alerts)")
        return results

    def flush_expired(self) -> List[Dict[str, Any]]:
        """Flush only groups whose window has expired. Returns flushed aggregated alerts."""
        results = []
        now = time.time()

        with self._lock:
            keys = list(self._pending.keys())
            for key in keys:
                start = self._window_start.get(key, 0)
                if now - start >= self._window:
                    alerts = self._pending.pop(key, [])
                    self._window_start.pop(key, None)
                    if alerts:
                        results.append(self._build_aggregated_alert(alerts))

        if results:
            logger.info(
                f"Flushed {len(results)} expired aggregated alert groups "
                f"({sum(len(a.get('_raw_alerts', [])) for a in results)} raw alerts)"
            )
        return results

    def _build_aggregated_alert(self, alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a single aggregated alert from a list of similar alerts."""
        if len(alerts) == 1:
            alert = alerts[0].copy()
            alert["_aggregated"] = False
            alert["_raw_alerts"] = alerts
            return alert

        # Use the most severe alert as the base
        risk_order = {"high": 3, "medium": 2, "low": 1}
        base = max(alerts, key=lambda a: risk_order.get(a.get("risk_level", "low"), 0))

        total_amount = sum(a.get("amount", 0) for a in alerts)
        avg_amount = total_amount / len(alerts) if alerts else 0

        aggregated = base.copy()
        aggregated["alert_count"] = len(alerts)
        aggregated["total_amount"] = total_amount
        aggregated["avg_amount"] = avg_amount
        aggregated["aggregation_window_seconds"] = self._window
        aggregated["message"] = (
            f"[Aggregated x{len(alerts)}] {base.get('message', '')} | "
            f"Total: ${total_amount:.2f}, Avg: ${avg_amount:.2f}"
        )
        aggregated["_aggregated"] = True
        aggregated["_raw_alerts"] = alerts

        logger.info(
            f"Aggregated {len(alerts)} alerts for {base.get('wallet_address', 'unknown')}:"
            f"{base.get('chain', '?')}/{base.get('alert_type', '?')}"
        )
        return aggregated

    @property
    def pending_count(self) -> int:
        """Total number of pending alerts across all groups."""
        with self._lock:
            return sum(len(v) for v in self._pending.values())

    def clear(self):
        """Clear all pending aggregated alerts."""
        with self._lock:
            self._pending.clear()
            self._window_start.clear()
        logger.info("Aggregation buffer cleared")


class AlertRuleEngine:
    """
    Optimized alert engine with rule caching, deduplication, and aggregation.
    
    - Rules are cached in memory and refreshed every 5 minutes (configurable).
    - Deduplication prevents the same wallet+chain+alert_type within 1 hour.
    - Aggregation batches similar alerts within a 5-min window.
    - Thread-safe for concurrent evaluation.
    """

    RULE_CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(
        self,
        dedup_window_seconds: int = 3600,
        aggregation_window_seconds: int = 300,
        rule_cache_ttl: int = 300,
    ):
        # Rule cache
        self._rules: List[Dict[str, Any]] = []
        self._rules_by_type: Dict[str, List[Dict[str, Any]]] = {}
        self._rules_loaded_at: float = 0
        self._rule_cache_ttl = rule_cache_ttl
        self._rules_lock = threading.Lock()

        # Deduplication
        self._deduplicator = AlertDeduplicator(dedup_window_seconds)

        # Aggregation
        self._aggregator = AlertAggregator(aggregation_window_seconds)

        # Notifier (lazy)
        self._notifier = None

        # Load initial rules
        self._load_rules()

        logger.info(
            f"AlertRuleEngine initialized: "
            f"dedup_window={dedup_window_seconds}s, "
            f"aggregation_window={aggregation_window_seconds}s, "
            f"rule_cache_ttl={rule_cache_ttl}s"
        )

    def _load_rules(self):
        """
        Load rules from storage into cache.
        Called on init and periodically (every RULE_CACHE_TTL_SECONDS).
        """
        try:
            from ..data.storage import DataStorage
            storage = DataStorage()
            rules = storage.get_alert_rules(enabled_only=True)

            # Index rules by type for O(1) lookup
            by_type: Dict[str, List[Dict[str, Any]]] = {}
            for rule in rules:
                rule_type = rule.get("rule_type", "")
                if rule_type not in by_type:
                    by_type[rule_type] = []
                by_type[rule_type].append(rule)

            with self._rules_lock:
                self._rules = rules
                self._rules_by_type = by_type
                self._rules_loaded_at = time.time()

            logger.info(f"Loaded {len(rules)} alert rules (types: {list(by_type.keys())})")
        except Exception as e:
            logger.error(f"Failed to load alert rules: {e}")
            with self._rules_lock:
                self._rules = []
                self._rules_by_type = {}

    def _maybe_refresh_rules(self):
        """Refresh rules if cache has expired."""
        if time.time() - self._rules_loaded_at > self._rule_cache_ttl:
            logger.info("Rule cache expired, refreshing...")
            self._load_rules()

    def refresh_rules(self):
        """
        Explicitly force a rule reload.
        Call this when rules are added/modified/deleted externally.
        """
        logger.info("Explicit rule refresh requested")
        self._load_rules()

    @property
    def rules(self) -> List[Dict[str, Any]]:
        """Thread-safe property that returns cached rules (auto-refreshes if stale)."""
        self._maybe_refresh_rules()
        with self._rules_lock:
            return list(self._rules)

    def _get_rules_by_type(self, rule_type: str) -> List[Dict[str, Any]]:
        """Get rules of a specific type from cache (fast O(1) lookup)."""
        self._maybe_refresh_rules()
        with self._rules_lock:
            return list(self._rules_by_type.get(rule_type, []))

    def evaluate_transaction(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate a transaction against all transaction-type rules.
        
        Args:
            transaction: Transaction data dict
            
        Returns:
            List of triggered alerts (after deduplication and aggregation)
        """
        alerts = []
        rules = self._get_rules_by_type("transaction")

        for rule in rules:
            alert = self._evaluate_transaction_rule(rule, transaction)
            if alert:
                alerts.append(alert)

        # Filter out duplicates
        deduped = []
        for alert in alerts:
            if not self._deduplicator.is_duplicate(alert):
                deduped.append(alert)
            else:
                logger.debug(
                    f"Skipped duplicate alert: {alert.get('alert_type')} "
                    f"for {alert.get('wallet_address')}:{alert.get('chain')}"
                )

        # Aggregate remaining alerts
        aggregated = []
        for alert in deduped:
            agg = self._aggregator.add_alert(alert)
            if agg:
                aggregated.append(agg)

        return aggregated

    def evaluate_balance(
        self, wallet_address: str, chain: str, balance: float
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a wallet balance against all balance-type rules.
        
        Args:
            wallet_address: Wallet address
            chain: Blockchain type
            balance: Current wallet balance
            
        Returns:
            List of triggered alerts (after deduplication and aggregation)
        """
        alerts = []
        rules = self._get_rules_by_type("balance")

        for rule in rules:
            alert = self._evaluate_balance_rule(rule, wallet_address, chain, balance)
            if alert:
                alerts.append(alert)

        # Filter out duplicates
        deduped = []
        for alert in alerts:
            if not self._deduplicator.is_duplicate(alert):
                deduped.append(alert)
            else:
                logger.debug(
                    f"Skipped duplicate alert: {alert.get('alert_type')} "
                    f"for {alert.get('wallet_address')}:{alert.get('chain')}"
                )

        # Aggregate remaining alerts
        aggregated = []
        for alert in deduped:
            agg = self._aggregator.add_alert(alert)
            if agg:
                aggregated.append(agg)

        return aggregated

    def evaluate_contract(self, transaction: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Evaluate a transaction against all contract-type rules.
        
        Args:
            transaction: Transaction data dict
            
        Returns:
            List of triggered alerts (after deduplication and aggregation)
        """
        alerts = []
        rules = self._get_rules_by_type("contract")

        for rule in rules:
            alert = self._evaluate_contract_rule(rule, transaction)
            if alert:
                alerts.append(alert)

        # Filter out duplicates
        deduped = []
        for alert in alerts:
            if not self._deduplicator.is_duplicate(alert):
                deduped.append(alert)
            else:
                logger.debug(
                    f"Skipped duplicate alert: {alert.get('alert_type')} "
                    f"for {alert.get('wallet_address')}:{alert.get('chain')}"
                )

        # Aggregate remaining alerts
        aggregated = []
        for alert in deduped:
            agg = self._aggregator.add_alert(alert)
            if agg:
                aggregated.append(agg)

        return aggregated

    def evaluate_anomaly(
        self,
        transaction: Dict[str, Any],
        wallet_history: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Evaluate a transaction against all anomaly-type rules.
        
        Args:
            transaction: Transaction data dict
            wallet_history: Historical transactions for the wallet
            
        Returns:
            List of triggered alerts (after deduplication and aggregation)
        """
        alerts = []
        rules = self._get_rules_by_type("anomaly")

        for rule in rules:
            alert = self._evaluate_anomaly_rule(rule, transaction, wallet_history)
            if alert:
                alerts.append(alert)

        # Filter out duplicates
        deduped = []
        for alert in alerts:
            if not self._deduplicator.is_duplicate(alert):
                deduped.append(alert)
            else:
                logger.debug(
                    f"Skipped duplicate alert: {alert.get('alert_type')} "
                    f"for {alert.get('wallet_address')}:{alert.get('chain')}"
                )

        # Aggregate remaining alerts
        aggregated = []
        for alert in deduped:
            agg = self._aggregator.add_alert(alert)
            if agg:
                aggregated.append(agg)

        return aggregated

    # ── Individual rule evaluators ──────────────────────────────────────

    def _evaluate_transaction_rule(
        self, rule: Dict[str, Any], transaction: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a single transaction rule against a transaction."""
        try:
            amount = transaction.get("amount", 0)
            threshold = rule.get("threshold", 0)

            if amount > threshold:
                risk_level = "high" if amount > threshold * 2 else "medium"
                logger.info(
                    f"Transaction rule triggered: ${amount} > ${threshold} "
                    f"(wallet={transaction.get('wallet_address')}, chain={transaction.get('chain')})"
                )
                return {
                    "wallet_address": transaction.get("wallet_address"),
                    "chain": transaction.get("chain"),
                    "alert_type": "transaction",
                    "message": f"Transaction amount exceeds threshold: ${amount} > ${threshold}",
                    "risk_level": risk_level,
                    "transaction_hash": transaction.get("hash"),
                    "amount": amount,
                    "threshold": threshold,
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "created_at": datetime.now().isoformat(),
                }
            return None
        except Exception as e:
            logger.error(f"Transaction rule evaluation failed: {e}", exc_info=True)
            return None

    def _evaluate_balance_rule(
        self,
        rule: Dict[str, Any],
        wallet_address: str,
        chain: str,
        balance: float,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a single balance rule against a wallet balance."""
        try:
            threshold = rule.get("threshold", 0)

            if balance < threshold:
                risk_level = "high" if balance < threshold * 0.5 else "medium"
                logger.info(
                    f"Balance rule triggered: ${balance} < ${threshold} "
                    f"(wallet={wallet_address}, chain={chain})"
                )
                return {
                    "wallet_address": wallet_address,
                    "chain": chain,
                    "alert_type": "balance",
                    "message": f"Wallet balance below threshold: ${balance} < ${threshold}",
                    "risk_level": risk_level,
                    "balance": balance,
                    "threshold": threshold,
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "created_at": datetime.now().isoformat(),
                }
            return None
        except Exception as e:
            logger.error(f"Balance rule evaluation failed: {e}", exc_info=True)
            return None

    def _evaluate_contract_rule(
        self, rule: Dict[str, Any], transaction: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a single contract interaction rule."""
        try:
            if transaction.get("is_contract_interaction"):
                logger.info(
                    f"Contract rule triggered: {transaction.get('contract_address')} "
                    f"(wallet={transaction.get('wallet_address')}, chain={transaction.get('chain')})"
                )
                return {
                    "wallet_address": transaction.get("wallet_address"),
                    "chain": transaction.get("chain"),
                    "alert_type": "contract",
                    "message": f"Contract interaction detected: {transaction.get('contract_address')}",
                    "risk_level": "medium",
                    "transaction_hash": transaction.get("hash"),
                    "contract_address": transaction.get("contract_address"),
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "created_at": datetime.now().isoformat(),
                }
            return None
        except Exception as e:
            logger.error(f"Contract rule evaluation failed: {e}", exc_info=True)
            return None

    def _evaluate_anomaly_rule(
        self,
        rule: Dict[str, Any],
        transaction: Dict[str, Any],
        wallet_history: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a single anomaly detection rule."""
        try:
            if not wallet_history:
                return None

            avg_amount = sum(tx.get("amount", 0) for tx in wallet_history) / len(wallet_history)
            current_amount = transaction.get("amount", 0)
            threshold = rule.get("threshold", 3)

            if current_amount > avg_amount * threshold:
                logger.info(
                    f"Anomaly rule triggered: ${current_amount} vs avg ${avg_amount} "
                    f"(threshold={threshold}x, wallet={transaction.get('wallet_address')}, "
                    f"chain={transaction.get('chain')})"
                )
                return {
                    "wallet_address": transaction.get("wallet_address"),
                    "chain": transaction.get("chain"),
                    "alert_type": "anomaly",
                    "message": f"Anomalous transaction detected: ${current_amount} (avg: ${avg_amount})",
                    "risk_level": "high",
                    "transaction_hash": transaction.get("hash"),
                    "amount": current_amount,
                    "avg_amount": avg_amount,
                    "threshold_multiplier": threshold,
                    "rule_id": rule.get("id"),
                    "rule_name": rule.get("name"),
                    "created_at": datetime.now().isoformat(),
                }
            return None
        except Exception as e:
            logger.error(f"Anomaly rule evaluation failed: {e}", exc_info=True)
            return None

    # ── Notification & persistence ──────────────────────────────────────

    def _get_notifier(self):
        """Lazy-load the notifier."""
        if self._notifier is None:
            from .notifier import get_notifier
            self._notifier = get_notifier()
        return self._notifier

    def flush_pending_alerts(self) -> List[Dict[str, Any]]:
        """
        Flush all aggregated alerts pending in the buffer.
        Call this periodically or on shutdown.
        """
        return self._aggregator.flush_all()

    def add_alert(self, alert: Dict[str, Any]) -> bool:
        """
        Persist an alert and send notification.
        
        Args:
            alert: Alert dict to store
            
        Returns:
            True if successfully stored and notified
        """
        try:
            from ..data.storage import DataStorage
            storage = DataStorage()
            success = storage.add_alert(alert)
            if success:
                logger.info(
                    f"Alert stored: {alert.get('alert_type')} "
                    f"for {alert.get('wallet_address')}:{alert.get('chain')} - "
                    f"{alert.get('message')}"
                )
                notifier = self._get_notifier()
                if notifier._channels:
                    notifier.notify(alert)
            else:
                logger.error(f"Failed to store alert: {alert.get('message')}")
            return success
        except Exception as e:
            logger.error(f"add_alert failed: {e}", exc_info=True)
            return False

    def add_alerts_batch(self, alerts: List[Dict[str, Any]]) -> int:
        """
        Persist and notify a batch of alerts.
        
        Returns:
            Count of successfully stored alerts
        """
        success_count = 0
        for alert in alerts:
            if self.add_alert(alert):
                success_count += 1
        if success_count:
            logger.info(f"Batch: {success_count}/{len(alerts)} alerts stored and notified")
        return success_count

    def get_alerts(
        self,
        wallet_address: Optional[str] = None,
        chain: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Get alerts from storage, optionally filtered."""
        try:
            from ..data.storage import DataStorage
            storage = DataStorage()
            return storage.get_alerts(wallet_address=wallet_address, chain=chain)
        except Exception as e:
            logger.error(f"Failed to retrieve alerts: {e}")
            return []

    # ── Maintenance ─────────────────────────────────────────────────────

    def cleanup(self):
        """
        Run periodic maintenance: flush expired aggregates and clean dedup cache.
        Call this periodically (e.g. every minute from a scheduler).
        """
        flushed = self._aggregator.flush_expired()
        if flushed:
            self.add_alerts_batch(flushed)

        cleaned = self._deduplicator.cleanup_old_entries()
        logger.debug(f"Maintenance: flushed {len(flushed)} groups, cleaned {cleaned} dedup entries")

    def reset(self):
        """Reset all caches (useful for testing or after config changes)."""
        with self._rules_lock:
            self._rules = []
            self._rules_by_type = {}
            self._rules_loaded_at = 0
        self._deduplicator.clear()
        self._aggregator.clear()
        logger.info("All engine caches reset")

    def stats(self) -> Dict[str, Any]:
        """Return engine statistics for monitoring."""
        with self._rules_lock:
            rule_count = len(self._rules)
            rule_types = list(self._rules_by_type.keys())
            cache_age = time.time() - self._rules_loaded_at

        return {
            "rule_count": rule_count,
            "rule_types": rule_types,
            "rule_cache_age_seconds": round(cache_age, 1),
            "rule_cache_ttl_seconds": self._rule_cache_ttl,
            "pending_aggregated_alerts": self._aggregator.pending_count,
            "dedup_window_seconds": self._deduplicator._dedup_window,
            "aggregation_window_seconds": self._aggregator._window,
        }
