<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- ==================== 场景 A：厂商与 Labs 大全列表 (参考 models.dev/labs/) ==================== -->
    <template v-if="!selectedLab">
      <!-- 顶部操作栏 -->
      <div class="p-3 rounded-xl bg-[#151922] border border-[#232936] flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-white">大模型厂商与研究机构 (共 {{ labsList.length }} 家)</span>
            <span class="text-xs text-gray-500 font-mono">| 参考 models.dev/labs/ 标准体系</span>
          </div>

          <!-- 搜索输入框 -->
          <div class="w-64 relative">
            <input
              v-model="labSearchQuery"
              type="text"
              placeholder="搜索厂商 (如 DeepSeek, OpenAI, 阿里)..."
              class="w-full bg-[#0B0E14] border border-[#2D3748] rounded-lg px-2.5 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            />
            <span v-if="labSearchQuery" @click="labSearchQuery = ''" class="absolute right-2 top-1 text-gray-500 hover:text-white cursor-pointer text-xs">✕</span>
          </div>
        </div>

        <button
          @click="store.syncModelsDev"
          class="text-xs px-3 py-1.5 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-blue-400 border border-[#374151] transition-all flex items-center space-x-1"
        >
          <span>🔄 从 models.dev 重新同步模型库</span>
        </button>
      </div>

      <!-- 厂商卡片流 (3 列 Grid 布局) -->
      <div class="flex-1 overflow-y-auto pr-1">
        <div class="grid grid-cols-3 gap-3">
          <div
            v-for="lab in filteredLabs"
            :key="lab.id"
            @click="selectLab(lab)"
            class="p-4 rounded-xl bg-[#151922] border border-[#232936] hover:border-blue-500/50 hover:bg-[#1A202C] transition-all cursor-pointer flex flex-col justify-between space-y-3 group shadow-sm"
          >
            <!-- 厂商头部：图标、名称、模型总数 Badge -->
            <div class="flex items-start justify-between">
              <div class="flex items-center space-x-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-[#1E293B] to-[#0F172A] border border-[#334155] flex items-center justify-center text-sm font-bold font-mono text-blue-400 group-hover:scale-105 transition-transform">
                  {{ lab.id.slice(0, 2).toUpperCase() }}
                </div>
                <div>
                  <div class="font-bold text-sm text-white group-hover:text-blue-400 transition-colors">
                    {{ lab.displayName }}
                  </div>
                  <div class="text-[11px] text-gray-500 font-mono mt-0.5">
                    {{ lab.id }}
                  </div>
                </div>
              </div>

              <!-- 模型数量 Badge -->
              <span class="px-2 py-0.5 rounded-full bg-blue-500/15 text-blue-400 text-xs font-mono font-bold">
                {{ lab.models.length }} 款模型
              </span>
            </div>

            <!-- 系列预览 Chips 胶囊 -->
            <div class="space-y-1">
              <div class="text-[10px] text-gray-500 uppercase tracking-wider font-semibold">主要模型系列:</div>
              <div class="flex flex-wrap gap-1">
                <span
                  v-for="fam in lab.families.slice(0, 4)"
                  :key="fam"
                  class="px-2 py-0.5 rounded bg-[#0B0E14] border border-[#232936] text-gray-300 text-[10px] font-mono"
                >
                  {{ fam }}
                </span>
                <span v-if="lab.families.length > 4" class="text-[10px] text-gray-500 font-mono self-center">
                  +{{ lab.families.length - 4 }} 系列
                </span>
              </div>
            </div>

            <!-- 底部进入按钮引导 -->
            <div class="pt-2 border-t border-[#232936]/60 flex items-center justify-between text-xs text-gray-400">
              <span class="text-[11px] text-gray-500">点击查看旗下模型与规格</span>
              <span class="text-blue-400 group-hover:translate-x-1 transition-transform font-bold">浏览系列 →</span>
            </div>
          </div>
        </div>

        <div v-if="filteredLabs.length === 0" class="py-16 text-center text-xs text-gray-500">
          无匹配的厂商或研究机构
        </div>
      </div>
    </template>

    <!-- ==================== 场景 B：某厂商专属模型系列详情下钻页 ==================== -->
    <template v-else>
      <!-- 顶部面包屑与返回导航 -->
      <div class="p-3 rounded-xl bg-[#151922] border border-[#232936] flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <button
            @click="selectedLab = null"
            class="px-2.5 py-1 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-200 border border-[#374151] transition-all text-xs font-medium flex items-center space-x-1"
          >
            <span>← 返回厂商列表</span>
          </button>
          <span class="text-gray-600">/</span>
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-white">{{ selectedLab.displayName }}</span>
            <span class="px-2 py-0.5 rounded bg-blue-500/15 text-blue-400 text-xs font-mono font-bold">
              共 {{ selectedLab.models.length }} 款模型
            </span>
          </div>
        </div>

        <!-- 厂商内模型搜索 -->
        <div class="w-64 relative">
          <input
            v-model="modelSearchQuery"
            type="text"
            placeholder="搜索该厂商下的模型..."
            class="w-full bg-[#0B0E14] border border-[#2D3748] rounded-lg px-2.5 py-1 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
          />
          <span v-if="modelSearchQuery" @click="modelSearchQuery = ''" class="absolute right-2 top-1 text-gray-500 hover:text-white cursor-pointer text-xs">✕</span>
        </div>
      </div>

      <!-- 按模型系列 (Series / Family) 分组展示主区域 -->
      <div class="flex-1 overflow-y-auto pr-1 space-y-4">
        <div
          v-for="group in groupedModelsByFamily"
          :key="group.family"
          class="p-4 rounded-xl bg-[#151922] border border-[#232936] space-y-3"
        >
          <!-- 系列标题栏 -->
          <div class="flex items-center justify-between border-b border-[#232936] pb-2">
            <div class="flex items-center space-x-2">
              <span class="text-sm font-bold text-white">📦 {{ group.family }} 系列</span>
              <span class="text-xs text-gray-500 font-mono">({{ group.models.length }} 款模型)</span>
            </div>
            <button
              @click="goToMatrixWithSeries(group.family)"
              class="text-xs text-blue-400 hover:text-blue-300 transition-colors font-mono"
            >
              [全系列全网比价 →]
            </button>
          </div>

          <!-- 系列下的模型卡片网格 (2列) -->
          <div class="grid grid-cols-2 gap-3">
            <div
              v-for="model in group.models"
              :key="model.model_id"
              class="p-3.5 rounded-lg bg-[#0B0E14]/80 border border-[#232936]/80 hover:border-gray-600 transition-all flex flex-col justify-between space-y-2.5"
            >
              <!-- 模型头部：名称、标准 ID -->
              <div class="flex items-start justify-between">
                <div>
                  <div class="font-bold text-xs text-white">{{ model.name }}</div>
                  <div class="text-[11px] text-blue-400 font-mono mt-0.5">{{ model.model_id }}</div>
                </div>
                <span class="px-1.5 py-0.2 rounded bg-[#1E293B] text-gray-300 text-[10px] font-mono">
                  {{ model.series || group.family }}
                </span>
              </div>

              <!-- 核心规格参数指标 -->
              <div class="grid grid-cols-3 gap-2 py-1.5 px-2.5 rounded bg-[#151922] border border-[#232936]/50 text-xs">
                <div>
                  <div class="text-[10px] text-gray-500">上下文窗口</div>
                  <div class="font-mono font-bold text-sky-400 text-[11px]">
                    {{ (model.context_window / 1000).toFixed(0) }}k Context
                  </div>
                </div>
                <div>
                  <div class="text-[10px] text-gray-500">最大输出</div>
                  <div class="font-mono font-bold text-gray-200 text-[11px]">{{ model.max_output }} Tokens</div>
                </div>
                <div>
                  <div class="text-[10px] text-gray-500">官方输入价</div>
                  <div class="font-mono font-bold text-emerald-400 text-[11px]">
                    ${{ model.official_input_price }} / 1M
                  </div>
                </div>
              </div>

              <!-- 底部渠道覆盖与快捷动作 -->
              <div class="pt-1.5 border-t border-[#232936]/50 flex items-center justify-between text-xs">
                <span class="text-[11px] text-gray-400">
                  全网最低: <strong class="text-emerald-400 font-mono">${{ model.lowest_price_usd }}/1M</strong>
                </span>
                <div class="flex items-center space-x-2 font-mono text-[11px]">
                  <button
                    @click="goToMatrix(model.model_id)"
                    class="text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    [全网比价]
                  </button>
                  <button
                    @click="goToSpeedTest(model.model_id)"
                    class="text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    [性能实测]
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="groupedModelsByFamily.length === 0" class="py-12 text-center text-xs text-gray-500">
          该厂商下无匹配的模型
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useDashboardStore } from '../stores/dashboardStore'
import type { ModelMetadata } from '../types'

