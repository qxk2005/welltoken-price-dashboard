"""
官方大模型定价表 (Official Pricing) API 路由
提供官方价格查询、汇率动态折算、用户自定义备注/标签更新、触发实时抓取以及 HTML 快照对账查阅。
"""
import os
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, update

from backend.app.database import get_db
from backend.app.models.token_price import OfficialModelPrice, OfficialSnapshot, SystemSetting
from backend.app.schemas.token_schema import (
    OfficialModelPriceSchema,
    OfficialModelPriceUpdateNotes,
    OfficialSnapshotSchema,
    OfficialScrapeRequest,
    OfficialScrapeResponse,
)
from backend.app.services.official_scraper_service import official_scraper_service, OFFICIAL_TARGETS
from backend.app.services.exchange_rate import exchange_rate_service

router = APIRouter(prefix="/official-pricing", tags=["Official Pricing"])


@router.get("/list", response_model=Dict[str, Any])
async def get_official_prices(
    provider: Optional[str] = Query(None, description="按厂商筛选，如 openai, deepseek 等"),
    series: Optional[str] = Query(None, description="按模型系列筛选，如 gpt-5.6, claude-3-5 等"),
    search: Optional[str] = Query(None, description="模型名称或备注关键字搜索"),
    billing_mode: Optional[str] = Query(None, description="计费模式筛选"),
    db: AsyncSession = Depends(get_db)
):
    """获取官方价格全量列表（支持多维筛选与汇率自动折算）"""
    rate = exchange_rate_service.current_rate
    if not rate or rate <= 0:
        rate = 7.30

    query = select(OfficialModelPrice).where(OfficialModelPrice.is_active == True)

    if provider:
        query = query.where(OfficialModelPrice.provider == provider)
    if series:
        query = query.where(OfficialModelPrice.series == series)
    if billing_mode:
        query = query.where(OfficialModelPrice.billing_mode == billing_mode)
    if search:
        kw = f"%{search.strip()}%"
        query = query.where(
            or_(
                OfficialModelPrice.model_name.ilike(kw),
                OfficialModelPrice.remarks.ilike(kw),
                OfficialModelPrice.custom_notes.ilike(kw),
                OfficialModelPrice.user_tags.ilike(kw),
                OfficialModelPrice.provider_name.ilike(kw)
            )
        )

    query = query.order_by(OfficialModelPrice.provider.asc(), OfficialModelPrice.series.asc(), OfficialModelPrice.model_name.asc())
    result = await db.execute(query)
    records = result.scalars().all()

    # 提取唯一的厂商列表与系列列表供前端筛选框使用
    providers_res = await db.execute(
        select(OfficialModelPrice.provider, OfficialModelPrice.provider_name)
        .where(OfficialModelPrice.is_active == True)
        .distinct()
    )
    providers_list = [{"code": r[0], "name": r[1]} for r in providers_res.all()]

    series_res = await db.execute(
        select(OfficialModelPrice.series, OfficialModelPrice.provider)
        .where(OfficialModelPrice.is_active == True)
        .distinct()
    )
    series_list = [{"series": r[0], "provider": r[1]} for r in series_res.all() if r[0]]

    # 封装并计算双币种（CNY ¥ 与 USD $）
    items = []
    for m in records:
        item_dict = {
            "id": m.id,
            "provider": m.provider,
            "provider_name": m.provider_name,
            "series": m.series or "other",
            "model_name": m.model_name,
            "raw_model_id": m.raw_model_id or "",
            "billing_mode": m.billing_mode or "Standard",
            "tier_range": m.tier_range or "无阶梯",
            "currency": m.currency,
            "input_price": m.input_price,
            "output_price": m.output_price,
            "cache_read_price": m.cache_read_price,
            "cache_write_price": m.cache_write_price,
            "remarks": m.remarks or "",
            "custom_notes": m.custom_notes or "",
            "user_tags": m.user_tags or "",
            "price_date": m.price_date or "",
            "source_page_url": m.source_page_url or "",
            "source_anchor": m.source_anchor or "",
            "snapshot_id": m.snapshot_id,
            "is_active": m.is_active,
            "created_at": m.created_at,
            "updated_at": m.updated_at,
        }
        # 汇率换算逻辑
        if m.currency == "USD":
            item_dict["converted_input_usd"] = m.input_price
            item_dict["converted_output_usd"] = m.output_price
            item_dict["converted_cache_read_usd"] = m.cache_read_price
            item_dict["converted_cache_write_usd"] = m.cache_write_price
            item_dict["converted_input_cny"] = round(m.input_price * rate, 4)
            item_dict["converted_output_cny"] = round(m.output_price * rate, 4)
            item_dict["converted_cache_read_cny"] = round(m.cache_read_price * rate, 4)
            item_dict["converted_cache_write_cny"] = round(m.cache_write_price * rate, 4)
        else:
            item_dict["converted_input_cny"] = m.input_price
            item_dict["converted_output_cny"] = m.output_price
            item_dict["converted_cache_read_cny"] = m.cache_read_price
            item_dict["converted_cache_write_cny"] = m.cache_write_price
            item_dict["converted_input_usd"] = round(m.input_price / rate, 4) if rate > 0 else 0.0
            item_dict["converted_output_usd"] = round(m.output_price / rate, 4) if rate > 0 else 0.0
            item_dict["converted_cache_read_usd"] = round(m.cache_read_price / rate, 4) if rate > 0 else 0.0
            item_dict["converted_cache_write_usd"] = round(m.cache_write_price / rate, 4) if rate > 0 else 0.0

        items.append(item_dict)

    return {
        "status": "success",
        "total": len(items),
        "models": items,
        "providers": providers_list,
        "series": series_list,
        "usd_to_cny_rate": rate,
    }


