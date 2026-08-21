import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    APP_NAME: str = "WellToken-Price-Dashboard"
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    SERVER_HOST: str = "127.0.0.1"
    SERVER_PORT: int = 8765
    
    DATABASE_PATH: str = str(DATA_DIR / "welltoken.db")
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DATA_DIR / 'welltoken.db'}"
    
    PRICE_FETCH_INTERVAL: int = 3  # 秒
    
    # 默认监控的预置 Token 列表
    DEFAULT_TOKENS: list[dict] = [
        {"symbol": "WELL", "name": "WellToken", "base_price": 1.85, "volatility": 0.015},
        {"symbol": "BTC", "name": "Bitcoin", "base_price": 68500.0, "volatility": 0.008},
        {"symbol": "ETH", "name": "Ethereum", "base_price": 3520.0, "volatility": 0.012},
        {"symbol": "SOL", "name": "Solana", "base_price": 182.5, "volatility": 0.020},
        {"symbol": "BNB", "name": "BNB", "base_price": 590.0, "volatility": 0.010},
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
