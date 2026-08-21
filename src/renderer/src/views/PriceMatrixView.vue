<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部四级联动多维筛选栏 -->
    <div class="p-3 rounded-xl bg-[#151922] border border-[#232936] space-y-2.5">
      <!-- 第一行：四大维度可搜索多选下拉 -->
      <div class="flex items-center justify-between flex-wrap gap-2">
        <div class="flex items-center flex-wrap gap-2">
          <!-- 1. 模型厂商多选 -->
          <MultiSelectFilter
            label="模型厂商"
            icon="🏢"
            :options="providerOptions"
            v-model="selectedProviders"
          />

          <!-- 2. 模型系列多选 (根据已选厂商联动收敛) -->
          <MultiSelectFilter
            label="模型系列"
            icon="📦"
            :options="seriesOptions"
            v-model="selectedSeries"
          />

          <!-- 3. 模型名称多选 (根据已选厂商与系列联动收敛) -->
          <MultiSelectFilter
            label="模型名称"
            icon="🤖"
            :options="modelOptions"
            v-model="selectedModels"
          />

          <!-- 4. 渠道中转站多选 -->
          <MultiSelectFilter
            label="渠道中转站"
            icon="🌐"
            :options="siteOptions"
            v-model="selectedSites"
          />
        </div>

        <!-- 右侧：快捷操作与匹配统计 -->
        <div class="flex items-center space-x-2 text-xs">
          <span class="text-gray-400">
            匹配到 <strong class="text-emerald-400 font-mono font-bold">{{ filteredMatrix.length }}</strong> 条报价
          </span>
          <button
            v-if="hasAnyFilter"
            @click="resetAllFilters"
            class="px-2.5 py-1 rounded bg-[#1E2430] hover:bg-rose-950/60 text-gray-300 hover:text-rose-300 border border-[#374151] hover:border-rose-700 transition-all text-xs"
          >
            重置筛选
          </button>
        </div>
      </div>

      <!-- 第二行：已选标签 Chips 展示条 (如果有选择) -->
      <div v-if="hasAnyFilter" class="flex items-center flex-wrap gap-1.5 pt-1.5 border-t border-[#232936]/60 text-xs">
        <span class="text-[11px] text-gray-500 font-medium">当前筛选:</span>

        <!-- 厂商 Chips -->
        <span
          v-for="p in selectedProviders"
          :key="`p-${p}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-300 text-[11px]"
        >
          <span>🏢 {{ getProviderLabel(p) }}</span>
          <button @click="removeProvider(p)" class="hover:text-white ml-0.5">✕</button>
        </span>

        <!-- 系列 Chips -->
        <span
          v-for="s in selectedSeries"
          :key="`s-${s}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-[11px]"
        >
          <span>📦 {{ s }}</span>
          <button @click="removeSeries(s)" class="hover:text-white ml-0.5">✕</button>
        </span>

        <!-- 模型 Chips -->
        <span
          v-for="m in selectedModels"
          :key="`m-${m}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-purple-500/15 border border-purple-500/30 text-purple-300 text-[11px] font-mono"
        >
          <span>🤖 {{ m }}</span>
          <button @click="removeModel(m)" class="hover:text-white ml-0.5">✕</button>
        </span>

        <!-- 渠道 Chips -->
        <span
          v-for="st in selectedSites"
          :key="`st-${st}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[11px]"
        >
          <span>🌐 {{ st }}</span>
          <button @click="removeSite(st)" class="hover:text-white ml-0.5">✕</button>
        </span>
      </div>
    </div>

    <!-- 价格对比大矩阵 (数据表格) -->
    <div class="flex-1 flex flex-col bg-[#151922] rounded-xl border border-[#232936] p-3 overflow-hidden min-h-0">
      <!-- 表头 -->
      <div class="grid grid-cols-12 gap-2 text-[11px] text-gray-400 font-bold px-3 py-2 border-b border-[#232936] bg-[#1A202C]/60 rounded-t-lg">
        <div class="col-span-2">模型系列 / 厂商</div>
        <div class="col-span-2">模型标准标识</div>
        <div class="col-span-2">渠道 / 中转站点</div>
        <div class="col-span-1">类型</div>
        <div class="col-span-1 text-right">输入单价</div>
        <div class="col-span-1 text-right">输出单价</div>
        <div class="col-span-1 text-center">倍率</div>
        <div class="col-span-1 text-center">官方折扣</div>
        <div class="col-span-1 text-right">实测 TPS</div>
      </div>

      <!-- 数据行列表 -->
      <div class="flex-1 overflow-y-auto divide-y divide-[#232936]/40 pr-1 mt-1">
        <div
          v-for="row in filteredMatrix"
          :key="row.id"
          @click="selectRow(row)"
          class="grid grid-cols-12 gap-2 items-center px-3 py-2.5 text-xs transition-colors cursor-pointer rounded-lg"
          :class="selectedRow?.id === row.id ? 'bg-blue-600/15 border border-blue-500/30' : 'hover:bg-[#1A202C]'"
        >
          <!-- 系列与厂商 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <span class="px-1.5 py-0.5 rounded bg-[#1E293B] text-gray-300 text-[10px] font-mono">
              {{ row.provider.toUpperCase() }}
            </span>
            <span class="text-gray-300 font-medium truncate">{{ row.series || '通用' }}</span>
          </div>

          <!-- 模型标识 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <span class="font-bold text-blue-400 font-mono truncate" :title="row.model_id">{{ row.model_id }}</span>
          </div>

          <!-- 渠道站点 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <span class="font-medium text-white truncate" :title="row.site_name">{{ row.site_name }}</span>
          </div>

          <!-- 类型徽标 -->
          <div class="col-span-1">
            <span
              class="px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold uppercase"
              :class="getTypeBadgeClass(row.site_type)"
            >
              {{ row.site_type }}
            </span>
          </div>

          <!-- 输入价格 -->
          <div class="col-span-1 text-right font-mono font-bold text-emerald-400">
            {{ formatPrice(row.calculated_input_usd, row.calculated_input_cny) }}
          </div>

          <!-- 输出价格 -->
          <div class="col-span-1 text-right font-mono text-emerald-400">
            {{ formatPrice(row.calculated_output_usd, row.calculated_output_cny) }}
          </div>

          <!-- 倍率 -->
          <div class="col-span-1 text-center font-mono text-gray-300 font-semibold">
            {{ row.model_ratio }}x
          </div>

          <!-- 官方折扣 -->
          <div class="col-span-1 text-center font-mono">
            <span
              v-if="row.discount_percent < 0"
              class="px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold text-[10px]"
            >
              {{ row.discount_percent }}%
            </span>
            <span v-else-if="row.is_official" class="text-gray-500 text-[10px]">
              官方基准
            </span>
            <span v-else class="text-gray-400 text-[10px]">
              +{{ row.discount_percent }}%
            </span>
          </div>

          <!-- 实测 TPS -->
          <div class="col-span-1 text-right font-mono text-sky-400 font-bold">
            {{ row.last_tested_tps }} <span class="text-[10px] text-gray-500 font-normal">tps</span>
          </div>
        </div>

        <div v-if="filteredMatrix.length === 0" class="py-12 text-center text-xs text-gray-500">
          无匹配的大模型比价数据，请调整筛选条件
        </div>
      </div>
    </div>

    <!-- 底部：全网价格-TPS 性价比散点图 (ECharts) -->
    <div class="h-44 rounded-xl bg-[#151922] border border-[#232936] p-3 flex flex-col">
      <div class="flex items-center justify-between pb-1 border-b border-[#232936]/60">
        <div class="flex items-center space-x-2 text-xs font-bold text-white">
          <span>📈 全网性价比散点分布 (当前模型: {{ activeScatterModelId }})</span>
          <span class="text-[11px] text-gray-400 font-normal">| 越偏左上角（价格低、TPS 高）综合性价比越高</span>
        </div>
      </div>
      <div class="flex-1 w-full relative min-h-0 mt-1">
        <div ref="scatterChartRef" class="w-full h-full"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useDashboardStore } from '../stores/dashboardStore'
