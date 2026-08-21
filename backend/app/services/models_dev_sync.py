import httpx
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy import select, delete
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import ModelMetadata, RelaySite, SiteModelPricing, SyncLog

def infer_model_series(model_id: str, provider: str, family: str = "") -> str:
    if family:
        return family.replace("-", " ").title()
    m = model_id.lower()
    p = provider.lower()
    
    if "deepseek" in p or "deepseek" in m:
        if "r1" in m or "reasoner" in m:
            return "DeepSeek-R1"
        if "v4" in m:
            return "DeepSeek-V4"
        if "v3" in m or "chat" in m:
            return "DeepSeek-V3"
        return "DeepSeek"
        
    if "openai" in p or "gpt" in m or "o1" in m or "o3" in m:
        if "5" in m:
            return "GPT-5"
        if "4o" in m:
            return "GPT-4o"
        if "o1" in m:
            return "OpenAI o1"
        if "o3" in m:
            return "OpenAI o3"
        if "gpt-4" in m:
            return "GPT-4"
        return "GPT"
        
    if "anthropic" in p or "claude" in m:
        if "3-7" in m or "3.7" in m:
            return "Claude-3.7"
        if "3-5" in m or "3.5" in m:
            return "Claude-3.5"
        if "3" in m:
            return "Claude-3"
        return "Claude"
        
    if "google" in p or "gemini" in m:
        if "2.0" in m or "2-0" in m:
            return "Gemini-2.0"
        if "1.5" in m or "1-5" in m:
            return "Gemini-1.5"
        return "Gemini"
        
    if "alibaba" in p or "qwen" in m:
        if "3" in m:
            return "Qwen-3"
        if "2.5" in m or "2-5" in m:
            return "Qwen-2.5"
        if "vl" in m:
            return "Qwen-VL"
        return "Qwen"
        
    return "通用大模型系列"

