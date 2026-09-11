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
        print(f"[{idx}/{len(targets)}] 正在抓取更新: {target_info['name']} ({target_key})...")
        try:
            # 允许网络抓取；若网络超时则降级使用本地样本
            count, err = await official_scraper_service.scrape_target(target_key, use_local_sample=False)
            if err:
                print(f"    ⚠️ 网络抓取遇到异常 ({err})，尝试本地离线样本降级...")
                count, err2 = await official_scraper_service.scrape_target(target_key, use_local_sample=True)
                if err2:
                    print(f"    ❌ 抓取失败: {err2}")
                    results[target_key] = {"count": 0, "status": f"error: {err2}"}
                else:
                    print(f"    ✅ 离线样本抓取解析成功: {count} 个模型规格")
                    results[target_key] = {"count": count, "status": "success (offline fallback)"}
            else:
                print(f"    ✅ 在线抓取解析成功: {count} 个模型规格")
                results[target_key] = {"count": count, "status": "success (online live)"}
        except Exception as e:
            print(f"    ❌ 抓取异常: {e}")
            results[target_key] = {"count": 0, "status": f"exception: {e}"}

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

        # 4. 导出当前全部官方模型价格到 official_prices_seed.json 保证打包与只读运行
        print("\n>>> 正在导出至 data/official_prices_seed.json 种子文件...")
        all_curr_res = await session.execute(
            select(OfficialModelPrice).where(OfficialModelPrice.is_current == True).order_by(OfficialModelPrice.id.asc())
        )
        curr_models = all_curr_res.scalars().all()

        seed_data = []
        for m in curr_models:
            seed_data.append({
                "provider": m.provider,
                "provider_name": m.provider_name,
                "series": m.series,
                "model_name": m.model_name,
                "raw_model_id": m.raw_model_id,
                "billing_mode": m.billing_mode,
                "tier_range": m.tier_range,
                "currency": m.currency,
                "input_price": m.input_price,
                "output_price": m.output_price,
                "cache_read_price": m.cache_read_price,
                "cache_write_price": m.cache_write_price,
                "remarks": m.remarks,
                "custom_notes": m.custom_notes,
                "user_tags": m.user_tags,
                "price_date": m.price_date,
                "source_page_url": m.source_page_url,
                "source_anchor": m.source_anchor,
                "is_active": m.is_active,
            })

        seed_path = DATA_DIR / "official_prices_seed.json"
        with open(seed_path, "w", encoding="utf-8") as f:
            json.dump(seed_data, f, ensure_ascii=False, indent=2)
        print(f"    ✅ 种子文件导出成功: {len(seed_data)} 条模型，路径: {seed_path}")


if __name__ == "__main__":
    asyncio.run(prepare_history_and_latest())
