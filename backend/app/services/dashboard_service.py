import asyncio
import time
from datetime import datetime
from typing import List, Dict, Any, Set
from fastapi import WebSocket
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing
from backend.app.schemas.token_schema import ComparisonItemSchema
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

        print("[DashboardService] Initializing models catalog from models.dev (online & offline)...")
        await models_dev_sync.sync_from_models_dev()

        print("[DashboardService] Initializing relay sites & real probe matrix...")
        await relay_fetcher.init_default_sites()
        
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
                await asyncio.sleep(30)
                await self.broadcast_market_update()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[DashboardService Worker Error]: {e}")
                await asyncio.sleep(10)

    async def get_comparison_matrix(
        self,
        provider: str | None = None,
        model_id: str | None = None,
        search_query: str | None = None
    ) -> List[ComparisonItemSchema]:
        """获取全网聚合比价大矩阵数据 (带实时汇率折算与官方折扣)"""
        async with AsyncSessionLocal() as session:
            stmt = select(SiteModelPricing, RelaySite, ModelMetadata).join(
                RelaySite, SiteModelPricing.site_id == RelaySite.id
            ).join(
                ModelMetadata, SiteModelPricing.model_id == ModelMetadata.model_id
            ).where(RelaySite.is_active == True)

            if provider and provider != "all":
                stmt = stmt.where(ModelMetadata.provider == provider.lower())
            if model_id and model_id != "all":
                stmt = stmt.where(ModelMetadata.model_id == model_id)

            res = await session.execute(stmt)
            rows = res.all()

            results: List[ComparisonItemSchema] = []
            for p, site, model in rows:
                if search_query:
                    q = search_query.lower()
                    if q not in model.model_id.lower() and q not in model.name.lower() and q not in site.name.lower():
                        continue

                in_cny = round(p.calculated_input_usd * self.usd_to_cny_rate, 4)
                out_cny = round(p.calculated_output_usd * self.usd_to_cny_rate, 4)

                results.append(
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

            return results

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
