<template>
  <div class="h-full flex flex-col space-y-2.5 overflow-hidden select-none">
    <!-- 顶部四级联动多维筛选栏 (苹果灰白卡片) -->
    <div class="p-3 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] space-y-2">
      <!-- 第一行：四大维度可搜索多选下拉 + 收藏快捷切换 (全部支持字母 A-Z 升序排序) -->
      <div class="flex items-center justify-between flex-wrap gap-2">
        <div class="flex items-center flex-wrap gap-2">
          <!-- 1. 模型厂商多选 (A-Z 排序，支持中文别名模糊搜索 如“深度探索”) -->
          <MultiSelectFilter
            label="模型厂商"
            icon="🏢"
            :options="sortedProviderOptions"
            :model-value="selectedProviders"
            @update:model-value="handleProviderChange"
          />

          <!-- 2. 模型系列多选 (A-Z 排序，根据已选厂商级联收敛) -->
          <MultiSelectFilter
            label="模型系列"
            icon="📦"
            :options="sortedSeriesOptions"
            :model-value="selectedSeries"
            @update:model-value="handleSeriesChange"
          />

          <!-- 3. 模型名称多选 (A-Z 排序，保留前面的厂商与系列) -->
          <MultiSelectFilter
            label="模型名称"
            icon="🤖"
            :options="sortedModelOptions"
            :model-value="selectedModels"
            @update:model-value="handleModelChange"
          />

          <!-- 4. 渠道中转站多选 (A-Z 排序，支持模糊搜索 如“七牛”, “OpenRouter”, “硅基”) -->
          <MultiSelectFilter
            label="渠道中转站"
            icon="🌐"
            :options="sortedSiteOptions"
            :model-value="selectedSites"
            @update:model-value="handleSiteChange"
          />

          <!-- 5. 仅看已收藏渠道快捷胶囊 -->
          <button
            @click="toggleOnlyFavorites"
            class="px-3 py-1.5 rounded-xl border text-xs font-medium transition-all flex items-center space-x-1"
            :class="onlyFavorites ? 'bg-[#FFF8E1] border-[#FFE082] text-[#B78103] font-bold shadow-xs' : 'bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
          >
            <span>{{ onlyFavorites ? '⭐ 已开启仅看收藏' : '☆ 仅看已收藏渠道' }}</span>
            <span v-if="store.favoriteSiteIds.length > 0" class="text-[10px] font-mono opacity-80">({{ store.favoriteSiteIds.length }})</span>
          </button>
        </div>

        <!-- 右侧：快捷操作与匹配统计 -->
        <div class="flex items-center space-x-2 text-xs">
          <span class="text-[#6E6E73]">
            全网匹配: <strong class="text-[#0071E3] font-mono font-bold">{{ totalRecords }}</strong> 条报价
          </span>
          <button
            v-if="hasAnyFilter || onlyFavorites"
            @click="resetAllFilters"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#FFE5E5] text-[#6E6E73] hover:text-[#FF3B30] border border-[#E5E5EA] transition-all text-xs"
          >
            重置筛选
          </button>
        </div>
      </div>

      <!-- 第二行：已选标签 Chips 展示条 (如果有选择) -->
      <div v-if="hasAnyFilter || onlyFavorites" class="flex items-center flex-wrap gap-1.5 pt-1.5 border-t border-[#E5E5EA] text-xs">
        <span class="text-[11px] text-[#86868B] font-medium">当前筛选:</span>

        <!-- 收藏状态 Chip -->
        <span
          v-if="onlyFavorites"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#FFF8E1] border border-[#FFE082] text-[#B78103] text-[11px] font-medium"
        >
          <span>⭐ 仅看已收藏渠道</span>
          <button @click="onlyFavorites = false" class="hover:text-[#8C6300] ml-0.5">✕</button>
        </span>

        <!-- 厂商 Chips -->
        <span
          v-for="p in selectedProviders"
          :key="`p-${p}`"
          class="inline-flex items-center space-x-1 px-2 py-0.5 rounded-full bg-[#E8F2FD] border border-[#CCE4FB] text-[#0071E3] text-[11px] font-medium"
        >
          <span>🏢 {{ getProviderLabel(p) }}</span>
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
      <!-- 表头 (支持点击多列排序) -->
      <div class="grid grid-cols-12 gap-2 text-[11px] text-[#6E6E73] font-bold px-3 py-2 border-b border-[#E5E5EA] bg-[#F9F9FB] rounded-t-xl select-none">
        <div class="col-span-2">模型系列 / 厂商</div>
        <div @click="toggleSort('model_id')" class="col-span-3 cursor-pointer hover:text-[#0071E3] transition-colors flex items-center space-x-1">
          <span>模型标准标识</span>
          <span class="text-[10px] font-mono" :class="sortField === 'model_id' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('model_id') }}</span>
        </div>
        <div @click="toggleSort('site_name')" class="col-span-2 cursor-pointer hover:text-[#0071E3] transition-colors flex items-center space-x-1">
          <span>渠道 / 供应商</span>
          <span class="text-[10px] font-mono" :class="sortField === 'site_name' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('site_name') }}</span>
        </div>
        <div class="col-span-1">类型</div>
        <div @click="toggleSort('calculated_input_usd')" class="col-span-1 text-right cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-end space-x-1">
          <span>输入单价 ({{ store.currency }})</span>
          <span class="text-[10px] font-mono" :class="sortField === 'calculated_input_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('calculated_input_usd') }}</span>
        </div>
        <div @click="toggleSort('calculated_output_usd')" class="col-span-1 text-right cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-end space-x-1">
          <span>输出单价 ({{ store.currency }})</span>
          <span class="text-[10px] font-mono" :class="sortField === 'calculated_output_usd' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('calculated_output_usd') }}</span>
        </div>
        <div @click="toggleSort('model_ratio')" class="col-span-1 text-center cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-center space-x-1">
          <span>倍率</span>
          <span class="text-[10px] font-mono" :class="sortField === 'model_ratio' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('model_ratio') }}</span>
        </div>
        <div @click="toggleSort('last_tested_tps')" class="col-span-1 text-right cursor-pointer hover:text-[#0071E3] transition-colors flex items-center justify-end space-x-1">
          <span>实测 TPS</span>
          <span class="text-[10px] font-mono" :class="sortField === 'last_tested_tps' ? 'text-[#0071E3] font-bold' : 'text-[#AEAEB2]'">{{ getSortIndicator('last_tested_tps') }}</span>
        </div>
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
            <span class="px-1.5 py-0.2 rounded bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] text-[10px] font-mono font-bold">
              {{ row.provider.toUpperCase() }}
            </span>
            <span class="text-[#1D1D1F] font-medium truncate text-[11px]">{{ row.series || '通用' }}</span>
          </div>

          <!-- 模型标识 -->
          <div class="col-span-3 flex items-center space-x-1.5 truncate">
            <span class="font-bold text-[#0071E3] font-mono truncate text-xs" :title="row.model_id">{{ row.model_id }}</span>
          </div>

          <!-- 渠道站点与收藏星标 -->
          <div class="col-span-2 flex items-center space-x-1.5 truncate">
            <button
              @click.stop="toggleFavoriteByName(row.site_name)"
              class="text-xs transition-transform hover:scale-125 focus:outline-none"
              :title="isSiteNameFavorite(row.site_name) ? '点击取消收藏' : '点击收藏该渠道'"
            >
              <span v-if="isSiteNameFavorite(row.site_name)" class="text-[#FF9500]">⭐</span>
              <span v-else class="text-[#AEAEB2] hover:text-[#FF9500]">☆</span>
            </button>
            <div class="flex items-center space-x-1 truncate">
              <span class="font-semibold text-[#1D1D1F] truncate text-xs" :title="row.site_name">{{ row.site_name }}</span>
              <span
                v-if="row.group_name"
                class="px-1 py-0.2 rounded bg-[#F3E8FD] text-[#8E24AA] border border-[#E1BEE7] text-[9px] font-mono font-bold truncate flex-shrink-0 shadow-2xs"
                :title="`结算分组: ${row.group_name}`"
              >
                {{ row.group_name }}
              </span>
            </div>
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
              @change="handlePageSizeChange"
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
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import { useDashboardStore } from '../stores/dashboardStore'
import MultiSelectFilter, { type FilterOption } from '../components/MultiSelectFilter.vue'
import type { ComparisonItem } from '../types'

