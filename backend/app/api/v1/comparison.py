from fastapi import APIRouter, Query
from typing import List, Optional
from backend.app.schemas.token_schema import (
    ComparisonItemSchema,
    PaginatedComparisonResponse,
    ComparisonFilterOptionsResponse
)
from backend.app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/comparison", tags=["Comparison Matrix"])

@router.get("/paginated", response_model=PaginatedComparisonResponse)
async def get_paginated_comparison(
    provider: Optional[List[str]] = Query(None, description="厂商多选"),
    series: Optional[List[str]] = Query(None, description="系列多选"),
    model: Optional[List[str]] = Query(None, description="模型多选"),
    site: Optional[List[str]] = Query(None, description="渠道多选"),
    search: Optional[str] = Query(None, description="全局搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=10, le=200, description="每页条数")
):
    """高性能分页查询全网大模型 Token 比价数据"""
    return await dashboard_service.get_paginated_comparison_matrix(
        providers=provider,
        series=series,
        models=model,
        sites=site,
        search_query=search,
        page=page,
        page_size=page_size
    )

@router.get("/filter-options", response_model=ComparisonFilterOptionsResponse)
async def get_filter_options(
    provider: Optional[List[str]] = Query(None, description="已选厂商"),
    series: Optional[List[str]] = Query(None, description="已选系列")
):
    """轻量级获取筛选器候选选项及统计条数"""
    return await dashboard_service.get_filter_options(
        selected_providers=provider,
        selected_series=series
    )

@router.get("/matrix", response_model=List[ComparisonItemSchema])
async def get_price_comparison_matrix(
    provider: Optional[str] = Query(None, description="厂商筛选"),
    model_id: Optional[str] = Query(None, description="模型 ID"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """兼容旧接口获取前 100 条比价数据"""
    return await dashboard_service.get_comparison_matrix(
        provider=provider,
        model_id=model_id,
        search_query=search
    )

@router.get("/analytics/scatter")
async def get_price_tps_scatter_data(
    model_id: str = Query("deepseek-v3", description="目标模型 ID")
):
    """获取指定模型在各渠道的性价比散点数据 (前 30 个渠道)"""
    res = await dashboard_service.get_paginated_comparison_matrix(
        models=[model_id],
        page=1,
        page_size=30
    )
    scatter_points = []
    for item in res.items:
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
