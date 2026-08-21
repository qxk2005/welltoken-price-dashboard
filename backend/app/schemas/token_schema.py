from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- 模型元数据相关 ---
class ModelMetadataBase(BaseModel):
    model_id: str
    name: str
    provider: str
    series: str = ""
    family: str = ""
    context_window: int = 128000
    max_output: int = 4096
    official_input_price: float = 0.0
    official_output_price: float = 0.0
    official_cache_price: float = 0.0
    modalities: str = "text"
    capabilities: str = "tool_calling"
    open_weights: bool = False
    release_date: str = ""
    is_featured: bool = False
    description: str = ""

class ModelMetadataCreate(ModelMetadataBase):
    pass

class ModelMetadataSchema(ModelMetadataBase):
    id: int
    created_at: datetime
    updated_at: datetime
    active_relay_count: int = 0
    lowest_price_usd: float = 0.0

    class Config:
        from_attributes = True

# --- 供应商与渠道相关 ---
class RelaySiteBase(BaseModel):
    provider_id: Optional[str] = ""
    name: str
    base_url: str
    site_type: str = "official" # official, cloud, newapi, sub2api, oneapi, custom
    group_name: Optional[str] = "" # 渠道绑定的结算分组 (如 deepseek-三方, vip)
    currency: str = "CNY" # 渠道结算货币 (CNY 或 USD)
    recharge_rate: float = 1.0
    models_endpoint: str = "/v1/models"
    status_endpoint: str = ""
    website: Optional[str] = ""
    doc_url: Optional[str] = ""
    env_vars: Optional[str] = ""
    is_official_catalog: bool = False
    is_active: bool = True
    notes: Optional[str] = ""

class RelaySiteCreate(RelaySiteBase):
    api_key: Optional[str] = ""

class RelaySiteUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    site_type: Optional[str] = None
    group_name: Optional[str] = None
    currency: Optional[str] = None
    recharge_rate: Optional[float] = None
    models_endpoint: Optional[str] = None
    status_endpoint: Optional[str] = None
    website: Optional[str] = None
    doc_url: Optional[str] = None
    env_vars: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class ChannelChangeGroupRequest(BaseModel):
    group_name: str

class SiteModelPricingSchema(BaseModel):
    id: int
    site_id: int
    model_id: str
    group_name: Optional[str] = ""
    site_model_name: Optional[str] = ""
    model_ratio: float
    group_ratio: float
    calculated_input_usd: float
    calculated_output_usd: float
    calculated_cache_usd: float
    discount_percent: float
    is_available: bool
    updated_at: datetime

    class Config:
        from_attributes = True

class RelaySiteSchema(RelaySiteBase):
    id: int
    last_status: str
    last_latency_ms: float
    last_sync_time: datetime
    score: float
    created_at: datetime
    model_count: int = 0

    class Config:
        from_attributes = True

# --- 聚合比价矩阵条目与分页 ---
class ComparisonItemSchema(BaseModel):
    id: int
    model_id: str
    model_name: str
    provider: str
    series: str = ""
    site_id: int
    site_name: str
    group_name: Optional[str] = ""
    site_currency: str = "CNY" # 渠道的结算货币基准
    site_type: str
    is_official: bool
    model_ratio: float
    calculated_input_usd: float
    calculated_output_usd: float
    calculated_cache_usd: float
    calculated_input_cny: float
    calculated_output_cny: float
    discount_percent: float
    last_tested_tps: float
    site_score: float
    site_status: str
    last_latency_ms: float
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedComparisonResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[ComparisonItemSchema]

class FilterItemOption(BaseModel):
    value: str
    label: str
    count: int = 0

class ComparisonFilterOptionsResponse(BaseModel):
    providers: List[FilterItemOption]
    series: List[FilterItemOption]
    models: List[FilterItemOption]
    sites: List[FilterItemOption]


# --- 测速请求与结果 ---
class SpeedTestRequest(BaseModel):
    site_ids: List[int]
    model_id: str = "deepseek-v3"
    prompt_type: str = "standard" # standard, reasoning, code
    rounds: int = 1

class SpeedTestStreamEvent(BaseModel):
    event: str # start, token, done, error
    site_id: int
    site_name: str
    model_id: str
    current_token_count: int = 0
    current_ttft_ms: float = 0.0
    current_tps: float = 0.0
    instant_tps: float = 0.0
    content_delta: Optional[str] = ""
    is_authentic: Optional[bool] = True

