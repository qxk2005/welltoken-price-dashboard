from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from backend.app.database import get_db, AsyncSessionLocal
from backend.app.models.token_price import RelaySite, SiteModelPricing
from backend.app.schemas.token_schema import RelaySiteSchema, RelaySiteCreate, RelaySiteUpdate
from backend.app.services.relay_fetcher import relay_fetcher

router = APIRouter(prefix="/channels", tags=["Relay Channels & Providers"])

@router.get("", response_model=List[RelaySiteSchema])
async def list_all_relay_channels():
    """获取所有供应商与中转渠道列表"""
    async with AsyncSessionLocal() as session:
        stmt = select(
            RelaySite,
            func.count(SiteModelPricing.id).label("model_count")
        ).outerjoin(
            SiteModelPricing, RelaySite.id == SiteModelPricing.site_id
        ).group_by(RelaySite.id).order_by(RelaySite.id.asc())

        res = await session.execute(stmt)
        rows = res.all()
        
        result = []
        for site, model_cnt in rows:
            schema_data = RelaySiteSchema.model_validate(site)
            schema_data.model_count = model_cnt
            result.append(schema_data)
        return result

@router.post("", response_model=RelaySiteSchema)
async def create_relay_channel(payload: RelaySiteCreate, db: AsyncSession = Depends(get_db)):
    """新增自建中转渠道配置"""
    site = RelaySite(
        name=payload.name,
        base_url=payload.base_url.rstrip("/"),
        api_key=payload.api_key or "",
        site_type=payload.site_type,
        recharge_rate=payload.recharge_rate,
        models_endpoint=payload.models_endpoint,
        status_endpoint=payload.status_endpoint,
        website=payload.website or "",
        doc_url=payload.doc_url or "",
        env_vars=payload.env_vars or "",
        is_official_catalog=False,
        is_active=payload.is_active,
        notes=payload.notes or "",
        last_latency_ms=50.0
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)
    
    # 异步触发初始化模型定价
    await relay_fetcher.detect_and_sync_site(site.id)
    return site

@router.put("/{site_id}", response_model=RelaySiteSchema)
async def update_relay_channel(site_id: int, payload: RelaySiteUpdate, db: AsyncSession = Depends(get_db)):
    """更新供应商/渠道信息 (如配置 API Key)"""
    stmt = select(RelaySite).where(RelaySite.id == site_id)
    res = await db.execute(stmt)
    site = res.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Channel not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        if k == "base_url" and v:
            v = v.rstrip("/")
        setattr(site, k, v)
        
    await db.commit()
    await db.refresh(site)
    return site

@router.delete("/{site_id}")
async def delete_relay_channel(site_id: int, db: AsyncSession = Depends(get_db)):
    """删除指定渠道"""
    stmt = delete(RelaySite).where(RelaySite.id == site_id)
    await db.execute(stmt)
    await db.commit()
    return {"status": "deleted", "site_id": site_id}

@router.post("/{site_id}/ping")
async def ping_and_sync_single_channel(site_id: int):
    """测试单个渠道连通性并同步最新倍率"""
    return await relay_fetcher.detect_and_sync_site(site_id)

@router.post("/ping-all")
async def ping_and_sync_all_channels():
    """一键探测并全量同步所有活跃渠道"""
    return await relay_fetcher.sync_all_sites()
