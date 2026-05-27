from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta

CST = timezone(timedelta(hours=8))

COMMON_COINS = [
    "BTC", "ETH", "SOL", "DOGE", "XRP", "SUI",
    "AVAX", "BNB", "LINK", "ARB", "OP", "kPEPE",
]

SORT_CONFIG = {
    "value": ("positionValueUsd", "持仓价值"),
    "upnl": ("unrealizedPnL", "未实现盈亏"),
    "leverage": ("leverage", "杠杆倍数"),
}

LEVERAGE_WARN_THRESHOLD = 10
LEVERAGE_DANGER_THRESHOLD = 20
LIQ_DISTANCE_WARN = 0.05


@dataclass
class WhalePosition:
    user: str = ""
    symbol: str = ""
    position_size: float = 0.0
    entry_price: float = 0.0
    liq_price: float = 0.0
    leverage: int = 0
    margin_balance: float = 0.0
    position_value_usd: float = 0.0
    unrealized_pnl: float = 0.0
    funding_fee: float = 0.0
    margin_mode: str = ""
    create_time: int = 0

    @classmethod
    def from_api(cls, data: dict) -> "WhalePosition":
        return cls(
            user=data.get("user", ""),
            symbol=data.get("symbol", ""),
            position_size=data.get("positionSize", 0) or 0,
            entry_price=data.get("entryPrice", 0) or 0,
            liq_price=data.get("liqPrice", 0) or 0,
            leverage=data.get("leverage", 0) or 0,
            margin_balance=data.get("marginBalance", 0) or 0,
            position_value_usd=data.get("positionValueUsd", 0) or 0,
            unrealized_pnl=data.get("unrealizedPnL", 0) or 0,
            funding_fee=data.get("fundingFee", 0) or 0,
            margin_mode=data.get("marginMode", ""),
            create_time=data.get("createTime", 0) or 0,
        )

    @property
    def is_long(self) -> bool:
        return self.position_size > 0

    @property
    def is_short(self) -> bool:
        return self.position_size < 0

    @property
    def leverage_level(self) -> str:
        if self.leverage >= LEVERAGE_DANGER_THRESHOLD:
            return "danger"
        if self.leverage >= LEVERAGE_WARN_THRESHOLD:
            return "warn"
        return "normal"

    @property
    def liq_risk(self) -> bool:
        if self.entry_price == 0 or self.liq_price == 0:
            return False
        return abs(self.entry_price - self.liq_price) / self.entry_price < LIQ_DISTANCE_WARN

    def to_dict(self) -> dict:
        return {
            "user": self.user,
            "symbol": self.symbol,
            "positionSize": self.position_size,
            "entryPrice": self.entry_price,
            "liqPrice": self.liq_price,
            "leverage": self.leverage,
            "marginBalance": self.margin_balance,
            "positionValueUsd": self.position_value_usd,
            "unrealizedPnL": self.unrealized_pnl,
            "fundingFee": self.funding_fee,
            "marginMode": self.margin_mode,
            "createTime": self.create_time,
        }


@dataclass
class MarketStats:
    long_count: int = 0
    short_count: int = 0

    @property
    def total(self) -> int:
        return self.long_count + self.short_count

    @property
    def long_pct(self) -> float:
        if self.total == 0:
            return 0.0
        return self.long_count / self.total * 100

    @property
    def short_pct(self) -> float:
        return 100.0 - self.long_pct

    def to_dict(self) -> dict:
        return {
            "longCount": self.long_count,
            "shortCount": self.short_count,
            "total": self.total,
            "longPct": round(self.long_pct, 1),
            "shortPct": round(self.short_pct, 1),
        }


@dataclass
class MonitorState:
    coin: str = "BTC"
    stats: MarketStats = field(default_factory=MarketStats)
    positions: list[WhalePosition] = field(default_factory=list)
    last_update: str = "--:--:--"
    sort_key: str = "value"
    sort_reverse: bool = True
    running: bool = True

    def update_stats(self, long_count: int, short_count: int):
        self.stats = MarketStats(long_count=long_count, short_count=short_count)

    def update_positions(self, raw_positions: list[dict]):
        self.positions = [WhalePosition.from_api(p) for p in raw_positions]

    def update_timestamp(self):
        self.last_update = datetime.now(CST).strftime("%H:%M:%S")

    def set_sort(self, key: str) -> bool:
        if key not in SORT_CONFIG:
            return False
        if self.sort_key == key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_key = key
            self.sort_reverse = True
        return True

    @property
    def sorted_positions(self) -> list[WhalePosition]:
        field_name = SORT_CONFIG.get(self.sort_key, ("positionValueUsd", ""))[0]
        attr_map = {
            "positionValueUsd": "position_value_usd",
            "unrealizedPnL": "unrealized_pnl",
            "leverage": "leverage",
        }
        attr = attr_map.get(field_name, "position_value_usd")
        return sorted(
            self.positions,
            key=lambda p: abs(getattr(p, attr, 0)),
            reverse=self.sort_reverse,
        )

    def to_dict(self) -> dict:
        from .formatter import get_position_row, get_risk_summary
        sorted_pos = self.sorted_positions
        return {
            "coin": self.coin,
            "stats": self.stats.to_dict(),
            "positions": [get_position_row(p) for p in sorted_pos],
            "risk": get_risk_summary(sorted_pos),
            "lastUpdate": self.last_update,
            "sortKey": self.sort_key,
            "sortReverse": self.sort_reverse,
        }
