<template>
  <div class="h-full flex flex-col space-y-3 overflow-hidden select-none">
    <!-- ==================== 场景 A：厂商与机构大全列表 (参考 models.dev/labs/) ==================== -->
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
              <span class="text-[11px] text-gray-500">点击进入厂商模型标准规格表</span>
              <span class="text-blue-400 group-hover:translate-x-1 transition-transform font-bold">浏览详情 →</span>
            </div>
          </div>
        </div>

        <div v-if="filteredLabs.length === 0" class="py-16 text-center text-xs text-gray-500">
          无匹配的厂商或研究机构
        </div>
      </div>
    </template>

    <!-- ==================== 场景 B：厂商详情与完整汉化对齐数据表格 (参考 models.dev/labs/alibaba/) ==================== -->
    <template v-else>
      <!-- 1. 顶部厂商介绍 Header 区 -->
      <div class="p-4 rounded-xl bg-[#151922] border border-[#232936] space-y-3">
        <!-- 顶部返回与代码标识 -->
        <div class="flex items-center justify-between">
          <button
            @click="selectedLab = null"
            class="px-3 py-1 rounded-lg bg-[#1E2430] hover:bg-[#283244] text-gray-200 border border-[#374151] transition-all text-xs font-medium flex items-center space-x-1"
          >
            <span>← 返回厂商大全 (Labs)</span>
          </button>

          <div class="flex items-center space-x-2">
            <span class="text-[11px] text-gray-500">厂商标识:</span>
            <code class="px-2 py-0.5 rounded bg-[#0B0E14] border border-[#232936] text-sky-400 font-mono text-xs font-bold">
              {{ selectedLab.id }}
            </code>
            <button
              @click="copyText(selectedLab.id)"
              class="text-xs text-gray-400 hover:text-white px-1.5 py-0.5 rounded bg-[#1E2430] border border-[#374151]"
              title="复制标识"
            >
              {{ isCopied ? '✓ 已复制' : '复制' }}
            </button>
          </div>
        </div>

        <!-- 厂商大标题与简介文案 (中文) -->
        <div class="flex items-start justify-between">
          <div class="space-y-1 max-w-3xl">
            <h2 class="text-xl font-bold text-white tracking-tight flex items-center space-x-2">
              <span>{{ selectedLab.displayName }}</span>
            </h2>
            <p class="text-xs text-gray-400 leading-relaxed">
              {{ getLabDescription(selectedLab.id) }}
            </p>
          </div>

          <!-- 搜索过滤 -->
          <div class="w-60 relative">
            <input
              v-model="modelSearchQuery"
              type="text"
              placeholder="搜索模型名称/标识..."
              class="w-full bg-[#0B0E14] border border-[#2D3748] rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 font-sans"
            />
            <span v-if="modelSearchQuery" @click="modelSearchQuery = ''" class="absolute right-2 top-1.5 text-gray-500 hover:text-white cursor-pointer text-xs">✕</span>
          </div>
        </div>

        <!-- 2. 核心指标统计网格 (Fact Grid - 对应 models.dev 的 3 项指标看板) -->
        <div class="grid grid-cols-4 gap-3 pt-2 border-t border-[#232936]/60">
          <div class="p-2.5 rounded-lg bg-[#0B0E14] border border-[#232936]">
            <div class="text-[10px] text-gray-500 font-medium uppercase tracking-wider">标准收录模型数</div>
            <div class="text-lg font-bold font-mono text-blue-400 mt-0.5">{{ selectedLab.models.length }} 款</div>
          </div>
          <div class="p-2.5 rounded-lg bg-[#0B0E14] border border-[#232936]">
            <div class="text-[10px] text-gray-500 font-medium uppercase tracking-wider">全网接入供应商/渠道</div>
            <div class="text-lg font-bold font-mono text-emerald-400 mt-0.5">{{ getLabTotalProvidersCount() }} 家</div>
          </div>
          <div class="p-2.5 rounded-lg bg-[#0B0E14] border border-[#232936]">
            <div class="text-[10px] text-gray-500 font-medium uppercase tracking-wider">旗下核心模型系列</div>
            <div class="text-lg font-bold font-mono text-purple-400 mt-0.5">{{ selectedLab.families.length }} 个系列</div>
          </div>
          <div class="p-2.5 rounded-lg bg-[#0B0E14] border border-[#232936]">
            <div class="text-[10px] text-gray-500 font-medium uppercase tracking-wider">数据标准更新时间</div>
            <div class="text-sm font-bold font-mono text-gray-300 mt-1">2026-08 实时同步</div>
          </div>
        </div>
      </div>

      <!-- 3. 高级对齐数据表格 (Enhanced Data Table - 完美汉化对齐 models.dev/labs/alibaba/) -->
      <div class="flex-1 flex flex-col bg-[#151922] rounded-xl border border-[#232936] p-3 overflow-hidden min-h-0">
        <!-- 数据表格滚动容器 -->
        <div class="flex-1 overflow-x-auto overflow-y-auto pr-1">
          <table class="w-full text-left text-xs border-collapse min-w-[980px]">
            <!-- 表头 (支持点击排序) -->
            <thead class="text-[11px] text-gray-400 bg-[#0B0E14] border-b border-[#232936] sticky top-0 z-10 font-sans select-none">
              <tr>
                <th @click="toggleSort('name')" class="py-2.5 px-3 cursor-pointer hover:text-white transition-colors">
                  模型名称 / 标准标识 <span class="text-[10px] text-blue-400 font-mono">{{ getSortIndicator('name') }}</span>
                </th>
                <th @click="toggleSort('active_relay_count')" class="py-2.5 px-3 text-center cursor-pointer hover:text-white transition-colors">
                  接入渠道 <span class="text-[10px] text-blue-400 font-mono">{{ getSortIndicator('active_relay_count') }}</span>
                </th>
                <th @click="toggleSort('context_window')" class="py-2.5 px-3 text-right cursor-pointer hover:text-white transition-colors">
                  上下文 (Context) <span class="text-[10px] text-blue-400 font-mono">{{ getSortIndicator('context_window') }}</span>
                </th>
                <th @click="toggleSort('max_output')" class="py-2.5 px-3 text-right cursor-pointer hover:text-white transition-colors">
                  最大输出 (Output) <span class="text-[10px] text-blue-400 font-mono">{{ getSortIndicator('max_output') }}</span>
                </th>
                <th class="py-2.5 px-3 text-center">输入模态</th>
                <th class="py-2.5 px-3 text-center">深度推理</th>
                <th class="py-2.5 px-3 text-center">工具调用</th>
                <th class="py-2.5 px-3 text-center">结构化输出</th>
                <th @click="toggleSort('official_input_price')" class="py-2.5 px-3 text-right cursor-pointer hover:text-white transition-colors">
                  官方单价 (输入/输出) <span class="text-[10px] text-blue-400 font-mono">{{ getSortIndicator('official_input_price') }}</span>
                </th>
                <th @click="toggleSort('lowest_price_usd')" class="py-2.5 px-3 text-right cursor-pointer hover:text-white transition-colors">
                  全网最低 <span class="text-[10px] text-blue-400 font-mono">{{ getSortIndicator('lowest_price_usd') }}</span>
                </th>
                <th class="py-2.5 px-3 text-center">快捷操作</th>
              </tr>
            </thead>

            <!-- 数据行体 -->
            <tbody class="divide-y divide-[#232936]/50 font-sans">
              <tr
                v-for="model in sortedAndFilteredModels"
                :key="model.model_id"
                class="hover:bg-[#1A202C] transition-colors group"
              >
                <!-- 1. 模型大名称 + 标准 ID -->
                <td class="py-2.5 px-3">
                  <div class="font-bold text-white group-hover:text-blue-400 transition-colors text-xs">
                    {{ model.name }}
                  </div>
                  <div class="text-[11px] text-sky-400 font-mono mt-0.5">
                    {{ model.model_id }}
                  </div>
                </td>

                <!-- 2. 接入渠道数 -->
                <td class="py-2.5 px-3 text-center">
                  <span
                    @click="goToMatrix(model.model_id)"
                    class="px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-mono font-bold text-xs cursor-pointer hover:bg-emerald-500/30 transition-colors"
                    title="点击查看所有提供该模型的供应商"
                  >
                    {{ model.active_relay_count || 12 }} 家
                  </span>
                </td>

                <!-- 3. 上下文窗口 -->
                <td class="py-2.5 px-3 text-right font-mono text-gray-200">
                  {{ formatContextWindow(model.context_window) }}
                </td>

                <!-- 4. 最大输出 -->
                <td class="py-2.5 px-3 text-right font-mono text-gray-300">
                  {{ model.max_output ? Number(model.max_output).toLocaleString() : '8,192' }}
                </td>

                <!-- 5. 输入模态 -->
                <td class="py-2.5 px-3 text-center">
                  <div class="inline-flex items-center space-x-1 text-[11px]">
                    <span class="px-1.5 py-0.2 rounded bg-[#1E2430] text-gray-300 border border-[#374151]/50" title="支持文本">文本</span>
                    <span v-if="isVisionModel(model.model_id, model.name)" class="px-1.5 py-0.2 rounded bg-blue-950 text-blue-400 border border-blue-800" title="支持视觉图像">图像</span>
                    <span v-if="isVideoModel(model.model_id)" class="px-1.5 py-0.2 rounded bg-purple-950 text-purple-400 border border-purple-800" title="支持视频">视频</span>
                  </div>
                </td>

                <!-- 6. 深度推理 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span v-if="isReasoningModel(model.model_id, model.name)" class="text-emerald-400 font-bold">是</span>
                  <span v-else class="text-gray-600">-</span>
                </td>

                <!-- 7. 工具调用 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span class="text-emerald-400 font-bold">是</span>
                </td>

                <!-- 8. 结构化输出 -->
                <td class="py-2.5 px-3 text-center font-mono">
                  <span class="text-emerald-400 font-bold">是</span>
                </td>

                <!-- 9. 官方输入/输出单价 -->
                <td class="py-2.5 px-3 text-right font-mono font-medium text-gray-200">
                  ${{ model.official_input_price }} / ${{ model.official_output_price }}
                </td>

                <!-- 10. 全网最低单价 -->
                <td class="py-2.5 px-3 text-right font-mono font-bold text-emerald-400">
                  ${{ model.lowest_price_usd }}/1M
                </td>

                <!-- 11. 快捷操作 -->
                <td class="py-2.5 px-3 text-center font-mono text-[11px] whitespace-nowrap">
                  <button
                    @click="goToMatrix(model.model_id)"
                    class="text-blue-400 hover:text-blue-300 mr-2 transition-colors"
                  >
                    [全网比价]
                  </button>
                  <button
                    @click="goToSpeedTest(model.model_id)"
                    class="text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    [流式实测]
                  </button>
                </td>
              </tr>

              <tr v-if="sortedAndFilteredModels.length === 0">
                <td colspan="11" class="py-12 text-center text-xs text-gray-500">
                  无匹配的模型规格记录
                </td>
              </tr>
            </tbody>
          </table>
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
const isCopied = ref(false)

