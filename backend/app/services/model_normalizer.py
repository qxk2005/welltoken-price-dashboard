import re
import fnmatch
import httpx
import time
from typing import List, Dict, Any, Optional, Tuple, Set
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import ModelMetadata, ModelAlias, ChannelModelMapping, RelaySite

# 内置高频常见别名映射种子库 (渠道混乱命名 -> 标准 models.dev model_id)
BUILTIN_SYSTEM_ALIASES = [
    # DeepSeek 核心映射
    {"pattern": "deepseek-chat", "standard": "deepseek-v3", "notes": "DeepSeek 官方 chat 别名默认指向 V3"},
    {"pattern": "deepseek-reasoner", "standard": "deepseek-r1", "notes": "DeepSeek 官方 reasoner 别名默认指向 R1"},
    {"pattern": "deepseek-ai/deepseek-v3", "standard": "deepseek-v3", "notes": "第三方平台厂商前缀剥离"},
    {"pattern": "deepseek-ai/deepseek-r1", "standard": "deepseek-r1", "notes": "第三方平台厂商前缀剥离"},
    {"pattern": "deepseek/deepseek-chat", "standard": "deepseek-v3", "notes": "OpenRouter 等平台前缀"},
    {"pattern": "deepseek/deepseek-r1", "standard": "deepseek-r1", "notes": "OpenRouter 等平台前缀"},

    # Anthropic Claude 映射 (剥离日期与 latest 后缀)
    {"pattern": "claude-3-5-sonnet-20241022", "standard": "claude-3-5-sonnet", "notes": "Sonnet 20241022 新版"},
    {"pattern": "claude-3-5-sonnet-20240620", "standard": "claude-3-5-sonnet", "notes": "Sonnet 20240620 初版"},
    {"pattern": "claude-3-5-sonnet-latest", "standard": "claude-3-5-sonnet", "notes": "Sonnet 最新动态别名"},
    {"pattern": "claude-3.5-sonnet", "standard": "claude-3-5-sonnet", "notes": "点号命名转换为短横线"},
    {"pattern": "claude-3.5-sonnet-20241022", "standard": "claude-3-5-sonnet", "notes": "点号与日期结合命名"},
    {"pattern": "claude-3-5-haiku-20241022", "standard": "claude-3-5-haiku", "notes": "Haiku 20241022 版本"},
    {"pattern": "claude-3-5-haiku-latest", "standard": "claude-3-5-haiku", "notes": "Haiku 最新动态别名"},
    {"pattern": "claude-3.5-haiku", "standard": "claude-3-5-haiku", "notes": "点号命名转换为短横线"},
    {"pattern": "claude-3-opus-20240229", "standard": "claude-3-opus", "notes": "Opus 20240229 版本"},
    {"pattern": "claude-3-opus-latest", "standard": "claude-3-opus", "notes": "Opus 最新动态别名"},
    {"pattern": "claude-3-sonnet-20240229", "standard": "claude-3-sonnet", "notes": "初代 Sonnet"},
    {"pattern": "claude-3-haiku-20240307", "standard": "claude-3-haiku", "notes": "初代 Haiku"},
    {"pattern": "anthropic/claude-3-5-sonnet", "standard": "claude-3-5-sonnet", "notes": "Anthropic 平台前缀"},
    {"pattern": "anthropic/claude-3-5-haiku", "standard": "claude-3-5-haiku", "notes": "Anthropic 平台前缀"},

    # OpenAI GPT / O 系列映射
    {"pattern": "gpt-4o-2024-05-13", "standard": "gpt-4o", "notes": "GPT-4o 初始版本"},
    {"pattern": "gpt-4o-2024-08-06", "standard": "gpt-4o", "notes": "GPT-4o 降价稳定版"},
    {"pattern": "gpt-4o-2024-11-20", "standard": "gpt-4o", "notes": "GPT-4o 1120 版"},
    {"pattern": "gpt-4o-all", "standard": "gpt-4o", "notes": "中转站全功能 4o 别名"},
    {"pattern": "chatgpt-4o-latest", "standard": "gpt-4o", "notes": "OpenAI 官方最新动态别名"},
    {"pattern": "gpt-4o-mini-2024-07-18", "standard": "gpt-4o-mini", "notes": "GPT-4o-mini 初始版"},
    {"pattern": "gpt-4-turbo-2024-04-09", "standard": "gpt-4-turbo", "notes": "GPT-4 Turbo Vision 稳定版"},
    {"pattern": "gpt-4-turbo-preview", "standard": "gpt-4-turbo", "notes": "GPT-4 Turbo 预览版"},
    {"pattern": "gpt-4-0125-preview", "standard": "gpt-4-turbo", "notes": "GPT-4 Turbo 0125 版"},
    {"pattern": "gpt-4-1106-preview", "standard": "gpt-4-turbo", "notes": "GPT-4 Turbo 1106 版"},
    {"pattern": "o1-preview-2024-09-12", "standard": "o1-preview", "notes": "o1-preview 初始版"},
    {"pattern": "o1-mini-2024-09-12", "standard": "o1-mini", "notes": "o1-mini 初始版"},
    {"pattern": "o3-mini-2025-01-31", "standard": "o3-mini", "notes": "o3-mini 初始版"},
    {"pattern": "openai/gpt-4o", "standard": "gpt-4o", "notes": "OpenAI 平台前缀"},
    {"pattern": "openai/o1", "standard": "o1", "notes": "OpenAI 平台前缀"},
    {"pattern": "openai/o3-mini", "standard": "o3-mini", "notes": "OpenAI 平台前缀"},

    # Google Gemini 映射
    {"pattern": "gemini-1.5-pro-latest", "standard": "gemini-1.5-pro", "notes": "Gemini 1.5 Pro 动态别名"},
    {"pattern": "gemini-1.5-pro-001", "standard": "gemini-1.5-pro", "notes": "Gemini 1.5 Pro 001版"},
    {"pattern": "gemini-1.5-pro-002", "standard": "gemini-1.5-pro", "notes": "Gemini 1.5 Pro 002版"},
    {"pattern": "gemini-1.5-flash-latest", "standard": "gemini-1.5-flash", "notes": "Gemini 1.5 Flash 动态别名"},
    {"pattern": "gemini-1.5-flash-001", "standard": "gemini-1.5-flash", "notes": "Gemini 1.5 Flash 001版"},
    {"pattern": "gemini-1.5-flash-002", "standard": "gemini-1.5-flash", "notes": "Gemini 1.5 Flash 002版"},
    {"pattern": "gemini-2.0-flash-exp", "standard": "gemini-2.0-flash", "notes": "Gemini 2.0 Flash 实验版"},
    {"pattern": "gemini-2.0-flash-thinking-exp*", "standard": "gemini-2.0-flash-thinking", "notes": "Gemini 2.0 思考版"},
    {"pattern": "google/gemini-1.5-pro", "standard": "gemini-1.5-pro", "notes": "Google 平台前缀"},

    # 阿里通义千问 Qwen 映射
    {"pattern": "qwen-plus-latest", "standard": "qwen-plus", "notes": "通义千问 Plus 最新版"},
    {"pattern": "qwen-turbo-latest", "standard": "qwen-turbo", "notes": "通义千问 Turbo 最新版"},
    {"pattern": "qwen-max-latest", "standard": "qwen-max", "notes": "通义千问 Max 最新版"},
    {"pattern": "qwen/qwen-2.5-72b-instruct", "standard": "qwen2.5-72b-instruct", "notes": "Qwen 开源型号前缀剥离"},
    {"pattern": "qwen2.5-72b", "standard": "qwen2.5-72b-instruct", "notes": "Qwen2.5 简写"},
]

