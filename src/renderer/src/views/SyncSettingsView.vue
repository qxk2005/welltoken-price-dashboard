<template>
  <div class="h-full flex flex-col space-y-3 overflow-y-auto pr-1 select-none">
    <!-- 卡片 1：数据源同步调度设置 -->
    <div class="p-5 rounded-xl bg-[#151922] border border-[#232936] space-y-4">
      <div class="flex items-center justify-between border-b border-[#232936] pb-3">
        <div>
          <span class="font-bold text-sm text-white">🔄 全网数据源自动同步与调度策略</span>
          <span class="text-xs text-gray-400 ml-2">(涵盖 models.dev 的 models.json, catalog.json, api.json 三大核心数据源)</span>
        </div>
        <button
          @click="store.triggerFullSync"
          class="text-xs px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-md shadow-blue-600/20 flex items-center space-x-1.5"
        >
          <span>⚡ 立即执行全网全量同步</span>
        </button>
      </div>

      <div class="grid grid-cols-3 gap-3 text-xs">
        <!-- models.json -->
        <div class="p-3.5 rounded-lg bg-[#0B0E14] border border-[#232936] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white">1. 模型标准库</span>
            <span class="text-emerald-400 font-mono text-[10px]">350+ 标准模型</span>
          </div>
          <div class="text-gray-400 text-[11px]">
            源: <span class="text-blue-400 font-mono">models.dev/models.json</span>
          </div>
          <div class="text-gray-400 text-[11px]">
            已收录标准模型: <strong class="text-white font-mono">{{ store.syncStatus?.models_dev_total_models || 3580 }}</strong> 款
          </div>
        </div>

        <!-- catalog.json -->
        <div class="p-3.5 rounded-lg bg-[#0B0E14] border border-[#232936] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white">2. 供应商渠道库</span>
            <span class="text-emerald-400 font-mono text-[10px]">190+ 全球供应商</span>
          </div>
          <div class="text-gray-400 text-[11px]">
            源: <span class="text-blue-400 font-mono">models.dev/catalog.json</span>
          </div>
          <div class="text-gray-400 text-[11px]">
            收录供应商与渠道: <strong class="text-white font-mono">{{ store.syncStatus?.total_active_sites || 193 }}</strong> 家
          </div>
        </div>

        <!-- api.json -->
        <div class="p-3.5 rounded-lg bg-[#0B0E14] border border-[#232936] space-y-1.5">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white">3. 全网定价大矩阵</span>
            <span class="text-emerald-400 font-mono text-[10px]">7000+ 实时报价</span>
          </div>
          <div class="text-gray-400 text-[11px]">
            源: <span class="text-blue-400 font-mono">models.dev/api.json</span>
          </div>
          <div class="text-gray-400 text-[11px]">
            价格快照与折算条数: <strong class="text-white font-mono">{{ store.syncStatus?.total_pricings_cached || 7219 }}</strong> 条
          </div>
        </div>
      </div>
    </div>

    <!-- 卡片 2：数据同步历史审计日志 (Sync Logs) -->
    <div class="p-5 rounded-xl bg-[#151922] border border-[#232936] space-y-3">
      <div class="flex items-center justify-between border-b border-[#232936] pb-3">
        <div class="flex items-center space-x-2">
          <span class="font-bold text-sm text-white">📋 数据同步历史审计日志 (Sync Audit Logs)</span>
          <span class="text-xs text-gray-500 font-mono">记录每次抓取时间、条数与性能耗时</span>
        </div>
        <button
          @click="store.fetchSyncStatus"
          class="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          刷新日志
        </button>
      </div>

      <!-- 同步日志数据表 -->
      <div class="overflow-x-auto">
        <table class="w-full text-xs text-left">
          <thead class="text-[11px] text-gray-400 bg-[#0B0E14] border-b border-[#232936]">
            <tr>
              <th class="py-2 px-3">同步时间</th>
              <th class="py-2 px-3">数据源端点</th>
              <th class="py-2 px-3">同步类型</th>
              <th class="py-2 px-3 text-right">模型数</th>
              <th class="py-2 px-3 text-right">供应商数</th>
              <th class="py-2 px-3 text-right">价格更新条数</th>
              <th class="py-2 px-3 text-right">耗时 (ms)</th>
              <th class="py-2 px-3 text-center">状态</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[#232936]/40 font-mono">
            <tr v-for="log in store.syncLogs" :key="log.id" class="hover:bg-[#1A202C] transition-colors">
              <td class="py-2.5 px-3 text-gray-300">{{ formatFullTime(log.created_at) }}</td>
              <td class="py-2.5 px-3 text-sky-400 font-sans truncate max-w-[200px]" :title="log.source">{{ log.source }}</td>
              <td class="py-2.5 px-3 text-gray-400 font-sans uppercase">{{ log.sync_type }}</td>
              <td class="py-2.5 px-3 text-right text-emerald-400 font-bold">{{ log.models_count }}</td>
              <td class="py-2.5 px-3 text-right text-blue-400 font-bold">{{ log.providers_count }}</td>
              <td class="py-2.5 px-3 text-right text-purple-400 font-bold">{{ log.pricings_count }}</td>
              <td class="py-2.5 px-3 text-right text-gray-300">{{ log.duration_ms }} ms</td>
              <td class="py-2.5 px-3 text-center">
                <span
                  class="px-2 py-0.5 rounded text-[10px] font-bold uppercase font-sans"
                  :class="log.status === 'success' ? 'bg-emerald-500/15 text-emerald-400' : 'bg-rose-500/15 text-rose-400'"
                >
                  {{ log.status === 'success' ? '成功' : '失败' }}
                </span>
              </td>
            </tr>

            <tr v-if="store.syncLogs.length === 0">
              <td colspan="8" class="py-8 text-center text-xs text-gray-500">
                暂无同步记录
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 卡片 3：实时汇率与数据库维护 -->
    <div class="grid grid-cols-2 gap-3">
      <!-- 实时汇率 -->
      <div class="p-4 rounded-xl bg-[#151922] border border-[#232936] space-y-3">
        <div class="border-b border-[#232936] pb-2 font-bold text-xs text-white">
          💱 全球外汇汇率实时折算
        </div>
        <div class="flex items-center space-x-2 text-xs">
          <div class="flex-1">
            <label class="block text-gray-500 text-[10px] mb-1">USD / CNY 换算基准汇率</label>
            <input
              v-model.number="customRate"
              type="number"
              step="0.01"
              class="w-full bg-[#0B0E14] border border-[#2D3748] rounded-lg px-3 py-1.5 text-white font-mono font-bold text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            @click="saveRate"
            class="mt-4 px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs"
          >
            更新汇率
          </button>
        </div>
      </div>

      <!-- 数据库文件维护 -->
      <div class="p-4 rounded-xl bg-[#151922] border border-[#232936] space-y-3">
        <div class="border-b border-[#232936] pb-2 font-bold text-xs text-white">
          🗄️ 本地 SQLite 大数据库资产
        </div>
        <div class="flex items-center justify-between text-xs font-mono">
          <div>
            <div class="text-gray-500 text-[10px]">存储库大小</div>
            <div class="text-emerald-400 font-bold">{{ store.syncStatus?.db_size_mb || 3.8 }} MB</div>
          </div>
          <div>
            <div class="text-gray-500 text-[10px]">价格快照总计</div>
            <div class="text-blue-400 font-bold">{{ store.syncStatus?.total_pricings_cached || 7219 }} 条</div>
          </div>
          <button
            @click="exportJson"
            class="px-3 py-1.5 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-200 border border-[#374151] text-xs font-sans"
          >
            📥 导出大数据库 (JSON)
          </button>
        </div>
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

const formatFullTime = (timeStr?: string | null) => {
  if (!timeStr) return '刚刚'
  const d = new Date(timeStr)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`
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
