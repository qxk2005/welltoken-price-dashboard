<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部厂商与模型多维筛选栏 -->
    <div class="p-3 rounded-xl bg-[#151922] border border-[#232936] flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-xs font-bold text-gray-400">厂商筛选:</span>
        <div class="flex items-center space-x-1 bg-[#0B0E14] p-0.5 rounded-lg border border-[#232936]">
          <button
            v-for="p in providers"
            :key="p.id"
            @click="store.selectedProvider = p.id"
            class="px-2.5 py-1 text-xs rounded font-medium transition-all"
            :class="store.selectedProvider === p.id ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-gray-200'"
          >
            {{ p.name }}
          </button>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <span class="text-xs font-bold text-gray-400">热点模型:</span>
        <div class="flex items-center space-x-1.5">
          <button
            v-for="m in featuredQuickModels"
            :key="m.id"
            @click="store.selectedModelId = m.id"
            class="px-2.5 py-1 text-xs rounded-lg border font-mono transition-all"
            :class="
              store.selectedModelId === m.id
                ? 'bg-blue-500/20 text-blue-300 border-blue-500/50 font-bold'
                : 'bg-[#1E2430] text-gray-400 border-[#2D3748] hover:text-gray-200'
            "
          >
            {{ m.name }}
          </button>
        </div>
      </div>
    </div>

    <!-- 价格对比大矩阵 (数据表格) -->
    <div class="flex-1 flex flex-col bg-[#151922] rounded-xl border border-[#232936] p-3 overflow-hidden min-h-0">
      <!-- 表头 -->
      <div class="grid grid-cols-12 gap-2 text-[11px] text-gray-400 font-bold px-3 py-2 border-b border-[#232936] bg-[#1A202C]/60 rounded-t-lg">
        <div class="col-span-2">模型标准标识</div>
        <div class="col-span-2">渠道 / 中转站点</div>
        <div class="col-span-1">类型</div>
        <div class="col-span-2 text-right">输入单价 (Input/1M)</div>
        <div class="col-span-2 text-right">输出单价 (Output/1M)</div>
        <div class="col-span-1 text-center">折算倍率</div>
        <div class="col-span-1 text-center">官方折扣</div>
        <div class="col-span-1 text-right">实测 TPS</div>
      </div>

      <!-- 数据行列表 -->
      <div class="flex-1 overflow-y-auto divide-y divide-[#232936]/40 pr-1 mt-1">
        <div
          v-for="row in store.filteredMatrix"
          :key="row.id"
          @click="selectRow(row)"
          class="grid grid-cols-12 gap-2 items-center px-3 py-2.5 text-xs transition-colors cursor-pointer rounded-lg"
          :class="selectedRow?.id === row.id ? 'bg-blue-600/15 border border-blue-500/30' : 'hover:bg-[#1A202C]'"
        >
          <!-- 模型标识 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <span class="font-bold text-blue-400 font-mono">{{ row.model_id }}</span>
          </div>

          <!-- 渠道站点 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <span class="font-medium text-white">{{ row.site_name }}</span>
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
          <div class="col-span-2 text-right font-mono font-bold text-emerald-400">
            {{ formatPrice(row.calculated_input_usd, row.calculated_input_cny) }}
          </div>

          <!-- 输出价格 -->
          <div class="col-span-2 text-right font-mono text-emerald-400">
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

        <div v-if="store.filteredMatrix.length === 0" class="py-12 text-center text-xs text-gray-500">
          暂无匹配的大模型比价数据
        </div>
      </div>
    </div>

    <!-- 底部：全网价格-TPS 性价比散点图 (ECharts) -->
    <div class="h-48 rounded-xl bg-[#151922] border border-[#232936] p-3 flex flex-col">
      <div class="flex items-center justify-between pb-1 border-b border-[#232936]/60">
        <div class="flex items-center space-x-2 text-xs font-bold text-white">
          <span>📈 全网性价比散点分布 (当前: {{ selectedRow ? selectedRow.model_id : 'deepseek-v3' }})</span>
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
import type { ComparisonItem } from '../types'

const store = useDashboardStore()
const scatterChartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const selectedRow = ref<ComparisonItem | null>(null)

const providers = [
  { id: 'all', name: '全部厂商' },
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'anthropic', name: 'Anthropic' },
  { id: 'openai', name: 'OpenAI' },
  { id: 'google', name: 'Google' },
  { id: 'alibaba', name: '阿里通义' }
]

const featuredQuickModels = [
  { id: 'all', name: '全部模型' },
  { id: 'deepseek-v3', name: 'DeepSeek V3' },
  { id: 'deepseek-r1', name: 'DeepSeek R1' },
  { id: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet' },
  { id: 'gpt-4o', name: 'GPT-4o' }
]

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

const initChart = () => {
  if (!scatterChartRef.value) return
  chartInstance = echarts.init(scatterChartRef.value, 'dark', { renderer: 'canvas' })
  updateScatterChart()
}

const updateScatterChart = () => {
  if (!chartInstance) return
  const currentModelId = selectedRow.value ? selectedRow.value.model_id : 'deepseek-v3'
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

watch(() => [store.comparisonMatrix, store.currency], () => {
  updateScatterChart()
}, { deep: true })
</script>
