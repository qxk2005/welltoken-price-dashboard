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

    def parse_billing_expr(self, expr: str) -> Dict[str, float]:
        """解析 NewAPI 的阶梯计费表达式 (billing_expr)，精确提取 p (输入), c (输出), cr (缓存读), cc (缓存写) 系数"""
        coeffs = {"p": 0.0, "c": 0.0, "cr": 0.0, "cc": 0.0}
        if not expr:
            return coeffs

        # 匹配 p * 0.2054794520547 或 p*0.2
        p_match = re.search(r"p\s*\*\s*([\d\.]+)", expr)
        if p_match:
            try:
                coeffs["p"] = float(p_match.group(1))
            except ValueError:
                pass

        c_match = re.search(r"c\s*\*\s*([\d\.]+)", expr)
        if c_match:
            try:
                coeffs["c"] = float(c_match.group(1))
            except ValueError:
                pass

        cr_match = re.search(r"cr\s*\*\s*([\d\.]+)", expr)
        if cr_match:
            try:
                coeffs["cr"] = float(cr_match.group(1))
            except ValueError:
                pass

        cc_match = re.search(r"cc\s*\*\s*([\d\.]+)", expr)
        if cc_match:
            try:
                coeffs["cc"] = float(cc_match.group(1))
            except ValueError:
                pass

        return coeffs

    async def probe_and_fetch_models(
        self,
        base_url: str,
        api_key: str = "",
        site_type: str = "newapi",
        models_endpoint: str = "/v1/models",
        target_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """使用 relay-watch 智能全量探测链：解析多分组、提取阶梯表达式精确价格、比对 Key 专属倍率"""
        start_t = time.time()
        is_online = False
        status_code = 0
        real_latency_ms = 0.0
        raw_models: List[str] = []
        raw_public_ratios: Dict[str, float] = {}
        raw_key_ratios: Dict[str, float] = {}
        fetch_source = ""
        error_msg = ""

        token_group = ""
        token_group_ratio = None
        global_group_ratios: Dict[str, float] = {"default": 1.0}
        raw_model_items: List[Dict[str, Any]] = []

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
        # Phase 0: 若提供了 API Key，先尝试嗅探该 Key 的用户分组与特权信息
        # -------------------------------------------------------------
        if api_key:
            group_probe_endpoints = [
                f"{root_url}/api/user/self",
                f"{root_url}/dashboard/billing/subscription",
                f"{root_url}/api/token"
            ]
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                for ep in group_probe_endpoints:
                    try:
                        g_resp = await client.get(ep, headers=headers_with_auth)
                        if g_resp.status_code == 200:
                            g_data = g_resp.json()
                            u_data = g_data.get("data") if isinstance(g_data, dict) else None
                            if isinstance(u_data, dict):
                                token_group = str(u_data.get("group") or u_data.get("user_group") or "").strip()
                            elif isinstance(g_data, dict):
                                token_group = str(g_data.get("group") or g_data.get("user_group") or "").strip()
                            if token_group:
                                break
                    except Exception:
                        pass

        # -------------------------------------------------------------
        # Phase 1: 优先探测公开端点 (免 Key，获取未受限全量模型及官方倍率)
        # -------------------------------------------------------------
        public_probe_targets = [
            # 1. NewAPI / OneAPI 全量定价接口 (最权威：包含全量模型与各分组倍率 group_ratio)
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
                        if isinstance(data, dict) and "group_ratio" in data and isinstance(data["group_ratio"], dict):
                            for g_k, g_v in data["group_ratio"].items():
                                try:
                                    global_group_ratios[str(g_k).strip()] = float(g_v)
                                except (ValueError, TypeError):
                                    pass

                        raw_model_items = raw_list if isinstance(raw_list, list) else []

                        for item in raw_model_items:
                            if isinstance(item, dict):
                                m_name = item.get("model_name") or item.get("id") or item.get("name")
                                m_ratio = item.get("model_ratio")
                                item_group_ratios = item.get("group_ratio") or {}
                                if isinstance(item_group_ratios, dict):
                                    for g_k, g_v in item_group_ratios.items():
                                        try:
                                            global_group_ratios[str(g_k).strip()] = float(g_v)
                                        except (ValueError, TypeError):
                                            pass

                                if m_ratio is not None:
                                    try:
                                        p_ratio = float(m_ratio)
                                        m_key = str(m_name).strip().lower()
                                        raw_public_ratios[m_key] = p_ratio

                                        # 计算 Key 专属倍率
                                        if token_group and token_group in global_group_ratios:
                                            g_coeff = global_group_ratios[token_group]
                                            raw_key_ratios[m_key] = round(p_ratio * g_coeff, 4)
                                        else:
                                            raw_key_ratios[m_key] = p_ratio
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
                except Exception:
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
                            raw_model_items = raw_list if isinstance(raw_list, list) else []
                            for item in raw_model_items:
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

        # 汇总全部分组列表 available_groups
        groups_set: Set[str] = set()
        for item in raw_model_items:
            if isinstance(item, dict) and "enable_groups" in item and isinstance(item["enable_groups"], list):
                for g in item["enable_groups"]:
                    if g:
                        groups_set.add(str(g).strip())
        for g_k in global_group_ratios.keys():
            if g_k:
                groups_set.add(g_k)

        available_groups = []
        for g_name in sorted(list(groups_set)):
            g_ratio = global_group_ratios.get(g_name, 1.0)
            # 计算该分组下支持的模型数
            m_cnt = 0
            for item in raw_model_items:
                if isinstance(item, dict):
                    eg = item.get("enable_groups")
                    if not eg or (isinstance(eg, list) and (g_name in eg or not eg)):
                        m_cnt += 1
                else:
                    m_cnt += 1
            available_groups.append({
                "name": g_name,
                "ratio": g_ratio,
                "model_count": m_cnt if m_cnt > 0 else len(unique_raw_models)
            })

        # 确定当前选中的分组 selected_group
        selected_group = target_group or token_group or (available_groups[0]["name"] if available_groups else "default")
        selected_group_ratio = global_group_ratios.get(selected_group, 1.0)

        # 统计差异倍率模型数
        special_cnt = 0
        for m in unique_raw_models:
            m_low = m.lower()
            if m_low in raw_public_ratios and m_low in raw_key_ratios:
                if raw_public_ratios[m_low] != raw_key_ratios[m_low]:
                    special_cnt += 1

        return {
            "is_online": is_online,
            "status_code": status_code,
            "latency_ms": real_latency_ms,
            "raw_models": unique_raw_models,
            "raw_count": len(unique_raw_models),
            "raw_public_ratios": raw_public_ratios,
            "raw_key_ratios": raw_key_ratios,
            "raw_model_items": raw_model_items,
            "token_group": token_group,
            "token_group_ratio": global_group_ratios.get(token_group),
            "available_groups": available_groups,
            "selected_group": selected_group,
            "selected_group_ratio": selected_group_ratio,
            "global_group_ratios": global_group_ratios,
            "has_special_pricing": special_cnt > 0,
            "special_pricing_count": special_cnt,
            "fetch_source": fetch_source or ("公开/鉴权端点均无响应" if not is_online else "未获取到模型列表"),
            "error": error_msg
        }

    async def match_models_for_channel(
        self,
        raw_model_names: List[str],
        site_id: Optional[int] = None,
        raw_public_ratios: Optional[Dict[str, float]] = None,
        raw_key_ratios: Optional[Dict[str, float]] = None,
        raw_model_items: Optional[List[Dict[str, Any]]] = None,
        selected_group: str = "default",
        selected_group_ratio: float = 1.0,
        global_group_ratios: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """为渠道的一批原始模型名称执行两层智能映射匹配，并精确计算输入/输出/缓存的人民币与美元实际金额"""
        if not self._is_initialized:
            await self.initialize()

        public_map = raw_public_ratios or {}
        key_map = raw_key_ratios or {}
        group_ratios_map = global_group_ratios or {"default": 1.0}

        # 建立 raw_model_name -> item dict 快速索引
        items_by_name: Dict[str, Dict[str, Any]] = {}
        if raw_model_items:
            for it in raw_model_items:
                if isinstance(it, dict):
                    k = str(it.get("model_name") or it.get("id") or it.get("name") or "").strip().lower()
                    if k:
                        items_by_name[k] = it

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
            raw_item = items_by_name.get(raw_lower, {})

            matched_standard_id: Optional[str] = None
            match_type = "unmapped"
            confidence = 0.0
            custom_ratio = None

            # 获取公开与 Key 倍率
            p_ratio = public_map.get(raw_lower)
            k_ratio = key_map.get(raw_lower) if key_map else p_ratio
            has_diff = (p_ratio is not None and k_ratio is not None and p_ratio != k_ratio)
            diff_pct = None
            if has_diff and p_ratio and p_ratio > 0:
                diff_pct = round(((k_ratio - p_ratio) / p_ratio) * 100, 1)

            # Level 1: 检查渠道私有映射 (最高优先级)
            if raw_lower in channel_mappings:
                cm = channel_mappings[raw_lower]
                matched_standard_id = cm.standard_model_id
                match_type = "channel_custom"
                confidence = 1.0
                custom_ratio = cm.custom_ratio

            # 默认应用更优惠的 Key 倍率，若无则使用公开倍率
            if custom_ratio is None:
                custom_ratio = k_ratio if k_ratio is not None else p_ratio

            # Level 2: 检查全局别名库 (ModelAlias 精确模式或通配符规则)
            if not matched_standard_id:
                for alias in self._cached_aliases:
                    pat = alias["pattern"]
                    if pat == raw_lower or fnmatch.fnmatch(raw_lower, pat):
                        matched_standard_id = alias["standard"]
                        match_type = "global_alias"
                        confidence = 0.95
                        break

            # Level 3: 检查是否与 models.dev 标准库直接精确一致
            if not matched_standard_id and raw_lower in self._cached_standard_models:
                matched_standard_id = raw_lower
                match_type = "exact"
                confidence = 1.0

            # Level 4: 规则自动剥离归一化
            if not matched_standard_id:
                normalized = self.normalize_string(raw_lower)
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
                    for std_id in self._cached_standard_models.keys():
                        if std_id in normalized or normalized in std_id:
                            matched_standard_id = std_id
                            match_type = "fuzzy"
                            confidence = 0.70
                            break

            std_meta = self._cached_standard_models.get(matched_standard_id) if matched_standard_id else None

            # ---------------------------------------------------------
            # 精确计算实际货币金额 (输入、输出、缓存价格)
            # ---------------------------------------------------------
            billing_mode = raw_item.get("billing_mode", "")
            billing_expr = raw_item.get("billing_expr", "")
            enable_groups = raw_item.get("enable_groups") or []
            item_completion_ratio = float(raw_item.get("completion_ratio") or 1.0)
            item_cache_ratio = float(raw_item.get("cache_ratio") or 0.1)

            # 多分组价格集合
            group_pricings = {}
            for g_name, g_ratio_val in group_ratios_map.items():
                if billing_mode == "tiered_expr" and billing_expr:
                    coeffs = self.parse_billing_expr(billing_expr)
                    in_cny = round(coeffs["p"] * 7.3 * g_ratio_val, 4)
                    out_cny = round(coeffs["c"] * 7.3 * g_ratio_val, 4)
                    ca_cny = round(coeffs["cr"] * 7.3 * g_ratio_val, 4)
                else:
                    m_rat = float(raw_item.get("model_ratio") or p_ratio or 1.0)
                    if m_rat >= 5.0:
                        in_cny = round(m_rat * g_ratio_val, 4)
                    else:
                        in_cny = round(m_rat * 7.3 * g_ratio_val, 4)
                    out_cny = round(in_cny * item_completion_ratio, 4)
                    ca_cny = round(in_cny * item_cache_ratio, 4)

                group_pricings[g_name] = {
                    "group_name": g_name,
                    "group_ratio": g_ratio_val,
                    "input_price_cny": in_cny,
                    "output_price_cny": out_cny,
                    "cache_price_cny": ca_cny,
                    "input_price_usd": round(in_cny / 7.25, 4),
                    "output_price_usd": round(out_cny / 7.25, 4),
                    "cache_price_usd": round(ca_cny / 7.25, 4),
                }

            # 确定该模型所属的分组集合 groups_for_this_model
            # 若 raw_item 中包含 enable_groups 且不为空，则严格只生成属于这些启用分组的条目！
            groups_for_this_model = enable_groups if (enable_groups and len(enable_groups) > 0) else ["default"]

            for g_name in groups_for_this_model:
                g_pricing = group_pricings.get(g_name, {
                    "input_price_cny": 0.0, "output_price_cny": 0.0, "cache_price_cny": 0.0,
                    "input_price_usd": 0.0, "output_price_usd": 0.0, "cache_price_usd": 0.0
                })

                results.append({
                    "channel_model_name": raw_clean,
                    "group_name": g_name,
                    "item_key": f"{raw_clean}::{g_name}",
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
                    "public_ratio": p_ratio,
                    "key_ratio": k_ratio,
                    "has_ratio_diff": has_diff,
                    "ratio_diff_percent": diff_pct,
                    "applied_ratio_source": "key" if has_diff else "public",
                    "is_selected": bool(matched_standard_id),
                    "input_price_cny": g_pricing["input_price_cny"],
                    "output_price_cny": g_pricing["output_price_cny"],
                    "cache_price_cny": g_pricing["cache_price_cny"],
                    "input_price_usd": g_pricing["input_price_usd"],
                    "output_price_usd": g_pricing["output_price_usd"],
                    "cache_price_usd": g_pricing["cache_price_usd"],
                    "enable_groups": enable_groups,
                    "group_pricings": group_pricings
                })

        return results

model_normalizer = ModelNormalizerService()
