"""
阶跃星辰 (StepFun) 官方模型定价抓取、快照生成与官方基准模型自动化测试
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
    print("=== 1. 测试 OFFICIAL_TARGETS 中包含阶跃星辰 (StepFun) ===")
    assert "stepfun" in OFFICIAL_TARGETS, "OFFICIAL_TARGETS 中必须包含 stepfun"
    stepfun_target = OFFICIAL_TARGETS["stepfun"]
    assert stepfun_target["code"] == "stepfun"
    assert stepfun_target["currency"] == "CNY"
    assert "stepfun.com" in stepfun_target["url"]
    print("✓ OFFICIAL_TARGETS 配置验证通过:", stepfun_target)

    print("\n=== 2. 测试 parse_stepfun 解析引擎 ===")
    sample_file = os.path.join(os.getcwd(), "data", "official_snapshots", "sample_stepfun.html")
    assert os.path.exists(sample_file), f"本地快照文件必须存在: {sample_file}"
    with open(sample_file, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    items = official_scraper_service.parse_stepfun(soup, stepfun_target["url"], snapshot_id=888)
    print(f"✓ parse_stepfun 成功解析模型规格数: {len(items)}")
    assert len(items) >= 9, f"预期至少解析 9 款阶跃星辰 Token 计费模型，实际为: {len(items)}"

    # 验证 flagship 多模态推理模型 step-3.7-flash
    step37 = next((m for m in items if m["raw_model_id"] == "step-3.7-flash"), None)
    assert step37 is not None, "未找到 step-3.7-flash 模型规格"
    assert step37["input_price"] == 1.35, f"step-3.7-flash 输入价应为 1.35，实际: {step37['input_price']}"
    assert step37["output_price"] == 8.1, f"step-3.7-flash 输出价应为 8.1，实际: {step37['output_price']}"
    assert step37["cache_read_price"] == 0.27, f"step-3.7-flash 缓存命中价应为 0.27，实际: {step37['cache_read_price']}"
    assert step37["currency"] == "CNY"
    print("✓ step-3.7-flash 定价参数校验通过:", step37)

    # 验证推理大模型 step-3.5-flash
    step35 = next((m for m in items if m["raw_model_id"] == "step-3.5-flash"), None)
    assert step35 is not None, "未找到 step-3.5-flash 模型规格"
    assert step35["input_price"] == 0.7, f"step-3.5-flash 输入价应为 0.7，实际: {step35['input_price']}"
    assert step35["output_price"] == 2.1, f"step-3.5-flash 输出价应为 2.1，实际: {step35['output_price']}"
    assert step35["cache_read_price"] == 0.14, f"step-3.5-flash 缓存命中价应为 0.14，实际: {step35['cache_read_price']}"
    print("✓ step-3.5-flash 定价参数校验通过:", step35)

    # 验证视觉大模型 step-1o-turbo-vision
    step1o = next((m for m in items if m["raw_model_id"] == "step-1o-turbo-vision"), None)
    assert step1o is not None, "未找到 step-1o-turbo-vision 模型规格"
    assert step1o["input_price"] == 2.5, f"step-1o 输入价应为 2.5，实际: {step1o['input_price']}"
    assert step1o["output_price"] == 8.0, f"step-1o 输出价应为 8.0，实际: {step1o['output_price']}"
    assert step1o["cache_read_price"] == 0.5, f"step-1o 缓存命中价应为 0.5，实际: {step1o['cache_read_price']}"
    print("✓ step-1o-turbo-vision 定价参数校验通过:", step1o)

    # 验证端到端语音模型 stepaudio-2.5-chat
    audio_model = next((m for m in items if m["raw_model_id"] == "stepaudio-2.5-chat"), None)
    assert audio_model is not None, "未找到 stepaudio-2.5-chat 模型规格"
    assert audio_model["input_price"] == 10.0, f"audio 输入价应为 10.0，实际: {audio_model['input_price']}"
    assert audio_model["output_price"] == 25.0, f"audio 输出价应为 25.0，实际: {audio_model['output_price']}"
    assert audio_model["cache_read_price"] == 2.0, f"audio 缓存价应为 2.0，实际: {audio_model['cache_read_price']}"
    print("✓ stepaudio-2.5-chat 定价参数校验通过:", audio_model)

    print("\n=== 3. 测试 scrape_target('stepfun') 数据入库与快照更新 ===")
    count, err = await official_scraper_service.scrape_target("stepfun", use_local_sample=True)
    assert err is None, f"抓取入库发生异常: {err}"
    assert count >= 9, f"入库数量预期 >= 9，实际为: {count}"

    async with AsyncSessionLocal() as session:
        # 验证数据库持久化
        db_res = await session.execute(
            select(OfficialModelPrice).where(OfficialModelPrice.provider == "stepfun")
        )
        db_models = db_res.scalars().all()
        assert len(db_models) == count, f"数据库实际记录数 ({len(db_models)}) 与入库数 ({count}) 不一致"
        print(f"✓ 数据库中已安全持久化 {len(db_models)} 款阶跃星辰官方模型")

        # 验证快照记录
        snap_res = await session.execute(
            select(OfficialSnapshot).where(OfficialSnapshot.provider == "stepfun").order_by(OfficialSnapshot.id.desc())
        )
        snap = snap_res.scalars().first()
        assert snap is not None, "快照记录不存在"
        assert os.path.exists(os.path.join(os.getcwd(), snap.local_file_path)), "快照文件本地磁盘必须存在"
        print(f"✓ 成功校验快照记录: ID={snap.id}, 标题={snap.page_title}, 磁盘路径={snap.local_file_path}")

        print("\n=== 4. 测试 official_benchmark_service 基准模型联动 ===")
        benchmarks = await official_benchmark_service.get_benchmark_models(session)
        stepfun_bms = [b for b in benchmarks if b.get("provider") == "stepfun"]
        assert len(stepfun_bms) >= 4, f"基准模型应收录阶跃星辰主力模型，实际为: {len(stepfun_bms)}"
        flash_bm = next((b for b in stepfun_bms if b.get("raw_model_id") == "step-3.7-flash"), None)
        assert flash_bm is not None, "step-3.7-flash 应作为第一档基准模型"
        assert flash_bm["converted_input_cny"] == 1.35, f"人民币基准价应为 1.35，实际: {flash_bm['converted_input_cny']}"
        assert flash_bm["converted_input_usd"] > 0, f"美元折算价应 > 0，实际: {flash_bm['converted_input_usd']}"
        print("✓ 基准模型引擎成功收录阶跃星辰基准模型:", flash_bm)

        print("\n=== 5. 测试名称标准化模糊匹配支持 stepfun ===")
        norm_res = official_benchmark_service._normalize_name("stepfun/step-3.7-flash")
        assert norm_res == "step37flash", f"去前缀标准化结果异常: {norm_res}"
        print("✓ _normalize_name 成功剥离 stepfun/ 前缀并规整:", norm_res)

    print("\n🎉 全部阶跃星辰 (StepFun) 官方定价、解析入库与快照测试 100% 成功通过！")


if __name__ == "__main__":
    asyncio.run(main())
