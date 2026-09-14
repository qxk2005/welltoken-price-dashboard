"""
Moonshot (Kimi) 官方模型定价抓取、新旧格式解析兼容、系列推断与上下文标注自动化测试
"""
import asyncio
import os
import re
from bs4 import BeautifulSoup
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import OfficialModelPrice, OfficialSnapshot
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS, _infer_series


async def main():
    print("=== 1. 测试 OFFICIAL_TARGETS 中 Kimi 的配置 ===")
    assert "kimi" in OFFICIAL_TARGETS, "OFFICIAL_TARGETS 中必须包含 kimi"
    kimi_target = OFFICIAL_TARGETS["kimi"]
    assert kimi_target["code"] == "moonshotai"
    assert kimi_target["currency"] == "CNY"
    expected_url = "https://platform.kimi.com/docs/pricing/chat"
    assert kimi_target["url"] == expected_url, f"Kimi URL 应为 {expected_url}, 实际为 {kimi_target['url']}"
    print(f"✓ OFFICIAL_TARGETS 配置验证通过: URL = {kimi_target['url']}")

    print("\n=== 2. 测试 _infer_series 系列分类推断 ===")
    assert _infer_series("kimi-k3", "moonshotai") == "kimi-k3"
    assert _infer_series("kimi-k2.7-code", "moonshotai") == "kimi-k2.7"
    assert _infer_series("kimi-k2.7-code-highspeed", "moonshotai") == "kimi-k2.7"
    assert _infer_series("kimi-k2.6", "moonshotai") == "kimi-k2.6"
    assert _infer_series("moonshot-v1-8k", "moonshotai") == "moonshot-v1"
    print("✓ _infer_series 系列分类推断通过 (kimi-k3, kimi-k2.7, kimi-k2.6, moonshot-v1)")

    print("\n=== 3. 测试 parse_kimi 对新版行列式表格的解析 ===")
    new_html = """
    <table>
      <thead>
        <tr><th>模型</th><th>计费单位</th><th>输入价格（缓存命中）</th><th>输入价格（缓存未命中）</th><th>输出价格</th><th>上下文窗口</th></tr>
      </thead>
      <tbody>
        <tr><td>kimi-k3</td><td>1M tokens</td><td>¥2.00</td><td>¥20.00</td><td>¥100.00</td><td>1,048,576 tokens</td></tr>
        <tr><td>kimi-k2.7-code</td><td>1M tokens</td><td>¥1.30</td><td>¥6.50</td><td>¥27.00</td><td>262,144 tokens</td></tr>
        <tr><td>kimi-k2.7-code-highspeed</td><td>1M tokens</td><td>¥2.60</td><td>¥13.00</td><td>¥54.00</td><td>262,144 tokens</td></tr>
        <tr><td>kimi-k2.6</td><td>1M tokens</td><td>¥1.10</td><td>¥6.50</td><td>¥27.00</td><td>262,144 tokens</td></tr>
      </tbody>
    </table>
    """
    soup_new = BeautifulSoup(new_html, "html.parser")
    items = official_scraper_service.parse_kimi(soup_new, kimi_target["url"], snapshot_id=999)
    assert len(items) == 4, f"新表格应解析出 4 个模型，实际为 {len(items)}"

    k3 = next(m for m in items if m["raw_model_id"] == "kimi-k3")
    assert k3["series"] == "kimi-k3"
    assert k3["input_price"] == 20.0
    assert k3["output_price"] == 100.0
    assert k3["cache_read_price"] == 2.0
    assert "1,048,576 tokens" in k3["remarks"]
    print("✓ kimi-k3 定价参数及上下文窗口校验通过:", k3["remarks"])

    k27 = next(m for m in items if m["raw_model_id"] == "kimi-k2.7-code")
    assert k27["series"] == "kimi-k2.7"
    assert k27["input_price"] == 6.5
    assert k27["output_price"] == 27.0
    assert k27["cache_read_price"] == 1.3
    assert "262,144 tokens" in k27["remarks"]
    print("✓ kimi-k2.7-code 校验通过")

    k27h = next(m for m in items if m["raw_model_id"] == "kimi-k2.7-code-highspeed")
    assert k27h["series"] == "kimi-k2.7"
    assert k27h["input_price"] == 13.0
    assert k27h["output_price"] == 54.0
    assert k27h["cache_read_price"] == 2.6
    print("✓ kimi-k2.7-code-highspeed 校验通过")

    k26 = next(m for m in items if m["raw_model_id"] == "kimi-k2.6")
    assert k26["series"] == "kimi-k2.6"
    assert k26["input_price"] == 6.5
    assert k26["output_price"] == 27.0
    assert k26["cache_read_price"] == 1.1
    print("✓ kimi-k2.6 校验通过")

    print("\n=== 4. 测试 parse_kimi 对旧版转置表格的向下兼容 ===")
    old_html = """
    <table>
      <tr><th>计费项目</th><th>moonshot-v1-8k</th><th>moonshot-v1-32k</th><th>moonshot-v1-128k</th></tr>
      <tr><td>缓存命中</td><td>¥0.003</td><td>¥0.006</td><td>¥0.015</td></tr>
      <tr><td>输入计费</td><td>¥0.012</td><td>¥0.024</td><td>¥0.060</td></tr>
      <tr><td>输出计费</td><td>¥0.012</td><td>¥0.024</td><td>¥0.060</td></tr>
    </table>
    """
    soup_old = BeautifulSoup(old_html, "html.parser")
    items_old = official_scraper_service.parse_kimi(soup_old, "https://www.kimi.com/membership/pricing", snapshot_id=888)
    assert len(items_old) == 3, f"旧表格兼容解析应为 3 个模型，实际为 {len(items_old)}"
    assert items_old[0]["series"] == "moonshot-v1"
    print("✓ 旧版转置表格兼容解析成功，解析出 3 款 moonshot-v1 系列模型")

    print("\n=== 5. 测试 parse_kimi 正则兜底能力 ===")
    doc_table_html = """
    <div>
      DocTable,{columns:[...],rows:[[`kimi-k3`,`1M tokens`,`¥2.00`,`¥20.00`,`¥100.00`,`1,048,576 tokens`],[`kimi-k2.6`,`1M tokens`,`¥1.10`,`¥6.50`,`¥27.00`,`262,144 tokens`]]}
    </div>
    """
    soup_regex = BeautifulSoup(doc_table_html, "html.parser")
    items_regex = official_scraper_service.parse_kimi(soup_regex, kimi_target["url"], snapshot_id=777)
    assert len(items_regex) == 2, f"正则兜底应提取 2 款模型，实际为 {len(items_regex)}"
    assert items_regex[0]["model_name"] == "kimi-k3"
    print("✓ 正则兜底解析机制验证通过")

    print("\n🎉 全部 Kimi 官方模型定价测试用例均验证通过！")


if __name__ == "__main__":
    asyncio.run(main())
