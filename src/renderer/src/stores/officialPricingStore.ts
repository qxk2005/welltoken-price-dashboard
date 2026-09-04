import { defineStore } from 'pinia'
import axios from 'axios'
import * as XLSX from 'xlsx'

export interface OfficialModelPrice {
  id: number
  provider: string
  provider_name: string
  series: string
  model_name: string
  raw_model_id: string
  billing_mode: string
  tier_range: string
  currency: 'USD' | 'CNY'
  input_price: number
  output_price: number
  cache_read_price: number
  cache_write_price: number
  remarks: string
  custom_notes: string
  user_tags: string
  price_date: string
  source_page_url: string
  source_anchor: string
  snapshot_id: number | null
  is_active: boolean
  created_at: string
  updated_at: string
  converted_input_cny?: number
  converted_output_cny?: number
  converted_cache_read_cny?: number
  converted_cache_write_cny?: number
  converted_input_usd?: number
  converted_output_usd?: number
  converted_cache_read_usd?: number
  converted_cache_write_usd?: number
}

export interface OfficialSnapshot {
  id: number
  provider: string
  source_url: string
  page_title: string
  local_file_path: string
  file_size_bytes: number
  models_count: number
  captured_at: string
}

export const DEFAULT_COLUMNS: Record<string, { label: string; defaultVisible: boolean }> = {
  provider_name: { label: '模型厂商', defaultVisible: true },
  series: { label: '模型系列', defaultVisible: true },
  model_name: { label: '模型规格 / 阶梯名', defaultVisible: true },
  billing_mode: { label: '计费模式', defaultVisible: true },
  input_price: { label: '输入价格 (1M)', defaultVisible: true },
  output_price: { label: '输出价格 (1M)', defaultVisible: true },
  cache_read_price: { label: '缓存命中/读 (1M)', defaultVisible: true },
  cache_write_price: { label: '缓存写 (1M)', defaultVisible: true },
  remarks: { label: '官方备注与规则', defaultVisible: true },
  custom_notes: { label: '自定义备注与标签', defaultVisible: true },
  price_date: { label: '价格生效时间', defaultVisible: true },
  source_anchor: { label: '页面位置与快照对账', defaultVisible: true }
}

