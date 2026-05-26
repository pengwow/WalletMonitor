import pytest
from unittest.mock import patch, MagicMock

from wallet_monitor.whale_monitor.monitor import WhaleMonitor
from tests.conftest import (
    SAMPLE_LONG_SHORT_RESPONSE,
    SAMPLE_POSITIONS_RESPONSE,
)


class TestWhaleMonitor:

    def setup_method(self):
        self.monitor = WhaleMonitor(coin="BTC", refresh_interval=30)

    def test_init(self):
        assert self.monitor.state.coin == "BTC"
        assert self.monitor.state.sort_key == "value"
        assert self.monitor.refresh_interval == 30

    def test_init_lowercase(self):
        monitor = WhaleMonitor(coin="eth")
        assert monitor.state.coin == "ETH"

    @patch("wallet_monitor.whale_monitor.monitor.HyperliquidClient")
    def test_fetch_once_success(self, MockClient):
        mock_client = MagicMock()
        mock_client.get_long_short.return_value = {"longCount": 100, "shortCount": 80}
        mock_client.get_positions.return_value = [
            {"user": "0x123", "positionSize": 10, "leverage": 5},
            {"user": "0x456", "positionSize": -5, "leverage": 20},
        ]
        MockClient.return_value = mock_client

        monitor = WhaleMonitor(coin="SOL")
        result = monitor.fetch_once()

        assert result is True
        assert monitor.state.stats.long_count == 100
        assert monitor.state.stats.short_count == 80
        assert len(monitor.state.positions) == 2

    @patch("wallet_monitor.whale_monitor.monitor.HyperliquidClient")
    def test_fetch_once_failure(self, MockClient):
        mock_client = MagicMock()
        mock_client.get_long_short.side_effect = Exception("network error")
        MockClient.return_value = mock_client

        monitor = WhaleMonitor(coin="SOL")
        result = monitor.fetch_once()

        assert result is False

    @patch("wallet_monitor.whale_monitor.monitor.HyperliquidClient")
    def test_get_snapshot(self, MockClient):
        mock_client = MagicMock()
        mock_client.get_long_short.return_value = {"longCount": 50, "shortCount": 30}
        mock_client.get_positions.return_value = [
            {"user": "0xabc", "positionSize": 100, "leverage": 10, "positionValueUsd": 50000},
        ]
        MockClient.return_value = mock_client

        monitor = WhaleMonitor(coin="ETH")
        monitor.fetch_once()
        snapshot = monitor.get_snapshot()

        assert snapshot["coin"] == "ETH"
        assert snapshot["stats"]["longCount"] == 50
        assert snapshot["stats"]["shortCount"] == 30
        assert len(snapshot["positions"]) == 1
        assert "lastUpdate" in snapshot
        assert "sortKey" in snapshot

    def test_set_sort(self):
        assert self.monitor.set_sort("upnl") is True
        assert self.monitor.state.sort_key == "upnl"
        assert self.monitor.state.sort_reverse is True

        assert self.monitor.set_sort("upnl") is True
        assert self.monitor.state.sort_reverse is False

        assert self.monitor.set_sort("invalid") is False

    @patch("wallet_monitor.whale_monitor.monitor.HyperliquidClient")
    def test_start_and_stop(self, MockClient):
        mock_client = MagicMock()
        mock_client.get_long_short.return_value = {"longCount": 1, "shortCount": 1}
        mock_client.get_positions.return_value = []
        MockClient.return_value = mock_client

        monitor = WhaleMonitor(coin="BTC", refresh_interval=1)
        monitor.start()

        assert monitor._thread is not None
        assert monitor._thread.is_alive()

        monitor.stop()

        assert monitor.state.running is False

    @patch("wallet_monitor.whale_monitor.monitor.HyperliquidClient")
    def test_start_idempotent(self, MockClient):
        mock_client = MagicMock()
        mock_client.get_long_short.return_value = {"longCount": 1, "shortCount": 1}
        mock_client.get_positions.return_value = []
        MockClient.return_value = mock_client

        monitor = WhaleMonitor(coin="BTC", refresh_interval=1)
        monitor.start()
        thread1 = monitor._thread
        monitor.start()
        thread2 = monitor._thread

        assert thread1 is thread2
        monitor.stop()

    @patch("wallet_monitor.whale_monitor.monitor.HyperliquidClient")
    def test_available_coins(self, MockClient):
        mock_client = MagicMock()
        mock_client.get_coins.return_value = ["BTC", "ETH", "SOL"]
        MockClient.return_value = mock_client

        coins = WhaleMonitor.available_coins()

        assert coins == ["BTC", "ETH", "SOL"]
