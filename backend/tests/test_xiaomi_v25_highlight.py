import asyncio
import os
import sys
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import OfficialSnapshot
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(OfficialSnapshot).where(OfficialSnapshot.provider == 'xiaomi'))
        snapshot = res.scalars().first()
        assert snapshot is not None, "未找到小米快照记录"

        abs_path = os.path.join(os.getcwd(), snapshot.local_file_path)
        with open(abs_path, 'r', encoding='utf-8') as f:
            raw_html = f.read()

    from backend.app.api.v1.official_pricing import view_snapshot_html
    from fastapi.responses import HTMLResponse

    async def get_injected_html(kw: str):
        async with AsyncSessionLocal() as db:
            resp = await view_snapshot_html(snapshot.id, highlight=kw, db=db)
            return resp.body.decode('utf-8')

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # ================= 测试 1: MiMo-V2.5 高亮定位 (验证不命中系列标题，精准命中第二行数据) =================
        print("\n=== 测试 1: MiMo-V2.5 点击对账定位 ===")
        html_v25 = await get_injected_html("MiMo-V2.5|mimo-v2.5")
        await page.set_content(html_v25)
        await page.wait_for_timeout(500)

        # 检查高亮行
        highlighted_rows = await page.locator('.wpd-highlight-row').all()
        print(f"Highlighted rows count: {len(highlighted_rows)}")
        assert len(highlighted_rows) >= 1, "必须至少有 1 个高亮行/块"
        
        row_text = await highlighted_rows[0].inner_text()
        print(f"Highlighted row content:\n{row_text}")
        assert "系列" not in row_text, f"错误：高亮行依然命中了系列标题！内容: {row_text}"
        assert "mimo-v2.5" in row_text, "高亮行必须包含 mimo-v2.5"
        assert "¥0.02" in row_text and "¥1.00" in row_text and "¥2.00" in row_text, "高亮行必须包含 v2.5 的三档单价"

        # 检查高亮单元格
        highlighted_cells = await page.locator('.wpd-highlight-cell').all()
        print(f"Highlighted cells count: {len(highlighted_cells)}")
        assert len(highlighted_cells) == 3, f"应该高亮 3 个价格单元格，实际高亮了 {len(highlighted_cells)}"
        cell_texts = [await c.inner_text() for c in highlighted_cells]
        print(f"Cell texts: {cell_texts}")
        assert "¥0.02" in cell_texts and "¥1.00" in cell_texts and "¥2.00" in cell_texts

        # 检查顶部居中提示条
        indicator = page.locator('.wpd-top-indicator')
        assert await indicator.is_visible(), "顶部提示胶囊应该可见"
        print(f"Top indicator: {await indicator.inner_text()}")

        # ================= 测试 2: MiMo-V2.5 Pro 高亮定位 =================
        print("\n=== 测试 2: MiMo-V2.5 Pro 点击对账定位 ===")
        html_pro = await get_injected_html("MiMo-V2.5 Pro|mimo-v2.5-pro")
        await page.set_content(html_pro)
        await page.wait_for_timeout(500)

        pro_rows = await page.locator('.wpd-highlight-row').all()
        pro_text = await pro_rows[0].inner_text()
        print(f"Highlighted Pro row content:\n{pro_text}")
        assert "mimo-v2.5-pro" in pro_text
        assert "¥0.025" in pro_text and "¥3.00" in pro_text and "¥6.00" in pro_text

        # ================= 测试 3: MiMo-V2.5 TTS 段落回退高亮定位 =================
        print("\n=== 测试 3: MiMo-V2.5 TTS 段落回退定位 ===")
        html_tts = await get_injected_html("MiMo-V2.5 TTS|mimo-v2.5-tts")
        await page.set_content(html_tts)
        await page.wait_for_timeout(500)

        tts_el = await page.locator('.wpd-highlight-row').all()
        assert len(tts_el) >= 1, "TTS 必须成功命中段落回退高亮"
        tts_text = await tts_el[0].inner_text()
        print(f"Highlighted TTS text:\n{tts_text}")
        assert "限时免费" in tts_text and "mimo-v2.5-tts" in tts_text

        await browser.close()
        print("\n🎉 所有测试场景 (v2.5 真实价格行、Pro 行、TTS 段落回退) 100% 成功通过！")

if __name__ == '__main__':
    asyncio.run(main())