class SpeedTestResultSchema(BaseModel):
    id: int
    site_id: int
    site_name: str
    site_type: str
    model_id: str
    test_time: datetime
    ttft_ms: float
    avg_tps: float
    peak_tps: float
    total_latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    is_success: bool
    error_message: str = ""
    is_authentic: bool
    jitter_rate: float
    score: float
    grade: str

    class Config:
        from_attributes = True

# --- 同步日志与设置 ---
class SyncLogSchema(BaseModel):
    id: int
    source: str
    sync_type: str
    status: str
    models_count: int
    providers_count: int
    pricings_count: int
    duration_ms: float
    error_message: str = ""
    created_at: datetime

    class Config:
        from_attributes = True

class SyncStatusSchema(BaseModel):
    models_dev_last_sync: Optional[datetime] = None
    models_dev_total_models: int = 0
    relays_last_sync: Optional[datetime] = None
    total_active_sites: int = 0
    total_pricings_cached: int = 0
    usd_to_cny_rate: float = 7.30
    db_size_mb: float = 0.0
    recent_sync_logs: List[SyncLogSchema] = []

class ExchangeRateUpdate(BaseModel):
    usd_to_cny_rate: float

class SystemHealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str = "1.0.0"
    uptime_seconds: float
    database_connected: bool

# --- 渠道向导与模型映射体系 Schemas ---
class ChannelProbeRequest(BaseModel):
    base_url: str
    api_key: Optional[str] = ""
    site_type: str = "newapi"
    models_endpoint: str = "/v1/models"
    target_group: Optional[str] = None

class ModelMappingItem(BaseModel):
    channel_model_name: str
    group_name: str = "default" # 该条目归属的具体渠道分组 (如 deepseek-三方, vip)
    item_key: str = "" # 唯一键 model_name::group_name
    is_matched: bool = False
    match_type: str = "unmapped" # exact, channel_custom, global_alias, rule_normalized, fuzzy, unmapped
    confidence: float = 0.0
    standard_model_id: str = ""
    standard_model_name: str = ""
    provider: str = ""
    series: str = ""
    official_input_price: float = 0.0
    official_output_price: float = 0.0
    official_cache_price: float = 0.0
    custom_ratio: Optional[float] = None
    public_ratio: Optional[float] = None
    key_ratio: Optional[float] = None
    has_ratio_diff: bool = False
    ratio_diff_percent: Optional[float] = None
    applied_ratio_source: str = "key" # key, public, custom
    is_selected: bool = True
    # 实际货币交易金额 (每 1M Tokens，精确计算)
    input_price_cny: float = 0.0
    output_price_cny: float = 0.0
    cache_price_cny: float = 0.0
    input_price_usd: float = 0.0
    output_price_usd: float = 0.0
    cache_price_usd: float = 0.0
    enable_groups: List[str] = []
    group_pricings: Dict[str, Any] = {}

class ChannelProbeResponse(BaseModel):
    is_online: bool
    status_code: int
    latency_ms: float
    raw_count: int
    matched_count: int
    unmatched_count: int
    fetch_source: str = ""
    token_group: str = ""
    token_group_ratio: Optional[float] = None
    has_special_pricing: bool = False
    special_pricing_count: int = 0
    available_groups: List[Dict[str, Any]] = []
    selected_group: str = ""
    currency: str = "CNY"
    error: str = ""
    mappings: List[ModelMappingItem] = []

class ChannelWizardCreateRequest(BaseModel):
    name: str
    base_url: str
    api_key: Optional[str] = ""
    site_type: str = "newapi"
    currency: str = "CNY" # 渠道结算货币 (CNY 或 USD)
    selected_group: Optional[str] = ""
    recharge_rate: float = 1.0
    default_ratio: float = 0.65
    models_endpoint: str = "/v1/models"
    status_endpoint: Optional[str] = ""
    notes: Optional[str] = ""
    mappings: List[ModelMappingItem] = []

class ChannelModelMappingSchema(BaseModel):
    id: int
    site_id: int
    channel_model_name: str
    standard_model_id: str
    custom_ratio: Optional[float] = None
    is_enabled: bool = True
    created_at: datetime

    class Config:
        from_attributes = True

class ChannelMappingsBatchUpdate(BaseModel):
    mappings: List[ModelMappingItem]

class PromoteAliasRequest(BaseModel):
    raw_pattern: str
    standard_model_id: str
    notes: Optional[str] = ""

