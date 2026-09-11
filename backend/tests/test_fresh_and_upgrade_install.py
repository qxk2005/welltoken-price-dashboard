#!/usr/bin/env python3
"""
验证冷启动全新安装与存量旧版本覆盖升级的双场景测试脚本
"""
import sys
import os
import asyncio
import tempfile
import sqlite3
from pathlib import Path

# 切换工作目录
os.chdir(str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, os.getcwd())

async def test_fresh_install():
    print("\n--- [TEST 1] 测试全新安装冷启动 ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_fresh.db"
        
        # 动态替换 settings 中的数据库 URL
        from backend.app.config import settings
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from backend.app import database
        
        orig_engine = database.engine
        orig_session = database.AsyncSessionLocal
        
        new_engine = create_async_engine(
            f"sqlite+aiosqlite:///{test_db_path}",
            echo=False,
            connect_args={"check_same_thread": False, "timeout": 30.0}
        )
        new_sessionmaker = async_sessionmaker(
            bind=new_engine, class_=AsyncSession, expire_on_commit=False
        )
        database.engine = new_engine
        database.AsyncSessionLocal = new_sessionmaker

        try:
            # 运行初始化
            await database.init_db()

            # 验证数据库数据
            conn = sqlite3.connect(str(test_db_path))
            c = conn.cursor()
            
            c.execute("SELECT count(*) FROM official_snapshots")
            snap_count = c.fetchone()[0]
            print(f"✅ 快照总数: {snap_count} (预期 20)")
            assert snap_count == 20, f"Expected 20 snapshots, got {snap_count}"

            c.execute("SELECT is_current, count(*) FROM official_model_prices GROUP BY is_current")
            status_counts = dict(c.fetchall())
            print(f"✅ 模型状态分布: {status_counts} (预期 1: 598, 0: 30)")
            assert status_counts.get(1) == 598, f"Expected 598 current models, got {status_counts.get(1)}"
            assert status_counts.get(0) == 30, f"Expected 30 historical models, got {status_counts.get(0)}"

            # 检查 snapshot_id 映射
            c.execute("SELECT count(*) FROM official_model_prices WHERE snapshot_id IS NULL")
            null_snaps = c.fetchone()[0]
            print(f"✅ 孤立无快照模型数: {null_snaps} (预期 0)")
            assert null_snaps == 0, f"Expected 0 unmapped models, got {null_snaps}"

            # 检查批次日期
            c.execute("SELECT DISTINCT strftime('%Y-%m-%d', captured_at) FROM official_snapshots ORDER BY 1 DESC")
            batches = [r[0] for r in c.fetchall()]
            print(f"✅ 快照批次分布: {batches} (必须包含 2026-09-11)")
            assert "2026-09-11" in batches, "2026-09-11 batch missing in fresh install!"

            conn.close()
        finally:
            await new_engine.dispose()
            database.engine = orig_engine
            database.AsyncSessionLocal = orig_session

async def test_upgrade_from_old_version():
    print("\n--- [TEST 2] 测试存量旧版本覆盖升级 (模拟只有 2026-09-04 批次的旧数据库) ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_upgrade.db"
        
        # 1. 预先构造旧版数据库 (仅有 2026-09-04 批次)
        conn = sqlite3.connect(str(test_db_path))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE official_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(50) NOT NULL,
                source_url VARCHAR(500),
                page_title VARCHAR(200),
                local_file_path VARCHAR(500),
                file_size_bytes INTEGER DEFAULT 0,
                models_count INTEGER DEFAULT 0,
                captured_at DATETIME
            );
        """)
        c.execute("""
            CREATE TABLE official_model_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(50) NOT NULL,
                provider_name VARCHAR(100) NOT NULL,
                series VARCHAR(100) DEFAULT 'other',
                model_name VARCHAR(150) NOT NULL,
                raw_model_id VARCHAR(150) DEFAULT '',
                billing_mode VARCHAR(50) DEFAULT 'Standard',
                tier_range VARCHAR(100) DEFAULT '无阶梯',
                currency VARCHAR(10) NOT NULL,
                input_price FLOAT NOT NULL,
                output_price FLOAT NOT NULL,
                cache_read_price FLOAT DEFAULT 0.0,
                cache_write_price FLOAT DEFAULT 0.0,
                remarks TEXT DEFAULT '',
                custom_notes TEXT DEFAULT '',
                user_tags VARCHAR(255) DEFAULT '',
                price_date VARCHAR(30) DEFAULT '',
                source_page_url VARCHAR(500) DEFAULT '',
                source_anchor VARCHAR(200) DEFAULT '',
                snapshot_id INTEGER,
                is_current BOOLEAN DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # 插入旧版 10 个 2026-09-04 快照
        providers = ["deepseek", "zhipuai", "moonshotai", "minimax", "alibaba", "xiaomi", "stepfun", "openai", "anthropic", "google"]
        for i, prov in enumerate(providers, 1):
            c.execute("""
                INSERT INTO official_snapshots (id, provider, source_url, page_title, local_file_path, file_size_bytes, models_count, captured_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (i, prov, f"https://{prov}.com", f"{prov} 官方定价", f"data/official_snapshots/sample_{prov}.html", 1000, 5, "2026-09-04 08:00:00"))
            # 插入旧价格
            c.execute("""
                INSERT INTO official_model_prices (provider, provider_name, model_name, currency, input_price, output_price, price_date, snapshot_id, is_current)
                VALUES (?, ?, ?, 'CNY', 10.0, 20.0, '2026-09-04 08:00:00', ?, 1)
            """, (prov, prov, f"{prov}-old-model", i))
        
        conn.commit()
        conn.close()

        # 2. 模拟运行新版 init_db()
        from backend.app import database
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        
        orig_engine = database.engine
        orig_session = database.AsyncSessionLocal
        
        new_engine = create_async_engine(
            f"sqlite+aiosqlite:///{test_db_path}",
            echo=False,
            connect_args={"check_same_thread": False, "timeout": 30.0}
        )
        new_sessionmaker = async_sessionmaker(
            bind=new_engine, class_=AsyncSession, expire_on_commit=False
        )
        database.engine = new_engine
        database.AsyncSessionLocal = new_sessionmaker

        try:
            await database.init_db()

            # 3. 验证升级结果
            conn = sqlite3.connect(str(test_db_path))
            c = conn.cursor()

            # 快照总数应该保留旧记录并增量扩充最新快照
            c.execute("SELECT count(*) FROM official_snapshots")
            snap_count = c.fetchone()[0]
            print(f"✅ 升级后快照总数: {snap_count} (预期 >= 20)")
            assert snap_count >= 20, f"Expected at least 20 snapshots after upgrade, got {snap_count}"

            # 验证批次包含 2026-09-11 和 2026-09-04
            c.execute("SELECT DISTINCT strftime('%Y-%m-%d', captured_at) FROM official_snapshots ORDER BY 1 DESC")
            batches = [r[0] for r in c.fetchall()]
            print(f"✅ 升级后批次分布: {batches} (必须包含 2026-09-11 与 2026-09-04)")
            assert "2026-09-11" in batches, "2026-09-11 batch missing after upgrade!"

            # 验证当前生效模型必须是 2026-09-11 批次
            c.execute("SELECT count(*) FROM official_model_prices WHERE is_current = 1")
            active_count = c.fetchone()[0]
            print(f"✅ 当前生效最新模型数: {active_count} (预期 598)")
            assert active_count == 598, f"Expected 598 active models, got {active_count}"

            # 验证旧模型是否降级为历史版本 (is_current = 0)
            c.execute("SELECT count(*) FROM official_model_prices WHERE is_current = 0")
            hist_count = c.fetchone()[0]
            print(f"✅ 归档历史模型数 (含旧版与历史基准): {hist_count}")
            assert hist_count >= 10, f"Expected at least 10 historical models, got {hist_count}"

            # 验证旧模型 deepseek-old-model 是否依然保留为 is_current=0
            c.execute("SELECT is_current FROM official_model_prices WHERE model_name = 'deepseek-old-model'")
            row = c.fetchone()
            assert row and row[0] == 0, "Old model should be downgraded to is_current=0"
            print("✅ 原始旧模型成功归档为历史参考！")

            conn.close()
        finally:
            await new_engine.dispose()
            database.engine = orig_engine
            database.AsyncSessionLocal = orig_session

async def main():
    await test_fresh_install()
    await test_upgrade_from_old_version()
    print("\n🎉 全部全新安装与覆盖升级双场景验证 100% 通过！\n")

if __name__ == "__main__":
    asyncio.run(main())
