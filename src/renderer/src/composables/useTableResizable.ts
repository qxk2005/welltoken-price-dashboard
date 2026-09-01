import { ref, onMounted } from 'vue'

export interface ColumnWidthConfig {
  [key: string]: number // 列宽 (px)
}

export interface UseTableResizableOptions {
  storageKey: string
  defaultWidths: ColumnWidthConfig
  minWidth?: number
  maxWidth?: number
}

export function useTableResizable(options: UseTableResizableOptions) {
  const {
    storageKey,
    defaultWidths,
    minWidth = 60,
    maxWidth = 900
  } = options

  const columnWidths = ref<ColumnWidthConfig>({ ...defaultWidths })
  const isResizing = ref(false)
  const resizingColumn = ref<string | null>(null)

  const loadWidths = () => {
    try {
      const saved = localStorage.getItem(storageKey)
      if (saved) {
        const parsed = JSON.parse(saved)
        columnWidths.value = { ...defaultWidths, ...parsed }
      }
    } catch (e) {
      console.warn('加载表格列宽失败:', e)
    }
  }

  const saveWidths = () => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(columnWidths.value))
    } catch (e) {
      console.warn('保存表格列宽失败:', e)
    }
  }

  const getWidth = (key: string): string => {
    const w = columnWidths.value[key] || defaultWidths[key]
    return w ? `${w}px` : 'auto'
  }

  const getWidthNum = (key: string): number => {
    return columnWidths.value[key] || defaultWidths[key] || 100
  }

  const resetWidths = () => {
    columnWidths.value = { ...defaultWidths }
    saveWidths()
  }

  const resetColumnWidth = (key: string) => {
    if (defaultWidths[key]) {
      columnWidths.value[key] = defaultWidths[key]
      saveWidths()
    }
  }

  const startResize = (key: string, event: MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()

    isResizing.value = true
    resizingColumn.value = key

    const startX = event.clientX
    const startWidth = columnWidths.value[key] || defaultWidths[key] || 100

    const onMouseMove = (e: MouseEvent) => {
      if (!isResizing.value) return
      const deltaX = e.clientX - startX
      let newWidth = Math.round(startWidth + deltaX)
      if (newWidth < minWidth) newWidth = minWidth
      if (newWidth > maxWidth) newWidth = maxWidth
      columnWidths.value[key] = newWidth
    }

    const onMouseUp = () => {
      if (isResizing.value) {
        isResizing.value = false
        resizingColumn.value = null
        saveWidths()
      }
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
    }

    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
  }

  onMounted(() => {
    loadWidths()
  })

  return {
    columnWidths,
    isResizing,
    resizingColumn,
    getWidth,
    getWidthNum,
    startResize,
    resetWidths,
    resetColumnWidth
  }
}
