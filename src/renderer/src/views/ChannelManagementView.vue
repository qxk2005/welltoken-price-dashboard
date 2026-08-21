<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- 顶部操作栏 -->
    <div class="p-3 rounded-xl bg-[#151922] border border-[#232936] flex items-center justify-between">
      <div class="flex items-center space-x-2">
        <span class="text-sm font-bold text-white">已收录中转渠道 (共 {{ store.relaySites.length }} 家)</span>
      </div>

      <div class="flex items-center space-x-2">
        <button
          @click="store.syncAllRelays"
          class="text-xs px-3 py-1.5 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-200 border border-[#374151] transition-all flex items-center space-x-1"
        >
          <span>⚡ 一键全站探测与同步</span>
        </button>
        <button
          @click="openAddModal"
          class="text-xs px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium shadow-md shadow-blue-600/20 transition-all flex items-center space-x-1"
        >
          <span>+ 新增中转渠道</span>
        </button>
      </div>
    </div>

    <!-- 渠道卡片流 (Grid 布局) -->
    <div class="flex-1 overflow-y-auto pr-1">
      <div class="grid grid-cols-2 gap-3">
        <div
          v-for="site in store.relaySites"
          :key="site.id"
          class="p-4 rounded-xl bg-[#151922] border border-[#232936] hover:border-[#353E52] transition-all flex flex-col justify-between space-y-3"
        >
          <!-- 卡片头部：站点名、类型、状态 -->
          <div class="flex items-start justify-between">
            <div class="flex items-center space-x-2">
              <div class="w-8 h-8 rounded-lg bg-[#232936] flex items-center justify-center text-xs font-bold text-blue-400 font-mono">
                {{ site.name.slice(0, 2) }}
              </div>
              <div>
                <div class="flex items-center space-x-2">
                  <span class="font-bold text-sm text-white">{{ site.name }}</span>
                  <span
                    class="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase font-semibold"
                    :class="getTypeBadgeClass(site.site_type)"
                  >
                    {{ site.site_type }}
                  </span>
                </div>
                <div class="text-[11px] text-gray-500 truncate max-w-[280px] font-mono mt-0.5">
                  {{ site.base_url }}
                </div>
              </div>
            </div>

            <!-- 在线状态指示 -->
            <div class="flex items-center space-x-1.5 text-xs font-mono">
              <span
                class="w-2 h-2 rounded-full"
                :class="site.last_status === 'online' ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50' : 'bg-rose-500'"
              ></span>
              <span :class="site.last_status === 'online' ? 'text-emerald-400' : 'text-rose-400'">
                {{ site.last_status === 'online' ? `${site.last_latency_ms}ms` : '离线' }}
              </span>
            </div>
          </div>

          <!-- 卡片数据体：充值汇率、模型数、说明 -->
          <div class="grid grid-cols-3 gap-2 py-2 px-3 rounded-lg bg-[#0B0E14]/60 border border-[#232936]/40 text-xs">
            <div>
              <div class="text-[10px] text-gray-500">充值汇率比</div>
              <div class="font-mono font-bold text-gray-200">{{ site.recharge_rate }} : 1</div>
            </div>
            <div>
              <div class="text-[10px] text-gray-500">支持模型数</div>
              <div class="font-mono font-bold text-blue-400">{{ site.model_count || 10 }} 款</div>
            </div>
            <div>
              <div class="text-[10px] text-gray-500">质量综合评分</div>
              <div class="font-mono font-bold text-emerald-400">{{ site.score }} 分</div>
            </div>
          </div>

          <div v-if="site.notes" class="text-[11px] text-gray-400 line-clamp-1">
            {{ site.notes }}
          </div>

          <!-- 卡片底部操作按钮 -->
          <div class="pt-2 border-t border-[#232936]/60 flex items-center justify-between text-xs">
            <span class="text-[10px] text-gray-500">
              最后同步: {{ formatTime(site.last_sync_time) }}
            </span>
            <div class="flex items-center space-x-2">
              <button
                @click="pingSite(site.id)"
                class="text-sky-400 hover:text-sky-300 transition-colors"
              >
                [探测同步]
              </button>
              <button
                @click="testSpeed(site.id)"
                class="text-emerald-400 hover:text-emerald-300 transition-colors"
              >
                [立即测速]
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增渠道模态弹窗 -->
    <div
      v-if="showModal"
      class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div class="w-[520px] rounded-xl bg-[#151922] border border-[#2D3748] p-5 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-[#232936] pb-3">
          <span class="font-bold text-sm text-white">新增中转渠道与自动探测规则</span>
          <button @click="showModal = false" class="text-gray-400 hover:text-white text-sm">✕</button>
        </div>

        <div class="space-y-3 text-xs">
          <div>
            <label class="block text-gray-400 mb-1">渠道架构类型</label>
            <select
              v-model="form.site_type"
              class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white focus:outline-none focus:border-blue-500"
            >
              <option value="newapi">NewAPI (支持 /api/models 与倍率表)</option>
              <option value="sub2api">Sub2API (包月/额度混合)</option>
              <option value="oneapi">OneAPI 架构</option>
              <option value="official">官方直连 API (OpenAI/Anthropic/DeepSeek)</option>
              <option value="custom">自定义中转</option>
            </select>
          </div>

          <div>
            <label class="block text-gray-400 mb-1">渠道站点名称</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="如：极速云 AI、星河中转"
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
            <label class="block text-gray-400 mb-1">API Key / 凭据 (可选)</label>
            <input
              v-model="form.api_key"
              type="password"
              placeholder="sk-xxxxxxxxxxxxxxxx"
              class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-blue-500"
            />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-gray-400 mb-1">充值汇率 (1元兑换多少刀额度)</label>
              <input
                v-model.number="form.recharge_rate"
                type="number"
                step="0.1"
                class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-blue-500"
              />
            </div>
            <div>
              <label class="block text-gray-400 mb-1">模型列表端点</label>
              <input
                v-model="form.models_endpoint"
                type="text"
                class="w-full bg-[#1A202C] border border-[#2D3748] rounded-lg px-3 py-2 text-white font-mono focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        <div class="pt-3 border-t border-[#232936] flex items-center justify-end space-x-2">
          <button
            @click="showModal = false"
            class="px-4 py-2 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-300 text-xs"
          >
            取消
          </button>
          <button
            @click="submitChannel"
            class="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs shadow-md shadow-blue-600/20"
          >
            保存并测试连通性
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import axios from 'axios'
import { useDashboardStore } from '../stores/dashboardStore'

const store = useDashboardStore()
const showModal = ref(false)

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
  showModal.value = true
}

