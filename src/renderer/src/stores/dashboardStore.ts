import { defineStore } from 'pinia'
import axios from 'axios'
import type {
  ComparisonItem,
  RelaySite,
  ModelMetadata,
  SpeedTestResult,
  SpeedTestStreamEvent,
  SyncStatus,
  SyncLog,
  ICloudSyncStatus,
  ICloudBackupItem,
  ICloudSyncConfig
} from '../types'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    apiUrl: 'http://127.0.0.1:8765',
    wsUrl: 'ws://127.0.0.1:8765/api/v1/price/ws',
    activeTab: (typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('tab'))
      ? (new URLSearchParams(window.location.search).get('tab') as any)
      : ('official-pricing' as 'official-pricing' | 'price-matrix' | 'channels' | 'models' | 'speed-tester' | 'settings' | 'about'),
    currency: 'USD' as 'USD' | 'CNY',
    usdToCnyRate: 7.25,
    searchQuery: '',
    selectedProvider: 'all',
    selectedModelId: 'all',
    selectedSiteId: null as number | null,
    
    // 收藏夹渠道 ID 集合 (持久化至 localStorage)
    favoriteSiteIds: JSON.parse(localStorage.getItem('welltoken_fav_sites') || '[]') as number[],
    
    // 侧边栏折叠状态 (支持 URL 参数覆盖与 localStorage 持久化)
    isSidebarCollapsed: typeof window !== 'undefined' && (window.location.search.includes('collapsed=true') || localStorage.getItem('welltoken_sidebar_collapsed') === 'true'),
    
    // 数据集合
    comparisonMatrix: [] as ComparisonItem[],
    relaySites: [] as RelaySite[],
    modelsCatalog: [] as ModelMetadata[],
    speedTestHistory: [] as SpeedTestResult[],
    syncStatus: null as SyncStatus | null,
    syncLogs: [] as SyncLog[],
    
    // 测速状态
    isSpeedTesting: false,
    currentSpeedStream: {} as Record<number, SpeedTestStreamEvent>,
    speedLogMessages: [] as string[],
    speedTestTargetSiteId: null as number | null,
    speedTestTargetModelId: null as string | null,

    // 跨模块比价跳转与高亮基准传参
    targetModelFilter: null as string | null,
    targetSiteFilter: null as string | null,
    targetProviderFilter: null as string | null,
    highlightBenchmarkSiteName: null as string | null,

    // 从全网比价跳转至详情标记与目标
    navigatedFromPriceMatrix: false,
    targetChannelSiteName: null as string | null,
    targetLabProvider: null as string | null,
    
    // 全网数据同步进度状态
    syncProgress: {
      visible: false,
      isSyncing: false,
      stage: 0, // 0: idle, 1: download, 2: normalize, 3: pricing, 4: persist, 5: done, -1: error
      progress: 0,
      message: '',
      detail: '',
      stats: {} as { models_count?: number; providers_count?: number; pricings_count?: number; duration_ms?: number },
      error: ''
    },

    // macOS iCloud 云端同步状态与持久化配置
    icloudStatus: null as ICloudSyncStatus | null,
    icloudBackups: [] as ICloudBackupItem[],
    isICloudLoading: false,
    isICloudSyncing: false,
    icloudConfig: (typeof window !== 'undefined' && JSON.parse(localStorage.getItem('welltoken_icloud_config') || 'null')) || ({
      autoSync: true,
      includeApiKeys: true,
      usePassword: false,
      password: '',
      modules: {
        custom_channels: true,
        custom_aliases: true,
        favorites: true,
        preferences: true,
        speed_tests: false
      }
    } as ICloudSyncConfig),

    // 系统连接状态
    isConnected: false,
    backendHealthy: false,
    ws: null as WebSocket | null
  }),

  getters: {
    filteredMatrix(state): ComparisonItem[] {
      let list = state.comparisonMatrix
      if (state.selectedProvider !== 'all') {
        list = list.filter((item) => item.provider.toLowerCase() === state.selectedProvider.toLowerCase())
      }
      if (state.selectedModelId !== 'all') {
        list = list.filter((item) => item.model_id === state.selectedModelId)
      }
      if (state.searchQuery.trim()) {
        const q = state.searchQuery.toLowerCase()
        list = list.filter(
          (item) =>
            item.model_id.toLowerCase().includes(q) ||
            item.model_name.toLowerCase().includes(q) ||
            item.site_name.toLowerCase().includes(q) ||
            (item.site_model_name && item.site_model_name.toLowerCase().includes(q))
        )
      }
      return list
    },
    featuredModels(state): ModelMetadata[] {
      return state.modelsCatalog.filter((m) => m.is_featured)
    },
    activeSites(state): RelaySite[] {
      return state.relaySites.filter((s) => s.is_active)
    },
    favoriteSites(state): RelaySite[] {
      return state.relaySites.filter((s) => state.favoriteSiteIds.includes(s.id))
    }
  },

  actions: {
    // 全局通用货币格式化方法 (响应 currency 切换：USD 显示 $, CNY 自动按汇率换算并显示 ¥)
    formatCurrency(usdPrice: number | null | undefined, digits: number = 3): string {
      if (usdPrice === null || usdPrice === undefined || isNaN(usdPrice)) return '-'
      if (usdPrice === 0) return this.currency === 'USD' ? '$0.000' : '¥0.000'

      if (this.currency === 'USD') {
        const str = usdPrice < 0.001 ? usdPrice.toFixed(4) : usdPrice.toFixed(digits)
        return `$${str}`
      } else {
        const cny = usdPrice * (this.usdToCnyRate || 7.25)
        const str = cny < 0.001 ? cny.toFixed(4) : cny.toFixed(digits)
        return `¥${str}`
      }
    },

    // 官方输入/输出双单价格式化
    formatDualCurrency(inputUsd: number | null | undefined, outputUsd: number | null | undefined, digits: number = 3): string {
      const inStr = this.formatCurrency(inputUsd, digits)
      const outStr = this.formatCurrency(outputUsd, digits)
      return `${inStr} / ${outStr}`
    },

    isSiteFavorite(siteId: number): boolean {
      return this.favoriteSiteIds.includes(siteId)
    },

    toggleFavoriteSite(siteId: number) {
      if (this.favoriteSiteIds.includes(siteId)) {
        this.favoriteSiteIds = this.favoriteSiteIds.filter((id) => id !== siteId)
      } else {
        this.favoriteSiteIds.push(siteId)
      }
      localStorage.setItem('welltoken_fav_sites', JSON.stringify(this.favoriteSiteIds))
    },

    async init() {
      if (window.api?.getBackendConfig) {
        try {
          const config = await window.api.getBackendConfig()
          this.apiUrl = config.apiUrl
          this.wsUrl = config.wsUrl
        } catch (e) {
          console.warn('Fallback config:', e)
        }
      }
      await this.fetchSyncStatus()
      await this.fetchComparisonMatrix()
      await this.fetchRelaySites()
      await this.fetchModelsCatalog()
      await this.fetchSpeedTestHistory()
      await this.fetchICloudStatus()
      this.connectWebSocket()
    },

    async fetchComparisonMatrix() {
      try {
        const res = await axios.get<ComparisonItem[]>(`${this.apiUrl}/api/v1/comparison/matrix`)
        this.comparisonMatrix = res.data
        this.backendHealthy = true
      } catch (e) {
        console.error('Fetch matrix failed:', e)
      }
    },

    async fetchRelaySites() {
      try {
        const res = await axios.get<RelaySite[]>(`${this.apiUrl}/api/v1/channels`)
        this.relaySites = res.data
      } catch (e) {
        console.error('Fetch sites failed:', e)
      }
    },

    async fetchModelsCatalog() {
      try {
        const res = await axios.get<ModelMetadata[]>(`${this.apiUrl}/api/v1/models`)
        this.modelsCatalog = res.data
      } catch (e) {
        console.error('Fetch models failed:', e)
      }
    },

    async fetchSpeedTestHistory() {
      try {
        const res = await axios.get<SpeedTestResult[]>(`${this.apiUrl}/api/v1/speed-test/history`)
        this.speedTestHistory = res.data
      } catch (e) {
        console.error('Fetch speed history failed:', e)
      }
    },

    async fetchSyncStatus() {
      try {
        const res = await axios.get<SyncStatus>(`${this.apiUrl}/api/v1/settings/status`)
        this.syncStatus = res.data
        if (res.data.usd_to_cny_rate) {
          this.usdToCnyRate = Number(res.data.usd_to_cny_rate)
        }
        if (res.data.recent_sync_logs) {
          this.syncLogs = res.data.recent_sync_logs
        }
      } catch (e) {
        console.error('Fetch sync status failed:', e)
      }
    },

    async syncModelsDev() {
      try {
        await axios.post(`${this.apiUrl}/api/v1/models/sync-models-dev`)
        await this.fetchModelsCatalog()
        await this.fetchComparisonMatrix()
        await this.fetchSyncStatus()
      } catch (e) {
        console.error('Sync models.dev failed:', e)
      }
    },

    async syncAllRelays() {
      try {
        await axios.post(`${this.apiUrl}/api/v1/channels/ping-all`)
        await this.fetchRelaySites()
        await this.fetchComparisonMatrix()
        await this.fetchSyncStatus()
      } catch (e) {
        console.error('Sync all relays failed:', e)
      }
    },

    async triggerFullSync() {
      this.syncProgress.visible = true
      this.syncProgress.isSyncing = true
      this.syncProgress.stage = 1
      this.syncProgress.progress = 10
      this.syncProgress.message = '正在连接并拉取 models.dev 官方 3 大核心数据源...'
      this.syncProgress.detail = '准备下载 models.json, catalog.json 与 api.json'
      this.syncProgress.error = ''

      try {
        const res = await axios.post(`${this.apiUrl}/api/v1/settings/full-sync`)
        const syncRes = res.data?.sync_result
        if (syncRes && syncRes.status === 'success') {
          this.syncProgress.stage = 5
          this.syncProgress.progress = 100
          this.syncProgress.message = '全网大模型与渠道比价数据同步完成！'
          this.syncProgress.detail = `已更新 ${syncRes.models_count || this.modelsCatalog.length} 款标准模型 · ${syncRes.providers_count || this.relaySites.length} 家供应商 · ${syncRes.pricings_count || this.comparisonMatrix.length} 条比价`
          this.syncProgress.stats = {
            models_count: syncRes.models_count || this.modelsCatalog.length,
            providers_count: syncRes.providers_count || this.relaySites.length,
            pricings_count: syncRes.pricings_count || this.comparisonMatrix.length,
            duration_ms: syncRes.duration_ms || 1200
          }
          this.syncProgress.isSyncing = false
        }
        await this.fetchComparisonMatrix()
        await this.fetchRelaySites()
        await this.fetchModelsCatalog()
        await this.fetchSyncStatus()
        return res.data
      } catch (e: any) {
        this.syncProgress.stage = -1
        this.syncProgress.isSyncing = false
        this.syncProgress.error = e.response?.data?.detail || e.message || '全网同步发生异常'
        console.error('Full sync failed:', e)
        throw e
      }
    },

    closeSyncProgress() {
      this.syncProgress.visible = false
      this.syncProgress.isSyncing = false
    },

    navigateToPriceMatrix(options?: {
      modelId?: string
      highlightSiteName?: string
      siteName?: string
      siteId?: number
      provider?: string
    }) {
      this.targetModelFilter = options?.modelId || null
      this.highlightBenchmarkSiteName = options?.highlightSiteName || null
      if (options?.siteName) {
        this.targetSiteFilter = options.siteName
      } else if (options?.siteId) {
        const site = this.relaySites.find((s) => s.id === options.siteId)
        this.targetSiteFilter = site ? site.name : null
      } else {
        this.targetSiteFilter = null
      }
      this.targetProviderFilter = options?.provider || null
      this.activeTab = 'price-matrix'
    },

    navigateToChannelDetail(siteName: string) {
      this.navigatedFromPriceMatrix = true
      this.targetChannelSiteName = siteName
      this.activeTab = 'channels'
    },

    navigateToLabDetail(provider: string) {
      this.navigatedFromPriceMatrix = true
      this.targetLabProvider = (provider || '').toLowerCase()
      this.activeTab = 'models'
    },

    returnToPriceMatrix() {
      this.navigatedFromPriceMatrix = false
      this.activeTab = 'price-matrix'
    },

    navigateToSpeedTest(siteId?: number, modelId?: string) {
      if (siteId !== undefined && siteId !== null) {
        this.speedTestTargetSiteId = siteId
      }
      if (modelId) {
        this.speedTestTargetModelId = modelId
      }
      this.activeTab = 'speed-tester'
    },

    async runSpeedTest(siteIds: number[], modelId = 'deepseek-v3', promptType = 'standard') {
      this.isSpeedTesting = true
      this.currentSpeedStream = {}
      this.speedLogMessages = [`[${new Date().toLocaleTimeString()}] 🚀 启动 ${siteIds.length} 个渠道并发流式测速任务 (模型: ${modelId})...`]
      
      try {
        const res = await axios.post<SpeedTestResult[]>(`${this.apiUrl}/api/v1/speed-test/run`, {
          site_ids: siteIds,
          model_id: modelId,
          prompt_type: promptType,
          rounds: 1
        })
        this.speedLogMessages.push(`[${new Date().toLocaleTimeString()}] ✅ 并发实测全部完成，历史排行已更新！`)
        await this.fetchSpeedTestHistory()
        await this.fetchComparisonMatrix()
        return res.data
      } catch (e) {
        this.speedLogMessages.push(`[${new Date().toLocaleTimeString()}] ❌ 测速任务发生异常`)
        return []
      } finally {
        this.isSpeedTesting = false
      }
    },

    toggleCurrency() {
      this.currency = this.currency === 'USD' ? 'CNY' : 'USD'
    },

    toggleSidebar() {
      this.isSidebarCollapsed = !this.isSidebarCollapsed
      localStorage.setItem('welltoken_sidebar_collapsed', String(this.isSidebarCollapsed))
    },

    setSidebarCollapsed(collapsed: boolean) {
      this.isSidebarCollapsed = collapsed
      localStorage.setItem('welltoken_sidebar_collapsed', String(collapsed))
    },

    connectWebSocket() {
      if (this.ws) {
        this.ws.close()
      }
      try {
        this.ws = new WebSocket(this.wsUrl)
        this.ws.onopen = async () => {
          this.isConnected = true
          this.backendHealthy = true
          await this.fetchSyncStatus()
          await this.fetchRelaySites()
          await this.fetchModelsCatalog()
        }
        this.ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'SYNC_PROGRESS') {
              this.syncProgress.visible = true
              this.syncProgress.stage = msg.stage
              this.syncProgress.progress = msg.progress
              this.syncProgress.message = msg.message
              this.syncProgress.detail = msg.detail
              if (msg.stats && Object.keys(msg.stats).length > 0) {
                this.syncProgress.stats = msg.stats
              }
              if (msg.stage === 5) {
                this.syncProgress.isSyncing = false
              } else if (msg.stage === -1) {
                this.syncProgress.isSyncing = false
                this.syncProgress.error = msg.message
              } else {
                this.syncProgress.isSyncing = true
              }
            } else if (msg.type === 'matrix_update' || msg.type === 'init') {
              this.comparisonMatrix = msg.data
            } else if (msg.type === 'speed_test_event') {
              const ev = msg.data as SpeedTestStreamEvent
              this.currentSpeedStream[ev.site_id] = ev
              if (ev.event === 'token' && ev.content_delta) {
                this.speedLogMessages.push(`[${ev.site_name}] 收到 Token: "${ev.content_delta}" (瞬时 TPS: ${ev.instant_tps})`)
                if (this.speedLogMessages.length > 50) this.speedLogMessages.shift()
              }
            }
          } catch (e) {
            console.error('WS message error:', e)
          }
        }
        this.ws.onclose = () => {
          this.isConnected = false
          setTimeout(() => this.connectWebSocket(), 3000)
        }
        this.ws.onerror = () => {
          this.isConnected = false
          this.ws?.close()
        }
      } catch (e) {
        setTimeout(() => this.connectWebSocket(), 3000)
      }
    },

    // ==================== macOS iCloud 同步 Actions ====================
    saveICloudConfig(config: ICloudSyncConfig) {
      this.icloudConfig = { ...config }
      localStorage.setItem('welltoken_icloud_config', JSON.stringify(this.icloudConfig))
    },

    async fetchICloudStatus() {
      try {
        const res = await axios.get<ICloudSyncStatus>(`${this.apiUrl}/api/v1/icloud/status`)
        this.icloudStatus = res.data
        return res.data
      } catch (e) {
        console.error('Fetch iCloud status failed:', e)
        return null
      }
    },

    async fetchICloudBackups() {
      try {
        const res = await axios.get<{ backups: ICloudBackupItem[]; count: number }>(`${this.apiUrl}/api/v1/icloud/backups`)
        this.icloudBackups = res.data.backups
        return res.data.backups
      } catch (e) {
        console.error('Fetch iCloud backups failed:', e)
        return []
      }
    },

    async pushToICloud(customPassword?: string): Promise<{ success: boolean; message: string; error?: string }> {
      this.isICloudSyncing = true
      try {
        const pwd = customPassword !== undefined ? customPassword : (this.icloudConfig.usePassword ? this.icloudConfig.password : undefined)
        const res = await axios.post(`${this.apiUrl}/api/v1/icloud/push`, {
          sync_modules: this.icloudConfig.modules,
          include_api_keys: this.icloudConfig.includeApiKeys,
          password: pwd || undefined,
          favorites_data: {
            favorite_site_ids: this.favoriteSiteIds
          }
        })
        await this.fetchICloudStatus()
        await this.fetchICloudBackups()
        return { success: true, message: res.data.message || '推送到 iCloud 成功' }
      } catch (e: any) {
        const msg = e.response?.data?.detail || e.message
        return { success: false, message: '推送到 iCloud 失败', error: msg }
      } finally {
        this.isICloudSyncing = false
      }
    },

    async pullFromICloud(customPassword?: string): Promise<{ success: boolean; message: string; report?: any; error?: string }> {
      this.isICloudSyncing = true
      try {
        const pwd = customPassword !== undefined ? customPassword : (this.icloudConfig.usePassword ? this.icloudConfig.password : undefined)
        const res = await axios.post(`${this.apiUrl}/api/v1/icloud/pull`, {
          password: pwd || undefined
        })
        
        // 如果云端恢复了收藏夹
        if (res.data.favorites?.favorite_site_ids && Array.isArray(res.data.favorites.favorite_site_ids)) {
          this.favoriteSiteIds = res.data.favorites.favorite_site_ids
          localStorage.setItem('welltoken_fav_sites', JSON.stringify(this.favoriteSiteIds))
        }

        await this.fetchComparisonMatrix()
        await this.fetchRelaySites()
        await this.fetchModelsCatalog()
        await this.fetchSyncStatus()
        await this.fetchICloudStatus()
        await this.fetchICloudBackups()
        return { success: true, message: '从 iCloud 拉取合并完成', report: res.data.report }
      } catch (e: any) {
        const msg = e.response?.data?.detail || e.message
        return { success: false, message: '从 iCloud 拉取失败', error: msg }
      } finally {
        this.isICloudSyncing = false
      }
    },

    async restoreICloudBackup(filename: string, customPassword?: string): Promise<{ success: boolean; message: string; error?: string }> {
      this.isICloudSyncing = true
      try {
        const pwd = customPassword !== undefined ? customPassword : (this.icloudConfig.usePassword ? this.icloudConfig.password : undefined)
        const res = await axios.post(`${this.apiUrl}/api/v1/icloud/restore`, {
          backup_filename: filename,
          password: pwd || undefined
        })

        if (res.data.details?.favorites?.favorite_site_ids) {
          this.favoriteSiteIds = res.data.details.favorites.favorite_site_ids
          localStorage.setItem('welltoken_fav_sites', JSON.stringify(this.favoriteSiteIds))
        }

        await this.fetchComparisonMatrix()
        await this.fetchRelaySites()
        await this.fetchModelsCatalog()
        await this.fetchSyncStatus()
        await this.fetchICloudStatus()
        await this.fetchICloudBackups()
        return { success: true, message: `已成功还原备份 [${filename}]` }
      } catch (e: any) {
        const msg = e.response?.data?.detail || e.message
        return { success: false, message: '还原备份失败', error: msg }
      } finally {
        this.isICloudSyncing = false
      }
    },

    async openICloudFolder() {
      if (this.icloudStatus?.sync_folder_path && window.api?.openPath) {
        await window.api.openPath(this.icloudStatus.sync_folder_path)
      } else {
        try {
          await axios.post(`${this.apiUrl}/api/v1/icloud/open-finder`)
        } catch (e) {
          console.error('Open finder failed:', e)
        }
      }
    },

    async exportLocalBundle(password?: string): Promise<any> {
      const res = await axios.post(`${this.apiUrl}/api/v1/icloud/export-bundle`, {
        sync_modules: this.icloudConfig.modules,
        include_api_keys: this.icloudConfig.includeApiKeys,
        password: password || (this.icloudConfig.usePassword ? this.icloudConfig.password : undefined),
        favorites_data: {
          favorite_site_ids: this.favoriteSiteIds
        }
      })
      return res.data
    },

    async importLocalBundle(bundle: any, password?: string): Promise<{ success: boolean; message: string; report?: any; error?: string }> {
      try {
        const res = await axios.post(`${this.apiUrl}/api/v1/icloud/import-bundle`, {
          bundle,
          password: password || (this.icloudConfig.usePassword ? this.icloudConfig.password : undefined)
        })
        if (res.data.favorites?.favorite_site_ids) {
          this.favoriteSiteIds = res.data.favorites.favorite_site_ids
          localStorage.setItem('welltoken_fav_sites', JSON.stringify(this.favoriteSiteIds))
        }
        await this.fetchComparisonMatrix()
        await this.fetchRelaySites()
        await this.fetchModelsCatalog()
        await this.fetchSyncStatus()
        return { success: true, message: res.data.message || '导入成功', report: res.data.report }
      } catch (e: any) {
        const msg = e.response?.data?.detail || e.message
        return { success: false, message: '导入失败', error: msg }
      }
    },

    async triggerAutoICloudSyncIfEnabled() {
      if (this.icloudConfig.autoSync && this.icloudStatus?.icloud_available) {
        try {
          await this.pushToICloud()
        } catch (e) {
          console.warn('Auto iCloud sync failed in background:', e)
        }
      }
    }
  }
})
