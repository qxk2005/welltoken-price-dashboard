import httpx
import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import ModelMetadata

# 辅助函数：根据 model_id 和 name 智能提取模型系列 (Series)
def infer_model_series(model_id: str, provider: str) -> str:
    m = model_id.lower()
    p = provider.lower()
    
    if "deepseek" in p or "deepseek" in m:
        if "r1" in m:
            return "DeepSeek-R1"
        if "v3" in m:
            return "DeepSeek-V3"
        if "v2" in m:
            return "DeepSeek-V2"
        if "coder" in m:
            return "DeepSeek-Coder"
        return "DeepSeek-V3"
        
    if "openai" in p or "gpt" in m or "o1" in m or "o3" in m:
        if "4o" in m:
            return "GPT-4o"
        if "o1" in m:
            return "OpenAI o1"
        if "o3" in m:
            return "OpenAI o3"
        if "gpt-4" in m:
            return "GPT-4"
        return "GPT-4o"
        
    if "anthropic" in p or "claude" in m:
        if "3-5" in m or "3.5" in m:
            return "Claude-3.5"
        if "3-7" in m or "3.7" in m:
            return "Claude-3.7"
        if "3" in m:
            return "Claude-3"
        return "Claude-3.5"
        
    if "google" in p or "gemini" in m:
        if "2.0" in m or "2-0" in m:
            return "Gemini-2.0"
        if "1.5" in m or "1-5" in m:
            return "Gemini-1.5"
        return "Gemini-1.5"
        
    if "alibaba" in p or "qwen" in m:
        if "2.5" in m or "2-5" in m:
            return "Qwen-2.5"
        if "2" in m:
            return "Qwen-2"
        if "vl" in m:
            return "Qwen-VL"
        return "Qwen-2.5"
        
    return "通用大模型系列"

