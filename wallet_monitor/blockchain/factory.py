"""
区块链工厂类，用于创建不同区块链的客户端实例。

RPC URLs are resolved from ``wallet_monitor.config.settings`` by default.
"""

from __future__ import annotations

import logging
from typing import Optional

from .base import BlockchainBase
from .ethereum import EthereumClient
from .solana import SolanaBlockchain

logger = logging.getLogger(__name__)


class BlockchainFactory:
    """
    区块链工厂类，用于创建不同区块链的实例。

    RPC URLs are read from ``config.settings`` (overridable via env vars
    or config file) rather than being hardcoded.
    """

    # Fallback defaults (used only if config module is unavailable)
    _FALLBACK_RPC_URLS = {
        "ethereum": "https://mainnet.infura.io/v3/YOUR_API_KEY",
        "bsc": "https://bsc-dataseed.binance.org/",
        "polygon": "https://polygon-rpc.com/",
        "solana": "https://api.mainnet-beta.solana.com",
    }

    @staticmethod
    def create_blockchain(
        chain_type: str,
        rpc_url: Optional[str] = None,
    ) -> Optional[BlockchainBase]:
        """
        创建区块链实例。

        Args:
            chain_type: 区块链类型（``ethereum``、``bsc``、``polygon``、``solana``）。
            rpc_url: RPC 服务地址。*None* → resolved from ``config.settings``.

        Returns:
            区块链实例，或 ``None`` on failure.
        """
        # Resolve RPC URL from config if not explicitly provided
        if rpc_url is None:
            try:
                from ..config import settings

                rpc_url = settings.rpc_url_for(chain_type)
            except Exception:
                rpc_url = None

        if rpc_url is None:
            rpc_url = BlockchainFactory._FALLBACK_RPC_URLS.get(chain_type)

        if rpc_url is None:
            logger.warning("Unsupported blockchain type: %s", chain_type)
            return None

        try:
            if chain_type in ("ethereum", "bsc", "binance", "polygon", "matic"):
                client = EthereumClient(rpc_url=rpc_url)
                # Override chain_name for non-Ethereum EVM chains
                if chain_type not in ("ethereum",):
                    client.chain_name = chain_type
                return client

            if chain_type in ("solana", "sol"):
                return SolanaBlockchain(rpc_url=rpc_url)

            logger.warning("Unsupported blockchain type: %s", chain_type)
            return None

        except Exception:
            logger.exception("Failed to create blockchain instance for %s", chain_type)
            return None

    @staticmethod
    def get_supported_chains() -> list:
        """返回支持的区块链列表。"""
        return list(BlockchainFactory._FALLBACK_RPC_URLS.keys())
