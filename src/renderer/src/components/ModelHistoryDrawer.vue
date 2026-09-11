<template>
  <div
    v-if="store.historyDrawer.visible"
    class="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs transition-opacity duration-300"
    @click.self="store.closeModelHistory"
  >
    <div
      class="w-full max-w-4xl h-full bg-[#FFFFFF] shadow-2xl flex flex-col border-l border-[#E5E5EA] animate-slide-left select-none overflow-hidden"
    >
      <!-- 抽屉顶部栏 (苹果极简设计) -->
      <div class="px-6 py-4 border-b border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between flex-shrink-0">
        <div class="flex items-center space-x-3 min-w-0">
          <div class="w-9 h-9 rounded-xl bg-[#0071E3]/10 text-[#0071E3] flex items-center justify-center font-bold flex-shrink-0 shadow-2xs">
            <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </div>
          <div class="min-w-0">
            <div class="flex items-center space-x-2">
              <h3 class="text-base font-bold text-[#1D1D1F] truncate font-mono">
                {{ store.historyDrawer.model?.model_name }}
              </h3>
              <span class="px-2 py-0.5 rounded-md text-[11px] font-bold" :class="getProviderBadgeClass(store.historyDrawer.model?.provider || '')">
                {{ store.historyDrawer.model?.provider_name }}
              </span>
              <span class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#F2F2F7] text-[#6E6E73] border border-[#E5E5EA]">
                {{ store.historyDrawer.model?.billing_mode || 'Standard' }}
              </span>
            </div>
            <p class="text-xs text-[#86868B] truncate mt-0.5 font-sans">
              系列: <strong class="text-[#1D1D1F]">{{ store.historyDrawer.model?.series }}</strong> • 历史价格走势大盘与全快照版本比对
            </p>
          </div>
        </div>

        <div class="flex items-center space-x-2 flex-shrink-0">
          <!-- 币种模式切换器 -->
          <div class="flex items-center bg-[#F2F2F7] rounded-xl p-0.5 border border-[#E5E5EA] text-xs">
            <button
              @click="displayCurrency = 'original'"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium"
              :class="displayCurrency === 'original'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              原币种
            </button>
            <button
              @click="displayCurrency = 'cny'"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium"
              :class="displayCurrency === 'cny'
                ? 'bg-white text-[#34C759] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              折合 ¥
            </button>
            <button
              @click="displayCurrency = 'usd'"
              class="px-2.5 py-1 rounded-lg transition-all cursor-pointer font-medium"
              :class="displayCurrency === 'usd'
                ? 'bg-white text-[#0071E3] font-bold shadow-2xs'
                : 'text-[#86868B] hover:text-[#1D1D1F]'"
            >
              折合 $
            </button>
          </div>

          <!-- 关闭按钮 -->
          <button
            @click="store.closeModelHistory"
            class="w-8 h-8 rounded-xl hover:bg-[#F2F2F7] text-[#86868B] hover:text-[#1D1D1F] flex items-center justify-center transition-all cursor-pointer"
            title="关闭 (ESC)"
          >
            ✕
          </button>
        </div>
      </div>

      <!-- 核心内容区 (滚动容器) -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6 bg-[#FAFAFC]">
        <!-- 加载中 -->
        <div v-if="store.historyDrawer.loading" class="py-24 text-center text-[#0071E3] space-y-2">
          <div class="w-7 h-7 border-2 border-[#0071E3] border-t-transparent rounded-full animate-spin mx-auto"></div>
          <div class="text-xs font-medium">正在分析并加载该模型历史调价轨迹...</div>
        </div>

        <!-- 错误提示 -->
        <div v-else-if="store.historyDrawer.error" class="p-4 bg-[#FFF2F0] border border-[#FFCCC7] rounded-2xl text-xs text-[#FF4D4F] flex items-center space-x-2">
          <span>⚠️</span>
          <span>{{ store.historyDrawer.error }}</span>
        </div>

        <template v-else>
          <!-- 1. 顶部关键指标卡片 (3 列网格) -->
          <div class="grid grid-cols-3 gap-3.5">
            <!-- 卡片 1: 当前生效最新输入价 -->
            <div class="p-4 rounded-2xl bg-white border border-[#E5E5EA] shadow-2xs space-y-1">
              <div class="text-[11px] font-medium text-[#86868B]">当前生效输入单价 (1M)</div>
              <div class="flex items-baseline space-x-2">
                <span class="text-xl font-bold font-mono text-[#0071E3]">
                  {{ formatPriceValue(latestPoint?.input_price, latestPoint) }}
                </span>
                <!-- 上期涨跌标记 -->
                <span
                  v-if="latestPoint && latestPoint.diff_input !== 0"
                  class="text-[11px] font-bold px-1.5 py-0.2 rounded"
                  :class="latestPoint.diff_input < 0 ? 'bg-[#E8F8EE] text-[#34C759]' : 'bg-[#FFF0F0] text-[#FF3B30]'"
                >
                  {{ latestPoint.diff_input < 0 ? '↓' : '↑' }} {{ Math.abs(latestPoint.diff_input_pct) }}%
                </span>
                <span v-else class="text-[10px] text-[#86868B] font-mono">持平 -</span>
              </div>
              <div class="text-[10px] text-[#86868B]">
                {{ latestPoint?.captured_at ? `生效时间: ${latestPoint.captured_at}` : '最新版本' }}
              </div>
            </div>

            <!-- 卡片 2: 当前生效最新输出价 -->
            <div class="p-4 rounded-2xl bg-white border border-[#E5E5EA] shadow-2xs space-y-1">
              <div class="text-[11px] font-medium text-[#86868B]">当前生效输出单价 (1M)</div>
              <div class="flex items-baseline space-x-2">
                <span class="text-xl font-bold font-mono text-[#1D1D1F]">
                  {{ formatPriceValue(latestPoint?.output_price, latestPoint) }}
                </span>
                <span
                  v-if="latestPoint && latestPoint.diff_output !== 0"
                  class="text-[11px] font-bold px-1.5 py-0.2 rounded"
                  :class="latestPoint.diff_output < 0 ? 'bg-[#E8F8EE] text-[#34C759]' : 'bg-[#FFF0F0] text-[#FF3B30]'"
                >
                  {{ latestPoint.diff_output < 0 ? '↓' : '↑' }} {{ Math.abs(latestPoint.diff_output_pct) }}%
                </span>
                <span v-else class="text-[10px] text-[#86868B] font-mono">持平 -</span>
              </div>
              <div class="text-[10px] text-[#86868B]">
                上期输出: {{ prevPoint ? formatPriceValue(prevPoint.output_price, prevPoint) : '无上一期' }}
              </div>
            </div>

            <!-- 卡片 3: 历史版本统计与调价次数 -->
            <div class="p-4 rounded-2xl bg-white border border-[#E5E5EA] shadow-2xs space-y-1">
              <div class="text-[11px] font-medium text-[#86868B]">历史快照记录版本数</div>
              <div class="flex items-baseline space-x-2">
                <span class="text-xl font-bold font-mono text-[#34C759]">
                  {{ store.historyDrawer.historyPoints.length }}
                </span>
                <span class="text-xs text-[#86868B]">个快照存档点</span>
              </div>
              <div class="text-[10px] text-[#86868B]">
                价格变动次数: <strong class="text-[#1D1D1F] font-mono">{{ changeCount }}</strong> 次
              </div>
            </div>
          </div>

          <!-- 2. ECharts 价格走势折线图卡片 -->
          <div class="p-4 rounded-2xl bg-white border border-[#E5E5EA] shadow-2xs space-y-3">
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="w-2 h-2 rounded-full bg-[#0071E3]"></span>
                <h4 class="text-xs font-bold text-[#1D1D1F]">官方定价时序变化趋势走势大盘</h4>
              </div>
              <div class="flex items-center space-x-3 text-[11px] text-[#86868B]">
                <div class="flex items-center space-x-1">
                  <span class="w-2.5 h-0.5 bg-[#0071E3] rounded-full"></span>
                  <span>输入价格</span>
                </div>
                <div class="flex items-center space-x-1">
                  <span class="w-2.5 h-0.5 bg-[#34C759] rounded-full"></span>
                  <span>输出价格</span>
                </div>
                <div class="flex items-center space-x-1">
                  <span class="w-2.5 h-0.5 bg-[#FF9500] rounded-full"></span>
                  <span>缓存价格</span>
                </div>
              </div>
            </div>

            <!-- 图表容器 -->
            <div ref="chartRef" class="w-full h-64 select-none"></div>
          </div>

          <!-- 3. 历次快照版本明细比对表格 -->
          <div class="rounded-2xl bg-white border border-[#E5E5EA] shadow-2xs overflow-hidden space-y-0">
            <div class="px-4 py-3 border-b border-[#E5E5EA] bg-[#FBFBFD] flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="text-xs font-bold text-[#1D1D1F]">全版本快照演变记录对照表</span>
                <span class="px-2 py-0.2 rounded-full text-[10px] bg-[#E8F2FD] text-[#0071E3] font-bold">
                  {{ store.historyDrawer.historyPoints.length }} 个版本
                </span>
              </div>
              <span class="text-[11px] text-[#86868B]">按时间降序（最新在上）</span>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs border-collapse">
                <thead>
                  <tr class="bg-[#F9F9FB] border-b border-[#E5E5EA] text-[#6E6E73] font-medium text-[11px]">
                    <th class="py-2.5 px-3">快照生成时间</th>
                    <th class="py-2.5 px-3">版本属性</th>
                    <th class="py-2.5 px-3 text-right">输入价格 (1M)</th>
                    <th class="py-2.5 px-3 text-right">环比涨跌 (输入)</th>
                    <th class="py-2.5 px-3 text-right">输出价格 (1M)</th>
                    <th class="py-2.5 px-3 text-right">环比涨跌 (输出)</th>
                    <th class="py-2.5 px-3 text-right">缓存命中价</th>
                    <th class="py-2.5 px-3 text-center">快照凭证</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E5E5EA]/60 font-mono">
                  <tr
                    v-for="point in reversedPoints"
                    :key="point.id"
                    class="hover:bg-[#F2F7FF]/50 transition-colors"
                    :class="point.is_current ? 'bg-[#F2F7FF]/20 font-bold' : ''"
                  >
                    <td class="py-2.5 px-3 text-[#1D1D1F] whitespace-nowrap">
                      {{ point.captured_at || point.price_date || '-' }}
                    </td>
                    <td class="py-2.5 px-3 whitespace-nowrap">
                      <span
                        v-if="point.is_current"
                        class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-[#34C759]/15 text-[#34C759] border border-[#34C759]/30"
                      >
                        当前生效
                      </span>
                      <span
                        v-else
                        class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-[#F2F2F7] text-[#86868B]"
                      >
                        历史归档
                      </span>
                    </td>
                    <td class="py-2.5 px-3 text-right text-[#0071E3] font-bold whitespace-nowrap">
                      {{ formatPriceValue(point.input_price, point) }}
                    </td>
                    <td class="py-2.5 px-3 text-right whitespace-nowrap">
                      <span
                        v-if="point.diff_input !== 0"
                        class="px-1.5 py-0.2 rounded text-[10px] font-bold"
                        :class="point.diff_input < 0 ? 'bg-[#E8F8EE] text-[#34C759]' : 'bg-[#FFF0F0] text-[#FF3B30]'"
                      >
                        {{ point.diff_input < 0 ? '↓' : '↑' }} {{ Math.abs(point.diff_input_pct) }}%
                      </span>
                      <span v-else class="text-[#86868B] text-[10px] font-normal">-</span>
                    </td>
                    <td class="py-2.5 px-3 text-right text-[#1D1D1F] font-bold whitespace-nowrap">
                      {{ formatPriceValue(point.output_price, point) }}
                    </td>
                    <td class="py-2.5 px-3 text-right whitespace-nowrap">
                      <span
                        v-if="point.diff_output !== 0"
                        class="px-1.5 py-0.2 rounded text-[10px] font-bold"
                        :class="point.diff_output < 0 ? 'bg-[#E8F8EE] text-[#34C759]' : 'bg-[#FFF0F0] text-[#FF3B30]'"
                      >
                        {{ point.diff_output < 0 ? '↓' : '↑' }} {{ Math.abs(point.diff_output_pct) }}%
                      </span>
                      <span v-else class="text-[#86868B] text-[10px] font-normal">-</span>
                    </td>
                    <td class="py-2.5 px-3 text-right text-[#34C759] whitespace-nowrap">
                      {{ formatPriceValue(point.cache_read_price, point) }}
                    </td>
                    <td class="py-2.5 px-3 text-center whitespace-nowrap font-sans">
                      <button
                        v-if="point.snapshot_id"
                        @click="openSnapshot(point)"
                        class="px-2 py-0.8 rounded-lg border border-[#0071E3]/30 bg-[#F2F7FF] hover:bg-[#0071E3] text-[#0071E3] hover:text-white text-[11px] font-medium transition-all shadow-2xs cursor-pointer flex items-center space-x-1 mx-auto"
                      >
                        <span>快照 #{{ point.snapshot_id }}</span>
                        <span>📄</span>
                      </button>
                      <span v-else class="text-[#86868B] text-[10px]">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { useOfficialPricingStore } from '../stores/officialPricingStore'

const store = useOfficialPricingStore()
const chartRef = ref<HTMLDivElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const displayCurrency = ref<'original' | 'cny' | 'usd'>('original')

// 获取厂商 Badge 样式
function getProviderBadgeClass(provider: string): string {
  const map: Record<string, string> = {
    openai: 'bg-[#10A37F]/10 text-[#10A37F] border border-[#10A37F]/20',
    anthropic: 'bg-[#D97706]/10 text-[#D97706] border border-[#D97706]/20',
    google: 'bg-[#4285F4]/10 text-[#4285F4] border border-[#4285F4]/20',
    deepseek: 'bg-[#0071E3]/10 text-[#0071E3] border border-[#0071E3]/20',
    zhipuai: 'bg-[#6366F1]/10 text-[#6366F1] border border-[#6366F1]/20',
    moonshotai: 'bg-[#8B5CF6]/10 text-[#8B5CF6] border border-[#8B5CF6]/20',
    minimax: 'bg-[#EC4899]/10 text-[#EC4899] border border-[#EC4899]/20',
    alibaba: 'bg-[#FF6A00]/10 text-[#FF6A00] border border-[#FF6A00]/20',
    xiaomi: 'bg-[#FF6900]/10 text-[#FF6900] border border-[#FF6900]/20',
    stepfun: 'bg-[#0EA5E9]/10 text-[#0EA5E9] border border-[#0EA5E9]/20'
  }
  return map[provider] || 'bg-gray-100 text-gray-700 border border-gray-200'
}

// 格式化价格
function formatPriceValue(val: number | undefined | null, point: any): string {
  if (val === undefined || val === null) return '-'
  if (val === 0) return '免费'
  const rate = store.usdToCnyRate || 7.30

  if (displayCurrency.value === 'cny') {
    const cnyVal = point?.currency === 'USD' ? val * rate : val
    return `¥${cnyVal >= 1 ? cnyVal.toFixed(2) : cnyVal.toFixed(4)}`
  } else if (displayCurrency.value === 'usd') {
    const usdVal = point?.currency === 'CNY' ? (rate > 0 ? val / rate : 0) : val
    return `$${usdVal >= 1 ? usdVal.toFixed(2) : usdVal.toFixed(4)}`
  } else {
    const sym = point?.currency === 'USD' ? '$' : '¥'
    return `${sym}${val >= 1 ? val.toFixed(2) : val.toFixed(4)}`
  }
}

// 获取最新一条与上一条
const latestPoint = computed(() => {
  const pts = store.historyDrawer.historyPoints
  if (!pts || pts.length === 0) return null
  return pts[pts.length - 1]
})

const prevPoint = computed(() => {
  const pts = store.historyDrawer.historyPoints
  if (!pts || pts.length < 2) return null
  return pts[pts.length - 2]
})

const reversedPoints = computed(() => {
  return [...store.historyDrawer.historyPoints].reverse()
})

const changeCount = computed(() => {
  let count = 0
  for (const p of store.historyDrawer.historyPoints) {
    if (p.diff_input !== 0 || p.diff_output !== 0) {
      count++
    }
  }
  return count
})

function openSnapshot(point: any) {
  if (!point.snapshot_id) return
  store.snapshotDrawer = {
    visible: true,
    snapshotId: point.snapshot_id,
    sourceUrl: store.historyDrawer.model?.source_page_url || '',
    modelName: store.historyDrawer.model?.model_name || '',
    pageTitle: `${store.historyDrawer.model?.model_name} 历史快照凭证 #${point.snapshot_id}`,
    highlightTarget: store.historyDrawer.model?.model_name || ''
  }
}

// 渲染 ECharts 折线走势图
function renderChart() {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const points = store.historyDrawer.historyPoints || []
  if (points.length === 0) {
    chartInstance.clear()
    return
  }

  const categories = points.map((p, idx) => {
    if (p.captured_at) {
      const parts = p.captured_at.split(' ')
      return parts.length > 1 ? parts[0].slice(5) + '\n' + parts[1].slice(0, 5) : p.captured_at
    }
    return `版本 #${idx + 1}`
  })

  const rate = store.usdToCnyRate || 7.30
  const getVal = (val: number, cur: string) => {
    if (displayCurrency.value === 'cny') return cur === 'USD' ? +(val * rate).toFixed(4) : val
    if (displayCurrency.value === 'usd') return cur === 'CNY' ? +(val / rate).toFixed(4) : val
    return val
  }

  const inputData = points.map((p) => getVal(p.input_price, p.currency))
  const outputData = points.map((p) => getVal(p.output_price, p.currency))
  const cacheData = points.map((p) => getVal(p.cache_read_price, p.currency))

  const sym = displayCurrency.value === 'cny' ? '¥' : (displayCurrency.value === 'usd' ? '$' : (points[0]?.currency === 'USD' ? '$' : '¥'))

  const option: echarts.EChartsOption = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#E5E5EA',
      borderWidth: 1,
      textStyle: { color: '#1D1D1F', fontSize: 12 },
      formatter: (params: any) => {
        let title = params[0]?.name?.replace('\n', ' ') || ''
        let res = `<div class="font-bold border-b border-gray-100 pb-1 mb-1 font-mono">${title}</div>`
        for (const item of params) {
          res += `<div class="flex items-center justify-between space-x-4">
            <span style="color: ${item.color}">● ${item.seriesName}:</span>
            <strong class="font-mono">${sym}${item.value}</strong>
          </div>`
        }
        return res
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      top: '15%',
      bottom: '12%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: categories,
      axisLine: { lineStyle: { color: '#E5E5EA' } },
      axisLabel: { color: '#86868B', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#F2F2F7', type: 'dashed' } },
      axisLabel: {
        color: '#86868B',
        fontSize: 10,
        formatter: (val: number) => `${sym}${val}`
      }
    },
    series: [
      {
        name: '输入价格 (1M)',
        type: 'line',
        data: inputData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#0071E3' },
        lineStyle: { width: 2.5 }
      },
      {
        name: '输出价格 (1M)',
        type: 'line',
        data: outputData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        itemStyle: { color: '#34C759' },
        lineStyle: { width: 2.5 }
      },
      {
        name: '缓存读取价 (1M)',
        type: 'line',
        data: cacheData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 5,
        itemStyle: { color: '#FF9500' },
        lineStyle: { width: 1.5, type: 'dashed' }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

watch(
  () => [store.historyDrawer.visible, store.historyDrawer.historyPoints, displayCurrency.value],
  () => {
    if (store.historyDrawer.visible && !store.historyDrawer.loading) {
      nextTick(() => {
        renderChart()
      })
    }
  },
  { deep: true }
)

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && store.historyDrawer.visible) {
    store.closeModelHistory()
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('resize', () => chartInstance?.resize())
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
  if (chartInstance) {
    chartInstance.dispose()
    chartInstance = null
  }
})
</script>

<style scoped>
@keyframes slideLeft {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}
.animate-slide-left {
  animation: slideLeft 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
