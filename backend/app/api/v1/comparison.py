from fastapi import APIRouter, Query, Request
from typing import List, Optional
from backend.app.schemas.token_schema import (
    ComparisonItemSchema,
    PaginatedComparisonResponse,
    ComparisonFilterOptionsResponse
)
from backend.app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/comparison", tags=["Comparison Matrix"])

def get_query_list(request: Request, *keys: str) -> Optional[List[str]]:
    """从请求中鲁棒提取数组参数 (自动兼容 key, key[], key[0] 等格式)"""
    results = []
    for k in keys:
        values = request.query_params.getlist(k)
        if values:
            results.extend(values)
        # 兼容 key[]
        values_bracket = request.query_params.getlist(f"{k}[]")
        if values_bracket:
            results.extend(values_bracket)
    return list(set(results)) if results else None

@router.get("/paginated", response_model=PaginatedComparisonResponse)
async def get_paginated_comparison(
    request: Request,
    provider: Optional[List[str]] = Query(None, description="厂商多选"),
    series: Optional[List[str]] = Query(None, description="系列多选"),
    model: Optional[List[str]] = Query(None, description="模型多选"),
    site: Optional[List[str]] = Query(None, description="渠道多选"),
    search: Optional[str] = Query(None, description="全局搜索"),
    exclude_zero: bool = Query(True, description="是否过滤0价格/未标价条目"),
    sort_by: str = Query("calculated_input_usd", description="排序字段"),
    sort_order: str = Query("asc", description="排序顺序 (asc/desc)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=10, le=200, description="每页条数")
):
    """高性能分页查询全网大模型 Token 比价数据，支持多维级联筛选、0 元过滤与多列排序"""
    effective_providers = get_query_list(request, "provider", "providers") or provider
    effective_series = get_query_list(request, "series") or series
    effective_models = get_query_list(request, "model", "models", "model_id") or model
    effective_sites = get_query_list(request, "site", "sites", "site_name") or site

    return await dashboard_service.get_paginated_comparison_matrix(
        providers=effective_providers,
        series=effective_series,
        models=effective_models,
        sites=effective_sites,
        search_query=search,
        exclude_zero_price=exclude_zero,
        sort_field=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )

@router.get("/filter-options", response_model=ComparisonFilterOptionsResponse)
async def get_filter_options(
    request: Request,
    provider: Optional[List[str]] = Query(None, description="已选厂商"),
    series: Optional[List[str]] = Query(None, description="已选系列"),
    model: Optional[List[str]] = Query(None, description="已选模型"),
    site: Optional[List[str]] = Query(None, description="已选渠道"),
    exclude_zero: bool = Query(True, description="是否过滤0价格/未标价条目")
):
    """轻量级获取筛选器候选选项及统计条数 (支持四级联动收敛与 0 价格过滤)"""
    effective_providers = get_query_list(request, "provider", "providers") or provider
    effective_series = get_query_list(request, "series") or series
    effective_models = get_query_list(request, "model", "models", "model_id") or model
    effective_sites = get_query_list(request, "site", "sites", "site_name") or site

    return await dashboard_service.get_filter_options(
        selected_providers=effective_providers,
        selected_series=effective_series,
        selected_models=effective_models,
        selected_sites=effective_sites,
        exclude_zero_price=exclude_zero
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
