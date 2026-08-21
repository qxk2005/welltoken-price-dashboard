from fastapi import APIRouter
from backend.app.api.v1.price import router as price_router
from backend.app.api.v1.system import router as system_router

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(price_router)
api_v1_router.include_router(system_router)

__all__ = ["api_v1_router"]