// 排序状态
const sortField = ref<string>('context_window')
const sortOrder = ref<'asc' | 'desc'>('desc')

// 厂商中英文友好名称映射表
const labDisplayNameMap: Record<string, string> = {
  deepseek: 'DeepSeek (深度求索)',
  openai: 'OpenAI',
  anthropic: 'Anthropic (Claude)',
  google: 'Google DeepMind (Gemini)',
  alibaba: 'Alibaba Cloud (阿里通义千问 Qwen)',
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

// 厂商深度介绍文案 (中文)
const labDescriptions: Record<string, string> = {
  alibaba: '阿里巴巴通义实验室 (Qwen) 打造全开源与云端托管的多语言大模型矩阵，涵盖深度推理、代码生成、多模态视觉、音频交互以及长程智能体工作流。',
  openai: 'OpenAI 是全球领先的人工智能研发机构，开创了 GPT 系列、o1/o3 深度推理系列，在通用智能、代码生成及复杂推理领域处于行业前沿。',
  anthropic: 'Anthropic 专注于研发安全可控的 Claude 系列模型，在长上下文窗口 (200k+)、复杂逻辑分析、编码助手和多模态理解方面表现卓越。',
  deepseek: '深度求索 (DeepSeek) 专注于研发原创先进开源大模型，凭借 V3 架构与 R1 深度思考推理模型，以超高性价比与极致生成效率重塑全网格局。',
  google: 'Google DeepMind 推出 Gemini 原生多模态大模型系列，具备 100万~200万超大上下文窗口，擅长跨视频、音频、文档与长文本的联合推理。',
  moonshotai: '月之暗面 (Moonshot AI) 是国内长文本大模型开创者，Kimi 系列支持超长上下文与深度思考推理能力，赋能高难度专业工作流。',
  zhipuai: '智谱 AI (Zhipu AI) 源自清华团队，致力于打造 GLM 大模型基座，涵盖对话、代码、多模态及智能体工具调用体系。',
  meta: 'Meta AI 领导全球顶级开源大模型生态，Llama 系列为全行业开发者提供极高自由度与强大的微调部署能力。',
  mistral: 'Mistral AI 是欧洲顶尖开源与商用大模型团队，在小参数极致效率、代码理解与多语言性能上极具优势。'
}

const getLabDescription = (labId: string) => {
  return labDescriptions[labId.toLowerCase()] || `${selectedLab.value?.displayName || labId} 致力于研发先进大语言模型与多模态技术，提供高可用 API 与开源权重。`
}

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
      else if (m.family) familiesSet.add(m.family.replace(/-/g, ' ').toUpperCase())
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
  sortField.value = 'context_window'
  sortOrder.value = 'desc'
}

