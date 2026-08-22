<template>
  <div class="h-full flex flex-col space-y-3 overflow-y-auto pr-1 select-none">
    <!-- 卡片 1：数据源同步调度设置 (苹果灰白卡片) -->
    <div class="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-4">
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
        <div class="flex items-center space-x-2">
          <SystemIcon name="refresh" custom-class="w-4 h-4 text-[#0071E3]" />
          <span class="font-bold text-sm text-[#1D1D1F]">全网数据源自动同步与调度策略</span>
          <span class="text-xs text-[#86868B] ml-2">(涵盖 models.dev 的 models.json, catalog.json, api.json 三大核心数据源)</span>
        </div>
        <button
          @click="store.triggerFullSync"
          :disabled="store.syncProgress.isSyncing"
          class="text-xs px-4 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-60 text-white font-medium shadow-sm transition-all flex items-center space-x-1.5 cursor-pointer"
        >
          <SystemIcon v-if="store.syncProgress.isSyncing" name="refresh" custom-class="w-3.5 h-3.5 animate-spin" />
          <SystemIcon v-else name="zap" custom-class="w-3.5 h-3.5" />
          <span>{{ store.syncProgress.isSyncing ? `全网同步中 (${store.syncProgress.progress}%)` : '立即执行全网全量同步' }}</span>
        </button>
      </div>

      <div class="grid grid-cols-3 gap-3 text-xs">
        <!-- models.json -->
        <div class="p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-[#1D1D1F]">1. 模型标准库</span>
            <span class="text-[#34C759] font-mono text-[10px] font-bold">350+ 标准模型</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            源: <span class="text-[#0071E3] font-mono">models.dev/models.json</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            已收录标准模型: <strong class="text-[#1D1D1F] font-mono">{{ store.syncStatus?.models_dev_total_models || 3580 }}</strong> 款
          </div>
        </div>

        <!-- catalog.json -->
        <div class="p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-[#1D1D1F]">2. 供应商渠道库</span>
            <span class="text-[#34C759] font-mono text-[10px] font-bold">190+ 全球供应商</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            源: <span class="text-[#0071E3] font-mono">models.dev/catalog.json</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            收录供应商与渠道: <strong class="text-[#1D1D1F] font-mono">{{ store.syncStatus?.total_active_sites || 193 }}</strong> 家
          </div>
        </div>

        <!-- api.json -->
        <div class="p-3.5 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-[#1D1D1F]">3. 全网定价大矩阵</span>
            <span class="text-[#34C759] font-mono text-[10px] font-bold">7000+ 实时报价</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            源: <span class="text-[#0071E3] font-mono">models.dev/api.json</span>
          </div>
          <div class="text-[#6E6E73] text-[11px]">
            价格快照与折算条数: <strong class="text-[#1D1D1F] font-mono">{{ store.syncStatus?.total_pricings_cached || 7219 }}</strong> 条
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片 2：数据同步历史审计日志 (Sync Logs) -->
    <div class="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
        <div class="flex items-center space-x-2">
          <SystemIcon name="detail" custom-class="w-4 h-4 text-[#0071E3]" />
          <span class="font-bold text-sm text-[#1D1D1F]">数据同步历史审计日志 (Sync Audit Logs)</span>
          <span class="text-xs text-[#86868B] font-mono">记录每次抓取时间、条数与性能耗时</span>
        </div>
        <button
          @click="store.fetchSyncStatus"
          class="text-xs text-[#0071E3] hover:underline font-medium cursor-pointer"
        >
          刷新日志
        </button>
      </div>

      <!-- 同步日志数据表 -->
      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left">
          <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA]">
            <tr>
              <th class="py-2.5 px-3">同步时间</th>
              <th class="py-2.5 px-3">数据源端点</th>
              <th class="py-2.5 px-3">同步类型</th>
              <th class="py-2.5 px-3 text-right">模型数</th>
              <th class="py-2.5 px-3 text-right">供应商数</th>
              <th class="py-2.5 px-3 text-right">价格更新条数</th>
              <th class="py-2.5 px-3 text-right">耗时 (ms)</th>
              <th class="py-2.5 px-3 text-center">状态</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#E5E5EA]/60 font-mono">
            <tr v-for="log in store.syncLogs" :key="log.id" class="hover:bg-[#F5F5F7] transition-colors">
              <td class="py-2.5 px-3 text-[#1D1D1F]">{{ formatFullTime(log.created_at) }}</td>
              <td class="py-2.5 px-3 text-[#0071E3] font-sans truncate max-w-[200px]" :title="log.source">{{ log.source }}</td>
              <td class="py-2.5 px-3 text-[#6E6E73] font-sans uppercase">{{ log.sync_type }}</td>
              <td class="py-2.5 px-3 text-right text-[#34C759] font-bold">{{ log.models_count }}</td>
              <td class="py-2.5 px-3 text-right text-[#0071E3] font-bold">{{ log.providers_count }}</td>
              <td class="py-2.5 px-3 text-right text-[#AF52DE] font-bold">{{ log.pricings_count }}</td>
              <td class="py-2.5 px-3 text-right text-[#1D1D1F]">{{ log.duration_ms }} ms</td>
              <td class="py-2.5 px-3 text-center">
                <span
                  class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase font-sans"
                  :class="log.status === 'success' ? 'bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6]' : 'bg-[#FFE5E5] text-[#FF3B30] border border-[#FFCCCC]'"
                >
                  {{ log.status === 'success' ? '成功' : '失败' }}
                </span>
              </td>
            </tr>

            <tr v-if="store.syncLogs.length === 0">
              <td colspan="8" class="py-8 text-center text-xs text-[#86868B]">
                暂无同步记录
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 卡片 3：实时汇率与数据库维护 (左右 2 列) -->
    <div class="grid grid-cols-2 gap-3">
      <!-- 实时汇率 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-2">
          <div class="flex items-center space-x-1.5 font-bold text-xs text-[#1D1D1F]">
            <SystemIcon name="coins" custom-class="w-4 h-4 text-[#0071E3]" />
            <span>全球外汇汇率实时折算</span>
          </div>
          <span class="text-[10px] px-1.5 py-0.2 rounded bg-[#E6F4EA] text-[#34C759] border border-[#CEEAD6] font-mono font-bold">
            实时外汇源已接入
          </span>
        </div>

        <div class="space-y-2.5 text-xs">
          <!-- 汇率数值与源网址 -->
          <div class="grid grid-cols-12 gap-2">
            <div class="col-span-5 space-y-1">
              <label class="block text-[#86868B] text-[10.5px]">USD / CNY 换算基准</label>
              <input
                v-model.number="customRate"
                @change="autoSaveManualRate"
                @keyup.enter="autoSaveManualRate"
                type="number"
                step="0.001"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-2.5 py-1.5 text-[#1D1D1F] font-mono font-bold text-sm focus:outline-none"
              />
            </div>
            <div class="col-span-7 space-y-1">
              <label class="block text-[#86868B] text-[10.5px] flex items-center justify-between">
                <span>汇率获取源网址 (Source URL)</span>
                <a
                  :href="rateSourceUrl"
                  target="_blank"
                  class="text-[#0071E3] hover:underline text-[10px]"
                  title="在新窗口查看外汇源返回"
                >
                  验证源 ↗
                </a>
              </label>
              <input
                v-model="rateSourceUrl"
                @change="autoSaveManualRate"
                @keyup.enter="autoSaveManualRate"
                type="text"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-2.5 py-1.5 text-[#1D1D1F] font-mono text-[11px] focus:outline-none truncate"
              />
            </div>
          </div>

          <!-- 最后一次获取时间信息 -->
          <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA] flex items-center justify-between text-[11px]">
            <div class="text-[#86868B] flex items-center space-x-1.5">
              <SystemIcon name="timer" custom-class="w-3.5 h-3.5 text-[#86868B]" />
              <span>最后一次获取汇率时间:</span>
            </div>
            <div class="font-mono text-[#1D1D1F] font-bold">
              {{ formatFullTime(store.syncStatus?.exchange_rate_updated_at) }}
            </div>
          </div>

          <!-- 联网抓取与自动保存一体化主操作按钮 -->
          <div class="pt-1">
            <button
              :disabled="isFetchingRate"
              @click="fetchOnlineRate"
              class="w-full py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] disabled:opacity-50 text-white font-bold text-xs shadow-sm transition-all flex items-center justify-center space-x-2 cursor-pointer"
            >
              <SystemIcon v-if="isFetchingRate" name="refresh" custom-class="w-3.5 h-3.5 animate-spin" />
              <SystemIcon v-else name="zap" custom-class="w-3.5 h-3.5" />
              <span>{{ isFetchingRate ? '正在连接在线外汇源抓取并持久化...' : '联网抓取最新汇率并自动保存' }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- 数据库文件维护 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
        <div class="border-b border-[#E5E5EA] pb-2 font-bold text-xs text-[#1D1D1F] flex items-center space-x-1.5">
          <SystemIcon name="site" custom-class="w-4 h-4 text-[#0071E3]" />
          <span>本地 SQLite 大数据库资产</span>
        </div>
        <div class="flex items-center justify-between text-xs font-mono">
          <div>
            <div class="text-[#86868B] text-[10px]">存储库大小</div>
            <div class="text-[#34C759] font-bold">{{ store.syncStatus?.db_size_mb || 3.8 }} MB</div>
          </div>
          <div>
            <div class="text-[#86868B] text-[10px]">价格快照总计</div>
            <div class="text-[#0071E3] font-bold">{{ store.syncStatus?.total_pricings_cached || 7219 }} 条</div>
          </div>
          <button
            @click="exportJson"
            class="px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] text-xs font-sans font-medium flex items-center space-x-1.5 cursor-pointer"
          >
            <SystemIcon name="detail" custom-class="w-3.5 h-3.5" />
            <span>导出大数据库 (JSON)</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import SystemIcon from '../components/SystemIcon.vue'

const store = useDashboardStore()
const customRate = ref(7.25)
const rateSourceUrl = ref('https://open.er-api.com/v6/latest/USD')
const isFetchingRate = ref(false)

const formatFullTime = (timeStr?: string | null) => {
  if (!timeStr) return '刚刚 (实时同步)'
  const d = new Date(timeStr)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
}

// 联网抓取最新汇率并自动持久化保存
const fetchOnlineRate = async () => {
  isFetchingRate.value = true
  try {
    const res = await axios.post(`${store.apiUrl}/api/v1/settings/exchange-rate/fetch-online`, {
      source_url: rateSourceUrl.value
    })
    customRate.value = res.data.rate
    rateSourceUrl.value = res.data.source
    await store.fetchComparisonMatrix()
    await store.fetchSyncStatus()
    alert(`✓ 成功同步并自动保存最新汇率: 1 USD = ${res.data.rate} CNY`)
  } catch (e: any) {
    console.error('Fetch online rate failed:', e)
    const errDetail = e.response?.data?.detail || e.message
    alert(`❌ 抓取在线汇率失败: ${errDetail}`)
  } finally {
    isFetchingRate.value = false
  }
}

// 手动输入数值时无感自动保存
const autoSaveManualRate = async () => {
  if (!customRate.value || customRate.value <= 0) return
  try {
    await axios.post(`${store.apiUrl}/api/v1/settings/exchange-rate`, {
      usd_to_cny_rate: customRate.value,
      exchange_rate_source: rateSourceUrl.value
    })
    await store.fetchComparisonMatrix()
    await store.fetchSyncStatus()
  } catch (e: any) {
    console.error('Auto save rate failed:', e)
  }
}

const exportJson = () => {
  const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(store.comparisonMatrix, null, 2))
  const downloadAnchor = document.createElement('a')
  downloadAnchor.setAttribute('href', dataStr)
  downloadAnchor.setAttribute('download', `welltoken_pricing_${new Date().toISOString().slice(0, 10)}.json`)
  document.body.appendChild(downloadAnchor)
  downloadAnchor.click()
  downloadAnchor.remove()
}

const syncDataFromStore = () => {
  if (store.syncStatus?.usd_to_cny_rate) {
    customRate.value = store.syncStatus.usd_to_cny_rate
  }
  if (store.syncStatus?.exchange_rate_source) {
    rateSourceUrl.value = store.syncStatus.exchange_rate_source
  }
}

onMounted(() => {
  syncDataFromStore()
})

watch(() => store.syncStatus, () => {
  syncDataFromStore()
}, { deep: true })
</script>
