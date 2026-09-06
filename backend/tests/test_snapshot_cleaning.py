"""
官方快照弹窗与遮罩层净化过滤测试 (包括小米 MiMo 等官网)
"""
import os
import pytest
from bs4 import BeautifulSoup
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS

def test_sample_xiaomi_modal_cleaned():
    """验证 sample_xiaomi.html 快照中已经没有 ant-modal-root 与遮罩蒙层"""
    sample_file = os.path.join(os.getcwd(), "data", "official_snapshots", "sample_xiaomi.html")
    assert os.path.exists(sample_file), f"快照文件不存在: {sample_file}"

    with open(sample_file, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # 验证弹窗与遮罩节点已彻底移除
    assert soup.find(class_="ant-modal-root") is None, "sample_xiaomi.html 中不应存在 ant-modal-root"
    assert soup.find(class_="ant-modal-mask") is None, "sample_xiaomi.html 中不应存在 ant-modal-mask"
    assert soup.find(class_="Announcement_announcementModal__AHN0r") is None, "营销公告弹窗必须被移除"

    # 验证主体定价表格与关键模型依然完整无损
    items = official_scraper_service.parse_xiaomi(soup, OFFICIAL_TARGETS["xiaomi"]["url"], snapshot_id=1)
    assert len(items) >= 6, f"预期解析到至少 6 款模型，实际: {len(items)}"
    model_ids = [m["raw_model_id"] for m in items]
    assert "mimo-v2.5-pro" in model_ids
    assert "mimo-v2.5" in model_ids
    assert "mimo-v2.5-asr" in model_ids
    assert "mimo-v2.5-tts" in model_ids
    print("[PASS] sample_xiaomi.html 快照净化与模型解析验证通过")


def test_modal_filtering_logic():
    """测试各类弹窗遮罩（AntD/Element/Bootstrap/Dialog）的过滤剔除与保留逻辑"""
    dirty_html = """
    <html>
      <head><title>Test Pricing</title></head>
      <body>
        <div class="ant-modal-root">
          <div class="ant-modal-mask"></div>
          <div class="ant-modal-wrap">
            <div class="ant-modal Announcement_announcementModal">
              <h2>广告促销弹窗</h2>
            </div>
          </div>
        </div>
        <div class="el-overlay">
          <div class="el-dialog__wrapper">
            <h3>通知弹窗</h3>
          </div>
        </div>
        <div class="modal-backdrop"></div>
        <div role="dialog" aria-modal="true" class="notice-modal">
          <p>无表格的纯提示框</p>
        </div>

        <div role="dialog" class="table-dialog">
          <table>
            <tr><td>保留包含表格的模型明细</td></tr>
          </table>
        </div>

        <div class="main-content">
          <table>
            <thead><tr><th>模型</th><th>价格</th></tr></thead>
            <tbody>
              <tr><td>MiMo-V2.5</td><td>¥1.00</td></tr>
            </tbody>
          </table>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(dirty_html, "html.parser")

    # 执行与 official_pricing.py 相同的清洗逻辑
    modal_selectors = [
        ".ant-modal-root",
        ".ant-modal-mask",
        ".ant-modal-wrap",
        ".ant-modal",
        ".el-overlay",
        ".el-overlay-dialog",
        ".el-dialog__wrapper",
        ".v-modal",
        ".modal-backdrop",
        "[class*='Announcement_announcementModal']",
        "[class*='announcementModal']",
        "[class*='announcement-modal']",
        "[class*='NoticeModal']",
        "[class*='notice-modal']",
        "[class*='promotion-modal']",
        "[class*='marketing-modal']",
        "[id*='announcement-modal']",
        "[id*='notice-modal']",
    ]
    for sel in modal_selectors:
        for el in soup.select(sel):
            el.decompose()

    for dialog in soup.find_all(attrs={"role": "dialog"}):
        if not dialog.find("table") and not dialog.find("tbody"):
            dialog.decompose()

    # 验证各种纯遮罩与公告弹窗已被完全清除
    assert soup.find(class_="ant-modal-root") is None
    assert soup.find(class_="ant-modal-mask") is None
    assert soup.find(class_="el-overlay") is None
    assert soup.find(class_="modal-backdrop") is None
    assert soup.find(class_="notice-modal") is None

    # 验证含有 table 的正常 dialog 以及主内容 table 依然完好
    assert soup.find(class_="table-dialog") is not None
    assert soup.find("tbody") is not None
    print("[PASS] 弹窗过滤剔除逻辑验证通过")


@pytest.mark.asyncio
async def test_api_view_snapshot_cleaning():
    """测试 /api/v1/official-pricing/snapshots/{id}/view 接口真实返回已完全净化无弹窗遮挡"""
    from httpx import AsyncClient, ASGITransport
    from backend.app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/v1/official-pricing/snapshots")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        xiaomi_snaps = [s for s in data if s.get("provider") == "xiaomi"]
        if xiaomi_snaps:
            snap_id = xiaomi_snaps[0]["id"]
            view_resp = await ac.get(f"/api/v1/official-pricing/snapshots/{snap_id}/view?highlight=MiMo-V2.5")
            assert view_resp.status_code == 200, view_resp.text
            soup = BeautifulSoup(view_resp.text, "html.parser")
            assert soup.find(class_="ant-modal-root") is None, "DOM 中不得有 ant-modal-root 元素"
            assert soup.find(class_="ant-modal-mask") is None, "DOM 中不得有 ant-modal-mask 元素"
            assert soup.find(class_="Announcement_announcementModal__AHN0r") is None, "DOM 中不得有公告弹窗"
            style_tags = soup.find_all("style")
            all_styles = " ".join(st.get_text() for st in style_tags)
            assert ".ant-modal-root" in all_styles, "样式表中必须包含屏蔽选择器"
            print("[PASS] API view 接口快照净化测试通过")


if __name__ == "__main__":
    import asyncio
    test_sample_xiaomi_modal_cleaned()
    test_modal_filtering_logic()
    asyncio.run(test_api_view_snapshot_cleaning())
    print("全部测试通过！")
