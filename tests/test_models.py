import pytest

from wallet_monitor.whale_monitor.models import (
    WhalePosition,
    MarketStats,
    MonitorState,
    COMMON_COINS,
    SORT_CONFIG,
    LEVERAGE_WARN_THRESHOLD,
    LEVERAGE_DANGER_THRESHOLD,
    LIQ_DISTANCE_WARN,
)
from tests.conftest import SAMPLE_API_POSITION, SAMPLE_SHORT_POSITION, SAMPLE_LOW_LEVERAGE_POSITION


class TestWhalePosition:

    def test_from_api_long(self, sample_api_position):
        pos = WhalePosition.from_api(sample_api_position)

        assert pos.user == "0xe668c4300f51344d8e6cee6294cb9cd1fb5fb5ca"
        assert pos.symbol == "BTC"
        assert pos.position_size == 51.37724
        assert pos.entry_price == 77472.5
        assert pos.liq_price == 74560.627
        assert pos.leverage == 25
        assert pos.margin_balance == 158852.26
        assert pos.position_value_usd == 3971306.52
        assert pos.unrealized_pnl == -9016.94
        assert pos.margin_mode == "cross"
        assert pos.create_time == 1779692644333

    def test_from_api_short(self, sample_short_position):
        pos = WhalePosition.from_api(sample_short_position)

        assert pos.position_size < 0
        assert pos.is_short is True
        assert pos.is_long is False

    def test_from_api_none_values(self):
        data = {"user": "0x123", "positionSize": None, "leverage": None}
        pos = WhalePosition.from_api(data)

        assert pos.position_size == 0
        assert pos.leverage == 0

    def test_is_long(self, sample_api_position):
        pos = WhalePosition.from_api(sample_api_position)
        assert pos.is_long is True
        assert pos.is_short is False

    def test_is_short(self, sample_short_position):
        pos = WhalePosition.from_api(sample_short_position)
        assert pos.is_short is True
        assert pos.is_long is False

    def test_leverage_level_normal(self):
        pos = WhalePosition(leverage=5)
        assert pos.leverage_level == "normal"

    def test_leverage_level_warn(self):
        pos = WhalePosition(leverage=LEVERAGE_WARN_THRESHOLD)
        assert pos.leverage_level == "warn"

    def test_leverage_level_danger(self):
        pos = WhalePosition(leverage=LEVERAGE_DANGER_THRESHOLD)
        assert pos.leverage_level == "danger"

    def test_liq_risk_true(self, sample_api_position):
        pos = WhalePosition.from_api(sample_api_position)
        distance = abs(pos.entry_price - pos.liq_price) / pos.entry_price
        assert distance < LIQ_DISTANCE_WARN
        assert pos.liq_risk is True

    def test_liq_risk_false(self, sample_low_position=SAMPLE_LOW_LEVERAGE_POSITION):
        pos = WhalePosition.from_api(sample_low_position)
        distance = abs(pos.entry_price - pos.liq_price) / pos.entry_price
        assert distance > LIQ_DISTANCE_WARN
        assert pos.liq_risk is False

    def test_liq_risk_zero_prices(self):
        pos = WhalePosition(entry_price=0, liq_price=0)
        assert pos.liq_risk is False

    def test_liq_risk_zero_entry(self):
        pos = WhalePosition(entry_price=0, liq_price=100)
        assert pos.liq_risk is False

    def test_to_dict(self, sample_api_position):
        pos = WhalePosition.from_api(sample_api_position)
        d = pos.to_dict()

        assert d["user"] == pos.user
        assert d["symbol"] == "BTC"
        assert d["positionSize"] == pos.position_size
        assert d["leverage"] == 25
        assert d["marginMode"] == "cross"


