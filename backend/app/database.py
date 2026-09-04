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
    # 确保所有 SQLAlchemy 模型显式注册到 Base.metadata 中
    import backend.app.models.token_price  # noqa: F401

    async with engine.begin() as conn:
        # 开启 SQLite WAL 预写日志模式与 busy_timeout，彻底消除 database is locked
        await conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
        await conn.exec_driver_sql("PRAGMA busy_timeout=30000;")
        await conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
        await conn.run_sync(Base.metadata.create_all)
        # 自动迁移检查：若表存在但缺少新字段则自动补齐
        migrations = [
            "ALTER TABLE relay_sites ADD COLUMN group_name VARCHAR(100) DEFAULT '';",
            "ALTER TABLE relay_sites ADD COLUMN currency VARCHAR(10) DEFAULT 'CNY';",
            "ALTER TABLE site_model_pricings ADD COLUMN group_name VARCHAR(100) DEFAULT '';",
            "ALTER TABLE site_model_pricings ADD COLUMN source_updated_at VARCHAR(40) DEFAULT '';",
            "ALTER TABLE site_model_pricings ADD COLUMN official_model_id INTEGER;",
            "ALTER TABLE site_model_pricings ADD COLUMN official_model_name VARCHAR(150) DEFAULT '';",
            "ALTER TABLE site_model_pricings ADD COLUMN official_input_discount FLOAT;",
            "ALTER TABLE site_model_pricings ADD COLUMN official_output_discount FLOAT;",
            "ALTER TABLE site_model_pricings ADD COLUMN official_composite_discount FLOAT;",
            "ALTER TABLE channel_model_mappings ADD COLUMN official_model_id INTEGER;",
            "ALTER TABLE channel_model_mappings ADD COLUMN official_model_name VARCHAR(150) DEFAULT '';",
            "ALTER TABLE model_metadata ADD COLUMN last_updated VARCHAR(30) DEFAULT '';",
            "ALTER TABLE model_metadata ADD COLUMN family VARCHAR(80) DEFAULT '';",
        ]
        for sql in migrations:
            try:
                await conn.exec_driver_sql(sql)
            except Exception:
                pass

        try:
            await conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
            await conn.exec_driver_sql("DELETE FROM site_model_pricings WHERE site_id NOT IN (SELECT id FROM relay_sites);")
            await conn.exec_driver_sql("DELETE FROM channel_model_mappings WHERE site_id NOT IN (SELECT id FROM relay_sites);")
        except Exception:
            pass

    # ================= 官方模型定价与快照数据平滑迁移引擎 =================
    try:
        import sys
        import os
        import shutil
        import json
        from pathlib import Path
        from datetime import datetime
        from sqlalchemy import select, func
        from backend.app.config import BASE_DIR, DATA_DIR
        from backend.app.models.token_price import OfficialModelPrice, OfficialSnapshot

        # 1. 智能定位预置资源包路径 (兼容 PyInstaller 临时目录与源码目录)
        bundle_roots = []
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundle_roots.append(Path(sys._MEIPASS))
        bundle_roots.extend([BASE_DIR, Path(os.getcwd())])

        bundled_seed_path = None
        bundled_snapshots_dir = None
        for root in bundle_roots:
            cand_seed = root / "data" / "official_prices_seed.json"
            if cand_seed.exists() and not bundled_seed_path:
                bundled_seed_path = cand_seed
            cand_snap = root / "data" / "official_snapshots"
            if cand_snap.exists() and not bundled_snapshots_dir:
                bundled_snapshots_dir = cand_snap

        # 2. 补齐用户的离线官方 HTML 快照证据链
        user_snapshots_dir = DATA_DIR / "official_snapshots"
        user_snapshots_dir.mkdir(parents=True, exist_ok=True)

        if bundled_snapshots_dir and bundled_snapshots_dir.exists():
            for src_file in bundled_snapshots_dir.glob("*.html"):
                dst_file = user_snapshots_dir / src_file.name
                if not dst_file.exists():
                    try:
                        shutil.copy2(str(src_file), str(dst_file))
                    except Exception:
                        pass

        # 3. 数据库快照表 (official_pricing_snapshots) 同步与 ID 映射建立
        async with AsyncSessionLocal() as session:
            existing_snaps_res = await session.execute(select(OfficialSnapshot))
            existing_snaps = existing_snaps_res.scalars().all()
            snap_map = {s.provider: s.id for s in existing_snaps}

            # 若缺少某些厂商快照记录，扫描本地快照文件并补齐
            target_snapshot_files = {
                "deepseek": "sample_deepseek.html",
                "zhipuai": "sample_glm.html",
                "moonshotai": "sample_kimi.html",
                "minimax": "sample_minimax.html",
                "alibaba": "sample_bailian.html",
                "openai": "sample_openai.html",
                "anthropic": "sample_claude.html",
                "google": "sample_gemini.html",
            }
            provider_names = {
                "deepseek": "DeepSeek 官方定价",
                "zhipuai": "智谱 GLM 开放平台",
                "moonshotai": "Moonshot Kimi 定价",
                "minimax": "MiniMax 开放平台",
                "alibaba": "阿里百炼官方定价",
                "openai": "OpenAI 官方定价",
                "anthropic": "Anthropic Claude 官方定价",
                "google": "Google Gemini 官方定价",
            }
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

            for prov, fname in target_snapshot_files.items():
                if prov not in snap_map:
                    local_f = user_snapshots_dir / fname
                    if local_f.exists():
                        new_snap = OfficialSnapshot(
                            provider=prov,
                            page_title=f"{provider_names.get(prov, prov)} 官方快照",
                            source_url="",
                            local_file_path=str(local_f),
                            captured_at=datetime.utcnow(),
                            file_size_bytes=local_f.stat().st_size,
                            models_count=0
                        )
                        session.add(new_snap)
                        await session.flush()
                        snap_map[prov] = new_snap.id

            await session.commit()

            # 4. 官方定价数据 (official_models_pricing) 智能全量灌入或增量对齐
            if bundled_seed_path and bundled_seed_path.exists():
                with open(bundled_seed_path, "r", encoding="utf-8") as f:
                    seed_items = json.load(f)

                cnt_res = await session.execute(select(func.count(OfficialModelPrice.id)))
                current_count = cnt_res.scalar() or 0

                if current_count == 0:
                    # 全量初始灌入 (旧版本首次升级场景)
                    for item in seed_items:
                        prov = item.get("provider")
                        item["snapshot_id"] = snap_map.get(prov, None)
                        session.add(OfficialModelPrice(**item))
                    await session.commit()
                else:
                    # 增量对齐补全 (覆盖升级且数据库已有部分旧官方数据场景)
                    res_existing = await session.execute(select(OfficialModelPrice))
                    existing_rows = res_existing.scalars().all()
                    existing_keys = {
                        (r.provider, r.raw_model_id, r.billing_mode, r.tier_range): r
                        for r in existing_rows
                    }

                    added_count = 0
                    for item in seed_items:
                        key = (
                            item.get("provider"),
                            item.get("raw_model_id"),
                            item.get("billing_mode"),
                            item.get("tier_range")
                        )
                        if key not in existing_keys:
                            prov = item.get("provider")
                            item["snapshot_id"] = snap_map.get(prov, None)
                            session.add(OfficialModelPrice(**item))
                            added_count += 1
                        else:
                            # 补全缺失的 snapshot_id
                            existing_obj = existing_keys[key]
                            prov = item.get("provider")
                            if not existing_obj.snapshot_id and prov in snap_map:
                                existing_obj.snapshot_id = snap_map[prov]

                    if added_count > 0:
                        await session.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
