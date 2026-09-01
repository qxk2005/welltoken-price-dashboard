<template>
  <Teleport to="body">
    <div v-if="visible" class="fixed inset-0 z-50 overflow-hidden select-none font-sans">
      <!-- 半透明磨砂遮罩背景 (点击关闭) -->
      <div
        @click="close"
        class="fixed inset-0 bg-black/30 backdrop-blur-xs transition-opacity animate-fade-in"
      ></div>

      <!-- 右侧滑出主体面板 -->
      <div class="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div class="w-screen max-w-2xl bg-[#F5F5F7] shadow-2xl flex flex-col overflow-hidden animate-slide-left border-l border-[#E5E5EA]">
          <!-- 1. 顶部 Header 导航与基本信息 -->
          <div class="p-4 bg-[#FFFFFF] border-b border-[#E5E5EA] space-y-3 flex-shrink-0 shadow-xs">
            <!-- 顶部返回与代码标识 -->
            <div class="flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="px-2.5 py-1 rounded-lg bg-[#E8F2FD] text-[#0071E3] text-xs font-bold font-mono flex items-center space-x-1.5">
                  <SystemIcon name="channels" custom-class="w-3.5 h-3.5 text-[#0071E3]" />
                  <span>渠道商详情与可用模型</span>
                </span>
              </div>

              <div class="flex items-center space-x-2">
                <span class="text-[11px] text-[#86868B]">渠道标识:</span>
                <code class="px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA] text-[#0071E3] font-mono text-xs font-bold">
                  {{ currentSite?.provider_id || (currentSite ? `site-${currentSite.id}` : '-') }}
                </code>
                <button
                  @click="copyText(currentSite?.provider_id || `site-${currentSite?.id}`)"
                  class="text-xs text-[#6E6E73] hover:text-[#1D1D1F] px-2 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA] cursor-pointer"
                >
                  {{ isCopied ? '✓ 已复制' : '复制' }}
                </button>
                <button
                  @click="close"
                  class="w-7 h-7 rounded-full bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F] flex items-center justify-center text-sm font-bold transition-all ml-2 cursor-pointer"
                  title="关闭 (Esc)"
                >
                  ✕
                </button>
              </div>
            </div>

            <!-- 供应商大标题、Logo 与操作 -->
            <div v-if="currentSite" class="flex items-start justify-between">
              <div class="flex items-start space-x-3.5">
                <div class="w-12 h-12 rounded-2xl bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center p-2 flex-shrink-0">
                  <ProviderLogo :provider-id="currentSite.provider_id || currentSite.name" custom-class="w-7 h-7" />
                </div>
                <div class="space-y-1">
                  <div class="flex items-center space-x-2">
                    <h2 class="text-lg font-bold text-[#1D1D1F] tracking-tight">{{ currentSite.name }}</h2>
                    <span
                      class="px-2 py-0.5 rounded-md text-[10px] font-medium border"
                      :class="getCategoryBadgeClass(currentSite)"
                    >
                      {{ getCategoryLabel(currentSite) }}
                    </span>
                    <button
                      @click="store.toggleFavoriteSite(currentSite.id)"
                      class="text-xs hover:scale-125 transition-transform cursor-pointer ml-1"
                    >
                      <span v-if="store.isSiteFavorite(currentSite.id)" class="text-[#FF9500]">⭐ 已收藏</span>
                      <span v-else class="text-[#AEAEB2] hover:text-[#FF9500]">☆ 收藏该渠道</span>
                    </button>
                  </div>
                  <div class="text-[11px] text-[#6E6E73] font-mono">
                    API Base URL: <span class="text-[#0071E3]">{{ currentSite.base_url || 'https://api.openai.com/v1' }}</span>
                  </div>
                </div>
              </div>

              <!-- 右侧快捷按钮 -->
              <div class="flex items-center space-x-1.5 flex-shrink-0">
                <a
                  v-if="currentSite.doc_url"
                  :href="currentSite.doc_url"
                  target="_blank"
                  class="px-2.5 py-1.5 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] text-xs font-medium flex items-center space-x-1"
                >
                  <span>📖 官方文档 ↗</span>
                </a>
                <button
                  @click="goToSpeedTestWithSite(currentSite.id)"
                  class="px-3 py-1.5 rounded-xl bg-[#34C759] hover:bg-[#2FB34F] text-white text-xs font-bold shadow-xs flex items-center space-x-1 cursor-pointer"
                >
                  <span>⚡ 一键测速</span>
                </button>
              </div>
            </div>

            <!-- 2. 四维 Fact Grid 看板 -->
            <div v-if="currentSite" class="grid grid-cols-4 gap-2 pt-2 border-t border-[#E5E5EA]">
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">可用模型数</div>
                <div class="text-base font-bold font-mono text-[#0071E3] mt-0.5">
                  {{ isDetailLoading ? '...' : `${providerModelsList.length} 款` }}
                </div>
              </div>
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">驱动驱动包</div>
                <div class="text-[11px] font-bold font-mono text-[#1D1D1F] mt-1 truncate">
                  @ai-sdk/openai
                </div>
              </div>
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">环境变量 Key</div>
                <div class="text-[11px] font-bold font-mono text-[#AF52DE] mt-1 truncate">
                  {{ currentSite.env_vars || `${currentSite.name.toUpperCase().replace(/[^A-Z]/g, '')}_API_KEY` }}
                </div>
              </div>
              <div class="p-2 rounded-xl bg-[#F9F9FB] border border-[#E5E5EA]">
                <div class="text-[10px] text-[#86868B] font-medium uppercase">综合评分 / 延迟</div>
                <div class="mt-1">
                  <span class="text-xs font-bold font-mono text-[#34C759]">
                    {{ currentSite.score || 95 }}分 / {{ currentSite.last_latency_ms ? currentSite.last_latency_ms.toFixed(0) : '35' }}ms
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- 3. 该渠道旗下所有可用模型与价格表格 -->
          <div class="flex-1 flex flex-col p-3 overflow-hidden min-h-0 bg-[#FFFFFF] m-3 rounded-2xl border border-[#E5E5EA] shadow-xs">
            <!-- 头部控制栏：支持筛选范围切换 (当前比价筛选 vs 查看全部) -->
            <div class="flex items-center justify-between pb-2 border-b border-[#E5E5EA] flex-shrink-0 flex-wrap gap-2">
              <div class="flex items-center space-x-2">
                <span class="text-xs font-bold text-[#1D1D1F]">
                  📋 模型清单
                </span>

                <!-- 模式切换 Segmented Control (有父级筛选时展示) -->
                <div v-if="hasActiveParentFilters" class="inline-flex p-0.5 rounded-lg bg-[#E5E5EA]/70 border border-[#D1D1D6]/60 text-xs">
                  <button
                    @click="viewScope = 'filtered'"
                    class="px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center space-x-1"
                    :class="viewScope === 'filtered' ? 'bg-[#FFFFFF] text-[#0071E3] font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>✨ 筛选项结果</span>
                    <span
                      class="px-1.5 py-0.2 rounded-full text-[10px] font-mono"
                      :class="viewScope === 'filtered' ? 'bg-[#E8F2FD] text-[#0071E3]' : 'bg-[#E5E5EA] text-[#86868B]'"
                    >
                      {{ matchingFilterModels.length }}
                    </span>
                  </button>
                  <button
                    @click="viewScope = 'all'"
                    class="px-2.5 py-1 rounded-md text-[11px] font-medium transition-all cursor-pointer flex items-center space-x-1"
                    :class="viewScope === 'all' ? 'bg-[#FFFFFF] text-[#1D1D1F] font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
                  >
                    <span>🌐 查看全部</span>
                    <span
                      class="px-1.5 py-0.2 rounded-full text-[10px] font-mono"
                      :class="viewScope === 'all' ? 'bg-[#F2F2F7] text-[#1D1D1F]' : 'bg-[#E5E5EA] text-[#86868B]'"
                    >
                      {{ providerModelsList.length }}
                    </span>
                  </button>
                </div>
              </div>

              <!-- 0 元过滤切换按钮 -->
              <button
                @click="excludeZeroPrice = !excludeZeroPrice"
                class="px-2 py-1 rounded-lg border text-[11px] font-medium transition-all flex items-center space-x-1 cursor-pointer select-none"
                :class="excludeZeroPrice ? 'bg-[#EBF5FF] border-[#B9E1FF] text-[#0071E3] font-bold shadow-2xs' : 'bg-[#FFFFFF] hover:bg-[#F2F2F7] border-[#E5E5EA] text-[#6E6E73] hover:text-[#1D1D1F]'"
                title="点击切换：隐藏或显示输入与输出均为 0 的免费/未标价模型"
              >
                <span>{{ excludeZeroPrice ? '🚫 已隐藏 0 元' : '👁️ 显示全部 (含 0 元)' }}</span>
              </button>

              <!-- 搜索框 -->
              <div class="w-36 relative">
                <input
                  v-model="searchQuery"
                  type="text"
                  placeholder="搜索模型名称/标识..."
                  class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
                />
                <span v-if="searchQuery" @click="searchQuery = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
              </div>

              <!-- 自定义列按钮 -->
              <button
                @click="showColumnConfigModal = true"
                class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA] transition-all text-xs flex items-center space-x-1 cursor-pointer font-medium flex-shrink-0"
                title="自定义表格显示列"
              >
                <span>🎛️</span>
                <span>自定义列</span>
              </button>

              <!-- 导出 Excel 按钮 -->
              <button
                @click="handleExportChannelModels"
                :disabled="displayedModels.length === 0"
                class="px-2 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#CCE4FB] transition-all text-xs flex items-center space-x-1 cursor-pointer font-medium disabled:opacity-40 flex-shrink-0"
                title="导出当前抽屉中筛选的模型规格与定价"
              >
                <span>📊</span>
                <span>导出</span>
              </button>
            </div>

            <!-- 当前筛选上下文指示条 (当处于 filtered 模式时) -->
            <div v-if="hasActiveParentFilters && viewScope === 'filtered'" class="flex items-center justify-between px-2.5 py-1.5 rounded-xl bg-[#E8F2FD]/70 border border-[#CCE4FB] text-[11px] text-[#0071E3] mt-2 mb-1 flex-shrink-0">
              <div class="flex items-center space-x-1.5 truncate">
                <span class="font-bold flex items-center space-x-1">
                  <span>🎯</span>
                  <span>已继承比价筛选:</span>
                </span>
                <span class="font-mono truncate">{{ activeFilterSummaryText }}</span>
              </div>
              <button @click="viewScope = 'all'" class="text-[11px] text-[#0071E3] hover:underline font-medium whitespace-nowrap ml-2 cursor-pointer flex-shrink-0">
                切换至全部 ({{ providerModelsList.length }}款) ➔
              </button>
            </div>

            <!-- 数据表格 -->
            <div class="flex-1 overflow-x-auto overflow-y-auto pr-1 mt-1">
              <div v-if="isDetailLoading" class="py-16 text-center text-xs text-[#0071E3] flex items-center justify-center space-x-2">
                <span class="animate-spin">🌀</span>
                <span>正在加载该渠道最新模型清单与定价...</span>
              </div>

              <table v-else class="w-full text-left text-xs border-collapse min-w-[560px]">
                <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans">
                  <tr>
                    <th class="py-2 px-2.5">模型名称 / 标准标识</th>

                    <!-- 动态表头 -->
                    <template v-for="col in visibleDrawerColumns" :key="col.key">
                      <th v-if="col.key === 'input_price'" class="py-2 px-2 text-right w-16">输入 ({{ store.currency }})</th>
                      <th v-else-if="col.key === 'output_price'" class="py-2 px-2 text-right w-16">输出 ({{ store.currency }})</th>
                      <th v-else-if="col.key === 'cache_price'" class="py-2 px-2 text-right w-16 text-[#8E24AA] font-semibold">命中缓存</th>
                      <th v-else-if="col.key === 'tps'" class="py-2 px-2 text-center w-14">实测TPS</th>
                    </template>

                    <th class="py-2 px-2 text-center w-20">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
                  <tr
                    v-for="item in displayedModels"
                    :key="`${item.model_id}-${item.group_name || 'default'}`"
                    class="hover:bg-[#F5F5F7] transition-colors group"
                  >
                    <!-- 模型名称 + 标准 ID -->
                    <td class="py-2 px-2.5">
                      <div class="font-bold text-[#1D1D1F] group-hover:text-[#0071E3] text-xs">
                        {{ item.name }}
                      </div>
                      <div class="text-[10px] text-[#0071E3] font-mono flex items-center space-x-1">
                        <span>{{ item.model_id }}</span>
                        <span v-if="item.site_model_name && item.site_model_name !== item.model_id" class="text-[#86868B] truncate max-w-[200px]" :title="item.site_model_name">({{ item.site_model_name }})</span>
                      </div>
                    </td>

                    <!-- 动态单元格 -->
                    <template v-for="col in visibleDrawerColumns" :key="col.key">
                      <!-- 输入价格 -->
                      <td v-if="col.key === 'input_price'" class="py-2 px-2 text-right font-mono font-medium text-[#34C759]">
                        {{ formatItemPrice(item.calculated_input_usd, item.calculated_input_cny) }}
                      </td>

                      <!-- 输出价格 -->
                      <td v-else-if="col.key === 'output_price'" class="py-2 px-2 text-right font-mono font-medium text-[#1D1D1F]">
                        {{ formatItemPrice(item.calculated_output_usd, item.calculated_output_cny) }}
                      </td>

                      <!-- 命中缓存价格 -->
                      <td v-else-if="col.key === 'cache_price'" class="py-2 px-2 text-right font-mono font-medium">
                        <span v-if="item.calculated_cache_usd && item.calculated_cache_usd > 0" class="text-[#8E24AA] font-bold">
                          {{ formatItemPrice(item.calculated_cache_usd, item.calculated_cache_cny) }}
                        </span>
                        <span v-else class="text-[#AEAEB2] font-normal">-</span>
                      </td>

                      <!-- TPS -->
                      <td v-else-if="col.key === 'tps'" class="py-2 px-2 text-center font-mono text-[#0071E3] font-bold text-[11px]">
                        {{ item.last_tested_tps || 55 }}
                      </td>
                    </template>

                    <!-- 快捷比价/测速/快照 -->
                    <td class="py-2 px-2 text-center whitespace-nowrap">
                      <button
                        @click="openSnapshotModal(item)"
                        class="px-1.5 py-0.5 rounded bg-[#F3E8FD] hover:bg-[#EBD6FA] text-[#8E24AA] border border-[#E1BEE7] text-[10px] font-medium transition-all cursor-pointer mr-1 inline-flex items-center space-x-0.5"
                        title="打开官方定价快照并定位核验"
                      >
                        <span>📸</span>
                      </button>
                      <button
                        @click="triggerModelCompare(item.model_id)"
                        class="px-2 py-0.5 rounded bg-[#E8F2FD] hover:bg-[#0071E3] text-[#0071E3] hover:text-white border border-[#CCE4FB] text-[10px] font-medium transition-all cursor-pointer mr-1 inline-flex items-center space-x-0.5"
                        title="在全网比价中只查看接入该模型的所有渠道"
                      >
                        <SystemIcon name="chart" custom-class="w-2.5 h-2.5" />
                        <span>比价</span>
                      </button>
                    </td>
                  </tr>

                  <tr v-if="displayedModels.length === 0">
                    <td :colspan="visibleDrawerColumns.length + 2" class="py-12 text-center text-xs text-[#86868B]">
                      <div v-if="viewScope === 'filtered' && filterContext?.availableModelIds?.length">
                        该渠道暂未接入当前全局筛选范围内的 {{ filterContext.availableModelIds.length }} 款模型
                        <div class="mt-2">
                          <button
                            @click="viewScope = 'all'"
                            class="text-xs text-[#0071E3] hover:underline font-bold cursor-pointer"
                          >
                            切换为「查看全部模型 ({{ providerModelsList.length }})」
                          </button>
                        </div>
                      </div>
                      <div v-else>
                        暂无匹配的模型记录
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 定价网页快照核对 Modal -->
    <SnapshotViewerModal
      v-if="showSnapshotModal && currentSite"
      :site-id="currentSite.id"
      :site-name="currentSite.name"
      :target-model="snapshotTargetModel"
      @close="showSnapshotModal = false"
    />

    <!-- 自定义表格显示列与排序配置 Modal -->
    <TableColumnConfigModal
      :show="showColumnConfigModal"
      :storage-key="CHANNEL_DRAWER_STORAGE_KEY"
      :default-columns="DEFAULT_DRAWER_COLUMNS"
      fixed-start-label="模型名称 / 标准标识"
      fixed-end-label="操作"
      @close="showColumnConfigModal = false"
      @update:columns="onUpdateDrawerColumns"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import ProviderLogo from './ProviderLogo.vue'
import SystemIcon from './SystemIcon.vue'
import SnapshotViewerModal from './SnapshotViewerModal.vue'
import TableColumnConfigModal, { type TableColumnDef } from './TableColumnConfigModal.vue'
import type { RelaySite } from '../types'
import { exportChannelModelsToExcel } from '../utils/excelExport'

export interface FilterContext {
  providers?: string[]
  series?: string[]
  models?: string[]
  availableModelIds?: string[]
}

const props = defineProps<{
  visible: boolean
  siteName: string | null
  filterContext?: FilterContext
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'compare-model', modelId: string): void
}>()

