import httpx
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Tuple
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import ModelMetadata, RelaySite, SiteModelPricing, SyncLog

def infer_lab_provider(model_id: str, raw_provider: str) -> str:
    """参考 models.dev/labs/ 官方体系，将模型精准归属到所属的真正研发母厂 (Lab)"""
    m = model_id.lower()
    p = (raw_provider or "").lower()

    # 1. 优先基于模型核心名称精准识别研发母厂 (避免云平台前缀如 alibaba/deepseek 误归属)
    if "deepseek" in m:
        return "deepseek"
    if "claude" in m:
        return "anthropic"
    if "gemini" in m or "gemma" in m:
        return "google"
    if "qwen" in m:
        return "alibaba"
    if "gpt" in m or "o1-" in m or "o1." in m or "o3-" in m or "o3." in m or "o4-" in m or "whisper" in m or "text-embedding-3" in m:
        return "openai"
    if "glm" in m or "chatglm" in m or "cogview" in m or "cogvideo" in m:
        return "zhipuai"
    if "kimi" in m or "moonshot" in m:
        return "moonshotai"
    if "doubao" in m or "skylark" in m or "seed-edit" in m:
        return "bytedance"
    if "hunyuan" in m:
        return "tencent"
    if "llama" in m:
        return "meta"
    if "mistral" in m or "codestral" in m or "pixtral" in m or "ministral" in m or "mixtral" in m:
        return "mistral"
    if "nemotron" in m:
        return "nvidia"
    if "command" in m or "cohere" in m:
        return "cohere"
    if "grok" in m:
        return "xai"
    if "minimax" in m or "abab" in m:
        return "minimax"
    if "step-" in m or "stepfun" in m:
        return "stepfun"
    if "sonar" in m:
        return "perplexity"
    if "mimo" in m or "milm" in m:
        return "xiaomi"
    if "baichuan" in m:
        return "baichuan"

    # 2. 如果模型名没有明显特征，检查 raw_provider
    if "deepseek" in p:
        return "deepseek"
    if "anthropic" in p:
        return "anthropic"
    if "google" in p:
        return "google"
    if "alibaba" in p or "aliyun" in p or "bailing" in p:
        return "alibaba"
    if "openai" in p:
        return "openai"
    if "zhipu" in p:
        return "zhipuai"
    if "moonshot" in p:
        return "moonshotai"
    if "bytedance" in p:
        return "bytedance"
    if "tencent" in p:
        return "tencent"
    if "meta" in p:
        return "meta"
    if "mistral" in p:
        return "mistral"
    if "nvidia" in p:
        return "nvidia"
    if "cohere" in p:
        return "cohere"
    if "xai" in p:
        return "xai"
    if "minimax" in p:
        return "minimax"
    if "stepfun" in p:
        return "stepfun"
    if "perplexity" in p:
        return "perplexity"
    if "xiaomi" in p:
        return "xiaomi"
    if "baichuan" in p:
        return "baichuan"
    if "microsoft" in p:
        return "microsoft"
    if "upstage" in p:
        return "upstage"

    # 3. 检查模型 ID 前缀
    if "/" in m:
        prefix = m.split("/")[0]
        if prefix in ["alibaba", "openai", "anthropic", "google", "deepseek", "meta", "mistral", "moonshotai", "zhipuai", "nvidia", "cohere", "xai", "minimax", "bytedance", "tencent", "baichuan", "stepfun", "xiaomi", "microsoft", "perplexity", "upstage"]:
            return prefix

    return p if p and p != "other" and p in ["alibaba", "openai", "anthropic", "google", "deepseek", "meta", "mistral", "moonshotai", "zhipuai", "nvidia", "cohere", "xai", "minimax", "bytedance", "tencent", "baichuan", "stepfun", "xiaomi", "microsoft", "perplexity", "upstage"] else "other"

