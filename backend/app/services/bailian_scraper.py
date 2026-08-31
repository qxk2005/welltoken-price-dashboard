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
from typing import List, Dict, Any, Optional, Tuple
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


def _clean_spec_segment(text: str) -> str:
    """清洗单项规格修饰词，去除多余的技术参数与列头"""
    t = text.strip()
    if not t:
        return ""
    if any(k in t for k in ["免费额度", "刊例价", "模型名称", "规格名称", "计费单元", "单价"]):
        return ""
    if "audio=true" in t or t in ["有声视频", "有声"]:
        return "有声"
    if "audio=false" in t or t in ["无声视频", "无声"]:
        return "无声"
    if "有参考" in t:
        return "有参考视频"
    if "无参考" in t:
        return "无参考视频"
    if "首尾帧" in t:
        return "首尾帧"
    if re.match(r"^\d+P$", t, re.I):
        return t.upper()
    return t


def _generate_spec_model_id(base_id: str, spec_desc: str) -> str:
    """为多规格拆分模型生成规范唯一的 model_id"""
    if not spec_desc:
        return base_id
    slug = spec_desc
    slug = slug.replace("有参考视频", "ref").replace("无参考视频", "noref")
    slug = slug.replace("有声", "audio").replace("无声", "noaudio")
    slug = slug.replace("首尾帧", "kf")
    slug = slug.replace(" · ", "-").replace(" ", "-")
    slug = re.sub(r"[^a-zA-Z0-9.\-_/]", "", slug)
    return f"{base_id}-{slug}".strip("-")


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
        """从 HTML / SSR JSON 中解析出全部模型定价清单 (使用 2D 矩阵填充还原多维跨行表格)"""
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

        # 临时聚合字典，item_key -> 模型项
        models_map: Dict[str, BailianModelItem] = {}
        current_category = "千问系列"

        for elem in soup.find_all(["h2", "h3", "section", "table"]):
            if elem.name == "h2":
                h2_text = elem.get_text(strip=True)
                if "第三方" in h2_text:
                    current_category = "第三方开源模型"
                elif "图像" in h2_text or "生图" in h2_text:
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
                parent_sec = elem.find_parent("section")
                if parent_sec and parent_sec.get("id") in ["美国-弗吉尼亚", "新加坡", "德国-法兰克福", "日本-东京"]:
                    continue

                tbody = elem.find("tbody")
                if not tbody:
                    continue

                trs = tbody.find_all("tr")
                if not trs:
                    continue

                # 1. 构建 2D 虚拟矩阵，完美解决多重 rowspan / colspan 错位问题
                grid: Dict[Tuple[int, int], str] = {}
                for r_idx, tr in enumerate(trs):
                    c_idx = 0
                    for td in tr.find_all(["td", "th"]):
                        while (r_idx, c_idx) in grid:
                            c_idx += 1

                        rowspan = int(td.get("rowspan", 1))
                        colspan = int(td.get("colspan", 1))
                        text = td.get_text(" ", strip=True)

                        for dr in range(rowspan):
                            for dc in range(colspan):
                                grid[(r_idx + dr, c_idx + dc)] = text

                        c_idx += colspan

                max_r = len(trs)
                max_c = max(c for (r, c) in grid.keys()) + 1 if grid else 0

                # 2. 逐行解析矩阵中的完整实体数据
                for r in range(max_r):
                    row_cells = [grid.get((r, c), "").strip() for c in range(max_c)]
                    if not row_cells or not row_cells[0]:
                        continue

                    first_cell = row_cells[0]
                    # 过滤纯说明行与过长文字
                    if any(k in first_cell for k in ["注：", "说明", "规则", "http://", "https://"]) or len(first_cell) > 100:
                        continue

                    base_model_id = re.split(r"[\n（(]", first_cell)[0].strip()
                    if not base_model_id or _is_tier_text(base_model_id):
                        continue

                    # 3. 定位价格列与提取价格
                    price_idx = -1
                    price_val = 0.0
                    for ci, cell in enumerate(row_cells):
                        if any(u in cell for u in ["元", "¥", "免费"]) and not _is_tier_text(cell):
                            price_val = _parse_price_text(cell)
                            price_idx = ci
                            break

                    if price_idx == -1:
                        continue

                    # 4. 提取中间规格列与阶梯区间
                    specs: List[str] = []
                    tier_label = ""
                    for ci in range(1, price_idx):
                        c_text = row_cells[ci]
                        if not c_text:
                            continue
                        if _is_tier_text(c_text):
                            tier_label = c_text
                        else:
                            cleaned_seg = _clean_spec_segment(c_text)
                            if cleaned_seg and cleaned_seg not in specs:
                                specs.append(cleaned_seg)

                    spec_desc = " · ".join(specs)
                    provider = _infer_provider(base_model_id, current_category)

                    # 5. 分类组织与拆分模型项
                    if spec_desc:
                        # 视频/生图等多规格模型：拆分为独立规格行展示
                        full_display_name = f"{base_model_id} ({spec_desc})"
                        spec_model_id = _generate_spec_model_id(base_model_id, spec_desc)
                        item_key = f"{spec_model_id}::{current_category}"

                        item = BailianModelItem(
                            model_id=spec_model_id,
                            display_name=full_display_name,
                            provider=provider,
                            category=current_category,
                            input_price_cny=price_val,
                            output_price_cny=price_val,
                            cache_price_cny=0.0,
                            is_free=(price_val == 0.0),
                            has_tiered_pricing=False,
                            price_tiers=[],
                            price_note=spec_desc
                        )
                        models_map[item_key] = item

                    elif tier_label:
                        # LLM 阶梯分段定价模型 (如千问 0-128k, 128k-256k)：归纳在同一个模型下
                        item_key = f"{base_model_id}::{current_category}"
                        if item_key not in models_map:
                            item = BailianModelItem(
                                model_id=base_model_id,
                                display_name=base_model_id,
                                provider=provider,
                                category=current_category,
                                input_price_cny=price_val,
                                output_price_cny=price_val,
                                cache_price_cny=0.0,
                                is_free=(price_val == 0.0),
                                has_tiered_pricing=True,
                                price_tiers=[],
                                price_note=""
                            )
                            item.price_tiers.append(BailianPriceTier(
                                tier_label=tier_label,
                                input_price_cny=price_val,
                                output_price_cny=price_val,
                                cache_price_cny=0.0
                            ))
                            models_map[item_key] = item
                        else:
                            existing = models_map[item_key]
                            existing_labels = {t.tier_label for t in existing.price_tiers}
                            if tier_label not in existing_labels:
                                existing.has_tiered_pricing = True
                                existing.price_tiers.append(BailianPriceTier(
                                    tier_label=tier_label,
                                    input_price_cny=price_val,
                                    output_price_cny=price_val,
                                    cache_price_cny=0.0
                                ))
                    else:
                        # 普通无规格模型
                        item_key = f"{base_model_id}::{current_category}"
                        item = BailianModelItem(
                            model_id=base_model_id,
                            display_name=base_model_id,
                            provider=provider,
                            category=current_category,
                            input_price_cny=price_val,
                            output_price_cny=price_val,
                            cache_price_cny=0.0,
                            is_free=(price_val == 0.0),
                            has_tiered_pricing=False,
                            price_tiers=[],
                            price_note=""
                        )
                        models_map[item_key] = item

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
                    | (SiteModelPricing.model_id.like("%参考视频%"))
                    | (SiteModelPricing.model_id.like("%声视频%"))
                )
                await session.execute(stmt_del_p)
                stmt_del_m = delete(ModelMetadata).where(
                    (ModelMetadata.model_id.like("%<%"))
                    | (ModelMetadata.model_id.like("%≤%"))
                    | (ModelMetadata.model_id.like("%Token%"))
                    | (ModelMetadata.model_id.like("%参考视频%"))
                    | (ModelMetadata.model_id.like("%声视频%"))
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