interface LabItem {
  id: string
  displayName: string
  models: ModelMetadata[]
  families: string[]
}

const store = useDashboardStore()
const selectedLab = ref<LabItem | null>(null)
const labSearchQuery = ref('')
const modelSearchQuery = ref('')

// 厂商中英文友好名称映射表
const labDisplayNameMap: Record<string, string> = {
  deepseek: 'DeepSeek (深度求索)',
  openai: 'OpenAI',
  anthropic: 'Anthropic (Claude)',
  google: 'Google DeepMind (Gemini)',
  alibaba: 'Alibaba Cloud (阿里通义千问)',
  moonshotai: 'Moonshot AI (月之暗面 Kimi)',
  zhipuai: 'Zhipu AI (智谱清言 GLM)',
  meta: 'Meta (Llama)',
  mistral: 'Mistral AI',
  nvidia: 'Nvidia (Nemotron)',
  cohere: 'Cohere',
  bytedance: 'ByteDance (字节跳动 Doubao)',
  'bytedance-seed': 'ByteDance Seed',
  xai: 'xAI (Grok)',
  minimax: 'MiniMax (稀宇科技)',
  xiaomi: 'Xiaomi (小米 MiLM)',
  tencent: 'Tencent (腾讯混元 Hunyuan)',
  baichuan: 'Baichuan (百川智能)'
}

