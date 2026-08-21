from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

class RelaySite(Base):
    """Token 渠道中转站 (NewAPI / Sub2API / OneAPI / 官方 API)"""
    __tablename__ = "relay_sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    base_url = Column(String(255), nullable=False)
    api_key = Column(String(255), default="")
    site_type = Column(String(30), default="newapi")  # newapi, sub2api, oneapi, official, custom
    recharge_rate = Column(Float, default=1.0)  # 充值汇率，例如 1元=1刀为1.0; 1元=0.5刀为2.0
    models_endpoint = Column(String(255), default="/api/models")
    status_endpoint = Column(String(255), default="/api/status")
    is_active = Column(Boolean, default=True)
    last_status = Column(String(20), default="online")  # online, offline, degraded, unknown
    last_latency_ms = Column(Float, default=0.0)
    last_sync_time = Column(DateTime, default=datetime.utcnow)
    score = Column(Float, default=90.0)  # 综合质量评分 (0-100)
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    pricings = relationship("SiteModelPricing", back_populates="site", cascade="all, delete-orphan")
    test_histories = relationship("SpeedTestHistory", back_populates="site", cascade="all, delete-orphan")

class ModelMetadata(Base):
    """大模型标准元数据 (基于 models.dev 标准化定义)"""
    __tablename__ = "model_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, index=True, nullable=False)  # 如 gpt-4o, claude-3-5-sonnet
    name = Column(String(100), nullable=False)
    provider = Column(String(50), index=True, nullable=False)  # openai, anthropic, deepseek, google, alibaba, meta
    series = Column(String(50), index=True, default="")       # deepseek-v3, deepseek-r1, gpt-4o, claude-3-5 等
    context_window = Column(Integer, default=128000)
    max_output = Column(Integer, default=4096)
    official_input_price = Column(Float, default=0.0)   # $/1M tokens
    official_output_price = Column(Float, default=0.0)  # $/1M tokens
    official_cache_price = Column(Float, default=0.0)   # $/1M tokens
    modalities = Column(String(100), default="text")    # text, image, audio, video
    capabilities = Column(String(150), default="tool_calling") # reasoning, vision, tool_calling, structured_outputs
    is_featured = Column(Boolean, default=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    pricings = relationship("SiteModelPricing", back_populates="model", cascade="all, delete-orphan")

class SiteModelPricing(Base):
    """各中转渠道与各模型的实际折算价格与倍率"""
    __tablename__ = "site_model_pricings"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("relay_sites.id"), index=True, nullable=False)
    model_id = Column(String(100), ForeignKey("model_metadata.model_id"), index=True, nullable=False)
    site_model_name = Column(String(100), default="")  # 站点别名
    model_ratio = Column(Float, default=1.0)           # 站点设置的模型基础倍率 (如 0.5x, 0.8x)
    group_ratio = Column(Float, default=1.0)           # 分组倍率 (默认 1.0)
    calculated_input_usd = Column(Float, default=0.0)  # 折算实际输入价 $/1M
    calculated_output_usd = Column(Float, default=0.0) # 折算实际输出价 $/1M
    calculated_cache_usd = Column(Float, default=0.0)  # 折算实际缓存价 $/1M
    discount_percent = Column(Float, default=0.0)      # 相比官方基准折扣 (如 -50.0%)
    is_available = Column(Boolean, default=True)
    last_tested_tps = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    site = relationship("RelaySite", back_populates="pricings")
    model = relationship("ModelMetadata", back_populates="pricings")

    __table_args__ = (
        Index("ix_site_model", "site_id", "model_id", unique=True),
    )

class SpeedTestHistory(Base):
    """渠道性能实测与一致性探针历史记录 (基于 token-speed-tester)"""
    __tablename__ = "speed_test_histories"
    
    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("relay_sites.id"), index=True, nullable=False)
    model_id = Column(String(100), index=True, nullable=False)
    test_time = Column(DateTime, default=datetime.utcnow, index=True)
    ttft_ms = Column(Float, default=0.0)               # 首字延迟 Time to First Token (ms)
    avg_tps = Column(Float, default=0.0)               # 平均生成速率 (Tokens/s)
    peak_tps = Column(Float, default=0.0)              # 10-Token 滑动窗口峰值 (Tokens/s)
    total_latency_ms = Column(Float, default=0.0)      # 总耗时 (ms)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    is_success = Column(Boolean, default=True)
    error_message = Column(String(255), default="")
    is_authentic = Column(Boolean, default=True)       # 模型一致性探针是否通过 (防降级作弊)
    jitter_rate = Column(Float, default=0.0)           # 吐字波动抖动率 (%)
    score = Column(Float, default=95.0)                # 单次打分

    # 关系
    site = relationship("RelaySite", back_populates="test_histories")
