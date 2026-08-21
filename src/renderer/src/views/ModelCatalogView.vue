<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部厂商 Tab 切换 -->
    <div class="p-3 rounded-xl bg-[#151922] border border-[#232936] flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-xs font-bold text-gray-400">厂商筛选:</span>
        <div class="flex items-center space-x-1 bg-[#0B0E14] p-0.5 rounded-lg border border-[#232936]">
          <button
            v-for="p in providers"
            :key="p.id"
            @click="selectedProvider = p.id"
            class="px-2.5 py-1 text-xs rounded font-medium transition-all"
            :class="selectedProvider === p.id ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-gray-200'"
          >
            {{ p.name }} ({{ getProviderCount(p.id) }})
          </button>
        </div>
      </div>

      <button
        @click="store.syncModelsDev"
        class="text-xs px-3 py-1.5 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-blue-400 border border-[#374151] transition-all flex items-center space-x-1"
      >
        <span>🔄 从 models.dev 重新拉取标准库</span>
      </button>
    </div>

    <!-- 模型标准规格卡片流 (Grid 2列) -->
    <div class="flex-1 overflow-y-auto pr-1">
      <div class="grid grid-cols-2 gap-3">
        <div
          v-for="model in filteredModels"
          :key="model.id"
          class="p-4 rounded-xl bg-[#151922] border border-[#232936] hover:border-[#353E52] transition-all flex flex-col justify-between space-y-3"
        >
          <!-- 模型卡片头部 -->
          <div class="flex items-start justify-between">
            <div>
              <div class="flex items-center space-x-2">
                <span class="font-bold text-sm text-white">{{ model.name }}</span>
                <span v-if="model.is_featured" class="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 text-[10px] font-bold border border-amber-500/20">
                  ★ 旗舰
                </span>
              </div>
              <div class="text-[11px] text-blue-400 font-mono mt-0.5">
                {{ model.model_id }}
              </div>
            </div>
            <span class="px-2 py-0.5 rounded bg-[#1E293B] text-gray-300 text-xs font-mono uppercase">
              {{ model.provider }}
            </span>
          </div>

          <!-- 模型规格参数矩阵 -->
          <div class="grid grid-cols-3 gap-2 py-2 px-3 rounded-lg bg-[#0B0E14]/60 border border-[#232936]/40 text-xs">
            <div>
              <div class="text-[10px] text-gray-500">上下文窗口</div>
              <div class="font-mono font-bold text-sky-400">{{ (model.context_window / 1000).toFixed(0) }}k Context</div>
            </div>
            <div>
              <div class="text-[10px] text-gray-500">最大输出</div>
              <div class="font-mono font-bold text-gray-200">{{ model.max_output }} Tokens</div>
            </div>
            <div>
              <div class="text-[10px] text-gray-500">官方输入基准价</div>
              <div class="font-mono font-bold text-emerald-400">${{ model.official_input_price }} / 1M</div>
            </div>
          </div>

          <!-- 能力标签与描述 -->
          <div class="space-y-1.5">
            <div class="flex flex-wrap gap-1">
              <span
                v-for="cap in model.capabilities.split(',')"
                :key="cap"
                class="px-1.5 py-0.5 rounded bg-[#1E293B] text-gray-400 text-[10px] font-mono"
              >
                {{ cap.trim() }}
              </span>
            </div>
            <div class="text-[11px] text-gray-400 line-clamp-1">
              {{ model.description }}
            </div>
          </div>

          <!-- 底部渠道覆盖统计 -->
          <div class="pt-2 border-t border-[#232936]/60 flex items-center justify-between text-xs">
            <span class="text-[11px] text-gray-400">
              全网接入: <strong class="text-white font-mono">{{ model.active_relay_count || 3 }}</strong> 家中转
              <span class="text-emerald-400 ml-1">(最低 ${{ model.lowest_price_usd }}/1M)</span>
            </span>
            <div class="flex items-center space-x-2">
              <button
                @click="goToMatrix(model.model_id)"
                class="text-blue-400 hover:text-blue-300 transition-colors"
              >
                [全网比价]
              </button>
              <button
                @click="goToSpeedTest(model.model_id)"
                class="text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                [实测性能]
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()
const selectedProvider = ref('all')

const providers = [
  { id: 'all', name: '全部' },
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'anthropic', name: 'Anthropic' },
  { id: 'openai', name: 'OpenAI' },
  { id: 'google', name: 'Google' },
  { id: 'alibaba', name: '阿里通义' }
]

const filteredModels = computed(() => {
  if (selectedProvider.value === 'all') return store.modelsCatalog
  return store.modelsCatalog.filter((m) => m.provider.toLowerCase() === selectedProvider.value.toLowerCase())
})

const getProviderCount = (id: string) => {
  if (id === 'all') return store.modelsCatalog.length
  return store.modelsCatalog.filter((m) => m.provider.toLowerCase() === id.toLowerCase()).length
}

const goToMatrix = (modelId: string) => {
  store.selectedModelId = modelId
  store.activeTab = 'price-matrix'
}

const goToSpeedTest = (modelId: string) => {
  store.activeTab = 'speed-tester'
  const siteIds = store.activeSites.slice(0, 3).map((s) => s.id)
  store.runSpeedTest(siteIds, modelId)
}
</script>
