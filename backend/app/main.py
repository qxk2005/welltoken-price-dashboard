from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.services.dashboard_service import dashboard_service
from backend.app.api import api_v1_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动阶段：初始化 SQLite 数据库、models.dev 标准库与渠道倍率数据
    await init_db()
    await dashboard_service.initialize()
    await dashboard_service.start_loop()
    print(f"[{settings.APP_NAME}] Backend service started successfully at http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    yield
    # 停止阶段：安全关闭后台任务
    await dashboard_service.stop_loop()
    print(f"[{settings.APP_NAME}] Backend service stopped.")

app = FastAPI(
    title=settings.APP_NAME,
    description="WellToken Price Dashboard - High-Performance LLM Token Aggregator & Speed Tester",
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
        "description": "Token 聚合比价与测评工具后端服务",
        "docs": "/docs",
        "api_v1": "/api/v1"
    }
