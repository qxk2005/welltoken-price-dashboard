<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部操作栏与分类筛选 (苹果高级灰白风格) -->
    <div class="p-3.5 rounded-2xl bg-[#FFFFFF] border border-[#E5E5EA] shadow-[0_1px_3px_rgba(0,0,0,0.02)] flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <!-- 分类切换胶囊按钮组 -->
        <div class="flex items-center space-x-1 bg-[#F2F2F7] p-0.5 rounded-xl border border-[#E5E5EA]">
          <button
            v-for="tab in categoryTabs"
            :key="tab.id"
            @click="setCategory(tab.id)"
            class="px-3 py-1 text-xs rounded-lg font-medium transition-all"
            :class="activeCategory === tab.id ? 'bg-[#0071E3] text-white font-bold shadow-xs' : 'text-[#6E6E73] hover:text-[#1D1D1F]'"
          >
            {{ tab.name }} ({{ getCategoryCount(tab.id) }})
          </button>
        </div>

        <!-- 供应商即时搜索框 -->
        <div class="w-64 relative">
          <input
            v-model="searchKey"
            type="text"
            placeholder="搜索供应商/渠道 (如 Cloudflare, Groq)..."
            class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-lg px-2.5 py-1 text-xs text-[#1D1D1F] placeholder-[#86868B] focus:outline-none transition-all font-sans"
          />
          <span v-if="searchKey" @click="searchKey = ''" class="absolute right-2 top-1 text-[#86868B] hover:text-[#1D1D1F] cursor-pointer text-xs">✕</span>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <button
          @click="store.triggerFullSync"
          class="text-xs px-3.5 py-1.5 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#0071E3] border border-[#E5E5EA] font-medium transition-all flex items-center space-x-1"
        >
          <span>🔄 从 models.dev 重新拉取供应商</span>
        </button>
        <button
          @click="openAddModal"
          class="text-xs px-3.5 py-1.5 rounded-lg bg-[#0071E3] hover:bg-[#0077ED] active:bg-[#0062C4] text-white font-medium shadow-sm transition-all flex items-center space-x-1"
        >
          <span>+ 添加自建 NewAPI/Sub2API 渠道</span>
        </button>
      </div>
    </div>

    <!-- 供应商与渠道列表式表格 (Data Table + 分页，高信息密度与对齐排版) -->
    <div class="flex-1 flex flex-col bg-[#FFFFFF] rounded-2xl border border-[#E5E5EA] p-3 shadow-[0_1px_3px_rgba(0,0,0,0.02)] overflow-hidden min-h-0">
      <!-- 表格滚动区 -->
      <div class="flex-1 overflow-x-auto overflow-y-auto pr-1">
        <table class="w-full text-left text-xs border-collapse min-w-[1020px]">
          <!-- 表头 (支持点击排序) -->
          <thead class="text-[11px] text-[#6E6E73] bg-[#F9F9FB] border-b border-[#E5E5EA] sticky top-0 z-10 font-sans select-none">
            <tr>
              <th @click="toggleSort('name')" class="py-2.5 px-3 cursor-pointer hover:text-[#1D1D1F] transition-colors">
                供应商 / 渠道名称 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('name') }}</span>
              </th>
              <th class="py-2.5 px-3 text-center">渠道性质</th>
              <th @click="toggleSort('model_count')" class="py-2.5 px-3 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors">
                提供模型数 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('model_count') }}</span>
              </th>
              <th class="py-2.5 px-3">API 基础端点 (Base URL)</th>
              <th class="py-2.5 px-3">环境变量标识</th>
              <th @click="toggleSort('recharge_rate')" class="py-2.5 px-3 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors">
                充值倍率 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('recharge_rate') }}</span>
              </th>
              <th @click="toggleSort('score')" class="py-2.5 px-3 text-center cursor-pointer hover:text-[#1D1D1F] transition-colors">
                评分 / 延迟 <span class="text-[10px] text-[#0071E3] font-mono">{{ getSortIndicator('score') }}</span>
              </th>
              <th class="py-2.5 px-3 text-center">状态</th>
              <th class="py-2.5 px-3 text-center">快捷操作</th>
            </tr>
          </thead>

          <!-- 数据行体 -->
          <tbody class="divide-y divide-[#E5E5EA]/60 font-sans">
            <tr
              v-for="site in paginatedSites"
              :key="site.id"
              class="hover:bg-[#F5F5F7] transition-colors group"
            >
              <!-- 1. 供应商名称、Logo 缩写与 ID -->
              <td class="py-2.5 px-3">
                <div class="flex items-center space-x-2.5">
                  <div class="w-8 h-8 rounded-lg bg-[#F2F2F7] border border-[#E5E5EA] flex items-center justify-center text-xs font-bold font-mono text-[#0071E3] group-hover:scale-105 transition-transform flex-shrink-0">
                    {{ site.name.slice(0, 2).toUpperCase() }}
                  </div>
                  <div>
                    <div class="flex items-center space-x-1.5">
                      <span class="font-bold text-xs text-[#1D1D1F] group-hover:text-[#0071E3] transition-colors">{{ site.name }}</span>
                      <span
                        v-if="site.is_official_catalog"
                        class="px-1.5 py-0.2 rounded bg-[#E8F2FD] text-[#0071E3] text-[9px] font-mono border border-[#CCE4FB] font-medium"
                        title="models.dev 官方标准供应商"
                      >
                        MODELS.DEV
                      </span>
                    </div>
                    <div class="text-[11px] text-[#86868B] font-mono mt-0.5">
                      {{ site.provider_id || `site-${site.id}` }}
                    </div>
                  </div>
                </div>
              </td>

              <!-- 2. 渠道性质分类 -->
              <td class="py-2.5 px-3 text-center">
                <span
                  class="px-2 py-0.5 rounded-md text-[10.5px] font-medium border"
                  :class="getCategoryBadgeClass(site)"
                >
                  {{ getCategoryLabel(site) }}
                </span>
              </td>

              <!-- 3. 提供模型总数 -->
              <td class="py-2.5 px-3 text-center">
                <span
                  @click="goToMatrixWithSite(site.id)"
                  class="px-2 py-0.5 rounded-full bg-[#E6F4EA] text-[#137333] border border-[#CEEAD6] font-mono font-bold text-xs cursor-pointer hover:bg-[#CEEAD6] transition-colors"
                  title="点击全网比价查看该渠道所有模型报价"
                >
                  {{ site.model_count || 12 }} 款
                </span>
              </td>

              <!-- 4. API 端点 Base URL -->
              <td class="py-2.5 px-3 font-mono text-[11px] text-[#6E6E73] max-w-[240px] truncate" :title="site.base_url">
                <div class="flex items-center space-x-1">
                  <span class="truncate">{{ site.base_url }}</span>
                  <button
                    @click="copyText(site.base_url)"
                    class="text-[#86868B] hover:text-[#0071E3] text-[10px] px-1 py-0.2 rounded bg-[#F2F2F7] border border-[#E5E5EA]"
                    title="复制端点 URL"
                  >
                    复制
                  </button>
                </div>
              </td>

              <!-- 5. 环境变量标识 -->
              <td class="py-2.5 px-3 font-mono text-[11px] text-[#1D1D1F] max-w-[180px] truncate">
                <span v-if="site.env_vars" class="px-1.5 py-0.5 rounded bg-[#F2F2F7] border border-[#E5E5EA] text-[#0071E3]" :title="site.env_vars">
                  {{ site.env_vars }}
                </span>
                <span v-else class="text-[#86868B]">-</span>
              </td>

              <!-- 6. 充值/折算倍率 -->
              <td class="py-2.5 px-3 text-center font-mono font-bold text-[#1D1D1F]">
                {{ site.recharge_rate ? site.recharge_rate.toFixed(2) : '1.00' }}x
              </td>

              <!-- 7. 评分与延迟 -->
              <td class="py-2.5 px-3 text-center font-mono text-[11px]">
                <div class="flex items-center justify-center space-x-1.5">
                  <span class="text-[#34C759] font-bold">{{ site.score || 95 }}分</span>
                  <span class="text-[#86868B]">/</span>
                  <span class="text-[#0071E3]">{{ site.last_latency_ms ? site.last_latency_ms.toFixed(0) : '35' }}ms</span>
                </div>
              </td>

              <!-- 8. 启用/活跃状态 -->
              <td class="py-2.5 px-3 text-center">
                <label class="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    :checked="site.is_active"
                    @change="toggleSiteActive(site)"
                    class="sr-only peer"
                  />
                  <div class="w-8 h-4 bg-[#E5E5EA] peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3.5 after:transition-all peer-checked:bg-[#34C759]"></div>
                </label>
              </td>

              <!-- 9. 快捷操作 -->
              <td class="py-2.5 px-3 text-center font-mono text-[11px] whitespace-nowrap">
                <button
                  @click="goToMatrixWithSite(site.id)"
                  class="text-[#0071E3] hover:underline mr-2 font-medium"
                >
                  [比价]
                </button>
                <button
                  @click="goToSpeedTestWithSite(site.id)"
                  class="text-[#34C759] hover:underline mr-2 font-bold"
                >
                  [测速]
                </button>
                <a
                  v-if="site.doc_url"
                  :href="site.doc_url"
                  target="_blank"
                  class="text-[#AF52DE] hover:underline mr-2"
                  title="打开官方文档"
                >
                  [文档]
                </a>
                <button
                  v-if="!site.is_official_catalog"
                  @click="openEditModal(site)"
                  class="text-[#FF9500] hover:underline mr-2 font-medium"
                >
                  [编辑]
                </button>
                <button
                  v-if="!site.is_official_catalog"
                  @click="deleteSite(site.id)"
                  class="text-[#FF3B30] hover:underline font-medium"
                >
                  [删除]
                </button>
              </td>
            </tr>

            <tr v-if="paginatedSites.length === 0">
              <td colspan="9" class="py-12 text-center text-xs text-[#86868B]">
                无匹配的供应商与渠道记录
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 底部现代化分页控制栏 (Pagination Bar - 苹果灰白风格) -->
      <div class="pt-3 border-t border-[#E5E5EA] flex items-center justify-between text-xs text-[#6E6E73]">
        <!-- 左侧：总数与每页条数选择器 -->
        <div class="flex items-center space-x-3">
          <span>
            显示第 <strong class="text-[#1D1D1F] font-mono">{{ startIndex + 1 }}</strong> -
            <strong class="text-[#1D1D1F] font-mono">{{ Math.min(startIndex + pageSize, totalItems) }}</strong> 条，
            共 <strong class="text-[#0071E3] font-mono">{{ totalItems }}</strong> 家供应商与渠道
          </span>

          <div class="flex items-center space-x-1.5">
            <span>每页:</span>
            <select
              v-model.number="pageSize"
              @change="currentPage = 1"
              class="bg-[#F2F2F7] border border-[#E5E5EA] rounded-lg px-2 py-0.5 text-xs text-[#1D1D1F] focus:outline-none focus:border-[#0071E3]"
            >
              <option :value="15">15 条/页</option>
              <option :value="20">20 条/页</option>
              <option :value="30">30 条/页</option>
              <option :value="50">50 条/页</option>
              <option :value="100">100 条/页</option>
            </select>
          </div>
        </div>

        <!-- 右侧：换页按钮与页码控制器 -->
        <div class="flex items-center space-x-1.5 font-mono">
          <button
            :disabled="currentPage <= 1"
            @click="currentPage = 1"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
            title="首页"
          >
            «
          </button>
          <button
            :disabled="currentPage <= 1"
            @click="currentPage--"
            class="px-3 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
          >
            ‹ 上一页
          </button>

          <!-- 动态页码 Pills -->
          <div class="flex items-center space-x-1 px-1">
            <button
              v-for="p in visiblePages"
              :key="p"
              @click="currentPage = p"
              class="w-7 h-7 rounded-lg text-xs font-bold transition-all"
              :class="currentPage === p ? 'bg-[#0071E3] text-white shadow-xs' : 'bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] border border-[#E5E5EA]'"
            >
              {{ p }}
            </button>
          </div>

          <button
            :disabled="currentPage >= totalPages"
            @click="currentPage++"
            class="px-3 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
          >
            下一页 ›
          </button>
          <button
            :disabled="currentPage >= totalPages"
            @click="currentPage = totalPages"
            class="px-2.5 py-1 rounded-lg bg-[#F2F2F7] hover:bg-[#E5E5EA] disabled:opacity-30 disabled:hover:bg-[#F2F2F7] text-[#1D1D1F] border border-[#E5E5EA] font-medium transition-all"
            title="末页"
          >
            »
          </button>

          <span class="text-[#86868B] text-[11px] ml-2">共 {{ totalPages }} 页</span>
        </div>
      </div>
    </div>

    <!-- 弹窗：添加 / 编辑渠道 Modal (苹果灰白质感弹窗) -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/30 backdrop-blur-xs flex items-center justify-center z-50 animate-fade-in"
    >
      <div class="bg-[#FFFFFF] border border-[#E5E5EA] rounded-2xl w-[520px] p-6 space-y-4 shadow-[0_20px_50px_rgba(0,0,0,0.15)]">
        <div class="flex items-center justify-between border-b border-[#E5E5EA] pb-3">
          <h3 class="font-bold text-sm text-[#1D1D1F]">
            {{ isEditing ? '✏️ 编辑自建渠道配置' : '➕ 添加自建 NewAPI / OneAPI / Sub2API 渠道' }}
          </h3>
          <button @click="showModal = false" class="text-[#86868B] hover:text-[#1D1D1F] text-sm">✕</button>
        </div>

        <div class="space-y-3 text-xs">
          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">渠道名称 (Name) *</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="例如: 我的自建 NewAPI 聚合站"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none"
            />
          </div>

          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">API 基础地址 (Base URL) *</label>
            <input
              v-model="form.base_url"
              type="text"
              placeholder="https://api.my-newapi.com/v1"
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">系统类型 (Site Type)</label>
              <select
                v-model="form.site_type"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] focus:outline-none"
              >
                <option value="newapi">NewAPI / OneAPI 系统</option>
                <option value="sub2api">Sub2API 系统</option>
                <option value="cloud">云服务商 (Cloud Platform)</option>
                <option value="official">官方直连渠道 (Official)</option>
              </select>
            </div>

            <div>
              <label class="block text-[#6E6E73] font-medium mb-1">充值折算倍率 (Recharge Rate)</label>
              <input
                v-model.number="form.recharge_rate"
                type="number"
                step="0.01"
                placeholder="1.0"
                class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label class="block text-[#6E6E73] font-medium mb-1">中转站 API Key (用于测速与模型探测)</label>
            <input
              v-model="form.api_key"
              type="password"
              placeholder="sk-..."
              class="w-full bg-[#F2F2F7] border border-[#E5E5EA] focus:border-[#0071E3] focus:bg-[#FFFFFF] rounded-xl px-3 py-2 text-[#1D1D1F] font-mono focus:outline-none"
            />
          </div>
        </div>

        <div class="flex items-center justify-end space-x-2 pt-2 border-t border-[#E5E5EA]">
          <button
            @click="showModal = false"
            class="px-4 py-2 rounded-xl bg-[#F2F2F7] hover:bg-[#E5E5EA] text-[#1D1D1F] text-xs font-medium"
          >
            取消
          </button>
          <button
            @click="saveChannel"
            class="px-4 py-2 rounded-xl bg-[#0071E3] hover:bg-[#0077ED] text-white text-xs font-medium shadow-sm"
          >
            {{ isEditing ? '保存修改' : '确认添加' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import type { RelaySite } from '../types'

const store = useDashboardStore()
const searchKey = ref('')
const activeCategory = ref('all')

// 分页状态
const currentPage = ref(1)
const pageSize = ref(20)

// 排序状态
const sortField = ref<string>('score')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 弹窗状态
const showModal = ref(false)
const isEditing = ref(false)
const currentEditId = ref<number | null>(null)
const form = ref({
  name: '',
  base_url: '',
  site_type: 'newapi',
  recharge_rate: 1.0,
  api_key: ''
})

const categoryTabs = [
  { id: 'all', name: '全部供应商' },
  { id: 'official', name: '官方直连' },
  { id: 'cloud', name: '知名云厂商' },
  { id: 'relay', name: '聚合中转站' }
]

const setCategory = (catId: string) => {
  activeCategory.value = catId
  currentPage.value = 1
}

const getCategoryCount = (catId: string) => {
  if (catId === 'all') return store.relaySites.length
  return store.relaySites.filter((s) => {
    if (catId === 'official') return s.is_official_catalog && s.site_type === 'official'
    if (catId === 'cloud') return s.site_type === 'cloud'
    return s.site_type === 'newapi' || s.site_type === 'sub2api' || !s.is_official_catalog
  }).length
}

const getCategoryLabel = (site: RelaySite) => {
  if (site.is_official_catalog && site.site_type === 'official') return '官方直连'
  if (site.site_type === 'cloud') return '云厂商'
  if (site.site_type === 'newapi') return 'NewAPI'
  if (site.site_type === 'sub2api') return 'Sub2API'
  return '聚合中转'
}

const getCategoryBadgeClass = (site: RelaySite) => {
  if (site.is_official_catalog && site.site_type === 'official') {
    return 'bg-[#E8F2FD] text-[#0071E3] border-[#CCE4FB]'
  }
  if (site.site_type === 'cloud') {
    return 'bg-[#F3E8FF] text-[#9333EA] border-[#E9D5FF]'
  }
  return 'bg-[#FFF8E1] text-[#B78103] border-[#FFE082]'
}

// 过滤与排序
const filteredAndSortedSites = computed(() => {
  let list = [...store.relaySites]

  if (activeCategory.value !== 'all') {
    list = list.filter((s) => {
      if (activeCategory.value === 'official') return s.is_official_catalog && s.site_type === 'official'
      if (activeCategory.value === 'cloud') return s.site_type === 'cloud'
      return s.site_type === 'newapi' || s.site_type === 'sub2api' || !s.is_official_catalog
    })
  }

  if (searchKey.value.trim()) {
    const q = searchKey.value.toLowerCase().trim()
    list = list.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        (s.provider_id && s.provider_id.toLowerCase().includes(q)) ||
        s.base_url.toLowerCase().includes(q)
    )
  }

  // 排序
  list.sort((a: any, b: any) => {
    let valA = a[sortField.value]
    let valB = b[sortField.value]

    if (typeof valA === 'string') {
      return sortOrder.value === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA)
    }
    valA = valA || 0
    valB = valB || 0
    return sortOrder.value === 'asc' ? valA - valB : valB - valA
  })

  return list
})