class ModelNormalizerService:
    def __init__(self):
        self._cached_aliases: List[Dict[str, Any]] = []
        self._cached_standard_models: Dict[str, ModelMetadata] = {}
        self._is_initialized = False

    async def initialize(self):
        """初始化加载标准模型库与别名规则库"""
        async with AsyncSessionLocal() as session:
            # 1. 确保内置规则已插入数据库
            for item in BUILTIN_SYSTEM_ALIASES:
                stmt = select(ModelAlias).where(ModelAlias.raw_pattern == item["pattern"])
                res = await session.execute(stmt)
                alias = res.scalar_one_or_none()
                if not alias:
                    alias = ModelAlias(
                        raw_pattern=item["pattern"],
                        standard_model_id=item["standard"],
                        is_system=True,
                        notes=item.get("notes", "")
                    )
                    session.add(alias)
            await session.commit()

            # 2. 缓存所有标准模型
            m_res = await session.execute(select(ModelMetadata))
            self._cached_standard_models = {m.model_id: m for m in m_res.scalars().all()}

            # 3. 缓存别名规则
            a_res = await session.execute(select(ModelAlias))
            self._cached_aliases = [
                {
                    "id": a.id,
                    "pattern": a.raw_pattern.lower(),
                    "standard": a.standard_model_id,
                    "is_system": a.is_system
                }
                for a in a_res.scalars().all()
            ]

        self._is_initialized = True

    def normalize_string(self, raw_name: str) -> str:
        """剥离常见平台前缀、日期后缀与特殊标点，得到规范候选名称"""
        if not raw_name:
            return ""
        name = raw_name.strip().lower()

        # 1. 剥离平台/组织前缀 (如 "openai/gpt-4o" -> "gpt-4o", "anthropic/claude..." -> "claude...")
        prefix_pattern = r"^(openai|anthropic|google|deepseek|deepseek-ai|meta-llama|qwen|alibaba|aliyun|together|groq|openrouter|mistralai|zhipuai|moonshotai|bytedance|tencent|baichuan|stepfun|xiaomi|microsoft|cohere|xai|minimax)\/"
        name = re.sub(prefix_pattern, "", name)

        # 2. 点号命名替换为破折号 (如 "claude-3.5-sonnet" -> "claude-3-5-sonnet")
        name = re.sub(r"(\d+)\.(\d+)", r"\1-\2", name)

        # 3. 剥离常见动态别名后缀 (如 "-latest", "-preview", "-all")
        name = re.sub(r"-(latest|preview|all|chat|instruct)$", "", name)

        # 4. 剥离常见 8 位或 YYYY-MM-DD 形式日期后缀 (如 "-20241022", "-2024-08-06", "-0125", "-1106")
        name = re.sub(r"-\d{4}-\d{2}-\d{2}$", "", name) # -2024-08-06
        name = re.sub(r"-\d{8}$", "", name)             # -20241022
        name = re.sub(r"-\d{4}$", "", name)               # -0125

        return name

    def extract_root_url(self, url: str) -> str:
        """从用户输入的 Base URL 中自动提取纯根域名 (如 https://domain.com/v1 -> https://domain.com)"""
        clean = url.strip().rstrip("/")
        # 剥离常见的 /v1, /api, /v1beta 等后缀
        clean = re.sub(r"/(v1|v1beta|api|v2)$", "", clean)
        return clean.rstrip("/")

    async def probe_and_fetch_models(
        self,
        base_url: str,
        api_key: str = "",
        site_type: str = "newapi",
        models_endpoint: str = "/v1/models"
    ) -> Dict[str, Any]:
        """使用 relay-watch 智能全量探测链：自动提取根域，优先免 Key 请求公开 JSON (/api/pricing, /api/models)，提取全量模型与真实倍率"""
        start_t = time.time()
        is_online = False
        status_code = 0
        real_latency_ms = 0.0
        raw_models: List[str] = []
        raw_ratios: Dict[str, float] = {}
        fetch_source = ""
        error_msg = ""

        clean_base = base_url.strip().rstrip("/")
        root_url = self.extract_root_url(clean_base)

        headers_no_auth = {
            "User-Agent": "WellToken-Dashboard/1.0.0 (Relay-Probe; +https://models.dev)"
        }
        headers_with_auth = {
            "User-Agent": "WellToken-Dashboard/1.0.0 (Relay-Probe; +https://models.dev)"
        }
        if api_key:
            headers_with_auth["Authorization"] = f"Bearer {api_key}"

        # -------------------------------------------------------------
        # Phase 1: 优先探测公开端点 (免 Key，获取未受限全量模型及官方倍率)
        # -------------------------------------------------------------
        public_probe_targets = [
            # 1. NewAPI / OneAPI 全量定价接口 (最权威：包含全量模型与真实倍率 model_ratio)
            {"url": f"{root_url}/api/pricing", "auth": False, "source": "/api/pricing (免Key全量定价)"},
            # 2. NewAPI / OneAPI 公开模型列表接口
            {"url": f"{root_url}/api/models", "auth": False, "source": "/api/models (免Key公开模型)"},
            # 3. Sub2API 公开模型端点
            {"url": f"{root_url}/api/user/models", "auth": False, "source": "/api/user/models (Sub2API公开)"},
            {"url": f"{root_url}/api/public/models", "auth": False, "source": "/api/public/models (Sub2API公开)"},
            # 4. Status 接口
            {"url": f"{root_url}/api/status", "auth": False, "source": "/api/status (公开状态)"}
        ]

        async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
            for target in public_probe_targets:
                try:
                    resp = await client.get(target["url"], headers=headers_no_auth)
                    status_code = resp.status_code
                    real_latency_ms = round((time.time() - start_t) * 1000, 1)

                    if resp.status_code == 200:
                        is_online = True
                        data = resp.json()
                        raw_list = data if isinstance(data, list) else (data.get("data") or data.get("models") or [])
                        
                        # 解析 pricing 格式（带有 model_name 与 model_ratio）
                        for item in raw_list:
                            if isinstance(item, dict):
                                m_name = item.get("model_name") or item.get("id") or item.get("name")
                                m_ratio = item.get("model_ratio")
                                if m_ratio is not None:
                                    try:
                                        raw_ratios[str(m_name).strip().lower()] = float(m_ratio)
                                    except (ValueError, TypeError):
                                        pass
                            elif isinstance(item, str):
                                m_name = item
                            else:
                                m_name = None

                            if m_name and isinstance(m_name, str):
                                raw_models.append(m_name.strip())

                        if raw_models:
                            fetch_source = target["source"]
                            break # 成功免 Key 获取到全量模型
                except Exception as e:
                    pass

        # -------------------------------------------------------------
        # Phase 2: 若公开端点无法获取，回退探测鉴权端点 (需要有效的 API Key)
        # -------------------------------------------------------------
        if not raw_models:
            auth_probe_targets = [
                {"url": f"{clean_base}/models", "auth": True, "source": f"{clean_base}/models (令牌权限)"},
                {"url": f"{clean_base}/v1/models" if not clean_base.endswith("/v1") else f"{clean_base}/models", "auth": True, "source": "/v1/models (令牌权限)"},
                {"url": f"{root_url}/v1/models", "auth": True, "source": "/v1/models (令牌权限)"}
            ]

            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                for target in auth_probe_targets:
                    try:
                        resp = await client.get(target["url"], headers=headers_with_auth)
                        status_code = resp.status_code
                        real_latency_ms = round((time.time() - start_t) * 1000, 1)

                        if resp.status_code == 200:
                            is_online = True
                            data = resp.json()
                            raw_list = data if isinstance(data, list) else (data.get("data") or data.get("models") or [])
                            for item in raw_list:
                                if isinstance(item, dict):
                                    m_id = item.get("id") or item.get("name") or item.get("model_name")
                                elif isinstance(item, str):
                                    m_id = item
                                else:
                                    m_id = None
                                if m_id and isinstance(m_id, str):
                                    raw_models.append(m_id.strip())
                            if raw_models:
                                fetch_source = target["source"]
                                break
                        elif resp.status_code == 401:
                            is_online = True
                            error_msg = "端点连通，但公开端点未开放，且 API Key 无效或未提供 (HTTP 401)"
                    except Exception as e:
                        error_msg = str(e)
                        real_latency_ms = round((time.time() - start_t) * 1000, 1)

        # 去重模型列表
        seen_m = set()
        unique_raw_models = [m for m in raw_models if not (m.lower() in seen_m or seen_m.add(m.lower()))]

        return {
            "is_online": is_online,
            "status_code": status_code,
            "latency_ms": real_latency_ms,
            "raw_models": unique_raw_models,
            "raw_count": len(unique_raw_models),
            "raw_ratios": raw_ratios,
            "fetch_source": fetch_source or ("公开/鉴权端点均无响应" if not is_online else "未获取到模型列表"),
            "error": error_msg
        }

    async def match_models_for_channel(
        self,
        raw_model_names: List[str],
        site_id: Optional[int] = None,
        raw_ratios: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """为渠道的一批原始模型名称执行两层智能映射匹配，并自动应用提取到的原生模型倍率"""
        if not self._is_initialized:
            await self.initialize()

        raw_ratios_map = raw_ratios or {}

        # 1. 如果指定了 site_id，先读取该渠道现存的专属映射表
        channel_mappings: Dict[str, ChannelModelMapping] = {}
        if site_id:
            async with AsyncSessionLocal() as session:
                cm_stmt = select(ChannelModelMapping).where(ChannelModelMapping.site_id == site_id)
                cm_res = await session.execute(cm_stmt)
                for cm in cm_res.scalars().all():
                    channel_mappings[cm.channel_model_name.lower()] = cm

        results = []
        for raw in raw_model_names:
            raw_clean = raw.strip()
            raw_lower = raw_clean.lower()

            matched_standard_id: Optional[str] = None
            match_type = "unmapped"  # exact, channel_custom, global_alias, rule_normalized, fuzzy, unmapped
            confidence = 0.0
            custom_ratio = None

            # Level 1: 检查渠道私有映射 (最高优先级)
            if raw_lower in channel_mappings:
                cm = channel_mappings[raw_lower]
                matched_standard_id = cm.standard_model_id
                match_type = "channel_custom"
                confidence = 1.0
                custom_ratio = cm.custom_ratio

            # 如果渠道没有私有指定倍率，尝试从探测到的公开原生倍率中提取
            if custom_ratio is None and raw_lower in raw_ratios_map:
                custom_ratio = raw_ratios_map[raw_lower]

            # Level 2: 检查全局别名库 (ModelAlias 精确模式或通配符规则，强制将混乱别名归一化到旗舰标准模型)
            if not matched_standard_id:
                for alias in self._cached_aliases:
                    pat = alias["pattern"]
                    if pat == raw_lower or fnmatch.fnmatch(raw_lower, pat):
                        matched_standard_id = alias["standard"]
                        match_type = "global_alias"
                        confidence = 0.95
                        break

            # Level 3: 检查是否与 models.dev 标准库直接精确一致 (Exact match)
            if not matched_standard_id and raw_lower in self._cached_standard_models:
                matched_standard_id = raw_lower
                match_type = "exact"
                confidence = 1.0

            # Level 4: 规则自动剥离归一化 (Rule Normalization 剥离厂商前缀、日期后缀与标点)
            if not matched_standard_id:
                normalized = self.normalize_string(raw_lower)
                # 再次检查归一化后的名称是否命中全局别名
                for alias in self._cached_aliases:
                    pat = alias["pattern"]
                    if pat == normalized or fnmatch.fnmatch(normalized, pat):
                        matched_standard_id = alias["standard"]
                        match_type = "global_alias"
                        confidence = 0.92
                        break

                if not matched_standard_id and normalized and normalized in self._cached_standard_models:
                    matched_standard_id = normalized
                    match_type = "rule_normalized"
                    confidence = 0.88
                elif not matched_standard_id:
                    # Level 5: 尝试前缀包含模糊匹配 (如 deepseek-v3-0328 包含 deepseek-v3)
                    for std_id in self._cached_standard_models.keys():
                        if std_id in normalized or normalized in std_id:
                            matched_standard_id = std_id
                            match_type = "fuzzy"
                            confidence = 0.70
                            break

            # 组装返回条目
            std_meta = self._cached_standard_models.get(matched_standard_id) if matched_standard_id else None
            
            results.append({
                "channel_model_name": raw_clean,
                "is_matched": bool(matched_standard_id),
                "match_type": match_type,
                "confidence": confidence,
                "standard_model_id": matched_standard_id or "",
                "standard_model_name": std_meta.name if std_meta else "",
                "provider": std_meta.provider if std_meta else "",
                "series": std_meta.series if std_meta else "",
                "official_input_price": std_meta.official_input_price if std_meta else 0.0,
                "official_output_price": std_meta.official_output_price if std_meta else 0.0,
                "custom_ratio": custom_ratio,
                "is_selected": bool(matched_standard_id) # 已匹配的默认勾选，未匹配的默认不勾选
            })

        return results

model_normalizer = ModelNormalizerService()
