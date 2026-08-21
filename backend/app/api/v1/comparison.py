from fastapi import APIRouter, Query
from typing import List, Optional
from backend.app.schemas.token_schema import ComparisonItemSchema
from backend.app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/comparison", tags=["Comparison Matrix"])

@router.get("/matrix", response_model=List[ComparisonItemSchema])
async def get_price_comparison_matrix(
    provider: Optional[str] = Query(None, description="厂商筛选: openai, anthropic, deepseek, google, alibaba, all"),
    model_id: Optional[str] = Query(None, description="模型 ID: gpt-4o, claude-3-5-sonnet, deepseek-v3 等"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取全网大模型 Token 聚合比价矩阵"""
    return await dashboard_service.get_comparison_matrix(
        provider=provider,
        model_id=model_id,
        search_query=search
    )

@router.get("/analytics/scatter")
async def get_price_tps_scatter_data(
    model_id: str = Query("deepseek-v3", description="目标模型 ID")
):
    """获取指定模型在全网各渠道的价格-性能 (Price vs TPS) 散点分布数据"""
    matrix = await dashboard_service.get_comparison_matrix(model_id=model_id)
    scatter_points = []
    for item in matrix:
        scatter_points.append({
            "site_id": item.site_id,
            "site_name": item.site_name,
            "site_type": item.site_type,
            "input_price_usd": item.calculated_input_usd,
            "tps": item.last_tested_tps,
            "score": item.site_score,
            "discount_percent": item.discount_percent,
            "is_official": item.is_official
        })
    return {
        "model_id": model_id,
        "points": scatter_points
    }