const store = useDashboardStore()
const isCopied = ref(false)
const isDetailLoading = ref(false)
const searchQuery = ref('')
const excludeZeroPrice = ref(true)
const providerModelsList = ref<any[]>([])
const viewScope = ref<'filtered' | 'all'>('filtered')

// 自定义列配置
const showColumnConfigModal = ref(false)
const CHANNEL_DRAWER_STORAGE_KEY = 'welltoken_col_config_channel_drawer'
const DEFAULT_DRAWER_COLUMNS: TableColumnDef[] = [
  { key: 'input_price', label: '输入单价', visible: true },
  { key: 'output_price', label: '输出单价', visible: true },
  { key: 'cache_price', label: '命中缓存单价', visible: true },
  { key: 'tps', label: '实测 TPS', visible: true },
]

const loadDrawerColumns = (): TableColumnDef[] => {
  try {
    const saved = localStorage.getItem(CHANNEL_DRAWER_STORAGE_KEY)
    if (saved) {
      const parsed: TableColumnDef[] = JSON.parse(saved)
      const merged: TableColumnDef[] = []
      for (const p of parsed) {
        const d = DEFAULT_DRAWER_COLUMNS.find(col => col.key === p.key)
        if (d) {
          merged.push({ key: p.key, label: d.label, visible: p.visible !== false })
        }
      }
      for (const d of DEFAULT_DRAWER_COLUMNS) {
        if (!merged.some(m => m.key === d.key)) {
          merged.push({ ...d })
        }
      }
      return merged
    }
  } catch (e) {
    console.warn('加载抽屉列配置失败:', e)
  }
  return DEFAULT_DRAWER_COLUMNS.map(c => ({ ...c }))
}

