import * as XLSX from 'xlsx'
import type { ComparisonItem, ModelMetadata } from '../types'

/**
 * 格式化导出时间戳：YYYYMMDD_HHmm
 */
function getTimestampString(): string {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const h = String(now.getHours()).padStart(2, '0')
  const min = String(now.getMinutes()).padStart(2, '0')
  return `${y}${m}${d}_${h}${min}`
}

/**
 * 自动计算 Excel 列宽（根据内容最大字符长度）
 */
function autoFitColumnWidths(data: any[][], minWidth = 10, maxWidth = 45): XLSX.ColInfo[] {
  if (!data || data.length === 0) return []
  const colCount = data[0].length
  const colWidths: number[] = new Array(colCount).fill(minWidth)

  for (const row of data) {
    for (let c = 0; c < colCount; c++) {
      const val = row[c]
      if (val !== null && val !== undefined) {
        const str = String(val)
        // 中文字符算 2 宽，ASCII 算 1 宽
        let len = 0
        for (let i = 0; i < str.length; i++) {
          len += str.charCodeAt(i) > 255 ? 2 : 1
        }
        if (len > colWidths[c]) {
          colWidths[c] = len
        }
      }
    }
  }

  return colWidths.map((w) => ({
    wch: Math.min(Math.max(w + 3, minWidth), maxWidth)
  }))
}

/**
 * 通用下载 Workbook 为 .xlsx 文件
 */
function downloadWorkbook(workbook: XLSX.WorkBook, filename: string) {
  XLSX.writeFile(workbook, filename, { compression: true })
}

/**
 * 1. 导出全网比价列表数据为 Excel
 */
export function exportPriceMatrixToExcel(
  items: ComparisonItem[],
  currency: 'USD' | 'CNY' = 'CNY'
) {
  if (!items || items.length === 0) {
    alert('当前筛选条件下无数据可导出')
    return
  }

  const currSymbol = currency === 'USD' ? '$' : '¥'
  const headers = [
    '模型厂商 (Provider)',
    '模型系列 (Series)',
    '模型标准标识 (Model ID)',
    '渠道规格/分段区间 (Tier / Alias)',
    '渠道名称 (Channel)',
    '渠道类型 (Site Type)',
    '结算分组 (Group)',
    `当前输入单价 (${currSymbol}/1M)`,
    `当前输出单价 (${currSymbol}/1M)`,
    `当前缓存单价 (${currSymbol}/1M)`,
    '输入单价 (USD/1M)',
    '输出单价 (USD/1M)',
    '输入单价 (CNY/1M)',
    '输出单价 (CNY/1M)',
    '相对官方基准折扣',
    '模型倍率 (Ratio)',
    '实测 TPS (Tokens/s)',
    '渠道可用状态',
    '实时延迟 (ms)',
    '数据更新时间'
  ]

  const rows: any[][] = [headers]

  for (const item of items) {
    const isUsd = currency === 'USD'
    const curIn = isUsd ? item.calculated_input_usd : item.calculated_input_cny
    const curOut = isUsd ? item.calculated_output_usd : item.calculated_output_cny
    const curCache = isUsd ? item.calculated_cache_usd : (item.calculated_cache_usd * 7.25)

    const discountText = item.discount_percent
      ? `${item.discount_percent > 0 ? '+' : ''}${item.discount_percent}%`
      : '基准价'

    rows.push([
      (item.provider || '').toUpperCase(),
      item.series || '通用系列',
      item.model_id || '',
      item.site_model_name && item.site_model_name !== item.model_id ? item.site_model_name : '默认规格',
      item.site_name || '',
      item.site_type || 'relay',
      item.group_name || 'default',
      curIn !== undefined ? Number(curIn.toFixed(4)) : '-',
      curOut !== undefined ? Number(curOut.toFixed(4)) : '-',
      curCache !== undefined ? Number(curCache.toFixed(4)) : '-',
      item.calculated_input_usd !== undefined ? Number(item.calculated_input_usd.toFixed(4)) : '-',
      item.calculated_output_usd !== undefined ? Number(item.calculated_output_usd.toFixed(4)) : '-',
      item.calculated_input_cny !== undefined ? Number(item.calculated_input_cny.toFixed(4)) : '-',
      item.calculated_output_cny !== undefined ? Number(item.calculated_output_cny.toFixed(4)) : '-',
      discountText,
      item.model_ratio ? `${item.model_ratio}x` : '1.0x',
      item.last_tested_tps || '-',
      item.site_status || 'online',
      item.last_latency_ms || '-',
      item.source_updated_at || item.updated_at || '-'
    ])
  }

  const worksheet = XLSX.utils.aoa_to_sheet(rows)
  worksheet['!cols'] = autoFitColumnWidths(rows)

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '全网比价清单')

  const filename = `WellToken-全网比价-${getTimestampString()}.xlsx`
  downloadWorkbook(workbook, filename)
}

/**
 * 2. 导出供应商详情中的可用模型列表为 Excel
 */
