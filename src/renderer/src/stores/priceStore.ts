import { defineStore } from 'pinia'
import axios from 'axios'
import type { TokenPriceSummary, KlinePoint, OrderBookDepth, SystemHealth } from '../types'

export const usePriceStore = defineStore('price', {
  state: () => ({
    apiUrl: 'http://127.0.0.1:8765',
    wsUrl: 'ws://127.0.0.1:8765/api/v1/price/ws',
    isConnected: false,
    backendHealthy: false,
    tokens: [] as TokenPriceSummary[],
    selectedSymbol: 'WELL',
    currentTimeframe: '1m',
    klineData: [] as KlinePoint[],
    depthData: null as OrderBookDepth | null,
    favorites: ['WELL', 'BTC'] as string[],
    previousPrices: {} as Record<string, number>,
    priceDirections: {} as Record<string, 'up' | 'down' | 'same'>,
    searchQuery: '',
    ws: null as WebSocket | null,
    systemInfo: null as SystemHealth | null
  }),

  getters: {
    selectedToken(state): TokenPriceSummary | undefined {
      return state.tokens.find((t) => t.symbol === state.selectedSymbol) || state.tokens[0]
    },
    filteredTokens(state): TokenPriceSummary[] {
      let list = state.tokens
      if (state.searchQuery.trim()) {
        const q = state.searchQuery.toLowerCase()
        list = list.filter(
          (t) => t.symbol.toLowerCase().includes(q) || t.name.toLowerCase().includes(q)
        )
      }
      return list
    },
    favoriteTokens(state): TokenPriceSummary[] {
      return state.tokens.filter((t) => state.favorites.includes(t.symbol))
    }
  },

  actions: {
    async initConfig() {
      if (window.api && window.api.getBackendConfig) {
        try {
          const config = await window.api.getBackendConfig()
          this.apiUrl = config.apiUrl
          this.wsUrl = config.wsUrl
        } catch (e) {
          console.warn('Electron IPC config fallback:', e)
        }
      }
    },

    async checkHealth() {
      try {
        const res = await axios.get<SystemHealth>(`${this.apiUrl}/api/v1/system/health`, {
          timeout: 2000
        })
        this.backendHealthy = res.data.status === 'ok'
        this.systemInfo = res.data
      } catch {
        this.backendHealthy = false
      }
    },

    async fetchSummaries() {
      try {
        const res = await axios.get<TokenPriceSummary[]>(`${this.apiUrl}/api/v1/price/summary`)
        this.updateTokenList(res.data)
      } catch (err) {
        console.error('Fetch summaries failed:', err)
      }
    },

    async fetchKline(symbol?: string, timeframe?: string) {
      const sym = symbol || this.selectedSymbol
      const tf = timeframe || this.currentTimeframe
      try {
        const res = await axios.get<KlinePoint[]>(`${this.apiUrl}/api/v1/price/kline`, {
          params: { symbol: sym, timeframe: tf, limit: 120 }
        })
        this.klineData = res.data
      } catch (err) {
        console.error('Fetch kline failed:', err)
      }
    },

    async fetchDepth(symbol?: string) {
      const sym = symbol || this.selectedSymbol
      try {
        const res = await axios.get<OrderBookDepth>(`${this.apiUrl}/api/v1/price/depth`, {
          params: { symbol: sym, levels: 15 }
        })
        this.depthData = res.data
      } catch (err) {
        console.error('Fetch depth failed:', err)
      }
    },

    updateTokenList(newList: TokenPriceSummary[]) {
      for (const item of newList) {
        const prev = this.previousPrices[item.symbol]
        if (prev !== undefined) {
          if (item.price > prev) {
            this.priceDirections[item.symbol] = 'up'
          } else if (item.price < prev) {
            this.priceDirections[item.symbol] = 'down'
          } else {
            this.priceDirections[item.symbol] = 'same'
          }
        }
        this.previousPrices[item.symbol] = item.price
      }
      this.tokens = newList
    },

    selectToken(symbol: string) {
      this.selectedSymbol = symbol
      this.fetchKline(symbol, this.currentTimeframe)
      this.fetchDepth(symbol)
    },

    setTimeframe(tf: string) {
      this.currentTimeframe = tf
      this.fetchKline(this.selectedSymbol, tf)
    },

    toggleFavorite(symbol: string) {
      if (this.favorites.includes(symbol)) {
        this.favorites = this.favorites.filter((s) => s !== symbol)
      } else {
        this.favorites.push(symbol)
      }
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
          console.log('[WebSocket] Connected to market stream')
        }

        this.ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data)
            if (msg.type === 'price_update' || msg.type === 'init') {
              this.updateTokenList(msg.data)
            }
          } catch (e) {
            console.error('[WebSocket] Parse error:', e)
          }
        }

        this.ws.onclose = () => {
          this.isConnected = false
          console.log('[WebSocket] Disconnected, retrying in 3s...')
          setTimeout(() => this.connectWebSocket(), 3000)
        }

        this.ws.onerror = () => {
          this.isConnected = false
          this.ws?.close()
        }
      } catch (err) {
        console.error('[WebSocket] Init failed:', err)
        setTimeout(() => this.connectWebSocket(), 3000)
      }
    }
  }
})