// 分页计算
const totalItems = computed(() => filteredAndSortedSites.value.length)
const totalPages = computed(() => Math.max(1, Math.ceil(totalItems.value / pageSize.value)))
const startIndex = computed(() => (currentPage.value - 1) * pageSize.value)

const paginatedSites = computed(() => {
  return filteredAndSortedSites.value.slice(startIndex.value, startIndex.value + pageSize.value)
})

// 动态可视页码
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

watch(searchKey, () => {
  currentPage.value = 1
})

const toggleSort = (field: string) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'desc'
  }
  currentPage.value = 1
}

const getSortIndicator = (field: string) => {
  if (sortField.value !== field) return '↕'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

const copyText = (txt: string) => {
  navigator.clipboard.writeText(txt)
}

const toggleSiteActive = async (site: RelaySite) => {
  try {
    site.is_active = !site.is_active
    await axios.put(`${store.apiUrl}/api/v1/channels/${site.id}`, {
      is_active: site.is_active
    })
  } catch (e) {
    console.error('Toggle active failed:', e)
  }
}

const goToMatrixWithSite = (siteId: number) => {
  store.selectedSiteId = siteId
  store.activeTab = 'price-matrix'
}

const goToSpeedTestWithSite = (siteId: number) => {
  store.activeTab = 'speed-tester'
  store.runSpeedTest([siteId], 'deepseek-v3')
}

const openAddModal = () => {
  isEditing.value = false
  currentEditId.value = null
  form.value = {
    name: '',
    base_url: '',
    site_type: 'newapi',
    recharge_rate: 1.0,
    api_key: ''
  }
  showModal.value = true
}

const openEditModal = (site: RelaySite) => {
  isEditing.value = true
  currentEditId.value = site.id
  form.value = {
    name: site.name,
    base_url: site.base_url,
    site_type: site.site_type,
    recharge_rate: site.recharge_rate || 1.0,
    api_key: site.api_key || ''
  }
  showModal.value = true
}

const saveChannel = async () => {
  try {
    if (isEditing.value && currentEditId.value) {
      await axios.put(`${store.apiUrl}/api/v1/channels/${currentEditId.value}`, form.value)
    } else {
      await axios.post(`${store.apiUrl}/api/v1/channels`, form.value)
    }
    await store.fetchRelaySites()
    showModal.value = false
  } catch (e) {
    console.error('Save channel failed:', e)
  }
}

const deleteSite = async (siteId: number) => {
  if (!confirm('确定要删除该渠道吗？')) return
  try {
    await axios.delete(`${store.apiUrl}/api/v1/channels/${siteId}`)
    await store.fetchRelaySites()
  } catch (e) {
    console.error('Delete site failed:', e)
  }
}
</script>
