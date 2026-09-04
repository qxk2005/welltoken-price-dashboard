from fastapi import APIRouter
from backend.app.api.v1.comparison import router as comparison_router
from backend.app.api.v1.channels import router as channels_router
from backend.app.api.v1.models_catalog import router as models_catalog_router
from backend.app.api.v1.speed_test import router as speed_test_router
from backend.app.api.v1.sync_settings import router as sync_settings_router
from backend.app.api.v1.price import router as price_router
from backend.app.api.v1.system import router as system_router

from backend.app.api.v1.icloud_sync import router as icloud_sync_router
from backend.app.api.v1.official_pricing import router as official_pricing_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(comparison_router)
api_v1_router.include_router(channels_router)
api_v1_router.include_router(models_catalog_router)
api_v1_router.include_router(speed_test_router)
api_v1_router.include_router(sync_settings_router)
api_v1_router.include_router(price_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(icloud_sync_router)
api_v1_router.include_router(official_pricing_router)

__all__ = ["api_v1_router"]