const drawerColumns = ref<TableColumnDef[]>(loadDrawerColumns())
const visibleDrawerColumns = computed(() => drawerColumns.value.filter(c => c.visible))
const onUpdateDrawerColumns = (newCols: TableColumnDef[]) => {
  drawerColumns.value = newCols
}

// 快照 Modal 状态
const showSnapshotModal = ref(false)
const snapshotTargetModel = ref<any>(null)

const openSnapshotModal = (modelItem?: any) => {
  if (!currentSite.value) return
  snapshotTargetModel.value = modelItem || null
  showSnapshotModal.value = true
}

const handleExportChannelModels = () => {
  if (!currentSite.value) return
  exportChannelModelsToExcel(
    currentSite.value.name,
    displayedModels.value,
    store.currency as any,
    store.usdToCnyRate || 7.25
  )
}

const currentSite = computed<RelaySite | null>(() => {
  if (!props.siteName) return null
  const target = props.siteName.toLowerCase().trim()
  return store.relaySites.find(
    (s) => s.name.toLowerCase() === target || (s.provider_id && s.provider_id.toLowerCase() === target)
  ) || null
})

const getCategoryLabel = (site: RelaySite) => {
  if (site.is_official_catalog) return '官方直连'
  if (site.provider_type === 'newapi') return '中转渠道'
  return '中转渠道'
}

