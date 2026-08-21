from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from backend.app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args={
        "check_same_thread": False,
        "timeout": 30.0  # 允许 30 秒锁等待
    }
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_db():
    async with engine.begin() as conn:
        # 开启 SQLite WAL 预写日志模式与 busy_timeout，彻底消除 database is locked
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        await conn.exec_driver_sql("PRAGMA busy_timeout=30000;")
        await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
        await conn.run_sync(Base.metadata.create_all)
        # 自动迁移检查：若表存在但无 group_name 则自动补齐
        try:
            await conn.exec_driver_sql("ALTER TABLE relay_sites ADD COLUMN group_name VARCHAR(100) DEFAULT '';")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("ALTER TABLE site_model_pricings ADD COLUMN group_name VARCHAR(100) DEFAULT '';")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("ALTER TABLE relay_sites ADD COLUMN currency VARCHAR(10) DEFAULT 'CNY';")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
            await conn.exec_driver_sql("DELETE FROM site_model_pricings WHERE site_id NOT IN (SELECT id FROM relay_sites);")
            await conn.exec_driver_sql("DELETE FROM channel_model_mappings WHERE site_id NOT IN (SELECT id FROM relay_sites);")
        except Exception:
            pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
