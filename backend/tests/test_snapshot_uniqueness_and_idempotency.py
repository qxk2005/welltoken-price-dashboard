"""
官方快照批次厂商唯一性、模型唯一性及抓取幂等化自动化回归测试
"""
import asyncio
from sqlalchemy import select, func

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import OfficialSnapshot, OfficialModelPrice
from backend.app.api.v1.official_pricing import list_snapshots_grouped


async def main():
    print("=== 1. 测试 list_snapshots_grouped 批次内厂商唯一性与数据准确性 ===")
    async with AsyncSessionLocal() as db:
        groups = await list_snapshots_grouped(db)
        assert len(groups) > 0, "必须存在至少一个快照批次"

        latest_group = groups[0]
        print(f"最新批次: {latest_group['snapshot_date']}, 当前生效: {latest_group['is_current']}, 厂商数: {latest_group['total_providers']}, 模型数: {latest_group['total_models']}")
        assert latest_group["is_current"] == True, "最新批次必须是当前生效基准"
        assert latest_group["total_providers"] == 10, f"最新批次必须包含全部 10 家厂商，实际为: {latest_group['total_providers']}"

        for g in groups:
            prov_codes = [p["provider"] for p in g["providers"]]
            unique_prov_codes = set(prov_codes)
            assert len(prov_codes) == len(unique_prov_codes), f"批次 {g['snapshot_date']} 中存在重复厂商: {prov_codes}"
            assert g["total_providers"] == len(unique_prov_codes), f"批次 {g['snapshot_date']} 厂商计数异常: total_providers={g['total_providers']}, 实际唯一={len(unique_prov_codes)}"
            
            # 验证 models 总数与下属快照总数精确一致
            sum_models = sum(p["models_count"] for p in g["providers"])
            assert g["total_models"] == sum_models, f"批次 {g['snapshot_date']} 模型总数与各快照之和不符: total_models={g['total_models']}, sum={sum_models}"
            print(f"✓ 批次 {g['snapshot_date']} 校验通过: {g['total_providers']} 家厂商唯一，共 {g['total_models']} 款模型")

    print("\n=== 2. 测试数据库当前生效模型规格严格唯一 ===")
    async with AsyncSessionLocal() as db:
        curr_res = await db.execute(
            select(OfficialModelPrice).where(OfficialModelPrice.is_current == True)
        )
        current_models = curr_res.scalars().all()
        assert len(current_models) == latest_group["total_models"], f"当前生效模型数 ({len(current_models)}) 应与最新批次模型数 ({latest_group['total_models']}) 完全一致"

        seen_keys = set()
        duplicates = []
        for m in current_models:
            key = (m.provider, m.model_name, m.billing_mode, m.tier_range)
            if key in seen_keys:
                duplicates.append(key)
            seen_keys.add(key)
        assert len(duplicates) == 0, f"发现重复模型规格: {duplicates}"
        print(f"✓ 校验通过: 当前生效批次中所有 {len(current_models)} 款模型规格严格唯一，无任何重复！")

    print("\n=== 3. 测试全部 10 家厂商在最新批次中齐全收录 ===")
    expected_providers = {"alibaba", "anthropic", "deepseek", "google", "minimax", "moonshotai", "openai", "stepfun", "xiaomi", "zhipuai"}
    latest_providers = set(p["provider"] for p in latest_group["providers"])
    assert latest_providers == expected_providers, f"厂商收录不全: 期望 {expected_providers}, 实际 {latest_providers}"
    print(f"✓ 全部 10 家厂商全部齐备: {sorted(latest_providers)}")

    print("\n🎉 快照批次厂商唯一性与模型唯一性测试 100% 验证通过！")


if __name__ == "__main__":
    asyncio.run(main())
