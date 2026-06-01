import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from wallet_monitor.app import create_app
from wallet_monitor.data.storage import DataStorage


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def storage():
    DataStorage._instance = None
    s = DataStorage(db_path=":memory:")
    yield s
    DataStorage._instance = None


class TestWalletAPI:

    def test_create_wallet(self, client, storage):
        response = client.post("/api/wallets/", json={
            "address": "0x1234567890123456789012345678901234567890",
            "chain": "ethereum",
            "name": "Test Wallet"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["address"] == "0x1234567890123456789012345678901234567890"
        assert data["chain"] == "ethereum"
        assert data["name"] == "Test Wallet"

    def test_get_wallets(self, client, storage):
        storage.add_wallet("0x1111111111111111111111111111111111111111", "ethereum", "Wallet 1")
        storage.add_wallet("0x2222222222222222222222222222222222222222", "bsc", "Wallet 2")

        response = client.get("/api/wallets/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_wallets_by_chain(self, client, storage):
        storage.add_wallet("0x1111111111111111111111111111111111111111", "ethereum", "ETH Wallet")
        storage.add_wallet("0x2222222222222222222222222222222222222222", "bsc", "BSC Wallet")

        response = client.get("/api/wallets/?chain=ethereum")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["chain"] == "ethereum"

    def test_get_wallet_by_id(self, client, storage):
        storage.add_wallet("0x1111111111111111111111111111111111111111", "ethereum", "Wallet 1")
        wallets = storage.get_wallets()
        wallet_id = wallets[0]["id"]

        response = client.get(f"/api/wallets/{wallet_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == wallet_id

    def test_update_wallet(self, client, storage):
        storage.add_wallet("0x1111111111111111111111111111111111111111", "ethereum", "Old Name")
        wallets = storage.get_wallets()
        wallet_id = wallets[0]["id"]

        response = client.put(f"/api/wallets/{wallet_id}", json={
            "name": "New Name",
            "description": "Updated description"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Updated description"

    def test_delete_wallet(self, client, storage):
        storage.add_wallet("0x1111111111111111111111111111111111111111", "ethereum", "Wallet to delete")
        wallets = storage.get_wallets()
        wallet_id = wallets[0]["id"]

        response = client.delete(f"/api/wallets/{wallet_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

        wallets_after = storage.get_wallets()
        assert len(wallets_after) == 0


class TestTransactionAPI:

    def test_get_transactions(self, client, storage):
        storage.add_transaction({
            "hash": "0xabc123",
            "wallet_address": "0x1111111111111111111111111111111111111111",
            "chain": "ethereum",
            "amount": 1.5,
            "status": "success"
        })

        response = client.get("/api/transactions/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["hash"] == "0xabc123"

    def test_get_transactions_by_wallet(self, client, storage):
        storage.add_transaction({
            "hash": "0xabc123",
            "wallet_address": "0x1111111111111111111111111111111111111111",
            "chain": "ethereum",
            "amount": 1.5,
            "status": "success"
        })
        storage.add_transaction({
            "hash": "0xdef456",
            "wallet_address": "0x2222222222222222222222222222222222222222",
            "chain": "ethereum",
            "amount": 2.0,
            "status": "success"
        })

        response = client.get("/api/transactions/?wallet_address=0x1111111111111111111111111111111111111111")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestAlertAPI:

    def test_get_alerts(self, client, storage):
        storage.add_alert({
            "wallet_address": "0x1111111111111111111111111111111111111111",
            "chain": "ethereum",
            "alert_type": "transaction",
            "message": "Test alert",
            "risk_level": "high"
        })

        response = client.get("/api/alerts/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["message"] == "Test alert"

    def test_get_alert_by_id(self, client, storage):
        storage.add_alert({
            "wallet_address": "0x1111111111111111111111111111111111111111",
            "chain": "ethereum",
            "alert_type": "transaction",
            "message": "Test alert",
            "risk_level": "high"
        })
        alerts = storage.get_alerts()
        alert_id = alerts[0]["id"]

        response = client.get(f"/api/alerts/{alert_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert_id

    def test_resolve_alert(self, client, storage):
        storage.add_alert({
            "wallet_address": "0x1111111111111111111111111111111111111111",
            "chain": "ethereum",
            "alert_type": "transaction",
            "message": "Test alert",
            "risk_level": "high"
        })
        alerts = storage.get_alerts()
        alert_id = alerts[0]["id"]

        response = client.post(f"/api/alerts/resolve/{alert_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_create_alert_rule(self, client, storage):
        response = client.post("/api/alerts/rules/", json={
            "name": "Large Transfer",
            "description": "Detect large transfers",
            "rule_type": "transaction",
            "threshold": 1000,
            "enabled": True
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Large Transfer"
        assert data["threshold"] == 1000

    def test_get_alert_rules(self, client, storage):
        storage.add_alert_rule({
            "name": "Rule 1",
            "rule_type": "transaction",
            "threshold": 100,
            "enabled": True
        })

        response = client.get("/api/alerts/rules/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_update_alert_rule(self, client, storage):
        storage.add_alert_rule({
            "name": "Old Rule",
            "rule_type": "transaction",
            "threshold": 100,
            "enabled": True
        })
        rules = storage.get_alert_rules(enabled_only=False)
        rule_id = rules[0]["id"]

        response = client.put(f"/api/alerts/rules/{rule_id}", json={
            "name": "Updated Rule",
            "threshold": 200
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Rule"
        assert data["threshold"] == 200

    def test_delete_alert_rule(self, client, storage):
        storage.add_alert_rule({
            "name": "Rule to delete",
            "rule_type": "transaction",
            "threshold": 100,
            "enabled": True
        })
        rules = storage.get_alert_rules(enabled_only=False)
        rule_id = rules[0]["id"]

        response = client.delete(f"/api/alerts/rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["success"] is True
