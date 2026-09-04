"""
官网第一档去阶梯化标准基准模型服务与智能模糊匹配引擎
1. 提取官方 576 款定价库中 Standard 模式的【第一档去阶梯化】纯净模型清单
2. 实现渠道模型与官网标准模型的自动多维模糊匹配打分
3. 精确计算相对官网第一档基准价的真实折扣（输入/输出/综合折扣，跨币种实时换算）
"""
import re
import difflib
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.models.token_price import OfficialModelPrice, ChannelModelMapping, SiteModelPricing
from backend.app.services.exchange_rate import exchange_rate_service


class OfficialBenchmarkService:
    """官网基准模型与模糊匹配算法核心服务"""

    def clean_benchmark_model_name(self, raw_name: str) -> str:
        """
        去除模型名中的阶梯信息、括号标注与多余空白，保留纯净模型名称
        如: "Qwen3 Max [0, 280k)" -> "Qwen3 Max"
            "Claude 3.5 Sonnet (Batch 模式)" -> "Claude 3.5 Sonnet"
            "DeepSeek-V3 [0, 64k)" -> "DeepSeek-V3"
            "GLM-5 输入长度 [0, 32)" -> "GLM-5"
        """
        if not raw_name:
            return ""
        name = raw_name.strip()
        # 去除方括号阶梯区间与时段标注，如 [0, 272k), [272k+), [高峰时段], [闲时优惠]
        name = re.sub(r"\s*\[\s*[^\]]+[\]\)]", "", name)
        # 去除“输入长度”、“输出长度”、“上下文长度”等阶梯前置引导词
        name = re.sub(r"\s*(?:输入长度|输出长度|上下文长度|长度|输入|输出)\s*$", "", name)
        # 去除圆括号模式标注如 (Batch 模式), (Flex 模式), (批处理)
        name = re.sub(r"\s*\((?:Batch|Flex|批处理|弹性|标准|Standard)[^)]*\)", "", name, flags=re.IGNORECASE)
        # 清理多余空格
        name = re.sub(r"\s+", " ", name).strip()
        return name

    def is_tier_one(self, tier_range: str, billing_mode: str) -> bool:
        """判断是否为第一档基础阶梯"""
        b_mode = (billing_mode or "").lower()
        if "batch" in b_mode or "flex" in b_mode:
            return False
        
        t_range = (tier_range or "").strip()
        if not t_range or t_range == "无阶梯" or "免费" in t_range or "第一档" in t_range:
            return True
        
        # 匹配区间起始为 0 的阶梯，例如 [0, 272k), [0, 100k), 输入长度 [0, 32)
        if re.search(r"\[\s*0\b", t_range):
            return True
        return False

    async def get_benchmark_models(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """
        从 official_model_prices 获取所有第一档去阶梯化的官方标准模型
        """
        rate = exchange_rate_service.current_rate
        if not rate or rate <= 0:
            rate = 7.30

        # 查询所有有效的官方定价记录，排除 Batch 等非 Standard
        stmt = (
            select(OfficialModelPrice)
            .where(OfficialModelPrice.is_active == True)
            .order_by(OfficialModelPrice.provider.asc(), OfficialModelPrice.id.asc())
        )
        res = await db.execute(stmt)
        all_prices = res.scalars().all()

        benchmarks: Dict[str, Dict[str, Any]] = {}

        for p in all_prices:
            # 必须优先匹配第一档阶梯
            if not self.is_tier_one(p.tier_range, p.billing_mode):
                continue

            pure_name = self.clean_benchmark_model_name(p.model_name)
            raw_id = (p.raw_model_id or pure_name).strip()
            # 唯一 key: 厂商 + 纯净标识
            bench_key = f"{p.provider}::{raw_id.lower()}"

            # 若已存在且已有记录更优先，跳过
            if bench_key in benchmarks:
                continue

            # 计算双币种折算单价
            curr = (p.currency or "USD").upper()
            in_p = float(p.input_price or 0.0)
            out_p = float(p.output_price or 0.0)
            cache_p = float(p.cache_read_price or 0.0)

            if curr == "CNY":
                in_cny = in_p
                out_cny = out_p
                cache_cny = cache_p
                in_usd = round(in_p / rate, 4) if rate > 0 else 0.0
                out_usd = round(out_p / rate, 4) if rate > 0 else 0.0
                cache_usd = round(cache_p / rate, 4) if rate > 0 else 0.0
            else:
                in_usd = in_p
                out_usd = out_p
                cache_usd = cache_p
                in_cny = round(in_p * rate, 4)
                out_cny = round(out_p * rate, 4)
                cache_cny = round(cache_p * rate, 4)

            benchmarks[bench_key] = {
                "id": p.id,
                "model_id": raw_id,
                "name": pure_name,
                "provider": p.provider,
                "provider_name": p.provider_name,
                "series": p.series or "other",
                "clean_name": pure_name,
                "raw_model_id": raw_id,
                "currency": curr,
                "official_input_price": in_p,
                "official_output_price": out_p,
                "official_cache_price": cache_p,
                "converted_input_usd": in_usd,
                "converted_output_usd": out_usd,
                "converted_cache_usd": cache_usd,
                "converted_input_cny": in_cny,
                "converted_output_cny": out_cny,
                "converted_cache_cny": cache_cny,
                "snapshot_id": p.snapshot_id,
                "tier_range": p.tier_range or "第一档",
            }

        return list(benchmarks.values())

    def calculate_discount(
        self,
        supplier_input_usd: float,
        supplier_output_usd: float,
        bench_input_usd: float,
        bench_output_usd: float
    ) -> Dict[str, Any]:
        """
        计算供应商折算价相对于官方第一档基准价的真实折扣 (折算比率)
        例如: 0.35 表示 3.5 折; 1.20 表示溢价 +20%
        """
        in_disc = None
        out_disc = None

        if bench_input_usd > 0:
            in_disc = round(supplier_input_usd / bench_input_usd, 3)
        elif supplier_input_usd == 0:
            in_disc = 0.0

        if bench_output_usd > 0:
            out_disc = round(supplier_output_usd / bench_output_usd, 3)
        elif supplier_output_usd == 0:
            out_disc = 0.0

        # 加权综合折扣 (输入 2 : 输出 1)
        if in_disc is not None and out_disc is not None:
            comp_disc = round((in_disc * 2 + out_disc) / 3, 3)
        elif in_disc is not None:
            comp_disc = in_disc
        elif out_disc is not None:
            comp_disc = out_disc
        else:
            comp_disc = None

        return {
            "input_discount": in_disc,
            "output_discount": out_disc,
            "composite_discount": comp_disc,
        }

    def _normalize_name(self, name: str) -> str:
        """标准化名称以便于比较 (深度纯化中文修饰词并兼容 Kimi 等代号)"""
        if not name:
            return ""
        s = name.lower().strip()
        is_kimi = bool(re.match(r"^(?:kimi|moonshotai|moonshot)[/\-_:]", s))

        # 1. 去除常见厂商前缀 (斜杠、破折号、下划线、冒号)
        s = re.sub(r"^(?:openai|anthropic|google|alibaba|deepseek|zhipu|kimi|moonshotai|moonshot|minimax|siliconflow|aliyun|xiaomi|stepfun)[/\-_:]", "", s)

        # 2. 剥离常见中文通用修饰词
        noise_cn = r"(?:通用模型|旗舰模型|大模型|模型|旗舰|通用|全血版|标准版|专业版|高性价比|长文本|文本转语音|语音识别)"
        s = re.sub(noise_cn, "", s)

        # 3. 剥离常见英文修饰词
        s = re.sub(r"\b(?:code\s*coding|code|coding|model|chat|instruct|preview|latest|version)\b", "", s)

        # 4. 去除特殊模式后缀 (如 -vip, -fast, -free)
        s = re.sub(r"-(?:vip|fast|latest|free|pro|chat)$", "", s)

        # 5. Kimi 代号特别折叠兼容: 若以纯数字开头(如 '2.6' 或 '3')，统一补齐 'k' 与官方 (k2.6/k3) 绝对对齐
        s = s.strip()
        if is_kimi and re.match(r"^\d+(\.\d+)?", s):
            s = "k" + s

        # 6. 去除分隔符与空白
        s = re.sub(r"[_\-:\.\s]", "", s)
        return s

    def fuzzy_match_one(
        self,
        candidate_name: str,
        benchmarks: List[Dict[str, Any]],
        threshold: float = 0.65
    ) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        对单个渠道模型名称执行多维智能模糊匹配
        返回 (最佳匹配官网模型, 匹配置信度得分 0.0~1.0)
        """
        if not candidate_name:
            return None, 0.0

        cand_raw = candidate_name.strip().lower()
        cand_norm = self._normalize_name(candidate_name)

        best_match = None
        best_score = 0.0

        for b in benchmarks:
            b_raw = b["raw_model_id"].lower()
            b_clean = b["clean_name"].lower()
            b_norm = self._normalize_name(b_raw)
            b_clean_norm = self._normalize_name(b_clean)

            # 1. 绝对精确匹配 (原始 ID 或去阶梯名)
            if cand_raw == b_raw or cand_raw == b_clean:
                return b, 1.0

            # 2. 归一化后完全相等
            if cand_norm == b_norm or cand_norm == b_clean_norm:
                return b, 0.95

            # 3. 包含匹配 (如 cand 包含 b_norm 且长度差异较小)
            if b_norm and b_norm in cand_norm:
                ratio = len(b_norm) / len(cand_norm)
                score = 0.85 * ratio
                if score > best_score:
                    best_score = score
                    best_match = b
                continue

            if cand_norm and cand_norm in b_norm:
                ratio = len(cand_norm) / len(b_norm)
                score = 0.82 * ratio
                if score > best_score:
                    best_score = score
                    best_match = b
                continue

            # 4. Difflib 序列相似度
            sim1 = difflib.SequenceMatcher(None, cand_norm, b_norm).ratio()
            sim2 = difflib.SequenceMatcher(None, cand_raw, b_raw).ratio()
            sim = max(sim1, sim2)

            if sim > best_score:
                best_score = sim
                best_match = b

        if best_score >= threshold:
            return best_match, round(best_score, 2)
        return None, round(best_score, 2)

    async def match_channel_models(
        self,
        channel_id: int,
        channel_models: List[Dict[str, Any]],
        db: AsyncSession
    ) -> List[Dict[str, Any]]:
        """
        对指定渠道下的所有模型执行批量自动匹配与真实折扣测算
        """
        benchmarks = await self.get_benchmark_models(db)
        bench_id_map = {b["id"]: b for b in benchmarks}

        # 查询该渠道已存在的映射记录
        existing_mappings_stmt = select(ChannelModelMapping).where(ChannelModelMapping.site_id == channel_id)
        res_m = await db.execute(existing_mappings_stmt)
        existing_mappings = {m.channel_model_name: m for m in res_m.scalars().all()}

        results = []

        for cm in channel_models:
            model_name = cm.get("site_model_name") or cm.get("model_id") or ""
            input_usd = float(cm.get("calculated_input_usd") or 0.0)
            output_usd = float(cm.get("calculated_output_usd") or 0.0)
            group_name = cm.get("group_name") or ""

            matched_bench = None
            score = 0.0
            is_auto_matched = False

            # 优先看数据库中是否已有映射
            if model_name in existing_mappings and existing_mappings[model_name].official_model_id:
                mapped_id = existing_mappings[model_name].official_model_id
                if mapped_id in bench_id_map:
                    matched_bench = bench_id_map[mapped_id]
                    score = 1.0
                    is_auto_matched = True

            # 若未匹配，执行智能模糊匹配
            if not matched_bench:
                matched_bench, score = self.fuzzy_match_one(model_name, benchmarks)
                if matched_bench and score >= 0.70:
                    is_auto_matched = True

            # 计算真实官方折扣
            discounts = {"input_discount": None, "output_discount": None, "composite_discount": None}
            if matched_bench:
                discounts = self.calculate_discount(
                    input_usd,
                    output_usd,
                    matched_bench["converted_input_usd"],
                    matched_bench["converted_output_usd"]
                )

            results.append({
                "channel_model_id": cm.get("id"),
                "channel_model_name": model_name,
                "group_name": group_name,
                "calculated_input_usd": input_usd,
                "calculated_output_usd": output_usd,
                "is_matched": matched_bench is not None,
                "is_auto_matched": is_auto_matched,
                "match_score": score,
                "official_benchmark": matched_bench,
                "official_model_id": matched_bench["id"] if matched_bench else None,
                "official_model_name": matched_bench["clean_name"] if matched_bench else "",
                "input_discount": discounts["input_discount"],
                "output_discount": discounts["output_discount"],
                "composite_discount": discounts["composite_discount"],
            })

        return results


official_benchmark_service = OfficialBenchmarkService()
