from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class RelaySite(Base):
    """Token 供应商与中转渠道 (基于 models.dev providers 规范与自建中转)"""
    __tablename__ = "relay_sites"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(String(100), index=True, default="") # 如 cloudflare-workers-ai, deepseek, openrouter
    name = Column(String(100), nullable=False, index=True)
    base_url = Column(String(255), nullable=False)
    api_key = Column(String(255), default="")
    site_type = Column(String(30), default="official")  # official, cloud, newapi, sub2api, oneapi, custom
    group_name = Column(String(100), default="")        # 渠道绑定的结算分组 (如 deepseek-三方, vip)
    currency = Column(String(10), default="CNY")        # 渠道结算货币 (CNY 或 USD)
    recharge_rate = Column(Float, default=1.0)  # 充值汇率比，例如 1元=1刀为1.0
    models_endpoint = Column(String(255), default="/v1/models")
    status_endpoint = Column(String(255), default="")
    website = Column(String(255), default="")
    doc_url = Column(String(255), default="")
    env_vars = Column(String(255), default="")          # 对应 models.dev 的 env 列表，如 OPENAI_API_KEY
    is_official_catalog = Column(Boolean, default=False) # 是否来自 models.dev 官方 catalog.json
    is_active = Column(Boolean, default=True)
    last_status = Column(String(20), default="online")  # online, offline, degraded, unknown
    last_latency_ms = Column(Float, default=0.0)
    last_sync_time = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, default=90.0)                 # 综合质量评分 (0-100)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    pricings = relationship("SiteModelPricing", back_populates="site", cascade="all, delete-orphan")
    test_histories = relationship("SpeedTestHistory", back_populates="site", cascade="all, delete-orphan")
    mappings = relationship("ChannelModelMapping", back_populates="site", cascade="all, delete-orphan")

class ModelMetadata(Base):
    """大模型标准元数据 (基于 models.dev/models.json 与 api.json 标准化定义)"""
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(150), unique=True, index=True, nullable=False)  # 如 deepseek/deepseek-v4-flash, gpt-4o
    name = Column(String(150), nullable=False)
    provider = Column(String(80), index=True, nullable=False)  # openai, anthropic, deepseek, google, alibaba, meta
    series = Column(String(80), index=True, default="")        # deepseek-flash, gpt-4o, claude-3-5 等
    family = Column(String(80), default="")                    # models.dev family 属性
    context_window = Column(Integer, default=128000)
    max_output = Column(Integer, default=4096)
    official_input_price = Column(Float, default=0.0)   # $/1M tokens
    official_output_price = Column(Float, default=0.0)  # $/1M tokens
    official_cache_price = Column(Float, default=0.0)   # $/1M tokens
    modalities = Column(String(100), default="text")    # text, image, audio, video
    capabilities = Column(String(200), default="tool_calling") # reasoning, vision, tool_calling, structured_outputs
    open_weights = Column(Boolean, default=False)
    release_date = Column(String(30), default="")
    is_featured = Column(Boolean, default=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    pricings = relationship("SiteModelPricing", back_populates="model", cascade="all, delete-orphan")

class SiteModelPricing(Base):
    """各供应商渠道与各模型的实际折算价格与倍率"""
    __tablename__ = "site_model_pricings"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("relay_sites.id"), index=True, nullable=False)
    model_id = Column(String(150), ForeignKey("model_metadata.model_id"), index=True, nullable=False)
    group_name = Column(String(100), default="")       # 价格所属分组 (如 deepseek-三方, vip)
    site_model_name = Column(String(150), default="")  # 站点别名
    model_ratio = Column(Float, default=1.0)          # 模型费率倍率
    group_ratio = Column(Float, default=1.0)          # 分组倍率
    calculated_input_usd = Column(Float, default=0.0)  # 折算后输入单价 ($/1M)
    calculated_output_usd = Column(Float, default=0.0) # 折算后输出单价 ($/1M)
    calculated_cache_usd = Column(Float, default=0.0)  # 折算后缓存单价 ($/1M)
    discount_percent = Column(Float, default=0.0)      # 相对官方基准价折扣百分比 (如 -50.0%)
    is_available = Column(Boolean, default=True)
    last_tested_tps = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    site = relationship("RelaySite", back_populates="pricings")
    model = relationship("ModelMetadata", back_populates="pricings")

class SpeedTestHistory(Base):
    """性能实测历史记录 (基于 token-speed-tester 规范)"""
    __tablename__ = "speed_test_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("relay_sites.id"), index=True, nullable=False)
    model_id = Column(String(150), index=True, nullable=False)
    test_time = Column(DateTime, default=datetime.utcnow, index=True)
    ttft_ms = Column(Float, default=0.0)           # 首字延迟 (Time to First Token, ms)
    avg_tps = Column(Float, default=0.0)           # 平均生成速率 (Tokens Per Second)
    peak_tps = Column(Float, default=0.0)          # 10-Token 滑动窗口峰值 TPS
    total_latency_ms = Column(Float, default=0.0)  # 总请求耗时 (ms)
    prompt_tokens = Column(Integer, default=0)     # Prompt Token 数
    completion_tokens = Column(Integer, default=0) # 生成 Token 数
    is_success = Column(Boolean, default=True)
    error_message = Column(Text, default="")
    is_authentic = Column(Boolean, default=True)   # 模型防降级/防作弊探针是否通过
    jitter_rate = Column(Float, default=0.0)       # 吐字时间抖动方差率
    score = Column(Float, default=0.0)             # 综合评分 (0-100)

    # 关系
    site = relationship("RelaySite", back_populates="test_histories")

class SyncLog(Base):
    """数据源同步审计历史日志"""
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(100), default="models.dev") # models.dev, relays, exchange_rate
    sync_type = Column(String(50), default="full")     # full, models, catalog, api, single
    status = Column(String(20), default="success")     # success, partial, failed
    models_count = Column(Integer, default=0)          # 成功同步的模型条数
    providers_count = Column(Integer, default=0)       # 成功同步的供应商条数
    pricings_count = Column(Integer, default=0)        # 成功更新的价格条数
    duration_ms = Column(Float, default=0.0)           # 同步耗时 (ms)
    error_message = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class ModelAlias(Base):
    """全局模型别名与模式规则库 (用于自动归一化各中转站混乱的命名到 models.dev 标准库)"""
    __tablename__ = "model_aliases"

    id = Column(Integer, primary_key=True, index=True)
    raw_pattern = Column(String(150), unique=True, index=True, nullable=False) # 原始命名或通配符规则，如 deepseek-chat, gpt-4o-2024*
    standard_model_id = Column(String(150), ForeignKey("model_metadata.model_id"), index=True, nullable=False) # 映射的标准模型 ID
    is_system = Column(Boolean, default=True) # 是否系统内置规则
    notes = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class ChannelModelMapping(Base):
    """渠道级自定义模型映射表 (允许单个渠道覆盖独立别名与专属倍率)"""
    __tablename__ = "channel_model_mappings"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("relay_sites.id"), index=True, nullable=False)
    channel_model_name = Column(String(150), index=True, nullable=False) # 渠道内原始名称 (如 deepseek-chat 或自定义别名)
    standard_model_id = Column(String(150), ForeignKey("model_metadata.model_id"), index=True, nullable=False) # 绑定的 models.dev 标准模型 ID
    custom_ratio = Column(Float, nullable=True) # 针对该模型的专属倍率 (为空则继承渠道全局 recharge_rate/default_ratio)
    is_enabled = Column(Boolean, default=True) # 是否启用该映射
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    site = relationship("RelaySite", back_populates="mappings")