import MultiSelectFilter, { type FilterOption } from '../components/MultiSelectFilter.vue'
import type { ComparisonItem } from '../types'

const store = useDashboardStore()

// 选中的多维筛选状态
const selectedProviders = ref<string[]>([])
const selectedSeries = ref<string[]>([])
const selectedModels = ref<string[]>([])
const selectedSites = ref<string[]>([])

const scatterChartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const selectedRow = ref<ComparisonItem | null>(null)

// 厂商名称中英文映射表
const providerNames: Record<string, string> = {
  deepseek: 'DeepSeek (深度求索)',
  openai: 'OpenAI',
  anthropic: 'Anthropic (Claude)',
  google: 'Google (Gemini)',
  alibaba: 'Alibaba (阿里通义)',
  meta: 'Meta (Llama)',
  zhipu: '智谱 AI'
}

const getProviderLabel = (p: string) => providerNames[p.toLowerCase()] || p

// 1. 厂商下拉选项 (包含计数)
const providerOptions = computed<FilterOption[]>(() => {
  const map: Record<string, number> = {}
  store.comparisonMatrix.forEach((item) => {
    const p = item.provider.toLowerCase()
    map[p] = (map[p] || 0) + 1
  })
  return Object.keys(map).map((p) => ({
    value: p,
    label: getProviderLabel(p),
    count: map[p]
  }))
})

