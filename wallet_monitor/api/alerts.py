from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..data.storage import DataStorage
from ..data.analyzer import DataAnalyzer
from .middleware import PaginatedResponse, paginate, require_auth

router = APIRouter(prefix="/alerts", tags=["alerts"])

# 数据存储实例（延迟初始化，由 plugin.py 先创建单例以确定正确 db_path）
_storage = None


def _get_storage() -> DataStorage:
    global _storage
    if _storage is None:
        _storage = DataStorage()
    return _storage


class AlertResponse(BaseModel):
    """
    告警响应模型
    """
    id: int
    wallet_address: str
    chain: str
    alert_type: str
    message: str
    risk_level: str
    transaction_hash: Optional[str] = None
    status: str
    created_at: str
    resolved_at: Optional[str] = None


class AlertRuleCreate(BaseModel):
    """
    创建告警规则请求模型
    """
    name: str
    description: Optional[str] = None
    rule_type: str
    threshold: Optional[float] = None
    enabled: Optional[bool] = True


class AlertRuleUpdate(BaseModel):
    """
    更新告警规则请求模型
    """
    name: Optional[str] = None
    description: Optional[str] = None
    threshold: Optional[float] = None
    enabled: Optional[bool] = None


class AlertRuleResponse(BaseModel):
    """
    告警规则响应模型
    """
    id: int
    name: str
    description: Optional[str] = None
    rule_type: str
    threshold: Optional[float] = None
    enabled: bool
    created_at: str
    updated_at: str


