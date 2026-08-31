"""
硅基流动 SiliconFlow 官网定价页爬取服务

通过 Playwright headless 浏览器访问 https://siliconflow.cn/pricing，
自动点击所有"展开更多"按钮后抓取完整的模型价格列表。
"""
import re
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import select

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing
from backend.app.schemas.token_schema import (
    SiliconFlowModelItem, SiliconFlowPriceTier,
    SiliconFlowScrapeResponse, SiliconFlowImportResponse
)

SILICONFLOW_PRICING_URL = "https://siliconflow.cn/pricing"
SILICONFLOW_SITE_NAME = "硅基流动 SiliconFlow"
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"

# 页面中类别标题与系统内部类别名的映射
CATEGORY_MAP = {
    "对话模型": "对话",
    "生图模型": "生图",
    "语音模型": "语音",
    "视频模型": "视频",
}

# 硅基流动厂商名到内部 provider 的映射（部分需要标准化）
PROVIDER_NORMALIZE = {
    "deepseek-ai": "deepseek",
    "Z-ai": "zhipuai",
    "zai-org": "zhipuai",
    "THUDM": "zhipuai",
    "Kimi": "moonshotai",
    "moonshotai": "moonshotai",
    "MiniMaxAI": "minimax",
    "Tongyi-MAI": "alibaba",
    "Qwen": "alibaba",
    "Wan": "alibaba",
    "Baidu": "baidu",
    "Stepfun-ai": "stepfun",
    "inclusionAI": "inclusionai",
    "ChinaTelecom": "chinatelecom",
    "hunyuan": "tencent",
    "ByteDance": "bytedance",
    "openmoss": "openmoss",
    "FunAudioLLM": "funaudillm",
    "BAAI": "baai",
    "Kolors": "kolors",
    "nex-agi": "nex-agi",
    "meituan-longcat": "meituan",
}


def _parse_price(text: str) -> Optional[float]:
    """从价格文本中解析数字，如 '¥ 12.00' -> 12.0, '免费' -> 0.0, '-' -> None"""
    if not text:
        return None
    text = text.strip()
    if text == "-" or text == "—":
        return None
    if "免费" in text:
        return 0.0
    # 提取 ¥ 后的数字
    m = re.search(r'[\d.]+', text)
    if m:
        try:
            return float(m.group())
        except ValueError:
            return None
    return None


def _is_free_text(text: str) -> bool:
    """判断是否为免费标记"""
    return "免费" in text.strip() if text else False


