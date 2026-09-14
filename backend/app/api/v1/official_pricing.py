"""
官方大模型定价表 (Official Pricing) API 路由
提供官方价格查询、汇率动态折算、用户自定义备注/标签更新、触发实时抓取以及 HTML 快照对账查阅。
"""
import os
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update, delete

from backend.app.config import DATA_DIR
from backend.app.database import get_db
from backend.app.models.token_price import (
    OfficialModelPrice,
    OfficialSnapshot,
    SystemSetting,
    SiteModelPricing,
    ChannelModelMapping,
)
from backend.app.schemas.token_schema import (
    OfficialModelPriceSchema,
    OfficialModelPriceUpdateNotes,
    OfficialSnapshotSchema,
    OfficialScrapeRequest,
    OfficialScrapeResponse,
    ChannelMatchOfficialRequest,
    SaveOfficialMappingsRequest,
)
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS
from backend.app.services.exchange_rate import exchange_rate_service
from backend.app.services.official_benchmark_service import official_benchmark_service

router = APIRouter(prefix="/official-pricing", tags=["Official Pricing"])


@router.get("/list", response_model=Dict[str, Any])
async def get_official_prices(
    provider: Optional[str] = Query(None, description="按厂商筛选，如 openai, deepseek 等"),
    series: Optional[str] = Query(None, description="按模型系列筛选，如 gpt-5.6, claude-3-5 等"),
    search: Optional[str] = Query(None, description="模型名称或备注关键字搜索"),
    billing_mode: Optional[str] = Query(None, description="计费模式筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取官方价格当前生效全量列表（支持多维筛选、汇率自动折算、上期价格自动对比与涨跌计算）"""
    rate = exchange_rate_service.current_rate
    if not rate or rate <= 0:
        rate = 7.30

    query = select(OfficialModelPrice).where(
        OfficialModelPrice.is_active == True,
        OfficialModelPrice.is_current == True
    )

    if provider and isinstance(provider, str):
        query = query.where(OfficialModelPrice.provider == provider)
    if series and isinstance(series, str):
        query = query.where(OfficialModelPrice.series == series)
    if billing_mode and isinstance(billing_mode, str):
        query = query.where(OfficialModelPrice.billing_mode == billing_mode)
    if search and isinstance(search, str) and search.strip():
        kw = f"%{search.strip()}%"
        query = query.where(
            or_(
                OfficialModelPrice.model_name.ilike(kw),
                OfficialModelPrice.remarks.ilike(kw),
                OfficialModelPrice.custom_notes.ilike(kw),
                OfficialModelPrice.user_tags.ilike(kw),
                OfficialModelPrice.provider_name.ilike(kw)
            )
        )

    query = query.order_by(OfficialModelPrice.provider.asc(), OfficialModelPrice.series.asc(), OfficialModelPrice.model_name.asc())
    result = await db.execute(query)
    records = result.scalars().all()

    # 预查询所有模型在历史快照中的上一次有效价格 (is_current == False)
    prev_subq = (
        select(
            OfficialModelPrice.provider,
            OfficialModelPrice.model_name,
            OfficialModelPrice.input_price,
            OfficialModelPrice.output_price,
            OfficialModelPrice.cache_read_price,
            OfficialModelPrice.cache_write_price,
            OfficialModelPrice.price_date,
            OfficialModelPrice.snapshot_id,
            func.row_number().over(
                partition_by=[OfficialModelPrice.provider, OfficialModelPrice.model_name],
                order_by=OfficialModelPrice.id.desc()
            ).label("rn")
        )
        .where(
            OfficialModelPrice.is_current == False,
            OfficialModelPrice.is_active == True
        )
        .subquery()
    )
    prev_stmt = select(prev_subq).where(prev_subq.c.rn == 1)
    prev_res = await db.execute(prev_stmt)
    prev_map = {
        (row.provider, row.model_name): row
        for row in prev_res.all()
    }

    # 提取唯一的厂商列表与系列列表供前端筛选框使用
    providers_res = await db.execute(
        select(OfficialModelPrice.provider, OfficialModelPrice.provider_name)
        .where(OfficialModelPrice.is_active == True, OfficialModelPrice.is_current == True)
        .distinct()
    )
    providers_list = [{"code": r[0], "name": r[1]} for r in providers_res.all()]

    series_res = await db.execute(
        select(OfficialModelPrice.series, OfficialModelPrice.provider)
        .where(OfficialModelPrice.is_active == True, OfficialModelPrice.is_current == True)
        .distinct()
    )
    series_list = [{"series": r[0], "provider": r[1]} for r in series_res.all() if r[0]]

    # 封装并计算双币种与上期价格对比
    items = []
    for m in records:
        item_dict = {
            "id": m.id,
            "provider": m.provider,
            "provider_name": m.provider_name,
            "series": m.series or "other",
            "model_name": m.model_name,
            "raw_model_id": m.raw_model_id or "",
            "billing_mode": m.billing_mode or "Standard",
            "tier_range": m.tier_range or "无阶梯",
            "currency": m.currency,
            "input_price": m.input_price,
            "output_price": m.output_price,
            "cache_read_price": m.cache_read_price,
            "cache_write_price": m.cache_write_price,
            "remarks": m.remarks or "",
            "custom_notes": m.custom_notes or "",
            "user_tags": m.user_tags or "",
            "price_date": m.price_date or "",
            "source_page_url": m.source_page_url or "",
            "source_anchor": m.source_anchor or "",
            "snapshot_id": m.snapshot_id,
            "is_current": m.is_current,
            "is_active": m.is_active,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }

        # 计算上期对比数据
        prev = prev_map.get((m.provider, m.model_name))
        if prev:
            prev_in = float(prev.input_price or 0.0)
            prev_out = float(prev.output_price or 0.0)
            diff_in = round(m.input_price - prev_in, 6)
            diff_out = round(m.output_price - prev_out, 6)
            diff_in_pct = round((diff_in / prev_in) * 100, 2) if prev_in > 0 else (100.0 if diff_in > 0 else 0.0)
            diff_out_pct = round((diff_out / prev_out) * 100, 2) if prev_out > 0 else (100.0 if diff_out > 0 else 0.0)

            item_dict["previous_input_price"] = prev_in
            item_dict["previous_output_price"] = prev_out
            item_dict["previous_cache_read_price"] = float(prev.cache_read_price or 0.0)
            item_dict["previous_cache_write_price"] = float(prev.cache_write_price or 0.0)
            item_dict["price_change_input"] = diff_in
            item_dict["price_change_output"] = diff_out
            item_dict["price_change_input_pct"] = diff_in_pct
            item_dict["price_change_output_pct"] = diff_out_pct
            item_dict["previous_snapshot_id"] = prev.snapshot_id
            item_dict["previous_price_date"] = prev.price_date or ""
            item_dict["is_new_model"] = False
        else:
            item_dict["previous_input_price"] = None
            item_dict["previous_output_price"] = None
            item_dict["previous_cache_read_price"] = None
            item_dict["previous_cache_write_price"] = None
            item_dict["price_change_input"] = 0.0
            item_dict["price_change_output"] = 0.0
            item_dict["price_change_input_pct"] = 0.0
            item_dict["price_change_output_pct"] = 0.0
            item_dict["previous_snapshot_id"] = None
            item_dict["previous_price_date"] = ""
            item_dict["is_new_model"] = True

        # 汇率换算逻辑
        if m.currency == "USD":
            item_dict["converted_input_usd"] = m.input_price
            item_dict["converted_output_usd"] = m.output_price
            item_dict["converted_cache_read_usd"] = m.cache_read_price
            item_dict["converted_cache_write_usd"] = m.cache_write_price
            item_dict["converted_input_cny"] = round(m.input_price * rate, 4)
            item_dict["converted_output_cny"] = round(m.output_price * rate, 4)
            item_dict["converted_cache_read_cny"] = round(m.cache_read_price * rate, 4)
            item_dict["converted_cache_write_cny"] = round(m.cache_write_price * rate, 4)
            # 上期折合
            if item_dict["previous_input_price"] is not None:
                item_dict["converted_prev_input_usd"] = item_dict["previous_input_price"]
                item_dict["converted_prev_output_usd"] = item_dict["previous_output_price"]
                item_dict["converted_prev_input_cny"] = round(item_dict["previous_input_price"] * rate, 4)
                item_dict["converted_prev_output_cny"] = round(item_dict["previous_output_price"] * rate, 4)
            else:
                item_dict["converted_prev_input_usd"] = None
                item_dict["converted_prev_output_usd"] = None
                item_dict["converted_prev_input_cny"] = None
                item_dict["converted_prev_output_cny"] = None
        else:
            item_dict["converted_input_cny"] = m.input_price
            item_dict["converted_output_cny"] = m.output_price
            item_dict["converted_cache_read_cny"] = m.cache_read_price
            item_dict["converted_cache_write_cny"] = m.cache_write_price
            item_dict["converted_input_usd"] = round(m.input_price / rate, 4) if rate > 0 else 0.0
            item_dict["converted_output_usd"] = round(m.output_price / rate, 4) if rate > 0 else 0.0
            item_dict["converted_cache_read_usd"] = round(m.cache_read_price / rate, 4) if rate > 0 else 0.0
            item_dict["converted_cache_write_usd"] = round(m.cache_write_price / rate, 4) if rate > 0 else 0.0
            # 上期折合
            if item_dict["previous_input_price"] is not None:
                item_dict["converted_prev_input_cny"] = item_dict["previous_input_price"]
                item_dict["converted_prev_output_cny"] = item_dict["previous_output_price"]
                item_dict["converted_prev_input_usd"] = round(item_dict["previous_input_price"] / rate, 4) if rate > 0 else 0.0
                item_dict["converted_prev_output_usd"] = round(item_dict["previous_output_price"] / rate, 4) if rate > 0 else 0.0
            else:
                item_dict["converted_prev_input_usd"] = None
                item_dict["converted_prev_output_usd"] = None
                item_dict["converted_prev_input_cny"] = None
                item_dict["converted_prev_output_cny"] = None

        items.append(item_dict)

    return {
        "status": "success",
        "total": len(items),
        "models": items,
        "providers": providers_list,
        "series": series_list,
        "usd_to_cny_rate": rate,
    }


@router.patch("/model/{model_id}/notes")
async def update_model_notes(
    model_id: int,
    payload: OfficialModelPriceUpdateNotes,
    db: AsyncSession = Depends(get_db)
):
    """更新用户自定义备注与标签"""
    stmt = select(OfficialModelPrice).where(OfficialModelPrice.id == model_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="未找到该模型记录")

    if payload.custom_notes is not None:
        model.custom_notes = payload.custom_notes.strip()
    if payload.user_tags is not None:
        model.user_tags = payload.user_tags.strip()

    await db.commit()
    await db.refresh(model)
    return {
        "status": "success",
        "id": model.id,
        "custom_notes": model.custom_notes,
        "user_tags": model.user_tags,
    }


@router.post("/scrape", response_model=OfficialScrapeResponse)
async def trigger_scrape(
    payload: OfficialScrapeRequest,
):
    """触发抓取（支持指定厂商或全部厂商，支持传入自定义代理）"""
    import time
    start_t = time.time()
    target = payload.provider

    if not target or target == "all":
        count, keys, err = await official_scraper_service.scrape_all(proxy=payload.proxy)
        duration = round((time.time() - start_t) * 1000, 2)
        return OfficialScrapeResponse(
            status="error" if err and count == 0 else "success",
            total_models=count,
            providers_scraped=keys,
            duration_ms=duration,
            error_message=err or ""
        )
    else:
        count, err = await official_scraper_service.scrape_target(target, proxy=payload.proxy)
        duration = round((time.time() - start_t) * 1000, 2)
        return OfficialScrapeResponse(
            status="error" if err else "success",
            total_models=count,
            providers_scraped=[target] if not err else [],
            duration_ms=duration,
            error_message=err or ""
        )


@router.get("/snapshots")
async def list_snapshots(db: AsyncSession = Depends(get_db)):
    """获取所有已留存的官网快照（标注当前生效版本）"""
    # 查找当前生效价格对应的 snapshot_id 集合
    curr_snap_ids_res = await db.execute(
        select(OfficialModelPrice.snapshot_id)
        .where(OfficialModelPrice.is_current == True, OfficialModelPrice.snapshot_id.is_not(None))
        .distinct()
    )
    current_snap_ids = set(r[0] for r in curr_snap_ids_res.all())

    query = select(OfficialSnapshot).order_by(OfficialSnapshot.captured_at.desc())
    res = await db.execute(query)
    snapshots = res.scalars().all()
    return [
        {
            "id": s.id,
            "provider": s.provider,
            "source_url": s.source_url,
            "page_title": s.page_title,
            "local_file_path": s.local_file_path,
            "file_size_bytes": s.file_size_bytes,
            "models_count": s.models_count,
            "is_current": s.id in current_snap_ids,
            "captured_at": s.captured_at.strftime("%Y-%m-%d %H:%M:%S") if s.captured_at else "",
        }
        for s in snapshots
    ]


@router.get("/snapshots/grouped")
async def list_snapshots_grouped(db: AsyncSession = Depends(get_db)):
    """按日期（YYYY-MM-DD）聚合快照列表（标注当前生效版本、收录厂商、模型总数）"""
    # 查找当前生效价格对应的 snapshot_id 集合
    curr_snap_ids_res = await db.execute(
        select(OfficialModelPrice.snapshot_id)
        .where(OfficialModelPrice.is_current == True, OfficialModelPrice.snapshot_id.is_not(None))
        .distinct()
    )
    current_snap_ids = set(r[0] for r in curr_snap_ids_res.all())

    # 查询所有快照，按 captured_at 降序
    query = select(OfficialSnapshot).order_by(OfficialSnapshot.captured_at.desc(), OfficialSnapshot.id.desc())
    res = await db.execute(query)
    snapshots = res.scalars().all()

    # 统计每个 snapshot 实际关联的模型数
    model_count_res = await db.execute(
        select(OfficialModelPrice.snapshot_id, func.count(OfficialModelPrice.id))
        .where(OfficialModelPrice.snapshot_id.is_not(None))
        .group_by(OfficialModelPrice.snapshot_id)
    )
    model_count_map = {r[0]: r[1] for r in model_count_res.all()}

    from backend.app.services.official_scraper_service import OFFICIAL_TARGETS
    provider_name_map = {
        p: conf.get("name", p) for p, conf in OFFICIAL_TARGETS.items()
    }

    # 按 YYYY-MM-DD 分组，并对同一日期内的同一厂商进行唯一性去重（优先保留生效中或最新快照）
    date_groups = OrderedDict()
    date_provider_map = OrderedDict()

    for s in snapshots:
        d_str = s.captured_at.strftime("%Y-%m-%d") if s.captured_at else "未知日期"
        if d_str not in date_groups:
            date_groups[d_str] = {
                "snapshot_date": d_str,
                "is_current": False,
                "total_providers": 0,
                "total_models": 0,
                "providers": []
            }

        is_curr = s.id in current_snap_ids
        if is_curr:
            date_groups[d_str]["is_current"] = True

        cnt = model_count_map.get(s.id, s.models_count or 0)
        p_item = {
            "snapshot_id": s.id,
            "provider": s.provider,
            "provider_name": provider_name_map.get(s.provider, s.provider),
            "source_url": s.source_url,
            "page_title": s.page_title,
            "local_file_path": s.local_file_path,
            "file_size_bytes": s.file_size_bytes,
            "models_count": cnt,
            "is_current": is_curr,
            "captured_at": s.captured_at.strftime("%Y-%m-%d %H:%M:%S") if s.captured_at else "",
        }

        key = (d_str, s.provider)
        if key not in date_provider_map:
            date_provider_map[key] = p_item
        else:
            # 若已存在同日期同厂商快照：若当前项是生效中而原有项不是，则替换为生效项
            if is_curr and not date_provider_map[key]["is_current"]:
                date_provider_map[key] = p_item

    # 将去重后的唯一厂商快照聚合装配到各日期批次中
    for (d_str, provider), p_item in date_provider_map.items():
        date_groups[d_str]["providers"].append(p_item)
        date_groups[d_str]["total_models"] += p_item["models_count"]

    result = []
    for g in date_groups.values():
        g["total_providers"] = len(g["providers"])
        result.append(g)

    return result


@router.get("/snapshots/{snapshot_id}/models")
async def get_snapshot_models(snapshot_id: int, db: AsyncSession = Depends(get_db)):
    """获取指定快照收录的所有模型明细列表"""
    snap_res = await db.execute(select(OfficialSnapshot).where(OfficialSnapshot.id == snapshot_id))
    snapshot = snap_res.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="未找到该快照")

    query = (
        select(OfficialModelPrice)
        .where(OfficialModelPrice.snapshot_id == snapshot_id)
        .order_by(OfficialModelPrice.is_current.desc(), OfficialModelPrice.id.desc())
    )
    res = await db.execute(query)
    raw_models = res.scalars().all()

    # 内存去重保护：针对同一个快照，确保 (model_name, billing_mode, tier_range) 唯一，优先保留 is_current=True 的记录
    seen_keys = set()
    models = []
    for m in raw_models:
        key = (m.model_name, m.billing_mode, m.tier_range)
        if key not in seen_keys:
            seen_keys.add(key)
            models.append(m)

    # 恢复系列与模型名正序展示
    models.sort(key=lambda m: (m.series or "other", m.model_name))

    from backend.app.services.official_scraper_service import OFFICIAL_TARGETS
    p_name = OFFICIAL_TARGETS.get(snapshot.provider, {}).get("name", snapshot.provider)

    items = []
    for m in models:
        items.append({
            "id": m.id,
            "provider": m.provider,
            "provider_name": p_name,
            "series": m.series or "other",
            "model_name": m.model_name,
            "raw_model_id": m.raw_model_id or "",
            "billing_mode": m.billing_mode or "Standard",
            "tier_range": m.tier_range or "无阶梯",
            "currency": m.currency,
            "input_price": m.input_price,
            "output_price": m.output_price,
            "cache_read_price": m.cache_read_price,
            "cache_write_price": m.cache_write_price,
            "remarks": m.remarks or "",
            "is_current": m.is_current,
        })

    return {
        "snapshot_id": snapshot.id,
        "provider": snapshot.provider,
        "provider_name": p_name,
        "captured_at": snapshot.captured_at.strftime("%Y-%m-%d %H:%M:%S") if snapshot.captured_at else "",
        "page_title": snapshot.page_title,
        "source_url": snapshot.source_url,
        "total": len(items),
        "models": items
    }


@router.get("/model/history")
async def get_model_history(
    provider: str = Query(..., description="厂商代码，如 openai, deepseek 等"),
    model_name: str = Query(..., description="模型名称"),
    db: AsyncSession = Depends(get_db)
):
    """获取指定模型在各历史快照中的价格变化轨迹序列（用于时序走势大盘与版本对比）"""
    rate = exchange_rate_service.current_rate
    if not rate or rate <= 0:
        rate = 7.30

    query = (
        select(OfficialModelPrice, OfficialSnapshot)
        .outerjoin(OfficialSnapshot, OfficialModelPrice.snapshot_id == OfficialSnapshot.id)
        .where(
            OfficialModelPrice.provider == provider,
            OfficialModelPrice.model_name == model_name,
            OfficialModelPrice.is_active == True
        )
        .order_by(OfficialModelPrice.created_at.asc(), OfficialModelPrice.id.asc())
    )
    result = await db.execute(query)
    rows = result.all()

    points = []
    prev_in = None
    prev_out = None

    for price_obj, snap_obj in rows:
        in_p = price_obj.input_price
        out_p = price_obj.output_price
        cache_r = price_obj.cache_read_price
        cache_w = price_obj.cache_write_price

        diff_in = round(in_p - prev_in, 6) if prev_in is not None else 0.0
        diff_out = round(out_p - prev_out, 6) if prev_out is not None else 0.0
        diff_in_pct = round((diff_in / prev_in) * 100, 2) if (prev_in is not None and prev_in > 0) else 0.0
        diff_out_pct = round((diff_out / prev_out) * 100, 2) if (prev_out is not None and prev_out > 0) else 0.0

        if price_obj.currency == "USD":
            in_cny = round(in_p * rate, 4)
            out_cny = round(out_p * rate, 4)
            in_usd = in_p
            out_usd = out_p
        else:
            in_cny = in_p
            out_cny = out_p
            in_usd = round(in_p / rate, 4) if rate > 0 else 0.0
            out_usd = round(out_p / rate, 4) if rate > 0 else 0.0

        captured_time = ""
        if snap_obj and snap_obj.captured_at:
            captured_time = snap_obj.captured_at.strftime("%Y-%m-%d %H:%M:%S")
        elif price_obj.created_at:
            captured_time = price_obj.created_at.strftime("%Y-%m-%d %H:%M:%S")

        points.append({
            "id": price_obj.id,
            "snapshot_id": price_obj.snapshot_id,
            "captured_at": captured_time,
            "price_date": price_obj.price_date or "",
            "is_current": price_obj.is_current,
            "currency": price_obj.currency,
            "input_price": in_p,
            "output_price": out_p,
            "cache_read_price": cache_r,
            "cache_write_price": cache_w,
            "converted_input_cny": in_cny,
            "converted_output_cny": out_cny,
            "converted_input_usd": in_usd,
            "converted_output_usd": out_usd,
            "diff_input": diff_in,
            "diff_output": diff_out,
            "diff_input_pct": diff_in_pct,
            "diff_output_pct": diff_out_pct,
            "billing_mode": price_obj.billing_mode,
            "tier_range": price_obj.tier_range,
            "remarks": price_obj.remarks,
        })
        prev_in = in_p
        prev_out = out_p

    return {
        "status": "success",
        "provider": provider,
        "model_name": model_name,
        "total_points": len(points),
        "history": points,
        "rate": rate,
    }


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除某次快照版本；若删除的是当前最新生效快照，自动将该厂商上一个有效快照回滚为当前生效版本"""
    query = select(OfficialSnapshot).where(OfficialSnapshot.id == snapshot_id)
    res = await db.execute(query)
    snapshot = res.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="未找到该快照")

    provider = snapshot.provider
    local_file_path = snapshot.local_file_path

    # 检查该快照下是否存在当前生效的价格 (is_current == True)
    curr_check = await db.execute(
        select(func.count(OfficialModelPrice.id))
        .where(OfficialModelPrice.snapshot_id == snapshot_id, OfficialModelPrice.is_current == True)
    )
    is_active_version = (curr_check.scalar() or 0) > 0

    rolled_back_to = None

    if is_active_version:
        # 寻找该厂商的上一个最新快照版本 (按 captured_at 倒序排列，排除当前快照)
        prev_snap_stmt = (
            select(OfficialSnapshot)
            .where(OfficialSnapshot.provider == provider, OfficialSnapshot.id != snapshot_id)
            .order_by(OfficialSnapshot.captured_at.desc(), OfficialSnapshot.id.desc())
            .limit(1)
        )
        prev_snap = (await db.execute(prev_snap_stmt)).scalar_one_or_none()
        if prev_snap:
            rolled_back_to = prev_snap.id
            # 将该上期快照的所有价格记录设为当前生效
            await db.execute(
                update(OfficialModelPrice)
                .where(OfficialModelPrice.snapshot_id == prev_snap.id)
                .values(is_current=True)
            )

    # 删除该快照下的所有价格记录
    await db.execute(delete(OfficialModelPrice).where(OfficialModelPrice.snapshot_id == snapshot_id))

    # 删除快照元数据记录
    await db.delete(snapshot)
    await db.commit()

    # 尝试物理删除本地磁盘 HTML 快照文件 (保护基础样本 sample_*.html 不被物理删除)
    cleaned_file = False
    try:
        if local_file_path and not os.path.basename(local_file_path).startswith("sample_"):
            raw_p = Path(local_file_path)
            cand_paths = [
                raw_p,
                DATA_DIR / "official_snapshots" / raw_p.name,
                DATA_DIR / raw_p,
                Path(os.getcwd()) / local_file_path,
            ]
            for p in cand_paths:
                if p.exists() and p.is_file():
                    os.remove(str(p))
                    cleaned_file = True
                    break
    except Exception:
        pass

    return {
        "status": "success",
        "message": f"快照 #{snapshot_id} 已成功删除",
        "provider": provider,
        "is_active_version": is_active_version,
        "rolled_back_to_snapshot_id": rolled_back_to,
        "file_deleted": cleaned_file
    }


@router.delete("/snapshots/by-date/{snapshot_date}")
async def delete_snapshots_by_date(snapshot_date: str, db: AsyncSession = Depends(get_db)):
    """一键删除指定日期的整批快照；若包含当前生效快照，自动回滚各厂商至上一个历史有效快照"""
    query = select(OfficialSnapshot).order_by(OfficialSnapshot.id.asc())
    res = await db.execute(query)
    all_snaps = res.scalars().all()

    target_snaps = [s for s in all_snaps if s.captured_at and s.captured_at.strftime("%Y-%m-%d") == snapshot_date]
    if not target_snaps:
        raise HTTPException(status_code=404, detail=f"未找到日期为 {snapshot_date} 的快照记录")

    target_ids = [s.id for s in target_snaps]

    # 检查其中是否有正在生效的快照
    curr_snap_ids_res = await db.execute(
        select(OfficialModelPrice.snapshot_id)
        .where(OfficialModelPrice.snapshot_id.in_(target_ids), OfficialModelPrice.is_current == True)
        .distinct()
    )
    active_in_batch = set(r[0] for r in curr_snap_ids_res.all())

    rolled_back_providers = {}
    if active_in_batch:
        # 对每一个受影响的厂商，寻找其在该日期之前的最近有效快照
        for snap in target_snaps:
            if snap.id in active_in_batch:
                prev_stmt = (
                    select(OfficialSnapshot)
                    .where(
                        OfficialSnapshot.provider == snap.provider,
                        OfficialSnapshot.id.notin_(target_ids),
                        OfficialSnapshot.captured_at < snap.captured_at
                    )
                    .order_by(OfficialSnapshot.captured_at.desc(), OfficialSnapshot.id.desc())
                    .limit(1)
                )
                prev_snap = (await db.execute(prev_stmt)).scalar_one_or_none()
                if prev_snap:
                    # 回滚生效
                    await db.execute(
                        update(OfficialModelPrice)
                        .where(OfficialModelPrice.snapshot_id == prev_snap.id)
                        .values(is_current=True)
                    )
                    rolled_back_providers[snap.provider] = prev_snap.id

    # 删除这些快照下的所有价格记录
    await db.execute(delete(OfficialModelPrice).where(OfficialModelPrice.snapshot_id.in_(target_ids)))

    # 物理删除本地磁盘 HTML 快照文件
    deleted_files = 0
    for s in target_snaps:
        if s.local_file_path and not os.path.basename(s.local_file_path).startswith("sample_"):
            raw_p = Path(s.local_file_path)
            cand_paths = [
                raw_p,
                DATA_DIR / "official_snapshots" / raw_p.name,
                DATA_DIR / raw_p,
                Path(os.getcwd()) / s.local_file_path,
            ]
            for p in cand_paths:
                if p.exists() and p.is_file():
                    try:
                        os.remove(str(p))
                        deleted_files += 1
                    except Exception:
                        pass
                    break

    # 删除快照元数据记录
    await db.execute(delete(OfficialSnapshot).where(OfficialSnapshot.id.in_(target_ids)))
    await db.commit()

    return {
        "status": "success",
        "message": f"成功删除日期 {snapshot_date} 下的 {len(target_snaps)} 份快照",
        "snapshot_date": snapshot_date,
        "deleted_count": len(target_snaps),
        "deleted_files_count": deleted_files,
        "rolled_back_providers": rolled_back_providers
    }


@router.get("/snapshots/{snapshot_id}/view")
async def view_snapshot_html(
    snapshot_id: int,
    highlight: Optional[str] = Query(None, description="需要高亮并自动滚动的目标模型关键字"),
    db: AsyncSession = Depends(get_db)
):
    """获取快照 HTML 内容供内置抽屉渲染对账（注入 Base 域、移除冲突 Script、自动平滑滚动高亮目标行）"""
    from bs4 import BeautifulSoup
    query = select(OfficialSnapshot).where(OfficialSnapshot.id == snapshot_id)
    res = await db.execute(query)
    snapshot = res.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="未找到该快照")

    import sys
    raw_p = Path(snapshot.local_file_path)
    if raw_p.is_absolute() and raw_p.exists():
        abs_path = str(raw_p)
    elif (DATA_DIR / "official_snapshots" / raw_p.name).exists():
        abs_path = str(DATA_DIR / "official_snapshots" / raw_p.name)
    elif (DATA_DIR / raw_p).exists():
        abs_path = str(DATA_DIR / raw_p)
    elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') and (Path(sys._MEIPASS) / "data" / "official_snapshots" / raw_p.name).exists():
        abs_path = str(Path(sys._MEIPASS) / "data" / "official_snapshots" / raw_p.name)
    elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS') and (Path(sys._MEIPASS) / snapshot.local_file_path).exists():
        abs_path = str(Path(sys._MEIPASS) / snapshot.local_file_path)
    elif (Path(os.getcwd()) / snapshot.local_file_path).exists():
        abs_path = str(Path(os.getcwd()) / snapshot.local_file_path)
    else:
        abs_path = str(DATA_DIR / "official_snapshots" / raw_p.name)

    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail=f"快照文件在本地磁盘不存在: {abs_path}")

    with open(abs_path, "r", encoding="utf-8") as f:
        raw_html = f.read()

    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. 移除所有可能会在本地环境中报错导致整页白屏的 <script> 标签
    for s in soup.find_all("script"):
        s.decompose()

    # 1.1 彻底移除所有遮挡页面内容的营销弹窗、公告模态框及全屏遮罩蒙层 (如 Ant Design、Element UI 等)
    modal_selectors = [
        ".ant-modal-root",
        ".ant-modal-mask",
        ".ant-modal-wrap",
        ".ant-modal",
        ".el-overlay",
        ".el-overlay-dialog",
        ".el-dialog__wrapper",
        ".v-modal",
        ".modal-backdrop",
        "[class*='Announcement_announcementModal']",
        "[class*='announcementModal']",
        "[class*='announcement-modal']",
        "[class*='NoticeModal']",
        "[class*='notice-modal']",
        "[class*='promotion-modal']",
        "[class*='marketing-modal']",
        "[id*='announcement-modal']",
        "[id*='notice-modal']",
    ]
    for sel in modal_selectors:
        for el in soup.select(sel):
            el.decompose()

    # 兜底清理无任何表格或价格数据的纯弹窗 dialog (防止误删有表格的模型对比弹出窗)
    for dialog in soup.find_all(attrs={"role": "dialog"}):
        if not dialog.find("table") and not dialog.find("tbody"):
            dialog.decompose()
    for modal in soup.find_all(attrs={"aria-modal": "true"}):
        if not modal.find("table") and not modal.find("tbody"):
            modal.decompose()

    # 2. 注入 <base href="{snapshot.source_url}"> 使得远程 CSS/图片/字体正常加载
    if soup.head:
        base_tag = soup.new_tag("base", href=snapshot.source_url)
        soup.head.insert(0, base_tag)

    # 3. 注入高亮样式与平滑滚动定位脚本
    import json
    target_kw = (highlight or "").strip()
    highlight_code = """
<style>
  @keyframes wpdRowPulse {
    0% {
      box-shadow: 0 0 0 0 rgba(0, 113, 227, 0.7);
      background-color: rgba(254, 240, 138, 0.3) !important;
    }
    50% {
      box-shadow: 0 0 0 6px rgba(0, 113, 227, 0.35);
      background-color: rgba(254, 240, 138, 0.65) !important;
    }
    100% {
      box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.85);
      background-color: rgba(254, 240, 138, 0.4) !important;
    }
  }
  @keyframes wpdCellPulse {
    0% {
      box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.9), inset 0 0 10px rgba(245, 158, 11, 0.35);
      background-color: rgba(254, 240, 138, 0.95) !important;
      transform: scale(1);
    }
    50% {
      box-shadow: 0 0 0 7px rgba(245, 158, 11, 0.45), inset 0 0 16px rgba(245, 158, 11, 0.6);
      background-color: rgba(253, 224, 71, 1) !important;
      transform: scale(1.05);
    }
    100% {
      box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.9), inset 0 0 10px rgba(245, 158, 11, 0.35);
      background-color: rgba(254, 240, 138, 0.95) !important;
      transform: scale(1);
    }
  }
  .wpd-highlight-row {
    animation: wpdRowPulse 1.6s ease-in-out infinite alternate !important;
    border-radius: 4px !important;
    position: relative !important;
    z-index: 98 !important;
    outline: 2px solid #0071E3 !important;
  }
  .wpd-highlight-cell {
    animation: wpdCellPulse 1.5s ease-in-out infinite alternate !important;
    outline: 2px solid #D97706 !important;
    border-radius: 4px !important;
    font-weight: 800 !important;
    color: #92400E !important;
    position: relative !important;
    z-index: 100 !important;
  }
  .wpd-top-indicator {
    position: fixed;
    top: 14px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999999;
    background: rgba(29, 29, 31, 0.92);
    color: #FFFFFF;
    padding: 8px 20px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.28);
    display: flex;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(255,255,255,0.25);
    cursor: pointer;
    user-select: none;
    transition: all 0.2s ease;
  }
  .wpd-top-indicator:hover {
    transform: translateX(-50%) scale(1.04);
    background: #0071E3;
  }
  /* 强力屏蔽可能遮挡定价核验的营销弹窗、公告模态框及背景遮罩蒙层 */
  .ant-modal-root,
  .ant-modal-mask,
  .ant-modal-wrap,
  .ant-modal,
  .el-overlay,
  .el-overlay-dialog,
  .el-dialog__wrapper,
  .v-modal,
  .modal-backdrop,
  [class*="announcementModal"],
  [class*="Announcement_announcementModal"],
  [class*="NoticeModal"],
  [class*="notice-modal"],
  [class*="promotion-modal"],
  [class*="marketing-modal"],
  div[role="dialog"]:not(:has(table)),
  div[aria-modal="true"]:not(:has(table)) {
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    z-index: -9999 !important;
  }