const getCategoryBadgeClass = (site: RelaySite) => {
  if (site.is_official_catalog) return 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB]'
  return 'bg-[#F3E8FF] text-[#9333EA] border-[#E9D5FF]'
}

const formatItemPrice = (usd?: number, cny?: number) => {
  if (usd === undefined || usd === null) return '$0.000'
  if (store.currency === 'USD') {
    return `$${Number(usd).toFixed(3)}`
  }
  return `¥${(cny || usd * (store.usdToCnyRate || 7.25)).toFixed(3)}`
}

const fetchSiteModels = async (siteId: number) => {
  isDetailLoading.value = true
  try {
    const res = await axios.get(`${store.apiUrl}/api/v1/channels/${siteId}/models`)
    providerModelsList.value = res.data
  } catch (e) {
    console.error('Fetch site models failed:', e)
    providerModelsList.value = []
  } finally {
    isDetailLoading.value = false
  }
}

const hasActiveParentFilters = computed(() => {
  if (!props.filterContext) return false
  return (
    (props.filterContext.providers && props.filterContext.providers.length > 0) ||
    (props.filterContext.series && props.filterContext.series.length > 0) ||
    (props.filterContext.models && props.filterContext.models.length > 0) ||
    (props.filterContext.availableModelIds && props.filterContext.availableModelIds.length > 0)
  )
})