// 自动聚合计算出所有的 Labs 厂商实体
const labsList = computed<LabItem[]>(() => {
  const map: Record<string, ModelMetadata[]> = {}

  store.modelsCatalog.forEach((m) => {
    let labId = m.provider.toLowerCase()
    if (m.model_id.includes('/')) {
      labId = m.model_id.split('/')[0].toLowerCase()
    }
    if (!map[labId]) {
      map[labId] = []
    }
    map[labId].push(m)
  })

  return Object.keys(map).map((labId) => {
    const models = map[labId]
    const familiesSet = new Set<string>()
    models.forEach((m) => {
      if (m.series) familiesSet.add(m.series)
      else if (m.family) familiesSet.add(m.family.replace('-', ' ').toUpperCase())
      else familiesSet.add('通用系列')
    })

    return {
      id: labId,
      displayName: labDisplayNameMap[labId] || labId.toUpperCase(),
      models,
      families: Array.from(familiesSet)
    }
  }).sort((a, b) => b.models.length - a.models.length)
})

// 厂商搜索过滤
const filteredLabs = computed(() => {
  if (!labSearchQuery.value.trim()) return labsList.value
  const q = labSearchQuery.value.toLowerCase().trim()
  return labsList.value.filter(
    (lab) => lab.displayName.toLowerCase().includes(q) || lab.id.toLowerCase().includes(q)
  )
})

const selectLab = (lab: LabItem) => {
  selectedLab.value = lab
  modelSearchQuery.value = ''
}

// 在选中的厂商详情中，按模型系列 (Family/Series) 分组
const groupedModelsByFamily = computed(() => {
  if (!selectedLab.value) return []
  let list = selectedLab.value.models

  if (modelSearchQuery.value.trim()) {
    const q = modelSearchQuery.value.toLowerCase().trim()
    list = list.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.model_id.toLowerCase().includes(q) ||
        (m.series && m.series.toLowerCase().includes(q))
    )
  }

  const map: Record<string, ModelMetadata[]> = {}
  list.forEach((m) => {
    let fam = m.series
    if (!fam && m.family) {
      fam = m.family.replace(/-/g, ' ').toUpperCase()
    }
    if (!fam) {
      fam = '通用系列'
    }
    if (!map[fam]) map[fam] = []
    map[fam].push(m)
  })

  return Object.keys(map).map((fam) => ({
    family: fam,
    models: map[fam]
  }))
})

const goToMatrix = (modelId: string) => {
  store.selectedModelId = modelId
  store.activeTab = 'price-matrix'
}

const goToMatrixWithSeries = (series: string) => {
  store.searchQuery = series
  store.activeTab = 'price-matrix'
}

const goToSpeedTest = (modelId: string) => {
  store.activeTab = 'speed-tester'
  const siteIds = store.activeSites.slice(0, 3).map((s) => s.id)
  store.runSpeedTest(siteIds, modelId)
}
</script>