@router.patch("/model/{model_id}/notes")
async def update_model_notes(
    model_id: int,
    payload: OfficialModelPriceUpdateNotes,
    db: AsyncSession = Depends(get_db)
):
    """更新用户自定义备注与标签"""
    stmt = select(OfficialModelPrice).where(OfficialModelPrice.id == model_id)
    res = await db.execute(stmt)
    model = res.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="未找到该模型记录")

    if payload.custom_notes is not None:
        model.custom_notes = payload.custom_notes.strip()
    if payload.user_tags is not None:
        model.user_tags = payload.user_tags.strip()

    await db.commit()
    await db.refresh(model)
    return {
        "status": "success",
        "id": model.id,
        "custom_notes": model.custom_notes,
        "user_tags": model.user_tags,
    }


@router.post("/scrape", response_model=OfficialScrapeResponse)
async def trigger_scrape(
    payload: OfficialScrapeRequest,
):
    """触发抓取（支持指定厂商或全部厂商，支持传入自定义代理）"""
    import time
    start_t = time.time()
    target = payload.provider

    if not target or target == "all":
        count, keys, err = await official_scraper_service.scrape_all(proxy=payload.proxy)
        duration = round((time.time() - start_t) * 1000, 2)
        return OfficialScrapeResponse(
            status="error" if err and count == 0 else "success",
            total_models=count,
            providers_scraped=keys,
            duration_ms=duration,
            error_message=err or ""
        )
    else:
        count, err = await official_scraper_service.scrape_target(target, proxy=payload.proxy)
        duration = round((time.time() - start_t) * 1000, 2)
        return OfficialScrapeResponse(
            status="error" if err else "success",
            total_models=count,
            providers_scraped=[target] if not err else [],
            duration_ms=duration,
            error_message=err or ""
        )


@router.get("/snapshots")
async def list_snapshots(db: AsyncSession = Depends(get_db)):
    """获取所有已留存的官网快照"""
    query = select(OfficialSnapshot).order_by(OfficialSnapshot.captured_at.desc())
    res = await db.execute(query)
    snapshots = res.scalars().all()
    return [
        {
            "id": s.id,
            "provider": s.provider,
            "source_url": s.source_url,
            "page_title": s.page_title,
            "local_file_path": s.local_file_path,
            "file_size_bytes": s.file_size_bytes,
            "models_count": s.models_count,
            "captured_at": s.captured_at.strftime("%Y-%m-%d %H:%M:%S") if s.captured_at else "",
        }
        for s in snapshots
    ]