class TestMarketStats:

    def test_basic(self):
        stats = MarketStats(long_count=156, short_count=146)

        assert stats.total == 302
        assert abs(stats.long_pct - 51.7) < 0.1
        assert abs(stats.short_pct - 48.3) < 0.1

    def test_zero_total(self):
        stats = MarketStats(long_count=0, short_count=0)

        assert stats.total == 0
        assert stats.long_pct == 0.0
        assert stats.short_pct == 100.0

    def test_all_long(self):
        stats = MarketStats(long_count=100, short_count=0)

        assert stats.long_pct == 100.0
        assert stats.short_pct == 0.0

    def test_to_dict(self):
        stats = MarketStats(long_count=60, short_count=40)
        d = stats.to_dict()

        assert d["longCount"] == 60
        assert d["shortCount"] == 40
        assert d["total"] == 100
        assert d["longPct"] == 60.0
        assert d["shortPct"] == 40.0


class TestMonitorState:

    def test_default(self):
        state = MonitorState()

        assert state.coin == "BTC"
        assert state.sort_key == "value"
        assert state.sort_reverse is True
        assert state.running is True
        assert len(state.positions) == 0

    def test_update_stats(self):
        state = MonitorState()
        state.update_stats(100, 50)

        assert state.stats.long_count == 100
        assert state.stats.short_count == 50

    def test_update_positions(self, sample_positions):
        state = MonitorState()
        state.update_positions(sample_positions)

        assert len(state.positions) == 2
        assert isinstance(state.positions[0], WhalePosition)
        assert state.positions[0].leverage == 25

    def test_update_timestamp(self):
        state = MonitorState()
        state.update_timestamp()

        assert state.last_update != "--:--:--"
        assert ":" in state.last_update

    def test_set_sort_change_key(self):
        state = MonitorState(sort_key="value", sort_reverse=False)

        result = state.set_sort("upnl")

        assert result is True
        assert state.sort_key == "upnl"
        assert state.sort_reverse is True

    def test_set_sort_toggle_reverse(self):
        state = MonitorState(sort_key="value", sort_reverse=True)

        result = state.set_sort("value")

        assert result is True
        assert state.sort_key == "value"
        assert state.sort_reverse is False

    def test_set_sort_invalid(self):
        state = MonitorState()

        result = state.set_sort("invalid")

        assert result is False

    def test_sorted_positions_by_value(self, sample_positions):
        state = MonitorState(sort_key="value", sort_reverse=True)
        state.update_positions(sample_positions)

        sorted_pos = state.sorted_positions

        assert sorted_pos[0].position_value_usd >= sorted_pos[1].position_value_usd

    def test_sorted_positions_by_leverage(self, sample_positions):
        state = MonitorState(sort_key="leverage", sort_reverse=True)
        state.update_positions(sample_positions)

        sorted_pos = state.sorted_positions

        assert sorted_pos[0].leverage >= sorted_pos[1].leverage

    def test_sorted_positions_by_upnl(self, sample_positions):
        state = MonitorState(sort_key="upnl", sort_reverse=True)
        state.update_positions(sample_positions)

        sorted_pos = state.sorted_positions

        assert abs(sorted_pos[0].unrealized_pnl) >= abs(sorted_pos[1].unrealized_pnl)

    def test_to_dict(self, sample_positions):
        state = MonitorState(coin="ETH")
        state.update_stats(73, 85)
        state.update_positions(sample_positions)
        state.update_timestamp()

        d = state.to_dict()

        assert d["coin"] == "ETH"
        assert d["stats"]["longCount"] == 73
        assert d["stats"]["shortCount"] == 85
        assert len(d["positions"]) == 2
        assert d["positions"][0]["address"].startswith("0x")
        assert d["sortKey"] == "value"


class TestConstants:

    def test_common_coins(self):
        assert "BTC" in COMMON_COINS
        assert "ETH" in COMMON_COINS
        assert "SOL" in COMMON_COINS
        assert len(COMMON_COINS) >= 10

    def test_sort_config(self):
        assert "value" in SORT_CONFIG
        assert "upnl" in SORT_CONFIG
        assert "leverage" in SORT_CONFIG
        assert SORT_CONFIG["value"][0] == "positionValueUsd"