const store = useDashboardStore()

// 厂商中文与别名映射表 (支持用户输入“深度探索”、“通义千问”、“Kimi”等模糊搜索)
const labNamesCn: Record<string, string> = {
  openai: 'OpenAI (ChatGPT)',
  anthropic: 'Anthropic (Claude)',
  google: 'Google (谷歌/Gemini)',
  deepseek: 'DeepSeek (深度求索/深度探索)',
  alibaba: 'Alibaba (阿里巴巴/通义千问/Qwen)',
  moonshotai: 'Moonshot AI (月之暗面/Kimi)',
  zhipuai: 'Zhipu AI (智谱/GLM)',
  bytedance: 'ByteDance (字节跳动/豆包)',
  tencent: 'Tencent (腾讯/混元)',
  minimax: 'MiniMax (名之梦)',
  meta: 'Meta (Facebook/Llama)',
  mistral: 'Mistral AI (欧洲顶尖开源)',
  nvidia: 'Nvidia (英伟达/Nemotron)',
  xai: 'xAI (马斯克/Grok)',
  cohere: 'Cohere (Command R)',
  stepfun: 'StepFun (阶跃星辰/跃问)',
  baichuan: 'Baichuan (百川智能)',
  xiaomi: 'Xiaomi (小米大模型)',
  microsoft: 'Microsoft (微软/MAI)',
  cloudflare: 'Cloudflare (Workers AI)',
  upstage: 'Upstage (Solar)',
  perplexity: 'Perplexity (AI 搜索)',
  meituan: 'Meituan (美团大模型)',
  internlm: 'InternLM (书生·浦语)',
  '01-ai': '01.AI (零一万物/Yi)',
  other: '其他独立研究机构 (Other)'
}

