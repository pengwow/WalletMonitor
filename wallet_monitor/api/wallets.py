from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging
import traceback

from ..blockchain.factory import BlockchainFactory
from ..data.storage import DataStorage
from ..data.processor import DataProcessor
from .middleware import PaginatedResponse, paginate, require_auth

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/wallets", tags=["wallets"])

# 数据存储实例（延迟初始化）
_storage = None


def _get_storage() -> DataStorage:
    global _storage
    if _storage is None:
        _storage = DataStorage()
    return _storage


# 区块链实例缓存
blockchain_instances = {}


def _get_balance_safe(chain: str, address: str) -> float:
    """安全获取余额，失败返回 0.0"""
    try:
        if chain not in blockchain_instances:
            blockchain_instances[chain] = BlockchainFactory.create_blockchain(chain)
        blockchain = blockchain_instances[chain]
        if blockchain is None:
            return 0.0
        return blockchain.get_balance(address) or 0.0
    except Exception as e:
        logger.warning(f"获取余额失败 ({chain}:{address}): {e}")
        return 0.0


class WalletCreate(BaseModel):
    """
    创建钱包请求模型
    """
    address: str
    chain: str
    name: Optional[str] = None
    description: Optional[str] = None


class WalletUpdate(BaseModel):
    """
    更新钱包请求模型
    """
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class WalletResponse(BaseModel):
    """
    钱包响应模型
    """
    id: int
    address: str
    chain: str
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str
    balance: Optional[float] = None


@router.post("/", response_model=WalletResponse)
async def create_wallet(wallet: WalletCreate):
    """
    创建钱包
    """
    storage = _get_storage()
    try:
        # 标准化地址
        normalized_address = DataProcessor.normalize_address(wallet.address)

        # 验证区块链类型
        supported_chains = BlockchainFactory.get_supported_chains()
        if wallet.chain not in supported_chains:
            raise HTTPException(status_code=400, detail=f"不支持的区块链类型: {wallet.chain}")

        # 创建钱包
        success = storage.add_wallet(
            address=normalized_address,
            chain=wallet.chain,
            name=wallet.name,
            description=wallet.description
        )

        if not success:
            raise HTTPException(status_code=400, detail="创建钱包失败")

        # 获取钱包信息
        wallets = storage.get_wallets(chain=wallet.chain)
        created_wallet = next((w for w in wallets if w["address"] == normalized_address), None)

        if not created_wallet:
            raise HTTPException(status_code=404, detail="钱包创建成功但未找到")

        # 安全获取余额
        balance = _get_balance_safe(wallet.chain, normalized_address)

        # 构建响应
        response = WalletResponse(
            id=created_wallet["id"],
            address=created_wallet["address"],
            chain=created_wallet["chain"],
            name=created_wallet["name"],
            description=created_wallet["description"],
            is_active=bool(created_wallet["is_active"]),
            created_at=created_wallet["created_at"],
            updated_at=created_wallet["updated_at"],
            balance=balance
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建钱包异常: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"创建钱包失败: {str(e)}")


@router.get("/", response_model=PaginatedResponse[WalletResponse])
async def get_wallets(
    chain: Optional[str] = None,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    _auth: dict = require_auth,
):
    """
    获取钱包列表（分页）
    """
    storage = _get_storage()
    try:
        # 获取全部钱包（用于分页计数）
        all_wallets = storage.get_wallets(chain=chain)
        total = len(all_wallets)

        # 切片获取当前页
        offset = (page - 1) * page_size
        page_wallets = all_wallets[offset : offset + page_size]

        # 构建响应
        responses = []
        for wallet in page_wallets:
            balance = _get_balance_safe(wallet["chain"], wallet["address"])
            responses.append(WalletResponse(
                id=wallet["id"],
                address=wallet["address"],
                chain=wallet["chain"],
                name=wallet["name"],
                description=wallet["description"],
                is_active=bool(wallet["is_active"]),
                created_at=wallet["created_at"],
                updated_at=wallet["updated_at"],
                balance=balance,
            ))

        return paginate(responses, total, page, page_size)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取钱包列表异常: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"获取钱包列表失败: {str(e)}")


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(wallet_id: int):
    """
    获取钱包详情
    """
    storage = _get_storage()
    try:
        # 获取所有钱包
        wallets = storage.get_wallets()
        wallet = next((w for w in wallets if w["id"] == wallet_id), None)

        if not wallet:
            raise HTTPException(status_code=404, detail="钱包不存在")

        # 安全获取余额
        balance = _get_balance_safe(wallet["chain"], wallet["address"])

        # 构建响应
        response = WalletResponse(
            id=wallet["id"],
            address=wallet["address"],
            chain=wallet["chain"],
            name=wallet["name"],
            description=wallet["description"],
            is_active=bool(wallet["is_active"]),
            created_at=wallet["created_at"],
            updated_at=wallet["updated_at"],
            balance=balance
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取钱包详情异常: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取钱包详情失败: {str(e)}")


@router.put("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(wallet_id: int, wallet_update: WalletUpdate):
    """
    更新钱包
    """
    storage = _get_storage()
    try:
        wallets = storage.get_wallets()
        wallet = next((w for w in wallets if w["id"] == wallet_id), None)

        if not wallet:
            raise HTTPException(status_code=404, detail="钱包不存在")

        success = storage.update_wallet(
            wallet_id=wallet_id,
            name=wallet_update.name,
            description=wallet_update.description,
            is_active=wallet_update.is_active
        )

        if not success:
            raise HTTPException(status_code=400, detail="更新钱包失败")

        updated_wallets = storage.get_wallets()
        updated_wallet = next((w for w in updated_wallets if w["id"] == wallet_id), None)

        if not updated_wallet:
            raise HTTPException(status_code=404, detail="更新后未找到钱包")

        balance = _get_balance_safe(updated_wallet["chain"], updated_wallet["address"])

        response = WalletResponse(
            id=updated_wallet["id"],
            address=updated_wallet["address"],
            chain=updated_wallet["chain"],
            name=updated_wallet["name"],
            description=updated_wallet["description"],
            is_active=bool(updated_wallet["is_active"]),
            created_at=updated_wallet["created_at"],
            updated_at=updated_wallet["updated_at"],
            balance=balance
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新钱包异常: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"更新钱包失败: {str(e)}")


@router.delete("/{wallet_id}", response_model=Dict[str, Any])
async def delete_wallet(wallet_id: int):
    """
    删除钱包
    """
    storage = _get_storage()
    try:
        wallets = storage.get_wallets()
        wallet = next((w for w in wallets if w["id"] == wallet_id), None)

        if not wallet:
            raise HTTPException(status_code=404, detail="钱包不存在")

        success = storage.delete_wallet(wallet_id)

        if not success:
            raise HTTPException(status_code=400, detail="删除钱包失败")

        return {"success": True, "message": "钱包删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除钱包失败: {str(e)}")


@router.get("/{wallet_id}/balance", response_model=Dict[str, Any])
async def get_wallet_balance(wallet_id: int):
    """
    获取钱包余额
    """
    storage = _get_storage()
    try:
        # 获取钱包
        wallets = storage.get_wallets()
        wallet = next((w for w in wallets if w["id"] == wallet_id), None)

        if not wallet:
            raise HTTPException(status_code=404, detail="钱包不存在")

        # 安全获取余额
        balance = _get_balance_safe(wallet["chain"], wallet["address"])

        return {
            "wallet_id": wallet_id,
            "address": wallet["address"],
            "chain": wallet["chain"],
            "balance": balance
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取钱包余额异常: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"获取钱包余额失败: {str(e)}")
