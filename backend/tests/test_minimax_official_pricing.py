from bs4 import BeautifulSoup
from backend.app.services.official_scraper_service import official_scraper_service

def test_minimax_parse_standard_vs_priority():
    with open("data/official_snapshots/minimax_20260914_035441.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    items = official_scraper_service.parse_minimax(soup, "https://platform.minimaxi.com/docs/guides/pricing-paygo", 164)
    assert len(items) > 0, "必须解析出 MiniMax 模型条目"

    m3_items = [it for it in items if "MiniMax-M3" in it["model_name"]]
    assert len(m3_items) == 4, f"MiniMax-M3 必须包含 4 款规格 (Standard 2 款 + Priority 2 款)，实际为 {len(m3_items)}"

    # 1. 验证 Standard 标准模式
    m3_std_low = next(it for it in m3_items if it["tier_range"] == "[0, 512k)" and it["billing_mode"] == "Standard")
    assert m3_std_low["input_price"] == 2.10, f"Standard 512k以下输入应为 2.10，实际为 {m3_std_low['input_price']}"
    assert m3_std_low["output_price"] == 8.40
    assert m3_std_low["cache_read_price"] == 0.42

    m3_std_high = next(it for it in m3_items if it["tier_range"] == "[512k+)" and it["billing_mode"] == "Standard")
    assert m3_std_high["input_price"] == 4.20, f"Standard 512k以上输入应为 4.20，实际为 {m3_std_high['input_price']}"
    assert m3_std_high["output_price"] == 16.80
    assert m3_std_high["cache_read_price"] == 0.84

    # 2. 验证 Priority 优先模式 (1.5倍计费)
    m3_prio_low = next(it for it in m3_items if it["tier_range"] == "[0, 512k)" and "Priority" in it["billing_mode"])
    assert m3_prio_low["input_price"] == 3.15
    assert m3_prio_low["output_price"] == 12.60

    m3_prio_high = next(it for it in m3_items if it["tier_range"] == "[512k+)" and "Priority" in it["billing_mode"])
    assert m3_prio_high["input_price"] == 6.30
    assert m3_prio_high["output_price"] == 25.20
    assert "优先" in m3_prio_high["remarks"]

    print("✓ MiniMax 解析器 Standard (2.1/4.2) 与 Priority (3.15/6.3) 双模式精准分离测试通过！")

if __name__ == "__main__":
    test_minimax_parse_standard_vs_priority()
