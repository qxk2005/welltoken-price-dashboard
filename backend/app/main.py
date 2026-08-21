from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.services.price_fetcher import price_service
from backend.app.api import api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段：初始化 SQLite 数据库及基础数据
    await init_db()
    await price_service.initialize()
    await price_service.start_loop()
    print(f"[{settings.APP_NAME}] Backend service started at {settings.SERVER_HOST}:{settings.SERVER_PORT}")
    yield
    # 停止阶段：安全关闭后台任务
    await price_service.stop_loop()
    print(f"[{settings.APP_NAME}] Backend service stopped.")

app = FastAPI(
    title=settings.APP_NAME,
    description="WellToken Price Dashboard High-Performance Backend Service",
    version="1.0.0",
    lifespan=lifespan
)

# 允许跨域 (Electron Renderer 访问)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
        "api_v1": "/api/v1"
    }