@router.get("/snapshots/{snapshot_id}/view")
async def view_snapshot_html(
    snapshot_id: int,
    highlight: Optional[str] = Query(None, description="需要高亮并自动滚动的目标模型关键字"),
    db: AsyncSession = Depends(get_db)
):
    """获取快照 HTML 内容供内置抽屉渲染对账（注入 Base 域、移除冲突 Script、自动平滑滚动高亮目标行）"""
    from bs4 import BeautifulSoup
    query = select(OfficialSnapshot).where(OfficialSnapshot.id == snapshot_id)
    res = await db.execute(query)
    snapshot = res.scalar_one_or_none()
    if not snapshot:
        raise HTTPException(status_code=404, detail="未找到该快照")

    abs_path = os.path.join(os.getcwd(), snapshot.local_file_path)
    if not os.path.exists(abs_path):
        raise HTTPException(status_code=404, detail="快照文件在本地磁盘不存在")

    with open(abs_path, "r", encoding="utf-8") as f:
        raw_html = f.read()

    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. 移除所有可能会在本地环境中报错导致整页白屏的 <script> 标签
    for s in soup.find_all("script"):
        s.decompose()

    # 2. 注入 <base href="{snapshot.source_url}"> 使得远程 CSS/图片/字体正常加载
    if soup.head:
        base_tag = soup.new_tag("base", href=snapshot.source_url)
        soup.head.insert(0, base_tag)

    # 3. 注入高亮样式与平滑滚动定位脚本
    import json
    target_kw = (highlight or "").strip()
    highlight_code = """
<style>
  @keyframes wpdRowPulse {
    0% {
      box-shadow: 0 0 0 0 rgba(0, 113, 227, 0.7);
      background-color: rgba(254, 240, 138, 0.3) !important;
    }
    50% {
      box-shadow: 0 0 0 6px rgba(0, 113, 227, 0.35);
      background-color: rgba(254, 240, 138, 0.65) !important;
    }
    100% {
      box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.85);
      background-color: rgba(254, 240, 138, 0.4) !important;
    }
  }
  @keyframes wpdCellPulse {
    0% {
      box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.9), inset 0 0 10px rgba(245, 158, 11, 0.35);
      background-color: rgba(254, 240, 138, 0.95) !important;
      transform: scale(1);
    }
    50% {
      box-shadow: 0 0 0 7px rgba(245, 158, 11, 0.45), inset 0 0 16px rgba(245, 158, 11, 0.6);
      background-color: rgba(253, 224, 71, 1) !important;
      transform: scale(1.05);
    }
    100% {
      box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.9), inset 0 0 10px rgba(245, 158, 11, 0.35);
      background-color: rgba(254, 240, 138, 0.95) !important;
      transform: scale(1);
    }
  }
  .wpd-highlight-row {
    animation: wpdRowPulse 1.6s ease-in-out infinite alternate !important;
    border-radius: 4px !important;
    position: relative !important;
    z-index: 98 !important;
    outline: 2px solid #0071E3 !important;
  }
  .wpd-highlight-cell {
    animation: wpdCellPulse 1.5s ease-in-out infinite alternate !important;
    outline: 2px solid #D97706 !important;
    border-radius: 4px !important;
    font-weight: 800 !important;
    color: #92400E !important;
    position: relative !important;
    z-index: 100 !important;
  }
  .wpd-top-indicator {
    position: fixed;
    top: 14px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 9999999;
    background: rgba(29, 29, 31, 0.92);
    color: #FFFFFF;
    padding: 8px 20px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.28);
    display: flex;
    align-items: center;
    gap: 8px;
    border: 1px solid rgba(255,255,255,0.25);
    cursor: pointer;
    user-select: none;
    transition: all 0.2s ease;
  }
  .wpd-top-indicator:hover {
    transform: translateX(-50%) scale(1.04);
    background: #0071E3;
  }
</style>
<script>
  (function() {
    var kw = __TARGET_KW__;
    function locateAndHighlight() {
      if (!kw) return;

      function norm(s) {
        return (s || '').toLowerCase().replace(/[\\s\\n\\r\\t]+/g, ' ').replace(/[，。；;,;]/g, ' ').trim();
      }

      var normKw = norm(kw);
      var cleanKw = norm(kw.split(' [')[0].split(' (')[0]);
      var coreName = cleanKw.split(' ')[0].trim();
      var isPeak = kw.indexOf('高峰') !== -1;
      var isIdle = kw.indexOf('闲时') !== -1 || kw.indexOf('空闲') !== -1;
      var isBatch = kw.indexOf('Batch') !== -1;
      var isFlex = kw.indexOf('Flex') !== -1;
      var isFast = kw.indexOf('Fast') !== -1 || kw.indexOf('Priority') !== -1;
      var isLong = kw.indexOf('272k+') !== -1 || kw.indexOf('Long') !== -1 || kw.indexOf('128k+') !== -1;
      var targetScrollEl = null;

      // ================= 步骤 0: 智能 Tab 选项卡模式切换 (如 OpenAI / Astro Content Switcher) =================
      var targetMode = isBatch ? 'Batch' : (isFlex ? 'Flex' : (isFast ? 'Fast mode' : 'Standard'));
      var targetTabIndex = isBatch ? 1 : (isFlex ? 2 : (isFast ? 3 : 0));

      var switchers = document.querySelectorAll('.content-switcher-selector, [role="tablist"]');
      var containers = document.querySelectorAll('.content-switcher-panes');

      // 切换 Pane 显示隐藏
      for (var c = 0; c < containers.length; c++) {
        var panes = containers[c].children;
        for (var p = 0; p < panes.length; p++) {
          if (p === targetTabIndex) {
            panes[p].removeAttribute('hidden');
            panes[p].style.display = 'block';
          } else {
            panes[p].setAttribute('hidden', 'true');
            panes[p].style.display = 'none';
          }
        }
      }

      // 切换 Tab 按钮高亮与状态
      for (var s = 0; s < switchers.length; s++) {
        var btns = switchers[s].querySelectorAll('button, a, [role="tab"]');
        for (var b = 0; b < btns.length; b++) {
          var btnText = (btns[b].innerText || btns[b].textContent || '').trim();
          if (btnText === targetMode || (isFast && (btnText === 'Fast mode' || btnText === 'Priority'))) {
            btns[b].style.backgroundColor = '#0071E3';
            btns[b].style.color = '#FFFFFF';
            btns[b].setAttribute('aria-selected', 'true');
          } else {
            btns[b].style.backgroundColor = '';
            btns[b].style.color = '';
            btns[b].setAttribute('aria-selected', 'false');
          }

          // 绑定用户手动点击切换事件
          (function(btnIdx, bEl) {
            bEl.onclick = function() {
              for (var c2 = 0; c2 < containers.length; c2++) {
                var pList = containers[c2].children;
                for (var p2 = 0; p2 < pList.length; p2++) {
                  if (p2 === btnIdx) {
                    pList[p2].removeAttribute('hidden');
                    pList[p2].style.display = 'block';
                  } else {
                    pList[p2].setAttribute('hidden', 'true');
                    pList[p2].style.display = 'none';
                  }
                }
              }
              var allSiblings = bEl.parentElement.querySelectorAll('button, a, [role="tab"]');
              for (var sib = 0; sib < allSiblings.length; sib++) {
                allSiblings[sib].style.backgroundColor = '';
                allSiblings[sib].style.color = '';
              }
              bEl.style.backgroundColor = '#0071E3';
              bEl.style.color = '#FFFFFF';
            };
          })(b, btns[b]);
        }
      }
      // ================= 步骤 0.1: Google Devsite Selector 模式切换 (针对 Gemini 模型) =================
      var targetGeminiTab = isBatch ? '批量' : (isFlex ? 'flex' : (isFast ? '优先级' : '标准'));
      var devsiteSelectors = document.querySelectorAll('devsite-selector');
      if (devsiteSelectors.length > 0) {
        for (var ds = 0; ds < devsiteSelectors.length; ds++) {
          var sel = devsiteSelectors[ds];
          var cur = sel;
          var matchSel = false;
          while (cur && cur !== document.body) {
            var prevSib = cur.previousElementSibling;
            while (prevSib) {
              var pText = norm(prevSib.innerText);
              if (pText.indexOf(cleanKw) !== -1 || (coreName.length >= 4 && pText.indexOf(coreName) !== -1)) {
                matchSel = true;
                break;
              }
              prevSib = prevSib.previousElementSibling;
            }
            if (matchSel) break;
            cur = cur.parentElement;
          }

          if (matchSel) {
            var secList = sel.querySelectorAll('section');
            var activeSec = null;
            for (var si = 0; si < secList.length; si++) {
              var sId = (secList[si].id || '').toLowerCase();
              if (sId.indexOf(targetGeminiTab.toLowerCase()) !== -1) {
                secList[si].style.display = 'block';
                secList[si].removeAttribute('hidden');
                activeSec = secList[si];
              } else {
                secList[si].style.display = 'none';
              }
            }

            var dsTabs = sel.querySelectorAll('tab, button, [role="tab"]');
            for (var dt = 0; dt < dsTabs.length; dt++) {
              if (norm(dsTabs[dt].innerText).indexOf(targetGeminiTab.toLowerCase()) !== -1) {
                dsTabs[dt].style.backgroundColor = '#0071E3';
                dsTabs[dt].style.color = '#FFFFFF';
              } else {
                dsTabs[dt].style.backgroundColor = '';
                dsTabs[dt].style.color = '';
              }
            }

            if (activeSec) {
              var tRows = activeSec.querySelectorAll('tr');
              for (var tr = 0; tr < tRows.length; tr++) {
                var rowTxt = norm(tRows[tr].innerText);
                if (rowTxt.indexOf('输入价格') !== -1 || rowTxt.indexOf('输出价格') !== -1) {
                  tRows[tr].classList.add('wpd-highlight-row');
                  var dCells = tRows[tr].querySelectorAll('td');
                  for (var dc = 0; dc < dCells.length; dc++) {
                    var cellT = dCells[dc].innerText;
                    if (/\\d+(?:\\.\\d+)?\\s*(?:美元|元|￥|¥|\\$)/.test(cellT) || /\\$\\s*\\d+/.test(cellT)) {
                      dCells[dc].classList.add('wpd-highlight-cell');
                    }
                  }
                  if (!targetScrollEl) targetScrollEl = tRows[tr];
                }
              }
            }
            break;
          }
        }
      }

      var tables = document.querySelectorAll('table');

      // ================= 场景 1: 列式模型表格定位 (如 DeepSeek) =================
      if (!targetScrollEl) {
        for (var t = 0; t < tables.length; t++) {
        var table = tables[t];
        var rows = table.querySelectorAll('tr');
        if (!rows || rows.length < 2) continue;

        var headerCells = rows[0].querySelectorAll('td, th');
        var modelCol = -1;
        for (var c = 1; c < headerCells.length; c++) {
          if (norm(headerCells[c].innerText).indexOf(coreName) !== -1) {
            modelCol = c;
            break;
          }
        }

        if (modelCol === -1 && rows.length > 1) {
          var h2Cells = rows[1].querySelectorAll('td, th');
          for (var c = 1; c < h2Cells.length; c++) {
            if (norm(h2Cells[c].innerText).indexOf(coreName) !== -1) {
              modelCol = c;
              headerCells = h2Cells;
              break;
            }
          }
        }

        if (modelCol !== -1) {
          var offsetFromEnd = headerCells.length - 1 - modelCol;

          for (var r = 0; r < rows.length; r++) {
            var rText = norm(rows[r].innerText);
            var isTargetPriceRow = false;
            if (isPeak && rText.indexOf('高峰') !== -1) isTargetPriceRow = true;
            else if (isIdle && (rText.indexOf('空闲') !== -1 || rText.indexOf('闲时') !== -1)) isTargetPriceRow = true;

            if (isTargetPriceRow) {
              var cells = rows[r].querySelectorAll('td, th');
              if (cells.length > offsetFromEnd) {
                var targetCell = cells[cells.length - 1 - offsetFromEnd];
                if (targetCell) {
                  rows[r].classList.add('wpd-highlight-row');
                  targetCell.classList.add('wpd-highlight-cell');
                  if (!targetScrollEl || rText.indexOf('未命中') !== -1 || rText.indexOf('输入') !== -1) {
                    targetScrollEl = targetCell;
                  }
                }
              }
            }
          }

          if (targetScrollEl) break;
        }
      }
    }

      // ================= 场景 2: 行式模型表格定位 (如 Claude、OpenAI、阿里百炼、智谱等) =================
      if (!targetScrollEl) {
        // 构建候选模型关键字列表，严禁单一取第 0 个单词截断导致变成厂商名 (如将 'claude opus 4.8' 变成 'claude')
        var modelCandidates = [cleanKw];
        var vendorPrefixes = ['claude ', 'openai ', 'alibaba ', 'zhipu ', 'deepseek ', 'baichuan ', 'minimax ', 'moonshot ', 'google '];
        for (var pfx = 0; pfx < vendorPrefixes.length; pfx++) {
          if (cleanKw.startsWith(vendorPrefixes[pfx])) {
            modelCandidates.push(cleanKw.slice(vendorPrefixes[pfx].length).trim());
          }
        }

        // 识别是否有独立 Batch 专属表格 (如 Anthropic 官方文档将 Batch 单独建表)
        var batchTables = [];
        var standardTables = [];
        for (var t = 0; t < tables.length; t++) {
          var tNorm = norm(tables[t].innerText);
          if (tNorm.indexOf('batch input') !== -1 || tNorm.indexOf('batch output') !== -1 || tNorm.indexOf('batch api') !== -1) {
            batchTables.push(tables[t]);
          } else {
            standardTables.push(tables[t]);
          }
        }

        var searchRoots = [];
        if (isBatch && batchTables.length > 0) {
          searchRoots = batchTables;
        } else if (!isBatch && batchTables.length > 0) {
          searchRoots = standardTables;
        } else if (containers.length > 0 && containers[0].children[targetTabIndex]) {
          searchRoots.push(containers[0].children[targetTabIndex]);
        } else {
          searchRoots.push(document);
        }

        function isWordMatch(text, term) {
          if (!text || !term) return false;
          var t = text.toLowerCase();
          var q = term.toLowerCase();
          var idx = 0;
          while ((idx = t.indexOf(q, idx)) !== -1) {
            var leftOk = (idx === 0) || !/[a-zA-Z0-9]/.test(t[idx - 1]);
            var endIdx = idx + q.length;
            var rightChar = endIdx < t.length ? t[endIdx] : '';
            var rightOk = (endIdx >= t.length) || !/[a-zA-Z0-9._\\-]/.test(rightChar);
            if (leftOk && rightOk) {
              return true;
            }
            idx += 1;
          }
          return false;
        }

        var matchedRow = null;

        for (var sr = 0; sr < searchRoots.length; sr++) {
          var rows = searchRoots[sr].querySelectorAll('tr');

          for (var i = 0; i < rows.length; i++) {
            var rText = norm(rows[i].innerText);

            // 严格单词边界匹配完整候选模型名 (防止 'fable 5' 误匹配 'fable 5.1' 或 'gpt-4' 误匹配 'gpt-4.5')
            var isModelMatch = modelCandidates.some(function(cand) {
              if (!cand || cand.length < 2) return false;
              return isWordMatch(rText, cand);
            });

            if (isModelMatch) {
              // 排除表头行 (仅当包含 'model' 且不包含具体价格数字时视为表头)
              var isHeaderRow = rText.indexOf('model') !== -1 && !/\\d+(?:\\.\\d+)?/.test(rText);
              if (!isHeaderRow) {
                // 若有阶梯参数，结合阶梯判定
                if (kw.indexOf('[') !== -1) {
                  var tierPart = kw.split('[')[1].split(')')[0].toLowerCase();
                  var tierNums = tierPart.match(/\\d+[kkmg]?/g) || [];
                  var hasTier = tierNums.length === 0 || tierNums.some(function(n) { return rText.indexOf(n) !== -1; });
                  if (hasTier) {
                    matchedRow = rows[i];
                    break;
                  }
                } else {
                  matchedRow = rows[i];
                  break;
                }
              }
            }
          }
          if (matchedRow) break;
        }

        if (matchedRow) {
          matchedRow.classList.add('wpd-highlight-row');
          var cells = matchedRow.querySelectorAll('td');

          // 如果是双阶梯表格 (如 OpenAI Short context 与 Long context 双区域共 8 列)
          if (cells.length >= 8) {
            var startIdx = isLong ? (cells.length - 4) : (cells.length - 8);
            var endIdx = isLong ? cells.length : (cells.length - 4);
            for (var ci = startIdx; ci < endIdx; ci++) {
              if (cells[ci]) {
                cells[ci].classList.add('wpd-highlight-cell');
              }
            }
            targetScrollEl = cells[startIdx] || matchedRow;
          } else {
            // 普通单阶梯行：高亮所有带货币符号或数值的价格单元格
            for (var c = 0; c < cells.length; c++) {
              var cText = cells[c].innerText;
              if (/\\d+(?:\\.\\d+)?\\s*(?:元|￥|¥|\\$|\\/)/.test(cText) || /\\$\\s*\\d+/.test(cText)) {
                cells[c].classList.add('wpd-highlight-cell');
              }
            }
            targetScrollEl = matchedRow;
          }
        }
      }

      // 执行平滑居中滚动与顶部提示条展示
      if (targetScrollEl) {
        targetScrollEl.scrollIntoView({ behavior: 'smooth', block: 'center' });

        var bar = document.createElement('div');
        bar.className = 'wpd-top-indicator';
        bar.innerHTML = '<span>🎯 已自动定位到模型: ' + kw + '</span><span style="opacity: 0.6; font-size: 10px;">(点击重新居中)</span>';
        bar.onclick = function() {
          targetScrollEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        };
        document.body.appendChild(bar);
      }
    }
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', locateAndHighlight);
    } else {
      setTimeout(locateAndHighlight, 300);
    }
  })();
</script>
""".replace("__TARGET_KW__", json.dumps(target_kw))
    if soup.body:
        soup.body.append(BeautifulSoup(highlight_code, "html.parser"))

    return HTMLResponse(content=str(soup))

