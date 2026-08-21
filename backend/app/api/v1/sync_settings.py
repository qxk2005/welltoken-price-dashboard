import os
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter
from sqlalchemy import select, func
from backend.app.config import settings
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing, SpeedTestHistory
from backend.app.schemas.token_schema import SyncStatusSchema, ExchangeRateUpdate
from backend.app.services.dashboard_service import dashboard_service
from backend.app.services.models_dev_sync import models_dev_sync
from backend.app.services.relay_fetcher import relay_fetcher

router = APIRouter(prefix="/settings", tags=["Sync Hub & Settings"])

@router.get("/status", response_model=SyncStatusSchema)
async def get_sync_and_db_status():
    """获取当前系统同步调度状态与 SQLite 数据库统计信息"""
    async with AsyncSessionLocal() as session:
        m_cnt = await session.scalar(select(func.count(ModelMetadata.id)))
        s_cnt = await session.scalar(select(func.count(RelaySite.id)).where(RelaySite.is_active == True))
        p_cnt = await session.scalar(select(func.count(SiteModelPricing.id)))

    # 计算 db 文件大小
    db_file = Path(settings.DATABASE_PATH)
    db_size = round(db_file.stat().st_size / (1024 * 1024), 2) if db_file.exists() else 0.0

    return SyncStatusSchema(
        models_dev_last_sync=models_dev_sync.last_sync_time,
        models_dev_total_models=m_cnt or 0,
        relays_last_sync=relay_fetcher.last_sync_time,
        total_active_sites=s_cnt or 0,
        total_pricings_cached=p_cnt or 0,
        usd_to_cny_rate=dashboard_service.usd_to_cny_rate,
        db_size_mb=db_size
    )

@router.post("/exchange-rate")
async def update_exchange_rate(payload: ExchangeRateUpdate):
    """更新 USD / CNY 基准换算汇率"""
    dashboard_service.usd_to_cny_rate = payload.usd_to_cny_rate
    # 广播最新汇率触发前端重算
    await dashboard_service.broadcast_market_update()
    return {"status": "updated", "rate": payload.usd_to_cny_rate}

@router.post("/full-sync")
async def trigger_full_system_sync():
    """一键触发全网数据全量同步 (models.dev + 全部中转渠道)"""
    res1 = await models_dev_sync.sync_from_models_dev()
    res2 = await relay_fetcher.sync_all_sites()
    await dashboard_service.broadcast_market_update()
    return {
        "status": "success",
        "models_sync": res1,
        "relays_sync": res2
    }
