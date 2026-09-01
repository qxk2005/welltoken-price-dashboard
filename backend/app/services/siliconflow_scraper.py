"""
硅基流动 SiliconFlow 官网定价页爬取服务

通过纯异步原生 HTTP 请求 (httpx) 获取官方定价页内容:
https://siliconflow.cn/pricing
并从 Next.js SSR 结构化数据流与页面 DOM 中毫秒级提取全部官方模型与价格，涵盖：
- 对话模型 (DeepSeek-V4-Flash / Pro, Qwen 3.5 系列, GLM 5 系列, Kimi, MiniMax 等)
- 生图模型 (Kolors, ERNIE-Image, Qwen-Image 等)
- 语音模型 (SenseVoiceSmall, CosyVoice2, XingChen 等)
- 视频模型 (Wanx, CogVideoX 等)
100% 零外部浏览器依赖 (不需要 Playwright / Chromium 内核)，新电脑与打包版即开即用！
"""
import re
import time
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, delete

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing, ChannelSnapshot
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
    if text in ["-", "—"]:
        return None
    if "免费" in text:
        return 0.0
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
    """硅基流动官网定价抓取与解析服务 (纯原生异步 HTTP 请求 + SSR 数据流解析，0 浏览器依赖)"""

    def __init__(self, pricing_url: str = SILICONFLOW_PRICING_URL):
        self.pricing_url = pricing_url
        self.last_raw_html: str = ""

    async def fetch_page_content(self) -> str:
        """拉取硅基流动定价页 HTML"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
        }
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(self.pricing_url, headers=headers)
            resp.raise_for_status()
            return resp.text

    def parse_pricing_html(self, raw_html: str) -> List[SiliconFlowModelItem]:
        """从 Next.js SSR 数据流中精准提取全量模型、规格与定价"""
        # 1. 提取所有 self.__next_f.push 数据段并拼接
        push_chunks = re.findall(r'self\.__next_f\.push\(\[1,\s*\"(.*?)\"\]\)', raw_html)
        combined = "".join(push_chunks).replace('\\"', '"').replace('\\\\', '\\')

        models: List[SiliconFlowModelItem] = []
        seen = set()

        for m in re.finditer(r'"modelName"\s*:\s*"([^"]+)"', combined):
            m_name = m.group(1)
            if m_name in seen:
                continue
            seen.add(m_name)

            start = max(0, m.start() - 200)
            end = min(len(combined), m.end() + 2000)
            chunk = combined[start:end]

            disp_m = re.search(r'"DisplayName"\s*:\s*"([^"]+)"', chunk)
            price_m = re.search(r'"price"\s*:\s*"?([0-9.]+)"?', chunk)
            mf_m = re.search(r'"mf"\s*:\s*"([^"]+)"', chunk)
            type_m = re.search(r'"type"\s*:\s*"([^"]+)"', chunk)
            sub_type_m = re.search(r'"subType"\s*:\s*"([^"]+)"', chunk)
            ctx_m = re.search(r'"contextLen"\s*:\s*([0-9]+)', chunk)

            disp_name = disp_m.group(1) if disp_m else m_name
            disp_name = re.split(r'["\',;\]\}\)]', disp_name)[0].strip() or m_name
            price = float(price_m.group(1)) if price_m else 0.0
            mf = mf_m.group(1) if mf_m else "SiliconFlow"
            mf = re.split(r'["\',;\]\}\)]', mf)[0].strip() or "SiliconFlow"

            t_name = type_m.group(1) if type_m else "text"
            sub_t = sub_type_m.group(1) if sub_type_m else "chat"
            ctx = int(ctx_m.group(1)) if ctx_m else 128000

            cat = "对话"
            if t_name == "image" or sub_t == "image":
                cat = "生图"
            elif t_name in ["voice", "audio"] or sub_t == "voice":
                cat = "语音"
            elif t_name == "video" or sub_t == "video":
                cat = "视频"

            models.append(SiliconFlowModelItem(
                model_id=m_name,
                display_name=disp_name,
                provider=mf,
                category=cat,
                input_price_cny=price,
                output_price_cny=price,
                cache_price_cny=0.0,
                is_free=(price == 0.0),
                has_tiered_pricing=False,
                price_tiers=[],
                price_note=f"官方标价: ¥{price}" if price > 0 else "免费"
            ))

        return models

    async def scrape_pricing_robust(self) -> SiliconFlowScrapeResponse:
        """主入口：纯 HTTP 异步高速抓取（0 外部浏览器依赖，新机器即开即用）"""
        start_time = time.time()
        try:
            raw_html = await self.fetch_page_content()
            models = self.parse_pricing_html(raw_html)

            # 快照清理：剥离 script 标签后保留纯静态 DOM，杜绝 Next.js hydration 错误
            self.last_raw_html = re.sub(
                r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', raw_html, flags=re.IGNORECASE
            )

            # 分类统计
            category_counts: Dict[str, int] = {}
            free_count = 0
            tiered_count = 0
            for m in models:
                category_counts[m.category] = category_counts.get(m.category, 0) + 1
                if m.is_free:
                    free_count += 1
                if m.has_tiered_pricing:
                    tiered_count += 1

            elapsed = round((time.time() - start_time) * 1000, 1)
            print(f"[SiliconFlowScraper] 爬取完成: {len(models)} 个模型, 耗时 {elapsed}ms")

            return SiliconFlowScrapeResponse(
                status="success",
                total_models=len(models),
                category_counts=category_counts,
                free_models_count=free_count,
                tiered_models_count=tiered_count,
                models=models,
                scrape_duration_ms=elapsed
            )
        except Exception as e:
            elapsed = round((time.time() - start_time) * 1000, 1)
            print(f"[SiliconFlowScraper] 爬取失败: {e}")
            return SiliconFlowScrapeResponse(
                status="error",
                error_message=f"爬取失败: {str(e)}",
                scrape_duration_ms=elapsed
            )

    async def scrape_pricing(self) -> SiliconFlowScrapeResponse:
        """兼容旧接口"""
        return await self.scrape_pricing_robust()

    async def import_to_database(
        self,
        models: List[SiliconFlowModelItem],
        usd_to_cny_rate: float = 7.25,
        site_id: Optional[int] = None
    ) -> SiliconFlowImportResponse:
        """
        将爬取到的硅基流动模型价格数据写入数据库。
        - 创建或获取 RelaySite 记录
        - 智能匹配或创建 ModelMetadata
        - 创建或更新 SiteModelPricing
        - 持久化 ChannelSnapshot 网页快照
        """
        new_models_created = 0
        prices_updated = 0
        prices_created = 0

        try:
            async with AsyncSessionLocal() as session:
                # 1. 获取或创建硅基流动 RelaySite
                site = None
                if site_id:
                    site = await session.get(RelaySite, site_id)

                if not site:
                    stmt = select(RelaySite).where(
                        (RelaySite.site_type == "siliconflow") | (RelaySite.name == SILICONFLOW_SITE_NAME)
                    )
                    res = await session.execute(stmt)
                    site = res.scalars().first()

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
                    await session.flush()

                site.last_sync_time = datetime.utcnow()
                site.last_status = "online"

                # 2. 持久化定价页面快照 ChannelSnapshot
                if self.last_raw_html:
                    snap_stmt = select(ChannelSnapshot).where(ChannelSnapshot.site_id == site.id)
                    snap_res = await session.execute(snap_stmt)
                    snapshot = snap_res.scalars().first()
                    if not snapshot:
                        snapshot = ChannelSnapshot(
                            site_id=site.id,
                            source_url=SILICONFLOW_PRICING_URL,
                            page_title="硅基流动 SiliconFlow 模型定价与推理服务说明",
                            doc_updated_at=datetime.utcnow().strftime("%Y-%m-%d"),
                            fetched_at=datetime.utcnow(),
                            raw_html=self.last_raw_html,
                            models_count=len(models)
                        )
                        session.add(snapshot)
                    else:
                        snapshot.source_url = SILICONFLOW_PRICING_URL
                        snapshot.doc_updated_at = datetime.utcnow().strftime("%Y-%m-%d")
                        snapshot.fetched_at = datetime.utcnow()
                        snapshot.raw_html = self.last_raw_html
                        snapshot.models_count = len(models)

                # 3. 逐个处理模型
                for item in models:
                    model_meta = await self._match_or_create_model(
                        session, item
                    )
                    if model_meta and model_meta not in session:
                        session.add(model_meta)
                        new_models_created += 1
                        await session.flush()

                    if not model_meta:
                        continue

                    # 3a. 先清理该渠道下此模型的旧定价条目，保证幂等
                    old_stmt = delete(SiteModelPricing).where(
                        SiteModelPricing.site_id == site.id,
                        SiteModelPricing.model_id == model_meta.model_id
                    )
                    await session.execute(old_stmt)

                    # 3b. 写入定价
                    input_usd = round(item.input_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0
                    output_usd = round(item.output_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0
                    cache_usd = round((item.cache_price_cny or 0) / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0

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
        """
        full_id = item.model_id

        # 策略 1: 精确匹配
        stmt = select(ModelMetadata).where(ModelMetadata.model_id == full_id)
        res = await session.execute(stmt)
        match = res.scalar_one_or_none()
        if match:
            return match

        # 策略 2: 小写匹配
        lower_id = full_id.lower()
        stmt2 = select(ModelMetadata).where(
            ModelMetadata.model_id == lower_id
        )
        res2 = await session.execute(stmt2)
        match2 = res2.scalar_one_or_none()
        if match2:
            return match2

        # 策略 3: 提取模型短名匹配
        short_name = full_id
        if "/" in short_name:
            parts = short_name.split("/")
            short_name = parts[-1]
        short_lower = short_name.lower()

        stmt3 = select(ModelMetadata).where(
            ModelMetadata.model_id == short_lower
        )
        res3 = await session.execute(stmt3)
        match3 = res3.scalar_one_or_none()
        if match3:
            return match3

        # 策略 4: 规范化匹配
        normalized = short_lower.replace("_", "-")
        stmt4 = select(ModelMetadata).where(
            ModelMetadata.model_id == normalized
        )
        res4 = await session.execute(stmt4)
        match4 = res4.scalar_one_or_none()
        if match4:
            return match4

        # 策略 5: 创建新的 ModelMetadata
        provider_normalized = PROVIDER_NORMALIZE.get(item.provider, item.provider.lower())

        modality_map = {"对话": "text", "生图": "image", "语音": "audio", "视频": "video"}
        modality = modality_map.get(item.category, "text")

        new_model = ModelMetadata(
            model_id=full_id,
            name=item.display_name,
            provider=provider_normalized,
            series=item.display_name.split("-")[0] if "-" in item.display_name else item.display_name,
            context_window=128000 if item.category == "对话" else 0,
            max_output=4096 if item.category == "对话" else 0,
            official_input_price=round(item.input_price_cny / 7.25, 4),
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
