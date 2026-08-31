"""
阿里百炼 Aliyun Model Studio 官网定价页爬取服务

通过访问阿里云帮助中心官方定价页面:
https://help.aliyun.com/zh/model-studio/model-pricing
精确解析「华北2（北京）」主力地域的全部模型价格表格，涵盖：
- 通义千问全系列 (Qwen-Max / Plus / Flash / Turbo / QwQ / QVQ / VL / Audio / Coder 等)
- 第三方开源模型 (DeepSeek-R1 / V3, Llama 3 系列, Kimi, GLM, MiniMax 等)
- 图像、视频、语音及向量模型 (Wanx 万相, CosyVoice, SenseVoice, Paraformer 等)
支持限时折扣折算与分段阶梯定价拆行入库。
"""
import re
import time
import httpx
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from sqlalchemy import select, delete

from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import RelaySite, ModelMetadata, SiteModelPricing, ChannelSnapshot
from backend.app.schemas.token_schema import (
    BailianModelItem, BailianPriceTier,
    BailianScrapeResponse, BailianImportResponse
)

BAILIAN_PRICING_URL = "https://help.aliyun.com/zh/model-studio/model-pricing"
BAILIAN_SITE_NAME = "阿里百炼 (Model Studio)"
BAILIAN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 厂商标准化映射
PROVIDER_MAP = {
    "deepseek": "deepseek",
    "glm": "zhipuai",
    "chatglm": "zhipuai",
    "智谱": "zhipuai",
    "kimi": "moonshotai",
    "moonshot": "moonshotai",
    "minimax": "minimax",
    "llama": "meta",
    "mimo": "xiaomi",
    "step": "stepfun",
    "unisound": "unisound",
    "qwen": "alibaba",
    "wanx": "alibaba",
    "cosyvoice": "alibaba",
    "sensevoice": "alibaba",
    "paraformer": "alibaba",
    "sambert": "alibaba",
    "bge": "baai",
}


def _infer_provider(model_id: str, category: str = "") -> str:
    """根据模型 ID 与分类推断所属厂商"""
    mid_low = (model_id or "").lower()
    cat_low = (category or "").lower()

    for k, v in PROVIDER_MAP.items():
        if k in mid_low or k in cat_low:
            return v
    if "第三方" in category:
        return "community"
    return "alibaba"


def _infer_context_and_output(model_id: str) -> tuple[int, int]:
    """根据模型名称预估默认上下文与最大输出 Token"""
    mid = (model_id or "").lower()
    if "1m" in mid or "max" in mid or "plus" in mid:
        return 1000000, 16384
    if "128k" in mid or "deepseek" in mid or "r1" in mid or "v3" in mid:
        return 128000, 8192
    if "32k" in mid:
        return 32768, 8192
    if "vl" in mid or "omni" in mid:
        return 128000, 8192
    return 131072, 8192


def _parse_price_text(text: str) -> float:
    """解析价格文本，自动计算限时折扣折后价与免费标识"""
    if not text:
        return 0.0
    text = text.strip()
    if "免费" in text or "0元" in text or "0 元" in text or "无阶梯计价" in text:
        return 0.0

    # 1. 识别限时折扣：如 '原价 12 元（限时 5 折）' 或 '原价 2 元（限时 8 折）'
    discount_match = re.search(r"原价\s*([0-9.]+)\s*元.*?(?:限时\s*([0-9.]+)\s*折)", text)
    if discount_match:
        original = float(discount_match.group(1))
        discount_rate = float(discount_match.group(2)) / 10.0
        return round(original * discount_rate, 4)

    # 2. 提取标准价格：如 '12 元', '2.5 元', '¥10.0'
    num_match = re.search(r"([0-9.]+)\s*(?:元|¥)", text)
    if num_match:
        return float(num_match.group(1))

    # 3. 纯数字
    num_only = re.search(r"^([0-9.]+)$", text)
    if num_only:
        return float(num_only.group(1))

    return 0.0


def _is_tier_text(text: str) -> bool:
    """判定文本是否为阶梯区间描述而非模型名"""
    if not text:
        return False
    t = text.strip()
    return any(k in t for k in ["Token≤", "Token<", "0<", "K<", "M<", "<Token", "≤Token", "无阶梯计价", "阶梯", "单次请求"])