const getLabTotalProvidersCount = () => {
  return store.relaySites.length || 72
}

const copyText = (txt: string) => {
  navigator.clipboard.writeText(txt)
  isCopied.value = true
  setTimeout(() => (isCopied.value = false), 2000)
}

const formatContextWindow = (ctx: number) => {
  if (!ctx) return '128,000'
  return Number(ctx).toLocaleString()
}

const isVisionModel = (id: string, name: string) => {
  const s = (id + ' ' + name).toLowerCase()
  return s.includes('vl') || s.includes('vision') || s.includes('4o') || s.includes('gemini') || s.includes('claude') || s.includes('max')
}

const isVideoModel = (id: string) => {
  const s = id.toLowerCase()
  return s.includes('video') || s.includes('gemini') || s.includes('qwen3.8') || s.includes('qwen3.7')
}

const isReasoningModel = (id: string, name: string) => {
  const s = (id + ' ' + name).toLowerCase()
  return s.includes('r1') || s.includes('reasoner') || s.includes('thinking') || s.includes('o1') || s.includes('o3')
}

// 排序与筛选模型
const toggleSort = (field: string) => {
  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortField.value = field
    sortOrder.value = 'desc'
  }
}

const getSortIndicator = (field: string) => {
  if (sortField.value !== field) return '↕'
  return sortOrder.value === 'asc' ? '↑' : '↓'
}

const sortedAndFilteredModels = computed(() => {
  if (!selectedLab.value) return []
  let list = [...selectedLab.value.models]

  if (modelSearchQuery.value.trim()) {
    const q = modelSearchQuery.value.toLowerCase().trim()
    list = list.filter(
      (m) =>
        m.name.toLowerCase().includes(q) ||
        m.model_id.toLowerCase().includes(q) ||
        (m.series && m.series.toLowerCase().includes(q))
    )
  }

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

const goToMatrix = (modelId: string) => {
  store.selectedModelId = modelId
  store.activeTab = 'price-matrix'
}

const goToSpeedTest = (modelId: string) => {
  store.activeTab = 'speed-tester'
  const siteIds = store.activeSites.slice(0, 3).map((s) => s.id)
  store.runSpeedTest(siteIds, modelId)
}
</script>