// 2. 模型系列下拉选项 (根据已选厂商级联收敛)
const seriesOptions = computed<FilterOption[]>(() => {
  let list = store.comparisonMatrix
  if (selectedProviders.value.length > 0) {
    list = list.filter((item) => selectedProviders.value.includes(item.provider.toLowerCase()))
  }
  const map: Record<string, number> = {}
  list.forEach((item) => {
    const s = item.series || '通用系列'
    map[s] = (map[s] || 0) + 1
  })
  return Object.keys(map).map((s) => ({
    value: s,
    label: s,
    count: map[s]
  }))
})

// 3. 模型名称下拉选项 (根据已选厂商与已选系列级联收敛)
const modelOptions = computed<FilterOption[]>(() => {
  let list = store.comparisonMatrix
  if (selectedProviders.value.length > 0) {
    list = list.filter((item) => selectedProviders.value.includes(item.provider.toLowerCase()))
  }
  if (selectedSeries.value.length > 0) {
    list = list.filter((item) => selectedSeries.value.includes(item.series || '通用系列'))
  }
  const map: Record<string, number> = {}
  list.forEach((item) => {
    const m = item.model_id
    map[m] = (map[m] || 0) + 1
  })
  return Object.keys(map).map((m) => ({
    value: m,
    label: m,
    count: map[m]
  }))
})

// 4. 渠道中转站下拉选项 (根据已选模型级联收敛)
const siteOptions = computed<FilterOption[]>(() => {
  let list = store.comparisonMatrix
  if (selectedProviders.value.length > 0) {
    list = list.filter((item) => selectedProviders.value.includes(item.provider.toLowerCase()))
  }
  if (selectedSeries.value.length > 0) {
    list = list.filter((item) => selectedSeries.value.includes(item.series || '通用系列'))
  }
  if (selectedModels.value.length > 0) {
    list = list.filter((item) => selectedModels.value.includes(item.model_id))
  }
  const map: Record<string, number> = {}
  list.forEach((item) => {
    const name = item.site_name
    map[name] = (map[name] || 0) + 1
  })
  return Object.keys(map).map((name) => ({
    value: name,
    label: name,
    count: map[name]
  }))
})

// 级联自愈：当上级筛选变更导致下级选项失效时，自动清理
watch(selectedProviders, (newProviders) => {
  if (newProviders.length > 0) {
    const validSeries = new Set(seriesOptions.value.map((o) => o.value))
    selectedSeries.value = selectedSeries.value.filter((s) => validSeries.has(s))
    const validModels = new Set(modelOptions.value.map((o) => o.value))
    selectedModels.value = selectedModels.value.filter((m) => validModels.has(m))
  }
})

watch(selectedSeries, (newSeries) => {
  if (newSeries.length > 0) {
    const validModels = new Set(modelOptions.value.map((o) => o.value))
    selectedModels.value = selectedModels.value.filter((m) => validModels.has(m))
  }
})

// 核心过滤计算：四维多选 + 全局模糊搜索复合过滤
const filteredMatrix = computed<ComparisonItem[]>(() => {
  let list = store.comparisonMatrix

  // 1. 厂商筛选
  if (selectedProviders.value.length > 0) {
    list = list.filter((item) => selectedProviders.value.includes(item.provider.toLowerCase()))
  }

  // 2. 系列筛选
  if (selectedSeries.value.length > 0) {
    list = list.filter((item) => selectedSeries.value.includes(item.series || '通用系列'))
  }

  // 3. 模型名称筛选
  if (selectedModels.value.length > 0) {
    list = list.filter((item) => selectedModels.value.includes(item.model_id))
  }

  // 4. 渠道筛选
  if (selectedSites.value.length > 0) {
    list = list.filter((item) => selectedSites.value.includes(item.site_name))
  }

  // 5. 全局搜索框模糊匹配
  if (store.searchQuery.trim()) {
    const q = store.searchQuery.toLowerCase().trim()
    list = list.filter(
      (item) =>
        item.model_id.toLowerCase().includes(q) ||
        item.model_name.toLowerCase().includes(q) ||
        (item.series && item.series.toLowerCase().includes(q)) ||
        item.site_name.toLowerCase().includes(q) ||
        item.provider.toLowerCase().includes(q)
    )
  }

  return list
})

