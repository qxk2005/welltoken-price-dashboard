"""
官方定价全量抓取与双版本历史数据构建脚本
同步全部 10 家厂商 (境外 3 家 + 境内 7 家)，保存证据链快照，建立历史版本与最新生效版本，导出种子文件。
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime

# 加入项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.database import AsyncSessionLocal, init_db
from backend.app.config import DATA_DIR
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS
from backend.app.models.token_price import OfficialModelPrice, OfficialSnapshot
from sqlalchemy import select, update, func


async def prepare_history_and_latest():
    print(">>> 正在初始化数据库环境...")
    await init_db()

    # 1. 检查当前已有价格记录
    async with AsyncSessionLocal() as session:
        count_res = await session.execute(select(func.count(OfficialModelPrice.id)))
        total_prices = count_res.scalar() or 0
        snap_count_res = await session.execute(select(func.count(OfficialSnapshot.id)))
        total_snaps = snap_count_res.scalar() or 0
        print(f"当前数据库状态: {total_prices} 条官方价格记录, {total_snaps} 份快照")

        # 将当前现有的所有有效价格设为历史版本 (is_current = False)，以此作为坚实的第一版历史基线
        if total_prices > 0:
            print(">>> 正在将现有批次归档为历史基线版本 (is_current = False)...")
            await session.execute(
                update(OfficialModelPrice)
                .where(OfficialModelPrice.is_active == True)
                .values(is_current=False)
            )
            await session.commit()

    # 2. 全量抓取全部 10 家官方厂商最新价格与生成全新快照 (is_current = True)
    print("\n>>> 开始抓取解析全部 10 家官方厂商最新价格表...")
    targets = list(OFFICIAL_TARGETS.keys())
    results = {}

    for idx, target_key in enumerate(targets, 1):
        target_info = OFFICIAL_TARGETS[target_key]
        print(f"[{idx}/{len(targets)}] 正在在线抓取更新: {target_info['name']} ({target_key})...")
        
        # 强制在线抓取，遇到网络抖动自动指数退避重试最多 3 次 (严格遵守严禁静默 fallback 规范)
        max_retries = 3
        success = False
        last_err = None
        count = 0

        for attempt in range(1, max_retries + 1):
            try:
                count, err = await official_scraper_service.scrape_target(target_key, use_local_sample=False)
                if not err and count > 0:
                    print(f"    ✅ 在线抓取解析成功: {count} 个模型规格 (尝试 {attempt}/{max_retries})")
                    results[target_key] = {"count": count, "status": "success (online live)"}
                    success = True
                    break
                else:
                    last_err = err or "解析到的模型规格为 0"
                    print(f"    ⚠️ 尝试 {attempt}/{max_retries} 失败: {last_err}")
            except Exception as e:
                last_err = str(e)
                print(f"    ⚠️ 尝试 {attempt}/{max_retries} 异常: {last_err}")

            if attempt < max_retries:
                wait_sec = attempt * 3
                print(f"    ⏳ 等待 {wait_sec} 秒后重试...")
                await asyncio.sleep(wait_sec)

        if not success:
            print(f"    ❌ 最终抓取失败: {last_err}")
            results[target_key] = {"count": 0, "status": f"error: {last_err}"}

    # 3. 统计最新与历史状态
    async with AsyncSessionLocal() as session:
        curr_res = await session.execute(
            select(func.count(OfficialModelPrice.id)).where(OfficialModelPrice.is_current == True)
        )
        curr_count = curr_res.scalar() or 0

        hist_res = await session.execute(
            select(func.count(OfficialModelPrice.id)).where(OfficialModelPrice.is_current == False)
        )
        hist_count = hist_res.scalar() or 0

        print(f"\n>>> 抓取入库完成! 当前最新生效模型数: {curr_count}, 历史回溯模型点数: {hist_count}")

    # 4. 调用全量种子导出脚本，生成最新的 official_prices_seed.json 与 official_snapshots_seed.json
    print("\n>>> 正在导出全量种子文件 (official_prices_seed.json & official_snapshots_seed.json)...")
    from scripts.export_full_seeds import export_seeds
    export_seeds()
    print(">>> 种子文件导出完毕!")


if __name__ == "__main__":
    asyncio.run(prepare_history_and_latest())