</style>
<script>
  (function() {
    var kw = __TARGET_KW__;
    function locateAndHighlight() {
      if (!kw) return;

      function norm(s) {
        return (s || '').toLowerCase().replace(/[\\s\\n\\r\\t]+/g, ' ').replace(/[，。；;,;]/g, ' ').trim();
      }

      var normKw = norm(kw);
      var cleanKw = norm(kw.split(' [')[0].split(' (')[0]);
      var coreName = cleanKw.split(' ')[0].trim();
      var isPeak = kw.indexOf('高峰') !== -1;
      var isIdle = kw.indexOf('闲时') !== -1 || kw.indexOf('空闲') !== -1;
      var isBatch = kw.indexOf('Batch') !== -1;
      var isFlex = kw.indexOf('Flex') !== -1;
      var isFast = kw.indexOf('Fast') !== -1 || kw.indexOf('Priority') !== -1;
      var isLong = kw.indexOf('272k+') !== -1 || kw.indexOf('Long') !== -1 || kw.indexOf('128k+') !== -1;
      var targetScrollEl = null;

      // ================= 步骤 0: 智能 Tab 选项卡模式切换与静态页面点击水合 =================
      var isPrioMode = isFast || kw.indexOf('Priority') !== -1 || kw.indexOf('优先') !== -1;
      var targetMode = isBatch ? 'Batch' : (isFlex ? 'Flex' : (isPrioMode ? 'Priority' : 'Standard'));
      var targetModeKeywords = isBatch
        ? ['batch', '批处理']
        : (isFlex ? ['flex', '弹性'] : (isPrioMode ? ['优先', 'priority', 'fast'] : ['标准', 'standard']));

      // 0.1 支持标准 WAI-ARIA [role="tab"] 与 [role="tabpanel"] (如 MiniMax, Tailwind/Radix UI 页面)
      var ariaTabs = document.querySelectorAll('[role="tab"]');
      var ariaPanels = document.querySelectorAll('[role="tabpanel"]');

      if (ariaTabs.length > 0) {
        function activateAriaTab(tabEl) {
          var targetPanelId = tabEl.getAttribute('aria-controls');
          var targetPanel = targetPanelId ? document.getElementById(targetPanelId) : null;

          if (!targetPanel) {
            var tabIdx = Array.prototype.indexOf.call(ariaTabs, tabEl);
            if (tabIdx !== -1 && ariaPanels[tabIdx]) targetPanel = ariaPanels[tabIdx];
          }

          for (var at = 0; at < ariaTabs.length; at++) {
            var t = ariaTabs[at];
            if (t === tabEl) {
              t.setAttribute('aria-selected', 'true');
              t.style.borderBottomColor = '#0071E3';
              t.style.color = '#0071E3';
              t.style.fontWeight = 'bold';
            } else {
              t.setAttribute('aria-selected', 'false');
              t.style.borderBottomColor = 'transparent';
              t.style.color = '';
              t.style.fontWeight = '';
            }
          }

          for (var ap = 0; ap < ariaPanels.length; ap++) {
            var p = ariaPanels[ap];
            if (p === targetPanel) {
              p.removeAttribute('hidden');
              p.classList.remove('hidden');
              p.style.display = 'block';
            } else {
              p.setAttribute('hidden', 'true');
              p.classList.add('hidden');
              p.style.display = 'none';
            }
          }
        }

        var matchedTab = null;
        for (var at = 0; at < ariaTabs.length; at++) {
          var tText = (ariaTabs[at].innerText || ariaTabs[at].textContent || '').trim().toLowerCase();
          var isTabMatch = targetModeKeywords.some(function(kwItem) { return tText.indexOf(kwItem.toLowerCase()) !== -1; });
          if (isTabMatch) {
            matchedTab = ariaTabs[at];
            break;
          }
        }
        if (!matchedTab && ariaTabs.length > 0) {
          matchedTab = ariaTabs[0];
        }
        if (matchedTab) {
          activateAriaTab(matchedTab);
        }

        for (var at = 0; at < ariaTabs.length; at++) {
          (function(tab) {
            tab.style.cursor = 'pointer';
            tab.onclick = function(e) {
              e.preventDefault();
              activateAriaTab(tab);
            };
          })(ariaTabs[at]);
        }
      }

      // 0.2 原有 Astro / OpenAI Content Switcher 兼容支持
      var targetTabIndex = isBatch ? 1 : (isFlex ? 2 : (isPrioMode ? 3 : 0));
      var switchers = document.querySelectorAll('.content-switcher-selector, [role="tablist"]');
      var containers = document.querySelectorAll('.content-switcher-panes');

      // 切换 Pane 显示隐藏
      for (var c = 0; c < containers.length; c++) {
        var panes = containers[c].children;
        for (var p = 0; p < panes.length; p++) {
          if (p === targetTabIndex) {
            panes[p].removeAttribute('hidden');
            panes[p].style.display = 'block';
          } else {
            panes[p].setAttribute('hidden', 'true');
            panes[p].style.display = 'none';
          }
        }
      }

      // 切换 Tab 按钮高亮与状态
      for (var s = 0; s < switchers.length; s++) {
        var btns = switchers[s].querySelectorAll('button, a, [role="tab"]');
        for (var b = 0; b < btns.length; b++) {
          var btnText = (btns[b].innerText || btns[b].textContent || '').trim();
          if (btnText === targetMode || (isPrioMode && (btnText === 'Fast mode' || btnText === 'Priority' || btnText.indexOf('优先') !== -1))) {
            btns[b].style.backgroundColor = '#0071E3';
            btns[b].style.color = '#FFFFFF';
            btns[b].setAttribute('aria-selected', 'true');
          } else {
            btns[b].style.backgroundColor = '';
            btns[b].style.color = '';
            btns[b].setAttribute('aria-selected', 'false');
          }

          // 绑定用户手动点击切换事件
          (function(btnIdx, bEl) {
            bEl.onclick = function() {
              for (var c2 = 0; c2 < containers.length; c2++) {
                var pList = containers[c2].children;
                for (var p2 = 0; p2 < pList.length; p2++) {
                  if (p2 === btnIdx) {
                    pList[p2].removeAttribute('hidden');
                    pList[p2].style.display = 'block';
                  } else {
                    pList[p2].setAttribute('hidden', 'true');
                    pList[p2].style.display = 'none';
                  }
                }
              }
              var allSiblings = bEl.parentElement.querySelectorAll('button, a, [role="tab"]');
              for (var sib = 0; sib < allSiblings.length; sib++) {
                allSiblings[sib].style.backgroundColor = '';
                allSiblings[sib].style.color = '';
              }
              bEl.style.backgroundColor = '#0071E3';
              bEl.style.color = '#FFFFFF';
            };
          })(b, btns[b]);
        }
      }
      // ================= 步骤 0.1: Google Devsite Selector 模式切换 (针对 Gemini 模型) =================
      var targetGeminiTab = isBatch ? '批量' : (isFlex ? 'flex' : (isFast ? '优先级' : '标准'));
      var devsiteSelectors = document.querySelectorAll('devsite-selector');
      if (devsiteSelectors.length > 0) {
        for (var ds = 0; ds < devsiteSelectors.length; ds++) {
          var sel = devsiteSelectors[ds];
          var cur = sel;
          var matchSel = false;
          while (cur && cur !== document.body) {
            var prevSib = cur.previousElementSibling;
            while (prevSib) {
              var pText = norm(prevSib.innerText);
              if (pText.indexOf(cleanKw) !== -1 || (coreName.length >= 4 && pText.indexOf(coreName) !== -1)) {
                matchSel = true;
                break;
              }
              prevSib = prevSib.previousElementSibling;
            }
            if (matchSel) break;
            cur = cur.parentElement;
          }

          if (matchSel) {
            var secList = sel.querySelectorAll('section');
            var activeSec = null;
            for (var si = 0; si < secList.length; si++) {
              var sId = (secList[si].id || '').toLowerCase();
              if (sId.indexOf(targetGeminiTab.toLowerCase()) !== -1) {
                secList[si].style.display = 'block';
                secList[si].removeAttribute('hidden');
                activeSec = secList[si];
              } else {
                secList[si].style.display = 'none';
              }
            }

            var dsTabs = sel.querySelectorAll('tab, button, [role="tab"]');
            for (var dt = 0; dt < dsTabs.length; dt++) {
              if (norm(dsTabs[dt].innerText).indexOf(targetGeminiTab.toLowerCase()) !== -1) {
                dsTabs[dt].style.backgroundColor = '#0071E3';
                dsTabs[dt].style.color = '#FFFFFF';
              } else {
                dsTabs[dt].style.backgroundColor = '';
                dsTabs[dt].style.color = '';
              }
            }

            if (activeSec) {
              var tRows = activeSec.querySelectorAll('tr');
              for (var tr = 0; tr < tRows.length; tr++) {
                var rowTxt = norm(tRows[tr].innerText);
                if (rowTxt.indexOf('输入价格') !== -1 || rowTxt.indexOf('输出价格') !== -1) {
                  tRows[tr].classList.add('wpd-highlight-row');
                  var dCells = tRows[tr].querySelectorAll('td');
                  for (var dc = 0; dc < dCells.length; dc++) {
                    var cellT = dCells[dc].innerText;
                    if (/\\d+(?:\\.\\d+)?\\s*(?:美元|元|￥|¥|\\$)/.test(cellT) || /\\$\\s*\\d+/.test(cellT)) {
                      dCells[dc].classList.add('wpd-highlight-cell');
                    }
                  }
                  if (!targetScrollEl) targetScrollEl = tRows[tr];
                }
              }
            }
            break;
          }
        }
      }

      var tables = document.querySelectorAll('table');

      // ================= 场景 1: 列式模型表格定位 (如 DeepSeek) =================
      if (!targetScrollEl) {
        for (var t = 0; t < tables.length; t++) {
        var table = tables[t];
        var rows = table.querySelectorAll('tr');
        if (!rows || rows.length < 2) continue;

        var headerCells = rows[0].querySelectorAll('td, th');
        var modelCol = -1;
        for (var c = 1; c < headerCells.length; c++) {
          if (norm(headerCells[c].innerText).indexOf(coreName) !== -1) {
            modelCol = c;
            break;
          }
        }

        if (modelCol === -1 && rows.length > 1) {
          var h2Cells = rows[1].querySelectorAll('td, th');
          for (var c = 1; c < h2Cells.length; c++) {
            if (norm(h2Cells[c].innerText).indexOf(coreName) !== -1) {
              modelCol = c;
              headerCells = h2Cells;
              break;
            }
          }
        }

        if (modelCol !== -1) {
          var offsetFromEnd = headerCells.length - 1 - modelCol;

          for (var r = 0; r < rows.length; r++) {
            var rText = norm(rows[r].innerText);
            var isTargetPriceRow = false;
            if (isPeak && rText.indexOf('高峰') !== -1) isTargetPriceRow = true;
            else if (isIdle && (rText.indexOf('空闲') !== -1 || rText.indexOf('闲时') !== -1)) isTargetPriceRow = true;

            if (isTargetPriceRow) {
              var cells = rows[r].querySelectorAll('td, th');
              if (cells.length > offsetFromEnd) {
                var targetCell = cells[cells.length - 1 - offsetFromEnd];
                if (targetCell) {
                  rows[r].classList.add('wpd-highlight-row');
                  targetCell.classList.add('wpd-highlight-cell');
                  if (!targetScrollEl || rText.indexOf('未命中') !== -1 || rText.indexOf('输入') !== -1) {
                    targetScrollEl = targetCell;
                  }
                }
              }
            }
          }

          if (targetScrollEl) break;
        }
      }
    }

      // ================= 场景 2: 行式模型表格定位 (如 Claude、OpenAI、阿里百炼、智谱等) =================
      if (!targetScrollEl) {
        // 构建候选模型关键字列表，严禁单一取第 0 个单词截断导致变成厂商名 (如将 'claude opus 4.8' 变成 'claude')
        var rawTargets = kw.split('|');
        var modelCandidates = [];

        function addCandidate(term) {
          if (!term) return;
          var n = norm(term);
          if (n && modelCandidates.indexOf(n) === -1) modelCandidates.push(n);
          // 空格转连字符 (如 mimo-v2.5 pro -> mimo-v2.5-pro)
          var hyp = n.replace(/\\s+/g, '-');
          if (hyp && modelCandidates.indexOf(hyp) === -1) modelCandidates.push(hyp);
          // 连字符转空格 (如 mimo-v2.5-pro -> mimo v2.5 pro)
          var spc = n.replace(/[-_]+/g, ' ');
          if (spc && modelCandidates.indexOf(spc) === -1) modelCandidates.push(spc);
        }

        for (var rt = 0; rt < rawTargets.length; rt++) {
          var cleanPart = norm(rawTargets[rt].split(' [')[0].split(' (')[0]);
          addCandidate(cleanPart);
          var vendorPrefixes = ['claude ', 'openai ', 'alibaba ', 'zhipu ', 'deepseek ', 'baichuan ', 'minimax ', 'moonshot ', 'google ', 'xiaomi ', 'mimo '];
          for (var pfx = 0; pfx < vendorPrefixes.length; pfx++) {
            if (cleanPart.startsWith(vendorPrefixes[pfx])) {
              addCandidate(cleanPart.slice(vendorPrefixes[pfx].length).trim());
            }
          }
        }

        // 识别是否有独立 Batch 专属表格 (如 Anthropic 官方文档将 Batch 单独建表)
        var batchTables = [];
        var standardTables = [];
        for (var t = 0; t < tables.length; t++) {
          var tNorm = norm(tables[t].innerText);
          if (tNorm.indexOf('batch input') !== -1 || tNorm.indexOf('batch output') !== -1 || tNorm.indexOf('batch api') !== -1) {
            batchTables.push(tables[t]);
          } else {
            standardTables.push(tables[t]);
          }
        }

        var searchRoots = [];
        var activeAriaPanel = document.querySelector('[role="tabpanel"]:not([hidden]):not(.hidden)');
        if (activeAriaPanel && activeAriaPanel.querySelector('table')) {
          searchRoots.push(activeAriaPanel);
        } else if (isBatch && batchTables.length > 0) {
          searchRoots = batchTables;
        } else if (!isBatch && batchTables.length > 0) {
          searchRoots = standardTables;
        } else if (containers.length > 0 && containers[0].children[targetTabIndex]) {
          searchRoots.push(containers[0].children[targetTabIndex]);
        } else {
          searchRoots.push(document);
        }

        function isWordMatch(text, term) {
          if (!text || !term) return false;
          var t = text.toLowerCase();
          var q = term.toLowerCase();
          var idx = 0;
          while ((idx = t.indexOf(q, idx)) !== -1) {
            var leftOk = (idx === 0) || !/[a-zA-Z0-9]/.test(t[idx - 1]);
            var endIdx = idx + q.length;
            var rightChar = endIdx < t.length ? t[endIdx] : '';
            var rightOk = (endIdx >= t.length) || !/[a-zA-Z0-9._\\-]/.test(rightChar);
            if (leftOk && rightOk) {
              return true;
            }
            idx += 1;
          }
          return false;
        }

        var candidateRows = [];

        for (var sr = 0; sr < searchRoots.length; sr++) {
          var rows = searchRoots[sr].querySelectorAll('tr');

          for (var i = 0; i < rows.length; i++) {
            var row = rows[i];
            var rText = norm(row.innerText);

            // 严格单词边界匹配完整候选模型名 (防止 'fable 5' 误匹配 'fable 5.1' 或 'gpt-4' 误匹配 'gpt-4.5')
            var isModelMatch = modelCandidates.some(function(cand) {
              if (!cand || cand.length < 2) return false;
              return isWordMatch(rText, cand);
            });
            if (!isModelMatch) continue;

            // 区分表头/系列标题与实际价格数据行
            var inThead = !!row.closest('thead');
            var tdList = row.querySelectorAll('td');
            var hasOnlyTh = tdList.length === 0;
            var hasPrices = /¥|\\$|元|￥|\\/小时|免费/.test(rText) || /\\d+(?:\\.\\d+)?\\s*(?:元|￥|¥|\\$|\\/)/.test(rText) || /\\$\\s*\\d+/.test(rText);
            var isHeaderKeywords = (rText.indexOf('系列') !== -1 || rText.indexOf('model') !== -1 || rText.indexOf('模型') !== -1 || rText.indexOf('规格') !== -1) && !hasPrices;
            var isHeaderRow = inThead || hasOnlyTh || isHeaderKeywords;

            // 若有阶梯参数，结合阶梯判定
            var tierMatched = true;
            var isUpperTier = kw.indexOf('+') !== -1 || kw.indexOf('>') !== -1 || /512k\+|200k\+|128k\+|256k\+/i.test(kw);
            var isLowerTier = kw.indexOf('[0') !== -1 || kw.indexOf('0,') !== -1 || kw.indexOf('≤') !== -1 || kw.indexOf('<') !== -1;

            if (kw.indexOf('[') !== -1) {
              var tierPart = kw.split('[')[1].replace(/[\\]\\)\\s]/g, '').toLowerCase();
              var tierNums = tierPart.match(/\\d+[kkmg]?/g) || [];
              tierMatched = tierNums.length === 0 || tierNums.some(function(n) { return rText.indexOf(n) !== -1; });
            }
            if (!tierMatched) continue;

            var score = 0;
            if (!isHeaderRow && tdList.length > 0) {
              score += 200; // 基础数据行
              if (hasPrices) score += 100; // 包含真实价格数据

              // 阶梯方向智能权重奖惩
              if (isUpperTier) {
                if (rText.indexOf('>') !== -1 || rText.indexOf('+') !== -1 || rText.indexOf('以上') !== -1) {
                  score += 250; // 阶梯方向精准吻合 (如 > 512k, 512k+)
                } else if (rText.indexOf('≤') !== -1 || rText.indexOf('<') !== -1 || rText.indexOf('以下') !== -1) {
                  score -= 200; // 反向阶梯严重扣分
                }
              } else if (isLowerTier) {
                if (rText.indexOf('≤') !== -1 || rText.indexOf('<') !== -1 || rText.indexOf('以下') !== -1) {
                  score += 250; // 阶梯方向精准吻合 (如 ≤ 512k, [0, 512k))
                } else if (rText.indexOf('>') !== -1 || rText.indexOf('+') !== -1 || rText.indexOf('以上') !== -1) {
                  score -= 200; // 反向阶梯严重扣分
                }
              }

              // 检查是否有某个具体单元格直接完全匹配或作为词首匹配候选词 (例如 <td><code>mimo-v2.5</code></td>)
              for (var d = 0; d < tdList.length; d++) {
                var tdT = norm(tdList[d].innerText);
                if (modelCandidates.some(function(c) { return tdT === c; })) {
                  score += 150; // 单元格完全精准相等
                  break;
                } else if (modelCandidates.some(function(c) { return isWordMatch(tdT, c); })) {
                  score += 80;
                  break;
                }
              }
            } else {
              // 表头或系列标题行：仅得 10 分最低兜底分，绝不抢占真实数据行
              score = 10;
            }

            candidateRows.push({ row: row, score: score });
          }
        }

        // 按打分从高到低排序，优先选取真实价格数据行
        candidateRows.sort(function(a, b) { return b.score - a.score; });
        var matchedRow = candidateRows.length > 0 ? candidateRows[0].row : null;

        // 如果表格中没有高分数据行 (得分 > 10)，尝试在正文段落 (<p> / <li>) 中寻找 (例如小米 TTS 限免说明)
        if (!matchedRow || (candidateRows.length > 0 && candidateRows[0].score <= 10)) {
          var textNodes = document.querySelectorAll('p, li, blockquote, div.mdx-p');
          var bestTextEl = null;
          var bestTextScore = 0;

          for (var p = 0; p < textNodes.length; p++) {
            var pEl = textNodes[p];
            if (pEl.querySelector('table')) continue;
            var pText = norm(pEl.innerText);
            if (!pText || pText.length > 300) continue;

            var pMatch = modelCandidates.some(function(cand) {
              return isWordMatch(pText, cand);
            });
            if (pMatch) {
              var pScore = 80;
              if (/免费|¥|\\$|元|￥|\\/小时/.test(pText)) pScore += 100;
              if (pScore > bestTextScore) {
                bestTextScore = pScore;
                bestTextEl = pEl;
              }
            }
          }

          if (bestTextEl && bestTextScore > (candidateRows.length > 0 ? candidateRows[0].score : 0)) {
            bestTextEl.classList.add('wpd-highlight-row');
            var codeEls = bestTextEl.querySelectorAll('code, strong, span');
            for (var ce = 0; ce < codeEls.length; ce++) {
              var cText = norm(codeEls[ce].innerText);
              if (modelCandidates.some(function(cand) { return isWordMatch(cText, cand); }) || /免费|¥|\\$/.test(cText)) {
                codeEls[ce].classList.add('wpd-highlight-cell');
              }
            }
            targetScrollEl = bestTextEl;
          }
        }

        if (matchedRow && !targetScrollEl) {
          matchedRow.classList.add('wpd-highlight-row');
          var cells = matchedRow.querySelectorAll('td');

          // 如果是双阶梯表格 (如 OpenAI Short context 与 Long context 双区域共 8 列)
          if (cells.length >= 8) {
            var startIdx = isLong ? (cells.length - 4) : (cells.length - 8);
            var endIdx = isLong ? cells.length : (cells.length - 4);
            for (var ci = startIdx; ci < endIdx; ci++) {
              if (cells[ci]) {
                cells[ci].classList.add('wpd-highlight-cell');
              }
            }
            targetScrollEl = cells[startIdx] || matchedRow;
          } else {
            // 普通单阶梯行：高亮所有带货币符号或数值的价格单元格
            for (var c = 0; c < cells.length; c++) {
              var cText = cells[c].innerText;
              if (/¥|\\$|元|￥|\\/小时|免费/.test(cText) || /\\d+(?:\\.\\d+)?\\s*(?:元|￥|¥|\\$|\\/)/.test(cText) || /\\$\\s*\\d+/.test(cText)) {
                cells[c].classList.add('wpd-highlight-cell');
              }
            }
            targetScrollEl = matchedRow;
          }
        }
      }

      // 执行平滑居中滚动与顶部提示条展示
      if (targetScrollEl) {
        targetScrollEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

        var bar = document.createElement('div');
        bar.className = 'wpd-top-indicator';
        bar.innerHTML = '<span>🎯 已自动定位到模型: ' + kw + '</span><span style="opacity: 0.6; font-size: 10px;">(点击重新居中)</span>';
        bar.onclick = function() {
          targetScrollEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        };
        document.body.appendChild(bar);
      }
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', locateAndHighlight);
    } else {
      setTimeout(locateAndHighlight, 300);
    }
  })();
