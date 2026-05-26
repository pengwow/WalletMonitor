import pytest

from wallet_monitor.whale_monitor.models import WhalePosition
from wallet_monitor.whale_monitor.formatter import (
    format_usd,
    format_usd_unsigned,
    format_address,
    format_timestamp,
    format_price,
    get_direction,
    get_leverage_text,
    get_liq_text,
    get_position_row,
    get_long_short_bar,
)
from tests.conftest import SAMPLE_API_POSITION, SAMPLE_SHORT_POSITION


class TestFormatUsd:

    def test_millions(self):
        assert format_usd(1500000) == "$+1.50M"

    def test_millions_negative(self):
        assert format_usd(-2500000) == "$-2.50M"

    def test_thousands(self):
        assert format_usd(1500) == "$+1.50K"

    def test_thousands_negative(self):
        assert format_usd(-9016) == "$-9.02K"

    def test_small_value(self):
        assert format_usd(500) == "$+500.00"

    def test_small_negative(self):
        assert format_usd(-50) == "$-50.00"

    def test_zero(self):
        assert format_usd(0) == "$0"


class TestFormatUsdUnsigned:

    def test_millions(self):
        assert format_usd_unsigned(3971306) == "$3.97M"

    def test_thousands(self):
        assert format_usd_unsigned(158852) == "$158.85K"

    def test_small(self):
        assert format_usd_unsigned(500) == "$500.00"

    def test_zero(self):
        assert format_usd_unsigned(0) == "$0.00"


class TestFormatAddress:

    def test_long_address(self):
        addr = "0xe668c4300f51344d8e6cee6294cb9cd1fb5fb5ca"
        assert format_address(addr) == "0xe668...b5ca"

    def test_short_address(self):
        assert format_address("0x1234") == "0x1234"

    def test_exact_10(self):
        assert format_address("0x12345678") == "0x12345678"


class TestFormatTimestamp:

    def test_valid(self):
        ts = 1779692644333
        result = format_timestamp(ts)
        assert "-" in result
        assert ":" in result

    def test_zero(self):
        result = format_timestamp(0)
        assert ":" in result

    def test_very_large(self):
        result = format_timestamp(999999999999999)
        assert result == "--"


class TestFormatPrice:

    def test_large_price(self):
        assert format_price(77472.5) == "$77,472"

    def test_medium_price(self):
        assert format_price(18.435) == "$18.43"

    def test_small_price(self):
        assert format_price(0.1234) == "$0.1234"


class TestGetDirection:

    def test_long(self, sample_api_position):
        pos = WhalePosition.from_api(sample_api_position)
        text, level = get_direction(pos)
        assert text == "▲ L"
        assert level == "green"

    def test_short(self, sample_short_position):
        pos = WhalePosition.from_api(sample_short_position)
        text, level = get_direction(pos)
        assert text == "▼ S"
        assert level == "red"

    def test_zero(self):
        pos = WhalePosition(position_size=0)
        text, level = get_direction(pos)
        assert text == "—"
        assert level == ""


class TestGetLeverageText:

    def test_normal(self):
        pos = WhalePosition(leverage=5)
        text, level = get_leverage_text(pos)
        assert text == "5x"
        assert level == "normal"

    def test_warn(self):
        pos = WhalePosition(leverage=15)
        text, level = get_leverage_text(pos)
        assert text == "15x"
        assert level == "warn"

    def test_danger(self):
        pos = WhalePosition(leverage=25)
        text, level = get_leverage_text(pos)
        assert text == "25x"
        assert level == "danger"


class TestGetLiqText:

    def test_normal(self):
        pos = WhalePosition(liq_price=60000, entry_price=77472)
        text, level = get_liq_text(pos)
        assert text == "$60,000"
        assert level == "normal"

    def test_danger(self):
        pos = WhalePosition(liq_price=74560, entry_price=77472)
        text, level = get_liq_text(pos)
        assert text == "$74,560"
        assert level == "danger"

    def test_zero(self):
        pos = WhalePosition(liq_price=0)
        text, level = get_liq_text(pos)
        assert text == "N/A"
        assert level == "normal"


class TestGetPositionRow:

    def test_long_position(self, sample_api_position):
        pos = WhalePosition.from_api(sample_api_position)
        row = get_position_row(pos)

        assert row["address"] == "0xe668...b5ca"
        assert row["direction"] == "▲ L"
        assert row["direction_level"] == "green"
        assert "M" in row["value"]
        assert row["upnl_positive"] is False
        assert "danger" in row["leverage_level"]
        assert row["mode"] == "cross"
        assert "value_raw" in row
        assert "upnl_raw" in row
        assert "leverage_raw" in row

    def test_short_position(self, sample_short_position):
        pos = WhalePosition.from_api(sample_short_position)
        row = get_position_row(pos)

        assert row["direction"] == "▼ S"
        assert row["direction_level"] == "red"
        assert row["upnl_positive"] is True
        assert row["mode"] == "isolated"


class TestGetLongShortBar:

    def test_normal(self):
        bar = get_long_short_bar(156, 146)

        assert bar["long_count"] == 156
        assert bar["short_count"] == 146
        assert bar["long_pct"] == 51.7
        assert bar["short_pct"] == 48.3
        assert bar["long_bars"] + bar["short_bars"] == 40

    def test_all_long(self):
        bar = get_long_short_bar(100, 0)

        assert bar["long_pct"] == 100.0
        assert bar["short_pct"] == 0.0
        assert bar["long_bars"] == 40
        assert bar["short_bars"] == 0

    def test_zero(self):
        bar = get_long_short_bar(0, 0)

        assert bar["text"] == "No data available"
        assert bar["long_bars"] == 0

    def test_custom_width(self):
        bar = get_long_short_bar(60, 40, width=20)

        assert bar["width"] == 20
        assert bar["long_bars"] + bar["short_bars"] == 20