// 选中的多维筛选状态
const selectedProviders = ref<string[]>([])
const selectedSeries = ref<string[]>([])
const selectedModels = ref<string[]>([])
const selectedSites = ref<string[]>([])
const onlyFavorites = ref(false)

// 筛选候选项原始数据
const rawProviderOptions = ref<FilterOption[]>([])
const rawSeriesOptions = ref<FilterOption[]>([])
const rawModelOptions = ref<FilterOption[]>([])
const rawSiteOptions = ref<FilterOption[]>([])

// 1. 厂商候选列表：带中文别名 + 按字母 A-Z 严格排序 (除 other 置底)
const sortedProviderOptions = computed<FilterOption[]>(() => {
  const mapped = rawProviderOptions.value.map((opt) => {
    const key = opt.value.toLowerCase()
    const cnName = labNamesCn[key]
    return {
      value: opt.value,
      label: cnName || opt.label || opt.value,
      count: opt.count
    }
  })

  return mapped.sort((a, b) => {
    if (a.value === 'other') return 1
    if (b.value === 'other') return -1
    return a.label.localeCompare(b.label, 'zh-CN', { sensitivity: 'base' })
  })
})

// 2. 系列候选列表：按字母 A-Z 严格升序排序
const sortedSeriesOptions = computed<FilterOption[]>(() => {
  return [...rawSeriesOptions.value].sort((a, b) => {
    return a.label.localeCompare(b.label, 'zh-CN', { numeric: true, sensitivity: 'base' })
  })
})

// 3. 模型候选列表：按字母 A-Z 严格升序排序
const sortedModelOptions = computed<FilterOption[]>(() => {
  return [...rawModelOptions.value].sort((a, b) => {
    return a.label.localeCompare(b.label, 'zh-CN', { numeric: true, sensitivity: 'base' })
  })
})

