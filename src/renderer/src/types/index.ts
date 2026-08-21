export interface ComparisonItem {
  id: number
  model_id: string
  model_name: string
  provider: string
  series: string
  site_id: number
  site_name: string
  group_name?: string
  site_type: string
  is_official: boolean
  model_ratio: number
  calculated_input_usd: number
  calculated_output_usd: number
  calculated_cache_usd: number
  calculated_input_cny: number
  calculated_output_cny: number
  discount_percent: number
  last_tested_tps: number
  site_score: number
  site_status: string
  last_latency_ms: number
  updated_at: string
}

export interface RelaySite {
  id: number
  provider_id?: string
  name: string
  base_url: string
  api_key: string
  site_type: string
  group_name?: string
  recharge_rate: number
  models_endpoint: string
  status_endpoint: string
  website?: string
  doc_url?: string
  env_vars?: string
  is_official_catalog: boolean
  is_active: boolean
  last_status: string
  last_latency_ms: number
  last_sync_time: string
  score: number
  notes: string
  created_at: string
  model_count: number
}

export interface ModelMetadata {
  id: number
  model_id: string
  name: string
  provider: string
  series: string
  family?: string
  context_window: number
  max_output: number
  official_input_price: number
  official_output_price: number
  official_cache_price: number
  modalities: string
  capabilities: string
  open_weights?: boolean
  release_date?: string
  is_featured: boolean
  description: string
  created_at: string
  updated_at: string
  active_relay_count: number
  lowest_price_usd: number
}

export interface SpeedTestResult {
  id: number
  site_id: number
  site_name: string
  site_type: string
  model_id: string
  test_time: string
  ttft_ms: number
  avg_tps: number
  peak_tps: number
  total_latency_ms: number
  prompt_tokens: number
  completion_tokens: number
  is_success: boolean
  error_message: string
  is_authentic: boolean
  jitter_rate: number
  score: number
  grade: string
}

export interface SpeedTestStreamEvent {
  event: 'start' | 'token' | 'done' | 'error'
  site_id: number
  site_name: string
  model_id: string
  current_token_count: number
  current_ttft_ms: number
  current_tps: number
  instant_tps: number
  content_delta?: string
  is_authentic?: boolean
}

export interface SyncLog {
  id: number
  source: string
  sync_type: string
  status: string
  models_count: number
  providers_count: number
  pricings_count: number
  duration_ms: number
  error_message: string
  created_at: string
}

export interface SyncStatus {
  models_dev_last_sync: string | null
  models_dev_total_models: number
  relays_last_sync: string | null
  total_active_sites: number
  total_pricings_cached: number
  usd_to_cny_rate: number
  db_size_mb: number
  recent_sync_logs: SyncLog[]
}
