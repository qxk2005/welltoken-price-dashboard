import os
from pathlib import Path
from datetime import datetime
from typing import List
from fastapi import APIRouter
from sqlalchemy import select, func, desc
from backend.app.config import settings
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing, SpeedTestHistory, SyncLog
from backend.app.schemas.token_schema import SyncStatusSchema, SyncLogSchema, ExchangeRateUpdate
from backend.app.services.dashboard_service import dashboard_service
from backend.app.services.models_dev_sync import models_dev_sync
from backend.app.services.relay_fetcher import relay_fetcher

router = APIRouter(prefix="/settings", tags=["Sync Hub & Settings"])

@router.get("/status", response_model=SyncStatusSchema)
async def get_system_sync_status():
    """获取数据同步总体健康状态与指标 (涵盖汇率源与更新时间)"""
    await dashboard_service.ensure_settings_loaded()
    async with AsyncSessionLocal() as session:
        # 模型数
        m_cnt = await session.scalar(select(func.count(ModelMetadata.id)))
        # 渠道数
        s_cnt = await session.scalar(select(func.count(RelaySite.id)))
        # 价格快照数
        p_cnt = await session.scalar(select(func.count(SiteModelPricing.id)))
        # 获取最近 10 条同步日志
        logs_stmt = select(SyncLog).order_by(desc(SyncLog.created_at)).limit(10)
        logs_res = await session.execute(logs_stmt)
        logs = logs_res.scalars().all()

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
        exchange_rate_source=dashboard_service.exchange_rate_source,
        exchange_rate_updated_at=dashboard_service.exchange_rate_updated_at,
        db_size_mb=db_size,
        recent_sync_logs=[SyncLogSchema.model_validate(l) for l in logs]
    )

@router.get("/sync-logs", response_model=List[SyncLogSchema])
async def get_all_sync_logs():
    """获取历史数据同步审计日志列表"""
    async with AsyncSessionLocal() as session:
        stmt = select(SyncLog).order_by(desc(SyncLog.created_at)).limit(50)
        res = await session.execute(stmt)
        logs = res.scalars().all()
        return [SyncLogSchema.model_validate(l) for l in logs]

@router.post("/exchange-rate")
async def update_exchange_rate(payload: ExchangeRateUpdate):
    """更新 USD / CNY 基准换算汇率与源网址并持久化保存"""
    await dashboard_service.ensure_settings_loaded()
    await dashboard_service.save_persisted_settings(
        rate=payload.usd_to_cny_rate,
        source=payload.exchange_rate_source,
        updated_at=datetime.utcnow()
    )
    await dashboard_service.broadcast_market_update()
    return {
        "status": "updated",
        "rate": dashboard_service.usd_to_cny_rate,
        "source": dashboard_service.exchange_rate_source,
        "updated_at": dashboard_service.exchange_rate_updated_at
    }

@router.post("/exchange-rate/fetch-online")
async def fetch_online_exchange_rate(payload: Optional[dict] = None):
    """从在线权威外汇源实时抓取最新 USD / CNY 汇率"""
    source_url = payload.get("source_url") if payload else None
    try:
        res = await dashboard_service.fetch_online_exchange_rate(source_url)
        await dashboard_service.broadcast_market_update()
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"抓取在线汇率失败: {str(e)}")

@router.post("/full-sync")
async def trigger_full_system_sync():
    """一键触发 models.dev (models.json + catalog.json + api.json) 全量同步"""
    res1 = await models_dev_sync.full_sync_from_models_dev()
    await dashboard_service.broadcast_market_update()
    return {
        "status": "success",
        "sync_result": res1
    }
