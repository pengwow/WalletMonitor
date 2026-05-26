import pytest
from unittest.mock import patch, MagicMock

from wallet_monitor.whale_monitor.client import HyperliquidClient
from tests.conftest import SAMPLE_META_RESPONSE, SAMPLE_LONG_SHORT_RESPONSE, SAMPLE_POSITIONS_RESPONSE


class TestHyperliquidClient:

    def setup_method(self):
        self.client = HyperliquidClient()

    @patch("wallet_monitor.whale_monitor.client.requests.post")
    def test_get_coins_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_META_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_post.return_value = mock_resp

        coins = self.client.get_coins()

        assert coins == ["BTC", "ETH", "SOL"]
        assert "MATIC" not in coins
        mock_post.assert_called_once_with(
            self.client.HL_API,
            json={"type": "meta"},
            timeout=self.client.TIMEOUT,
        )

    @patch("wallet_monitor.whale_monitor.client.requests.post")
    def test_get_coins_network_error(self, mock_post):
        mock_post.side_effect = Exception("timeout")

        coins = self.client.get_coins()

        assert coins == []

    @patch("wallet_monitor.whale_monitor.client.requests.get")
    def test_get_long_short_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_LONG_SHORT_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = self.client.get_long_short("BTC")

        assert result == {"longCount": 156, "shortCount": 146}
        mock_get.assert_called_once_with(
            f"{self.client.BOT_API}/long-short",
            params={"coin": "BTC"},
            headers=self.client.HEADERS,
            timeout=self.client.TIMEOUT,
        )

    @patch("wallet_monitor.whale_monitor.client.requests.get")
    def test_get_long_short_error_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": -1, "msg": "SYSTEM ERROR", "data": None}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = self.client.get_long_short("BTC")

        assert result == {"longCount": 0, "shortCount": 0}

    @patch("wallet_monitor.whale_monitor.client.requests.get")
    def test_get_long_short_network_error(self, mock_get):
        mock_get.side_effect = Exception("connection refused")

        result = self.client.get_long_short("ETH")

        assert result == {"longCount": 0, "shortCount": 0}

    @patch("wallet_monitor.whale_monitor.client.requests.get")
    def test_get_positions_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_POSITIONS_RESPONSE
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = self.client.get_positions("BTC")

        assert len(result) == 2
        assert result[0]["user"] == "0xe668c4300f51344d8e6cee6294cb9cd1fb5fb5ca"
        assert result[0]["leverage"] == 25

    @patch("wallet_monitor.whale_monitor.client.requests.get")
    def test_get_positions_error_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"code": -1, "msg": "error", "data": None}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        result = self.client.get_positions("BTC")

        assert result == []

    @patch("wallet_monitor.whale_monitor.client.requests.get")
    def test_get_positions_network_error(self, mock_get):
        mock_get.side_effect = Exception("timeout")

        result = self.client.get_positions("SOL")

        assert result == []
