import math
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, or_, and_, distinct
from sqlalchemy.orm import selectinload
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, SiteModelPricing, ModelMetadata
from backend.app.schemas.token_schema import (
    ComparisonItemSchema,
    PaginatedComparisonResponse,
    ComparisonFilterOptionsResponse,
    FilterItemOption
)

class DashboardService:
    def __init__(self):
        self.usd_to_cny_rate = 7.25

    async def get_overview_statistics(self) -> Dict[str, Any]:
        """获取仪表盘概览统计指标"""
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
        page: int = 1,
        page_size: int = 50
    ) -> PaginatedComparisonResponse:
        """高性能分页查询全网 Token 比价矩阵"""
        async with AsyncSessionLocal() as session:
            # 基础条件构建
            base_conditions = [RelaySite.is_active == True]

            if providers and len(providers) > 0 and "all" not in providers:
                lower_p = [p.lower() for p in providers]
                base_conditions.append(func.lower(ModelMetadata.provider).in_(lower_p))

            if series and len(series) > 0 and "all" not in series:
                base_conditions.append(ModelMetadata.series.in_(series))

            if models and len(models) > 0 and "all" not in models:
                base_conditions.append(
                    or_(
                        ModelMetadata.model_id.in_(models),
                        SiteModelPricing.model_id.in_(models)
                    )
                )

            if sites and len(sites) > 0 and "all" not in sites:
                if "__NONE__" in sites:
                    base_conditions.append(RelaySite.id == -999)
                else:
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
        selected_series: Optional[List[str]] = None,
        selected_models: Optional[List[str]] = None,
        selected_sites: Optional[List[str]] = None
    ) -> ComparisonFilterOptionsResponse:
        """轻量级快速获取各筛选维度的去重候选列表与计数 (四级完全级联联动)"""
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
            ).group_by(ModelMetadata.provider)
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

            # 2. 系列列表与计数 (根据选中的厂商级联收敛)
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

            # 3. 模型列表 (根据选中的厂商与系列级联收敛)
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
            m_stmt = m_stmt.group_by(ModelMetadata.model_id, ModelMetadata.name).order_by(func.count(SiteModelPricing.id).desc()).limit(300)
            m_res = await session.execute(m_stmt)
            models_opt = [
                FilterItemOption(value=m_id, label=f"{m_name} ({m_id})", count=cnt)
                for m_id, m_name, cnt in m_res.all()
            ]

            # 4. 供应商/渠道列表 (根据选中的厂商/系列/模型级联收敛)
            st_stmt = select(
                RelaySite.name,
                func.count(SiteModelPricing.id)
            ).join(
                SiteModelPricing, RelaySite.id == SiteModelPricing.site_id
            ).join(
                ModelMetadata, SiteModelPricing.model_id == ModelMetadata.model_id
            )
            if selected_providers and len(selected_providers) > 0 and "all" not in selected_providers:
                st_stmt = st_stmt.where(func.lower(ModelMetadata.provider).in_([p.lower() for p in selected_providers]))
            if selected_series and len(selected_series) > 0 and "all" not in selected_series:
                st_stmt = st_stmt.where(ModelMetadata.series.in_(selected_series))
            if selected_models and len(selected_models) > 0 and "all" not in selected_models:
                st_stmt = st_stmt.where(ModelMetadata.model_id.in_(selected_models))

            st_stmt = st_stmt.group_by(RelaySite.name).order_by(func.count(SiteModelPricing.id).desc()).limit(200)
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