</script>
""".replace("__TARGET_KW__", json.dumps(target_kw))
    if soup.body:
        soup.body.append(BeautifulSoup(highlight_code, "html.parser"))

    return HTMLResponse(content=str(soup))


@router.get("/benchmarks", response_model=Dict[str, Any])
async def get_benchmark_models(db: AsyncSession = Depends(get_db)):
    """获取所有官网第一档去阶梯化标准基准模型列表"""
    benchmarks = await official_benchmark_service.get_benchmark_models(db)
    # 按厂商统计
    providers_set = set()
    for b in benchmarks:
        providers_set.add((b["provider"], b["provider_name"]))
    providers_list = [{"code": p[0], "name": p[1]} for p in sorted(list(providers_set), key=lambda x: x[0])]

    return {
        "status": "success",
        "total": len(benchmarks),
        "benchmarks": benchmarks,
        "providers": providers_list,
        "usd_to_cny_rate": exchange_rate_service.current_rate,
    }


@router.post("/match-channel-models/{channel_id}", response_model=Dict[str, Any])
async def match_channel_models(
    channel_id: int,
    payload: Optional[ChannelMatchOfficialRequest] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    对指定渠道模型执行自动模糊匹配官网第一档基准模型
    如果请求体传递了 models 数组则使用，否则自动查询 site_model_pricings 表中的渠道模型
    """
    channel_models = []
    if payload and payload.models:
        channel_models = [m.model_dump() for m in payload.models]
    else:
        # 查询该渠道已存在的模型价格记录
        stmt = select(SiteModelPricing).where(SiteModelPricing.site_id == channel_id)
        res = await db.execute(stmt)
        pricings = res.scalars().all()
        for p in pricings:
            channel_models.append({
                "id": p.id,
                "site_model_name": p.site_model_name or p.model_id,
                "model_id": p.model_id,
                "group_name": p.group_name or "",
                "calculated_input_usd": p.calculated_input_usd,
                "calculated_output_usd": p.calculated_output_usd,
            })

    matches = await official_benchmark_service.match_channel_models(channel_id, channel_models, db)

    matched_count = sum(1 for m in matches if m.get("is_matched"))
    unmatched_count = len(matches) - matched_count
    
    # 计算有效折扣平均值
    discounts = [m["composite_discount"] for m in matches if m.get("composite_discount") is not None]
    avg_discount = round(sum(discounts) / len(discounts), 3) if discounts else None

    return {
        "status": "success",
        "channel_id": channel_id,
        "total_models": len(matches),
        "matched_count": matched_count,
        "unmatched_count": unmatched_count,
        "avg_discount": avg_discount,
        "items": matches,
    }


