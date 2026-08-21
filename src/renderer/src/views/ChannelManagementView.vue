<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部操作栏与分类筛选 (参考 models.dev/providers/ 设计) -->
    <div class="p-3 rounded-xl bg-[#151922] border border-[#232936] flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <!-- 分类切换按钮组 -->
        <div class="flex items-center space-x-1 bg-[#0B0E14] p-0.5 rounded-lg border border-[#232936]">
          <button
            v-for="tab in categoryTabs"
            :key="tab.id"
            @click="activeCategory = tab.id"
            class="px-3 py-1 text-xs rounded font-medium transition-all"
            :class="activeCategory === tab.id ? 'bg-blue-600 text-white font-bold' : 'text-gray-400 hover:text-gray-200'"
          >
            {{ tab.name }} ({{ getCategoryCount(tab.id) }})
          </button>
        </div>

        <!-- 供应商即时搜索框 -->
        <div class="w-64 relative">
          <input
            v-model="searchKey"
            type="text"
            placeholder="搜索供应商 (如 Cloudflare, Groq)..."
            class="w-full bg-[#0B0E14] border border-[#2D3748] rounded-lg px-2.5 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-sans"
          />
          <span v-if="searchKey" @click="searchKey = ''" class="absolute right-2 top-1 text-gray-500 hover:text-white cursor-pointer text-xs">✕</span>
        </div>
      </div>

      <div class="flex items-center space-x-2">
        <button
          @click="store.triggerFullSync"
          class="text-xs px-3 py-1.5 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-blue-400 border border-[#374151] transition-all flex items-center space-x-1"
        >
          <span>🔄 从 models.dev 重新拉取供应商与渠道</span>
        </button>
        <button
          @click="openAddModal"
          class="text-xs px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-md shadow-blue-600/20 transition-all flex items-center space-x-1"
        >
          <span>+ 添加自建 NewAPI/Sub2API 渠道</span>
        </button>
      </div>
    </div>

    <!-- 供应商卡片网格 (3 列 Grid 布局，参考 models.dev/providers/) -->
    <div class="flex-1 overflow-y-auto pr-1">
      <div class="grid grid-cols-3 gap-3">
        <div
          v-for="site in filteredSites"
          :key="site.id"
          class="p-3.5 rounded-xl bg-[#151922] border border-[#232936] hover:border-[#353E52] transition-all flex flex-col justify-between space-y-2.5 group"
        >
          <!-- 卡片头部：图标、名称、官方/云端标识、模型数 Badge -->
          <div class="flex items-start justify-between">
            <div class="flex items-center space-x-2.5 truncate">
              <!-- 供应商 Logo 占位 -->
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-[#1E293B] to-[#0F172A] border border-[#334155] flex items-center justify-center text-xs font-bold font-mono text-blue-400">
                {{ site.name.slice(0, 2).toUpperCase() }}
              </div>
              <div class="truncate">
                <div class="flex items-center space-x-1.5">
                  <span class="font-bold text-sm text-white truncate group-hover:text-blue-400 transition-colors">{{ site.name }}</span>
                  <span
                    v-if="site.is_official_catalog"
                    class="px-1 py-0.2 rounded bg-blue-500/10 text-blue-400 text-[9px] font-mono border border-blue-500/20 font-medium"
                    title="models.dev 官方收录供应商"
                  >
                    MODELS.DEV
                  </span>
                </div>
                <div class="text-[10px] text-gray-500 font-mono truncate mt-0.5" :title="site.base_url">
                  {{ site.base_url }}
                </div>
              </div>
            </div>

            <!-- 模型数 Badge -->
            <span class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 text-[10px] font-mono font-bold whitespace-nowrap">
              {{ site.model_count || 10 }} Models
            </span>
          </div>

          <!-- 供应商元信息：环境变量与 API 文档 -->
          <div class="p-2 rounded-lg bg-[#0B0E14]/70 border border-[#232936]/50 text-[11px] space-y-1 font-mono">
            <div v-if="site.env_vars" class="flex items-center justify-between text-gray-400 truncate">
              <span class="text-gray-500 text-[10px]">环境变量:</span>
              <span class="text-sky-300 text-[10px] truncate max-w-[150px]" :title="site.env_vars">{{ site.env_vars }}</span>
            </div>
            <div class="flex items-center justify-between text-gray-400">
              <span class="text-gray-500 text-[10px]">充值汇率比:</span>
              <span class="text-gray-200 text-[10px] font-bold">{{ site.recharge_rate }} : 1</span>
            </div>
          </div>

          <!-- 底部操作与外链 -->
          <div class="pt-2 border-t border-[#232936]/60 flex items-center justify-between text-xs">
            <!-- 官方文档外链 -->
            <div class="flex items-center space-x-2">
              <a
                v-if="site.doc_url"
                :href="site.doc_url"
                target="_blank"
                class="text-blue-400 hover:text-blue-300 text-[11px] flex items-center space-x-0.5"
                title="查看官方开发文档"
              >
                <span>官方文档</span>
                <span class="text-[10px]">↗</span>
              </a>
              <span v-else class="text-[10px] text-gray-500">自建渠道</span>
            </div>

            <!-- 测速与探测动作 -->
            <div class="flex items-center space-x-2">
              <button
                @click="openKeyModal(site)"
                class="text-sky-400 hover:text-sky-300 transition-colors text-[11px]"
              >
                {{ site.api_key ? '[已设Key]' : '[配置Key]' }}
              </button>
              <button
                @click="testSpeed(site.id)"
                class="text-emerald-400 hover:text-emerald-300 transition-colors text-[11px]"
              >
                [实测]
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredSites.length === 0" class="py-16 text-center text-xs text-gray-500">
        无匹配的供应商或渠道
      </div>
    </div>

    <!-- 配置 API Key 模态框 -->
    <div
      v-if="keyModalSite"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="w-[460px] rounded-xl bg-[#151922] border border-[#2D3748] p-5 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-[#232936] pb-3">
          <span class="font-bold text-sm text-white">配置 {{ keyModalSite.name }} API 凭证</span>
          <button @click="keyModalSite = null" class="text-gray-400 hover:text-white text-sm">✕</button>
        </div>
        <div class="space-y-2 text-xs">
          <div class="text-gray-400 leading-relaxed">
            填入您的真实 API Key 即可针对该供应商发起高精度流式测速与连通性验证：
          </div>
          <div v-if="keyModalSite.env_vars" class="text-[11px] text-sky-400 font-mono">
            提示: 对应环境变量 <strong>{{ keyModalSite.env_vars }}</strong>
          </div>
          <input
            v-model="tempApiKey"
            type="password"
            placeholder="sk-xxxxxxxxxxxxxxxx"
            class="w-full bg-[#0B0E14] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-blue-500 text-xs"
          />
        </div>
        <div class="pt-3 border-t border-[#232936] flex items-center justify-end space-x-2">
          <button
            @click="keyModalSite = null"
            class="px-4 py-1.5 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-300 text-xs"
          >
            取消
          </button>
          <button
            @click="saveApiKey"
            class="px-4 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md shadow-blue-600/20"
          >
            保存并测试连通
          </button>
        </div>
      </div>
    </div>

    <!-- 新增自建中转渠道模态弹窗 -->
    <div
      v-if="showAddModal"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="w-[520px] rounded-xl bg-[#151922] border border-[#2D3748] p-5 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-[#232936] pb-3">
          <span class="font-bold text-sm text-white">新增自建中转渠道 (NewAPI / Sub2API)</span>
          <button @click="showAddModal = false" class="text-gray-400 hover:text-white text-sm">✕</button>
        </div>

        <div class="space-y-3 text-xs">
          <div>
            <label class="block text-gray-400 mb-1">中转站点名称</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="如：极速云 AI、星河聚合"
              class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label class="block text-gray-400 mb-1">Base URL (接口地址)</label>
            <input
              v-model="form.base_url"
              type="text"
              placeholder="如：https://api.yourrelay.com/v1"
              class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label class="block text-gray-400 mb-1">API Key / 访问令牌 (可选)</label>
            <input
              v-model="form.api_key"
              type="password"
              placeholder="sk-xxxxxxxxxxxxxxxx"
              class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-blue-500"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-gray-400 mb-1">充值汇率比 (1元兑多少刀额度)</label>
              <input
                v-model.number="form.recharge_rate"
                type="number"
                step="0.1"
                class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-gray-400 mb-1">架构类型</label>
              <select
                v-model="form.site_type"
                class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
              >
                <option value="newapi">NewAPI (支持倍率表)</option>
                <option value="sub2api">Sub2API (包月/混合)</option>
                <option value="oneapi">OneAPI</option>
                <option value="official">官方直连 API</option>
              </select>
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-[#232936] flex items-center justify-end space-x-2">
          <button
            @click="showAddModal = false"
            class="px-4 py-2 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-300 text-xs"
          >
            取消
          </button>
          <button
            @click="submitChannel"
            class="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md shadow-blue-600/20"
          >
            保存并测试连通
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'
import type { RelaySite } from '../types'

const store = useDashboardStore()
const activeCategory = ref('all')
const searchKey = ref('')
const showAddModal = ref(false)
const keyModalSite = ref<RelaySite | null>(null)
const tempApiKey = ref('')

const categoryTabs = [
  { id: 'all', name: '全部供应商' },
  { id: 'official', name: '官方与原厂' },
  { id: 'cloud', name: '云算力与路由' },
  { id: 'custom', name: '自建中转站' }
]

const getCategoryCount = (catId: string) => {
  if (catId === 'all') return store.relaySites.length
  if (catId === 'official') return store.relaySites.filter((s) => s.site_type === 'official').length
  if (catId === 'cloud') return store.relaySites.filter((s) => s.site_type === 'cloud').length
  if (catId === 'custom') return store.relaySites.filter((s) => !s.is_official_catalog).length
  return 0
}

const filteredSites = computed(() => {
  let list = store.relaySites
  if (activeCategory.value === 'official') {
    list = list.filter((s) => s.site_type === 'official')
  } else if (activeCategory.value === 'cloud') {
    list = list.filter((s) => s.site_type === 'cloud')
  } else if (activeCategory.value === 'custom') {
    list = list.filter((s) => !s.is_official_catalog)
  }

  if (searchKey.value.trim()) {
    const q = searchKey.value.toLowerCase().trim()
    list = list.filter((s) => s.name.toLowerCase().includes(q) || (s.provider_id && s.provider_id.toLowerCase().includes(q)))
  }
  return list
})

const form = ref({
  name: '',
  base_url: '',
  api_key: '',
  site_type: 'newapi',
  recharge_rate: 1.0,
  models_endpoint: '/api/models',
  status_endpoint: '/api/status',
  is_active: true,
  notes: ''
})

const openAddModal = () => {
  form.value = {
    name: '',
    base_url: '',
    api_key: '',
    site_type: 'newapi',
    recharge_rate: 1.0,
    models_endpoint: '/api/models',
    status_endpoint: '/api/status',
    is_active: true,
    notes: ''
  }
  showAddModal.value = true
}

const submitChannel = async () => {
  if (!form.value.name || !form.value.base_url) return
  try {
    await axios.post(`${store.apiUrl}/api/v1/channels`, form.value)
    showAddModal.value = false
    await store.fetchRelaySites()
    await store.fetchComparisonMatrix()
  } catch (e) {
    console.error('Submit channel failed:', e)
  }
}

const openKeyModal = (site: RelaySite) => {
  keyModalSite.value = site
  tempApiKey.value = site.api_key || ''
}

const saveApiKey = async () => {
  if (!keyModalSite.value) return
  try {
    await axios.put(`${store.apiUrl}/api/v1/channels/${keyModalSite.value.id}`, {
      api_key: tempApiKey.value
    })
    keyModalSite.value = null
    await store.fetchRelaySites()
  } catch (e) {
    console.error('Save API Key failed:', e)
  }
}

const testSpeed = (id: number) => {
  store.activeTab = 'speed-tester'
  store.runSpeedTest([id], 'deepseek-v3')
}
</script>