const activeFilterSummaryText = computed(() => {
  if (!props.filterContext) return ''
  const parts: string[] = []
  if (props.filterContext.providers && props.filterContext.providers.length > 0) {
    parts.push(`厂商: ${props.filterContext.providers.join(', ')}`)
  }
  if (props.filterContext.series && props.filterContext.series.length > 0) {
    parts.push(`系列: ${props.filterContext.series.join(', ')}`)
  }
  if (props.filterContext.models && props.filterContext.models.length > 0) {
    parts.push(`模型: ${props.filterContext.models.length > 2 ? `${props.filterContext.models.length}款` : props.filterContext.models.join(', ')}`)
  }
  return parts.join(' | ') || '全网比价筛选条件'
})

// 计算符合父级筛选条件的当前渠道模型子集
const matchingFilterModels = computed(() => {
  if (!hasActiveParentFilters.value) return providerModelsList.value
  const targetModelIds = new Set(
    (props.filterContext?.availableModelIds || []).map((m) => m.toLowerCase().trim())
  )
  const explicitModels = new Set(
    (props.filterContext?.models || []).map((m) => m.toLowerCase().trim())
  )
  const explicitSeries = (props.filterContext?.series || []).map((s) => s.toLowerCase().trim())

  return providerModelsList.value.filter((item) => {
    const mId = (item.model_id || '').toLowerCase().trim()
    const mName = (item.name || '').toLowerCase().trim()

    // 1. 如果有精确指定的模型
    if (explicitModels.size > 0) {
      if (explicitModels.has(mId) || explicitModels.has(mName)) return true
    }

    // 2. 如果指定了系列 (如 "Qwen-3.8" -> "qwen-3.8", "qwen3.8")
    if (explicitSeries.length > 0) {
      if (
        explicitSeries.some((s) => {
          const sNorm = s.replace(/[^a-z0-9]/g, '')
          const mNorm = mId.replace(/[^a-z0-9]/g, '')
          return mId.includes(s) || mName.includes(s) || (sNorm && mNorm.includes(sNorm))
        })
      ) {
        return true
      }
    }

    // 3. 如果背景比价列表有收敛的模型 ID
    if (targetModelIds.size > 0) {
      if (targetModelIds.has(mId) || targetModelIds.has(mName)) return true
      for (const t of targetModelIds) {
        const tNorm = t.replace(/[^a-z0-9]/g, '')
        const mNorm = mId.replace(/[^a-z0-9]/g, '')
        if (mId.includes(t) || t.includes(mId) || (tNorm && mNorm.includes(tNorm))) return true
      }
    }

    return false
  })
})

