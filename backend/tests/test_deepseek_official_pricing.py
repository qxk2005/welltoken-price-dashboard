"""
DeepSeek (深度求索) 官方模型定价解析、纯净模型命名清洗与政策注解提取自动化测试
"""
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import OfficialModelPrice
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS


async def main():
    print("=== 1. 测试 OFFICIAL_TARGETS 中 DeepSeek 的配置 ===")
    assert "deepseek" in OFFICIAL_TARGETS, "OFFICIAL_TARGETS 中必须包含 deepseek"
    ds_target = OFFICIAL_TARGETS["deepseek"]
    assert ds_target["code"] == "deepseek"
    assert ds_target["currency"] == "CNY"
    print(f"✓ OFFICIAL_TARGETS 配置验证通过: URL = {ds_target['url']}")

    print("\n=== 2. 测试 parse_deepseek 解析与角标数字清洗 ===")
    sample_file = Path("data/official_snapshots/sample_deepseek.html")
    assert sample_file.exists(), "sample_deepseek.html 快照必须存在"
    with open(sample_file, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    items = official_scraper_service.parse_deepseek(soup, ds_target["url"], snapshot_id=999)
    print(f"✓ sample_deepseek.html 成功解析出 {len(items)} 款模型规格")
    assert len(items) == 4, f"解析模型数应为 4 款，实际解析出 {len(items)} 款"

    # 验证模型名称与 raw_model_id 绝不包含 (1) 或 (2) 等角标无效数字
    for it in items:
        m_name = it["model_name"]
        raw_id = it["raw_model_id"]
        assert "(1)" not in m_name and "(2)" not in m_name, f"模型名称包含无效角标数字: {m_name}"
        assert "(1)" not in raw_id and "(2)" not in raw_id, f"raw_model_id 包含无效角标数字: {raw_id}"
        assert raw_id in {"deepseek-flash", "deepseek-v4-pro"}, f"raw_model_id 异常: {raw_id}"
        # 验证备注中收录了政策注解
        assert "官方注解" in it["remarks"], f"备注字段应包含官方注解: {it['remarks']}"
        print(f"  ✓ [{m_name}] raw_id: {raw_id}, in: ¥{it['input_price']}, out: ¥{it['output_price']}")

    print("\n=== 3. 校验数据库中当前生效的 DeepSeek 模型 ===")
    async with AsyncSessionLocal() as session:
        stmt = (
            select(OfficialModelPrice)
            .where(OfficialModelPrice.provider == "deepseek")
            .where(OfficialModelPrice.is_current == True)
        )
        res = await session.execute(stmt)
        active_ds = res.scalars().all()
        assert len(active_ds) == 4, f"当前生效的 DeepSeek 模型数应为 4，实际为 {len(active_ds)}"
        for m in active_ds:
            assert "(1)" not in m.model_name and "(2)" not in m.model_name, f"数据库模型名包含无效角标: {m.model_name}"
            assert "(1)" not in m.raw_model_id and "(2)" not in m.raw_model_id, f"数据库 raw_model_id 包含无效角标: {m.raw_model_id}"
            print(f"  ✓ [{m.model_name}] raw_id: {m.raw_model_id}, 模式: {m.billing_mode}, 输入: ¥{m.input_price}, 输出: ¥{m.output_price}")

    print("\n🎉 全部 DeepSeek (深度求索) 模型纯净命名与政策注解测试 100% 验证通过！")


if __name__ == "__main__":
    asyncio.run(main())
