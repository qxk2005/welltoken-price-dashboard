import math
from datetime import datetime
from typing import List, Optional, Dict, Any
import httpx
from sqlalchemy import select, func, or_, and_, distinct
from sqlalchemy.orm import selectinload
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, SiteModelPricing, ModelMetadata, SystemSetting
from backend.app.schemas.token_schema import (
    ComparisonItemSchema,
    PaginatedComparisonResponse,
    ComparisonFilterOptionsResponse,
    FilterItemOption
)

OFFICIAL_LAB_KEYS = [
    "alibaba", "openai", "google", "anthropic", "deepseek", "zhipuai",
    "moonshotai", "meta", "mistral", "nvidia", "bytedance", "xai",
    "minimax", "xiaomi", "cohere", "stepfun", "tencent", "perplexity",
    "microsoft", "baichuan", "upstage", "aisingapore", "arcee-ai", "ibm",
    "meituan", "poolside", "sakana", "sarvam", "thinkingmachines"
]

from fastapi import WebSocket

class DashboardService:
    def __init__(self):
        self.usd_to_cny_rate = 7.25
        self.exchange_rate_source = "https://open.er-api.com/v6/latest/USD"
        self.exchange_rate_updated_at = datetime.utcnow()
        self.active_websockets: set = set()
        self._is_settings_loaded = False

    async def ensure_settings_loaded(self):
        """确保系统配置已从数据库加载"""
        if not self._is_settings_loaded:
            await self.load_persisted_settings()
            self._is_settings_loaded = True

    async def load_persisted_settings(self):
        """从数据库加载持久化的系统配置 (汇率、源端网址、更新时间戳等)"""
        async with AsyncSessionLocal() as session:
            try:
                res = await session.execute(select(SystemSetting))
                settings_map = {s.key: s.value for s in res.scalars().all()}
                
                if "usd_to_cny_rate" in settings_map:
                    self.usd_to_cny_rate = float(settings_map["usd_to_cny_rate"])
                if "exchange_rate_source" in settings_map:
                    self.exchange_rate_source = settings_map["exchange_rate_source"]
                if "exchange_rate_updated_at" in settings_map:
                    try:
                        self.exchange_rate_updated_at = datetime.fromisoformat(settings_map["exchange_rate_updated_at"])
                    except Exception:
                        pass
                self._is_settings_loaded = True
            except Exception as e:
                print(f"[DashboardService] 加载持久化系统配置失败: {e}")

    async def save_persisted_settings(
        self,
        rate: Optional[float] = None,
        source: Optional[str] = None,
        updated_at: Optional[datetime] = None
    ):
        """将系统配置持久化写入数据库"""
        async with AsyncSessionLocal() as session:
            try:
                if rate is not None:
                    self.usd_to_cny_rate = float(rate)
                    s_obj = await session.get(SystemSetting, "usd_to_cny_rate")
                    if not s_obj:
                        s_obj = SystemSetting(key="usd_to_cny_rate", value=str(self.usd_to_cny_rate), description="USD对CNY基础换算汇率")
                        session.add(s_obj)
                    else:
                        s_obj.value = str(self.usd_to_cny_rate)

                if source is not None:
                    self.exchange_rate_source = source
                    s_obj = await session.get(SystemSetting, "exchange_rate_source")
                    if not s_obj:
                        s_obj = SystemSetting(key="exchange_rate_source", value=self.exchange_rate_source, description="外汇汇率权威获取源网址")
                        session.add(s_obj)
                    else:
                        s_obj.value = self.exchange_rate_source

                if updated_at is not None:
                    self.exchange_rate_updated_at = updated_at
                else:
                    self.exchange_rate_updated_at = datetime.utcnow()

                s_obj = await session.get(SystemSetting, "exchange_rate_updated_at")
                if not s_obj:
                    s_obj = SystemSetting(key="exchange_rate_updated_at", value=self.exchange_rate_updated_at.isoformat(), description="外汇汇率最后一次更新时间")
                    session.add(s_obj)
                else:
                    s_obj.value = self.exchange_rate_updated_at.isoformat()

                await session.commit()
                self._is_settings_loaded = True
            except Exception as e:
                print(f"[DashboardService] 持久化保存系统配置失败: {e}")

    async def connect_ws(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)

    def disconnect_ws(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)

    async def broadcast(self, payload: dict):
        if not self.active_websockets:
            return
        dead = []
        for ws in list(self.active_websockets):
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active_websockets.discard(ws)

    async def broadcast_market_update(self):
        if not self.active_websockets:
            return
        matrix = await self.get_comparison_matrix()
        await self.broadcast({
            "type": "update",
            "data": [m.model_dump(mode="json") for m in matrix],
            "usd_to_cny_rate": self.usd_to_cny_rate,
            "exchange_rate_source": self.exchange_rate_source,
            "exchange_rate_updated_at": self.exchange_rate_updated_at.isoformat()
        })

    async def fetch_online_exchange_rate(self, source_url: Optional[str] = None) -> Dict[str, Any]:
        """从在线权威外汇源抓取最新 USD/CNY 实时汇率并持久化到数据库"""
        await self.ensure_settings_loaded()
        target_url = source_url.strip() if source_url and source_url.strip() else self.exchange_rate_source
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(target_url)
            if resp.status_code != 200:
                raise Exception(f"在线外汇源返回异常状态码: {resp.status_code}")
            
            data = resp.json()
            rates = data.get("rates") or data.get("conversion_rates") or {}
            cny_rate = rates.get("CNY") or rates.get("cny")
            
            if not cny_rate or not isinstance(cny_rate, (int, float)):
                raise Exception("未能从返回数据中解析到有效的 CNY 人民币汇率字段")
            
            new_rate = round(float(cny_rate), 4)
            new_updated_at = datetime.utcnow()
            
            # 持久化保存到数据库
            await self.save_persisted_settings(
                rate=new_rate,
                source=target_url,
                updated_at=new_updated_at
            )
            
            await self.broadcast({
                "type": "EXCHANGE_RATE_UPDATE",
                "rate": self.usd_to_cny_rate,
                "source": self.exchange_rate_source,
                "updated_at": self.exchange_rate_updated_at.isoformat()
            })
            
            return {
                "status": "success",
                "rate": self.usd_to_cny_rate,
                "source": self.exchange_rate_source,
                "updated_at": self.exchange_rate_updated_at
            }

    async def get_overview_statistics(self) -> Dict[str, Any]:
        """获取仪表盘概览统计指标"""
        await self.ensure_settings_loaded()
        async with AsyncSessionLocal() as session:
            # 渠道总数与活跃数
            site_count_res = await session.execute(
                select(
                    func.count(RelaySite.id),
                    func.count().filter(RelaySite.is_active == True)
                )
            )
            total_sites, active_sites = site_count_res.one()

            # 收录标准模型总数
            model_count = await session.scalar(select(func.count(ModelMetadata.id))) or 0

            # 聚合定价条目总数
            pricing_count = await session.scalar(select(func.count(SiteModelPricing.id))) or 0

            # 计算平均折扣力度
            avg_discount = await session.scalar(
                select(func.avg(SiteModelPricing.discount_percent))
                .where(SiteModelPricing.discount_percent > 0)
            ) or 0.0

            # 平均网络延迟
            avg_latency = await session.scalar(
                select(func.avg(RelaySite.last_latency_ms))
                .where(RelaySite.is_active == True, RelaySite.last_latency_ms > 0)
            ) or 45.0

            return {
                "total_sites": total_sites,
                "active_sites": active_sites,
                "total_models": model_count,
                "total_pricings": pricing_count,
                "usd_to_cny_rate": self.usd_to_cny_rate,
                "avg_discount_percent": round(avg_discount, 1),
                "avg_network_latency_ms": round(avg_latency, 1),
                "last_sync_time": "实时同步中"
            }

    async def get_paginated_comparison_matrix(
        self,
        providers: Optional[List[str]] = None,
        series: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        sites: Optional[List[str]] = None,
        search_query: Optional[str] = None,
        exclude_zero_price: bool = True,
        sort_field: str = "calculated_input_usd",
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 50
    ) -> PaginatedComparisonResponse:
        """高性能分页查询全网 Token 比价矩阵 (支持多列升降序排序与 0 元过滤)"""
        await self.ensure_settings_loaded()
        async with AsyncSessionLocal() as session:
            # 基础条件构建
            base_conditions = [RelaySite.is_active == True]

            # 0. 过滤输入输出均为 0 的条目
            if exclude_zero_price:
                base_conditions.append(
                    or_(
                        SiteModelPricing.calculated_input_usd > 0,
                        SiteModelPricing.calculated_output_usd > 0
                    )
                )

            # 1. 模型厂商过滤 (支持 30 大权威 Lab 与 other)
            if providers and len(providers) > 0 and "all" not in providers:
                has_other = "other" in [p.lower() for p in providers]
                normal_providers = [p.lower() for p in providers if p.lower() != "other"]
                if "bytedance" in normal_providers:
                    normal_providers.append("bytedance-seed")

                if has_other and normal_providers:
                    base_conditions.append(
                        or_(
                            func.lower(ModelMetadata.provider).in_(normal_providers),
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif has_other:
                    base_conditions.append(
                        or_(
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif normal_providers:
                    base_conditions.append(func.lower(ModelMetadata.provider).in_(normal_providers))

            # 2. 模型系列过滤
            if series and len(series) > 0 and "all" not in series:
                base_conditions.append(ModelMetadata.series.in_(series))

            # 3. 模型名称过滤
            if models and len(models) > 0 and "all" not in models:
                base_conditions.append(
                    or_(
                        ModelMetadata.model_id.in_(models),
                        SiteModelPricing.model_id.in_(models)
                    )
                )

            # 4. 渠道中转站过滤
            if sites and len(sites) > 0 and "all" not in sites:
                if "__NONE__" in sites:
                    base_conditions.append(RelaySite.id == -999)
                else:
                    base_conditions.append(RelaySite.name.in_(sites))

            # 5. 全局模糊搜索
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

            # 统计总数
            count_stmt = select(func.count(SiteModelPricing.id)).join(
                RelaySite, SiteModelPricing.site_id == RelaySite.id
            ).join(
                ModelMetadata, SiteModelPricing.model_id == ModelMetadata.model_id
            ).where(*base_conditions)

            total = await session.scalar(count_stmt) or 0
            total_pages = math.ceil(total / page_size) if total > 0 else 1

            # 排序构建
            sort_col_map = {
                "calculated_input_usd": SiteModelPricing.calculated_input_usd,
                "input_price": SiteModelPricing.calculated_input_usd,
                "calculated_output_usd": SiteModelPricing.calculated_output_usd,
                "output_price": SiteModelPricing.calculated_output_usd,
                "model_ratio": SiteModelPricing.model_ratio,
                "last_tested_tps": SiteModelPricing.last_tested_tps,
                "tps": SiteModelPricing.last_tested_tps,
                "model_id": ModelMetadata.model_id,
                "site_name": RelaySite.name,
                "provider": ModelMetadata.provider,
                "series": ModelMetadata.series
            }
            order_col = sort_col_map.get(sort_field, SiteModelPricing.calculated_input_usd)
            order_expr = order_col.desc() if sort_order.lower() == "desc" else order_col.asc()

            # 分页提取条目
            offset = max(0, (page - 1) * page_size)
            data_stmt = select(SiteModelPricing, RelaySite, ModelMetadata).join(
                RelaySite, SiteModelPricing.site_id == RelaySite.id
            ).join(
                ModelMetadata, SiteModelPricing.model_id == ModelMetadata.model_id
            ).where(*base_conditions).order_by(
                order_expr
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
                        group_name=getattr(site, "group_name", "") or p.group_name or "",
                        site_currency=getattr(site, "currency", "CNY") or "CNY",
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
        selected_series: Optional[List[str]] = None,
        selected_models: Optional[List[str]] = None,
        selected_sites: Optional[List[str]] = None,
        exclude_zero_price: bool = True
    ) -> ComparisonFilterOptionsResponse:
        """轻量级快速获取各筛选维度的去重候选列表与计数 (四级完全级联联动与 0 价格过滤)"""
        await self.ensure_settings_loaded()
        async with AsyncSessionLocal() as session:
            # 1. 厂商列表与计数 (严格与「厂商与模型系列」30 大权威 Lab 对齐)
            official_labs_order = [
                "alibaba", "openai", "google", "anthropic", "deepseek", "zhipuai",
                "moonshotai", "meta", "mistral", "nvidia", "bytedance", "xai",
                "minimax", "xiaomi", "cohere", "stepfun", "tencent", "perplexity",
                "microsoft", "baichuan", "upstage", "aisingapore", "arcee-ai", "ibm",
                "meituan", "poolside", "sakana", "sarvam", "thinkingmachines", "other"
            ]

            p_stmt = select(
                ModelMetadata.provider,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, ModelMetadata.model_id == SiteModelPricing.model_id
            )
            if exclude_zero_price:
                p_stmt = p_stmt.where(
                    or_(
                        SiteModelPricing.calculated_input_usd > 0,
                        SiteModelPricing.calculated_output_usd > 0
                    )
                )
            p_stmt = p_stmt.group_by(ModelMetadata.provider)
            p_res = await session.execute(p_stmt)
            raw_counts = {p.lower(): cnt for p, cnt in p_res.all() if p}

            # 汇总 30 家权威 Lab 计数
            providers_opt: List[FilterItemOption] = []
            other_cnt = 0
            for lab_key in official_labs_order:
                if lab_key == "other":
                    continue
                cnt = raw_counts.get(lab_key, 0)
                if lab_key == "bytedance":
                    cnt += raw_counts.get("bytedance-seed", 0)
                if cnt > 0:
                    providers_opt.append(FilterItemOption(value=lab_key, label=lab_key.title(), count=cnt))

            # 统计非 30 大厂商的模型条目归入 other
            for p, cnt in raw_counts.items():
                if p not in official_labs_order and p != "bytedance-seed":
                    other_cnt += cnt
            if other_cnt > 0 or raw_counts.get("other", 0) > 0:
                other_total = other_cnt + raw_counts.get("other", 0)
                providers_opt.append(FilterItemOption(value="other", label="其他独立研究机构", count=other_total))

            # 2. 系列列表与计数 (根据选中的厂商级联收敛，按字母升序排序)
            s_stmt = select(
                ModelMetadata.series,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, ModelMetadata.model_id == SiteModelPricing.model_id
            )
            if exclude_zero_price:
                s_stmt = s_stmt.where(
                    or_(
                        SiteModelPricing.calculated_input_usd > 0,
                        SiteModelPricing.calculated_output_usd > 0
                    )
                )
            if selected_providers and len(selected_providers) > 0 and "all" not in selected_providers:
                has_other = "other" in [p.lower() for p in selected_providers]
                normal_p = [p.lower() for p in selected_providers if p.lower() != "other"]
                if "bytedance" in normal_p:
                    normal_p.append("bytedance-seed")
                
                if has_other and normal_p:
                    s_stmt = s_stmt.where(
                        or_(
                            func.lower(ModelMetadata.provider).in_(normal_p),
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif has_other:
                    s_stmt = s_stmt.where(
                        or_(
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif normal_p:
                    s_stmt = s_stmt.where(func.lower(ModelMetadata.provider).in_(normal_p))

            s_stmt = s_stmt.group_by(ModelMetadata.series).order_by(ModelMetadata.series.asc())
            s_res = await session.execute(s_stmt)
            series_opt = [
                FilterItemOption(value=s or "通用系列", label=s or "通用系列", count=cnt)
                for s, cnt in s_res.all() if s
            ]

            # 3. 模型列表 (根据选中的厂商与系列级联收敛，按字母升序排序)
            m_stmt = select(
                ModelMetadata.model_id,
                ModelMetadata.name,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, ModelMetadata.model_id == SiteModelPricing.model_id
            )
            if exclude_zero_price:
                m_stmt = m_stmt.where(
                    or_(
                        SiteModelPricing.calculated_input_usd > 0,
                        SiteModelPricing.calculated_output_usd > 0
                    )
                )
            if selected_providers and len(selected_providers) > 0 and "all" not in selected_providers:
                has_other = "other" in [p.lower() for p in selected_providers]
                normal_p = [p.lower() for p in selected_providers if p.lower() != "other"]
                if "bytedance" in normal_p:
                    normal_p.append("bytedance-seed")
                
                if has_other and normal_p:
                    m_stmt = m_stmt.where(
                        or_(
                            func.lower(ModelMetadata.provider).in_(normal_p),
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif has_other:
                    m_stmt = m_stmt.where(
                        or_(
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif normal_p:
                    m_stmt = m_stmt.where(func.lower(ModelMetadata.provider).in_(normal_p))

            if selected_series and len(selected_series) > 0 and "all" not in selected_series:
                m_stmt = m_stmt.where(ModelMetadata.series.in_(selected_series))

            m_stmt = m_stmt.group_by(ModelMetadata.model_id, ModelMetadata.name).order_by(ModelMetadata.name.asc()).limit(300)
            m_res = await session.execute(m_stmt)
            models_opt = [
                FilterItemOption(value=m_id, label=f"{m_name} ({m_id})", count=cnt)
                for m_id, m_name, cnt in m_res.all()
            ]

            # 4. 供应商/渠道列表 (根据选中的厂商/系列/模型级联收敛，按字母升序排序)
            st_stmt = select(
                RelaySite.name,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, RelaySite.id == SiteModelPricing.site_id
            ).join(
                ModelMetadata, SiteModelPricing.model_id == ModelMetadata.model_id
            )
            if exclude_zero_price:
                st_stmt = st_stmt.where(
                    or_(
                        SiteModelPricing.calculated_input_usd > 0,
                        SiteModelPricing.calculated_output_usd > 0
                    )
                )
            if selected_providers and len(selected_providers) > 0 and "all" not in selected_providers:
                has_other = "other" in [p.lower() for p in selected_providers]
                normal_p = [p.lower() for p in selected_providers if p.lower() != "other"]
                if "bytedance" in normal_p:
                    normal_p.append("bytedance-seed")
                if has_other and normal_p:
                    st_stmt = st_stmt.where(
                        or_(
                            func.lower(ModelMetadata.provider).in_(normal_p),
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif has_other:
                    st_stmt = st_stmt.where(
                        or_(
                            func.lower(ModelMetadata.provider) == "other",
                            func.lower(ModelMetadata.provider).notin_(OFFICIAL_LAB_KEYS)
                        )
                    )
                elif normal_p:
                    st_stmt = st_stmt.where(func.lower(ModelMetadata.provider).in_(normal_p))

            if selected_series and len(selected_series) > 0 and "all" not in selected_series:
                st_stmt = st_stmt.where(ModelMetadata.series.in_(selected_series))
            if selected_models and len(selected_models) > 0 and "all" not in selected_models:
                st_stmt = st_stmt.where(ModelMetadata.model_id.in_(selected_models))

            st_stmt = st_stmt.group_by(RelaySite.name).order_by(RelaySite.name.asc()).limit(200)
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
        """兼容获取比价数据"""
        res = await self.get_paginated_comparison_matrix(
            providers=[provider] if provider else None,
            models=[model_id] if model_id else None,
            search_query=search_query,
            page=1,
            page_size=100
        )
        return res.items

dashboard_service = DashboardService()
