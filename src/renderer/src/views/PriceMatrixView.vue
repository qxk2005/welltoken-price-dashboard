<template>
  <div class="h-full flex flex-col space-y-2.5 overflow-hidden select-none">
    <!-- 顶部四级联动多维筛选栏 (苹果灰白卡片) -->
    <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2">
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

          <!-- 2. 模型系列多选 (联动收敛) -->
          <MultiSelectFilter
            label="模型系列"
            icon="📦"
            :options="seriesOptions"
            v-model="selectedSeries"
          />

          <!-- 3. 模型名称多选 (联动收敛) -->
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
          <span class="text-[#6E6E73]">
            全网匹配: <strong class="text-[#0071E3] font-mono font-bold">{{ totalRecords }}</strong> 条报价
          </span>
          <button
            v-if="hasAnyFilter"
            @click="resetAllFilters"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#FFE5E5] text-[#6E6E73] hover:text-[#FF3B30] border border-[#E5E5EA] transition-all text-xs"
          >
            重置筛选
          </button>
        </div>
      </div>

      <!-- 第二行：已选标签 Chips 展示条 (如果有选择) -->
      <div v-if="hasAnyFilter" class="flex items-center flex-wrap gap-1.5 pt-1.5 border-t border-[#E5E5EA] text-xs">
        <span class="text-[11px] text-[#86868B] font-medium">当前筛选:</span>

        <!-- 厂商 Chips -->
        <span
          v-for="p in selectedProviders"
          :key="`p-${p}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] text-[11px] font-medium"
        >
          <span>🏢 {{ p }}</span>
          <button @click="removeProvider(p)" class="hover:text-[#004BB3] ml-0.5">✕</button>
        </span>

        <!-- 系列 Chips -->
        <span
          v-for="s in selectedSeries"
          :key="`s-${s}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#F3E8FF] border border-[#E9D5FF] text-[#9333EA] text-[11px] font-medium"
        >
          <span>📦 {{ s }}</span>
          <button @click="removeSeries(s)" class="hover:text-[#6B21A8] ml-0.5">✕</button>
        </span>

        <!-- 模型 Chips -->
        <span
          v-for="m in selectedModels"
          :key="`m-${m}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#EDE9FE] border border-[#DDD6FE] text-[#7C3AED] text-[11px] font-mono font-medium"
        >
          <span>🤖 {{ m }}</span>
          <button @click="removeModel(m)" class="hover:text-[#5B21B6] ml-0.5">✕</button>
        </span>

        <!-- 渠道 Chips -->
        <span
          v-for="st in selectedSites"
          :key="`st-${st}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E6F4EA] border border-[#CEEAD6] text-[#137333] text-[11px] font-medium"
        >
          <span>🌐 {{ st }}</span>
          <button @click="removeSite(st)" class="hover:text-[#0D652D] ml-0.5">✕</button>
        </span>
      </div>
    </div>

    <!-- 价格对比大矩阵 (数据表格) -->
    <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-0">
      <!-- 表头 -->
      <div class="grid grid-cols-12 gap-2 text-[11px] text-[#6E6E73] font-bold px-3 py-2 border-b border-[#E5E5EA] bg-[#F9F9FB] rounded-t-xl">
        <div class="col-span-2">模型系列 / 厂商</div>
        <div class="col-span-3">模型标准标识</div>
        <div class="col-span-2">渠道 / 供应商</div>
        <div class="col-span-1">类型</div>
        <div class="col-span-1 text-right">输入单价</div>
        <div class="col-span-1 text-right">输出单价</div>
        <div class="col-span-1 text-center">倍率</div>
        <div class="col-span-1 text-right">实测 TPS</div>
      </div>

      <!-- 数据行列表 (仅渲染当前页 50 条，极速流畅 60 FPS) -->
      <div class="flex-1 overflow-y-auto divide-y divide-[#E5E5EA]/60 pr-1 mt-1 relative">
        <div v-if="isLoading" class="absolute inset-0 bg-white/70 backdrop-blur-xs flex items-center justify-center z-10">
          <div class="text-xs text-[#0071E3] font-medium flex items-center space-x-2">
            <span class="animate-spin">🌀</span>
            <span>加载报价数据中...</span>
          </div>
        </div>

        <div
          v-for="row in pagedItems"
          :key="row.id"
          @click="selectRow(row)"
          class="grid grid-cols-12 gap-2 items-center px-3 py-2 text-xs transition-colors cursor-pointer rounded-xl"
          :class="selectedRow?.id === row.id ? 'bg-[#E8F2FD] border border-[#CCE4FB]' : 'hover:bg-[#F5F5F7]'"
        >
          <!-- 系列与厂商 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <span class="px-1.5 py-0.2 rounded bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] text-[10px] font-mono">
              {{ row.provider.toUpperCase() }}
            </span>
            <span class="text-[#1D1D1F] font-medium truncate text-[11px]">{{ row.series || '通用' }}</span>
          </div>

          <!-- 模型标识 -->
          <div class="col-span-3 flex items-center space-x-1.5 truncate">
            <span class="font-bold text-[#0071E3] font-mono truncate text-xs" :title="row.model_id">{{ row.model_id }}</span>
          </div>

          <!-- 渠道站点 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <span class="font-semibold text-[#1D1D1F] truncate text-xs" :title="row.site_name">{{ row.site_name }}</span>
          </div>

          <!-- 类型徽标 -->
          <div class="col-span-1">
            <span
              class="px-1.5 py-0.2 rounded text-[9px] font-mono font-semibold uppercase"
              :class="getTypeBadgeClass(row.site_type)"
            >
              {{ row.site_type }}
            </span>
          </div>

          <!-- 输入价格 -->
          <div class="col-span-1 text-right font-mono font-bold text-[#34C759] text-xs">
            {{ formatPrice(row.calculated_input_usd, row.calculated_input_cny) }}
          </div>

          <!-- 输出价格 -->
          <div class="col-span-1 text-right font-mono text-[#1D1D1F] text-xs">
            {{ formatPrice(row.calculated_output_usd, row.calculated_output_cny) }}
          </div>

          <!-- 倍率 -->
          <div class="col-span-1 text-center font-mono text-[#6E6E73] font-semibold text-xs">
            {{ row.model_ratio }}x
          </div>

          <!-- 实测 TPS -->
          <div class="col-span-1 text-right font-mono text-[#0071E3] font-bold text-xs">
            {{ row.last_tested_tps }} <span class="text-[9px] text-[#86868B] font-normal">tps</span>
          </div>
        </div>

        <div v-if="!isLoading && pagedItems.length === 0" class="py-12 text-center text-xs text-[#86868B]">
          无匹配的大模型比价数据，请调整筛选条件
        </div>
      </div>

      <!-- 底部精致高性能分页控制栏 (苹果浅灰按钮组) -->
      <div class="pt-2.5 border-t border-[#E5E5EA] flex items-center justify-between text-xs text-[#6E6E73]">
        <!-- 左侧信息 -->
        <div class="flex items-center space-x-3 text-[11px]">
          <span>
            第 <strong class="text-[#1D1D1F] font-mono">{{ currentPage }}</strong> / <span class="font-mono">{{ totalPages }}</span> 页
            (共 <strong class="text-[#0071E3] font-mono">{{ totalRecords }}</strong> 条)
          </span>
          <div class="flex items-center space-x-1">
            <span>每页</span>
            <select
              v-model="pageSize"
              class="bg-[#F2F2F7] border border-[#E5E5EA] rounded-md px-1.5 py-0.5 text-[#1D1D1F] font-mono text-xs focus:outline-none focus:border-[#0071E3]"
            >
              <option :value="20">20 条</option>
              <option :value="50">50 条</option>
              <option :value="100">100 条</option>
            </select>
          </div>
        </div>

        <!-- 中间页码翻页控制器 -->
        <div class="flex items-center space-x-1 font-mono">
          <button
            :disabled="currentPage <= 1"
            @click="changePage(1)"
            class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
            title="首页"
          >
            «
          </button>
          <button
            :disabled="currentPage <= 1"
            @click="changePage(currentPage - 1)"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
          >
            ◀ 上一页
          </button>

          <!-- 数字页码按钮组 -->
          <div class="flex items-center space-x-1">
            <button
              v-for="p in visiblePages"
              :key="`page-${p}`"
              @click="changePage(p)"
              class="w-7 h-7 rounded-lg text-[11px] font-bold transition-all flex items-center justify-center"
              :class="
                currentPage === p
                  ? 'bg-[#0071E3] text-white shadow-xs'
                  : 'bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA]'
              "
            >
              {{ p }}
            </button>
          </div>

          <button
            :disabled="currentPage >= totalPages"
            @click="changePage(currentPage + 1)"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
          >
            下一页 ▶
          </button>
          <button
            :disabled="currentPage >= totalPages"
            @click="changePage(totalPages)"
            class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-40 text-[#1D1D1F] border border-[#E5E5EA] text-[11px]"
            title="末页"
          >
            »
          </button>
        </div>
      </div>
    </div>

    <!-- 底部：全网价格-TPS 性价比散点图 (ECharts 浅色苹果风格) -->
    <div class="h-36 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] p-2.5 shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex flex-col">
      <div class="flex items-center justify-between pb-1 border-b border-[#E5E5EA]">
        <div class="flex items-center space-x-2 text-xs font-bold text-[#1D1D1F]">
          <span>📈 全网性价比散点分布 (当前模型: {{ activeScatterModelId }})</span>
          <span class="text-[10px] text-[#86868B] font-normal">| 越偏左上角（价格低、TPS 高）综合性价比越高</span>
        </div>
      </div>
      <div class="flex-1 w-full relative min-h-0 mt-0.5">
        <div ref="scatterChartRef" class="w-full h-full"></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import axios from 'axios'
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

// 筛选候选项数据
const providerOptions = ref<FilterOption[]>([])
const seriesOptions = ref<FilterOption[]>([])
const modelOptions = ref<FilterOption[]>([])
const siteOptions = ref<FilterOption[]>([])

// 分页状态
const pagedItems = ref<ComparisonItem[]>([])
const totalRecords = ref(0)
const totalPages = ref(1)
const currentPage = ref(1)
const pageSize = ref(50)
const isLoading = ref(false)

const scatterChartRef = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null
const selectedRow = ref<ComparisonItem | null>(null)

// 异步获取筛选器候选选项
const fetchFilterOptions = async () => {
  try {
    const params: any = {}
    if (selectedProviders.value.length > 0) params.provider = selectedProviders.value
    if (selectedSeries.value.length > 0) params.series = selectedSeries.value

    const res = await axios.get(`${store.apiUrl}/api/v1/comparison/filter-options`, { params })
    providerOptions.value = res.data.providers
    seriesOptions.value = res.data.series
    modelOptions.value = res.data.models
    siteOptions.value = res.data.sites
  } catch (e) {
    console.error('Fetch filter options failed:', e)
  }
}

// 核心高性能分页拉取方法 (毫秒级响应)
const fetchPaginatedData = async () => {
  isLoading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (selectedProviders.value.length > 0) params.provider = selectedProviders.value
    if (selectedSeries.value.length > 0) params.series = selectedSeries.value
    if (selectedModels.value.length > 0) params.model = selectedModels.value
    if (selectedSites.value.length > 0) params.site = selectedSites.value
    if (store.searchQuery.trim()) params.search = store.searchQuery.trim()

    const res = await axios.get(`${store.apiUrl}/api/v1/comparison/paginated`, { params })
    pagedItems.value = res.data.items
    totalRecords.value = res.data.total
    totalPages.value = res.data.total_pages
    currentPage.value = res.data.page

    if (pagedItems.value.length > 0 && !selectedRow.value) {
      selectedRow.value = pagedItems.value[0]
    }
    updateScatterChart()
  } catch (e) {
    console.error('Fetch paginated data failed:', e)
  } finally {
    isLoading.value = false
  }
}

