"""
统一快照日期维度与数据去重瘦身脚本
规则：每天每个厂商以最后一次（最新或当前生效）抓取的快照为准，清理当天较早的冗余快照、作废模型记录及无用本地快照文件。
最新日期的 10 家厂商快照作为当前生效基准 (is_current = True)。
清洗完成后自动调用 export_full_seeds 导出干净的种子文件。
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
        # 1. 找出当前已标记为 is_current=True 的 snapshot_id 集合
        curr_res = await db.execute(
            select(OfficialModelPrice.snapshot_id)
            .where(OfficialModelPrice.is_current == True, OfficialModelPrice.snapshot_id.is_not(None))
            .distinct()
        )
        current_snap_ids = set(r[0] for r in curr_res.all())
        print(f"当前数据库中生效的 snapshot_ids: {current_snap_ids}")

        # 2. 查询所有快照
        snaps_res = await db.execute(
            select(OfficialSnapshot).order_by(OfficialSnapshot.captured_at.asc(), OfficialSnapshot.id.asc())
        )
        all_snapshots = snaps_res.scalars().all()
        print(f"当前数据库共有快照: {len(all_snapshots)} 份")

        # 3. 按 (day, provider) 分组
        grouped = defaultdict(list)
        for s in all_snapshots:
            day = str(s.captured_at)[:10] if s.captured_at else "unknown"
            grouped[(day, s.provider)].append(s)

        keepers = []
        to_delete_snaps = []

        for (day, provider), slist in grouped.items():
            # 优先选属于当前生效集合的快照；若均不在生效集合中，选该日最后一次抓取的最新快照
            curr_in_list = [s for s in slist if s.id in current_snap_ids]
            if curr_in_list:
                keeper = curr_in_list[-1]
            else:
                keeper = slist[-1]
            keepers.append(keeper)
            for s in slist:
                if s.id != keeper.id:
                    to_delete_snaps.append(s)

        print(f"保留基准快照: {len(keepers)} 份，待清理冗余快照: {len(to_delete_snaps)} 份")

        keeper_files = set(os.path.abspath(k.local_file_path) for k in keepers if k.local_file_path)
        deleted_files_count = 0

        # 4. 删除冗余快照及下属价格点
        for old in to_delete_snaps:
            # 删除旧价格记录
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

        # 5. 重新校准 is_current 状态
        # 找出最新日期（即当前抓取批次，如 2026-09-14）
        all_days = sorted(set(str(k.captured_at)[:10] for k in keepers), reverse=True)
        latest_day = all_days[0] if all_days else None
        print(f"当前最新生效基准日期为: {latest_day}")

        # 先将所有历史记录 is_current 置为 False
        await db.execute(update(OfficialModelPrice).values(is_current=False))

        # 将 latest_day 的 keeper 对应的价格置为 True
        latest_keeper_ids = [k.id for k in keepers if str(k.captured_at)[:10] == latest_day]
        await db.execute(
            update(OfficialModelPrice)
            .where(OfficialModelPrice.snapshot_id.in_(latest_keeper_ids))
            .values(is_current=True)
        )
        await db.commit()

        # 6. 统计核查当前生效模型数
        curr_res = await db.execute(
            select(OfficialModelPrice).where(OfficialModelPrice.is_current == True)
        )
        current_models = curr_res.scalars().all()
        print(f"清洗完成！最新生效日期 {latest_day} 下共有 {len(current_models)} 款官方模型生效中")

        # 验证这批模型中 (provider, model_name) 是否严格唯一
        seen = set()
        duplicates = []
        for m in current_models:
            key = (m.provider, m.model_name, m.billing_mode, m.tier_range)
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        assert len(duplicates) == 0, f"发现重复模型: {duplicates}"
        print(f"✓ 校验通过: 当前生效批次中所有 {len(current_models)} 款模型规格严格唯一，无任何重复！")

    # 7. 同步导出种子文件
    print("\n>>> 正在调用 scripts/export_full_seeds.py 同步全量干净种子...")
    from scripts.export_full_seeds import export_seeds
    export_seeds()
    print(">>> 种子文件同步完毕！")


if __name__ == "__main__":
    asyncio.run(clean_and_unify())
