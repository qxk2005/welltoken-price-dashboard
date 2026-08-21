from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# ================================
# 1. 大模型元数据 Schema
# ================================
class ModelMetadataBase(BaseModel):
    model_id: str
    name: str
    provider: str
    series: str = ""
    context_window: int = 128000
    max_output: int = 4096
    official_input_price: float = 0.0
    official_output_price: float = 0.0
    official_cache_price: float = 0.0
    modalities: str = "text"
    capabilities: str = "tool_calling"
    is_featured: bool = False
    description: Optional[str] = ""

class ModelMetadataCreate(ModelMetadataBase):
    pass

class ModelMetadataSchema(ModelMetadataBase):
    id: int
    created_at: datetime
    updated_at: datetime
    active_relay_count: Optional[int] = 0
    lowest_price_usd: Optional[float] = 0.0

    class Config:
        from_attributes = True

# ================================
# 2. 中转渠道站点 Schema
# ================================
class RelaySiteBase(BaseModel):
    name: str
    base_url: str
    api_key: Optional[str] = ""
    site_type: str = "newapi"
    recharge_rate: float = 1.0
    models_endpoint: str = "/api/models"
    status_endpoint: str = "/api/status"
    is_active: bool = True
    notes: Optional[str] = ""

class RelaySiteCreate(RelaySiteBase):
    pass

class RelaySiteUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    site_type: Optional[str] = None
    recharge_rate: Optional[float] = None
    models_endpoint: Optional[str] = None
    status_endpoint: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class RelaySiteSchema(RelaySiteBase):
    id: int
    last_status: str
    last_latency_ms: float
    last_sync_time: datetime
    score: float
    created_at: datetime
    model_count: Optional[int] = 0

    class Config:
        from_attributes = True

# ================================
# 3. 聚合比价矩阵 Schema
# ================================
class ComparisonItemSchema(BaseModel):
    id: int
    model_id: str
    model_name: str
    provider: str
    series: str = ""
    site_id: int
    site_name: str
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

# ================================
# 4. 性能实测 Schema (token-speed-tester)
# ================================
class SpeedTestRequest(BaseModel):
    site_ids: List[int] = Field(..., description="测试目标渠道 ID 列表")
    model_id: str = Field("deepseek-v3", description="测试模型 ID")
    prompt_type: str = Field("standard", description="standard / reasoning / code / probe")
    custom_prompt: Optional[str] = None
    rounds: int = Field(1, ge=1, le=5, description="测试轮数")

class SpeedTestStreamEvent(BaseModel):
    event: str  # start, token, metric_update, done, error
    site_id: int
    site_name: str
    model_id: str
    current_token_count: int
    current_ttft_ms: float
    current_tps: float
    instant_tps: float
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
    error_message: Optional[str] = ""
    is_authentic: bool
    jitter_rate: float
    score: float
    grade: str  # S, A, B, C, F

# ================================
# 5. 同步与设置 Schema
# ================================
class SyncStatusSchema(BaseModel):
    models_dev_last_sync: Optional[datetime] = None
    models_dev_total_models: int = 0
    relays_last_sync: Optional[datetime] = None
    total_active_sites: int = 0
    total_pricings_cached: int = 0
    usd_to_cny_rate: float = 7.30
    db_size_mb: float = 0.0

class ExchangeRateUpdate(BaseModel):
    usd_to_cny_rate: float

class SystemHealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str = "1.0.0"
    uptime_seconds: float
    database_connected: bool

