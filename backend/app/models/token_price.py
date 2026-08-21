from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Index
from backend.app.database import Base

class TokenInfo(Base):
    __tablename__ = "token_info"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(50), nullable=False)
    icon_url = Column(String(255), default="")
    is_active = Column(Boolean, default=True)
    is_favorite = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class TokenPriceRecord(Base):
    __tablename__ = "token_price_records"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    price = Column(Float, nullable=False)
    change_24h = Column(Float, default=0.0)
    high_24h = Column(Float, default=0.0)
    low_24h = Column(Float, default=0.0)
    volume_24h = Column(Float, default=0.0)
    market_cap = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_symbol_timestamp", "symbol", "timestamp"),
    )

class KlineData(Base):
    __tablename__ = "kline_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)
    timeframe = Column(String(10), default="1m", index=True)  # 1m, 5m, 15m, 1h, 1d
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_kline_query", "symbol", "timeframe", "timestamp"),
    )
