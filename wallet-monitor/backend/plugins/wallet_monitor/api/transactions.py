# 交易查询API接口

from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any

router = APIRouter(prefix="/transactions", tags=["transactions"])

# 模拟交易数据
transactions = [
    {
        "id": 1,
        "hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
        "from": "0x1234567890123456789012345678901234567890",
        "to": "0x0987654321098765432109876543210987654321",
        "value": 1000000000000000000,  # 1 ETH
        "gas": 21000,
        "gas_price": 20000000000,  # 20 Gwei
        "nonce": "0",
        "input": "0x",
        "block_hash": "0x1234567890123456789012345678901234567890123456789012345678901234",
        "block_number": 1000000,
        "transaction_index": 0,
        "chain": "ethereum",
        "timestamp": 1640995200,  # 2022-01-01 00:00:00
        "processed_at": 1640995200
    },
    {
        "id": 2,
        "hash": "0x0987654321098765432109876543210987654321098765432109876543210987",
        "from": "0x0987654321098765432109876543210987654321",
        "to": "0x1234567890123456789012345678901234567890",
        "value": 500000000000000000,  # 0.5 ETH
        "gas": 21000,
        "gas_price": 20000000000,  # 20 Gwei
        "nonce": "1",
        "input": "0x",
        "block_hash": "0x0987654321098765432109876543210987654321098765432109876543210987",
        "block_number": 1000001,
        "transaction_index": 0,
        "chain": "ethereum",
        "timestamp": 1640995260,  # 2022-01-01 00:01:00
        "processed_at": 1640995260
    }
]

@router.get("/")
def get_transactions(
    wallet_address: str = Query(None, description="钱包地址"),
    chain: str = Query(None, description="区块链"),
    limit: int = Query(100, description="返回数量限制")
) -> List[Dict[str, Any]]:
    """获取交易列表
    
    Args:
        wallet_address: 钱包地址
        chain: 区块链
        limit: 返回数量限制
        
    Returns:
        交易列表
    """
    filtered_transactions = transactions
    
    # 按钱包地址过滤
    if wallet_address:
        filtered_transactions = [
            tx for tx in filtered_transactions
            if tx["from"] == wallet_address or tx["to"] == wallet_address
        ]
    
    # 按区块链过滤
    if chain:
        filtered_transactions = [
            tx for tx in filtered_transactions
            if tx["chain"] == chain
        ]
    
    # 按时间戳降序排序
    filtered_transactions.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # 限制返回数量
    return filtered_transactions[:limit]

@router.get("/{transaction_hash}")
def get_transaction(transaction_hash: str) -> Dict[str, Any]:
    """获取交易详情
    
    Args:
        transaction_hash: 交易哈希
        
    Returns:
        交易详情
    """
    for transaction in transactions:
        if transaction["hash"] == transaction_hash:
            return transaction
    
    raise HTTPException(status_code=404, detail="交易不存在")