export const useOfficialPricingStore = defineStore('officialPricing', {
  state: () => {
    // 从 localStorage 读取已保存的列设置
    const savedCols = localStorage.getItem('welltoken_official_cols')
    let visibleCols: Record<string, boolean> = {}
    if (savedCols) {
      try {
        visibleCols = JSON.parse(savedCols)
      } catch {
        visibleCols = {}
      }
    }
    for (const key of Object.keys(DEFAULT_COLUMNS)) {
      if (visibleCols[key] === undefined) {
        visibleCols[key] = DEFAULT_COLUMNS[key].defaultVisible
      }
    }

    return {
      apiUrl: 'http://127.0.0.1:8765',
      isLoading: false,
      isScraping: false,
      scrapeMessage: '',
      
      // 数据源
      allModels: [] as OfficialModelPrice[],
      providersList: [] as Array<{ code: string; name: string }>,
      seriesList: [] as Array<{ series: string; provider: string }>,
      snapshots: [] as OfficialSnapshot[],
      usdToCnyRate: 7.30,

      // 筛选条件
      selectedProviders: [] as string[],
      selectedSeries: [] as string[],
      selectedBillingMode: 'all',
      searchKeyword: '',

      // 展现模式：平铺 (flat) / 按厂商分组 (group-vendor) / 按系列分组 (group-series) / 树形层级 (tree)
      viewMode: (localStorage.getItem('welltoken_official_viewmode') as 'flat' | 'group-vendor' | 'group-series' | 'tree') || 'flat',
      
      // 币种模式：原币种 (original: 国外$ 国内¥) / 统一折合人民币 (cny) / 统一折合美元 (usd)
      currencyMode: (localStorage.getItem('welltoken_official_currency') as 'original' | 'cny' | 'usd') || 'original',

      // 分组展开/折叠状态
      collapsedGroups: {} as Record<string, boolean>,

      // 自定义列显隐
      visibleColumns: visibleCols,

      // 快照预览抽屉
      snapshotDrawer: {
        visible: false,
        snapshotId: null as number | null,
        sourceUrl: '',
        modelName: '',
        pageTitle: '',
        highlightTarget: ''
      },

      // 编辑自定义备注模态框
      editingNoteItem: null as OfficialModelPrice | null,

      // 代理配置弹窗与状态
      scrapeModalVisible: false,
      customProxy: localStorage.getItem('welltoken_scrape_proxy') || '',

      // 排序状态 (三态：asc -> desc -> null)
      sortField: (localStorage.getItem('welltoken_official_sort_field') as 'provider_name' | 'series' | 'model_name' | null) || null,
      sortOrder: (localStorage.getItem('welltoken_official_sort_order') as 'asc' | 'desc' | null) || null
    }
  },

  getters: {
    // 经过多维筛选与字段排序后的模型列表
    filteredModels(state): OfficialModelPrice[] {
      const list = state.allModels.filter((m) => {
        // 厂商筛选
        if (state.selectedProviders.length > 0 && !state.selectedProviders.includes(m.provider)) {
          return false
        }
        // 系列筛选
        if (state.selectedSeries.length > 0 && !state.selectedSeries.includes(m.series)) {
          return false
        }
        // 计费模式筛选 (纯净大类覆盖)
        if (state.selectedBillingMode !== 'all') {
          const target = state.selectedBillingMode
          const mode = m.billing_mode || ''
          if (target === 'Standard') {
            // 包含所有 Standard 标准计费模型 (涵盖各种阶梯区间与特惠模型)
            if (!mode.toLowerCase().startsWith('standard') && mode !== 'Standard') {
              return false
            }
          } else if (target === '闲时半价') {
            if (!mode.includes('闲时')) return false
          } else if (target === 'Batch 批处理') {
            if (!mode.includes('Batch') && !mode.includes('批处理')) return false
          } else if (target === 'Flex 弹性') {
            if (!mode.includes('Flex') && !mode.includes('弹性')) return false
          } else if (target === 'Priority 优先') {
            if (!mode.includes('Priority') && !mode.includes('优先')) return false
          } else {
            if (mode !== target) return false
          }
        }
        // 搜索关键字模糊过滤
        if (state.searchKeyword.trim()) {
          const kw = state.searchKeyword.trim().toLowerCase()
          const matchName = m.model_name.toLowerCase().includes(kw)
          const matchProvider = m.provider_name.toLowerCase().includes(kw)
          const matchSeries = m.series.toLowerCase().includes(kw)
          const matchRemarks = (m.remarks || '').toLowerCase().includes(kw)
          const matchNotes = (m.custom_notes || '').toLowerCase().includes(kw)
          const matchTags = (m.user_tags || '').toLowerCase().includes(kw)
          if (!matchName && !matchProvider && !matchSeries && !matchRemarks && !matchNotes && !matchTags) {
            return false
          }
        }
        return true
      })

      // 字段排序 (支持 中文拼音/自然数字/字母 规范排序)
      if (state.sortField && state.sortOrder) {
        const field = state.sortField
        const factor = state.sortOrder === 'asc' ? 1 : -1
        list.sort((a, b) => {
          const valA = String(a[field] || '')
          const valB = String(b[field] || '')
          return valA.localeCompare(valB, 'zh-CN', { numeric: true, sensitivity: 'base' }) * factor
        })
      }

      return list
    },

    // 按厂商分组的数据结构
    groupedByVendor(state): Array<{
      key: string
      provider: string
      providerName: string
      count: number
      items: OfficialModelPrice[]
    }> {
      const groups: Record<string, { provider: string; providerName: string; items: OfficialModelPrice[] }> = {}
      for (const m of this.filteredModels) {
        if (!groups[m.provider]) {
          groups[m.provider] = {
            provider: m.provider,
            providerName: m.provider_name,
            items: []
          }
        }
        groups[m.provider].items.push(m)
      }

      const keys = Object.keys(groups)
      if (state.sortField === 'provider_name' && state.sortOrder) {
        const factor = state.sortOrder === 'asc' ? 1 : -1
        keys.sort((a, b) => groups[a].providerName.localeCompare(groups[b].providerName, 'zh-CN') * factor)
      } else {
        keys.sort()
      }

      return keys.map((code) => ({
        key: `vendor_${code}`,
        provider: code,
        providerName: groups[code].providerName,
        count: groups[code].items.length,
        items: groups[code].items
      }))
    },

    // 按模型系列分组的数据结构
    groupedBySeries(state): Array<{
      key: string
      series: string
      providerName: string
      count: number
      items: OfficialModelPrice[]
    }> {
      const groups: Record<string, { series: string; providerName: string; items: OfficialModelPrice[] }> = {}
      for (const m of this.filteredModels) {
        const sKey = `${m.provider}_${m.series}`
        if (!groups[sKey]) {
          groups[sKey] = {
            series: m.series,
            providerName: m.provider_name,
            items: []
          }
        }
        groups[sKey].items.push(m)
      }

      const keys = Object.keys(groups)
      if (state.sortField === 'series' && state.sortOrder) {
        const factor = state.sortOrder === 'asc' ? 1 : -1
        keys.sort((a, b) => groups[a].series.localeCompare(groups[b].series, 'zh-CN') * factor)
      } else {
        keys.sort()
      }

      return keys.map((sKey) => ({
        key: `series_${sKey}`,
        series: groups[sKey].series,
        providerName: groups[sKey].providerName,
        count: groups[sKey].items.length,
        items: groups[sKey].items
      }))
    },

    // 树形折叠层级结构：厂商 (Level 1) ➔ 系列 (Level 2) ➔ 具体模型/阶梯 (Level 3)
    treeHierarchy(): Array<{
      key: string
      provider: string
      providerName: string
      count: number
      seriesNodes: Array<{
        key: string
        series: string
        count: number
        items: OfficialModelPrice[]
      }>
    }> {
      const vendorMap: Record<string, {
        provider: string
        providerName: string
        seriesMap: Record<string, OfficialModelPrice[]>
      }> = {}

      for (const m of this.filteredModels) {
        if (!vendorMap[m.provider]) {
          vendorMap[m.provider] = {
            provider: m.provider,
            providerName: m.provider_name,
            seriesMap: {}
          }
        }
        if (!vendorMap[m.provider].seriesMap[m.series]) {
          vendorMap[m.provider].seriesMap[m.series] = []
        }
        vendorMap[m.provider].seriesMap[m.series].push(m)
      }

      return Object.keys(vendorMap).sort().map((pCode) => {
        const v = vendorMap[pCode]
        const seriesKeys = Object.keys(v.seriesMap).sort()
        let totalCount = 0
        const seriesNodes = seriesKeys.map((s) => {
          const items = v.seriesMap[s]
          totalCount += items.length
          return {
            key: `tree_series_${pCode}_${s}`,
            series: s,
            count: items.length,
            items
          }
        })
        return {
          key: `tree_vendor_${pCode}`,
          provider: pCode,
          providerName: v.providerName,
          count: totalCount,
          seriesNodes
        }
      })
    }
  },

  actions: {
    toggleSort(field: 'provider_name' | 'series' | 'model_name') {
      if (this.sortField !== field) {
        this.sortField = field
        this.sortOrder = 'asc'
      } else if (this.sortOrder === 'asc') {
        this.sortOrder = 'desc'
      } else {
        this.sortField = null
        this.sortOrder = null
      }
      if (this.sortField && this.sortOrder) {
        localStorage.setItem('welltoken_official_sort_field', this.sortField)
        localStorage.setItem('welltoken_official_sort_order', this.sortOrder)
      } else {
        localStorage.removeItem('welltoken_official_sort_field')
        localStorage.removeItem('welltoken_official_sort_order')
      }
    },

    setViewMode(mode: 'flat' | 'group-vendor' | 'group-series' | 'tree') {
      this.viewMode = mode
      localStorage.setItem('welltoken_official_viewmode', mode)
    },

    setCurrencyMode(mode: 'original' | 'cny' | 'usd') {
      this.currencyMode = mode
      localStorage.setItem('welltoken_official_currency', mode)
    },

    toggleGroup(groupKey: string) {
      this.collapsedGroups[groupKey] = !this.collapsedGroups[groupKey]
    },

    expandAll() {
      this.collapsedGroups = {}
    },

    collapseAll() {
      // 收起所有当前视图的分组
      if (this.viewMode === 'group-vendor') {
        for (const g of this.groupedByVendor) {
          this.collapsedGroups[g.key] = true
        }
      } else if (this.viewMode === 'group-series') {
        for (const g of this.groupedBySeries) {
          this.collapsedGroups[g.key] = true
        }
      } else if (this.viewMode === 'tree') {
        for (const v of this.treeHierarchy) {
          this.collapsedGroups[v.key] = true
          for (const s of v.seriesNodes) {
            this.collapsedGroups[s.key] = true
          }
        }
      }
    },

    toggleColumn(key: string) {
      this.visibleColumns[key] = !this.visibleColumns[key]
      localStorage.setItem('welltoken_official_cols', JSON.stringify(this.visibleColumns))
    },

    resetColumns() {
      for (const key of Object.keys(DEFAULT_COLUMNS)) {
        this.visibleColumns[key] = DEFAULT_COLUMNS[key].defaultVisible
      }
      localStorage.setItem('welltoken_official_cols', JSON.stringify(this.visibleColumns))
    },

    // 加载官方模型价格数据
    async fetchOfficialPrices() {
      this.isLoading = true
      try {
        const resp = await axios.get(`${this.apiUrl}/api/v1/official-pricing/list`)
        if (resp.data && resp.data.status === 'success') {
          this.allModels = resp.data.models || []
          this.providersList = resp.data.providers || []
          this.seriesList = resp.data.series || []
          this.usdToCnyRate = resp.data.usd_to_cny_rate || 7.30
        }
      } catch (err) {
        console.error('Failed to fetch official prices:', err)
      } finally {
        this.isLoading = false
      }
    },

    // 加载网页快照列表
    async fetchSnapshots() {
      try {
        const resp = await axios.get(`${this.apiUrl}/api/v1/official-pricing/snapshots`)
        this.snapshots = resp.data || []
      } catch (err) {
        console.error('Failed to fetch snapshots:', err)
      }
    },

    // 打开快照预览抽屉
    openSnapshotDrawer(item: OfficialModelPrice) {
      this.snapshotDrawer = {
        visible: true,
        snapshotId: item.snapshot_id,
        sourceUrl: item.source_page_url,
        modelName: item.model_name,
        pageTitle: `${item.provider_name} 官方定价快照对账`,
        highlightTarget: item.raw_model_id ? `${item.model_name}|${item.raw_model_id}` : (item.model_name || '')
      }
    },

    closeSnapshotDrawer() {
      this.snapshotDrawer.visible = false
    },

    // 更新用户自定义备注与标签
    async saveModelNotes(modelId: number, customNotes: string, userTags: string) {
      try {
        const resp = await axios.patch(`${this.apiUrl}/api/v1/official-pricing/model/${modelId}/notes`, {
          custom_notes: customNotes,
          user_tags: userTags
        })
        if (resp.data && resp.data.status === 'success') {
          const target = this.allModels.find((m) => m.id === modelId)
          if (target) {
            target.custom_notes = customNotes
            target.user_tags = userTags
          }
          return true
        }
      } catch (err) {
        console.error('Failed to save notes:', err)
        return false
      }
      return false
    },

    // 触发抓取
    async triggerScrape(provider?: string) {
      this.isScraping = true
      this.scrapeMessage = '正在连接官网并解析渲染 DOM...'
      try {
        if (this.customProxy) {
          localStorage.setItem('welltoken_scrape_proxy', this.customProxy)
        }
        const resp = await axios.post(`${this.apiUrl}/api/v1/official-pricing/scrape`, {
          provider: provider || 'all',
          proxy: this.customProxy || null
        })
        if (resp.data) {
          await this.fetchOfficialPrices()
          await this.fetchSnapshots()
          return resp.data
        }
      } catch (err: any) {
        console.error('Scrape error:', err)
        throw err
      } finally {
        this.isScraping = false
        this.scrapeMessage = ''
      }
    },

    // 导出 Excel (.xlsx)
    exportToExcel() {
      const dataToExport = this.filteredModels.map((m) => {
        const row: Record<string, any> = {}
        if (this.visibleColumns.provider_name) row['模型厂商'] = m.provider_name
        if (this.visibleColumns.series) row['模型系列'] = m.series
        if (this.visibleColumns.model_name) row['模型规格与阶梯名'] = m.model_name
        if (this.visibleColumns.billing_mode) row['计费模式'] = m.billing_mode

        // 价格显示根据当前币种模式转换
        if (this.currencyMode === 'cny') {
          if (this.visibleColumns.input_price) row['输入价格 (¥/1M)'] = m.converted_input_cny ?? m.input_price
          if (this.visibleColumns.output_price) row['输出价格 (¥/1M)'] = m.converted_output_cny ?? m.output_price
          if (this.visibleColumns.cache_read_price) row['缓存读/命中 (¥/1M)'] = m.converted_cache_read_cny ?? m.cache_read_price
          if (this.visibleColumns.cache_write_price) row['缓存写 (¥/1M)'] = m.converted_cache_write_cny ?? m.cache_write_price
        } else if (this.currencyMode === 'usd') {
          if (this.visibleColumns.input_price) row['输入价格 ($/1M)'] = m.converted_input_usd ?? m.input_price
          if (this.visibleColumns.output_price) row['输出价格 ($/1M)'] = m.converted_output_usd ?? m.output_price
          if (this.visibleColumns.cache_read_price) row['缓存读/命中 ($/1M)'] = m.converted_cache_read_usd ?? m.cache_read_price
          if (this.visibleColumns.cache_write_price) row['缓存写 ($/1M)'] = m.converted_cache_write_usd ?? m.cache_write_price
        } else {
          const sym = m.currency === 'USD' ? '$' : '¥'
          if (this.visibleColumns.input_price) row[`输入价格 (${sym}/1M)`] = m.input_price
          if (this.visibleColumns.output_price) row[`输出价格 (${sym}/1M)`] = m.output_price
          if (this.visibleColumns.cache_read_price) row[`缓存读/命中 (${sym}/1M)`] = m.cache_read_price
          if (this.visibleColumns.cache_write_price) row[`缓存写 (${sym}/1M)`] = m.cache_write_price
        }

        if (this.visibleColumns.remarks) row['官方备注'] = m.remarks
        if (this.visibleColumns.custom_notes) row['自定义备注/标签'] = `${m.custom_notes} ${m.user_tags}`.trim()
        if (this.visibleColumns.price_date) row['价格生效时间'] = m.price_date
        if (this.visibleColumns.source_anchor) row['来源网址与位置'] = `${m.source_page_url} (${m.source_anchor})`

        return row
      })

      const worksheet = XLSX.utils.json_to_sheet(dataToExport)
      const workbook = XLSX.utils.book_new()
      XLSX.utils.book_append_sheet(workbook, worksheet, '官方模型价格表')
      
      const filename = `官方模型价格表_${new Date().toISOString().slice(0, 10)}.xlsx`
      XLSX.writeFile(workbook, filename)
    }
  }
})
