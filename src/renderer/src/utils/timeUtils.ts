/**
 * 后端 UTC 时间解析工具
 *
 * 后端统一使用 datetime.utcnow() 存储 UTC 时间，
 * 但返回的 ISO 字符串没有 'Z' 后缀（naive datetime），
 * 导致前端 new Date() 在解析时将其当作本地时间而非 UTC。
 *
 * 本模块统一处理这种 UTC naive datetime → 本地时区的转换。
 */

/**
 * 将后端返回的 UTC 时间字符串解析为正确的本地 Date 对象。
 * 自动为没有时区标记的 ISO 字符串添加 'Z' 后缀，
 * 确保浏览器正确将其作为 UTC 解析并转换为本地时区。
 *
 * @param raw 后端返回的时间字符串，如 "2026-08-31 14:05:32" 或 "2026-08-31T14:05:32"
 * @returns Date 对象（本地时区），或 null（解析失败时）
 */
export function parseUtcDate(raw: string): Date | null {
  if (!raw) return null

  // 纯日期格式 (如 "2026-08-31")，不需要时区修正
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    return new Date(raw + 'T00:00:00Z')
  }

  // 将空格替换为 T (兼容 "2026-08-31 14:05:32" 格式)
  let normalized = raw.replace(' ', 'T')

  // 如果没有时区标记 (Z, +XX:XX, -XX:XX)，添加 'Z' 表示 UTC
  if (!/[Zz]$/.test(normalized) && !/[+-]\d{2}:\d{2}$/.test(normalized)) {
    normalized += 'Z'
  }

  const d = new Date(normalized)
  return isNaN(d.getTime()) ? null : d
}

/**
 * 将后端 UTC 时间格式化为相对时间字符串（如 "刚刚"、"5分钟前"、"2天前"）
 *
 * @param raw 后端返回的 UTC 时间字符串
 * @returns 相对时间字符串
 */
export function formatRelativeTime(raw: string): string {
  const d = parseUtcDate(raw)
  if (!d) return raw || '—'

  const now = new Date()
  const diffSec = Math.floor((now.getTime() - d.getTime()) / 1000)
  if (diffSec < 0) return raw

  const diffMin = Math.floor(diffSec / 60)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)
  const diffMonth = Math.floor(diffDay / 30)
  const diffYear = Math.floor(diffDay / 365)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay < 30) return `${diffDay}天前`
  if (diffMonth < 12) return `${diffMonth}个月前`
  return `${diffYear}年前`
}

/**
 * 将后端 UTC 时间格式化为本地绝对时间字符串（如 "08-31 22:05"）
 *
 * @param raw 后端返回的 UTC 时间字符串
 * @param includeYear 是否包含年份
 * @returns 格式化的本地时间字符串
 */
export function formatLocalAbsoluteTime(raw: string, includeYear = false): string {
  const d = parseUtcDate(raw)
  if (!d) return raw || '—'

  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')

  if (includeYear) {
    const sec = String(d.getSeconds()).padStart(2, '0')
    return `${y}-${m}-${day} ${h}:${min}:${sec}`
  }
  return `${m}-${day} ${h}:${min}`
}
