from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from data.storage import DataStorage
from data.processor import DataProcessor
from data.analyzer import DataAnalyzer
from blockchain.factory import BlockchainFactory

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

# 数据存储实例
storage = DataStorage()

# 区块链实例缓存
blockchain_instances = {}


class TransactionResponse(BaseModel):
    """
    交易响应模型
    """
    id: int
    hash: str
    wallet_address: str
    chain: str
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    amount: float
    status: str
    timestamp: Optional[int] = None
    block_number: Optional[int] = None
    block_hash: Optional[str] = None
    gas_used: Optional[int] = None
    gas_price: Optional[int] = None
    input_data: Optional[str] = None
    is_contract_interaction: bool
    contract_address: Optional[str] = None
    anomaly_score: float
    risk_level: str
    created_at: str


class TransactionFilter(BaseModel):
    """
    交易过滤模型
    """
    wallet_address: Optional[str] = None
    chain: Optional[str] = None
    from_address: Optional[str] = None
    to_address: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    is_contract_interaction: Optional[bool] = None
    risk_level: Optional[str] = None


@router.get("/", response_model=List[TransactionResponse])
async def get_transactions(
    wallet_address: Optional[str] = Query(None, description="钱包地址"),
    chain: Optional[str] = Query(None, description="区块链类型"),
    limit: int = Query(100, description="返回数量限制"),
    offset: int = Query(0, description="偏移量")
):
    """
    获取交易列表
    """
    try:
        # 获取交易列表
        transactions = storage.get_transactions(
            wallet_address=wallet_address,
            chain=chain,
            limit=limit
        )
        
        # 构建响应
        responses = []
        for tx in transactions:
            response = TransactionResponse(
                id=tx["id"],
                hash=tx["hash"],
                wallet_address=tx["wallet_address"],
                chain=tx["chain"],
                from_address=tx["from_address"],
                to_address=tx["to_address"],
                amount=tx["amount"],
                status=tx["status"],
                timestamp=tx["timestamp"],
                block_number=tx["block_number"],
                block_hash=tx["block_hash"],
                gas_used=tx["gas_used"],
                gas_price=tx["gas_price"],
                input_data=tx["input_data"],
                is_contract_interaction=bool(tx["is_contract_interaction"]),
                contract_address=tx["contract_address"],
                anomaly_score=tx["anomaly_score"],
                risk_level=tx["risk_level"],
                created_at=tx["created_at"]
            )
            responses.append(response)
        
        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易列表失败: {str(e)}")


@router.get("/{transaction_hash}", response_model=TransactionResponse)
async def get_transaction(transaction_hash: str):
    """
    获取交易详情
    """
    try:
        # 这里简化处理，实际需要根据交易哈希查询
        # 暂时返回模拟数据
        raise HTTPException(status_code=404, detail="交易不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易详情失败: {str(e)}")


@router.post("/sync", response_model=Dict[str, Any])
async def sync_transactions(wallet_address: str, chain: str):
    """
    同步钱包交易
    """
    try:
        # 验证区块链类型
        supported_chains = BlockchainFactory.get_supported_chains()
        if chain not in supported_chains:
            raise HTTPException(status_code=400, detail=f"不支持的区块链类型: {chain}")
        
        # 获取区块链实例
        if chain not in blockchain_instances:
            blockchain_instances[chain] = BlockchainFactory.create_blockchain(chain)
        
        blockchain = blockchain_instances[chain]
        if not blockchain:
            raise HTTPException(status_code=500, detail="无法连接到区块链网络")
        
        # 获取交易历史
        transactions = blockchain.get_transactions(wallet_address)
        
        # 清洗和存储交易
        synced_count = 0
        for tx in transactions:
            # 清洗交易数据
            cleaned_tx = DataProcessor.clean_transaction(tx, chain)
            cleaned_tx["wallet_address"] = wallet_address
            
            # 检测异常
            wallet_history = storage.get_transactions(wallet_address=wallet_address, chain=chain)
            anomaly_result = DataProcessor.detect_anomaly(cleaned_tx, wallet_history)
            cleaned_tx["anomaly_score"] = anomaly_result.get("anomaly_score", 0)
            cleaned_tx["risk_level"] = anomaly_result.get("risk_level", "low")
            
            # 存储交易
            if storage.add_transaction(cleaned_tx):
                synced_count += 1
        
        return {
            "success": True,
            "message": f"同步交易成功，共同步 {synced_count} 笔交易",
            "synced_count": synced_count
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"同步交易失败: {str(e)}")


@router.post("/analyze", response_model=Dict[str, Any])
async def analyze_transactions(wallet_address: str, chain: str):
    """
    分析钱包交易
    """
    try:
        # 获取钱包交易
        transactions = storage.get_transactions(wallet_address=wallet_address, chain=chain)
        
        if not transactions:
            raise HTTPException(status_code=404, detail="钱包没有交易记录")
        
        # 分析交易
        analysis_result = DataAnalyzer.analyze_wallet_activity(wallet_address, transactions)
        
        # 分析交易趋势
        trend_analysis = DataAnalyzer.analyze_transaction_trends(transactions)
        
        # 检测异常
        anomalies = DataAnalyzer.detect_wallet_anomalies(wallet_address, transactions)
        
        return {
            "success": True,
            "wallet_address": wallet_address,
            "chain": chain,
            "activity_analysis": analysis_result,
            "trend_analysis": trend_analysis,
            "anomalies": anomalies
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析交易失败: {str(e)}")


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_transaction_summary():
    """
    获取交易统计摘要
    """
    try:
        # 获取所有交易
        transactions = storage.get_transactions()
        
        if not transactions:
            return {
                "total_transactions": 0,
                "total_volume": 0,
                "avg_transaction_amount": 0,
                "contract_interactions": 0,
                "anomaly_count": 0,
                "by_chain": {}
            }
        
        # 计算统计数据
        total_transactions = len(transactions)
        total_volume = sum(tx.get("amount", 0) for tx in transactions)
        avg_transaction_amount = total_volume / total_transactions if total_transactions > 0 else 0
        contract_interactions = sum(1 for tx in transactions if tx.get("is_contract_interaction"))
        anomaly_count = sum(1 for tx in transactions if tx.get("risk_level") in ["medium", "high"])
        
        # 按链统计
        by_chain = {}
        for tx in transactions:
            chain = tx.get("chain")
            if chain not in by_chain:
                by_chain[chain] = {
                    "count": 0,
                    "volume": 0
                }
            by_chain[chain]["count"] += 1
            by_chain[chain]["volume"] += tx.get("amount", 0)
        
        return {
            "total_transactions": total_transactions,
            "total_volume": total_volume,
            "avg_transaction_amount": avg_transaction_amount,
            "contract_interactions": contract_interactions,
            "anomaly_count": anomaly_count,
            "by_chain": by_chain
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取交易统计失败: {str(e)}")