export function exportChannelModelsToExcel(
  channelName: string,
  models: any[],
  currency: 'USD' | 'CNY' = 'CNY'
) {
  if (!models || models.length === 0) {
    alert('当前渠道下无模型数据可导出')
    return
  }

  const currSymbol = currency === 'USD' ? '$' : '¥'
  const headers = [
    '渠道/供应商',
    '模型显示名称',
    '模型标准标识 (Model ID)',
    '规格/分段区间/别名',
    '价格所属分组',
    '上下文窗口 (Context)',
    '最大输出 (Max Output)',
    `输入单价 (${currSymbol}/1M)`,
    `输出单价 (${currSymbol}/1M)`,
    '折算输入单价 (USD)',
    '折算输出单价 (USD)',
    '深度推理',
    '实测 TPS'
  ]

  const rows: any[][] = [headers]

  for (const m of models) {
    const isUsd = currency === 'USD'
    const curIn = isUsd ? (m.calculated_input_usd || 0) : (m.calculated_input_cny || 0)
    const curOut = isUsd ? (m.calculated_output_usd || 0) : (m.calculated_output_cny || 0)

    rows.push([
      channelName,
      m.name || m.model_name || m.model_id,
      m.model_id || '',
      m.site_model_name && m.site_model_name !== m.model_id ? m.site_model_name : '默认规格',
      m.group_name || 'default',
      m.context_window ? Number(m.context_window) : '-',
      m.max_output ? Number(m.max_output) : 8192,
      curIn !== undefined ? Number(curIn.toFixed(4)) : '-',
      curOut !== undefined ? Number(curOut.toFixed(4)) : '-',
      m.calculated_input_usd !== undefined ? Number(m.calculated_input_usd.toFixed(4)) : '-',
      m.calculated_output_usd !== undefined ? Number(m.calculated_output_usd.toFixed(4)) : '-',
      m.is_reasoning || (m.model_id && /r1|o1|o3|reason|deepseek-r/i.test(m.model_id)) ? '支持' : '否',
      m.last_tested_tps || 55
    ])
  }

  const worksheet = XLSX.utils.aoa_to_sheet(rows)
  worksheet['!cols'] = autoFitColumnWidths(rows)

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '渠道可用模型与定价')

  const safeName = channelName.replace(/[\\/:*?"<>|]/g, '_')
  const filename = `WellToken-渠道-${safeName}-${getTimestampString()}.xlsx`
  downloadWorkbook(workbook, filename)
}

/**
 * 3. 导出模型厂商详情中的模型列表为 Excel
 */
export function exportVendorModelsToExcel(
  vendorName: string,
  models: ModelMetadata[] | any[],
  currency: 'USD' | 'CNY' = 'CNY'
) {
  if (!models || models.length === 0) {
    alert('当前厂商下无模型数据可导出')
    return
  }

  const currSymbol = currency === 'USD' ? '$' : '¥'
  const headers = [
    '厂商名称 (Vendor)',
    '模型名称 (Model Name)',
    '模型标准标识 (Model ID)',
    '所属系列 (Series)',
    '上下文窗口 (Context)',
    '最大输出 (Max Output)',
    '官方输入价格 ($/1M)',
    '官方输出价格 ($/1M)',
    `全网最低价 (${currSymbol}/1M)`,
    '接入渠道数 (Channels)',
    '多模态支持 (Modality)',
    '深度推理 (Reasoning)',
    '工具调用 (Tool Call)',
    '结构化输出 (Structured)'
  ]

  const rows: any[][] = [headers]

  for (const m of models) {
    const isUsd = currency === 'USD'
    const lowest = isUsd ? (m.lowest_price_usd || 0) : ((m.lowest_price_usd || 0) * 7.25)

    rows.push([
      vendorName.toUpperCase(),
      m.name || m.model_name || m.model_id,
      m.model_id || '',
      m.series || '通用系列',
      m.context_window ? Number(m.context_window) : '-',
      m.max_output ? Number(m.max_output) : 8192,
      m.official_input_price !== undefined ? Number(m.official_input_price.toFixed(4)) : '-',
      m.official_output_price !== undefined ? Number(m.official_output_price.toFixed(4)) : '-',
      lowest > 0 ? Number(lowest.toFixed(4)) : '未标价/0',
      m.active_relay_count || m.providersCount || 0,
      m.modalities && m.modalities.length > 0 ? m.modalities.join('/') : 'text->text',
      m.supports_reasoning || /r1|o1|o3|reason/i.test(m.model_id) ? '支持' : '否',
      m.supports_tool_call !== false ? '支持' : '否',
      m.supports_structured_output !== false ? '支持' : '否'
    ])
  }

  const worksheet = XLSX.utils.aoa_to_sheet(rows)
  worksheet['!cols'] = autoFitColumnWidths(rows)

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, `${vendorName}模型规格清单`)

  const safeName = vendorName.replace(/[\\/:*?"<>|]/g, '_')
  const filename = `WellToken-模型厂商-${safeName}-${getTimestampString()}.xlsx`
  downloadWorkbook(workbook, filename)
}
