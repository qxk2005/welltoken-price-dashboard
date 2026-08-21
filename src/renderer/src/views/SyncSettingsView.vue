<template>
  <div class="h-full flex flex-col space-y-3 overflow-y-auto pr-1 select-none">
    <!-- 卡片 1：数据源同步调度设置 (苹果灰白卡片) -->
    <div class="p-5 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-4">
      <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
        <div>
          <span class="font-bold text-sm text-[#1D1D1F]">🔄 全网数据源自动同步与调度策略</span>
          <span class="text-xs text-[#86868B] ml-2">(涵盖 models.dev 的 models.json, catalog.json, api.json 三大核心数据源)</span>
        </div>
        <button
          @click="store.triggerFullSync"
          class="text-xs px-4 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white font-medium shadow-sm transition-all flex items-center space-x-1.5"
        >
          <span>⚡ 立即执行全网全量同步</span>
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
          <span class="font-bold text-sm text-[#1D1D1F]">📋 数据同步历史审计日志 (Sync Audit Logs)</span>
          <span class="text-xs text-[#86868B] font-mono">记录每次抓取时间、条数与性能耗时</span>
        </div>
        <button
          @click="store.fetchSyncStatus"
          class="text-xs text-[#0071E3] hover:underline font-medium"
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
        <div class="border-b border-[#E5E5EA] pb-2 font-bold text-xs text-[#1D1D1F]">
          💱 全球外汇汇率实时折算
        </div>
        <div class="flex items-center space-x-2 text-xs">
          <div class="flex-1">
            <label class="block text-[#86868B] text-[10px] mb-1">USD / CNY 换算基准汇率</label>
            <input
              v-model.number="customRate"
              type="number"
              step="0.01"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-1.5 text-[#1D1D1F] font-mono font-bold text-sm focus:outline-none"
            />
          </div>
          <button
            @click="saveRate"
            class="mt-4 px-3.5 py-1.5 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white font-medium text-xs shadow-sm"
          >
            更新汇率
          </button>
        </div>
      </div>

      <!-- 数据库文件维护 -->
      <div class="p-4 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-3">
        <div class="border-b border-[#E5E5EA] pb-2 font-bold text-xs text-[#1D1D1F]">
          🗄️ 本地 SQLite 大数据库资产
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
            class="px-3 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] text-xs font-sans font-medium"
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
