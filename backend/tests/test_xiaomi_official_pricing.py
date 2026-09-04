"""
小米 (Xiaomi MiMo) 官方模型定价抓取、快照生成与官方基准模型自动化测试
"""
import asyncio
import os
from bs4 import BeautifulSoup
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import OfficialModelPrice, OfficialSnapshot
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS
from backend.app.services.official_benchmark_service import official_benchmark_service


async def main():
    print("=== 1. 测试 OFFICIAL_TARGETS 中包含小米 ===")
    assert "xiaomi" in OFFICIAL_TARGETS, "OFFICIAL_TARGETS 中必须包含 xiaomi"
    xiaomi_target = OFFICIAL_TARGETS["xiaomi"]
    assert xiaomi_target["code"] == "xiaomi"
    assert xiaomi_target["currency"] == "CNY"
    assert "mimo.mi.com" in xiaomi_target["url"]
    print("✓ OFFICIAL_TARGETS 配置验证通过:", xiaomi_target)

    print("\n=== 2. 测试 parse_xiaomi 解析引擎 ===")
    sample_file = os.path.join(os.getcwd(), "data", "official_snapshots", "sample_xiaomi.html")
    assert os.path.exists(sample_file), f"本地快照文件必须存在: {sample_file}"
    with open(sample_file, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    items = official_scraper_service.parse_xiaomi(soup, xiaomi_target["url"], snapshot_id=999)
    print(f"✓ parse_xiaomi 成功解析模型规格数: {len(items)}")
    assert len(items) >= 6, f"预期至少解析 6 款小米模型规格，实际为: {len(items)}"

    # 验证 flagship 语言模型
    pro_model = next((m for m in items if m["raw_model_id"] == "mimo-v2.5-pro"), None)
    assert pro_model is not None, "未找到 mimo-v2.5-pro 模型规格"
    assert pro_model["input_price"] == 3.0, f"pro 输入价应为 3.0，实际: {pro_model['input_price']}"
    assert pro_model["output_price"] == 6.0, f"pro 输出价应为 6.0，实际: {pro_model['output_price']}"
    assert pro_model["cache_read_price"] == 0.025, f"pro 缓存价应为 0.025，实际: {pro_model['cache_read_price']}"
    assert pro_model["currency"] == "CNY"
    print("✓ mimo-v2.5-pro 定价参数校验通过:", pro_model)

    std_model = next((m for m in items if m["raw_model_id"] == "mimo-v2.5"), None)
    assert std_model is not None, "未找到 mimo-v2.5 模型规格"
    assert std_model["input_price"] == 1.0, f"std 输入价应为 1.0，实际: {std_model['input_price']}"
    assert std_model["output_price"] == 2.0, f"std 输出价应为 2.0，实际: {std_model['output_price']}"
    assert std_model["cache_read_price"] == 0.02, f"std 缓存价应为 0.02，实际: {std_model['cache_read_price']}"
    print("✓ mimo-v2.5 定价参数校验通过:", std_model)

    asr_model = next((m for m in items if m["raw_model_id"] == "mimo-v2.5-asr"), None)
    assert asr_model is not None, "未找到 mimo-v2.5-asr 音频模型规格"
    assert asr_model["input_price"] == 0.5, f"asr 输入价应为 0.5，实际: {asr_model['input_price']}"
    print("✓ mimo-v2.5-asr 定价参数校验通过:", asr_model)

    tts_model = next((m for m in items if m["raw_model_id"] == "mimo-v2.5-tts"), None)
    assert tts_model is not None, "未找到 mimo-v2.5-tts 语音合成规格"
    assert tts_model["tier_range"] == "限时免费"
    assert tts_model["input_price"] == 0.0
    print("✓ mimo-v2.5-tts 限免参数校验通过:", tts_model)

    print("\n=== 3. 测试 scrape_target('xiaomi') 数据入库与快照更新 ===")
    count, err = await official_scraper_service.scrape_target("xiaomi", use_local_sample=True)
    assert err is None, f"抓取入库发生异常: {err}"
    assert count >= 6, f"入库数量预期 >= 6，实际为: {count}"

    async with AsyncSessionLocal() as session:
        # 验证数据库记录
        db_res = await session.execute(
            select(OfficialModelPrice).where(OfficialModelPrice.provider == "xiaomi")
        )
        db_models = db_res.scalars().all()
        assert len(db_models) == count, f"数据库实际记录数 ({len(db_models)}) 与入库数 ({count}) 不一致"
        print(f"✓ 数据库中已安全持久化 {len(db_models)} 款小米官方模型")

        # 验证快照记录
        snap_res = await session.execute(
            select(OfficialSnapshot).where(OfficialSnapshot.provider == "xiaomi").order_by(OfficialSnapshot.id.desc())
        )
        snap = snap_res.scalars().first()
        assert snap is not None, "快照记录不存在"
        assert os.path.exists(os.path.join(os.getcwd(), snap.local_file_path)), "快照文件本地磁盘必须存在"
        print(f"✓ 成功校验快照记录: ID={snap.id}, 标题={snap.page_title}, 磁盘路径={snap.local_file_path}")

        print("\n=== 4. 测试 official_benchmark_service 基准模型联动 ===")
        benchmarks = await official_benchmark_service.get_benchmark_models(session)
        xiaomi_bms = [b for b in benchmarks if b.get("provider") == "xiaomi"]
        assert len(xiaomi_bms) >= 2, f"基准模型应收录小米主力模型，实际为: {len(xiaomi_bms)}"
        mimo_bm = next((b for b in xiaomi_bms if b.get("raw_model_id") == "mimo-v2.5"), None)
        assert mimo_bm is not None, "mimo-v2.5 应作为基准模型"
        assert mimo_bm["converted_input_cny"] == 1.0, f"人民币基准价应为 1.0，实际: {mimo_bm['converted_input_cny']}"
        assert mimo_bm["converted_input_usd"] > 0, f"美元折算价应 > 0，实际: {mimo_bm['converted_input_usd']}"
        print("✓ 基准模型引擎成功收录小米基准模型:", mimo_bm)

    print("\n🎉 全部小米官方定价与快照测试 100% 成功通过！")


if __name__ == "__main__":
    asyncio.run(main())
