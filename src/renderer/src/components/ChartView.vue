<template>
  <div class="h-full flex flex-col bg-[#151922] rounded-xl border border-[#232936] p-4 overflow-hidden">
    <!-- 图表顶部控制栏 -->
    <div class="flex items-center justify-between pb-3 border-b border-[#232936]/80">
      <!-- 左侧：当前币种信息与即时价格 -->
      <div class="flex items-center space-x-3">
        <div class="flex items-center space-x-2">
          <span class="text-xl font-bold font-mono text-white">{{ currentToken?.symbol }}</span>
          <span class="text-xs text-gray-400">/ USDT</span>
          <span class="text-xs px-2 py-0.5 rounded bg-[#232936] text-gray-300">现货</span>
        </div>
        <div class="h-4 w-[1px] bg-[#232936]"></div>
        <div class="font-mono text-lg font-bold text-white">
          ${{ currentToken ? currentToken.price.toLocaleString() : '--' }}
        </div>
        <div
          v-if="currentToken"
          class="text-xs font-semibold px-2 py-0.5 rounded font-mono"
          :class="currentToken.change_24h >= 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'"
        >
          {{ currentToken.change_24h >= 0 ? '+' : '' }}{{ currentToken.change_24h }}%
        </div>
      </div>

      <!-- 右侧：图表模式与周期选择器 -->
      <div class="flex items-center space-x-2">
        <!-- 模式切换：K线 / 分时 / 深度 -->
        <div class="flex items-center bg-[#0B0E14] p-0.5 rounded-lg border border-[#232936]">
          <button
            v-for="mode in (['kline', 'area', 'depth'] as const)"
            :key="mode"
            @click="chartType = mode"
            class="px-2.5 py-1 text-xs rounded font-medium transition-all"
            :class="chartType === mode ? 'bg-[#232936] text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'"
          >
            {{ mode === 'kline' ? 'K线图' : (mode === 'area' ? '分时走势' : '深度盘口') }}
          </button>
        </div>

        <!-- 周期切换 (K线与分时模式有效) -->
        <div v-if="chartType !== 'depth'" class="flex items-center bg-[#0B0E14] p-0.5 rounded-lg border border-[#232936]">
          <button
            v-for="tf in ['1m', '5m', '1h', '1d']"
            :key="tf"
            @click="store.setTimeframe(tf)"
            class="px-2 py-1 text-xs rounded font-mono transition-all"
            :class="store.currentTimeframe === tf ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-gray-200'"
          >
            {{ tf }}
          </button>
        </div>
      </div>
    </div>

    <!-- ECharts 容器 -->
    <div class="flex-1 w-full relative mt-2 min-h-[300px]">
      <div ref="chartRef" class="w-full h-full"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import * as echarts from 'echarts'
import { usePriceStore } from '../stores/priceStore'

const store = usePriceStore()
const chartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

const chartType = ref<'kline' | 'area' | 'depth'>('kline')
const currentToken = computed(() => store.selectedToken)

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value, 'dark', {
    renderer: 'canvas'
  })
  updateChartOptions()
}

const calculateMA = (dayCount: number, data: any[]) => {
  const result: (number | string)[] = []
  for (let i = 0, len = data.length; i < len; i++) {
    if (i < dayCount) {
      result.push('-')
      continue
    }
    let sum = 0
    for (let j = 0; j < dayCount; j++) {
      sum += data[i - j][1] // close price
    }
    result.push(+(sum / dayCount).toFixed(4))
  }
  return result
}

const updateChartOptions = () => {
  if (!chartInstance) return

  if (chartType.value === 'depth') {
    renderDepthChart()
    return
  }

  if (chartType.value === 'area') {
    renderAreaChart()
    return
  }

  renderKlineChart()
}