def infer_model_series(model_id: str, provider: str, family: str = "") -> str:
    """根据研发厂商与模型名称推断强绑定的模型系列 (Series)"""
    m = model_id.lower()
    p = provider.lower()
    
    # 1. Alibaba 强绑定系列
    if p == "alibaba":
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
        if "audio" in m:
            return "Qwen-Audio"
        return "Qwen"

    # 2. DeepSeek 强绑定系列
    if p == "deepseek":
        if "r1" in m or "reasoner" in m:
            return "DeepSeek-R1"
        if "v4" in m:
            return "DeepSeek-V4"
        if "v3" in m:
            return "DeepSeek-V3"
        if "coder" in m:
            return "DeepSeek-Coder"
        if "math" in m:
            return "DeepSeek-Math"
        if "vl" in m or "janus" in m:
            return "DeepSeek-Janus"
        return "DeepSeek"

    # 3. OpenAI 强绑定系列
    if p == "openai":
        if "5" in m:
            return "GPT-5"
        if "4o" in m:
            return "GPT-4o"
        if "o1" in m:
            return "OpenAI o1"
        if "o3" in m:
            return "OpenAI o3"
        if "o4" in m:
            return "OpenAI o4"
        if "gpt-4" in m:
            return "GPT-4"
        if "3.5" in m or "3-5" in m:
            return "GPT-3.5"
        if "whisper" in m:
            return "Whisper"
        if "embedding" in m:
            return "Text-Embedding"
        return "GPT"

    # 4. Anthropic 强绑定系列
    if p == "anthropic":
        if "3-7" in m or "3.7" in m:
            return "Claude-3.7"
        if "3-5" in m or "3.5" in m:
            return "Claude-3.5"
        if "3" in m:
            return "Claude-3"
        return "Claude"

    # 5. Google 强绑定系列
    if p == "google":
        if "2.0" in m or "2-0" in m:
            return "Gemini-2.0"
        if "1.5" in m or "1-5" in m:
            return "Gemini-1.5"
        if "gemma" in m:
            return "Gemma"
        return "Gemini"

    # 6. Zhipu AI 强绑定系列
    if p == "zhipuai":
        if "5" in m:
            return "GLM-5"
        if "4" in m:
            return "GLM-4"
        if "cog" in m:
            return "CogView"
        return "GLM"

    # 7. Moonshot AI 强绑定系列
    if p == "moonshotai":
        if "k3" in m:
            return "Kimi-K3"
        if "k2" in m:
            return "Kimi-K2"
        return "Kimi"

    # 8. ByteDance 强绑定系列
    if p == "bytedance":
        if "1.5" in m:
            return "Doubao-1.5"
        if "seed" in m:
            return "Seed"
        return "Doubao"

    # 9. Meta 强绑定系列
    if p == "meta":
        if "3.3" in m or "3-3" in m:
            return "Llama-3.3"
        if "3.1" in m or "3-1" in m:
            return "Llama-3.1"
        if "3" in m:
            return "Llama-3"
        if "2" in m:
            return "Llama-2"
        return "Llama"

    # 10. Mistral 强绑定系列
    if p == "mistral":
        if "codestral" in m:
            return "Codestral"
        if "pixtral" in m:
            return "Pixtral"
        if "ministral" in m:
            return "Ministral"
        if "large" in m:
            return "Mistral Large"
        if "small" in m:
            return "Mistral Small"
        return "Mistral"

    # 11. Tencent 强绑定系列
    if p == "tencent":
        return "Hunyuan"

    # 12. MiniMax 强绑定系列
    if p == "minimax":
        if "abab" in m:
            return "Abab"
        return "MiniMax"

    # 13. StepFun 强绑定系列
    if p == "stepfun":
        return "Step"

    # 14. Xiaomi 强绑定系列
    if p == "xiaomi":
        if "mimo" in m:
            return "MiMo"
        return "MiLM"

    # 15. xAI 强绑定系列
    if p == "xai":
        if "3" in m:
            return "Grok-3"
        if "2" in m:
            return "Grok-2"
        return "Grok"

    # 16. Baichuan 强绑定系列
    if p == "baichuan":
        return "Baichuan"

    # 17. Cohere 强绑定系列
    if p == "cohere":
        return "Command R"

    if family:
        return family.replace("-", " ").title()

    return "通用大模型系列"