@router.get("/", response_model=PaginatedResponse[AlertResponse])
async def get_alerts(
    wallet_address: Optional[str] = Query(None, description="钱包地址"),
    chain: Optional[str] = Query(None, description="区块链类型"),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    _auth: dict = require_auth,
):
    """
    获取告警列表（分页）
    """
    storage = _get_storage()
    try:
        # 获取全部告警（用于分页计数）
        all_alerts = storage.get_alerts(
            wallet_address=wallet_address,
            chain=chain,
        )
        total = len(all_alerts)

        # 切片获取当前页
        offset = (page - 1) * page_size
        page_alerts = all_alerts[offset : offset + page_size]

        # 构建响应
        responses = []
        for alert in page_alerts:
            responses.append(AlertResponse(
                id=alert["id"],
                wallet_address=alert["wallet_address"],
                chain=alert["chain"],
                alert_type=alert["alert_type"],
                message=alert["message"],
                risk_level=alert["risk_level"],
                transaction_hash=alert["transaction_hash"],
                status=alert["status"],
                created_at=alert["created_at"],
                resolved_at=alert["resolved_at"],
            ))

        return paginate(responses, total, page, page_size)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: int):
    """
    获取告警详情
    """
    storage = _get_storage()
    try:
        alert = storage.get_alert_by_id(alert_id)

        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")

        response = AlertResponse(
            id=alert["id"],
            wallet_address=alert["wallet_address"],
            chain=alert["chain"],
            alert_type=alert["alert_type"],
            message=alert["message"],
            risk_level=alert["risk_level"],
            transaction_hash=alert.get("transaction_hash"),
            status=alert["status"],
            created_at=alert["created_at"],
            resolved_at=alert.get("resolved_at")
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警详情失败: {str(e)}")


@router.post("/resolve/{alert_id}", response_model=Dict[str, Any])
async def resolve_alert(alert_id: int):
    """
    解决告警
    """
    storage = _get_storage()
    try:
        alert = storage.get_alert_by_id(alert_id)

        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")

        success = storage.resolve_alert(alert_id)

        if not success:
            raise HTTPException(status_code=400, detail="解决告警失败")

        return {"success": True, "message": "告警解决成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")


@router.get("/rules/", response_model=List[AlertRuleResponse])
async def get_alert_rules(enabled_only: bool = Query(True, description="是否只返回启用的规则")):
    """
    获取告警规则列表
    """
    storage = _get_storage()
    try:
        # 获取告警规则列表
        rules = storage.get_alert_rules(enabled_only=enabled_only)

        # 构建响应
        responses = []
        for rule in rules:
            response = AlertRuleResponse(
                id=rule["id"],
                name=rule["name"],
                description=rule["description"],
                rule_type=rule["rule_type"],
                threshold=rule["threshold"],
                enabled=bool(rule["enabled"]),
                created_at=rule["created_at"],
                updated_at=rule["updated_at"]
            )
            responses.append(response)

        return responses
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警规则列表失败: {str(e)}")


@router.post("/rules/", response_model=AlertRuleResponse)
async def create_alert_rule(rule: AlertRuleCreate):
    """
    创建告警规则
    """
    storage = _get_storage()
    try:
        # 创建告警规则
        success = storage.add_alert_rule({
            "name": rule.name,
            "description": rule.description,
            "rule_type": rule.rule_type,
            "threshold": rule.threshold,
            "enabled": rule.enabled
        })

        if not success:
            raise HTTPException(status_code=400, detail="创建告警规则失败")

        # 获取创建的规则
        rules = storage.get_alert_rules(enabled_only=False)
        created_rule = next((r for r in rules if r["name"] == rule.name), None)

        if not created_rule:
            raise HTTPException(status_code=404, detail="告警规则创建成功但未找到")

        # 构建响应
        response = AlertRuleResponse(
            id=created_rule["id"],
            name=created_rule["name"],
            description=created_rule["description"],
            rule_type=created_rule["rule_type"],
            threshold=created_rule["threshold"],
            enabled=bool(created_rule["enabled"]),
            created_at=created_rule["created_at"],
            updated_at=created_rule["updated_at"]
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建告警规则失败: {str(e)}")


@router.put("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_alert_rule(rule_id: int, rule_update: AlertRuleUpdate):
    """
    更新告警规则
    """
    storage = _get_storage()
    try:
        rule = storage.get_alert_rule_by_id(rule_id)

        if not rule:
            raise HTTPException(status_code=404, detail="告警规则不存在")

        success = storage.update_alert_rule(
            rule_id=rule_id,
            name=rule_update.name,
            description=rule_update.description,
            threshold=rule_update.threshold,
            enabled=rule_update.enabled
        )

        if not success:
            raise HTTPException(status_code=400, detail="更新告警规则失败")

        updated_rule = storage.get_alert_rule_by_id(rule_id)

        if not updated_rule:
            raise HTTPException(status_code=404, detail="更新后未找到告警规则")

        response = AlertRuleResponse(
            id=updated_rule["id"],
            name=updated_rule["name"],
            description=updated_rule["description"],
            rule_type=updated_rule["rule_type"],
            threshold=updated_rule["threshold"],
            enabled=bool(updated_rule["enabled"]),
            created_at=updated_rule["created_at"],
            updated_at=updated_rule["updated_at"]
        )

        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新告警规则失败: {str(e)}")


@router.delete("/rules/{rule_id}", response_model=Dict[str, Any])
async def delete_alert_rule(rule_id: int):
    """
    删除告警规则
    """
    storage = _get_storage()
    try:
        rule = storage.get_alert_rule_by_id(rule_id)

        if not rule:
            raise HTTPException(status_code=404, detail="告警规则不存在")

        success = storage.delete_alert_rule(rule_id)

        if not success:
            raise HTTPException(status_code=400, detail="删除告警规则失败")

        return {"success": True, "message": "告警规则删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除告警规则失败: {str(e)}")


@router.get("/stats/patterns", response_model=Dict[str, Any])
async def get_alert_patterns():
    """
    获取告警模式分析
    """
    storage = _get_storage()
    try:
        # 获取所有告警
        alerts = storage.get_alerts()

        # 分析告警模式
        analysis_result = DataAnalyzer.analyze_alert_patterns(alerts)

        return {
            "success": True,
            "analysis": analysis_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警模式分析失败: {str(e)}")


@router.post("/test", response_model=Dict[str, Any])
async def test_alert(wallet_address: str, chain: str, alert_type: str):
    """
    测试告警
    """
    storage = _get_storage()
    try:
        # 创建测试告警
        alert = {
            "wallet_address": wallet_address,
            "chain": chain,
            "alert_type": alert_type,
            "message": f"测试告警: {alert_type}",
            "risk_level": "medium",
            "transaction_hash": None
        }

        success = storage.add_alert(alert)

        if not success:
            raise HTTPException(status_code=400, detail="创建测试告警失败")

        return {
            "success": True,
            "message": "测试告警创建成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试告警失败: {str(e)}")
