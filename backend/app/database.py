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
            "ALTER TABLE official_model_prices ADD COLUMN is_current BOOLEAN DEFAULT 1;",
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
        from sqlalchemy import select, func, update
        from backend.app.config import BASE_DIR, DATA_DIR
        from backend.app.models.token_price import OfficialModelPrice, OfficialSnapshot

        # 1. 智能定位预置资源包路径 (兼容 PyInstaller 临时目录与源码目录)
        bundle_roots = []
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            bundle_roots.append(Path(sys._MEIPASS))
        bundle_roots.extend([BASE_DIR, Path(os.getcwd())])

        bundled_prices_seed = None
        bundled_snaps_seed = None
        bundled_snapshots_dir = None
        for root in bundle_roots:
            cand_p_seed = root / "data" / "official_prices_seed.json"
            if cand_p_seed.exists() and not bundled_prices_seed:
                bundled_prices_seed = cand_p_seed
            cand_s_seed = root / "data" / "official_snapshots_seed.json"
            if cand_s_seed.exists() and not bundled_snaps_seed:
                bundled_snaps_seed = cand_s_seed
            cand_snap_dir = root / "data" / "official_snapshots"
            if cand_snap_dir.exists() and not bundled_snapshots_dir:
                bundled_snapshots_dir = cand_snap_dir

        # 2. 补齐用户的离线官方 HTML 快照证据链文件
        user_snapshots_dir = DATA_DIR / "official_snapshots"
        user_snapshots_dir.mkdir(parents=True, exist_ok=True)

        if bundled_snapshots_dir and bundled_snapshots_dir.exists():
            for src_file in bundled_snapshots_dir.glob("*.html"):
                dst_file = user_snapshots_dir / src_file.name
                if not dst_file.exists() or dst_file.stat().st_size == 0:
                    try:
                        shutil.copy2(str(src_file), str(dst_file))
                    except Exception:
                        pass

        # 3. 官方快照元数据表 (official_snapshots) 导入与增量同步
        async with AsyncSessionLocal() as session:
            existing_snaps_res = await session.execute(select(OfficialSnapshot))
            existing_snaps = existing_snaps_res.scalars().all()

            # 建立多维度定位索引：(provider, captured_at_str), local_file_name, provider
            snap_by_ref = {}
            snap_by_filename = {}
            snap_by_provider_latest = {}

            for s in existing_snaps:
                capt_str = s.captured_at.strftime("%Y-%m-%d %H:%M:%S") if s.captured_at else ""
                snap_by_ref[(s.provider, capt_str)] = s.id
                if s.local_file_path:
                    fname = Path(s.local_file_path).name
                    snap_by_filename[fname] = s
                snap_by_provider_latest[s.provider] = s.id

            seed_snap_id_map = {}  # seed_item['id'] -> real_db_id

            if bundled_snaps_seed and bundled_snaps_seed.exists():
                with open(bundled_snaps_seed, "r", encoding="utf-8") as f:
                    seed_snapshots = json.load(f)

                for s_item in seed_snapshots:
                    prov = s_item["provider"]
                    capt_raw = s_item.get("captured_at", "")
                    s_fname = Path(s_item.get("local_file_path", "")).name
                    real_file = user_snapshots_dir / s_fname

                    # 检查本地是否已有该快照记录（通过 provider + captured_at 前19位精确对齐，杜绝不同批次复用文件名导致的冲突）
                    matched_snap_id = snap_by_ref.get((prov, capt_raw[:19]))
                    matched_snap = None
                    if matched_snap_id:
                        matched_snap = next((x for x in existing_snaps if x.id == matched_snap_id), None)

                    if matched_snap:
                        # 确保路径指向当前系统合法的绝对路径
                        if real_file.exists():
                            matched_snap.local_file_path = str(real_file)
                            matched_snap.file_size_bytes = real_file.stat().st_size
                        seed_snap_id_map[s_item["id"]] = matched_snap.id
                        snap_by_ref[(prov, capt_raw[:19])] = matched_snap.id
                        snap_by_provider_latest[prov] = matched_snap.id
                    else:
                        # 增量插入快照元数据记录
                        capt_dt = datetime.utcnow()
                        if capt_raw:
                            try:
                                capt_dt = datetime.fromisoformat(capt_raw)
                            except Exception:
                                pass

                        new_snap = OfficialSnapshot(
                            provider=prov,
                            source_url=s_item.get("source_url", ""),
                            page_title=s_item.get("page_title", f"{prov} 官方快照"),
                            local_file_path=str(real_file) if real_file.exists() else s_item.get("local_file_path", ""),
                            file_size_bytes=real_file.stat().st_size if real_file.exists() else s_item.get("file_size_bytes", 0),
                            models_count=s_item.get("models_count", 0),
                            captured_at=capt_dt
                        )
                        session.add(new_snap)
                        await session.flush()
                        seed_snap_id_map[s_item["id"]] = new_snap.id
                        snap_by_ref[(prov, capt_raw[:19])] = new_snap.id
                        snap_by_filename[s_fname] = new_snap
                        snap_by_provider_latest[prov] = new_snap.id

                await session.commit()

            # 4. 官方定价数据 (official_model_prices) 智能版本升级与平滑迁移
            if bundled_prices_seed and bundled_prices_seed.exists():
                with open(bundled_prices_seed, "r", encoding="utf-8") as f:
                    seed_prices = json.load(f)

                cnt_res = await session.execute(select(func.count(OfficialModelPrice.id)))
                current_total_models = cnt_res.scalar() or 0

                # 探测本地是否已经包含最新的 2026-09-11 批次生效模型
                check_latest_res = await session.execute(
                    select(OfficialModelPrice.id)
                    .where(OfficialModelPrice.is_current == True)
                    .where(OfficialModelPrice.price_date.like("2026-09-11%"))
                    .limit(1)
                )
                has_latest_active_batch = check_latest_res.first() is not None

                def resolve_snap_id(p_item):
                    snap_ref = p_item.get("snapshot_ref")
                    if snap_ref:
                        ref_prov = snap_ref.get("provider")
                        ref_capt = (snap_ref.get("captured_at") or "")[:19]
                        if (ref_prov, ref_capt) in snap_by_ref:
                            return snap_by_ref[(ref_prov, ref_capt)]
                    # 兜底按 provider 查找最近快照
                    return snap_by_provider_latest.get(p_item.get("provider"))

                if current_total_models == 0:
                    # 场景 A: 全新安装冷启动 (导入全量多版本基准：598款最新 + 30款历史基准)
                    for item in seed_prices:
                        row_data = dict(item)
                        row_data.pop("snapshot_ref", None)
                        row_data["snapshot_id"] = resolve_snap_id(item)
                        session.add(OfficialModelPrice(**row_data))
                    await session.commit()

                elif not has_latest_active_batch:
                    # 场景 B: 存量旧客户端覆盖升级 (无 2026-09-11 批次)
                    # 1. 将本地原有当前生效模型全部降级为历史基准 (is_current=False)，保留上期比对和时序大盘
                    await session.execute(
                        update(OfficialModelPrice)
                        .where(OfficialModelPrice.is_current == True)
                        .values(is_current=False)
                    )

                    # 2. 注入种子中 2026-09-11 批次的最新官方模型并标记为当前生效 (is_current=True)
                    for item in seed_prices:
                        if item.get("is_current"):
                            row_data = dict(item)
                            row_data.pop("snapshot_ref", None)
                            row_data["snapshot_id"] = resolve_snap_id(item)
                            session.add(OfficialModelPrice(**row_data))

                    # 3. 补齐可能缺失的种子历史模型
                    res_existing = await session.execute(
                        select(OfficialModelPrice.provider, OfficialModelPrice.model_name, OfficialModelPrice.price_date)
                    )
                    existing_tuples = set(res_existing.all())

                    for item in seed_prices:
                        if not item.get("is_current"):
                            tpl = (item.get("provider"), item.get("model_name"), item.get("price_date"))
                            if tpl not in existing_tuples:
                                row_data = dict(item)
                                row_data.pop("snapshot_ref", None)
                                row_data["snapshot_id"] = resolve_snap_id(item)
                                session.add(OfficialModelPrice(**row_data))

                    await session.commit()

                else:
                    # 场景 C: 已包含最新 2026-09-11 批次，做快照外键缺失兜底对齐
                    for prov, s_id in snap_by_provider_latest.items():
                        if s_id:
                            await session.execute(
                                update(OfficialModelPrice)
                                .where(OfficialModelPrice.provider == prov)
                                .where(OfficialModelPrice.snapshot_id.is_(None))
                                .values(snapshot_id=s_id)
                            )
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
