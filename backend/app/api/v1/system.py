import time
from fastapi import APIRouter
from sqlalchemy import text
from backend.app.config import settings
from backend.app.database import AsyncSessionLocal
from backend.app.schemas.token_schema import SystemHealthResponse

router = APIRouter(prefix="/system", tags=["System"])
START_TIME = time.time()

@router.get("/health", response_model=SystemHealthResponse)
async def health_check():
    """系统与数据库健康状态检查 (供 Electron 探活)"""
    db_connected = False
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        db_connected = False

    return SystemHealthResponse(
        status="ok" if db_connected else "degraded",
        app=settings.APP_NAME,
        version="1.0.0",
        uptime_seconds=round(time.time() - START_TIME, 2),
        database_connected=db_connected
    )
