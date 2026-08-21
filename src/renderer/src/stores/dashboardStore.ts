import { defineStore } from 'pinia'
import axios from 'axios'
import type {
  ComparisonItem,
  RelaySite,
  ModelMetadata,
  SpeedTestResult,
  SpeedTestStreamEvent,
  SyncStatus
} from '../types'

export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    apiUrl: 'http://127.0.0.1:8765',
    wsUrl: 'ws://127.0.0.1:8765/api/v1/price/ws',
    activeTab: 'price-matrix' as 'price-matrix' | 'channels' | 'models' | 'speed-tester' | 'settings',
    currency: 'USD' as 'USD' | 'CNY',
    searchQuery: '',
    selectedProvider: 'all',
    selectedModelId: 'all',
    
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
            item.site_name.toLowerCase().includes(q)
        )
      }
      return list
    },
    featuredModels(state): ModelMetadata[] {
      return state.modelsCatalog.filter((m) => m.is_featured)
    },
    activeSites(state): RelaySite[] {
      return state.relaySites.filter((s) => s.is_active)
    }
  },

  actions: {
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
      try {
        await axios.post(`${this.apiUrl}/api/v1/settings/full-sync`)
        await this.fetchComparisonMatrix()
        await this.fetchRelaySites()
        await this.fetchModelsCatalog()
        await this.fetchSyncStatus()
      } catch (e) {
        console.error('Full sync failed:', e)
      }
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
      } finally {
        this.isSpeedTesting = false
      }
    },

    toggleCurrency() {
      this.currency = this.currency === 'USD' ? 'CNY' : 'USD'
    },

    connectWebSocket() {
      if (this.ws) {
        this.ws.close()
      }
      try {
        this.ws = new WebSocket(this.wsUrl)
        this.ws.onopen = () => {
          this.isConnected = true
          this.backendHealthy = true
        }
        this.ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'matrix_update' || msg.type === 'init') {
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
    }
  }
})
