"""
区块链基础客户端，提供重试、缓存、速率限制和配置集成功能。

Features:
  - Exponential backoff retry (3 retries, base delay 1s)
  - TTL cache for get_balance (30s), get_block_number (5s), get_block (30s)
  - Per-chain rate limiter (max 10 requests/second)
  - RPC URLs read from config module
  - Structured logging via ``logging`` module
"""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests


# ---------------------------------------------------------------------------
# Rate limiter (per-chain, sliding window)
# ---------------------------------------------------------------------------

class _RateLimiter:
    """Sliding-window rate limiter: max *max_rps* requests per 1-second window."""

    def __init__(self, max_rps: int = 10):
        self._max_rps = max_rps
        self._timestamps: List[float] = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a request slot is available."""
        with self._lock:
            now = time.monotonic()
            # Evict timestamps older than 1 s
            self._timestamps = [t for t in self._timestamps if now - t < 1.0]
            if len(self._timestamps) >= self._max_rps:
                sleep_for = 1.0 - (now - self._timestamps[0])
                if sleep_for > 0:
                    time.sleep(sleep_for)
            self._timestamps.append(time.monotonic())


# ---------------------------------------------------------------------------
# Simple TTL cache (thread-safe, ordered)
# ---------------------------------------------------------------------------

class _TTLCache:
    """Key → (value, expiry) with a hard cap of 1 000 entries."""

    _MAX_ENTRIES = 1000

    def __init__(self) -> None:
        self._store: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if entry is not None:
                value, expiry = entry
                if time.monotonic() < expiry:
                    return value
                del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: float) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl)
            # Evict oldest when full
            while len(self._store) > self._MAX_ENTRIES:
                self._store.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()


# ---------------------------------------------------------------------------
# Shared rate-limiter registry (one limiter per chain name)
# ---------------------------------------------------------------------------

_rate_limiters: Dict[str, _RateLimiter] = {}
_rate_limiters_lock = threading.Lock()


def _get_rate_limiter(chain_name: str, max_rps: int = 10) -> _RateLimiter:
    """Return (and lazily create) the shared rate limiter for *chain_name*."""
    with _rate_limiters_lock:
        if chain_name not in _rate_limiters:
            _rate_limiters[chain_name] = _RateLimiter(max_rps=max_rps)
        return _rate_limiters[chain_name]


# ---------------------------------------------------------------------------
# BlockchainBase
# ---------------------------------------------------------------------------

class BlockchainBase(ABC):
    """
    区块链基础接口，提供重试、缓存、速率限制和配置集成功能。

    Subclasses must implement:
        - ``get_transactions``
        - ``get_token_transfers``
        - ``watch_address``
    """

    def __init__(self, chain_name: str, rpc_url: Optional[str] = None) -> None:
        """
        初始化区块链接口。

        Args:
            chain_name: 区块链名称（如 ``"ethereum"``、``"bsc"`` …）。
            rpc_url: RPC 服务地址。*None* → resolved from
                     ``wallet_monitor.config.settings``.
        """
        from ..config import settings

        self.chain_name = chain_name
        self.rpc_url = rpc_url or settings.rpc_url_for(chain_name) or ""
        self.logger = logging.getLogger(f"wallet_monitor.blockchain.{chain_name}")
        self._cache = _TTLCache()
        self._request_id = 0
        self._rate_limiter = _get_rate_limiter(chain_name)
        self._session = requests.Session()

        self.logger.debug("Initialised %s client (rpc=%s)", chain_name, self.rpc_url)

    # ------------------------------------------------------------------
    # Core RPC helper (retry + rate limit)
    # ------------------------------------------------------------------

    def _make_rpc_request(
        self,
        method: str,
        params: Optional[List[Any]] = None,
        *,
        timeout: int = 30,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ) -> Any:
        """
        Send a JSON-RPC request with exponential-backoff retry and
        per-chain rate limiting.

        Returns the ``"result"`` field from the JSON-RPC response.
        Raises ``RuntimeError`` on RPC-level errors and re-raises the
        underlying exception after all retries are exhausted.
        """
        if params is None:
            params = []

        last_exc: Optional[Exception] = None

        for attempt in range(1, max_retries + 1):
            self._rate_limiter.acquire()

            try:
                self._request_id += 1
                payload = {
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": self._request_id,
                }

                resp = self._session.post(
                    self.rpc_url,
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=timeout,
                )
                resp.raise_for_status()
                body = resp.json()

                if "error" in body:
                    raise RuntimeError(
                        f"RPC error for {method}: {body['error']}"
                    )

                return body.get("result")

            except Exception as exc:
                last_exc = exc
                delay = base_delay * (2 ** (attempt - 1))
                self.logger.warning(
                    "%s.%s failed (attempt %d/%d): %s – retrying in %.1fs",
                    self.chain_name,
                    method,
                    attempt,
                    max_retries,
                    exc,
                    delay,
                )
                if attempt < max_retries:
                    time.sleep(delay)

        self.logger.error(
            "%s.%s failed after %d retries",
            self.chain_name,
            method,
            max_retries,
        )
        raise last_exc  # type: ignore[misc]

    # ------------------------------------------------------------------
    # Concrete methods (with TTL caching)
    # ------------------------------------------------------------------

    def get_balance(
        self,
        address: str,
        token_address: Optional[str] = None,
    ) -> float:
        """
        获取钱包原生代币余额。

        Result is cached for **30 s** per ``(address, token_address)`` pair.
        """
        cache_key = f"balance:{address}:{token_address or ''}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._make_rpc_request("eth_getBalance", [address, "latest"])
        balance = int(result, 16) / 1e18
        self._cache.set(cache_key, balance, ttl=30.0)
        return balance

    def get_block_number(self) -> int:
        """
        获取当前区块号。

        Result is cached for **5 s**.
        """
        cache_key = "block_number"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        result = self._make_rpc_request("eth_blockNumber", [])
        block_number = int(result, 16)
        self._cache.set(cache_key, block_number, ttl=5.0)
        return block_number

    def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """
        获取区块信息。

        Result is cached for **30 s** per block number.
        """
        cache_key = f"block:{block_number}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        param = hex(block_number) if block_number is not None else "latest"
        result = self._make_rpc_request("eth_getBlockByNumber", [param, True])
        self._cache.set(cache_key, result, ttl=30.0)
        return result

    # ------------------------------------------------------------------
    # Abstract interface – subclasses must implement
    # ------------------------------------------------------------------

    @abstractmethod
    def get_transactions(
        self, address: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取钱包交易历史。"""
        ...

    @abstractmethod
    def get_token_transfers(
        self,
        address: str,
        token_address: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取代币转账记录。"""
        ...

    @abstractmethod
    def watch_address(self, address: str, callback: Callable) -> None:
        """监听地址交易。"""
        ...