class ModelsDevSyncService:
    def __init__(self):
        self.models_url = "https://models.dev/models.json"
        self.catalog_url = "https://models.dev/catalog.json"
        self.api_url = "https://models.dev/api.json"
        self.last_sync_time: datetime | None = None

    async def full_sync_from_models_dev(self) -> Dict[str, Any]:
        """全量真实抓取 models.dev 的 models.json, catalog.json, api.json 三大接口"""
        start_t = time.time()
        models_count = 0
        providers_count = 0
        pricings_count = 0
        status = "success"
        error_msg = ""

        try:
            print("[ModelsDevSync] Starting Full Real Sync from models.dev...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                # 1. 抓取 models.json (350+ 模型标准库)
                print(f"[ModelsDevSync] 1/3 Fetching {self.models_url} ...")
                m_resp = await client.get(self.models_url)
                models_dict = m_resp.json() if m_resp.status_code == 200 else {}
                
                # 2. 抓取 catalog.json (190+ 供应商)
                print(f"[ModelsDevSync] 2/3 Fetching {self.catalog_url} ...")
                c_resp = await client.get(self.catalog_url)
                catalog_data = c_resp.json() if c_resp.status_code == 200 else {}
                providers_dict = catalog_data.get("providers", {})

                # 3. 抓取 api.json (全网定价大矩阵)
                print(f"[ModelsDevSync] 3/3 Fetching {self.api_url} ...")
                a_resp = await client.get(self.api_url)
                api_data = a_resp.json() if a_resp.status_code == 200 else {}

            async with AsyncSessionLocal() as session:
                # === A. 同步模型库 ===
                for m_id, m in models_dict.items():
                    name = m.get("name") or m_id
                    provider = m.get("provider") or m.get("company") or (m_id.split("/")[0] if "/" in m_id else "other")
                    family = m.get("family") or ""
                    series = infer_model_series(m_id, provider, family)
                    
                    pricing = m.get("pricing") or m.get("cost") or {}
                    in_price = float(pricing.get("prompt") or pricing.get("input") or 0.0)
                    out_price = float(pricing.get("completion") or pricing.get("output") or 0.0)
                    cache_price = float(pricing.get("cache_read") or (in_price * 0.5 if in_price > 0 else 0.0))
                    
                    limit = m.get("limit") or {}
                    context_w = int(limit.get("context") or m.get("context_window") or 128000)
                    max_out = int(limit.get("output") or m.get("max_output") or 8192)

                    stmt = select(ModelMetadata).where(ModelMetadata.model_id == m_id)
                    res = await session.execute(stmt)
                    exist_m = res.scalar_one_or_none()
                    if exist_m:
                        exist_m.name = name
                        exist_m.provider = provider
                        exist_m.series = series
                        exist_m.family = family
                        exist_m.context_window = context_w
                        exist_m.max_output = max_out
                        if in_price > 0:
                            exist_m.official_input_price = in_price
                        if out_price > 0:
                            exist_m.official_output_price = out_price
                        exist_m.official_cache_price = cache_price
                        exist_m.updated_at = datetime.utcnow()
                    else:
                        new_m = ModelMetadata(
                            model_id=m_id,
                            name=name,
                            provider=provider,
                            series=series,
                            family=family,
                            context_window=context_w,
                            max_output=max_out,
                            official_input_price=in_price,
                            official_output_price=out_price,
                            official_cache_price=cache_price,
                            modalities="text",
                            capabilities="tool_calling",
                            is_featured=False,
                            description=m.get("description") or f"models.dev 官方标准模型 {m_id}"
                        )
                        session.add(new_m)
                    models_count += 1

                # === B. 同步供应商库 ===
                for p_id, p in providers_dict.items():
                    name = p.get("name") or p_id.upper()
                    base_url = p.get("api") or p.get("url") or f"https://api.{p_id}.com/v1"
                    doc = p.get("doc") or p.get("website") or ""
                    env_list = p.get("env") or []
                    env_str = ", ".join(env_list) if isinstance(env_list, list) else str(env_list)

                    stmt = select(RelaySite).where(RelaySite.provider_id == p_id)
                    res = await session.execute(stmt)
                    exist_s = res.scalar_one_or_none()
                    if exist_s:
                        exist_s.name = name
                        exist_s.base_url = base_url
                        exist_s.doc_url = doc
                        exist_s.env_vars = env_str
                        exist_s.is_official_catalog = True
                    else:
                        new_s = RelaySite(
                            provider_id=p_id,
                            name=name,
                            base_url=base_url,
                            site_type="cloud" if "router" in p_id or "ai" in p_id else "official",
                            recharge_rate=1.0,
                            models_endpoint="/v1/models",
                            doc_url=doc,
                            env_vars=env_str,
                            is_official_catalog=True,
                            is_active=True,
                            score=90.0,
                            last_latency_ms=40.0
                        )
                        session.add(new_s)
                    providers_count += 1

                await session.flush()

                # === C. 同步定价大矩阵 ===
                for p_id, p_obj in api_data.items():
                    # 找到对应站点
                    s_stmt = select(RelaySite).where(RelaySite.provider_id == p_id)
                    s_res = await session.execute(s_stmt)
                    site = s_res.scalar_one_or_none()
                    if not site:
                        continue

                    site_models = p_obj.get("models") or {}
                    for m_id, m_data in site_models.items():
                        # 确保对应模型在 model_metadata 中存在
                        m_stmt = select(ModelMetadata).where(ModelMetadata.model_id == m_id)
                        m_res = await session.execute(m_stmt)
                        meta_m = m_res.scalar_one_or_none()
                        
                        cost = m_data.get("cost") or {}
                        in_p = float(cost.get("input") or 0.0)
                        out_p = float(cost.get("output") or 0.0)
                        cache_p = float(cost.get("cache_read") or 0.0)

                        if not meta_m:
                            # 动态注册新发现的模型
                            meta_m = ModelMetadata(
                                model_id=m_id,
                                name=m_data.get("name") or m_id,
                                provider=m_id.split("/")[0] if "/" in m_id else "other",
                                series=infer_model_series(m_id, "other", m_data.get("family", "")),
                                family=m_data.get("family") or "",
                                context_window=int(m_data.get("limit", {}).get("context") or 128000),
                                max_output=int(m_data.get("limit", {}).get("output") or 8192),
                                official_input_price=in_p,
                                official_output_price=out_p,
                                official_cache_price=cache_p,
                                is_featured=False,
                                description=m_data.get("description") or ""
                            )
                            session.add(meta_m)
                            await session.flush()
                            models_count += 1

                        # 更新或创建 SiteModelPricing
                        p_stmt = select(SiteModelPricing).where(
                            SiteModelPricing.site_id == site.id,
                            SiteModelPricing.model_id == m_id
                        )
                        p_res = await session.execute(p_stmt)
                        exist_p = p_res.scalar_one_or_none()

                        # 计算折扣
                        discount = round(((in_p - meta_m.official_input_price) / meta_m.official_input_price * 100), 1) if meta_m.official_input_price > 0 else 0.0

                        if exist_p:
                            exist_p.calculated_input_usd = in_p
                            exist_p.calculated_output_usd = out_p
                            exist_p.calculated_cache_usd = cache_p
                            exist_p.discount_percent = discount
                        else:
                            new_p = SiteModelPricing(
                                site_id=site.id,
                                model_id=m_id,
                                model_ratio=1.0,
                                group_ratio=1.0,
                                calculated_input_usd=in_p,
                                calculated_output_usd=out_p,
                                calculated_cache_usd=cache_p,
                                discount_percent=discount,
                                is_available=True,
                                last_tested_tps=55.0
                            )
                            session.add(new_p)
                        pricings_count += 1

                # === D. 写入同步审计日志 ===
                duration_ms = round((time.time() - start_t) * 1000, 1)
                sync_log = SyncLog(
                    source="models.dev (api+models+catalog)",
                    sync_type="full",
                    status=status,
                    models_count=models_count,
                    providers_count=providers_count,
                    pricings_count=pricings_count,
                    duration_ms=duration_ms,
                    error_message=error_msg
                )
                session.add(sync_log)
                await session.commit()
                print(f"[ModelsDevSync] Sync complete in {duration_ms}ms! Models: {models_count}, Providers: {providers_count}, Pricings: {pricings_count}")

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            print(f"[ModelsDevSync Error]: {e}")
            duration_ms = round((time.time() - start_t) * 1000, 1)
            async with AsyncSessionLocal() as session:
                sync_log = SyncLog(
                    source="models.dev",
                    sync_type="full",
                    status="failed",
                    models_count=models_count,
                    providers_count=providers_count,
                    pricings_count=pricings_count,
                    duration_ms=duration_ms,
                    error_message=error_msg
                )
                session.add(sync_log)
                await session.commit()

        self.last_sync_time = datetime.utcnow()
        return {
            "status": status,
            "models_count": models_count,
            "providers_count": providers_count,
            "pricings_count": pricings_count,
            "duration_ms": duration_ms,
            "error": error_msg,
            "timestamp": self.last_sync_time.isoformat()
        }

    async def sync_from_models_dev(self):
        """兼容入口"""
        return await self.full_sync_from_models_dev()

models_dev_sync = ModelsDevSyncService()
