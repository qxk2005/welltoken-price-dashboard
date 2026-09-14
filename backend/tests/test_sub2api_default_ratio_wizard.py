import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.schemas.token_schema import ChannelWizardCreateRequest, ModelMappingItem
from backend.app.api.v1.channels import wizard_create_channel
from backend.app.models.token_price import RelaySite, ChannelModelMapping, SiteModelPricing
from sqlalchemy import select, delete

async def main():
    async with AsyncSessionLocal() as session:
        # 1. 模拟 Sub2API 场景：探测时未返回独立倍率 (public_ratio=None, key_ratio=None)
        mock_item = ModelMappingItem(
            channel_model_name="kimi-k2.6",
            group_name="default",
            item_key="kimi-k2.6::default",
            is_matched=True,
            standard_model_id="kimi-k2.6",
            standard_model_name="kimi-k2.6",
            official_model_id=10077,
            official_model_name="kimi-k2.6",
            official_input_price=0.8904,
            official_output_price=3.6986,
            official_cache_price=0.1507,
            custom_ratio=None,
            public_ratio=None,
            key_ratio=None,
            applied_ratio_source="default",
            is_selected=True,
            input_price_usd=0.8966, # 探测时的临时原价
            output_price_usd=3.7241,
            cache_price_usd=0.1507
        )

        test_site_name = "pytest_sub2api_temp_test"
        req = ChannelWizardCreateRequest(
            name=test_site_name,
            base_url="http://127.0.0.1:9999",
            site_type="sub2api",
            currency="CNY",
            selected_group="default",
            recharge_rate=1.0,
            default_ratio=0.65, # 用户指定的全局兜底倍率
            notes="Pytest for Sub2API default ratio",
            mappings=[mock_item]
        )

        # 2. 执行 wizard_create_channel
        res = await wizard_create_channel(req, session)
        assert res["status"] == "success"
        test_site_id = res["site_id"]

        try:
            # 3. 验证数据库中入库的 pricing
            p_stmt = select(SiteModelPricing).where(SiteModelPricing.site_id == test_site_id)
            p_res = await session.execute(p_stmt)
            pricings = p_res.scalars().all()
            assert len(pricings) == 1
            p = pricings[0]

            # 断言 model_ratio 严格等于 0.65，而非 1.0
            assert p.model_ratio == 0.65, f"预期 model_ratio 为 0.65，实际为 {p.model_ratio}"
            # 断言 calculated_input_usd 严格等于 0.8904 * 0.65 = 0.5788，而非原价 0.8966
            expected_in = round(0.8904 * 0.65, 4)
            assert p.calculated_input_usd == expected_in, f"预期 calculated_input_usd 为 {expected_in}，实际为 {p.calculated_input_usd}"
            # 断言真实折扣为 0.65 (6.5折)，而非 10.1折 (1.007)
            assert p.official_input_discount == 0.65, f"预期 official_input_discount 为 0.65，实际为 {p.official_input_discount}"
            print("✓ Sub2API 全局默认兜底倍率 0.65 测试通过，折算价格与真实折扣完全准确，无 1.0 原价短路！")
        finally:
            # 4. 清理测试产生的临时数据
            await session.execute(delete(SiteModelPricing).where(SiteModelPricing.site_id == test_site_id))
            await session.execute(delete(ChannelModelMapping).where(ChannelModelMapping.site_id == test_site_id))
            await session.execute(delete(RelaySite).where(RelaySite.id == test_site_id))
            await session.commit()

if __name__ == "__main__":
    asyncio.run(main())
