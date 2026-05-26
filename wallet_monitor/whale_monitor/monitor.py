import threading
import time

from .client import HyperliquidClient
from .models import MonitorState


class WhaleMonitor:
    def __init__(self, coin: str, refresh_interval: int = 30, sort_key: str = "value"):
        self.client = HyperliquidClient()
        self.state = MonitorState(coin=coin.upper(), sort_key=sort_key)
        self.refresh_interval = refresh_interval
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None

    def fetch_once(self) -> bool:
        try:
            ls = self.client.get_long_short(self.state.coin)
            pos = self.client.get_positions(self.state.coin)
            with self._lock:
                self.state.update_stats(ls.get("longCount", 0), ls.get("shortCount", 0))
                self.state.update_positions(pos)
                self.state.update_timestamp()
            return True
        except Exception:
            return False

    def _refresh_loop(self):
        while self.state.running:
            self.fetch_once()
            time.sleep(self.refresh_interval)

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.state.running = False
        if self._thread:
            self._thread.join(timeout=2)

    def get_snapshot(self) -> dict:
        with self._lock:
            return self.state.to_dict()

    def set_sort(self, key: str) -> bool:
        with self._lock:
            return self.state.set_sort(key)

    @staticmethod
    def available_coins() -> list[str]:
        return HyperliquidClient().get_coins()
