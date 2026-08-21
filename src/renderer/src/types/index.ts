export interface TokenPriceSummary {
  symbol: string
  name: string
  price: number
  change_24h: number
  high_24h: number
  low_24h: number
  volume_24h: number
  market_cap: number
  timestamp: string
  sparkline: number[]
}

export interface KlinePoint {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface DepthLevel {
  price: number
  amount: number
  total: number
}

export interface OrderBookDepth {
  symbol: string
  timestamp: number
  bids: DepthLevel[]
  asks: DepthLevel[]
}

export interface SystemHealth {
  status: string
  app: string
  version: string
  uptime_seconds: number
  database_connected: boolean
}
