from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, update
from sqlalchemy.orm import selectinload
from backend.app.database import get_db, AsyncSessionLocal
from backend.app.models.token_price import RelaySite, SiteModelPricing, ModelMetadata, ChannelModelMapping, ModelAlias
from backend.app.schemas.token_schema import (
    RelaySiteSchema, RelaySiteCreate, RelaySiteUpdate,
    ChannelProbeRequest, ChannelProbeResponse, ModelMappingItem,
    ChannelWizardCreateRequest, ChannelModelMappingSchema,
    ChannelMappingsBatchUpdate, PromoteAliasRequest
)
from backend.app.services.relay_fetcher import relay_fetcher
from backend.app.services.model_normalizer import model_normalizer

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

@router.get("/{site_id}/models")
async def get_channel_models(site_id: int):
    """高速查询指定供应商/渠道所提供的所有模型与实时定价列表"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(SiteModelPricing)
            .where(SiteModelPricing.site_id == site_id)
            .options(selectinload(SiteModelPricing.model))
            .order_by(SiteModelPricing.calculated_input_usd.asc())
        )
        res = await session.execute(stmt)
        pricings = res.scalars().all()

        result = []
        for p in pricings:
            m = p.model
            result.append({
                "id": p.id,
                "model_id": p.model_id,
                "model_name": m.name if m else p.model_id,
                "provider": m.provider if m else "other",
                "series": m.series if m else "通用系列",
                "context_window": m.context_window if m else 128000,
                "max_output": m.max_output if m else 8192,
                "calculated_input_usd": p.calculated_input_usd,
                "calculated_output_usd": p.calculated_output_usd,
                "calculated_cache_usd": p.calculated_cache_usd,
                "discount_percent": p.discount_percent,
                "last_tested_tps": p.last_tested_tps,
                "is_available": p.is_available
            })
        return result

@router.post("/probe", response_model=ChannelProbeResponse)
async def probe_channel_and_models(payload: ChannelProbeRequest):
    """【向导第2步】真实发起 HTTP 请求探测中转站连通性，并执行智能模型归一化映射与多分组价格折算"""
    probe_res = await model_normalizer.probe_and_fetch_models(
        base_url=payload.base_url,
        api_key=payload.api_key or "",
        site_type=payload.site_type,
        models_endpoint=payload.models_endpoint,
        target_group=payload.target_group
    )

    mappings_data = []
    if probe_res["raw_models"]:
        raw_mappings = await model_normalizer.match_models_for_channel(
            raw_model_names=probe_res["raw_models"],
            raw_public_ratios=probe_res.get("raw_public_ratios"),
            raw_key_ratios=probe_res.get("raw_key_ratios"),
            raw_model_items=probe_res.get("raw_model_items"),
            selected_group=probe_res.get("selected_group", "default"),
            selected_group_ratio=probe_res.get("selected_group_ratio", 1.0),
            global_group_ratios=probe_res.get("global_group_ratios")
        )
        for m in raw_mappings:
            mappings_data.append(ModelMappingItem(**m))

    matched_cnt = sum(1 for m in mappings_data if m.is_matched)
    unmatched_cnt = len(mappings_data) - matched_cnt

    return ChannelProbeResponse(
        is_online=probe_res["is_online"],
        status_code=probe_res["status_code"],
        latency_ms=probe_res["latency_ms"],
        raw_count=probe_res["raw_count"],
        matched_count=matched_cnt,
        unmatched_count=unmatched_cnt,
        fetch_source=probe_res.get("fetch_source", ""),
        token_group=probe_res.get("token_group", ""),
        token_group_ratio=probe_res.get("token_group_ratio"),
        has_special_pricing=probe_res.get("has_special_pricing", False),
        special_pricing_count=probe_res.get("special_pricing_count", 0),
        available_groups=probe_res.get("available_groups", []),
        selected_group=probe_res.get("selected_group", ""),
        currency="CNY",
        error=probe_res["error"],
        mappings=mappings_data
    )

@router.post("/wizard-create")
async def wizard_create_channel(payload: ChannelWizardCreateRequest, db: AsyncSession = Depends(get_db)):
    """【向导第4步】完成渠道创建、写入渠道模型映射，并初始化生成模型定价记录"""
    selected_grp = payload.selected_group or ""

    # 1. 创建渠道主体
    site = RelaySite(
        name=payload.name,
        base_url=payload.base_url.rstrip("/"),
        api_key=payload.api_key or "",
        site_type=payload.site_type,
        group_name=selected_grp,
        recharge_rate=payload.recharge_rate,
        models_endpoint=payload.models_endpoint,
        status_endpoint=payload.status_endpoint or "",
        is_official_catalog=False,
        is_active=True,
        notes=payload.notes or "",
        last_latency_ms=45.0
    )
    db.add(site)
    await db.flush()

    # 2. 遍历 mappings，写入 ChannelModelMapping 并生成 SiteModelPricing
    selected_items = [m for m in payload.mappings if m.is_selected and m.standard_model_id]
    created_models_count = 0

    # 预加载所有标准模型
    m_res = await db.execute(select(ModelMetadata))
    standard_models = {m.model_id: m for m in m_res.scalars().all()}

    for item in selected_items:
        std_id = item.standard_model_id.strip()
        # A. 写入渠道私有映射记录
        cm = ChannelModelMapping(
            site_id=site.id,
            channel_model_name=item.channel_model_name.strip(),
            standard_model_id=std_id,
            custom_ratio=item.custom_ratio,
            is_enabled=True
        )
        db.add(cm)

        # B. 查验标准模型是否存在，计算折算价格
        std_meta = standard_models.get(std_id)
        if std_meta:
            ratio = item.custom_ratio if item.custom_ratio is not None else payload.default_ratio
            if item.input_price_usd > 0:
                calc_in = item.input_price_usd
                calc_out = item.output_price_usd
                calc_cache = item.cache_price_usd
            else:
                calc_in = round(std_meta.official_input_price * ratio * site.recharge_rate, 4)
                calc_out = round(std_meta.official_output_price * ratio * site.recharge_rate, 4)
                calc_cache = round(std_meta.official_cache_price * ratio * site.recharge_rate, 4)

            discount = round(((calc_in - std_meta.official_input_price) / std_meta.official_input_price * 100), 1) if std_meta.official_input_price > 0 else 0.0

            pricing = SiteModelPricing(
                site_id=site.id,
                model_id=std_id,
                group_name=selected_grp,
                site_model_name=item.channel_model_name.strip(),
                model_ratio=ratio,
                group_ratio=1.0,
                calculated_input_usd=calc_in,
                calculated_output_usd=calc_out,
                calculated_cache_usd=calc_cache,
                discount_percent=discount,
                is_available=True,
                last_tested_tps=50.0
            )
            db.add(pricing)
            created_models_count += 1

    await db.commit()
    await db.refresh(site)

    return {
        "status": "success",
        "site_id": site.id,
        "site_name": site.name,
        "group_name": site.group_name,
        "imported_models_count": created_models_count
    }

@router.get("/{site_id}/mappings")
async def get_channel_mappings(site_id: int, db: AsyncSession = Depends(get_db)):
    """获取指定渠道的模型映射配置列表"""
    stmt = (
        select(ChannelModelMapping)
        .where(ChannelModelMapping.site_id == site_id)
        .order_by(ChannelModelMapping.id.asc())
    )
    res = await db.execute(stmt)
    mappings = res.scalars().all()
    return mappings

@router.put("/{site_id}/mappings")
async def update_channel_mappings(site_id: int, payload: ChannelMappingsBatchUpdate, db: AsyncSession = Depends(get_db)):
    """全量更新渠道的模型映射，并同步更新定价表"""
    # 1. 验证渠道存在
    site_res = await db.execute(select(RelaySite).where(RelaySite.id == site_id))
    site = site_res.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Channel not found")

    # 2. 清理旧的映射与定价
    await db.execute(delete(ChannelModelMapping).where(ChannelModelMapping.site_id == site_id))
    await db.execute(delete(SiteModelPricing).where(SiteModelPricing.site_id == site_id))

    # 3. 重新写入
    m_res = await db.execute(select(ModelMetadata))
    standard_models = {m.model_id: m for m in m_res.scalars().all()}

    count = 0
    for item in payload.mappings:
        if not item.is_selected or not item.standard_model_id:
            continue
        std_id = item.standard_model_id.strip()
        cm = ChannelModelMapping(
            site_id=site.id,
            channel_model_name=item.channel_model_name.strip(),
            standard_model_id=std_id,
            custom_ratio=item.custom_ratio,
            is_enabled=True
        )
        db.add(cm)

        std_meta = standard_models.get(std_id)
        if std_meta:
            ratio = item.custom_ratio if item.custom_ratio is not None else 0.65
            calc_in = round(std_meta.official_input_price * ratio * site.recharge_rate, 4)
            calc_out = round(std_meta.official_output_price * ratio * site.recharge_rate, 4)
            calc_cache = round(std_meta.official_cache_price * ratio * site.recharge_rate, 4)
            discount = round(((calc_in - std_meta.official_input_price) / std_meta.official_input_price * 100), 1) if std_meta.official_input_price > 0 else 0.0

            pricing = SiteModelPricing(
                site_id=site.id,
                model_id=std_id,
                site_model_name=item.channel_model_name.strip(),
                model_ratio=ratio,
                group_ratio=1.0,
                calculated_input_usd=calc_in,
                calculated_output_usd=calc_out,
                calculated_cache_usd=calc_cache,
                discount_percent=discount,
                is_available=True,
                last_tested_tps=50.0
            )
            db.add(pricing)
            count += 1

    await db.commit()
    return {"status": "success", "site_id": site_id, "updated_models_count": count}

@router.post("/{site_id}/change-group")
async def change_channel_group(site_id: int, payload: ChannelChangeGroupRequest, db: AsyncSession = Depends(get_db)):
    """在渠道详情中切换绑定结算分组，并一键重新计算和更新全量模型价格"""
    stmt = select(RelaySite).where(RelaySite.id == site_id)
    res = await db.execute(stmt)
    site = res.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="渠道不存在")

    site.group_name = payload.group_name.strip()
    db.add(site)
    await db.execute(
        update(RelaySite)
        .where(RelaySite.id == site.id)
        .values(group_name=site.group_name)
    )

    # 重新触发 probe 探测该分组
    probe_res = await model_normalizer.probe_and_fetch_models(
        base_url=site.base_url,
        api_key=site.api_key or "",
        site_type=site.site_type,
        models_endpoint=site.models_endpoint,
        target_group=site.group_name
    )

    if probe_res["raw_models"]:
        raw_mappings = await model_normalizer.match_models_for_channel(
            raw_model_names=probe_res["raw_models"],
            site_id=site.id,
            raw_public_ratios=probe_res.get("raw_public_ratios"),
            raw_key_ratios=probe_res.get("raw_key_ratios"),
            raw_model_items=probe_res.get("raw_model_items"),
            selected_group=site.group_name,
            selected_group_ratio=probe_res.get("selected_group_ratio", 1.0),
            global_group_ratios=probe_res.get("global_group_ratios")
        )

        await db.execute(
            update(SiteModelPricing)
            .where(SiteModelPricing.site_id == site.id)
            .values(group_name=site.group_name)
        )

        pricing_stmt = select(SiteModelPricing).where(SiteModelPricing.site_id == site.id)
        p_res = await db.execute(pricing_stmt)
        existing_pricings = {p.model_id: p for p in p_res.scalars().all()}
        for p in existing_pricings.values():
            p.group_name = site.group_name
            db.add(p)

        m_res = await db.execute(select(ModelMetadata))
        standard_models = {m.model_id: m for m in m_res.scalars().all()}

        for m_item in raw_mappings:
            std_id = m_item.get("standard_model_id")
            if std_id and std_id in standard_models:
                std_meta = standard_models[std_id]
                in_usd = m_item.get("input_price_usd", 0.0)
                out_usd = m_item.get("output_price_usd", 0.0)
                ca_usd = m_item.get("cache_price_usd", 0.0)
                discount = round(((in_usd - std_meta.official_input_price) / std_meta.official_input_price * 100), 1) if std_meta.official_input_price > 0 else 0.0

                if std_id in existing_pricings:
                    p = existing_pricings[std_id]
                    p.group_name = site.group_name
                    p.calculated_input_usd = in_usd
                    p.calculated_output_usd = out_usd
                    p.calculated_cache_usd = ca_usd
                    p.discount_percent = discount
                    p.model_ratio = m_item.get("custom_ratio") or 1.0
                else:
                    new_p = SiteModelPricing(
                        site_id=site.id,
                        model_id=std_id,
                        group_name=site.group_name,
                        site_model_name=m_item.get("channel_model_name", ""),
                        model_ratio=m_item.get("custom_ratio") or 1.0,
                        group_ratio=1.0,
                        calculated_input_usd=in_usd,
                        calculated_output_usd=out_usd,
                        calculated_cache_usd=ca_usd,
                        discount_percent=discount,
                        is_available=True,
                        last_tested_tps=50.0
                    )
                    db.add(new_p)

    await db.commit()
    return {"status": "success", "group_name": site.group_name, "message": f"已成功切换为 [{site.group_name}] 结算分组并更新模型价格"}

@router.post("/promote-alias")
async def promote_to_global_alias(payload: PromoteAliasRequest, db: AsyncSession = Depends(get_db)):
    """将某个渠道的自定义别名固化提升为全局智能别名库规则"""
    pat = payload.raw_pattern.strip().lower()
    stmt = select(ModelAlias).where(ModelAlias.raw_pattern == pat)
    res = await db.execute(stmt)
    alias = res.scalar_one_or_none()

    if alias:
        alias.standard_model_id = payload.standard_model_id
        alias.notes = payload.notes or "用户手动固化提升的全局别名"
    else:
        alias = ModelAlias(
            raw_pattern=pat,
            standard_model_id=payload.standard_model_id,
            is_system=False,
            notes=payload.notes or "用户手动固化提升的全局别名"
        )
        db.add(alias)

    await db.commit()
    # 刷新服务缓存
    await model_normalizer.initialize()
    return {"status": "success", "pattern": pat, "standard_model_id": payload.standard_model_id}

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

