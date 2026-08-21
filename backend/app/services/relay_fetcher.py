import httpx
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Set
from sqlalchemy import select, delete
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing, ChannelModelMapping

# 初始默认收录的中转与官方对照渠道 (方便用户初次启动体验，支持用户随时自由新增/修改真实站点与 Key)
DEFAULT_RELAY_SITES = [
    {
        "name": "DeepSeek 官方 API",
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "",
        "site_type": "official",
        "recharge_rate": 1.0,
        "models_endpoint": "/models",
        "status_endpoint": "",
        "score": 96.5,
        "notes": "DeepSeek 原厂官方直连通道 (填入有效 Key 可进行真实测速)",
        "default_ratios": {
            "deepseek-v3": 1.0,
            "deepseek-r1": 1.0,
        }
    },
    {
        "name": "OpenAI 官方 API",
        "base_url": "https://api.openai.com/v1",
        "api_key": "",
        "site_type": "official",
        "recharge_rate": 1.0,
        "models_endpoint": "/models",
        "status_endpoint": "",
        "score": 95.0,
        "notes": "OpenAI 原厂官方直连通道 (基准对照组)",
        "default_ratios": {
            "gpt-4o": 1.0,
            "gpt-4o-mini": 1.0,
            "o1": 1.0,
        }
    },
    {
        "name": "极速云 AI 中转 (NewAPI)",
        "base_url": "https://api.speedrelay.com/v1",
        "api_key": "",
        "site_type": "newapi",
        "recharge_rate": 1.0,  # 1元=1刀
        "models_endpoint": "/api/models",
        "status_endpoint": "/api/status",
        "score": 98.2,
        "notes": "NewAPI 架构中转站，支持 DeepSeek 与 Claude 高并发",
        "default_ratios": {
            "deepseek-v3": 0.50,
            "deepseek-r1": 0.40,
            "claude-3-5-sonnet": 0.65,
            "claude-3-5-haiku": 0.60,
            "gpt-4o": 0.55,
            "gpt-4o-mini": 0.50,
            "gemini-1.5-pro": 0.60,
            "qwen2.5-72b-instruct": 0.45,
        }
    },
    {
        "name": "星河 AI 聚合 (Sub2API)",
        "base_url": "https://sub.galaxyapi.net/v1",
        "api_key": "",
        "site_type": "sub2api",
        "recharge_rate": 1.0,
        "models_endpoint": "/api/user/models",
        "status_endpoint": "/api/status",
        "score": 92.5,
        "notes": "Sub2API 包月与额度混合计费架构",
        "default_ratios": {
            "deepseek-v3": 0.60,
            "deepseek-r1": 0.55,
            "claude-3-5-sonnet": 0.60,
            "claude-3-5-haiku": 0.60,
            "gpt-4o": 0.60,
            "gpt-4o-mini": 0.60,
            "o1": 0.70,
            "gemini-1.5-pro": 0.65,
        }
    }
]

