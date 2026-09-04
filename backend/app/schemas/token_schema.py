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
    api_key: Optional[str] = ""
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
    pass

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
    groups: List[str] = []
    group_count: int = 0

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
    official_model_id: Optional[int] = None
    official_model_name: Optional[str] = ""
    official_input_discount: Optional[float] = None
    official_output_discount: Optional[float] = None
    official_composite_discount: Optional[float] = None
    last_tested_tps: float
    site_score: float
    site_status: str
    last_latency_ms: float
    source_updated_at: Optional[str] = ""
    source_time_type: Optional[str] = "models_dev" # "models_dev" 或 "manual"
    is_official_catalog: bool = True
    site_model_name: Optional[str] = ""
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

# --- 渠道单点高精度性能压测 (Benchmark) ---
class ChannelBenchmarkRequest(BaseModel):
    site_id: int
    model_id: str
    custom_api_key: Optional[str] = ""
    custom_base_url: Optional[str] = ""
    rounds: int = 3
    concurrency: int = 1
    prompt_type: str = "standard"

class ExecutionDetailItem(BaseModel):
    round_index: int
    thread_id: str
    status_code: int = 200
    ttfb_ms: float = 0.0
    ttft_ms: float = 0.0
    itl_ms: float = 0.0 # Inter-Token Latency (毫秒)
    total_duration_s: float = 0.0 # 秒
    tps: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    response_content: str = ""
    is_success: bool = True
    error_msg: str = ""

class ChannelBenchmarkResponse(BaseModel):
    site_id: int
    site_name: str
    model_id: str
    total_rounds: int
    concurrency: int
    # 核心聚合统计 (Avg / Max / Min)
    avg_ttft_ms: float
    max_ttft_ms: float
    min_ttft_ms: float
    avg_ttfb_ms: float
    max_ttfb_ms: float
    min_ttfb_ms: float
    avg_tps: float
    max_tps: float
    min_tps: float
    avg_itl_ms: float
    max_itl_ms: float
    min_itl_ms: float
    avg_duration_s: float
    max_duration_s: float
    min_duration_s: float
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    jitter_ms: float
    score: float
    grade: str
    details: List[ExecutionDetailItem] = []

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
    exchange_rate_source: str = "https://open.er-api.com/v6/latest/USD"
    exchange_rate_updated_at: Optional[datetime] = None
    db_size_mb: float = 0.0
    recent_sync_logs: List[SyncLogSchema] = []

class ExchangeRateUpdate(BaseModel):
    usd_to_cny_rate: float
    exchange_rate_source: Optional[str] = None

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
    official_input_cny: float = 0.0
    official_output_cny: float = 0.0
    official_cache_cny: float = 0.0
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
    site_id: Optional[int] = None # 若提供则原地更新已有渠道配置与模型映射
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

# --- Token 实时行情与 K线/深度 Schema ---
class DepthLevel(BaseModel):
    price: float
    amount: float
    total: float

class OrderBookDepth(BaseModel):
    symbol: str
    timestamp: int
    bids: List[DepthLevel] = []
    asks: List[DepthLevel] = []

class KlinePoint(BaseModel):
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class TokenPriceSummary(BaseModel):
    symbol: str
    name: str
    price: float
    change_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    market_cap: float
    timestamp: datetime
    sparkline: List[float] = []


# --- 硅基流动 SiliconFlow 爬取相关 ---
class SiliconFlowPriceTier(BaseModel):
    """硅基流动分段定价条目"""
    tier_label: str = ""           # 价格段标签，如 "输入 [0, 32k)" 或 "输入 [32k, +∞)"
    input_price_cny: float = 0.0   # 该段输入价格 (¥/1M Tokens)
    output_price_cny: float = 0.0  # 该段输出价格 (¥/1M Tokens)
    cache_price_cny: float = 0.0   # 该段缓存价格 (¥/1M Tokens)

class SiliconFlowModelItem(BaseModel):
    """硅基流动爬取到的单个模型价格信息"""
    model_id: str                  # 完整模型 ID，如 deepseek-ai/DeepSeek-V4-Flash
    display_name: str              # 显示名称，如 DeepSeek-V4-Flash
    provider: str                  # 厂商名称，如 deepseek-ai
    category: str = "对话"          # 模型类别：对话 / 生图 / 语音 / 视频
    input_price_cny: float = 0.0   # 输入价格 (¥/1M Tokens)，取第一段
    output_price_cny: float = 0.0  # 输出价格 (¥/1M Tokens)，取第一段
    cache_price_cny: float = 0.0   # 缓存价格 (¥/1M Tokens)，取第一段
    is_free: bool = False          # 是否免费模型
    has_tiered_pricing: bool = False  # 是否存在分段定价
    price_tiers: List[SiliconFlowPriceTier] = []  # 分段定价详情
    price_note: str = ""           # 价格备注 (分段定价描述等)

class SiliconFlowScrapeResponse(BaseModel):
    """硅基流动爬取结果响应"""
    status: str = "success"
    total_models: int = 0
    category_counts: Dict[str, int] = {}  # 按类别统计：{"对话": 50, "生图": 10, ...}
    free_models_count: int = 0
    tiered_models_count: int = 0
    models: List[SiliconFlowModelItem] = []
    scrape_duration_ms: float = 0.0
    error_message: str = ""

class SiliconFlowImportRequest(BaseModel):
    """硅基流动导入请求"""
    models: List[SiliconFlowModelItem]
    site_id: Optional[int] = None