@router.post("/save-channel-mappings/{channel_id}", response_model=Dict[str, Any])
async def save_channel_official_mappings(
    channel_id: int,
    payload: SaveOfficialMappingsRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    保存用户确认的渠道模型与官网标准模型映射关系，并更新数据库中的价格真实折扣
    """
    benchmarks = await official_benchmark_service.get_benchmark_models(db)
    bench_map = {b["id"]: b for b in benchmarks}

    # 查询该渠道已有的模型价格记录
    pricings_stmt = select(SiteModelPricing).where(SiteModelPricing.site_id == channel_id)
    p_res = await db.execute(pricings_stmt)
    existing_pricings = p_res.scalars().all()
    pricings_map = {
        p.site_model_name or p.model_id: p for p in existing_pricings
    }

    # 查询已有的渠道映射记录
    maps_stmt = select(ChannelModelMapping).where(ChannelModelMapping.site_id == channel_id)
    m_res = await db.execute(maps_stmt)
    existing_maps = {m.channel_model_name: m for m in m_res.scalars().all()}

    saved_count = 0
    updated_pricing_count = 0

    for item in payload.mappings:
        c_name = item.channel_model_name.strip()
        if not c_name:
            continue

        off_id = item.official_model_id
        off_bench = bench_map.get(off_id) if off_id else None
        off_name = off_bench["clean_name"] if off_bench else (item.official_model_name or "")

        # 1. 更新或创建 ChannelModelMapping
        if c_name in existing_maps:
            cm = existing_maps[c_name]
            cm.official_model_id = off_id
            cm.official_model_name = off_name
        else:
            new_cm = ChannelModelMapping(
                site_id=channel_id,
                channel_model_name=c_name,
                standard_model_id=off_bench["raw_model_id"] if off_bench else c_name,
                official_model_id=off_id,
                official_model_name=off_name,
            )
            db.add(new_cm)
            existing_maps[c_name] = new_cm
        saved_count += 1

        # 2. 同步更新 SiteModelPricing 中的官网字段与真实折扣
        if c_name in pricings_map:
            p_obj = pricings_map[c_name]
            p_obj.official_model_id = off_id
            p_obj.official_model_name = off_name

            if off_bench:
                disc = official_benchmark_service.calculate_discount(
                    p_obj.calculated_input_usd,
                    p_obj.calculated_output_usd,
                    off_bench["converted_input_usd"],
                    off_bench["converted_output_usd"]
                )
                p_obj.official_input_discount = disc["input_discount"]
                p_obj.official_output_discount = disc["output_discount"]
                p_obj.official_composite_discount = disc["composite_discount"]
            else:
                p_obj.official_input_discount = None
                p_obj.official_output_discount = None
                p_obj.official_composite_discount = None
            updated_pricing_count += 1

    await db.commit()

    return {
        "status": "success",
        "channel_id": channel_id,
        "saved_mappings_count": saved_count,
        "updated_pricings_count": updated_pricing_count,
        "message": f"成功保存 {saved_count} 条模型官网映射并更新真实折扣",
    }


