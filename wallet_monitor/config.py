"""
Centralized configuration management for WalletMonitor.

Configuration is loaded from (in order of priority, highest first):
  1. Environment variables with WALLET_MONITOR_ prefix
  2. config.yaml or config.json in the project root
  3. Sensible defaults

Environment variable mapping (WALLET_MONITOR_ prefix stripped):
  WALLET_MONITOR_DB_PATH        → db_path
  WALLET_MONITOR_ETH_RPC_URL    → eth_rpc_url
  WALLET_MONITOR_BSC_RPC_URL    → bsc_rpc_url
  WALLET_MONITOR_POLYGON_RPC_URL → polygon_rpc_url
  WALLET_MONITOR_SOLANA_RPC_URL → solana_rpc_url
  WALLET_MONITOR_LOG_LEVEL      → log_level
  WALLET_MONITOR_API_HOST       → api_host
  WALLET_MONITOR_API_PORT       → api_port
  WALLET_MONITOR_SECRET_KEY     → secret_key

Usage:
    from wallet_monitor.config import settings

    print(settings.db_path)
    print(settings.eth_rpc_url)
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_ENV_PREFIX = "WALLET_MONITOR_"

_PROJECT_ROOT = Path(__file__).resolve().parent.parent  # wallet_monitor/ → WalletMonitor/


def _env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Return the value of an env var with the WALLET_MONITOR_ prefix, or *default*."""
    return os.environ.get(_ENV_PREFIX + name, default)


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (ValueError, TypeError):
        logger.warning("Invalid integer for %s%s: %r – using default %d", _ENV_PREFIX, name, raw, default)
        return default


def _load_yaml_config(path: Path) -> dict:
    """Try to load a YAML config file. Returns {} on any failure."""
    try:
        import yaml  # type: ignore
    except ImportError:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_json_config(path: Path) -> dict:
    """Load a JSON config file. Returns {} on any failure."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _load_file_config() -> dict:
    """Attempt to load config from yaml or json files in the project root."""
    for name in ("config.yaml", "config.yml", "config.json"):
        path = _PROJECT_ROOT / name
        if path.is_file():
            logger.debug("Loading config from %s", path)
            if path.suffix in (".yaml", ".yml"):
                return _load_yaml_config(path)
            else:
                return _load_json_config(path)
    return {}


def _get(key: str, default: str, file_cfg: dict) -> str:
    """Resolve a single config value: env → file → default."""
    env_val = _env(key)
    if env_val is not None:
        return env_val
    file_val = file_cfg.get(key)
    if file_val is not None:
        return str(file_val)
    return default


def _get_int(key: str, default: int, file_cfg: dict) -> int:
    """Resolve a single integer config value: env → file → default."""
    env_val = _env(key)
    if env_val is not None:
        return _env_int(key, default)
    file_val = file_cfg.get(key)
    if file_val is not None:
        try:
            return int(file_val)
        except (ValueError, TypeError):
            pass
    return default


# ---------------------------------------------------------------------------
# Settings dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Settings:
    """
    Immutable, typed configuration for WalletMonitor.

    All attributes have sensible defaults and can be overridden via
    environment variables (``WALLET_MONITOR_*``) or a config file.
    """

    # --- Database ---
    db_path: str = ""

    # --- Blockchain RPC endpoints ---
    eth_rpc_url: str = "https://mainnet.infura.io/v3/YOUR_API_KEY"
    bsc_rpc_url: str = "https://bsc-dataseed.binance.org/"
    polygon_rpc_url: str = "https://polygon-rpc.com/"
    solana_rpc_url: str = "https://api.mainnet-beta.solana.com"

    # --- Logging ---
    log_level: str = "INFO"

    # --- API server ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- Security ---
    secret_key: str = "change-me-in-production"

    # --- Derived / internal (not loaded from env) ---
    project_root: str = field(default_factory=lambda: str(_PROJECT_ROOT))

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def log_level_numeric(self) -> int:
        """Return the numeric log level (e.g. ``logging.INFO``)."""
        return getattr(logging, self.log_level.upper(), logging.INFO)

    @property
    def database_dir(self) -> str:
        """Return the parent directory of ``db_path``."""
        return os.path.dirname(self.db_path) or "."

    def rpc_url_for(self, chain: str) -> Optional[str]:
        """Return the RPC URL for a given chain name (case-insensitive)."""
        chain = chain.lower()
        mapping = {
            "ethereum": self.eth_rpc_url,
            "eth": self.eth_rpc_url,
            "bsc": self.bsc_rpc_url,
            "binance": self.bsc_rpc_url,
            "polygon": self.polygon_rpc_url,
            "matic": self.polygon_rpc_url,
            "solana": self.solana_rpc_url,
            "sol": self.solana_rpc_url,
        }
        return mapping.get(chain)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

def _build_settings() -> Settings:
    """Build a ``Settings`` instance by merging file config, env vars, and defaults."""
    file_cfg = _load_file_config()

    # Determine default db_path: plugin data dir → wallet_monitor.db
    default_db_dir = os.path.join(_PROJECT_ROOT, "data")
    default_db_path = os.path.join(default_db_dir, "wallet_monitor.db")

    return Settings(
        db_path=_get("DB_PATH", default_db_path, file_cfg),
        eth_rpc_url=_get("ETH_RPC_URL", "https://mainnet.infura.io/v3/YOUR_API_KEY", file_cfg),
        bsc_rpc_url=_get("BSC_RPC_URL", "https://bsc-dataseed.binance.org/", file_cfg),
        polygon_rpc_url=_get("POLYGON_RPC_URL", "https://polygon-rpc.com/", file_cfg),
        solana_rpc_url=_get("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com", file_cfg),
        log_level=_get("LOG_LEVEL", "INFO", file_cfg),
        api_host=_get("API_HOST", "0.0.0.0", file_cfg),
        api_port=_get_int("API_PORT", 8000, file_cfg),
        secret_key=_get("SECRET_KEY", "change-me-in-production", file_cfg),
    )


#: The singleton ``Settings`` instance.  Import and use directly:
#:
#:     from wallet_monitor.config import settings
settings: Settings = _build_settings()