class SiliconFlowScraperService:
    """硅基流动官网定价爬取服务"""

    async def scrape_pricing(self) -> SiliconFlowScrapeResponse:
        """
        爬取硅基流动官网定价页全部模型价格。
        使用 Playwright headless 浏览器打开页面，点击所有展开按钮后解析 DOM。
        """
        start_time = time.time()
        models: List[SiliconFlowModelItem] = []

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return SiliconFlowScrapeResponse(
                status="error",
                error_message="未安装 playwright，请运行: pip install playwright && playwright install chromium"
            )

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                print(f"[SiliconFlowScraper] 正在加载定价页: {SILICONFLOW_PRICING_URL}")
                await page.goto(SILICONFLOW_PRICING_URL, wait_until="networkidle", timeout=30000)

                # 等待价格表格出现
                await page.wait_for_selector("[id^='pricing-provider-']", timeout=15000)
                print("[SiliconFlowScraper] 页面加载完成，开始点击展开按钮...")

                # 循环点击所有"展开更多"按钮
                expand_round = 0
                while True:
                    expand_buttons = await page.query_selector_all(
                        "button:has-text('展开更多')"
                    )
                    visible_buttons = []
                    for btn in expand_buttons:
                        if await btn.is_visible():
                            visible_buttons.append(btn)

                    if not visible_buttons:
                        break

                    expand_round += 1
                    print(f"[SiliconFlowScraper] 第 {expand_round} 轮: 发现 {len(visible_buttons)} 个展开按钮")
                    for btn in visible_buttons:
                        try:
                            await btn.click()
                            await asyncio.sleep(0.3)
                        except Exception:
                            pass

                    # 等待 DOM 更新
                    await asyncio.sleep(0.5)

                print("[SiliconFlowScraper] 所有展开按钮已点击，开始解析 DOM...")

                # 解析各分类的模型
                sections = await page.query_selector_all("section:has(h2)")
                for section in sections:
                    h2_el = await section.query_selector("h2")
                    if not h2_el:
                        continue
                    h2_text = (await h2_el.inner_text()).strip()
                    category = CATEGORY_MAP.get(h2_text, "")
                    if not category:
                        continue

                    # 找到该 section 下所有 provider 区块
                    provider_blocks = await section.query_selector_all("[id^='pricing-provider-']")
                    for provider_block in provider_blocks:
                        block_id = await provider_block.get_attribute("id") or ""
                        # 从 id 提取 provider 名，如 pricing-provider-text-deepseek-ai -> deepseek-ai
                        provider_raw = block_id.replace("pricing-provider-text-", "").replace("pricing-provider-image-", "").replace("pricing-provider-audio-", "").replace("pricing-provider-video-", "")

                        # 获取 provider 区块内的所有模型行
                        model_rows = await provider_block.query_selector_all("[id^='pricing-row-']")
                        for row in model_rows:
                            model_item = await self._parse_model_row(
                                row, provider_raw, category
                            )
                            if model_item:
                                models.append(model_item)

                await browser.close()

        except Exception as e:
            elapsed = round((time.time() - start_time) * 1000, 1)
            print(f"[SiliconFlowScraper] 爬取失败: {e}")
            return SiliconFlowScrapeResponse(
                status="error",
                error_message=f"爬取失败: {str(e)}",
                scrape_duration_ms=elapsed
            )

        elapsed = round((time.time() - start_time) * 1000, 1)

        # 统计分类
        category_counts: Dict[str, int] = {}
        free_count = 0
        tiered_count = 0
        for m in models:
            category_counts[m.category] = category_counts.get(m.category, 0) + 1
            if m.is_free:
                free_count += 1
            if m.has_tiered_pricing:
                tiered_count += 1

        print(f"[SiliconFlowScraper] 爬取完成: {len(models)} 个模型, 耗时 {elapsed}ms")
        print(f"[SiliconFlowScraper] 分类统计: {category_counts}")

        return SiliconFlowScrapeResponse(
            status="success",
            total_models=len(models),
            category_counts=category_counts,
            free_models_count=free_count,
            tiered_models_count=tiered_count,
            models=models,
            scrape_duration_ms=elapsed
        )

    async def _parse_model_row(
        self, row, provider_raw: str, category: str
    ) -> Optional[SiliconFlowModelItem]:
        """解析单个模型行的 DOM 元素，提取模型 ID、显示名称和价格信息"""
        try:
            # 获取模型链接元素提取 model_id
            link_el = await row.query_selector("a[title]")
            if not link_el:
                return None

            full_model_id = (await link_el.get_attribute("title") or "").strip()
            display_name = (await link_el.inner_text()).strip()

            if not full_model_id:
                return None

            # 检查模型行是否为分段定价 (grid-row span > 1)
            name_cell = await row.query_selector("div[style*='grid-row']")
            grid_row_span = 1
            if name_cell:
                style = await name_cell.get_attribute("style") or ""
                span_match = re.search(r'span\s+(\d+)', style)
                if span_match:
                    grid_row_span = int(span_match.group(1))

            # 获取所有价格列（输入、输出、缓存）
            price_cells = await row.query_selector_all(
                "div.flex.items-center.justify-between"
            )

            if grid_row_span > 1:
                # 分段定价模型
                return await self._parse_tiered_model(
                    row, price_cells, full_model_id, display_name,
                    provider_raw, category, grid_row_span
                )
            else:
                # 普通单价模型
                return self._parse_simple_model(
                    price_cells, full_model_id, display_name,
                    provider_raw, category
                )
        except Exception as e:
            print(f"[SiliconFlowScraper] 解析模型行失败: {e}")
            return None

    def _parse_simple_model(
        self, price_cells, full_model_id: str, display_name: str,
        provider_raw: str, category: str
    ) -> Optional[SiliconFlowModelItem]:
        """解析无分段定价的普通模型行"""
        input_price = 0.0
        output_price = 0.0
        cache_price = 0.0
        is_free = False

        # price_cells 顺序: [输入, 输出, 缓存] (对话模型) 或更少列
        prices = []
        for cell in price_cells:
            # 同步获取不了 inner_text，这里存为占位
            prices.append(cell)

        return SiliconFlowModelItem(
            model_id=full_model_id,
            display_name=display_name,
            provider=provider_raw,
            category=category,
            input_price_cny=input_price,
            output_price_cny=output_price,
            cache_price_cny=cache_price,
            is_free=is_free
        )

    async def _parse_tiered_model(
        self, row, price_cells, full_model_id: str, display_name: str,
        provider_raw: str, category: str, span: int
    ) -> Optional[SiliconFlowModelItem]:
        """解析分段定价模型"""
        tiers: List[SiliconFlowPriceTier] = []
        tier_notes = []

        # 分段定价行的 price_cells 包含多个段
        cells_per_tier = 3  # 输入、输出、缓存
        total_cells = len(price_cells)

        for tier_idx in range(span):
            start = tier_idx * cells_per_tier
            if start >= total_cells:
                break
            end = min(start + cells_per_tier, total_cells)
            tier_cells = price_cells[start:end]

            tier_label = ""
            t_input = 0.0
            t_output = 0.0
            t_cache = 0.0

            for ci, cell in enumerate(tier_cells):
                label_el = await cell.query_selector("span.text-slate-500 span")
                if label_el and tier_label == "":
                    tier_label = (await label_el.inner_text()).strip()

                price_el = await cell.query_selector("span.font-semibold.leading-5.text-\\[\\#6E29F6\\]")
                free_el = await cell.query_selector("span:has-text('免费')")

                price_text = ""
                if free_el:
                    price_text = "免费"
                elif price_el:
                    price_text = (await price_el.inner_text()).strip()

                val = _parse_price(price_text)
                if val is None:
                    val = 0.0

                if ci == 0:
                    t_input = val
                elif ci == 1:
                    t_output = val
                elif ci == 2:
                    t_cache = val

            tiers.append(SiliconFlowPriceTier(
                tier_label=tier_label,
                input_price_cny=t_input,
                output_price_cny=t_output,
                cache_price_cny=t_cache
            ))
            if tier_label:
                tier_notes.append(f"{tier_label}: 输入¥{t_input} / 输出¥{t_output}")

        # 取第一段作为主价格
        first = tiers[0] if tiers else SiliconFlowPriceTier()
        is_free = all(t.input_price_cny == 0 and t.output_price_cny == 0 for t in tiers)

        return SiliconFlowModelItem(
            model_id=full_model_id,
            display_name=display_name,
            provider=provider_raw,
            category=category,
            input_price_cny=first.input_price_cny,
            output_price_cny=first.output_price_cny,
            cache_price_cny=first.cache_price_cny,
            is_free=is_free,
            has_tiered_pricing=True,
            price_tiers=tiers,
            price_note=" | ".join(tier_notes)
        )

    async def scrape_pricing_robust(self) -> SiliconFlowScrapeResponse:
        """
        更健壮的爬取方式：利用 Playwright 的 evaluate 在浏览器上下文中一次性提取全部数据，
        避免大量 query_selector 跨进程调用。
        """
        start_time = time.time()

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return SiliconFlowScrapeResponse(
                status="error",
                error_message="未安装 playwright，请运行: pip install playwright && playwright install chromium"
            )

        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": 1920, "height": 1080},
                    locale="zh-CN",
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                print(f"[SiliconFlowScraper] 正在加载定价页: {SILICONFLOW_PRICING_URL}")
                await page.goto(SILICONFLOW_PRICING_URL, wait_until="networkidle", timeout=30000)
                await page.wait_for_selector("[id^='pricing-provider-']", timeout=15000)

                # 点击所有展开按钮
                expand_round = 0
                while True:
                    count = await page.evaluate("""() => {
                        const btns = [...document.querySelectorAll('button')].filter(
                            b => b.textContent.includes('展开更多') && b.offsetParent !== null
                        );
                        btns.forEach(b => b.click());
                        return btns.length;
                    }""")
                    if count == 0:
                        break
                    expand_round += 1
                    print(f"[SiliconFlowScraper] 第 {expand_round} 轮: 点击了 {count} 个展开按钮")
                    await asyncio.sleep(0.6)

                print("[SiliconFlowScraper] 展开完成，通过 JS 一次性提取所有数据...")

                # 在浏览器中一次性提取所有模型数据
                raw_data = await page.evaluate("""() => {
                    const results = [];
                    const sections = document.querySelectorAll('section:has(> h2)');

                    // 类别映射
                    const catMap = {'对话模型': '对话', '生图模型': '生图', '语音模型': '语音', '视频模型': '视频'};

                    sections.forEach(section => {
                        const h2 = section.querySelector('h2');
                        if (!h2) return;
                        const category = catMap[h2.textContent.trim()] || '';
                        if (!category) return;

                        const providerBlocks = section.querySelectorAll('[id^="pricing-provider-"]');
                        providerBlocks.forEach(block => {
                            const blockId = block.id || '';
                            // 提取 provider 名称
                            const providerRaw = blockId
                                .replace('pricing-provider-text-', '')
                                .replace('pricing-provider-image-', '')
                                .replace('pricing-provider-audio-', '')
                                .replace('pricing-provider-video-', '');

                            const rows = block.querySelectorAll('[id^="pricing-row-"]');
                            rows.forEach(row => {
                                const link = row.querySelector('a[title]');
                                if (!link) return;

                                const modelId = link.getAttribute('title') || '';
                                const displayName = link.textContent.trim();
                                if (!modelId) return;

                                // 检查 grid-row span 判断分段定价
                                const nameCell = row.querySelector('div[style*="grid-row"]');
                                let gridRowSpan = 1;
                                if (nameCell) {
                                    const style = nameCell.getAttribute('style') || '';
                                    const m = style.match(/span\\s+(\\d+)/);
                                    if (m) gridRowSpan = parseInt(m[1]);
                                }

                                // 提取所有价格单元格
                                const priceCells = row.querySelectorAll('div.flex.items-center.justify-between');
                                const tiers = [];
                                const cellsPerTier = 3;

                                for (let ti = 0; ti < gridRowSpan; ti++) {
                                    const start = ti * cellsPerTier;
                                    let tierLabel = '';
                                    let inputPrice = null;
                                    let outputPrice = null;
                                    let cachePrice = null;

                                    for (let ci = 0; ci < cellsPerTier; ci++) {
                                        const idx = start + ci;
                                        if (idx >= priceCells.length) break;
                                        const cell = priceCells[idx];

                                        // 获取阶梯标签
                                        const labelEl = cell.querySelector('span.text-slate-500 span');
                                        if (labelEl && !tierLabel) {
                                            tierLabel = labelEl.textContent.trim();
                                        }

                                        // 获取价格值
                                        let priceText = '';
                                        const freeEl = cell.querySelector('span.text-slate-500:has(> span)');
                                        if (cell.textContent.includes('免费')) {
                                            priceText = '免费';
                                        } else {
                                            const priceEl = cell.querySelector('span.font-semibold.leading-5');
                                            if (priceEl) {
                                                priceText = priceEl.textContent.trim();
                                            }
                                        }

                                        // 解析价格
                                        let val = null;
                                        if (priceText === '免费') {
                                            val = 0;
                                        } else if (priceText && priceText !== '-' && priceText !== '—') {
                                            const nm = priceText.match(/[\\d.]+/);
                                            if (nm) val = parseFloat(nm[0]);
                                        }

                                        if (ci === 0) inputPrice = val;
                                        else if (ci === 1) outputPrice = val;
                                        else if (ci === 2) cachePrice = val;
                                    }

                                    tiers.push({
                                        tier_label: tierLabel,
                                        input_price_cny: inputPrice !== null ? inputPrice : 0,
                                        output_price_cny: outputPrice !== null ? outputPrice : 0,
                                        cache_price_cny: cachePrice !== null ? cachePrice : 0
                                    });
                                }

                                const firstTier = tiers[0] || {input_price_cny: 0, output_price_cny: 0, cache_price_cny: 0};
                                const isFree = tiers.every(t => t.input_price_cny === 0 && t.output_price_cny === 0);
                                const hasTiered = gridRowSpan > 1;

                                results.push({
                                    model_id: modelId,
                                    display_name: displayName,
                                    provider: providerRaw,
                                    category: category,
                                    input_price_cny: firstTier.input_price_cny,
                                    output_price_cny: firstTier.output_price_cny,
                                    cache_price_cny: firstTier.cache_price_cny,
                                    is_free: isFree,
                                    has_tiered_pricing: hasTiered,
                                    price_tiers: hasTiered ? tiers : [],
                                    price_note: hasTiered ? tiers.map(t => t.tier_label + ': 输入¥' + t.input_price_cny + ' / 输出¥' + t.output_price_cny).join(' | ') : ''
                                });
                            });
                        });
                    });

                    return results;
                }""")

                await browser.close()

        except Exception as e:
            elapsed = round((time.time() - start_time) * 1000, 1)
            print(f"[SiliconFlowScraper] 爬取失败: {e}")
            return SiliconFlowScrapeResponse(
                status="error",
                error_message=f"爬取失败: {str(e)}",
                scrape_duration_ms=elapsed
            )

        # 转换为 Pydantic 模型
        models: List[SiliconFlowModelItem] = []
        for item in raw_data:
            tiers = [SiliconFlowPriceTier(**t) for t in item.get("price_tiers", [])]
            models.append(SiliconFlowModelItem(
                model_id=item["model_id"],
                display_name=item["display_name"],
                provider=item["provider"],
                category=item["category"],
                input_price_cny=item.get("input_price_cny", 0),
                output_price_cny=item.get("output_price_cny", 0),
                cache_price_cny=item.get("cache_price_cny", 0),
                is_free=item.get("is_free", False),
                has_tiered_pricing=item.get("has_tiered_pricing", False),
                price_tiers=tiers,
                price_note=item.get("price_note", "")
            ))

        elapsed = round((time.time() - start_time) * 1000, 1)

        # 统计
        category_counts: Dict[str, int] = {}
        free_count = 0
        tiered_count = 0
        for m in models:
            category_counts[m.category] = category_counts.get(m.category, 0) + 1
            if m.is_free:
                free_count += 1
            if m.has_tiered_pricing:
                tiered_count += 1

        print(f"[SiliconFlowScraper] 爬取完成: {len(models)} 个模型, 耗时 {elapsed}ms")
        print(f"[SiliconFlowScraper] 分类统计: {category_counts}")

        return SiliconFlowScrapeResponse(
            status="success",
            total_models=len(models),
            category_counts=category_counts,
            free_models_count=free_count,
            tiered_models_count=tiered_count,
            models=models,
            scrape_duration_ms=elapsed
        )

    async def import_to_database(
        self,
        models: List[SiliconFlowModelItem],
        usd_to_cny_rate: float = 7.25
    ) -> SiliconFlowImportResponse:
        """
        将爬取到的硅基流动模型价格数据写入数据库。
        - 创建或获取 RelaySite 记录
        - 智能匹配或创建 ModelMetadata
        - 创建或更新 SiteModelPricing
        """
        new_models_created = 0
        prices_updated = 0
        prices_created = 0

        try:
            async with AsyncSessionLocal() as session:
                # 1. 获取或创建硅基流动 RelaySite
                stmt = select(RelaySite).where(RelaySite.name == SILICONFLOW_SITE_NAME)
                res = await session.execute(stmt)
                site = res.scalar_one_or_none()

                if not site:
                    site = RelaySite(
                        name=SILICONFLOW_SITE_NAME,
                        base_url=SILICONFLOW_BASE_URL,
                        api_key="",
                        site_type="siliconflow",
                        currency="CNY",
                        recharge_rate=1.0,
                        models_endpoint="/v1/models",
                        website="https://siliconflow.cn",
                        doc_url="https://api-docs.siliconflow.cn",
                        is_official_catalog=False,
                        is_active=True,
                        last_status="online",
                        score=92.0,
                        notes="硅基流动推理平台 · 从官网定价页自动爬取"
                    )
                    session.add(site)
                    await session.flush()  # 获取 site.id

                site.last_sync_time = datetime.utcnow()
                site.last_status = "online"

                # 2. 逐个处理模型
                for item in models:
                    # 2a. 智能匹配或创建 ModelMetadata
                    model_meta = await self._match_or_create_model(
                        session, item
                    )
                    if model_meta and model_meta not in session:
                        # 新创建的模型
                        session.add(model_meta)
                        new_models_created += 1
                        await session.flush()

                    if not model_meta:
                        continue

                    # 2b. 创建或更新 SiteModelPricing
                    # 对于分段定价模型，每个区间段各建一行
                    if item.has_tiered_pricing and item.price_tiers and len(item.price_tiers) > 1:
                        # 先删除旧的单行 "(分段定价)" 记录 (迁移旧数据)
                        old_stmt = select(SiteModelPricing).where(
                            SiteModelPricing.site_id == site.id,
                            SiteModelPricing.model_id == model_meta.model_id
                        )
                        old_res = await session.execute(old_stmt)
                        old_rows = old_res.scalars().all()
                        for old_row in old_rows:
                            await session.delete(old_row)

                        # 为每个区间段创建独立行
                        for tier in item.price_tiers:
                            tier_input_usd = round(tier.input_price_cny / usd_to_cny_rate, 4) if usd_to_cny_rate > 0 else 0
                            tier_output_usd = round(tier.output_price_cny / usd_to_cny_rate, 4) if usd_to_cny_rate > 0 else 0
                            tier_cache_usd = round((tier.cache_price_cny or 0) / usd_to_cny_rate, 4) if usd_to_cny_rate > 0 else 0

                            tier_discount = 0.0
                            if model_meta.official_input_price > 0 and tier_input_usd > 0:
                                tier_discount = round(
                                    ((tier_input_usd - model_meta.official_input_price) / model_meta.official_input_price) * 100, 1
                                )

                            tier_pricing = SiteModelPricing(
                                site_id=site.id,
                                model_id=model_meta.model_id,
                                group_name=item.category,
                                site_model_name=f"{item.display_name} {tier.tier_label}",
                                model_ratio=1.0,
                                group_ratio=1.0,
                                calculated_input_usd=tier_input_usd,
                                calculated_output_usd=tier_output_usd,
                                calculated_cache_usd=tier_cache_usd,
                                discount_percent=tier_discount,
                                is_available=True,
                                source_updated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                            )
                            session.add(tier_pricing)
                            prices_created += 1
                    else:
                        # 非分段定价：正常单行入库
                        input_usd = round(item.input_price_cny / usd_to_cny_rate, 4) if usd_to_cny_rate > 0 else 0
                        output_usd = round(item.output_price_cny / usd_to_cny_rate, 4) if usd_to_cny_rate > 0 else 0
                        cache_usd = round(item.cache_price_cny / usd_to_cny_rate, 4) if usd_to_cny_rate > 0 else 0

                        p_stmt = select(SiteModelPricing).where(
                            SiteModelPricing.site_id == site.id,
                            SiteModelPricing.model_id == model_meta.model_id
                        )
                        p_res = await session.execute(p_stmt)
                        pricing = p_res.scalar_one_or_none()

                        if pricing:
                            pricing.calculated_input_usd = input_usd
                            pricing.calculated_output_usd = output_usd
                            pricing.calculated_cache_usd = cache_usd
                            pricing.is_available = True
                            pricing.source_updated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                            pricing.group_name = item.category
                            pricing.site_model_name = item.display_name
                            prices_updated += 1
                        else:
                            discount = 0.0
                            if model_meta.official_input_price > 0 and input_usd > 0:
                                discount = round(
                                    ((input_usd - model_meta.official_input_price) / model_meta.official_input_price) * 100, 1
                                )

                            new_pricing = SiteModelPricing(
                                site_id=site.id,
                                model_id=model_meta.model_id,
                                group_name=item.category,
                                site_model_name=item.display_name,
                                model_ratio=1.0,
                                group_ratio=1.0,
                                calculated_input_usd=input_usd,
                                calculated_output_usd=output_usd,
                                calculated_cache_usd=cache_usd,
                                discount_percent=discount,
                                is_available=True,
                                source_updated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                            )
                            session.add(new_pricing)
                            prices_created += 1

                await session.commit()

                return SiliconFlowImportResponse(
                    status="success",
                    site_id=site.id,
                    site_name=site.name,
                    total_imported=len(models),
                    new_models_created=new_models_created,
                    prices_updated=prices_updated,
                    prices_created=prices_created
                )

        except Exception as e:
            print(f"[SiliconFlowScraper] 导入数据库失败: {e}")
            return SiliconFlowImportResponse(
                status="error",
                error_message=f"导入失败: {str(e)}"
            )

    async def _match_or_create_model(
        self, session, item: SiliconFlowModelItem
    ) -> Optional[ModelMetadata]:
        """
        尝试将硅基流动的模型与现有 ModelMetadata 匹配。
        匹配策略：
        1. 精确匹配 model_id
        2. 将硅基流动的 provider/ModelName 格式转换后模糊匹配
        3. 匹配不上则创建新的 ModelMetadata
        """
        full_id = item.model_id  # 如 deepseek-ai/DeepSeek-V4-Flash

        # 策略 1: 精确匹配（原始 model_id）
        stmt = select(ModelMetadata).where(ModelMetadata.model_id == full_id)
        res = await session.execute(stmt)
        match = res.scalar_one_or_none()
        if match:
            return match

        # 策略 2: 将 model_id 转为小写匹配
        lower_id = full_id.lower()
        stmt2 = select(ModelMetadata).where(
            ModelMetadata.model_id == lower_id
        )
        res2 = await session.execute(stmt2)
        match2 = res2.scalar_one_or_none()
        if match2:
            return match2

        # 策略 3: 提取模型短名匹配（去除 provider 前缀和 Pro/ 前缀）
        short_name = full_id
        if "/" in short_name:
            parts = short_name.split("/")
            short_name = parts[-1]  # 取最后一段
        short_lower = short_name.lower()

        stmt3 = select(ModelMetadata).where(
            ModelMetadata.model_id == short_lower
        )
        res3 = await session.execute(stmt3)
        match3 = res3.scalar_one_or_none()
        if match3:
            return match3

        # 策略 4: 去除连字符、大小写等模糊匹配
        # 例如 DeepSeek-V3.2 -> deepseek-v3.2
        normalized = short_lower.replace("_", "-")
        stmt4 = select(ModelMetadata).where(
            ModelMetadata.model_id == normalized
        )
        res4 = await session.execute(stmt4)
        match4 = res4.scalar_one_or_none()
        if match4:
            return match4

        # 策略 5: 都匹配不上，创建新的 ModelMetadata
        provider_normalized = PROVIDER_NORMALIZE.get(item.provider, item.provider.lower())

        # 确定模态
        modality_map = {"对话": "text", "生图": "image", "语音": "audio", "视频": "video"}
        modality = modality_map.get(item.category, "text")

        new_model = ModelMetadata(
            model_id=full_id,
            name=item.display_name,
            provider=provider_normalized,
            series=item.display_name.split("-")[0] if "-" in item.display_name else item.display_name,
            context_window=128000 if item.category == "对话" else 0,
            max_output=4096 if item.category == "对话" else 0,
            official_input_price=round(item.input_price_cny / 7.25, 4),  # 大致转换
            official_output_price=round(item.output_price_cny / 7.25, 4),
            official_cache_price=round(item.cache_price_cny / 7.25, 4),
            modalities=modality,
            open_weights=False,
            release_date=datetime.utcnow().strftime("%Y-%m-%d"),
            description=f"从硅基流动官网自动导入 ({item.category}模型)"
        )
        return new_model


# 模块级单例
siliconflow_scraper = SiliconFlowScraperService()