// 4. 渠道候选列表：按字母 A-Z 严格升序排序
const sortedSiteOptions = computed<FilterOption[]>(() => {
  return [...rawSiteOptions.value].sort((a, b) => {
    return a.label.localeCompare(b.label, 'zh-CN', { numeric: true, sensitivity: 'base' })
  })
})

const getProviderLabel = (p: string) => {
  const key = p.toLowerCase()
  return labNamesCn[key] || p.toUpperCase()
}

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

// 构造标准的 URLSearchParams 请求参数，彻底解决 Axios 数组带 [] 导致 FastAPI 忽略参数的问题
const buildSearchParams = (paramsObj: Record<string, any>): URLSearchParams => {
  const sp = new URLSearchParams()
  for (const [k, v] of Object.entries(paramsObj)) {
    if (Array.isArray(v)) {
      for (const item of v) {
        if (item) sp.append(k, item)
      }
    } else if (v !== undefined && v !== null && v !== '') {
      sp.append(k, String(v))
    }
  }
  return sp
}

// 异步获取筛选器候选选项 (根据已选维度进行四级级联联动收敛)
const fetchFilterOptions = async (
  customProviders?: string[],
  customSeries?: string[],
  customModels?: string[]
) => {
  try {
    const providersToUse = customProviders !== undefined ? customProviders : selectedProviders.value
    const seriesToUse = customSeries !== undefined ? customSeries : selectedSeries.value
    const modelsToUse = customModels !== undefined ? customModels : selectedModels.value

    const params: Record<string, any> = {}
    if (providersToUse.length > 0) params.provider = providersToUse
    if (seriesToUse.length > 0) params.series = seriesToUse
    if (modelsToUse.length > 0) params.model = modelsToUse
    if (selectedSites.value.length > 0) params.site = selectedSites.value

    const sp = buildSearchParams(params)
    const res = await axios.get(`${store.apiUrl}/api/v1/comparison/filter-options?${sp.toString()}`)
    rawProviderOptions.value = res.data.providers || []
    rawSeriesOptions.value = res.data.series || []
    rawModelOptions.value = res.data.models || []
    rawSiteOptions.value = res.data.sites || []
  } catch (e) {
    console.error('Fetch filter options failed:', e)
  }
}

// 排序状态
const sortField = ref<string>('calculated_input_usd')
const sortOrder = ref<'asc' | 'desc'>('asc')