class SiliconFlowImportResponse(BaseModel):
    """硅基流动导入结果响应"""
    status: str = "success"
    site_id: int = 0
    site_name: str = ""
    total_imported: int = 0
    new_models_created: int = 0     # 新建的 ModelMetadata 数量
    prices_updated: int = 0         # 更新的 SiteModelPricing 数量
    prices_created: int = 0         # 新建的 SiteModelPricing 数量
    error_message: str = ""


# --- 阿里百炼 Aliyun Model Studio 爬取相关 ---
class BailianPriceTier(BaseModel):
    """阿里百炼分段定价条目"""
    tier_label: str = ""           # 价格段标签，如 "0<Token≤32K" 或 "32K<Token≤128K"
    input_price_cny: float = 0.0   # 该段输入价格 (¥/1M Tokens)
    output_price_cny: float = 0.0  # 该段输出价格 (¥/1M Tokens)
    cache_price_cny: float = 0.0   # 该段缓存价格 (¥/1M Tokens)

class BailianModelItem(BaseModel):
    """阿里百炼爬取到的单个模型价格信息"""
    model_id: str                  # 模型标准 ID，如 qwen3.8-max
    display_name: str              # 显示名称，如 Qwen3.8-Max
    provider: str = "alibaba"      # 厂商归属，如 alibaba / deepseek / zhipuai 等
    category: str = "千问系列"      # 模型类别：千问系列 / 第三方开源模型 / 多模态 / 语音 / 视频等
    input_price_cny: float = 0.0   # 输入价格 (¥/1M Tokens)
    output_price_cny: float = 0.0  # 输出价格 (¥/1M Tokens)
    cache_price_cny: float = 0.0   # 缓存价格 (¥/1M Tokens)
    is_free: bool = False          # 是否免费模型
    has_tiered_pricing: bool = False  # 是否存在阶梯分段定价
    price_tiers: List[BailianPriceTier] = []  # 分段定价明细
    price_note: str = ""           # 价格备注 (限时折扣、原价说明等)

class BailianScrapeResponse(BaseModel):
    """阿里百炼爬取结果响应"""
    status: str = "success"
    total_models: int = 0
    category_counts: Dict[str, int] = {}
    free_models_count: int = 0
    tiered_models_count: int = 0
    models: List[BailianModelItem] = []
    scrape_duration_ms: float = 0.0
    error_message: str = ""

class BailianImportRequest(BaseModel):
    """阿里百炼导入请求"""
    models: List[BailianModelItem]
    site_id: Optional[int] = None

class BailianImportResponse(BaseModel):
    """阿里百炼导入结果响应"""
    status: str = "success"
    site_id: int = 0
    site_name: str = ""
    total_imported: int = 0
    new_models_created: int = 0
    prices_updated: int = 0
    prices_created: int = 0
    error_message: str = ""


# --- 官方模型价格表相关 Schema ---
class OfficialSnapshotSchema(BaseModel):
    id: int
    provider: str
    source_url: str
    page_title: str
    local_file_path: str
    file_size_bytes: int
    models_count: int
    captured_at: datetime

    class Config:
        from_attributes = True


class OfficialModelPriceSchema(BaseModel):
    id: int
    provider: str
    provider_name: str
    series: str
    model_name: str
    raw_model_id: str
    billing_mode: str
    tier_range: str
    currency: str
    input_price: float
    output_price: float
    cache_read_price: float
    cache_write_price: float
    remarks: str
    custom_notes: str = ""
    user_tags: str = ""
    price_date: str
    source_page_url: str
    source_anchor: str
    snapshot_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # 汇率换算附加属性（由服务层在返回时自动计算或前端按需计算）
    converted_input_cny: Optional[float] = None
    converted_output_cny: Optional[float] = None
    converted_cache_read_cny: Optional[float] = None
    converted_cache_write_cny: Optional[float] = None
    converted_input_usd: Optional[float] = None
    converted_output_usd: Optional[float] = None
    converted_cache_read_usd: Optional[float] = None
    converted_cache_write_usd: Optional[float] = None

    class Config:
        from_attributes = True


class OfficialModelPriceUpdateNotes(BaseModel):
    custom_notes: Optional[str] = None
    user_tags: Optional[str] = None


class OfficialScrapeRequest(BaseModel):
    provider: Optional[str] = None # 若为 None 或 "all" 则全量抓取，否则为指定厂商 code
    proxy: Optional[str] = None    # 可选代理地址，如 "http://127.0.0.1:7890"


class OfficialScrapeResponse(BaseModel):
    status: str = "success"
    total_models: int = 0
    providers_scraped: List[str] = []
    duration_ms: float = 0.0
    error_message: str = ""


# --- 官网基准第一档模型与渠道映射 ---
class ChannelMatchOfficialItem(BaseModel):
    id: Optional[int] = None
    site_model_name: Optional[str] = ""
    model_id: Optional[str] = ""
    group_name: Optional[str] = ""
    calculated_input_usd: float = 0.0
    calculated_output_usd: float = 0.0


class ChannelMatchOfficialRequest(BaseModel):
    models: Optional[List[ChannelMatchOfficialItem]] = None


class SaveOfficialMappingItem(BaseModel):
    channel_model_id: Optional[int] = None
    channel_model_name: str
    official_model_id: Optional[int] = None
    official_model_name: Optional[str] = ""
    group_name: Optional[str] = ""


class SaveOfficialMappingsRequest(BaseModel):
    mappings: List[SaveOfficialMappingItem]