class RelayFetcherService:
    def __init__(self):
        self.last_sync_time: datetime | None = None

    async def init_default_sites(self):
        """初始化默认渠道站点与基准价格关联"""
        async with AsyncSessionLocal() as session:
            # 1. 确保所有站点存在
            for item in DEFAULT_RELAY_SITES:
                stmt = select(RelaySite).where(RelaySite.name == item["name"])
                res = await session.execute(stmt)
                site = res.scalar_one_or_none()
                if not site:
                    site = RelaySite(
                        name=item["name"],
                        base_url=item["base_url"],
                        api_key=item["api_key"],
                        site_type=item["site_type"],
                        recharge_rate=item["recharge_rate"],
                        models_endpoint=item["models_endpoint"],
                        status_endpoint=item["status_endpoint"],
                        score=item["score"],
                        notes=item["notes"],
                        last_latency_ms=25.0 if "官方" in item["name"] else 45.0
                    )
                    session.add(site)
            await session.commit()

            # 2. 重新构建所有站点的定价关联
            await self._rebuild_all_pricings(session)

        self.last_sync_time = datetime.utcnow()

    async def _rebuild_all_pricings(self, session):
        """基于当前数据库中的模型库和渠道库重新计算所有折算定价"""
        sites_res = await session.execute(select(RelaySite))
        sites = sites_res.scalars().all()
        models_res = await session.execute(select(ModelMetadata))
        models = {m.model_id: m for m in models_res.scalars().all()}

        for s in sites:
            site_preset = next((p for p in DEFAULT_RELAY_SITES if p["name"] == s.name), None)
            ratios = site_preset.get("default_ratios", {}) if site_preset else {}

            for m_id, m in models.items():
                p_stmt = select(SiteModelPricing).where(
                    SiteModelPricing.site_id == s.id,
                    SiteModelPricing.model_id == m_id
                )
                p_res = await session.execute(p_stmt)
                pricing = p_res.scalar_one_or_none()

                ratio = ratios.get(m_id)
                if ratio is None:
                    if s.site_type == "official":
                        continue
                    ratio = 0.65

                calc_in = round(m.official_input_price * ratio * s.recharge_rate, 4)
                calc_out = round(m.official_output_price * ratio * s.recharge_rate, 4)
                calc_cache = round(m.official_cache_price * ratio * s.recharge_rate, 4)
                discount = round(((calc_in - m.official_input_price) / m.official_input_price * 100), 1) if m.official_input_price > 0 else 0.0

                if not pricing:
                    pricing = SiteModelPricing(
                        site_id=s.id,
                        model_id=m_id,
                        model_ratio=ratio,
                        group_ratio=1.0,
                        calculated_input_usd=calc_in,
                        calculated_output_usd=calc_out,
                        calculated_cache_usd=calc_cache,
                        discount_percent=discount,
                        is_available=True,
                        last_tested_tps=58.5 if "极速" in s.name else (64.0 if "官方" in s.name else 48.0)
                    )
                    session.add(pricing)
                else:
                    pricing.model_ratio = ratio
                    pricing.calculated_input_usd = calc_in
                    pricing.calculated_output_usd = calc_out
                    pricing.calculated_cache_usd = calc_cache
                    pricing.discount_percent = discount

        await session.commit()

    async def detect_and_sync_site(self, site_id: int) -> Dict[str, Any]:
        """真实发起 HTTP 请求探测单个中转站的连通性、实时延迟与模型列表"""
        async with AsyncSessionLocal() as session:
            stmt = select(RelaySite).where(RelaySite.id == site_id)
            res = await session.execute(stmt)
            site = res.scalar_one_or_none()
            if not site:
                return {"status": "error", "message": "Site not found"}

            start_t = time.time()
            is_online = False
            real_latency_ms = 0.0
            discovered_models: Set[str] = set()

            headers = {}
            if site.api_key:
                headers["Authorization"] = f"Bearer {site.api_key}"

            # 1. 真实请求探测 models 端点
            target_models_url = f"{site.base_url.rstrip('/')}{site.models_endpoint}"
            try:
                print(f"[RelayFetcher] Real probing models at: {target_models_url}")
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(target_models_url, headers=headers)
                    real_latency_ms = round((time.time() - start_t) * 1000, 1)
                    
                    if resp.status_code == 200:
                        is_online = True
                        data = resp.json()
                        raw_list = data if isinstance(data, list) else (data.get("data") or data.get("models") or [])
                        for item in raw_list:
                            m_id = item.get("id") or item.get("name")
                            if m_id and isinstance(m_id, str):
                                discovered_models.add(m_id.lower())
                    elif resp.status_code == 401:
                        # 401 说明网络与端口畅通，只是鉴权 Key 需要用户配置
                        is_online = True
                        print(f"[RelayFetcher] Site reachable but needs valid Key (HTTP 401).")
            except Exception as e:
                print(f"[RelayFetcher] Probe error for {target_models_url}: {e}")
                real_latency_ms = round((time.time() - start_t) * 1000, 1)

            # 2. 真实探测 status 端点 (若配置)
            if site.status_endpoint:
                try:
                    status_url = f"{site.base_url.rstrip('/')}{site.status_endpoint}"
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        s_resp = await client.get(status_url)
                        if s_resp.status_code == 200:
                            s_data = s_resp.json()
                            if isinstance(s_data, dict) and s_data.get("data"):
                                is_online = True
                except Exception:
                    pass

            site.last_latency_ms = real_latency_ms
            site.last_status = "online" if is_online else "offline"
            site.last_sync_time = datetime.utcnow()
            
            # 如果成功发现了模型，且该渠道未被用户精确指定映射，才进行兜底默认匹配
            if discovered_models:
                cm_stmt = select(ChannelModelMapping).where(ChannelModelMapping.site_id == site.id)
                cm_res = await session.execute(cm_stmt)
                user_mappings = cm_res.scalars().all()

                if not user_mappings:
                    models_res = await session.execute(select(ModelMetadata))
                    db_models = models_res.scalars().all()
                    for m in db_models:
                        if m.model_id.lower() in discovered_models or any(d in m.model_id.lower() for d in discovered_models):
                            # 确保存在定价记录
                            p_stmt = select(SiteModelPricing).where(
                                SiteModelPricing.site_id == site.id,
                                SiteModelPricing.model_id == m.model_id
                            )
                            p_res = await session.execute(p_stmt)
                            exist_p = p_res.scalar_one_or_none()
                            if not exist_p:
                                calc_in = round(m.official_input_price * 0.65 * site.recharge_rate, 4)
                                calc_out = round(m.official_output_price * 0.65 * site.recharge_rate, 4)
                                new_p = SiteModelPricing(
                                    site_id=site.id,
                                    model_id=m.model_id,
                                    model_ratio=0.65,
                                    group_ratio=1.0,
                                    calculated_input_usd=calc_in,
                                    calculated_output_usd=calc_out,
                                    calculated_cache_usd=round(m.official_cache_price * 0.65, 4),
                                    discount_percent=-35.0,
                                    is_available=True,
                                    last_tested_tps=50.0
                                )
                                session.add(new_p)

            await session.commit()

            return {
                "status": "success",
                "site_id": site.id,
                "site_name": site.name,
                "latency_ms": real_latency_ms,
                "is_online": is_online,
                "discovered_models_count": len(discovered_models)
            }

    async def sync_all_sites(self) -> List[Dict[str, Any]]:
        """全量探测所有启用的中转渠道"""
        async with AsyncSessionLocal() as session:
            sites_res = await session.execute(select(RelaySite).where(RelaySite.is_active == True))
            sites = sites_res.scalars().all()
            site_ids = [s.id for s in sites]

        results = []
        for sid in site_ids:
            res = await self.detect_and_sync_site(sid)
            results.append(res)
        self.last_sync_time = datetime.utcnow()
        return results

relay_fetcher = RelayFetcherService()
