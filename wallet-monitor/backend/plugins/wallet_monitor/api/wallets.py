# 钱包管理API接口

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

router = APIRouter(prefix="/wallets", tags=["wallets"])

# 模拟数据存储
wallets = []

@router.get("/")
def get_wallets() -> List[Dict[str, Any]]:
    """获取钱包列表
    
    Returns:
        钱包列表
    """
    return wallets

@router.post("/")
def add_wallet(wallet: Dict[str, Any]) -> Dict[str, Any]:
    """添加钱包
    
    Args:
        wallet: 钱包信息
        
    Returns:
        添加的钱包信息
    """
    # 验证钱包信息
    if "address" not in wallet or "chain" not in wallet:
        raise HTTPException(status_code=400, detail="钱包地址和链不能为空")
    
    # 检查钱包是否已存在
    for existing_wallet in wallets:
        if existing_wallet["address"] == wallet["address"] and existing_wallet["chain"] == wallet["chain"]:
            raise HTTPException(status_code=400, detail="钱包已存在")
    
    # 添加钱包
    wallet_id = len(wallets) + 1
    wallet["id"] = wallet_id
    wallets.append(wallet)
    
    return wallet

@router.get("/{wallet_id}")
def get_wallet(wallet_id: int) -> Dict[str, Any]:
    """获取钱包详情
    
    Args:
        wallet_id: 钱包ID
        
    Returns:
        钱包详情
    """
    for wallet in wallets:
        if wallet["id"] == wallet_id:
            return wallet
    
    raise HTTPException(status_code=404, detail="钱包不存在")

@router.put("/{wallet_id}")
def update_wallet(wallet_id: int, wallet: Dict[str, Any]) -> Dict[str, Any]:
    """更新钱包信息
    
    Args:
        wallet_id: 钱包ID
        wallet: 钱包信息
        
    Returns:
        更新后的钱包信息
    """
    for i, existing_wallet in enumerate(wallets):
        if existing_wallet["id"] == wallet_id:
            # 更新钱包信息
            wallets[i].update(wallet)
            wallets[i]["id"] = wallet_id  # 保持ID不变
            return wallets[i]
    
    raise HTTPException(status_code=404, detail="钱包不存在")

@router.delete("/{wallet_id}")
def delete_wallet(wallet_id: int) -> Dict[str, str]:
    """删除钱包
    
    Args:
        wallet_id: 钱包ID
        
    Returns:
        删除结果
    """
    for i, existing_wallet in enumerate(wallets):
        if existing_wallet["id"] == wallet_id:
            wallets.pop(i)
            return {"message": "钱包删除成功"}
    
    raise HTTPException(status_code=404, detail="钱包不存在")