const baseListByScope = computed(() => {
  if (viewScope.value === 'filtered' && hasActiveParentFilters.value) {
    return matchingFilterModels.value
  }
  return providerModelsList.value
})

const displayedModels = computed(() => {
  let list = baseListByScope.value
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.toLowerCase().trim()
    list = list.filter(
      (m) =>
        (m.name && m.name.toLowerCase().includes(q)) ||
        (m.model_id && m.model_id.toLowerCase().includes(q)) ||
        (m.group_name && m.group_name.toLowerCase().includes(q)) ||
        (m.site_model_name && m.site_model_name.toLowerCase().includes(q))
    )
  }
  if (excludeZeroPrice.value) {
    list = list.filter((m: any) => {
      const inUsd = Number(m.calculated_input_usd || 0)
      const outUsd = Number(m.calculated_output_usd || 0)
      const inCny = Number(m.calculated_input_cny || 0)
      const outCny = Number(m.calculated_output_cny || 0)
      return inUsd >= 0.0001 || outUsd >= 0.0001 || inCny >= 0.0001 || outCny >= 0.0001
    })
  }
  return list
})

const copyText = (txt?: string) => {
  if (!txt) return
  navigator.clipboard.writeText(txt)
  isCopied.value = true
  setTimeout(() => (isCopied.value = false), 2000)
}

const close = () => {
  emit('close')
}

const triggerModelCompare = (modelId: string) => {
  emit('compare-model', modelId)
  close()
}

const goToSpeedTestWithSite = (siteId: number) => {
  store.navigateToSpeedTest(siteId)
  close()
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.visible) {
    close()
  }
}

watch(
  () => [props.visible, props.siteName],
  ([visible, siteName]) => {
    if (visible && siteName && currentSite.value) {
      searchQuery.value = ''
      viewScope.value = hasActiveParentFilters.value ? 'filtered' : 'all'
      fetchSiteModels(currentSite.value.id)
    }
  },
  { immediate: true }
)

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
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
