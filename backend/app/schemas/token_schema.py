from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

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
    sparkline: List[float] = Field(default_factory=list)

class KlinePoint(BaseModel):
    timestamp: int  # 毫秒时间戳
    open: float
    high: float
    low: float
    close: float
    volume: float

class DepthLevel(BaseModel):
    price: float
    amount: float
    total: float

class OrderBookDepth(BaseModel):
    symbol: str
    timestamp: int
    bids: List[DepthLevel]  # 买单
    asks: List[DepthLevel]  # 卖单

class TokenWatchlistCreate(BaseModel):
    symbol: str
    name: str
    is_favorite: Optional[bool] = False

class SystemHealthResponse(BaseModel):
    status: str = "ok"
    app: str
    version: str = "1.0.0"
    uptime_seconds: float
    database_connected: bool