class BailianScraper:
    """阿里百炼官方定价页抓取与解析器"""

    def __init__(self, pricing_url: str = BAILIAN_PRICING_URL):
        self.pricing_url = pricing_url
        self.last_raw_html: str = ""
        self.last_doc_updated_at: str = ""

    async def fetch_page_content(self) -> str:
        """拉取阿里百炼定价帮助文档 HTML"""
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

    def parse_pricing_html(self, html_content: str) -> List[BailianModelItem]:
        """从 HTML / SSR JSON 中解析出全部模型定价清单"""
        # 尝试提取 window.__ICE_PAGE_PROPS__
        m = re.search(r"window\.__ICE_PAGE_PROPS__\s*=\s*(\{.*?\});", html_content, re.DOTALL)
        if m:
            import json
            try:
                data = json.loads(m.group(1))
                doc_data = data.get("docDetailData", {}).get("storeData", {}).get("data", {})
                doc_content = doc_data.get("content", "")
                self.last_doc_updated_at = doc_data.get("updateTime", "") or datetime.utcnow().strftime("%Y-%m-%d")
                self.last_raw_html = doc_content or html_content
                soup = BeautifulSoup(doc_content, "html.parser")
            except Exception as e:
                print(f"[BailianScraper] 解析 __ICE_PAGE_PROPS__ 失败，回退至全局 HTML: {e}")
                self.last_raw_html = html_content
                soup = BeautifulSoup(html_content, "html.parser")
        else:
            self.last_raw_html = html_content
            soup = BeautifulSoup(html_content, "html.parser")

        # 临时聚合字典，模型 ID -> 模型详情与分段
        models_map: Dict[str, BailianModelItem] = {}
        current_category = "千问系列"

        for elem in soup.find_all(["h2", "h3", "section", "table"]):
            if elem.name == "h2":
                h2_text = elem.get_text(strip=True)
                if "第三方" in h2_text:
                    current_category = "第三方开源模型"
                elif "图像" in h2_text:
                    current_category = "生图与视觉"
                elif "语音" in h2_text or "音频" in h2_text:
                    current_category = "语音与音频"
                elif "视频" in h2_text:
                    current_category = "视频生成"
                elif "向量" in h2_text or "排序" in h2_text:
                    current_category = "向量与排序"
                elif "千问" in h2_text:
                    current_category = "千问系列"
            elif elem.name == "section":
                sec_id = elem.get("id", "")
                # 过滤海外地域板块，只保留北京或通用表格
                if sec_id in ["美国-弗吉尼亚", "新加坡", "德国-法兰克福", "日本-东京"]:
                    continue
            elif elem.name == "table":
                # 检查 table 是否包含在海外地域 section 内
                parent_sec = elem.find_parent("section")
                if parent_sec and parent_sec.get("id") in ["美国-弗吉尼亚", "新加坡", "德国-法兰克福", "日本-东京"]:
                    continue

                headers = [th.get_text(strip=True) for th in elem.find_all("th")]
                if not headers:
                    continue

                tbody = elem.find("tbody")
                if not tbody:
                    continue

                active_model_id = ""
                active_display_name = ""

                for tr in tbody.find_all("tr"):
                    tds = tr.find_all("td")
                    if not tds:
                        continue

                    td_texts = []
                    for td in tds:
                        p_first = td.find("p")
                        if p_first:
                            td_texts.append(p_first.get_text(strip=True))
                        else:
                            td_texts.append(td.get_text(strip=True))

                    first_text = td_texts[0] if len(td_texts) > 0 else ""

                    # 1. 严格检查第一列是否为阶梯区间（由于上一行 rowspan 产生的跨行）
                    if _is_tier_text(first_text):
                        tier_label = first_text
                    else:
                        clean_id = re.split(r"[\n（(]", first_text)[0].strip()
                        # 过滤非法模型名称 (如包含比较符、说明性文字等)
                        if (
                            clean_id
                            and not _is_tier_text(clean_id)
                            and not any(k in clean_id for k in ["<", ">", "≤", "≥", "限时", "免费", "注：", "说明", "规则"])
                            and not clean_id.startswith("http")
                        ):
                            active_model_id = clean_id
                            active_display_name = clean_id
                        tier_label = ""

                    if not active_model_id:
                        continue

                    # 2. 提取阶梯区间与单价
                    input_price = 0.0
                    output_price = 0.0
                    price_note = ""

                    for t_val in td_texts:
                        if _is_tier_text(t_val):
                            tier_label = t_val
                        elif "元" in t_val or "¥" in t_val or "免费" in t_val:
                            p = _parse_price_text(t_val)
                            if "折" in t_val:
                                price_note = t_val
                            if input_price == 0.0:
                                input_price = p
                            elif output_price == 0.0:
                                output_price = p

                    if output_price == 0.0 and input_price > 0.0:
                        output_price = input_price

                    provider = _infer_provider(active_model_id, current_category)

                    # 3. 构造或更新模型项
                    if active_model_id not in models_map:
                        item = BailianModelItem(
                            model_id=active_model_id,
                            display_name=active_display_name,
                            provider=provider,
                            category=current_category,
                            input_price_cny=input_price,
                            output_price_cny=output_price,
                            cache_price_cny=0.0,
                            is_free=(input_price == 0.0 and output_price == 0.0),
                            has_tiered_pricing=bool(tier_label),
                            price_tiers=[],
                            price_note=price_note
                        )
                        if tier_label:
                            item.price_tiers.append(BailianPriceTier(
                                tier_label=tier_label,
                                input_price_cny=input_price,
                                output_price_cny=output_price,
                                cache_price_cny=0.0
                            ))
                        models_map[active_model_id] = item
                    else:
                        existing = models_map[active_model_id]
                        if tier_label:
                            # 避免重复添加完全相同区间的阶梯（去重）
                            existing_labels = {t.tier_label for t in existing.price_tiers}
                            if tier_label not in existing_labels:
                                existing.has_tiered_pricing = True
                                existing.price_tiers.append(BailianPriceTier(
                                    tier_label=tier_label,
                                    input_price_cny=input_price,
                                    output_price_cny=output_price,
                                    cache_price_cny=0.0
                                ))

        return list(models_map.values())

    async def scrape_pricing_page(self) -> BailianScrapeResponse:
        """抓取并解析阿里百炼定价页全流程"""
        start_time = time.time()
        try:
            html = await self.fetch_page_content()
            models = self.parse_pricing_html(html)

            # 统计分类与特征
            category_counts: Dict[str, int] = {}
            free_count = 0
            tiered_count = 0

            for m in models:
                cat = m.category or "千问系列"
                category_counts[cat] = category_counts.get(cat, 0) + 1
                if m.is_free:
                    free_count += 1
                if m.has_tiered_pricing:
                    tiered_count += 1

            duration_ms = round((time.time() - start_time) * 1000, 2)
            return BailianScrapeResponse(
                status="success",
                total_models=len(models),
                category_counts=category_counts,
                free_models_count=free_count,
                tiered_models_count=tiered_count,
                models=models,
                scrape_duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            print(f"[BailianScraper] 抓取解析失败: {e}")
            return BailianScrapeResponse(
                status="error",
                total_models=0,
                models=[],
                scrape_duration_ms=duration_ms,
                error_message=str(e)
            )

    async def _match_or_create_model(
        self, session, item: BailianModelItem, usd_to_cny_rate: float
    ) -> Optional[ModelMetadata]:
        """智能匹配现有 ModelMetadata 或创建新记录"""
        mid = item.model_id
        mid_lower = mid.lower()

        # 1. 精确匹配
        stmt = select(ModelMetadata).where(ModelMetadata.model_id == mid)
        res = await session.execute(stmt)
        match = res.scalars().first()
        if match:
            return match

        # 2. 小写匹配
        stmt2 = select(ModelMetadata).where(ModelMetadata.model_id == mid_lower)
        res2 = await session.execute(stmt2)
        match2 = res2.scalars().first()
        if match2:
            return match2

        # 3. 补齐 provider/ 前缀匹配 (例如 alibaba/qwen3.8-max)
        alt_id = f"{item.provider}/{mid_lower}"
        stmt3 = select(ModelMetadata).where(ModelMetadata.model_id == alt_id)
        res3 = await session.execute(stmt3)
        match3 = res3.scalars().first()
        if match3:
            return match3

        # 4. 创建新的 ModelMetadata
        ctx_w, max_o = _infer_context_and_output(mid)
        input_usd = round(item.input_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0
        output_usd = round(item.output_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0

        modality = "text"
        if "生图" in item.category or "视觉" in item.category:
            modality = "image"
        elif "语音" in item.category or "音频" in item.category:
            modality = "audio"
        elif "视频" in item.category:
            modality = "video"
        elif "向量" in item.category:
            modality = "embeddings"

        new_meta = ModelMetadata(
            model_id=mid,
            name=item.display_name,
            provider=item.provider,
            series=item.display_name.split("-")[0] if "-" in item.display_name else "Qwen",
            context_window=ctx_w,
            max_output=max_o,
            official_input_price=input_usd,
            official_output_price=output_usd,
            official_cache_price=0.0,
            modalities=modality,
            capabilities="reasoning,tool_calling" if ("qwq" in mid_lower or "r1" in mid_lower) else "tool_calling",
            open_weights=False,
            release_date=datetime.utcnow().strftime("%Y-%m-%d"),
            description=f"从阿里百炼官方定价页自动导入 ({item.category})"
        )
        return new_meta

    async def save_to_database(
        self,
        models: List[BailianModelItem],
        site_id: Optional[int] = None,
        usd_to_cny_rate: float = 7.25
    ) -> BailianImportResponse:
        """将抓取到的模型列表写入或更新至数据库中"""
        new_models_created = 0
        prices_created = 0

        try:
            async with AsyncSessionLocal() as session:
                # 1. 查找或创建阿里百炼 RelaySite
                site = None
                if site_id:
                    site = await session.get(RelaySite, site_id)

                if not site:
                    stmt = select(RelaySite).where(
                        (RelaySite.site_type == "aliyun_bailian") | (RelaySite.name == BAILIAN_SITE_NAME)
                    )
                    res = await session.execute(stmt)
                    site = res.scalars().first()

                if not site:
                    site = RelaySite(
                        name=BAILIAN_SITE_NAME,
                        base_url=BAILIAN_BASE_URL,
                        api_key="",
                        site_type="aliyun_bailian",
                        currency="CNY",
                        recharge_rate=1.0,
                        models_endpoint="/v1/models",
                        website="https://bailian.console.aliyun.com",
                        doc_url="https://help.aliyun.com/zh/model-studio/model-pricing",
                        is_official_catalog=False,
                        is_active=True,
                        last_status="online",
                        score=95.0,
                        notes="阿里百炼大模型服务平台 · 从阿里云帮助中心官方定价页自动抓取"
                    )
                    session.add(site)
                    await session.flush()

                site.last_sync_time = datetime.utcnow()
                site.last_status = "online"
                now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M")

                # 2. 持久化定价页面快照 ChannelSnapshot
                if self.last_raw_html:
                    snap_stmt = select(ChannelSnapshot).where(ChannelSnapshot.site_id == site.id)
                    snap_res = await session.execute(snap_stmt)
                    snapshot = snap_res.scalars().first()
                    doc_date = self.last_doc_updated_at or datetime.utcnow().strftime("%Y-%m-%d")
                    if not snapshot:
                        snapshot = ChannelSnapshot(
                            site_id=site.id,
                            source_url=self.pricing_url,
                            page_title="阿里云百炼 (Model Studio) 模型定价与规格说明",
                            doc_updated_at=doc_date,
                            fetched_at=datetime.utcnow(),
                            raw_html=self.last_raw_html,
                            models_count=len(models)
                        )
                        session.add(snapshot)
                    else:
                        snapshot.source_url = self.pricing_url
                        snapshot.doc_updated_at = doc_date
                        snapshot.fetched_at = datetime.utcnow()
                        snapshot.raw_html = self.last_raw_html
                        snapshot.models_count = len(models)

                # 3. 清理历史可能产生的非法 ModelMetadata 与 SiteModelPricing 脏数据
                stmt_del_p = delete(SiteModelPricing).where(
                    (SiteModelPricing.model_id.like("%<%"))
                    | (SiteModelPricing.model_id.like("%≤%"))
                    | (SiteModelPricing.model_id.like("%Token%"))
                )
                await session.execute(stmt_del_p)
                stmt_del_m = delete(ModelMetadata).where(
                    (ModelMetadata.model_id.like("%<%"))
                    | (ModelMetadata.model_id.like("%≤%"))
                    | (ModelMetadata.model_id.like("%Token%"))
                )
                await session.execute(stmt_del_m)

                # 3. 逐个处理模型
                for item in models:
                    model_meta = await self._match_or_create_model(session, item, usd_to_cny_rate)
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

                    # 3b. 写入阶梯定价或单一定价
                    if item.has_tiered_pricing and item.price_tiers and len(item.price_tiers) > 1:
                        for tier in item.price_tiers:
                            tier_input_usd = round(tier.input_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0
                            tier_output_usd = round(tier.output_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0

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
                                calculated_cache_usd=0.0,
                                discount_percent=tier_discount,
                                is_available=True,
                                source_updated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                            )
                            session.add(tier_pricing)
                            prices_created += 1
                    else:
                        input_usd = round(item.input_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0
                        output_usd = round(item.output_price_cny / usd_to_cny_rate, 6) if usd_to_cny_rate > 0 else 0.0

                        discount = 0.0
                        if model_meta.official_input_price > 0 and input_usd > 0:
                            discount = round(
                                ((input_usd - model_meta.official_input_price) / model_meta.official_input_price) * 100, 1
                            )

                        pricing = SiteModelPricing(
                            site_id=site.id,
                            model_id=model_meta.model_id,
                            group_name=item.category,
                            site_model_name=item.display_name,
                            model_ratio=1.0,
                            group_ratio=1.0,
                            calculated_input_usd=input_usd,
                            calculated_output_usd=output_usd,
                            calculated_cache_usd=0.0,
                            discount_percent=discount,
                            is_available=True,
                            source_updated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M")
                        )
                        session.add(pricing)
                        prices_created += 1

                await session.commit()

                return BailianImportResponse(
                    status="success",
                    site_id=site.id,
                    site_name=site.name,
                    total_imported=len(models),
                    new_models_created=new_models_created,
                    prices_updated=0,
                    prices_created=prices_created
                )
        except Exception as e:
            print(f"[BailianScraper] 保存至数据库失败: {e}")
            return BailianImportResponse(
                status="error",
                error_message=str(e)
            )


# 单例
bailian_scraper = BailianScraper()
