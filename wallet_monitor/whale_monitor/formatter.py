from datetime import datetime

from .models import CST, WhalePosition


def format_usd(value: float) -> str:
    av = abs(value)
    if av >= 1_000_000:
        return f"${value / 1_000_000:+.2f}M" if value != 0 else "$0"
    if av >= 1_000:
        return f"${value / 1_000:+.2f}K" if value != 0 else "$0"
    return f"${value:+,.2f}" if value != 0 else "$0"


def format_usd_unsigned(value: float) -> str:
    av = abs(value)
    if av >= 1_000_000:
        return f"${av / 1_000_000:.2f}M"
    if av >= 1_000:
        return f"${av / 1_000:.2f}K"
    return f"${av:,.2f}"


def format_address(addr: str) -> str:
    if len(addr) > 10:
        return f"{addr[:6]}...{addr[-4:]}"
    return addr


def format_timestamp(ts: int) -> str:
    try:
        dt = datetime.fromtimestamp(ts / 1000, tz=CST)
        return dt.strftime("%m-%d %H:%M")
    except Exception:
        return "--"


def format_price(price: float) -> str:
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:,.2f}"
    else:
        return f"${price:,.4f}"


def get_direction(position: WhalePosition) -> tuple[str, str]:
    if position.is_long:
        return "▲ L", "green"
    elif position.is_short:
        return "▼ S", "red"
    return "—", ""


def get_leverage_text(position: WhalePosition) -> tuple[str, str]:
    level = position.leverage_level
    if level == "danger":
        return f"{position.leverage}x", "danger"
    elif level == "warn":
        return f"{position.leverage}x", "warn"
    return f"{position.leverage}x", "normal"


def get_liq_text(position: WhalePosition) -> tuple[str, str]:
    liq = position.liq_price
    if liq == 0:
        return "N/A", "normal"
    text = format_price(liq)
    if position.liq_risk:
        return text, "danger"
    return text, "normal"


def get_position_row(position: WhalePosition) -> dict:
    dir_text, dir_level = get_direction(position)
    lev_text, lev_level = get_leverage_text(position)
    liq_text, liq_level = get_liq_text(position)

    return {
        "address": format_address(position.user),
        "direction": dir_text,
        "direction_level": dir_level,
        "value": format_usd_unsigned(position.position_value_usd),
        "value_raw": position.position_value_usd,
        "upnl": format_usd(position.unrealized_pnl),
        "upnl_positive": position.unrealized_pnl >= 0,
        "upnl_raw": position.unrealized_pnl,
        "margin": format_usd_unsigned(position.margin_balance),
        "entry": format_price(position.entry_price),
        "liq_price": liq_text,
        "liq_level": liq_level,
        "leverage": lev_text,
        "leverage_level": lev_level,
        "leverage_raw": position.leverage,
        "mode": position.margin_mode if position.margin_mode else "cross",
        "time": format_timestamp(position.create_time),
    }


def get_long_short_bar(long_count: int, short_count: int, width: int = 40) -> dict:
    total = long_count + short_count
    if total == 0:
        return {"text": "No data available", "long_bars": 0, "short_bars": 0, "width": width}

    long_pct = long_count / total
    long_bars = int(long_pct * width)
    short_bars = width - long_bars

    return {
        "long_count": long_count,
        "short_count": short_count,
        "long_pct": round(long_pct * 100, 1),
        "short_pct": round((1 - long_pct) * 100, 1),
        "long_bars": long_bars,
        "short_bars": short_bars,
        "width": width,
    }
