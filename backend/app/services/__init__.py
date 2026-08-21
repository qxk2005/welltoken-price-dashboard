from backend.app.services.models_dev_sync import models_dev_sync
from backend.app.services.relay_fetcher import relay_fetcher
from backend.app.services.speed_tester import speed_tester
from backend.app.services.dashboard_service import dashboard_service

# 兼容旧引入名称
price_service = dashboard_service

__all__ = [
    "models_dev_sync",
    "relay_fetcher",
    "speed_tester",
    "dashboard_service",
    "price_service"
]
