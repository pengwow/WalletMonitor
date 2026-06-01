import pytest
from unittest.mock import patch, MagicMock

from wallet_monitor.alert.engine import AlertRuleEngine
from wallet_monitor.data.storage import DataStorage


@pytest.fixture
def storage():
    DataStorage._instance = None
    s = DataStorage(db_path=":memory:")
    yield s
    DataStorage._instance = None


@pytest.fixture
def engine(storage):
    engine = AlertRuleEngine()
    yield engine


class TestAlertRuleEngine:

    def test_load_rules(self, engine, storage):
        storage.add_alert_rule({
            "name": "Large Transfer",
            "rule_type": "transaction",
            "threshold": 1000,
            "enabled": True
        })
        engine.load_rules()
        assert len(engine.rules) == 1
        assert engine.rules[0]["name"] == "Large Transfer"

    def test_evaluate_transaction_rule_triggered(self, engine, storage):
        storage.add_alert_rule({
            "name": "Large Transfer",
            "rule_type": "transaction",
            "threshold": 1000,
            "enabled": True
        })
        engine.load_rules()

        transaction = {
            "wallet_address": "0x123",
            "chain": "ethereum",
            "amount": 2000,
            "hash": "0xabc"
        }

        alerts = engine.evaluate_transaction(transaction)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "transaction"
        assert "2000" in alerts[0]["message"]

    def test_evaluate_transaction_rule_not_triggered(self, engine, storage):
        storage.add_alert_rule({
            "name": "Large Transfer",
            "rule_type": "transaction",
            "threshold": 1000,
            "enabled": True
        })
        engine.load_rules()

        transaction = {
            "wallet_address": "0x123",
            "chain": "ethereum",
            "amount": 500,
            "hash": "0xabc"
        }

        alerts = engine.evaluate_transaction(transaction)
        assert len(alerts) == 0

    def test_evaluate_balance_rule_triggered(self, engine, storage):
        storage.add_alert_rule({
            "name": "Low Balance",
            "rule_type": "balance",
            "threshold": 100,
            "enabled": True
        })
        engine.load_rules()

        alerts = engine.evaluate_balance("0x123", "ethereum", 50)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "balance"
        assert "50" in alerts[0]["message"]

    def test_evaluate_balance_rule_not_triggered(self, engine, storage):
        storage.add_alert_rule({
            "name": "Low Balance",
            "rule_type": "balance",
            "threshold": 100,
            "enabled": True
        })
        engine.load_rules()

        alerts = engine.evaluate_balance("0x123", "ethereum", 200)
        assert len(alerts) == 0

    def test_evaluate_contract_rule_triggered(self, engine, storage):
        storage.add_alert_rule({
            "name": "Contract Interaction",
            "rule_type": "contract",
            "enabled": True
        })
        engine.load_rules()

        transaction = {
            "wallet_address": "0x123",
            "chain": "ethereum",
            "is_contract_interaction": True,
            "contract_address": "0x456",
            "hash": "0xabc"
        }

        alerts = engine.evaluate_contract(transaction)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "contract"

    def test_evaluate_anomaly_rule_triggered(self, engine, storage):
        storage.add_alert_rule({
            "name": "Anomaly Detection",
            "rule_type": "anomaly",
            "threshold": 3,
            "enabled": True
        })
        engine.load_rules()

        wallet_history = [
            {"amount": 10},
            {"amount": 15},
            {"amount": 12}
        ]

        transaction = {
            "wallet_address": "0x123",
            "chain": "ethereum",
            "amount": 100,
            "hash": "0xabc"
        }

        alerts = engine.evaluate_anomaly(transaction, wallet_history)
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "anomaly"

    def test_add_alert(self, engine, storage):
        alert = {
            "wallet_address": "0x123",
            "chain": "ethereum",
            "alert_type": "transaction",
            "message": "Test alert",
            "risk_level": "high"
        }

        result = engine.add_alert(alert)
        assert result is True

        alerts = storage.get_alerts()
        assert len(alerts) == 1
        assert alerts[0]["message"] == "Test alert"

    def test_get_alerts(self, engine, storage):
        storage.add_alert({
            "wallet_address": "0x123",
            "chain": "ethereum",
            "alert_type": "transaction",
            "message": "Alert 1",
            "risk_level": "high"
        })
        storage.add_alert({
            "wallet_address": "0x456",
            "chain": "bsc",
            "alert_type": "balance",
            "message": "Alert 2",
            "risk_level": "low"
        })

        alerts = engine.get_alerts()
        assert len(alerts) == 2

    def test_get_alerts_by_wallet(self, engine, storage):
        storage.add_alert({
            "wallet_address": "0x123",
            "chain": "ethereum",
            "alert_type": "transaction",
            "message": "Alert 1",
            "risk_level": "high"
        })
        storage.add_alert({
            "wallet_address": "0x456",
            "chain": "bsc",
            "alert_type": "balance",
            "message": "Alert 2",
            "risk_level": "low"
        })

        alerts = engine.get_alerts(wallet_address="0x123")
        assert len(alerts) == 1
        assert alerts[0]["wallet_address"] == "0x123"
