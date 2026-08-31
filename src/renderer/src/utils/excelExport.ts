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
 * 统一价格格式化计算函数：与界面 store.formatCurrency 保持 100% 精度与舍入对齐
 * 消除浮点数乘除汇率产生的如 23.9997 / 12.0002 / 7.9997 等微差
 */
export function formatExportPrice(
  usdPrice: number | null | undefined,
  currency: 'USD' | 'CNY' = 'CNY',
  exchangeRate = 7.25
): number {
  if (usdPrice === null || usdPrice === undefined || isNaN(usdPrice) || usdPrice === 0) {
    return 0
  }
  const rate = exchangeRate > 0 ? exchangeRate : 7.25
  const val = currency === 'USD' ? usdPrice : usdPrice * rate

  if (val < 0.001) {
    return Number(val.toFixed(4))
  }
  // 保持与前端 store.formatCurrency 统一的 3 位小数四舍五入
  return Number(val.toFixed(3))
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
    const inVal = formatExportPrice(item.calculated_input_usd, currency, rate)
    const outVal = formatExportPrice(item.calculated_output_usd, currency, rate)
    const cacheVal = formatExportPrice(item.calculated_cache_usd, currency, rate)

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
      inVal,
      outVal,
      cacheVal,
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
    const inVal = formatExportPrice(m.calculated_input_usd, currency, rate)
    const outVal = formatExportPrice(m.calculated_output_usd, currency, rate)

    rows.push([
      channelName,
      m.name || m.model_name || m.model_id,
      m.model_id || '',
      m.site_model_name && m.site_model_name !== m.model_id ? m.site_model_name : '默认规格',
      m.group_name || 'default',
      m.context_window ? Number(m.context_window) : '-',
      m.max_output ? Number(m.max_output) : 8192,
      inVal,
      outVal,
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
    const rawOffIn = m.official_input_price
    const rawOffOut = m.official_output_price
    const rawLowest = m.lowest_price_usd

    const offIn = formatExportPrice(rawOffIn, currency, rate)
    const offOut = formatExportPrice(rawOffOut, currency, rate)
    const lowest = formatExportPrice(rawLowest, currency, rate)

    rows.push([
      vendorName.toUpperCase(),
      m.name || m.model_name || m.model_id,
      m.model_id || '',
      m.series || '通用系列',
      m.context_window ? Number(m.context_window) : '-',
      m.max_output ? Number(m.max_output) : 8192,
      rawOffIn && rawOffIn > 0 ? offIn : '未标价/0',
      rawOffOut && rawOffOut > 0 ? offOut : '未标价/0',
      rawLowest && rawLowest > 0 ? lowest : '未标价/0',
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
