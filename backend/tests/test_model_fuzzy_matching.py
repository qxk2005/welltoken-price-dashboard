"""
官方大模型基准智能模糊匹配算法与深度纯化测试
包含 Kimi、StepFun、MiniMax、Aliyun 等主流官方模型的智能模糊匹配验证
"""
import asyncio
from backend.app.database import AsyncSessionLocal
from backend.app.services.official_benchmark_service import official_benchmark_service


async def main():
    print("=== 1. 测试 _normalize_name 纯化与代号折叠逻辑 ===")
    assert official_benchmark_service._normalize_name("kimi-k2.6") == "k26"
    assert official_benchmark_service._normalize_name("kimi-2.6") == "k26"
    assert official_benchmark_service._normalize_name("K2.6通用模型") == "k26"
    assert official_benchmark_service._normalize_name("kimi-k3") == "k3"
    assert official_benchmark_service._normalize_name("kimi-3") == "k3"
    assert official_benchmark_service._normalize_name("K3旗舰模型") == "k3"
    assert official_benchmark_service._normalize_name("K2.7 CodeCoding 模型") == "k27"
    assert official_benchmark_service._normalize_name("minimax-m3-fast") == "m3"
    assert official_benchmark_service._normalize_name("stepfun/step-3.7-flash") == "step37flash"
    print("✓ _normalize_name 全部测试用例验证通过！")

    print("\n=== 2. 测试真实数据库中的官方基准模糊匹配 ===")
    async with AsyncSessionLocal() as session:
        benchmarks = await official_benchmark_service.get_benchmark_models(session)
        print(f"当前数据库官方去阶梯第一档基准模型数: {len(benchmarks)}")

        test_cases = [
            ("kimi-k2.6", "K2.6通用模型"),
            ("kimi-2.6", "K2.6通用模型"),
            ("kimi-k3", "K3旗舰模型"),
            ("kimi-3", "K3旗舰模型"),
            ("kimi-k2.7", "K2.7 CodeCoding 模型"),
            ("minimax-m3-fast", "MiniMax-M3"),
            ("step-3.7-flash", "step-3.7-flash"),
            ("GLM-5", "GLM-5"),
            ("glm-5", "GLM-5"),
            ("zhipu/glm-5", "GLM-5"),
            ("glm-5-turbo", "GLM-5-Turbo"),
        ]

        for cand, expected_substr in test_cases:
            match, score = official_benchmark_service.fuzzy_match_one(cand, benchmarks, threshold=0.70)
            assert match is not None, f"候选模型 {cand} 未能匹配到任何官方模型！"
            clean_name = match.get("clean_name", "")
            assert expected_substr.lower() in clean_name.lower() or expected_substr.lower() in match.get("raw_model_id", "").lower(), \
                f"候选模型 {cand} 期望匹配包含 {expected_substr}，实际匹配为 {clean_name}"
            assert score >= 0.85, f"候选模型 {cand} 匹配置信度不足 ({score})，期望 >= 0.85"
            print(f"✓ 成功匹配: {cand:16} ➔ [{match.get('provider_name')}] {clean_name} (得分: {score})")

    print("\n🎉 全部官方大模型基准智能模糊匹配测试 100% 成功通过！")


if __name__ == "__main__":
    asyncio.run(main())
