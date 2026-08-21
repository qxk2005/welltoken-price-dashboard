import httpx
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import ModelMetadata, RelaySite, SiteModelPricing, SyncLog

def infer_lab_provider(model_id: str, raw_provider: str) -> str:
    """参考 models.dev/labs/ 官方体系，将模型精准归属到所属的研究机构/厂商 (Lab)"""
    m = model_id.lower()
    p = (raw_provider or "").lower()

    if "/" in m:
        prefix = m.split("/")[0]
        if prefix in ["alibaba", "openai", "anthropic", "google", "deepseek", "meta", "mistral", "moonshotai", "zhipuai", "nvidia", "cohere", "xai", "minimax", "bytedance", "bytedance-seed", "tencent", "baichuan", "stepfun", "sensetime", "xiaomi", "aisingapore", "arcee-ai", "ibm", "meituan", "microsoft", "perplexity", "poolside", "sakana", "sarvam", "sdaia", "swiss-ai", "thinkingmachines", "trendyol", "upstage"]:
            return prefix

    # 规则识别厂商
    if "qwen" in m or "alibaba" in p:
        return "alibaba"
    if "deepseek" in m or "deepseek" in p:
        return "deepseek"
    if "gpt" in m or "o1" in m or "o3" in m or "whisper" in m or "openai" in p:
        return "openai"
    if "claude" in m or "anthropic" in p:
        return "anthropic"
    if "gemini" in m or "gemma" in m or "google" in p:
        return "google"
    if "llama" in m or "meta" in p:
        return "meta"
    if "kimi" in m or "moonshot" in p:
        return "moonshotai"
    if "glm" in m or "zhipu" in p or "chatglm" in m:
        return "zhipuai"
    if "doubao" in m or "seed" in m or "bytedance" in p:
        return "bytedance"
    if "hunyuan" in m or "tencent" in p:
        return "tencent"
    if "mistral" in m or "codestral" in m or "pixtral" in m or "ministral" in m:
        return "mistral"
    if "nemotron" in m or "nvidia" in p:
        return "nvidia"
    if "command" in m or "cohere" in p:
        return "cohere"
    if "grok" in m or "xai" in p:
        return "xai"
    if "minimax" in m or "minimax" in p:
        return "minimax"
    if "step" in m or "stepfun" in p:
        return "stepfun"
    if "sonar" in m or "perplexity" in p:
        return "perplexity"
    if "mimo" in m or "milm" in m or "xiaomi" in p:
        return "xiaomi"
    if "baichuan" in m:
        return "baichuan"

    return p if p and p != "other" else (m.split("/")[0] if "/" in m else "other")

def infer_model_series(model_id: str, provider: str, family: str = "") -> str:
    """推断模型所属的系列 (Family / Series)"""
    if family:
        return family.replace("-", " ").title()
    m = model_id.lower()
    p = provider.lower()
    
    if p == "deepseek" or "deepseek" in m:
        if "r1" in m or "reasoner" in m:
            return "DeepSeek-R1"
        if "v4" in m:
            return "DeepSeek-V4"
        if "v3" in m or "chat" in m:
            return "DeepSeek-V3"
        return "DeepSeek"
        
    if p == "openai" or "gpt" in m or "o1" in m or "o3" in m:
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
        
    if p == "anthropic" or "claude" in m:
        if "3-7" in m or "3.7" in m:
            return "Claude-3.7"
        if "3-5" in m or "3.5" in m:
            return "Claude-3.5"
        if "3" in m:
            return "Claude-3"
        return "Claude"
        
    if p == "google" or "gemini" in m or "gemma" in m:
        if "2.0" in m or "2-0" in m:
            return "Gemini-2.0"
        if "1.5" in m or "1-5" in m:
            return "Gemini-1.5"
        if "gemma" in m:
            return "Gemma"
        return "Gemini"
        
    if p == "alibaba" or "qwen" in m:
        if "3.8" in m:
            return "Qwen-3.8"
        if "3.7" in m:
            return "Qwen-3.7"
        if "3.6" in m:
            return "Qwen-3.6"
        if "3.5" in m:
            return "Qwen-3.5"
        if "3" in m:
            return "Qwen-3"
        if "2.5" in m or "2-5" in m:
            return "Qwen-2.5"
        if "vl" in m:
            return "Qwen-VL"
        if "coder" in m:
            return "Qwen-Coder"
        return "Qwen"

    if p == "moonshotai" or "kimi" in m:
        if "k3" in m:
            return "Kimi-K3"
        if "k2" in m:
            return "Kimi-K2"
        return "Kimi"

    if p == "zhipuai" or "glm" in m:
        if "5" in m:
            return "GLM-5"
        if "4" in m:
            return "GLM-4"
        return "GLM"
        
    return "通用大模型系列"

