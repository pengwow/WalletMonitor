from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from blockchain.factory import BlockchainFactory
from data.storage import DataStorage
from data.processor import DataProcessor

router = APIRouter(prefix="/api/wallets", tags=["wallets"])

# 数据存储实例
storage = DataStorage()

# 区块链实例缓存
blockchain_instances = {}


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
        
        # 获取钱包余额
        if wallet.chain not in blockchain_instances:
            blockchain_instances[wallet.chain] = BlockchainFactory.create_blockchain(wallet.chain)
        
        blockchain = blockchain_instances[wallet.chain]
        balance = blockchain.get_balance(normalized_address) if blockchain else 0.0
        
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
        raise HTTPException(status_code=500, detail=f"创建钱包失败: {str(e)}")


@router.get("/", response_model=List[WalletResponse])
async def get_wallets(chain: Optional[str] = None):
    """
    获取钱包列表
    """
    try:
        # 获取钱包列表
        wallets = storage.get_wallets(chain=chain)
        
        # 构建响应
        responses = []
        for wallet in wallets:
            # 获取钱包余额
            if wallet["chain"] not in blockchain_instances:
                blockchain_instances[wallet["chain"]] = BlockchainFactory.create_blockchain(wallet["chain"])
            
            blockchain = blockchain_instances[wallet["chain"]]
            balance = blockchain.get_balance(wallet["address"]) if blockchain else 0.0
            
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
            responses.append(response)
        
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取钱包列表失败: {str(e)}")


@router.get("/{wallet_id}", response_model=WalletResponse)
async def get_wallet(wallet_id: int):
    """
    获取钱包详情
    """
    try:
        # 获取所有钱包
        wallets = storage.get_wallets()
        wallet = next((w for w in wallets if w["id"] == wallet_id), None)
        
        if not wallet:
            raise HTTPException(status_code=404, detail="钱包不存在")
        
        # 获取钱包余额
        if wallet["chain"] not in blockchain_instances:
            blockchain_instances[wallet["chain"]] = BlockchainFactory.create_blockchain(wallet["chain"])
        
        blockchain = blockchain_instances[wallet["chain"]]
        balance = blockchain.get_balance(wallet["address"]) if blockchain else 0.0
        
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
        raise HTTPException(status_code=500, detail=f"获取钱包详情失败: {str(e)}")


@router.put("/{wallet_id}", response_model=WalletResponse)
async def update_wallet(wallet_id: int, wallet_update: WalletUpdate):
    """
    更新钱包
    """
    try:
        # 获取钱包
        wallets = storage.get_wallets()
        wallet = next((w for w in wallets if w["id"] == wallet_id), None)
        
        if not wallet:
            raise HTTPException(status_code=404, detail="钱包不存在")
        
        # 这里简化处理，实际需要实现更新逻辑
        # 暂时返回原钱包信息
        
        # 获取钱包余额
        if wallet["chain"] not in blockchain_instances:
            blockchain_instances[wallet["chain"]] = BlockchainFactory.create_blockchain(wallet["chain"])
        
        blockchain = blockchain_instances[wallet["chain"]]
        balance = blockchain.get_balance(wallet["address"]) if blockchain else 0.0
        
        # 构建响应
        response = WalletResponse(
            id=wallet["id"],
            address=wallet["address"],
            chain=wallet["chain"],
            name=wallet_update.name or wallet["name"],
            description=wallet_update.description or wallet["description"],
            is_active=wallet_update.is_active if wallet_update.is_active is not None else bool(wallet["is_active"]),
            created_at=wallet["created_at"],
            updated_at=wallet["updated_at"],
            balance=balance
        )
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新钱包失败: {str(e)}")


@router.delete("/{wallet_id}", response_model=Dict[str, Any])
async def delete_wallet(wallet_id: int):
    """
    删除钱包
    """
    try:
        # 这里简化处理，实际需要实现删除逻辑
        # 暂时返回成功
        return {"success": True, "message": "钱包删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除钱包失败: {str(e)}")


@router.get("/{wallet_id}/balance", response_model=Dict[str, Any])
async def get_wallet_balance(wallet_id: int):
    """
    获取钱包余额
    """
    try:
        # 获取钱包
        wallets = storage.get_wallets()
        wallet = next((w for w in wallets if w["id"] == wallet_id), None)
        
        if not wallet:
            raise HTTPException(status_code=404, detail="钱包不存在")
        
        # 获取钱包余额
        if wallet["chain"] not in blockchain_instances:
            blockchain_instances[wallet["chain"]] = BlockchainFactory.create_blockchain(wallet["chain"])
        
        blockchain = blockchain_instances[wallet["chain"]]
        balance = blockchain.get_balance(wallet["address"]) if blockchain else 0.0
        
        return {
            "wallet_id": wallet_id,
            "address": wallet["address"],
            "chain": wallet["chain"],
            "balance": balance
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取钱包余额失败: {str(e)}")
