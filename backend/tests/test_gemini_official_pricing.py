"""
Google (Gemini) 官方模型定价抓取、Gemini 3.8 Flash / 3.7 Flash 新模型规格识别及权威英文定价页自动化测试
"""
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import OfficialModelPrice, OfficialSnapshot
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS


async def main():
    print("=== 1. 测试 OFFICIAL_TARGETS 中 Gemini 的配置 ===")
    assert "gemini" in OFFICIAL_TARGETS, "OFFICIAL_TARGETS 中必须包含 gemini"
    gemini_target = OFFICIAL_TARGETS["gemini"]
    assert gemini_target["code"] == "google"
    assert gemini_target["currency"] == "USD"
    expected_url = "https://ai.google.dev/gemini-api/docs/pricing"
    assert gemini_target["url"] == expected_url, f"Gemini URL 应为 {expected_url} (避免中文本地化滞后缺失新模型), 实际为 {gemini_target['url']}"
    print(f"✓ OFFICIAL_TARGETS 配置验证通过: URL = {gemini_target['url']}")

    print("\n=== 2. 测试 parse_gemini 对权威快照 sample_gemini.html 的解析 ===")
    sample_file = Path("data/official_snapshots/sample_gemini.html")
    assert sample_file.exists(), "sample_gemini.html 快照必须存在"
    with open(sample_file, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    items = official_scraper_service.parse_gemini(soup, gemini_target["url"], snapshot_id=999)
    print(f"✓ sample_gemini.html 成功解析出 {len(items)} 款模型规格")
    assert len(items) >= 70, f"解析模型数应至少 70 款，实际解析出 {len(items)} 款"

    # 检查 Gemini 3.8 Flash
    g38_items = [m for m in items if "Gemini 3.8 Flash" in m["model_name"]]
    print(f"✓ 解析出的 Gemini 3.8 Flash 规格数: {len(g38_items)}")
    assert len(g38_items) == 4, f"Gemini 3.8 Flash 应有 4 种计费模式规格，实际为 {len(g38_items)}"

    standard_38 = next((m for m in g38_items if m["billing_mode"] == "Standard"), None)
    assert standard_38 is not None, "必须包含 Standard 标准模式"
    assert standard_38["input_price"] == 0.75, f"Standard 输入价应为 0.75，实际为 {standard_38['input_price']}"
    assert standard_38["output_price"] == 3.75, f"Standard 输出价应为 3.75，实际为 {standard_38['output_price']}"
    print("✓ Gemini 3.8 Flash (Standard) 定价校验通过: $0.75 / $3.75")

    batch_38 = next((m for m in g38_items if "Batch" in m["billing_mode"]), None)
    assert batch_38 is not None, "必须包含 Batch 模式"
    assert batch_38["input_price"] == 0.375, f"Batch 输入价应为 0.375，实际为 {batch_38['input_price']}"
    assert batch_38["output_price"] == 1.875, f"Batch 输出价应为 1.875，实际为 {batch_38['output_price']}"
    print("✓ Gemini 3.8 Flash (Batch) 定价校验通过: $0.375 / $1.875")

    # 检查 Gemini 3.7 Flash
    g37_items = [m for m in items if "Gemini 3.7 Flash" in m["model_name"]]
    print(f"✓ 解析出的 Gemini 3.7 Flash 规格数: {len(g37_items)}")
    assert len(g37_items) >= 1, "必须包含 Gemini 3.7 Flash"

    print("\n=== 3. 校验数据库中当前生效的 Google 模型 ===")
    async with AsyncSessionLocal() as session:
        stmt = (
            select(OfficialModelPrice)
            .where(OfficialModelPrice.provider == "google")
            .where(OfficialModelPrice.is_current == True)
        )
        res = await session.execute(stmt)
        active_google = res.scalars().all()
        print(f"✓ 数据库中当前生效的 Google 模型规格总数: {len(active_google)}")
        assert len(active_google) >= 70, f"当前生效的 Google 模型数应不少于 70，实际为 {len(active_google)}"

        db_38 = [m for m in active_google if "Gemini 3.8 Flash" in m.model_name]
        assert len(db_38) == 4, f"当前生效的模型中应包含 4 种 Gemini 3.8 Flash 规格，实际为 {len(db_38)}"
        for m in db_38:
            print(f"  - [{m.model_name}] 模式: {m.billing_mode}, 输入: ${m.input_price}, 输出: ${m.output_price}, 快照ID: {m.snapshot_id}")

    print("\n🎉 全部 Google (Gemini) 官方模型定价测试用例均验证通过！")


if __name__ == "__main__":
    asyncio.run(main())
