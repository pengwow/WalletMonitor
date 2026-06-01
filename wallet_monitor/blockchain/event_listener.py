import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, Set
from datetime import datetime

logger = logging.getLogger(__name__)


class BlockchainEventListener:
    """
    区块链事件监听器，通过轮询方式检测新交易
    """

    def __init__(self, blockchain_client, poll_interval: int = 12):
        """
        初始化事件监听器
        
        Args:
            blockchain_client: 区块链客户端实例
            poll_interval: 轮询间隔（秒），默认12秒（以太坊出块时间）
        """
        self.client = blockchain_client
        self.poll_interval = poll_interval
        self._watched_addresses: Dict[str, Set[Callable]] = {}
        self._last_block: Optional[int] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def watch_address(self, address: str, callback: Callable[[Dict[str, Any]], None]):
        """
        监听指定地址的交易
        
        Args:
            address: 要监听的钱包地址
            callback: 交易回调函数，接收交易数据字典
        """
        address_lower = address.lower()
        with self._lock:
            if address_lower not in self._watched_addresses:
                self._watched_addresses[address_lower] = set()
            self._watched_addresses[address_lower].add(callback)
        logger.info(f"开始监听地址: {address}")

    def unwatch_address(self, address: str, callback: Optional[Callable] = None):
        """
        停止监听指定地址
        
        Args:
            address: 要停止监听的钱包地址
            callback: 要移除的回调函数，None表示移除该地址的所有回调
        """
        address_lower = address.lower()
        with self._lock:
            if address_lower in self._watched_addresses:
                if callback:
                    self._watched_addresses[address_lower].discard(callback)
                    if not self._watched_addresses[address_lower]:
                        del self._watched_addresses[address_lower]
                else:
                    del self._watched_addresses[address_lower]
        logger.info(f"停止监听地址: {address}")

    def start(self):
        """启动事件监听"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()
        logger.info("事件监听器已启动")

    def stop(self):
        """停止事件监听"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("事件监听器已停止")

    def _poll_loop(self):
        """轮询主循环"""
        while self._running:
            try:
                self._check_new_transactions()
            except Exception as e:
                logger.error(f"轮询检查失败: {e}")
            time.sleep(self.poll_interval)

    def _check_new_transactions(self):
        """检查新交易"""
        try:
            current_block = self.client.get_block_number()

            if self._last_block is None:
                self._last_block = current_block
                return

            if current_block <= self._last_block:
                return

            for block_num in range(self._last_block + 1, current_block + 1):
                block = self.client.get_block(block_num, full_transactions=True)
                if block and "transactions" in block:
                    self._process_block_transactions(block["transactions"])

            self._last_block = current_block
        except Exception as e:
            logger.error(f"检查新交易失败: {e}")

    def _process_block_transactions(self, transactions):
        """处理区块中的交易"""
        with self._lock:
            watched = dict(self._watched_addresses)

        for tx in transactions:
            if not isinstance(tx, dict):
                continue

            from_addr = (tx.get("from") or "").lower()
            to_addr = (tx.get("to") or "").lower()

            callbacks = set()
            if from_addr in watched:
                callbacks.update(watched[from_addr])
            if to_addr in watched:
                callbacks.update(watched[to_addr])

            for callback in callbacks:
                try:
                    callback(tx)
                except Exception as e:
                    logger.error(f"回调执行失败: {e}")

    @property
    def watched_count(self) -> int:
        """获取监听地址数量"""
        with self._lock:
            return len(self._watched_addresses)

    @property
    def is_running(self) -> bool:
        """获取运行状态"""
        return self._running


_global_listener: Optional[BlockchainEventListener] = None
_listener_lock = threading.Lock()


def get_global_listener(blockchain_client=None, poll_interval: int = 12) -> BlockchainEventListener:
    """
    获取全局事件监听器单例
    
    Args:
        blockchain_client: 区块链客户端，首次调用时需要提供
        poll_interval: 轮询间隔
        
    Returns:
        全局事件监听器实例
    """
    global _global_listener
    with _listener_lock:
        if _global_listener is None:
            if blockchain_client is None:
                raise ValueError("首次调用需要提供blockchain_client")
            _global_listener = BlockchainEventListener(blockchain_client, poll_interval)
        return _global_listener