class ModelsDevSyncService:
    def __init__(self):
        self.models_url = "https://models.dev/models.json"
        self.catalog_url = "https://models.dev/catalog.json"
        self.api_url = "https://models.dev/api.json"
        self.cache_dir = "data/cache"
        self.last_sync_time: datetime | None = None

    async def _fetch_with_cache(self, client: httpx.AsyncClient, url: str, cache_filename: str) -> Any:
        """优先从远端抓取，成功后写入本地缓存；若网络失败则自动回退加载本地缓存"""
        import os
        os.makedirs(self.cache_dir, exist_ok=True)
        cache_path = os.path.join(self.cache_dir, cache_filename)

        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                try:
                    with open(cache_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False)
                except Exception as ce:
                    print(f"[ModelsDevSync] 写入缓存文件失败: {ce}")
                return data
        except Exception as e:
            print(f"[ModelsDevSync] 抓取远端 {url} 失败: {e}，尝试读取本地缓存...")

        # 尝试读取本地缓存
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[ModelsDevSync] 读取缓存文件失败: {e}")

        return None

    async def full_sync_from_models_dev(self) -> Dict[str, Any]:
        """内存批量聚合全量同步 models.dev 三大接口并精确规范化 Lab 厂商与渠道定价"""
        from backend.app.services.dashboard_service import dashboard_service
        start_t = time.time()
        models_count = 0
        providers_count = 0
        pricings_count = 0
        status = "success"
        error_msg = ""

        async def report_progress(stage: int, progress: int, message: str, detail: str = "", stats: dict = None):
            try:
                await dashboard_service.broadcast({
                    "type": "SYNC_PROGRESS",
                    "stage": stage,
                    "progress": progress,
                    "message": message,
                    "detail": detail,
                    "stats": stats or {}
                })
            except Exception:
                pass

        try:
            # 阶段 1: 抓取数据源 (15%)
            await report_progress(1, 15, "正在连接并拉取 models.dev 官方 3 大核心数据源...", "正在下载 models.json, catalog.json 与 api.json")

            async with httpx.AsyncClient(timeout=35.0) as client:
                api_data = await self._fetch_with_cache(client, self.api_url, "models_dev_api.json") or {}
                models_data = await self._fetch_with_cache(client, self.models_url, "models_dev_models.json") or {}
                catalog_data = await self._fetch_with_cache(client, self.catalog_url, "models_dev_catalog.json") or {}

            if not api_data and not models_data and not catalog_data:
                raise Exception("无法从 models.dev 获取数据且本地暂无可用缓存，请检查网络或代理连接")

            await report_progress(1, 35, "核心数据源已就绪 (包含本地高速缓存)", "正在解析全网大模型与供应商结构树...")

            # 整理统一 models_dict 与 providers_dict
            raw_models = {}
            if isinstance(models_data, dict):
                raw_models.update(models_data)
            elif isinstance(models_data, list):
                for m in models_data:
                    m_id = m.get("id") or m.get("model_id")
                    if m_id:
                        raw_models[m_id] = m

            catalog_models = catalog_data.get("models") or {}
            if isinstance(catalog_models, dict):
                for m_id, m in catalog_models.items():
                    if m_id not in raw_models:
                        raw_models[m_id] = m

            providers_dict = {}
            catalog_providers = catalog_data.get("providers") or {}
            if isinstance(catalog_providers, dict):
                providers_dict.update(catalog_providers)

            if isinstance(api_data, dict):
                for p_id, p_obj in api_data.items():
                    if p_id not in providers_dict:
                        providers_dict[p_id] = p_obj

            # 阶段 2: 规范化模型 (55%)
            await report_progress(2, 55, "正在标准化 30 大权威 Lab 厂商与模型系列层级...", f"已识别 {len(raw_models)} 款大模型标准规格")

            async with AsyncSessionLocal() as session:
                # 加载现有数据以做增量比对
                existing_models_res = await session.execute(select(ModelMetadata))
                model_map: Dict[str, ModelMetadata] = {m.model_id: m for m in existing_models_res.scalars().all()}

                existing_sites_res = await session.execute(select(RelaySite))
                site_map: Dict[str, RelaySite] = {s.provider_id or s.name.lower(): s for s in existing_sites_res.scalars().all()}

                # 1. 批量处理标准模型库 (ModelMetadata)
                for m_id, m in raw_models.items():
                    name = m.get("name") or m.get("display_name") or m_id
                    family = m.get("family") or ""
                    raw_provider = m.get("provider") or m.get("organization") or (m_id.split("/")[0] if "/" in m_id else "other")
                    provider = infer_lab_provider(m_id, raw_provider)
                    series = infer_model_series(m_id, provider, family)

                    cost = m.get("cost") or m.get("pricing") or {}
                    in_price = float(cost.get("input") or cost.get("prompt") or 0.0)
                    out_price = float(cost.get("output") or cost.get("completion") or 0.0)
                    cache_price = float(cost.get("cache_read") or (in_price * 0.5 if in_price > 0 else 0.0))

                    limit = m.get("limit") or {}
                    context_w = int(limit.get("context") or m.get("context_window") or 128000)
                    max_out = int(limit.get("output") or m.get("max_output") or 8192)

                    release_d = str(m.get("release_date") or "")
                    last_upd = str(m.get("last_updated") or m.get("release_date") or "")

                    if m_id in model_map:
                        exist_m = model_map[m_id]
                        exist_m.name = name
                        exist_m.provider = provider
                        exist_m.series = series
                        exist_m.family = family
                        exist_m.context_window = context_w
                        exist_m.max_output = max_out
                        exist_m.release_date = release_d or exist_m.release_date
                        exist_m.last_updated = last_upd or exist_m.last_updated
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
                            release_date=release_d,
                            last_updated=last_upd,
                            is_featured=False,
                            description=m.get("description") or f"models.dev 官方标准模型 {m_id}"
                        )
                        session.add(new_m)
                        model_map[m_id] = new_m
                    models_count += 1

                # 阶段 3: 整理供应商渠道与定价矩阵 (75%)
                await report_progress(3, 75, "正在整理 190+ 供应商中转渠道与聚合定价矩阵...", f"正在构建 {len(providers_dict)} 家渠道与比价矩阵")

                # 2. 批量处理供应商/渠道库 (RelaySite)
                for p_id, p in providers_dict.items():
                    p_key = p_id.lower()
                    name = p.get("name") or p_id.upper()
                    base_url = p.get("api") or p.get("url") or f"https://api.{p_id}.com/v1"
                    doc = p.get("doc") or p.get("website") or ""
                    env_list = p.get("env") or []
                    env_str = ", ".join(env_list) if isinstance(env_list, list) else str(env_list)

                    if p_key in site_map:
                        exist_s = site_map[p_key]
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
                            site_type="cloud" if ("router" in p_key or "ai" in p_key) else "official",
                            recharge_rate=1.0,
                            currency="USD",
                            models_endpoint="/v1/models",
                            doc_url=doc,
                            env_vars=env_str,
                            is_official_catalog=True,
                            is_active=True,
                            score=92.0,
                            last_latency_ms=45.0
                        )
                        session.add(new_s)
                        site_map[p_key] = new_s
                    providers_count += 1

                # 确保新增的 sites 获得数据库自增 ID (通过 flush)
                await session.flush()

                # 3. 批量处理定价矩阵 (SiteModelPricing)
                existing_pricings_res = await session.execute(select(SiteModelPricing))
                pricing_map = {(p.site_id, p.model_id): p for p in existing_pricings_res.scalars().all()}

                if isinstance(api_data, dict):
                    for p_id, p_obj in api_data.items():
                        p_key = p_id.lower()
                        site = site_map.get(p_key)
                        if not site:
                            continue

                        site_models = p_obj.get("models") or {}
                        if not isinstance(site_models, dict):
                            continue

                        for m_id, m_data in site_models.items():
                            meta_m = model_map.get(m_id)
                            cost = m_data.get("cost") or {}
                            in_p = float(cost.get("input") or cost.get("prompt") or 0.0)
                            out_p = float(cost.get("output") or cost.get("completion") or 0.0)
                            cache_p = float(cost.get("cache_read") or 0.0)

                            if not meta_m:
                                raw_p = m_id.split("/")[0] if "/" in m_id else "other"
                                lab_p = infer_lab_provider(m_id, raw_p)
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

                            discount = (
                                round(((in_p - meta_m.official_input_price) / meta_m.official_input_price * 100), 1)
                                if meta_m.official_input_price > 0 and in_p > 0
                                else 0.0
                            )

                            m_src_time = str(m_data.get("last_updated") or m_data.get("release_date") or getattr(meta_m, "last_updated", "") or getattr(meta_m, "release_date", "") or "")

                            p_tuple = (site.id, meta_m.model_id)
                            if p_tuple in pricing_map:
                                exist_p = pricing_map[p_tuple]
                                exist_p.calculated_input_usd = in_p
                                exist_p.calculated_output_usd = out_p
                                exist_p.calculated_cache_usd = cache_p
                                exist_p.discount_percent = discount
                                exist_p.source_updated_at = m_src_time
                                exist_p.updated_at = datetime.utcnow()
                            else:
                                new_p = SiteModelPricing(
                                    site_id=site.id,
                                    model_id=meta_m.model_id,
                                    site_model_name=m_id,
                                    model_ratio=1.0,
                                    group_ratio=1.0,
                                    calculated_input_usd=in_p,
                                    calculated_output_usd=out_p,
                                    calculated_cache_usd=cache_p,
                                    discount_percent=discount,
                                    is_available=True,
                                    last_tested_tps=55.0,
                                    source_updated_at=m_src_time
                                )
                                session.add(new_p)
                                pricing_map[p_tuple] = new_p
                            pricings_count += 1

                # 阶段 4: 持久化写入 SQLite (90%)
                await report_progress(4, 90, "正在持久化写入 SQLite 数据库与构建索引快照...", f"正在提交 {models_count} 款模型、{providers_count} 家渠道与 {pricings_count} 条报价...")

                # 4. 单次持久化审计日志
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
                print(f"[ModelsDevSync] 批量同步成功! 耗时: {duration_ms}ms, 标准模型: {models_count}, 供应商渠道: {providers_count}, 定价条目: {pricings_count}")

                # 刷新模型规范化服务缓存
                try:
                    from backend.app.services.model_normalizer import model_normalizer
                    await model_normalizer.initialize()
                except Exception:
                    pass

            self.last_sync_time = datetime.utcnow()

            # 阶段 5: 完成广播 (100%)
            final_stats = {
                "models_count": models_count,
                "providers_count": providers_count,
                "pricings_count": pricings_count,
                "duration_ms": duration_ms
            }
            await report_progress(5, 100, "全网大模型与渠道比价数据同步完成！", f"已更新 {models_count} 款标准模型 · {providers_count} 家供应商 · {pricings_count} 条比价", final_stats)

            return {
                "status": "success",
                "models_count": models_count,
                "providers_count": providers_count,
                "pricings_count": pricings_count,
                "duration_ms": duration_ms,
                "timestamp": self.last_sync_time.isoformat()
            }

        except Exception as e:
            status = "failed"
            error_msg = str(e)
            print(f"[ModelsDevSync Error]: {e}")
            duration_ms = round((time.time() - start_t) * 1000, 1)
            self.last_sync_time = datetime.utcnow()
            await report_progress(-1, 0, f"❌ 同步失败: {error_msg}", "请检查网络或稍后重试")
            return {
                "status": "failed",
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
