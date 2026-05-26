import requests


class HyperliquidClient:
    HL_API = "https://api.hyperliquid.xyz/info"
    BOT_API = "https://hyperbot.network/api/whales"
    HEADERS = {"device": "web"}
    TIMEOUT = 10

    def get_coins(self) -> list[str]:
        try:
            resp = requests.post(
                self.HL_API,
                json={"type": "meta"},
                timeout=self.TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                u["name"]
                for u in data.get("universe", [])
                if not u.get("isDelisted")
            ]
        except Exception:
            return []

    def get_long_short(self, coin: str) -> dict:
        try:
            resp = requests.get(
                f"{self.BOT_API}/long-short",
                params={"coin": coin},
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                return data["data"]
            return {"longCount": 0, "shortCount": 0}
        except Exception:
            return {"longCount": 0, "shortCount": 0}

    def get_positions(self, coin: str) -> list[dict]:
        try:
            resp = requests.get(
                f"{self.BOT_API}/open-positions",
                params={"coin": coin},
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("code") == 0:
                return data.get("data", [])
            return []
        except Exception:
            return []