const changePage = (p: number) => {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  fetchPaginatedData()
}

// 计算当前页码周围可见的页码数字
const visiblePages = computed(() => {
  const cur = currentPage.value
  const total = totalPages.value
  const pages: number[] = []
  const start = Math.max(1, cur - 2)
  const end = Math.min(total, cur + 2)
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  return pages
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
  currentPage.value = 1
  fetchPaginatedData()
}

const formatPrice = (usd: number, cny: number) => {
  if (store.currency === 'CNY') {
    return `￥${cny.toFixed(3)}`
  }
  return `$${usd >= 1 ? usd.toFixed(2) : usd.toFixed(3)}`
}

const getTypeBadgeClass = (type: string) => {
  if (type === 'official') return 'bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA]'
  if (type === 'cloud') return 'bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]'
  if (type === 'newapi') return 'bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6]'
  if (type === 'sub2api') return 'bg-[#F3E8FF] text-[#9333EA] border border-[#E9D5FF]'
  return 'bg-[#F2F2F7] text-[#1D1D1F]'
}

const selectRow = (row: ComparisonItem) => {
  selectedRow.value = row
  updateScatterChart()
}

const activeScatterModelId = computed(() => {
  if (selectedRow.value) return selectedRow.value.model_id
  if (selectedModels.value.length === 1) return selectedModels.value[0]
  if (pagedItems.value.length > 0) return pagedItems.value[0].model_id
  return 'deepseek/deepseek-v4-flash'
})

const initChart = () => {
  if (!scatterChartRef.value) return
  chartInstance = echarts.init(scatterChartRef.value, undefined, { renderer: 'canvas' })
  updateScatterChart()
}

const updateScatterChart = () => {
  if (!chartInstance) return
  const currentModelId = activeScatterModelId.value
  const items = pagedItems.value.filter((item) => item.model_id === currentModelId)
  const displayItems = items.length > 0 ? items : pagedItems.value.slice(0, 15)

  const data = displayItems.map((item) => [
    item.calculated_input_usd,
    item.last_tested_tps,
    item.site_name,
    item.discount_percent,
    item.site_type
  ])

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E5EA',
      textStyle: { color: '#1D1D1F', fontSize: 11 },
      extraCssText: 'box-shadow: 0 4px 16px rgba(0,0,0,0.08); border-radius: 8px;',
      formatter: (params: any) => {
        const val = params.value
        return `<strong>${val[2]}</strong> (${val[4]})<br/>输入单价: $${val[0]}/1M<br/>实测 TPS: ${val[1]} tps<br/>折扣: ${val[3]}%`
      }
    },
    grid: { left: '4%', right: '4%', top: '15%', bottom: '18%' },
    xAxis: {
      name: '输入单价 ($/1M)',
      nameLocation: 'end',
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#F2F2F7', type: 'solid' } },
      axisLabel: { color: '#86868B', fontSize: 10 }
    },
    yAxis: {
      name: '生成速率 (TPS)',
      type: 'value',
      scale: true,
      splitLine: { lineStyle: { color: '#F2F2F7', type: 'solid' } },
      axisLabel: { color: '#86868B', fontSize: 10 }
    },
    series: [
      {
        name: '性价比点',
        type: 'scatter',
        symbolSize: 18,
        data: data,
        itemStyle: {
          color: (params: any) => {
            const type = params.value[4]
            if (type === 'official') return '#6E6E73'
            if (type === 'cloud') return '#0071E3'
            if (type === 'newapi') return '#34C759'
            if (type === 'sub2api') return '#AF52DE'
            return '#0071E3'
          },
          shadowBlur: 6,
          shadowColor: 'rgba(0, 0, 0, 0.08)'
        }
      }
    ]
  }
  chartInstance.setOption(option, true)
}

const handleResize = () => chartInstance?.resize()

onMounted(async () => {
  await fetchFilterOptions()
  await fetchPaginatedData()
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

// 监听筛选条件与分页变化
watch(
  [selectedProviders, selectedSeries, selectedModels, selectedSites, () => store.searchQuery, pageSize],
  () => {
    currentPage.value = 1
    fetchPaginatedData()
    fetchFilterOptions()
  },
  { deep: true }
)

watch(() => [store.currency, activeScatterModelId.value], () => {
  updateScatterChart()
})
</script>
