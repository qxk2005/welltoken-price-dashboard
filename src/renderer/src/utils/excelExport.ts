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
 * 1. 导出全网比价列表数据为 Excel（仅包含用户当前选中的单一币种）
 */
export function exportPriceMatrixToExcel(
  items: ComparisonItem[],
  currency: 'USD' | 'CNY' = 'CNY',
  exchangeRate = 7.25
) {
  if (!items || items.length === 0) {
    alert('当前筛选条件下无数据可导出')
    return
  }

  const currSymbol = currency === 'USD' ? '$' : '¥'
  const isUsd = currency === 'USD'
  const rate = exchangeRate > 0 ? exchangeRate : 7.25

  const headers = [
    '模型厂商',
    '模型系列',
    '模型标准标识 (Model ID)',
    '渠道规格/分段区间',
    '渠道名称',
    '渠道类型',
    '结算分组',
    `输入单价 (${currSymbol}/1M)`,
    `输出单价 (${currSymbol}/1M)`,
    `缓存单价 (${currSymbol}/1M)`,
    '相对官方基准折扣',
    '模型倍率',
    '实测 TPS (Tokens/s)',
    '渠道可用状态',
    '实时延迟 (ms)',
    '数据更新时间'
  ]

  const rows: any[][] = [headers]

  for (const item of items) {
    const inVal = isUsd
      ? item.calculated_input_usd
      : (item.calculated_input_cny !== undefined && item.calculated_input_cny > 0 ? item.calculated_input_cny : item.calculated_input_usd * rate)
    const outVal = isUsd
      ? item.calculated_output_usd
      : (item.calculated_output_cny !== undefined && item.calculated_output_cny > 0 ? item.calculated_output_cny : item.calculated_output_usd * rate)
    const cacheVal = isUsd
      ? item.calculated_cache_usd
      : (item.calculated_cache_usd * rate)

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
      inVal !== undefined ? Number(inVal.toFixed(4)) : 0,
      outVal !== undefined ? Number(outVal.toFixed(4)) : 0,
      cacheVal !== undefined ? Number(cacheVal.toFixed(4)) : 0,
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

  const filename = `WellToken-全网比价-${currency}-${getTimestampString()}.xlsx`
  downloadWorkbook(workbook, filename)
}

/**
 * 2. 导出供应商详情中的可用模型列表为 Excel（严格响应当前全局选中的单一币种）
 */
export function exportChannelModelsToExcel(
  channelName: string,
  models: any[],
  currency: 'USD' | 'CNY' = 'CNY',
  exchangeRate = 7.25
) {
  if (!models || models.length === 0) {
    alert('当前渠道下无模型数据可导出')
    return
  }

  const currSymbol = currency === 'USD' ? '$' : '¥'
  const isUsd = currency === 'USD'
  const rate = exchangeRate > 0 ? exchangeRate : 7.25

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
    '深度推理',
    '实测 TPS'
  ]

  const rows: any[][] = [headers]

  for (const m of models) {
    const inVal = isUsd
      ? (m.calculated_input_usd || 0)
      : (m.calculated_input_cny !== undefined && m.calculated_input_cny > 0 ? m.calculated_input_cny : (m.calculated_input_usd || 0) * rate)
    const outVal = isUsd
      ? (m.calculated_output_usd || 0)
      : (m.calculated_output_cny !== undefined && m.calculated_output_cny > 0 ? m.calculated_output_cny : (m.calculated_output_usd || 0) * rate)

    rows.push([
      channelName,
      m.name || m.model_name || m.model_id,
      m.model_id || '',
      m.site_model_name && m.site_model_name !== m.model_id ? m.site_model_name : '默认规格',
      m.group_name || 'default',
      m.context_window ? Number(m.context_window) : '-',
      m.max_output ? Number(m.max_output) : 8192,
      Number(inVal.toFixed(4)),
      Number(outVal.toFixed(4)),
      m.is_reasoning || (m.model_id && /r1|o1|o3|reason|deepseek-r/i.test(m.model_id)) ? '支持' : '否',
      m.last_tested_tps || 55
    ])
  }

  const worksheet = XLSX.utils.aoa_to_sheet(rows)
  worksheet['!cols'] = autoFitColumnWidths(rows)

  const workbook = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(workbook, worksheet, '渠道可用模型与定价')

  const safeName = channelName.replace(/[\\/:*?"<>|]/g, '_')
  const filename = `WellToken-渠道-${safeName}-${currency}-${getTimestampString()}.xlsx`
  downloadWorkbook(workbook, filename)
}

/**
 * 3. 导出模型厂商详情中的模型列表为 Excel（严格响应当前全局选中的单一币种）
 */
export function exportVendorModelsToExcel(
  vendorName: string,
  models: ModelMetadata[] | any[],
  currency: 'USD' | 'CNY' = 'CNY',
  exchangeRate = 7.25
) {
  if (!models || models.length === 0) {
    alert('当前厂商下无模型数据可导出')
    return
  }

  const currSymbol = currency === 'USD' ? '$' : '¥'
  const isUsd = currency === 'USD'
  const rate = exchangeRate > 0 ? exchangeRate : 7.25

  const headers = [
    '厂商名称',
    '模型名称',
    '模型标准标识 (Model ID)',
    '所属系列',
    '上下文窗口 (Context)',
    '最大输出 (Max Output)',
    `官方输入单价 (${currSymbol}/1M)`,
    `官方输出单价 (${currSymbol}/1M)`,
    `全网最低价 (${currSymbol}/1M)`,
    '接入渠道数',
    '多模态支持',
    '深度推理',
    '工具调用',
    '结构化输出'
  ]

  const rows: any[][] = [headers]

  for (const m of models) {
    const rawOffIn = m.official_input_price || 0
    const rawOffOut = m.official_output_price || 0
    const rawLowest = m.lowest_price_usd || 0

    const offIn = isUsd ? rawOffIn : rawOffIn * rate
    const offOut = isUsd ? rawOffOut : rawOffOut * rate
    const lowest = isUsd ? rawLowest : rawLowest * rate

    rows.push([
      vendorName.toUpperCase(),
      m.name || m.model_name || m.model_id,
      m.model_id || '',
      m.series || '通用系列',
      m.context_window ? Number(m.context_window) : '-',
      m.max_output ? Number(m.max_output) : 8192,
      rawOffIn > 0 ? Number(offIn.toFixed(4)) : '未标价/0',
      rawOffOut > 0 ? Number(offOut.toFixed(4)) : '未标价/0',
      rawLowest > 0 ? Number(lowest.toFixed(4)) : '未标价/0',
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
  XLSX.utils.book_append_sheet(workbook, worksheet, `${vendorName}模型清单`)

  const safeName = vendorName.replace(/[\\/:*?"<>|]/g, '_')
  const filename = `WellToken-模型厂商-${safeName}-${currency}-${getTimestampString()}.xlsx`
  downloadWorkbook(workbook, filename)
}