class ModelsDevSyncService:
    def __init__(self):
        self.models_url = "https://models.dev/models.json"
        self.catalog_url = "https://models.dev/catalog.json"
        self.api_url = "https://models.dev/api.json"
        self.last_sync_time: datetime | None = None

    async def full_sync_from_models_dev(self) -> Dict[str, Any]:
        """内存批量聚合全量同步 models.dev 三大接口并精确规范化 Lab 厂商"""
        start_t = time.time()
        models_count = 0
        providers_count = 0
        pricings_count = 0
        status = "success"
        error_msg = ""

        try:
            print("[ModelsDevSync] Fetching raw JSON from models.dev endpoints...")
            async with httpx.AsyncClient(timeout=20.0) as client:
                m_resp = await client.get(self.models_url)
                models_dict = m_resp.json() if m_resp.status_code == 200 else {}
                
                c_resp = await client.get(self.catalog_url)
                catalog_data = c_resp.json() if c_resp.status_code == 200 else {}
                providers_dict = catalog_data.get("providers", {})

                a_resp = await client.get(self.api_url)
                api_data = a_resp.json() if a_resp.status_code == 200 else {}

            async with AsyncSessionLocal() as session:
                existing_models_res = await session.execute(select(ModelMetadata))
                model_map: Dict[str, ModelMetadata] = {m.model_id: m for m in existing_models_res.scalars().all()}

                existing_sites_res = await session.execute(select(RelaySite))
                site_map: Dict[str, RelaySite] = {s.provider_id: s for s in existing_sites_res.scalars().all() if s.provider_id}

                # 1. 处理模型库并规范化 Lab
                for m_id, m in models_dict.items():
                    name = m.get("name") or m_id
                    raw_provider = m.get("provider") or m.get("company") or (m_id.split("/")[0] if "/" in m_id else "other")
                    provider = infer_lab_provider(m_id, raw_provider)
                    family = m.get("family") or ""
                    series = infer_model_series(m_id, provider, family)
                    
                    pricing = m.get("pricing") or m.get("cost") or {}
                    in_price = float(pricing.get("prompt") or pricing.get("input") or 0.0)
                    out_price = float(pricing.get("completion") or pricing.get("output") or 0.0)
                    cache_price = float(pricing.get("cache_read") or (in_price * 0.5 if in_price > 0 else 0.0))
                    
                    limit = m.get("limit") or {}
                    context_w = int(limit.get("context") or m.get("context_window") or 128000)
                    max_out = int(limit.get("output") or m.get("max_output") or 8192)

                    if m_id in model_map:
                        exist_m = model_map[m_id]
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
                        model_map[m_id] = new_m
                    models_count += 1

                # 2. 处理供应商库
                for p_id, p in providers_dict.items():
                    name = p.get("name") or p_id.upper()
                    base_url = p.get("api") or p.get("url") or f"https://api.{p_id}.com/v1"
                    doc = p.get("doc") or p.get("website") or ""
                    env_list = p.get("env") or []
                    env_str = ", ".join(env_list) if isinstance(env_list, list) else str(env_list)

                    if p_id in site_map:
                        exist_s = site_map[p_id]
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
                        site_map[p_id] = new_s
                    providers_count += 1

                # 3. 处理定价矩阵
                for p_id, p_obj in api_data.items():
                    site = site_map.get(p_id)
                    if not site:
                        continue

                    site_models = p_obj.get("models") or {}
                    for m_id, m_data in site_models.items():
                        meta_m = model_map.get(m_id)
                        cost = m_data.get("cost") or {}
                        in_p = float(cost.get("input") or 0.0)
                        out_p = float(cost.get("output") or 0.0)
                        cache_p = float(cost.get("cache_read") or 0.0)

                        if not meta_m:
                            lab_p = infer_lab_provider(m_id, "other")
                            meta_m = ModelMetadata(
                                model_id=m_id,
                                name=m_data.get("name") or m_id,
                                provider=lab_p,
                                series=infer_model_series(m_id, lab_p, m_data.get("family", "")),
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
                            model_map[m_id] = meta_m
                            models_count += 1

                        discount = round(((in_p - meta_m.official_input_price) / meta_m.official_input_price * 100), 1) if meta_m.official_input_price > 0 else 0.0

                        new_p = SiteModelPricing(
                            site=site,
                            model=meta_m,
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

                # 4. 单次持久化
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
                print(f"[ModelsDevSync] Precision Lab Normalized in {duration_ms}ms! Models: {models_count}, Providers: {providers_count}, Pricings: {pricings_count}")

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            print(f"[ModelsDevSync Error]: {e}")
            duration_ms = round((time.time() - start_t) * 1000, 1)

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
        return await self.full_sync_from_models_dev()

models_dev_sync = ModelsDevSyncService()
