"""
以太坊区块链交互模块
负责与以太坊网络通信，获取交易、区块、合约事件等数据。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .base import BlockchainBase

logger = logging.getLogger(__name__)


class EthereumClient(BlockchainBase):
    """以太坊（及 EVM 兼容链）客户端，继承 BlockchainBase 提供的重试、缓存与速率限制。"""

    def __init__(self, rpc_url: Optional[str] = None) -> None:
        """
        初始化以太坊客户端。

        Args:
            rpc_url: 以太坊 RPC 节点 URL。*None* → 从 ``config.settings`` 读取。
        """
        super().__init__(chain_name="ethereum", rpc_url=rpc_url)

    # ------------------------------------------------------------------
    # Extra EVM helpers (on top of the base class methods)
    # ------------------------------------------------------------------

    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """获取交易信息。"""
        return self._make_rpc_request("eth_getTransactionByHash", [tx_hash]) or {}

    def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """获取交易收据。"""
        return self._make_rpc_request("eth_getTransactionReceipt", [tx_hash]) or {}

    def get_transactions(
        self, address: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取钱包交易历史。

        Note: A production implementation would query an indexer such as
        Etherscan, Alchemy, or ``eth_getLogs``. This is a placeholder.
        """
        logger.debug(
            "get_transactions called for %s (not yet fully implemented via RPC)",
            address,
        )
        return []

    def get_token_transfers(
        self,
        address: str,
        token_address: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        获取代币转账记录（ERC-20）。

        Note: This is a placeholder. A production implementation would
        query an indexer such as Etherscan or a log-filtering API.
        """
        logger.debug("get_token_transfers called for %s (not yet implemented via RPC)", address)
        return []

    # ------------------------------------------------------------------
    # Event listener integration
    # ------------------------------------------------------------------

    def watch_address(self, address: str, callback: Callable) -> None:
        """
        监听地址交易。

        Uses the global ``BlockchainEventListener`` to poll for new blocks.
        """
        from .event_listener import get_global_listener

        listener = get_global_listener(self)
        listener.watch_address(address, callback)
        if not listener.is_running:
            listener.start()

    # ------------------------------------------------------------------
    # Legacy compatibility: accept old constructor signature
    # ------------------------------------------------------------------

    @classmethod
    def from_legacy(cls, rpc_url: str = "https://mainnet.infura.io/v3/YOUR_API_KEY") -> "EthereumClient":
        """Create an EthereumClient from a raw RPC URL (backward-compat)."""
        return cls(rpc_url=rpc_url)