const submitChannel = async () => {
  if (!form.value.name || !form.value.base_url) return
  try {
    await axios.post(`${store.apiUrl}/api/v1/channels`, form.value)
    showModal.value = false
    await store.fetchRelaySites()
    await store.fetchComparisonMatrix()
  } catch (e) {
    console.error('Submit channel failed:', e)
  }
}

const pingSite = async (id: number) => {
  try {
    await axios.post(`${store.apiUrl}/api/v1/channels/${id}/ping`)
    await store.fetchRelaySites()
    await store.fetchComparisonMatrix()
  } catch (e) {
    console.error('Ping failed:', e)
  }
}

const testSpeed = (id: number) => {
  store.activeTab = 'speed-tester'
  store.runSpeedTest([id], 'deepseek-v3')
}

const getTypeBadgeClass = (type: string) => {
  if (type === 'official') return 'bg-slate-800 text-slate-300'
  if (type === 'newapi') return 'bg-emerald-950 text-emerald-400 border border-emerald-800'
  if (type === 'sub2api') return 'bg-purple-950 text-purple-300 border border-purple-800'
  return 'bg-blue-950 text-blue-300'
}

const formatTime = (timeStr: string) => {
  if (!timeStr) return '刚刚'
  const d = new Date(timeStr)
  return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
</script>
