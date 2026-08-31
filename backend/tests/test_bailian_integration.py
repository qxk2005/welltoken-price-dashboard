import asyncio
import sys
from backend.app.services.bailian_scraper import bailian_scraper
from backend.app.services.relay_fetcher import relay_fetcher
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, SiteModelPricing
from sqlalchemy import select

async def run_full_suite():
    print("=== 开始阿里百炼全流程集成测试 ===")
    
    # 1. 爬取
    res = await bailian_scraper.scrape_pricing_page()
    assert res.status == "success", f"爬取失败: {res.error_message}"
    print(f"✓ 爬取成功: {res.total_models} 款模型")
    
    # 2. 全量入库
    import_res = await bailian_scraper.save_to_database(res.models)
    assert import_res.status == "success", f"入库失败: {import_res.error_message}"
    print(f"✓ 入库成功: site_id={import_res.site_id}, 总导入规格={import_res.total_imported}")
    
    # 3. 验证数据库数据
    async with AsyncSessionLocal() as session:
        site = await session.get(RelaySite, import_res.site_id)
        assert site is not None
        assert site.site_type == "aliyun_bailian"
        
        stmt = select(SiteModelPricing).where(SiteModelPricing.site_id == site.id)
        prices = (await session.execute(stmt)).scalars().all()
        print(f"✓ 数据库中百炼渠道包含定价条目: {len(prices)} 条")
        assert len(prices) > 0
        
        # 抽查带区间的阶梯定价
        tiered_prices = [p for p in prices if "0<" in p.site_model_name or "Token≤" in p.site_model_name or "32K<" in p.site_model_name]
        print(f"✓ 抽查分段阶梯定价条目: {len(tiered_prices)} 条")
        for tp in tiered_prices[:5]:
            print(f"    • {tp.model_id} -> {tp.site_model_name} (USD ${tp.calculated_input_usd} / ¥{round(tp.calculated_input_usd * 7.25, 3)})")
            
    # 4. 测试重新探测接口
    probe_res = await relay_fetcher.detect_and_sync_site(import_res.site_id)
    print(f"✓ 重新探测结果: {probe_res}")
    assert probe_res.get("status") == "online"
    
    print("=== 🎉 全部阿里百炼集成测试 100% 通过！===")

if __name__ == "__main__":
    asyncio.run(run_full_suite())