const hasAnyFilter = computed(() => {
  return (
    selectedProviders.value.length > 0 ||
    selectedSeries.value.length > 0 ||
    selectedModels.value.length > 0 ||
    selectedSites.value.length > 0
  )
})

const removeProvider = (p: string) => {
  selectedProviders.value = selectedProviders.value.filter((x) => x !== p)
}

const removeSeries = (s: string) => {
  selectedSeries.value = selectedSeries.value.filter((x) => x !== s)
}

const removeModel = (m: string) => {
  selectedModels.value = selectedModels.value.filter((x) => x !== m)
}

const removeSite = (st: string) => {
  selectedSites.value = selectedSites.value.filter((x) => x !== st)
}

const resetAllFilters = () => {
  selectedProviders.value = []
  selectedSeries.value = []
  selectedModels.value = []
  selectedSites.value = []
  store.searchQuery = ''
}

const formatPrice = (usd: number, cny: number) => {
  if (store.currency === 'CNY') {
    return `￥${cny.toFixed(2)}`
  }
  return `$${usd >= 1 ? usd.toFixed(2) : usd.toFixed(3)}`
}

const getTypeBadgeClass = (type: string) => {
  if (type === 'official') return 'bg-slate-700 text-slate-200'
  if (type === 'newapi') return 'bg-emerald-950 text-emerald-400 border border-emerald-800'
  if (type === 'sub2api') return 'bg-purple-950 text-purple-300 border border-purple-800'
  return 'bg-blue-950 text-blue-300'
}

const selectRow = (row: ComparisonItem) => {
  selectedRow.value = row
  updateScatterChart()
}

const activeScatterModelId = computed(() => {
  if (selectedRow.value) return selectedRow.value.model_id
  if (selectedModels.value.length === 1) return selectedModels.value[0]
  if (filteredMatrix.value.length > 0) return filteredMatrix.value[0].model_id
  return 'deepseek-v3'
})

const initChart = () => {
  if (!scatterChartRef.value) return
  chartInstance = echarts.init(scatterChartRef.value, 'dark', { renderer: 'canvas' })
  updateScatterChart()
}

const updateScatterChart = () => {
  if (!chartInstance) return
  const currentModelId = activeScatterModelId.value
  const items = store.comparisonMatrix.filter((item) => item.model_id === currentModelId)

  const data = items.map((item) => [
    item.calculated_input_usd,
    item.last_tested_tps,
    item.site_name,
    item.discount_percent,
    item.site_type
  ])

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#1E2430',
      borderColor: '#374151',
      textStyle: { color: '#F3F4F6', fontSize: 11 },
      formatter: (params: any) => {
        const val = params.value
        return `<strong>${val[2]}</strong> (${val[4]})<br/>输入单价: $${val[0]}/1M<br/>实测 TPS: ${val[1]} tps<br/>折扣: ${val[3]}%`
      }
    },
    grid: { left: '4%', right: '4%', top: '15%', bottom: '15%' },
    xAxis: {
      name: '输入单价 ($/1M)',
      nameLocation: 'end',
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#232936', type: 'dashed' } },
      axisLabel: { color: '#9CA3AF', fontSize: 10 }
    },
    yAxis: {
      name: '生成速率 (TPS)',
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#232936', type: 'dashed' } },
      axisLabel: { color: '#9CA3AF', fontSize: 10 }
    },
    series: [
      {
        name: '性价比点',
        type: 'scatter',
        symbolSize: 22,
        data: data,
        itemStyle: {
          color: (params: any) => {
            const type = params.value[4]
            if (type === 'official') return '#64748B'
            if (type === 'newapi') return '#10B981'
            if (type === 'sub2api') return '#A855F7'
            return '#3B82F6'
          },
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    ]
  }
  chartInstance.setOption(option, true)
}

const handleResize = () => chartInstance?.resize()

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

watch(() => [filteredMatrix.value, store.currency, activeScatterModelId.value], () => {
  updateScatterChart()
}, { deep: true })
</script>