# 丰富精细的模型标准库
FALLBACK_MODELS_CATALOG = [
    # DeepSeek 系列
    {
        "model_id": "deepseek-v3",
        "name": "DeepSeek V3 (通用大模型)",
        "provider": "deepseek",
        "series": "DeepSeek-V3",
        "context_window": 64000,
        "max_output": 8192,
        "official_input_price": 0.14,
        "official_output_price": 0.28,
        "official_cache_price": 0.014,
        "modalities": "text",
        "capabilities": "tool_calling,structured_outputs",
        "is_featured": True,
        "description": "DeepSeek 开源 MoE 架构旗舰模型，性价比之王"
    },
    {
        "model_id": "deepseek-chat",
        "name": "DeepSeek Chat (官方通用对话别名)",
        "provider": "deepseek",
        "series": "DeepSeek-V3",
        "context_window": 64000,
        "max_output": 8192,
        "official_input_price": 0.14,
        "official_output_price": 0.28,
        "official_cache_price": 0.014,
        "modalities": "text",
        "capabilities": "chat,tool_calling",
        "is_featured": True,
        "description": "DeepSeek 官方 API 默认对话端点模型"
    },
    {
        "model_id": "deepseek-r1",
        "name": "DeepSeek R1 (推理旗舰)",
        "provider": "deepseek",
        "series": "DeepSeek-R1",
        "context_window": 64000,
        "max_output": 8192,
        "official_input_price": 0.55,
        "official_output_price": 2.19,
        "official_cache_price": 0.14,
        "modalities": "text",
        "capabilities": "reasoning,math,coding",
        "is_featured": True,
        "description": "DeepSeek 强化学习推理旗舰模型，对标 OpenAI o1"
    },
    {
        "model_id": "deepseek-reasoner",
        "name": "DeepSeek Reasoner (官方推理别名)",
        "provider": "deepseek",
        "series": "DeepSeek-R1",
        "context_window": 64000,
        "max_output": 8192,
        "official_input_price": 0.55,
        "official_output_price": 2.19,
        "official_cache_price": 0.14,
        "modalities": "text",
        "capabilities": "reasoning,chain_of_thought",
        "is_featured": True,
        "description": "DeepSeek 官方 API 默认深度思考端点"
    },
    # Anthropic 系列
    {
        "model_id": "claude-3-5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "provider": "anthropic",
        "series": "Claude-3.5",
        "context_window": 200000,
        "max_output": 8192,
        "official_input_price": 3.00,
        "official_output_price": 15.00,
        "official_cache_price": 0.30,
        "modalities": "text,image",
        "capabilities": "vision,artifacts,computer_use,coding",
        "is_featured": True,
        "description": "Anthropic 编程与通用综合能力行业天花板"
    },
    {
        "model_id": "claude-3-5-haiku",
        "name": "Claude 3.5 Haiku",
        "provider": "anthropic",
        "series": "Claude-3.5",
        "context_window": 200000,
        "max_output": 8192,
        "official_input_price": 0.80,
        "official_output_price": 4.00,
        "official_cache_price": 0.08,
        "modalities": "text,image",
        "capabilities": "vision,fast_response",
        "is_featured": False,
        "description": "极速高性价比轻量级模型"
    },
    # OpenAI 系列
    {
        "model_id": "gpt-4o",
        "name": "GPT-4o (Omni 全能旗舰)",
        "provider": "openai",
        "series": "GPT-4o",
        "context_window": 128000,
        "max_output": 16384,
        "official_input_price": 2.50,
        "official_output_price": 10.00,
        "official_cache_price": 1.25,
        "modalities": "text,image,audio",
        "capabilities": "vision,tool_calling,structured_outputs",
        "is_featured": True,
        "description": "OpenAI 多模态旗舰模型，高智力与极速响应"
    },
    {
        "model_id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "openai",
        "series": "GPT-4o",
        "context_window": 128000,
        "max_output": 16384,
        "official_input_price": 0.15,
        "official_output_price": 0.60,
        "official_cache_price": 0.075,
        "modalities": "text,image",
        "capabilities": "vision,tool_calling,fast",
        "is_featured": True,
        "description": "高性价比轻量多模态模型，适合日常大吞吐场景"
    },
    {
        "model_id": "o1",
        "name": "OpenAI o1 (深度推理)",
        "provider": "openai",
        "series": "OpenAI o1",
        "context_window": 200000,
        "max_output": 100000,
        "official_input_price": 15.00,
        "official_output_price": 60.00,
        "official_cache_price": 7.50,
        "modalities": "text,image",
        "capabilities": "reasoning,deep_math,stem",
        "is_featured": True,
        "description": "OpenAI 复杂科学与数理推理旗舰"
    },
    # Google 系列
    {
        "model_id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "provider": "google",
        "series": "Gemini-1.5",
        "context_window": 2000000,
        "max_output": 8192,
        "official_input_price": 1.25,
        "official_output_price": 5.00,
        "official_cache_price": 0.30,
        "modalities": "text,image,audio,video",
        "capabilities": "2m_context,video_audio_understanding",
        "is_featured": True,
        "description": "200万超长上下文与全模态理解旗舰"
    },
    {
        "model_id": "gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "provider": "google",
        "series": "Gemini-1.5",
        "context_window": 1000000,
        "max_output": 8192,
        "official_input_price": 0.075,
        "official_output_price": 0.30,
        "official_cache_price": 0.01875,
        "modalities": "text,image,audio,video",
        "capabilities": "1m_context,ultra_fast",
        "is_featured": True,
        "description": "极速百万上下文与高频轻量模型"
    },
    # Alibaba 系列
    {
        "model_id": "qwen2.5-72b-instruct",
        "name": "Qwen 2.5 72B Instruct",
        "provider": "alibaba",
        "series": "Qwen-2.5",
        "context_window": 128000,
        "max_output": 8192,
        "official_input_price": 0.55,
        "official_output_price": 1.65,
        "official_cache_price": 0.10,
        "modalities": "text",
        "capabilities": "coding,math,tool_calling",
        "is_featured": True,
        "description": "阿里通义千问开源 72B 旗舰模型"
    },
    {
        "model_id": "qwen2.5-32b-instruct",
        "name": "Qwen 2.5 32B Instruct",
        "provider": "alibaba",
        "series": "Qwen-2.5",
        "context_window": 128000,
        "max_output": 8192,
        "official_input_price": 0.28,
        "official_output_price": 0.84,
        "official_cache_price": 0.05,
        "modalities": "text",
        "capabilities": "coding,fast",
        "is_featured": False,
        "description": "阿里通义千问 32B 高效通用模型"
    }
]