const renderKlineChart = () => {
  if (!chartInstance) return
  const rawData = store.klineData
  if (!rawData || rawData.length === 0) return

  const dates = rawData.map((d) => {
    const date = new Date(d.timestamp)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  })
  // [open, close, lowest, highest]
  const values = rawData.map((d) => [d.open, d.close, d.low, d.high])
  const volumes = rawData.map((d, i) => [i, d.volume, d.close >= d.open ? 1 : -1])
  const ma5 = calculateMA(5, values)
  const ma20 = calculateMA(20, values)

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    animation: false,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', lineStyle: { color: '#4B5563', type: 'dashed' } },
      backgroundColor: '#1E2430',
      borderColor: '#374151',
      textStyle: { color: '#F3F4F6', fontSize: 11 }
    },
    grid: [
      { left: '3%', right: '4%', top: '8%', height: '65%' },
      { left: '3%', right: '4%', top: '78%', height: '16%' }
    ],
    xAxis: [
      {
        type: 'category',
        data: dates,
        gridIndex: 0,
        axisLine: { lineStyle: { color: '#2D3748' } },
        axisLabel: { color: '#718096', fontSize: 10 }
      },
      {
        type: 'category',
        data: dates,
        gridIndex: 1,
        axisLine: { lineStyle: { color: '#2D3748' } },
        axisLabel: { show: false }
      }
    ],
    yAxis: [
      {
        scale: true,
        gridIndex: 0,
        splitLine: { lineStyle: { color: '#1F2733', type: 'dashed' } },
        axisLabel: { color: '#718096', fontSize: 10 }
      },
      {
        scale: true,
        gridIndex: 1,
        splitLine: { show: false },
        axisLabel: { show: false }
      }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: values,
        itemStyle: {
          color: '#10B981',
          color0: '#EF4444',
          borderColor: '#10B981',
          borderColor0: '#EF4444'
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: ma5,
        smooth: true,
        showSymbol: false,
        lineStyle: { opacity: 0.8, width: 1.2, color: '#38BDF8' }
      },
      {
        name: 'MA20',
        type: 'line',
        data: ma20,
        smooth: true,
        showSymbol: false,
        lineStyle: { opacity: 0.8, width: 1.2, color: '#F59E0B' }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes.map((v) => ({
          value: v[1],
          itemStyle: { color: v[2] === 1 ? '#10B98188' : '#EF444488' }
        }))
      }
    ]
  }

  chartInstance.setOption(option, true)
}

const renderAreaChart = () => {
  if (!chartInstance) return
  const rawData = store.klineData
  if (!rawData || rawData.length === 0) return

  const dates = rawData.map((d) => {
    const date = new Date(d.timestamp)
    return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  })
  const prices = rawData.map((d) => d.close)

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#3B82F6', type: 'dashed' } },
      backgroundColor: '#1E2430',
      borderColor: '#374151',
      textStyle: { color: '#F3F4F6' }
    },
    grid: { left: '3%', right: '3%', top: '8%', bottom: '8%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2D3748' } },
      axisLabel: { color: '#718096', fontSize: 10 }
    },
    yAxis: {
      scale: true,
      splitLine: { lineStyle: { color: '#1F2733', type: 'dashed' } },
      axisLabel: { color: '#718096', fontSize: 10 }
    },
    series: [
      {
        name: '价格走势',
        type: 'line',
        data: prices,
        smooth: true,
        showSymbol: false,
        lineStyle: { color: '#3B82F6', width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(59, 130, 246, 0.35)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.00)' }
          ])
        }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

const renderDepthChart = () => {
  if (!chartInstance || !store.depthData) return
  const bids = store.depthData.bids || []
  const asks = store.depthData.asks || []

  const bidData = bids.map((b) => [b.price, b.total]).reverse()
  const askData = asks.map((a) => [a.price, a.total])

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1E2430',
      borderColor: '#374151',
      textStyle: { color: '#F3F4F6' }
    },
    grid: { left: '3%', right: '3%', top: '8%', bottom: '8%' },
    xAxis: {
      type: 'value',
      scale: true,
      axisLine: { lineStyle: { color: '#2D3748' } },
      axisLabel: { color: '#718096', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: '#1F2733', type: 'dashed' } },
      axisLabel: { color: '#718096', fontSize: 10 }
    },
    series: [
      {
        name: '买盘深度',
        type: 'line',
        data: bidData,
        step: 'start',
        showSymbol: false,
        lineStyle: { color: '#10B981', width: 2 },
        areaStyle: { color: 'rgba(16, 185, 129, 0.25)' }
      },
      {
        name: '卖盘深度',
        type: 'line',
        data: askData,
        step: 'end',
        showSymbol: false,
        lineStyle: { color: '#EF4444', width: 2 },
        areaStyle: { color: 'rgba(239, 68, 68, 0.25)' }
      }
    ]
  }

  chartInstance.setOption(option, true)
}

const handleResize = () => {
  chartInstance?.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

watch(() => [store.klineData, store.depthData, chartType.value], () => {
  updateChartOptions()
}, { deep: true })
</script>
