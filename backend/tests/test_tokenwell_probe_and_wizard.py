import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.services.model_normalizer import model_normalizer
from backend.app.schemas.token_schema import ChannelWizardCreateRequest, ModelMappingItem
from backend.app.api.v1.channels import wizard_create_channel
from backend.app.models.token_price import RelaySite, ChannelModelMapping, SiteModelPricing, ModelMetadata
from sqlalchemy import select

async def main():
    print("=== 1. 测试 tokenwell 重新探测逻辑 ===")
    probe_res = await model_normalizer.probe_and_fetch_models(base_url="https://tokenwell.net:50501")
    assert probe_res["is_online"] is True, "Tokenwell 应当处于 Online 状态"
    print(f"✓ 探测在线状态: {probe_res['is_online']}, 状态码: {probe_res['status_code']}")
    print(f"✓ 发现原始模型数: {probe_res['raw_count']}")
    
    # 验证分组
    group_names = [g["name"] for g in probe_res["available_groups"]]
    print(f"✓ 可用分组列表: {probe_res['available_groups']}")
    assert "default" not in group_names, "错误的分组 'default' 不应出现在真实分组列表中！"
    assert "默认用户" in group_names, "'默认用户' 必须在可用分组中！"
    assert probe_res["selected_group"] == "默认用户", f"默认选中分组应为 '默认用户'，实际为 {probe_res['selected_group']}"

    print("\n=== 2. 测试智能映射对接官方定价标准模型 ===")
    mappings = await model_normalizer.match_models_for_channel(
        raw_model_names=probe_res["raw_models"],
        raw_public_ratios=probe_res.get("raw_public_ratios"),
        raw_key_ratios=probe_res.get("raw_key_ratios"),
        raw_model_items=probe_res.get("raw_model_items"),
        selected_group=probe_res.get("selected_group", "默认用户"),
        selected_group_ratio=probe_res.get("selected_group_ratio", 1.0),
        global_group_ratios=probe_res.get("global_group_ratios")
    )
    print(f"✓ 生成映射总数: {len(mappings)}")
    assert len(mappings) > 0, "必须生成有效的映射项"

    matched_items = [m for m in mappings if m["is_matched"]]
    unmatched_items = [m for m in mappings if not m["is_matched"]]
    print(f"✓ 已命中官方定价标准模型: {len(matched_items)} 款")
    print(f"✓ 待确认/自定义模型: {len(unmatched_items)} 款")

    # 验证命中官方模型的数据完整性
    for m in matched_items[:3]:
        assert m["official_model_id"] is not None, "官方模型 ID 必须存在"
        assert m["official_model_name"], "官方模型名称必须存在"
        assert m["is_selected"] is True, "匹配到官方模型的条目默认应勾选收录"
        print(f"  - 命中示例: {m['channel_model_name']} ➔ 官方[{m['official_model_name']}] 原价: ¥{m['official_input_cny']}")

    # 验证未命中官方模型脱钩
    for u in unmatched_items[:3]:
        assert u["official_model_id"] is None, "未命中模型官方 ID 应为 None"
        assert u["is_selected"] is False, "未命中官方模型的条目默认不勾选收录"
        print(f"  - 未命中示例: {u['channel_model_name']} ➔ 待确认自定义条目 (Selected: False)")

    print("\n=== 3. 测试向导确认入库 (/wizard-create) 写入官方模型关系与折扣 ===")
    mapping_items = [ModelMappingItem(**m) for m in mappings]
    
    # 模拟为已有的 tokenwell 渠道执行入库
    async with AsyncSessionLocal() as session:
        site_res = await session.execute(select(RelaySite).where(RelaySite.name.ilike('%tokenwell%')))
        site = site_res.scalars().first()
        site_id = site.id if site else None

        req = ChannelWizardCreateRequest(
            site_id=site_id,
            name="tokenwell",
            base_url="https://tokenwell.net:50501",
            site_type="newapi",
            currency="CNY",
            selected_group="默认用户",
            recharge_rate=1.0,
            default_ratio=1.0,
            notes="自动化测试向导入库",
            mappings=mapping_items
        )

        create_res = await wizard_create_channel(req, session)
        print(f"✓ 入库结果: {create_res}")
        assert create_res["status"] == "success", "入库状态应为 success"
        target_site_id = create_res["site_id"]

        # 检查数据库中的 ChannelModelMapping 与 SiteModelPricing
        maps_res = await session.execute(select(ChannelModelMapping).where(ChannelModelMapping.site_id == target_site_id))
        saved_maps = maps_res.scalars().all()
        print(f"✓ 写入 ChannelModelMapping 数量: {len(saved_maps)}")
        assert any(sm.official_model_id is not None for sm in saved_maps), "必须至少有一条记录包含 official_model_id"

        prices_res = await session.execute(select(SiteModelPricing).where(SiteModelPricing.site_id == target_site_id))
        saved_prices = prices_res.scalars().all()
        print(f"✓ 写入 SiteModelPricing 数量: {len(saved_prices)}")
        assert any(sp.official_input_discount is not None for sp in saved_prices), "必须至少有一条价格记录计算了官方真实折扣"

        sample_p = next((sp for sp in saved_prices if sp.official_input_discount is not None), None)
        if sample_p:
            print(f"  - 真实折扣样例: {sample_p.site_model_name} ➔ 官方模型: {sample_p.official_model_name}, 真实输入折扣: {sample_p.official_input_discount}x, 综合折扣: {sample_p.official_composite_discount}x")

    print("\n🎉 全部自动化断言与验证完美通过！")

if __name__ == "__main__":
    asyncio.run(main())
