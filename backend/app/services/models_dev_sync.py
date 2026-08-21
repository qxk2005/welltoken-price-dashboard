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
            async with AsyncSessionLocal() as session:
                res = await session.execute(select(ModelMetadata))
                models = res.scalars().all()
                for m in models:
                    canonical_provider = infer_lab_provider(m.model_id, m.provider)
                    canonical_series = infer_model_series(m.model_id, canonical_provider, m.family)
                    m.provider = canonical_provider
                    m.series = canonical_series
                await session.commit()
                models_count = len(models)

            return {
                "status": "success",
                "models_count": models_count,
                "duration_ms": round((time.time() - start_t) * 1000, 2)
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }

models_dev_sync = ModelsDevSyncService()
