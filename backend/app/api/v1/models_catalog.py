from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.database import get_db, AsyncSessionLocal
from backend.app.models.token_price import ModelMetadata, SiteModelPricing
from backend.app.schemas.token_schema import ModelMetadataSchema, ModelMetadataCreate
from backend.app.services.models_dev_sync import models_dev_sync

router = APIRouter(prefix="/models", tags=["Model Catalog & Standards"])

@router.get("", response_model=List[ModelMetadataSchema])
async def list_models_catalog(
    provider: Optional[str] = Query(None, description="厂商筛选"),
    featured_only: bool = Query(False, description="仅看置顶热门")
):
    """获取所有大模型标准规格元数据列表"""
    async with AsyncSessionLocal() as session:
        stmt = select(ModelMetadata).order_by(ModelMetadata.provider.asc())
        if provider and provider != "all":
            stmt = stmt.where(ModelMetadata.provider == provider.lower())
        if featured_only:
            stmt = stmt.where(ModelMetadata.is_featured == True)
            
        res = await session.execute(stmt)
        models = res.scalars().all()
        
        result = []
        for m in models:
            # 统计提供该模型的中转站总数与最低价格
            p_stmt = select(SiteModelPricing).where(
                SiteModelPricing.model_id == m.model_id,
                SiteModelPricing.is_available == True
            )
            p_res = await session.execute(p_stmt)
            pricings = p_res.scalars().all()
            
            cnt = len(pricings)
            lowest = min([p.calculated_input_usd for p in pricings]) if pricings else m.official_input_price
            
            item = ModelMetadataSchema.model_validate(m)
            item.active_relay_count = cnt
            item.lowest_price_usd = lowest
            result.append(item)
            
        return result

@router.get("/{model_id}", response_model=ModelMetadataSchema)
async def get_model_detail(model_id: str, db: AsyncSession = Depends(get_db)):
    """获取指定模型详情"""
    stmt = select(ModelMetadata).where(ModelMetadata.model_id == model_id)
    res = await db.execute(stmt)
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="Model not found")
    return m

@router.post("/sync-models-dev")
async def trigger_sync_models_dev():
    """手动触发从 models.dev 同步最新大模型元数据与官方价格"""
    return await models_dev_sync.sync_from_models_dev()