class ModelsDevSyncService:
    def __init__(self):
        self.api_urls = [
            "https://models.dev/api.json",
            "https://raw.githubusercontent.com/models-dev/models/main/models.json"
        ]
        self.last_sync_time: datetime | None = None

    async def init_default_models(self):
        """初始化官方标准模型库"""
        async with AsyncSessionLocal() as session:
            for item in FALLBACK_MODELS_CATALOG:
                stmt = select(ModelMetadata).where(ModelMetadata.model_id == item["model_id"])
                res = await session.execute(stmt)
                exist = res.scalar_one_or_none()
                if not exist:
                    model = ModelMetadata(
                        model_id=item["model_id"],
                        name=item["name"],
                        provider=item["provider"],
                        series=item["series"],
                        context_window=item["context_window"],
                        max_output=item["max_output"],
                        official_input_price=item["official_input_price"],
                        official_output_price=item["official_output_price"],
                        official_cache_price=item["official_cache_price"],
                        modalities=item["modalities"],
                        capabilities=item["capabilities"],
                        is_featured=item["is_featured"],
                        description=item["description"]
                    )
                    session.add(model)
                else:
                    exist.series = item["series"]
                    exist.name = item["name"]
            await session.commit()
        self.last_sync_time = datetime.utcnow()

    async def sync_from_models_dev(self) -> Dict[str, Any]:
        """真实发起 HTTP 请求从 models.dev 拉取全球官方模型规格与定价"""
        online_success = False
        parsed_count = 0

        for url in self.api_urls:
            try:
                print(f"[ModelsDevSync] Fetching real data from: {url}")
                async with httpx.AsyncClient(timeout=8.0) as client:
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        raw_data = resp.json()
                        models_list = raw_data if isinstance(raw_data, list) else (raw_data.get("models") or raw_data.get("data") or [])
                        
                        if models_list and len(models_list) > 0:
                            async with AsyncSessionLocal() as session:
                                for m in models_list:
                                    m_id = m.get("id") or m.get("name")
                                    if not m_id:
                                        continue
                                    
                                    provider = m.get("provider") or m.get("organization") or "other"
                                    series = infer_model_series(m_id, provider)

                                    pricing = m.get("pricing") or {}
                                    in_price = float(pricing.get("prompt") or pricing.get("input") or 0.0)
                                    out_price = float(pricing.get("completion") or pricing.get("output") or 0.0)
                                    cache_price = float(pricing.get("cache_read") or (in_price * 0.5 if in_price > 0 else 0.0))
                                    
                                    stmt = select(ModelMetadata).where(ModelMetadata.model_id == m_id)
                                    res = await session.execute(stmt)
                                    exist = res.scalar_one_or_none()
                                    if exist:
                                        if in_price > 0:
                                            exist.official_input_price = in_price
                                        if out_price > 0:
                                            exist.official_output_price = out_price
                                        exist.series = series
                                        exist.updated_at = datetime.utcnow()
                                    else:
                                        new_model = ModelMetadata(
                                            model_id=m_id,
                                            name=m.get("display_name") or m.get("name") or m_id,
                                            provider=provider,
                                            series=series,
                                            context_window=int(m.get("context_window") or m.get("max_input_tokens") or 128000),
                                            max_output=int(m.get("max_output") or m.get("max_tokens") or 4096),
                                            official_input_price=in_price,
                                            official_output_price=out_price,
                                            official_cache_price=cache_price,
                                            modalities="text",
                                            capabilities="tool_calling",
                                            is_featured=False,
                                            description=m.get("description") or f"models.dev 标准模型 {m_id}"
                                        )
                                        session.add(new_model)
                                    parsed_count += 1
                                await session.commit()
                            online_success = True
                            print(f"[ModelsDevSync] Successfully parsed and updated {parsed_count} models from online API.")
                            break
            except Exception as e:
                print(f"[ModelsDevSync] Network fetch error for {url}: {e}")

        if not online_success:
            print("[ModelsDevSync] Online fetch failed, keeping local fallback models catalog.")
            await self.init_default_models()
            parsed_count = len(FALLBACK_MODELS_CATALOG)

        self.last_sync_time = datetime.utcnow()
        return {
            "status": "success",
            "is_online": online_success,
            "models_count": parsed_count,
            "timestamp": self.last_sync_time.isoformat()
        }

models_dev_sync = ModelsDevSyncService()
