"""
Solana 区块链交互类。
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .base import BlockchainBase

logger = logging.getLogger(__name__)


class SolanaBlockchain(BlockchainBase):
    """Solana 区块链交互类。"""

    def __init__(self, rpc_url: Optional[str] = None) -> None:
        """
        初始化 Solana 区块链接口。

        Args:
            rpc_url: RPC 服务地址。*None* → 从 ``config.settings`` 读取。
        """
        # solana 库为可选依赖，延迟导入避免插件加载失败
        from solana.rpc.api import Client

        super().__init__("solana", rpc_url)
        self.client = Client(self.rpc_url)
        self.connected = True

    # ------------------------------------------------------------------
    # Balance
    # ------------------------------------------------------------------

    def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """获取钱包余额。"""
        from solana.publickey import PublicKey

        try:
            public_key = PublicKey(address)
            if token_address:
                return 0.0

            balance_response = self.client.get_balance(public_key)
            if "result" in balance_response:
                return balance_response["result"] / 1e9
            return 0.0
        except Exception as exc:
            logger.error("Solana get_balance failed: %s", exc)
            return 0.0

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    def get_transactions(self, address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取钱包交易历史。"""
        from solana.publickey import PublicKey

        try:
            public_key = PublicKey(address)
            signatures_response = self.client.get_signatures_for_address(
                public_key, limit=limit
            )

            if "result" not in signatures_response:
                return []

            transactions: List[Dict[str, Any]] = []
            for sig_info in signatures_response["result"]:
                tx_response = self.client.get_transaction(sig_info["signature"])
                if "result" in tx_response:
                    transactions.append(
                        {
                            "signature": sig_info["signature"],
                            "slot": sig_info["slot"],
                            "block_time": sig_info.get("blockTime"),
                            "transaction": tx_response["result"],
                        }
                    )
            return transactions
        except Exception as exc:
            logger.error("Solana get_transactions failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Token transfers (placeholder)
    # ------------------------------------------------------------------

    def get_token_transfers(
        self,
        address: str,
        token_address: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """获取代币转账记录（SPL tokens） – placeholder implementation."""
        logger.debug(
            "Solana get_token_transfers not yet implemented for %s", address
        )
        return []

    # ------------------------------------------------------------------
    # Block info
    # ------------------------------------------------------------------

    def get_block(self, block_number: Optional[int] = None) -> Dict[str, Any]:
        """获取区块信息。"""
        try:
            if block_number is None:
                block_response = self.client.get_latest_blockhash()
            else:
                block_response = self.client.get_block(block_number)

            return block_response.get("result", {})
        except Exception as exc:
            logger.error("Solana get_block failed: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # Watch address (not supported on Solana via polling)
    # ------------------------------------------------------------------

    def watch_address(self, address: str, callback: Callable) -> None:
        """监听地址交易（Solana 暂不支持轮询模式）。"""
        logger.warning("watch_address is not yet supported for Solana")
