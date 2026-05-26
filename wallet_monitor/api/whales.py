from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..whale_monitor import WhaleMonitor, COMMON_COINS, SORT_CONFIG
from ..whale_monitor.formatter import get_long_short_bar

router = APIRouter(prefix="/whales", tags=["whales"])

_monitor_cache: dict[str, WhaleMonitor] = {}


def _get_monitor(coin: str, refresh: int = 30) -> WhaleMonitor:
    key = coin.upper()
    if key not in _monitor_cache:
        monitor = WhaleMonitor(coin=key, refresh_interval=refresh)
        monitor.fetch_once()
        monitor.start()
        _monitor_cache[key] = monitor
    return _monitor_cache[key]


@router.get("/coins")
async def get_coins():
    coins = WhaleMonitor.available_coins()
    if not coins:
        raise HTTPException(status_code=502, detail="获取币种列表失败")
    return {
        "coins": coins,
        "common": COMMON_COINS,
        "total": len(coins),
    }


@router.get("/snapshot")
async def get_snapshot(
    coin: str = Query("BTC", description="币种名称"),
    sort: str = Query("value", description="排序字段: value / upnl / leverage"),
):
    if sort not in SORT_CONFIG:
        raise HTTPException(status_code=400, detail=f"无效排序字段: {sort}")

    monitor = _get_monitor(coin)
    monitor.set_sort(sort)
    snapshot = monitor.get_snapshot()

    bar = get_long_short_bar(
        snapshot["stats"]["longCount"],
        snapshot["stats"]["shortCount"],
    )

    return {
        "coin": snapshot["coin"],
        "stats": snapshot["stats"],
        "bar": bar,
        "positions": snapshot["positions"],
        "positionCount": len(snapshot["positions"]),
        "lastUpdate": snapshot["lastUpdate"],
        "sortKey": snapshot["sortKey"],
        "sortReverse": snapshot["sortReverse"],
    }


@router.get("/long-short")
async def get_long_short(coin: str = Query("BTC")):
    from ..whale_monitor.client import HyperliquidClient
    client = HyperliquidClient()
    data = client.get_long_short(coin)
    return {"coin": coin.upper(), **data}


@router.get("/positions")
async def get_positions(coin: str = Query("BTC")):
    from ..whale_monitor.client import HyperliquidClient
    client = HyperliquidClient()
    raw = client.get_positions(coin)
    from ..whale_monitor.models import WhalePosition
    positions = [WhalePosition.from_api(p).to_dict() for p in raw]
    return {"coin": coin.upper(), "positions": positions, "count": len(positions)}
