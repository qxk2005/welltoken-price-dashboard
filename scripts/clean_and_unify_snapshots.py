"""
统一快照日期维度与数据去重瘦身脚本
规则：每天每个厂商以最后一次（最新）抓取的快照为准，清理当天较早的冗余快照、价格记录及无用本地快照文件。
最新日期（2026-09-11）的 10 家厂商快照作为当前生效基准 (is_current = True)。
"""
import os
import sys
import json
import asyncio
from pathlib import Path
from collections import defaultdict
from sqlalchemy import select, delete, update

# 添加项目根目录到 sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import OfficialSnapshot, OfficialModelPrice


async def clean_and_unify():
    print("=== 开始执行快照统一日期整理与数据清洗 ===")
    async with AsyncSessionLocal() as db:
        # 1. 查询所有快照
        snaps_res = await db.execute(select(OfficialSnapshot).order_by(OfficialSnapshot.captured_at.asc()))
        all_snapshots = snaps_res.scalars().all()
        print(f"当前数据库共有快照: {len(all_snapshots)} 份")

        # 2. 按 (day, provider) 分组
        grouped = defaultdict(list)
        for s in all_snapshots:
            day = str(s.captured_at)[:10]
            grouped[(day, s.provider)].append(s)

        keepers = []
        to_delete_snaps = []

        for (day, provider), slist in grouped.items():
            # 按 captured_at 升序，最后一个为最新
            latest = slist[-1]
            keepers.append(latest)
            if len(slist) > 1:
                for old in slist[:-1]:
                    to_delete_snaps.append(old)

        print(f"保留最新基准快照: {len(keepers)} 份，待清理冗余快照: {len(to_delete_snaps)} 份")

        keeper_files = set(os.path.abspath(k.local_file_path) for k in keepers if k.local_file_path)
        deleted_files_count = 0

        # 3. 删除冗余快照及下属价格点
        for old in to_delete_snaps:
            # 删除价格点
            await db.execute(
                delete(OfficialModelPrice).where(OfficialModelPrice.snapshot_id == old.id)
            )
            # 物理删除无用 html 文件（保留 sample_*.html 与 keeper 使用的文件）
            if old.local_file_path:
                abs_path = os.path.abspath(old.local_file_path)
                fname = os.path.basename(abs_path)
                if not fname.startswith("sample_") and abs_path not in keeper_files:
                    try:
                        if os.path.exists(abs_path):
                            os.remove(abs_path)
                            deleted_files_count += 1
                    except Exception as e:
                        print(f"清理文件失败 {abs_path}: {e}")

            # 删除快照记录
            await db.execute(
                delete(OfficialSnapshot).where(OfficialSnapshot.id == old.id)
            )

        await db.commit()
        print(f"成功清理 {len(to_delete_snaps)} 份冗余快照，删除 {deleted_files_count} 个冗余 HTML 快照文件")

        # 4. 重新设置 is_current 状态
        # 找出最大的日期（最新日期，即 2026-09-11）
        all_days = sorted(set(str(k.captured_at)[:10] for k in keepers), reverse=True)
        latest_day = all_days[0] if all_days else None
        print(f"当前最新生效基准日期为: {latest_day}")

        # 先将所有记录 is_current 置为 False
        await db.execute(update(OfficialModelPrice).values(is_current=False))

        # 将 latest_day 的 keeper 对应的价格置为 True
        latest_keeper_ids = [k.id for k in keepers if str(k.captured_at)[:10] == latest_day]
        await db.execute(
            update(OfficialModelPrice)
            .where(OfficialModelPrice.snapshot_id.in_(latest_keeper_ids))
            .values(is_current=True)
        )
        await db.commit()

        # 5. 统计核查当前生效模型数
        curr_res = await db.execute(
            select(OfficialModelPrice).where(OfficialModelPrice.is_current == True)
        )
        current_models = curr_res.scalars().all()
        print(f"清洗完成！最新生效日期 {latest_day} 下共有 {len(current_models)} 款官方模型生效中")

        # 6. 同步导出至种子文件 data/official_prices_seed.json
        seed_path = Path("data/official_prices_seed.json")
        seed_data = []
        for m in current_models:
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
                "is_current": True,
                "is_active": True
            })

        with open(seed_path, "w", encoding="utf-8") as f:
            json.dump(seed_data, f, ensure_ascii=False, indent=2)
        print(f"已同步更新种子数据 -> {seed_path} ({len(seed_data)} 条)")


if __name__ == "__main__":
    asyncio.run(clean_and_unify())
