import asyncio
import time
import math
from datetime import datetime
from typing import List, Dict, Any, Set, Optional
from fastapi import WebSocket
from sqlalchemy import select, func, or_
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing
from backend.app.schemas.token_schema import (
    ComparisonItemSchema,
    PaginatedComparisonResponse,
    ComparisonFilterOptionsResponse,
    FilterItemOption
)
from backend.app.services.models_dev_sync import models_dev_sync
from backend.app.services.relay_fetcher import relay_fetcher
from backend.app.services.exchange_rate import exchange_rate_service

class TokenDashboardService:
    def __init__(self):
        self.usd_to_cny_rate: float = 7.30
        self.active_websockets: Set[WebSocket] = set()
        self.is_running: bool = False
        self._loop_task: asyncio.Task | None = None

    async def initialize(self):
        """系统启动时全量真实初始化：拉取外汇汇率、models.dev 标准库与渠道倍率数据"""
        print("[DashboardService] Fetching real USD/CNY exchange rate...")
        self.usd_to_cny_rate = await exchange_rate_service.fetch_real_rate()

        # 检查数据库是否已有数据，若无则执行一次全量拉取
        async with AsyncSessionLocal() as session:
            count = await session.scalar(select(func.count(SiteModelPricing.id)))
            if not count or count == 0:
                print("[DashboardService] Database is empty, performing initial full sync from models.dev...")
                await models_dev_sync.full_sync_from_models_dev()
            else:
                print(f"[DashboardService] Found {count} pricing records in local SQLite cache.")

        print(f"[DashboardService] System ready! Exchange rate: 1 USD = {self.usd_to_cny_rate} CNY")

    async def start_loop(self):
        """启动后台定时扫描与行情广播循环"""
        self.is_running = True
        self._loop_task = asyncio.create_task(self._background_worker())
        print("[DashboardService] Background auto-sync worker started.")

    async def stop_loop(self):
        """停止后台循环"""
        self.is_running = False
        if self._loop_task:
            self._loop_task.cancel()
        print("[DashboardService] Background auto-sync worker stopped.")

    async def _background_worker(self):
        """后台轮询更新中转站状态与广播行情"""
        while self.is_running:
            try:
                await asyncio.sleep(60)
                await self.broadcast_market_update()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[DashboardService Worker Error]: {e}")
                await asyncio.sleep(10)

    async def get_paginated_comparison_matrix(
        self,
        providers: Optional[List[str]] = None,
        series: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        sites: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> PaginatedComparisonResponse:
        """高性能分页查询全网聚合比价大矩阵 (SQLite 级 LIMIT + OFFSET)"""
        async with AsyncSessionLocal() as session:
            # 基础条件构建
            base_conditions = [RelaySite.is_active == True]

            if providers and len(providers) > 0 and "all" not in providers:
                lower_p = [p.lower() for p in providers]
                base_conditions.append(func.lower(ModelMetadata.provider).in_(lower_p))

            if series and len(series) > 0 and "all" not in series:
                base_conditions.append(ModelMetadata.series.in_(series))

            if models and len(models) > 0 and "all" not in models:
                base_conditions.append(ModelMetadata.model_id.in_(models))

            if sites and len(sites) > 0 and "all" not in sites:
                base_conditions.append(RelaySite.name.in_(sites))

            if search_query and search_query.strip():
                q = f"%{search_query.strip().lower()}%"
                base_conditions.append(
                    or_(
                        func.lower(ModelMetadata.model_id).like(q),
                        func.lower(ModelMetadata.name).like(q),
                        func.lower(ModelMetadata.series).like(q),
                        func.lower(RelaySite.name).like(q),
                        func.lower(ModelMetadata.provider).like(q)
                    )
                )

            # 1. 统计总数
            count_stmt = select(func.count(SiteModelPricing.id)).join(
                RelaySite, SiteModelPricing.site_id == RelaySite.id
            ).join(
                ModelMetadata, SiteModelPricing.model_id == ModelMetadata.model_id
            ).where(*base_conditions)

            total = await session.scalar(count_stmt) or 0
            total_pages = math.ceil(total / page_size) if total > 0 else 1

            # 2. 分页提取条目
            offset = max(0, (page - 1) * page_size)
            data_stmt = select(SiteModelPricing, RelaySite, ModelMetadata).join(
                RelaySite, SiteModelPricing.site_id == RelaySite.id
            ).join(
                ModelMetadata, SiteModelPricing.model_id == ModelMetadata.model_id
            ).where(*base_conditions).order_by(
                SiteModelPricing.calculated_input_usd.asc()
            ).limit(page_size).offset(offset)

            res = await session.execute(data_stmt)
            rows = res.all()

            items: List[ComparisonItemSchema] = []
            for p, site, model in rows:
                in_cny = round(p.calculated_input_usd * self.usd_to_cny_rate, 4)
                out_cny = round(p.calculated_output_usd * self.usd_to_cny_rate, 4)

                items.append(
                    ComparisonItemSchema(
                        id=p.id,
                        model_id=model.model_id,
                        model_name=model.name,
                        provider=model.provider,
                        series=model.series or "通用系列",
                        site_id=site.id,
                        site_name=site.name,
                        site_type=site.site_type,
                        is_official=site.site_type == "official",
                        model_ratio=p.model_ratio,
                        calculated_input_usd=p.calculated_input_usd,
                        calculated_output_usd=p.calculated_output_usd,
                        calculated_cache_usd=p.calculated_cache_usd,
                        calculated_input_cny=in_cny,
                        calculated_output_cny=out_cny,
                        discount_percent=p.discount_percent,
                        last_tested_tps=p.last_tested_tps,
                        site_score=site.score,
                        site_status=site.last_status,
                        last_latency_ms=site.last_latency_ms,
                        updated_at=p.updated_at
                    )
                )

            return PaginatedComparisonResponse(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
                items=items
            )

    async def get_filter_options(
        self,
        selected_providers: Optional[List[str]] = None,
        selected_series: Optional[List[str]] = None
    ) -> ComparisonFilterOptionsResponse:
        """轻量级快速获取各筛选维度的去重候选列表与计数"""
        async with AsyncSessionLocal() as session:
            # 1. 厂商列表与计数
            p_stmt = select(
                ModelMetadata.provider,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, ModelMetadata.model_id == SiteModelPricing.model_id
            ).group_by(ModelMetadata.provider).order_by(func.count(SiteModelPricing.id).desc())
            p_res = await session.execute(p_stmt)
            providers_opt = [
                FilterItemOption(value=p, label=p.title(), count=cnt)
                for p, cnt in p_res.all() if p
            ]

            # 2. 系列列表与计数
            s_stmt = select(
                ModelMetadata.series,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, ModelMetadata.model_id == SiteModelPricing.model_id
            )
            if selected_providers and len(selected_providers) > 0 and "all" not in selected_providers:
                s_stmt = s_stmt.where(func.lower(ModelMetadata.provider).in_([p.lower() for p in selected_providers]))
            s_stmt = s_stmt.group_by(ModelMetadata.series).order_by(func.count(SiteModelPricing.id).desc())
            s_res = await session.execute(s_stmt)
            series_opt = [
                FilterItemOption(value=s or "通用系列", label=s or "通用系列", count=cnt)
                for s, cnt in s_res.all() if s
            ]

            # 3. 热门模型列表 (Top 100)
            m_stmt = select(
                ModelMetadata.model_id,
                ModelMetadata.name,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, ModelMetadata.model_id == SiteModelPricing.model_id
            )
            if selected_providers and len(selected_providers) > 0 and "all" not in selected_providers:
                m_stmt = m_stmt.where(func.lower(ModelMetadata.provider).in_([p.lower() for p in selected_providers]))
            if selected_series and len(selected_series) > 0 and "all" not in selected_series:
                m_stmt = m_stmt.where(ModelMetadata.series.in_(selected_series))
            m_stmt = m_stmt.group_by(ModelMetadata.model_id).order_by(func.count(SiteModelPricing.id).desc()).limit(100)
            m_res = await session.execute(m_stmt)
            models_opt = [
                FilterItemOption(value=m_id, label=m_id, count=cnt)
                for m_id, m_name, cnt in m_res.all()
            ]

            # 4. 供应商/渠道列表 (Top 100)
            st_stmt = select(
                RelaySite.name,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, RelaySite.id == SiteModelPricing.site_id
            ).group_by(RelaySite.name).order_by(func.count(SiteModelPricing.id).desc()).limit(100)
            st_res = await session.execute(st_stmt)
            sites_opt = [
                FilterItemOption(value=s_name, label=s_name, count=cnt)
                for s_name, cnt in st_res.all()
            ]

            return ComparisonFilterOptionsResponse(
                providers=providers_opt,
                series=series_opt,
                models=models_opt,
                sites=sites_opt
            )

    async def get_comparison_matrix(
        self,
        provider: str | None = None,
        model_id: str | None = None,
        search_query: str | None = None
    ) -> List[ComparisonItemSchema]:
        """兼容获取前 100 条比价数据"""
        res = await self.get_paginated_comparison_matrix(
            providers=[provider] if provider else None,
            models=[model_id] if model_id else None,
            search_query=search_query,
            page=1,
            page_size=100
        )
        return res.items

    # WebSocket 管理
    async def connect_ws(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)

    def disconnect_ws(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)

    async def broadcast(self, payload: Dict[str, Any]):
        if not self.active_websockets:
            return
        dead = set()
        for ws in self.active_websockets:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.add(ws)
        for d in dead:
            self.disconnect_ws(d)

    async def broadcast_market_update(self):
        matrix = await self.get_comparison_matrix()
        payload = {
            "type": "matrix_update",
            "timestamp": int(time.time() * 1000),
            "data": [m.model_dump(mode="json") for m in matrix]
        }
        await self.broadcast(payload)

dashboard_service = TokenDashboardService()
