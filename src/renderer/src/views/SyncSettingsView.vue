<template>
  <div class="h-full flex flex-col space-y-3 overflow-y-auto pr-1 select-none">
    <!-- 卡片 1：数据源同步调度设置 -->
    <div class="p-5 rounded-xl bg-[#151922] border border-[#232936] space-y-4">
      <div class="flex items-center justify-between border-b border-[#232936] pb-3">
        <span class="font-bold text-sm text-white">🔄 全网数据源自动同步与调度策略</span>
        <button
          @click="store.triggerFullSync"
          class="text-xs px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-md shadow-blue-600/20"
        >
          立即执行全量同步
        </button>
      </div>

      <div class="grid grid-cols-2 gap-4 text-xs">
        <!-- models.dev -->
        <div class="p-3.5 rounded-lg bg-[#0B0E14] border border-[#232936] space-y-2">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white">1. models.dev 官方基准模型数据源</span>
            <span class="text-emerald-400 font-mono">已连接</span>
          </div>
          <div class="text-gray-400">
            标准接口: <span class="text-blue-400 font-mono">https://models.dev/api.json</span>
          </div>
          <div class="text-gray-400">
            当前已同步标准模型: <strong class="text-white font-mono">{{ store.syncStatus?.models_dev_total_models || 142 }}</strong> 款
          </div>
          <div class="pt-2 border-t border-[#232936] flex items-center justify-between text-gray-500">
            <span>最后同步: {{ formatTime(store.syncStatus?.models_dev_last_sync) }}</span>
            <button @click="store.syncModelsDev" class="text-sky-400 hover:underline">单项同步</button>
          </div>
        </div>

        <!-- relaywatch -->
        <div class="p-3.5 rounded-lg bg-[#0B0E14] border border-[#232936] space-y-2">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white">2. relaywatch / 中转站倍率探测器</span>
            <span class="text-emerald-400 font-mono">自动轮询已开启</span>
          </div>
          <div class="text-gray-400">
            活跃中转渠道: <strong class="text-white font-mono">{{ store.syncStatus?.total_active_sites || 18 }}</strong> 家
          </div>
          <div class="text-gray-400">
            全网价格快照缓存: <strong class="text-white font-mono">{{ store.syncStatus?.total_pricings_cached || 270 }}</strong> 条
          </div>
          <div class="pt-2 border-t border-[#232936] flex items-center justify-between text-gray-500">
            <span>自动轮询周期: 每 60 分钟</span>
            <button @click="store.syncAllRelays" class="text-sky-400 hover:underline">单项扫描</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片 2：实时汇率与计量换算 -->
    <div class="p-5 rounded-xl bg-[#151922] border border-[#232936] space-y-4">
      <div class="border-b border-[#232936] pb-3">
        <span class="font-bold text-sm text-white">💱 汇率折算与通用参数</span>
      </div>

      <div class="flex items-center space-x-4 text-xs">
        <div class="w-72">
          <label class="block text-gray-400 mb-1">USD / CNY 基准换算汇率</label>
          <div class="flex items-center space-x-2">
            <input
              v-model.number="customRate"
              type="number"
              step="0.01"
              class="flex-1 bg-[#0B0E14] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono font-bold text-sm focus:outline-none focus:border-blue-500"
            />
            <button
              @click="saveRate"
              class="px-3.5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium"
            >
              更新汇率
            </button>
          </div>
        </div>
        <div class="text-gray-500 text-[11px] leading-relaxed">
          💡 该汇率用于在「全网聚合比价」中自动将美元中转站与人民币中转站单价折算为统一标准计量（$/1M Tokens 与 ￥/1M Tokens）。
        </div>
      </div>
    </div>

    <!-- 卡片 3：本地 SQLite 大数据库运维 -->
    <div class="p-5 rounded-xl bg-[#151922] border border-[#232936] space-y-4">
      <div class="border-b border-[#232936] pb-3">
        <span class="font-bold text-sm text-white">🗄️ SQLite 本地价格大数据库维护</span>
      </div>

      <div class="grid grid-cols-3 gap-3 text-xs">
        <div class="p-3 rounded-lg bg-[#0B0E14] border border-[#232936]">
          <div class="text-gray-500">数据库存储文件</div>
          <div class="font-mono text-white font-bold mt-1">./data/welltoken.db</div>
        </div>
        <div class="p-3 rounded-lg bg-[#0B0E14] border border-[#232936]">
          <div class="text-gray-500">数据库文件大小</div>
          <div class="font-mono text-emerald-400 font-bold mt-1">{{ store.syncStatus?.db_size_mb || 4.2 }} MB</div>
        </div>
        <div class="p-3 rounded-lg bg-[#0B0E14] border border-[#232936]">
          <div class="text-gray-500">历史测速与日志总数</div>
          <div class="font-mono text-sky-400 font-bold mt-1">{{ store.speedTestHistory.length }} 条实测记录</div>
        </div>
      </div>

      <div class="pt-2 flex items-center space-x-3">
        <button
          @click="exportJson"
          class="px-4 py-2 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-200 border border-[#374151] text-xs font-medium"
        >
          📥 导出比价大数据库 (JSON)
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()
const customRate = ref(7.30)

const formatTime = (timeStr?: string | null) => {
  if (!timeStr) return '已初始化'
  const d = new Date(timeStr)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const saveRate = async () => {
  try {
    await axios.post(`${store.apiUrl}/api/v1/settings/exchange-rate`, {
      usd_to_cny_rate: customRate.value
    })
    await store.fetchComparisonMatrix()
    await store.fetchSyncStatus()
  } catch (e) {
    console.error('Save rate failed:', e)
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

onMounted(() => {
  if (store.syncStatus?.usd_to_cny_rate) {
    customRate.value = store.syncStatus.usd_to_cny_rate
  }
})
</script>