const toggleSort = (field: string) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    // 实测 TPS 默认从高到低排序，价格/倍率默认从低到高排序
    sortOrder.value = field === 'last_tested_tps' ? 'desc' : 'asc'
  }
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const getSortIndicator = (field: string) => {
  if (sortField.value !== field) return '↕'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

// 异步分页拉取比价数据
const fetchPaginatedMatrix = async () => {
  isLoading.value = true
  try {
    let effectiveSites = [...selectedSites.value]
    if (onlyFavorites.value) {
      const favNames = store.favoriteSites.map((s) => s.name)
      if (favNames.length > 0) {
        effectiveSites = effectiveSites.length > 0 ? effectiveSites.filter((n) => favNames.includes(n)) : favNames
      } else {
        effectiveSites = ['__NONE__']
      }
    }

    const params: Record<string, any> = {
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: sortField.value,
      sort_order: sortOrder.value
    }
    if (selectedProviders.value.length > 0) params.provider = selectedProviders.value
    if (selectedSeries.value.length > 0) params.series = selectedSeries.value
    if (selectedModels.value.length > 0) params.model = selectedModels.value
    if (effectiveSites.length > 0) params.site = effectiveSites

    const sp = buildSearchParams(params)
    const res = await axios.get(`${store.apiUrl}/api/v1/comparison/paginated?${sp.toString()}`)
    pagedItems.value = res.data.items || []
    totalRecords.value = res.data.total || 0
    totalPages.value = res.data.total_pages || res.data.pages || 1
    currentPage.value = res.data.page || 1

    if (pagedItems.value.length > 0 && !selectedRow.value) {
      selectedRow.value = pagedItems.value[0]
    }
    updateScatterChart()
  } catch (e) {
    console.error('Fetch paginated matrix failed:', e)
  } finally {
    isLoading.value = false
  }
}

// ==================== 核心联动控制规则 ====================

// 1. 用户变更【模型厂商】-> 触发系列与模型收敛，清洗失效已选项
const handleProviderChange = async (newProviders: string[]) => {
  selectedProviders.value = newProviders
  currentPage.value = 1

  // 刷新级联候选项
  await fetchFilterOptions(newProviders, [], [])

  // 若已选系列不在新候选池中，清空系列
  if (selectedSeries.value.length > 0) {
    const validSeries = new Set(rawSeriesOptions.value.map((s) => s.value))
    selectedSeries.value = selectedSeries.value.filter((s) => validSeries.has(s))
  }
  // 若已选模型不在新候选池中，清空模型
  if (selectedModels.value.length > 0) {
    const validModels = new Set(rawModelOptions.value.map((m) => m.value))
    selectedModels.value = selectedModels.value.filter((m) => validModels.has(m))
  }

  fetchPaginatedMatrix()
}

// 2. 用户变更【模型系列】-> 触发模型收敛，清洗失效模型
const handleSeriesChange = async (newSeries: string[]) => {
  selectedSeries.value = newSeries
  currentPage.value = 1

  await fetchFilterOptions(selectedProviders.value, newSeries, [])

  if (selectedModels.value.length > 0) {
    const validModels = new Set(rawModelOptions.value.map((m) => m.value))
    selectedModels.value = selectedModels.value.filter((m) => validModels.has(m))
  }

  fetchPaginatedMatrix()
}

// 3. 用户选择【模型名称】-> 严格保留前面已选的厂商与系列，共同组合筛选！
const handleModelChange = (newModels: string[]) => {
  selectedModels.value = newModels
  currentPage.value = 1

  fetchPaginatedMatrix()
}

// 4. 渠道变更
const handleSiteChange = (newSites: string[]) => {
  selectedSites.value = newSites
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const handlePageSizeChange = () => {
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const toggleOnlyFavorites = () => {
  onlyFavorites.value = !onlyFavorites.value
  currentPage.value = 1
  fetchPaginatedMatrix()
}

const isSiteNameFavorite = (siteName: string): boolean => {
  const site = store.relaySites.find((s) => s.name === siteName)
  return site ? store.isSiteFavorite(site.id) : false
}

const toggleFavoriteByName = (siteName: string) => {
  const site = store.relaySites.find((s) => s.name === siteName)
  if (site) {
    store.toggleFavoriteSite(site.id)
  }
}

const changePage = (page: number) => {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  fetchPaginatedMatrix()
}

const visiblePages = computed(() => {
  const pages: number[] = []
  const max = totalPages.value
  const cur = currentPage.value

  let start = Math.max(1, cur - 2)
  let end = Math.min(max, cur + 2)

  if (end - start < 4) {
    if (start === 1) end = Math.min(max, start + 4)
    else if (end === max) start = Math.max(1, end - 4)
  }

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

const resetAllFilters = () => {
  selectedProviders.value = []
  selectedSeries.value = []
  selectedModels.value = []
  selectedSites.value = []
  onlyFavorites.value = false
  currentPage.value = 1
  fetchFilterOptions()
  fetchPaginatedMatrix()
}

const removeProvider = (p: string) => {
  const next = selectedProviders.value.filter((item) => item !== p)
  handleProviderChange(next)
}

const removeSeries = (s: string) => {
  const next = selectedSeries.value.filter((item) => item !== s)
  handleSeriesChange(next)
}

const removeModel = (m: string) => {
  const next = selectedModels.value.filter((item) => item !== m)
  handleModelChange(next)
}

const removeSite = (st: string) => {
  selectedSites.value = selectedSites.value.filter((item) => item !== st)
  handleSiteChange(selectedSites.value)
}

const selectRow = (row: ComparisonItem) => {
  selectedRow.value = row
  updateScatterChart()
}

const formatPrice = (usd: number, cny: number) => {
  if (store.currency === 'USD') {
    return `$${usd.toFixed(3)}`
  }
  return `¥${(cny || usd * (store.usdToCnyRate || 7.25)).toFixed(3)}`
}

// 监听全局货币切换，实时重绘散点图
watch(() => store.currency, () => {
  updateScatterChart()
})

const getTypeBadgeClass = (type: string) => {
  if (type === 'official') return 'bg-[#E8F2FD] text-[#0071E3] border border-[#CCE4FB]'
  if (type === 'cloud') return 'bg-[#F3E8FF] text-[#9333EA] border border-[#E9D5FF]'
  if (type === 'newapi') return 'bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6]'
  return 'bg-[#FFF8E1] text-[#B78103] border border-[#FFE082]'
}

const activeScatterModelId = computed(() => {
  return selectedRow.value?.model_id || (pagedItems.value.length > 0 ? pagedItems.value[0].model_id : 'deepseek-v3')
})

const initScatterChart = () => {
  if (!scatterChartRef.value) return
  chartInstance = echarts.init(scatterChartRef.value)
  updateScatterChart()
}

const updateScatterChart = () => {
  if (!chartInstance) return

  const targetModelId = activeScatterModelId.value
  const targetItems = pagedItems.value.filter((item) => item.model_id === targetModelId)

  const data = targetItems.map((item) => [
    store.currency === 'USD' ? item.calculated_input_usd : item.calculated_input_cny,
    item.last_tested_tps || 50,
    item.site_name,
    item.model_ratio
  ])

  const option: echarts.EChartsOption = {
    backgroundColor: 'transparent',
    grid: {
      left: 50,
      right: 30,
      top: 15,
      bottom: 25
    },
    tooltip: {
      backgroundColor: '#FFFFFF',
      borderColor: '#E5E5EA',
      textStyle: { color: '#1D1D1F', fontSize: 11 },
      formatter: (params: any) => {
        const d = params.data
        return `
          <div class="font-sans font-bold text-[#1D1D1F]">${d[2]}</div>
          <div class="text-[#6E6E73] text-[10px]">输入价格: <strong class="text-[#34C759]">${store.currency === 'USD' ? '$' : '¥'}${d[0]}</strong></div>
          <div class="text-[#6E6E73] text-[10px]">实测速率: <strong class="text-[#0071E3]">${d[1]} TPS</strong></div>
        `
      }
    },
    xAxis: {
      type: 'value',
      name: `价格 (${store.currency})`,
      nameLocation: 'end',
      nameTextStyle: { color: '#86868B', fontSize: 10 },
      splitLine: { lineStyle: { color: '#E5E5EA', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#D1D1D6' } },
      axisLabel: { color: '#6E6E73', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: 'TPS',
      nameTextStyle: { color: '#86868B', fontSize: 10 },
      splitLine: { lineStyle: { color: '#E5E5EA', type: 'dashed' } },
      axisLine: { lineStyle: { color: '#D1D1D6' } },
      axisLabel: { color: '#6E6E73', fontSize: 10 }
    },
    series: [
      {
        type: 'scatter',
        symbolSize: 14,
        data: data,
        itemStyle: {
          color: (params: any) => {
            const ratio = params.data[3] || 1.0
            return ratio < 1.0 ? '#34C759' : '#0071E3'
          },
          shadowBlur: 4,
          shadowColor: 'rgba(0, 113, 227, 0.2)'
        }
      }
    ]
  }

  chartInstance.setOption(option)
}

onMounted(() => {
  fetchFilterOptions()
  fetchPaginatedMatrix()
  initScatterChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

const handleResize = () => {
  chartInstance?.resize()
}
</script>
